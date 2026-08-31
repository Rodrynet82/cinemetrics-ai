"""
mcp_client.py - Cliente MCP para ClickHouse
============================================
Este módulo gestiona la comunicación con el servidor MCP de ClickHouse.

ARQUITECTURA MCP:
=================
El Model Context Protocol (MCP) define un protocolo estándar para que los
modelos de IA puedan usar "herramientas" externas de forma segura.

En este proyecto, el flujo es:
  1. Este script Python (cliente MCP) lanza `mcp-clickhouse` como subproceso.
  2. La comunicación es por stdin/stdout usando JSON-RPC 2.0.
  3. El servidor mcp-clickhouse expone herramientas como `run_select_query`.
  4. El agente Gemini llama a esas herramientas mediante Function Calling.
  5. Este cliente recibe la llamada de Gemini, la reenvía al servidor MCP,
     y devuelve el resultado JSON a Gemini para formular la respuesta final.

PREREQUISITO EXTERNO:
=====================
El servidor mcp-clickhouse debe estar instalado. Las opciones son:
  - Con uv (recomendado): `pip install uv` → luego usa `uvx mcp-clickhouse`
  - Con pip:              `pip install mcp-clickhouse`
  - Con npx:             `npx @clickhouse/mcp-server`

El servidor se lanza AUTOMÁTICAMENTE como subproceso cuando se crea
una instancia de MCPClickHouseClient. No necesitas iniciarlo manualmente.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool

from config import Settings, get_settings

logger = logging.getLogger(__name__)


def resolve_mcp_command(command: str) -> str:
    """
    Resuelve la ruta completa del comando MCP para evitar FileNotFoundError (WinError 2) en Windows.
    Busca en PATH, en .venv/Scripts y en sys.prefix.
    """
    if not command:
        return command

    # 1. Si ya es una ruta existente
    if Path(command).is_absolute() and Path(command).exists():
        return command

    # 2. Buscar en PATH del sistema
    which_path = shutil.which(command)
    if which_path:
        return which_path

    # 3. Buscar en el virtualenv activo (sys.prefix/Scripts en Windows)
    venv_scripts = Path(sys.prefix) / "Scripts"
    for ext in ["", ".exe", ".cmd", ".bat"]:
        candidate = venv_scripts / f"{command}{ext}"
        if candidate.exists():
            return str(candidate)

    # 4. Buscar en .venv del workspace
    local_scripts = Path.cwd() / ".venv" / "Scripts"
    for ext in ["", ".exe", ".cmd", ".bat"]:
        candidate = local_scripts / f"{command}{ext}"
        if candidate.exists():
            return str(candidate)

    return command


def extract_clean_error_message(exc: BaseException) -> str:
    """
    Extrae el mensaje de error real y legible, desenvolviendo ExceptionGroups de Python 3.11+.
    """
    # Si es BaseExceptionGroup / ExceptionGroup de Python 3.11+ / AnyIO TaskGroup
    if hasattr(exc, "exceptions") and exc.exceptions:
        messages = [extract_clean_error_message(sub) for sub in exc.exceptions]
        clean_msgs = [m for m in messages if m and m != "unhandled errors in a TaskGroup"]
        if clean_msgs:
            return " | ".join(clean_msgs)

    msg = str(exc)
    if "10061" in msg or "Failed to establish a new connection" in msg or "ConnectionRefused" in msg:
        return (
            "No se pudo conectar al servidor ClickHouse (conexión rechazada en el host/puerto configurado). "
            "Asegúrate de que ClickHouse esté corriendo en tu máquina o desactiva 'ClickHouse Real' para usar el Modo Demo."
        )
    if "WinError 2" in msg or "FileNotFoundError" in msg or "cannot find the file" in msg:
        return "El ejecutable del servidor MCP no fue encontrado en el sistema."

    return msg or type(exc).__name__


class MCPClickHouseClient:
    """
    Cliente asíncrono para el servidor MCP de ClickHouse.

    Gestiona el ciclo de vida del subproceso del servidor MCP y provee
    métodos de alto nivel para listar herramientas y ejecutar queries.

    Uso típico (como context manager):
        async with MCPClickHouseClient() as client:
            tools = await client.list_tools()
            result = await client.run_query("SELECT count() FROM tickets")
    """

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._session: ClientSession | None = None
        self._available_tools: list[Tool] = []

    @asynccontextmanager
    async def _managed_session(self):
        """
        Context manager que lanza el servidor MCP como subproceso stdio
        y establece la sesión MCP cliente-servidor.

        El servidor `mcp-clickhouse` recibe su configuración de ClickHouse
        a través de variables de entorno (no flags de CLI), por eso
        pasamos `settings.clickhouse_env` como `env` al subproceso.
        """
        resolved_cmd = resolve_mcp_command(self.settings.mcp_server_command)
        server_params = StdioServerParameters(
            command=resolved_cmd,
            args=self.settings.mcp_server_args_list,
            env=self.settings.clickhouse_env,
        )

        cmd_display = (
            f"{resolved_cmd} "
            f"{' '.join(self.settings.mcp_server_args_list)}"
        )
        logger.info("Iniciando servidor MCP: %s", cmd_display)

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    logger.info("Sesión MCP inicializada correctamente.")
                    self._session = session
                    try:
                        yield session
                    finally:
                        self._session = None
        except FileNotFoundError as exc:
            raise MCPServerNotFoundError(
                command=self.settings.mcp_server_command,
                args=self.settings.mcp_server_args_list,
            ) from exc
        except Exception as exc:
            err_str = str(exc).lower()
            if "winerror 2" in err_str or "no such file" in err_str or "cannot find" in err_str:
                raise MCPServerNotFoundError(
                    command=self.settings.mcp_server_command,
                    args=self.settings.mcp_server_args_list,
                ) from exc
            raise

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        Lista todas las herramientas disponibles en el servidor MCP.

        El servidor mcp-clickhouse típicamente expone:
          - run_select_query / run_query: Ejecuta una query SELECT en ClickHouse
          - list_tables:      Lista las tablas de la base de datos
          - describe_table:   Describe el esquema de una tabla

        Returns:
            Lista de definiciones de herramientas compatibles con
            el formato de Function Calling de Gemini.
        """
        async with self._managed_session() as session:
            response = await session.list_tools()
            self._available_tools = response.tools

            # Convertir al formato de herramientas de Gemini (Function Declarations)
            gemini_tools = []
            for tool in response.tools:
                gemini_tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                })
                logger.debug("Herramienta MCP disponible: %s", tool.name)

            return gemini_tools

    async def call_tool(
        self, tool_name: str, tool_args: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Ejecuta una herramienta del servidor MCP y retorna el resultado.

        Este método es llamado por el agente cuando Gemini decide usar
        una herramienta. El flujo completo es:
          Gemini → FunctionCall → call_tool() → MCP Server → ClickHouse → Result
          Result → Gemini → Respuesta en lenguaje natural

        Args:
            tool_name: Nombre de la herramienta MCP (ej: "run_select_query" o "run_query")
            tool_args: Argumentos de la herramienta (ej: {"query": "SELECT..."})

        Returns:
            Diccionario con el resultado de la herramienta.
        """
        logger.info(
            "Ejecutando herramienta MCP '%s' con args: %s",
            tool_name, tool_args
        )

        async with self._managed_session() as session:
            result = await session.call_tool(tool_name, tool_args)

            # Extraer el contenido del resultado MCP
            if result.content:
                # El servidor MCP retorna una lista de bloques de contenido
                content_blocks = []
                for block in result.content:
                    if hasattr(block, "text"):
                        try:
                            # Intentar parsear como JSON si es posible
                            parsed = json.loads(block.text)
                            content_blocks.append(parsed)
                        except json.JSONDecodeError:
                            content_blocks.append({"text": block.text})

                result_data = (
                    content_blocks[0] if len(content_blocks) == 1
                    else content_blocks
                )
            else:
                result_data = {}

            if result.isError:
                err_text = ""
                if isinstance(result_data, dict) and "text" in result_data:
                    err_text = result_data["text"]
                elif isinstance(result_data, list) and result_data and isinstance(result_data[0], dict):
                    err_text = result_data[0].get("text", str(result_data))
                else:
                    err_text = str(result_data)

                # Si es un error de conexión a ClickHouse
                if "10061" in err_text or "Failed to establish a new connection" in err_text or "ConnectionRefused" in err_text:
                    clean_msg = (
                        f"Error de conexión con ClickHouse: el servidor de base de datos no está accesible "
                        f"en {self.settings.clickhouse_host}:{self.settings.clickhouse_port}. "
                        "Asegúrate de que ClickHouse esté ejecutándose o usa el Modo Demo."
                    )
                else:
                    clean_msg = f"Error ejecutando consulta en ClickHouse: {err_text}"

                logger.error("Error en herramienta MCP '%s': %s", tool_name, clean_msg)
                return {"error": clean_msg, "raw_error": err_text}

            logger.info("Herramienta MCP '%s' completada exitosamente.", tool_name)
            return result_data

    async def run_query(self, sql: str) -> dict[str, Any]:
        """
        Método de conveniencia para ejecutar una query SQL SELECT.

        Args:
            sql: Query SQL SELECT a ejecutar en ClickHouse.

        Returns:
            Resultado de la query como diccionario.
        """
        return await self.call_tool("run_query", {"query": sql})


class MCPToolError(Exception):
    """Excepción lanzada cuando el servidor MCP reporta un error en una herramienta."""
    pass



class MCPServerNotFoundError(Exception):
    """
    Excepción lanzada cuando el ejecutable del servidor MCP no se encuentra.

    Ocurre cuando el comando configurado (ej: 'uvx' o 'mcp-clickhouse')
    no está instalado o no está en el PATH del sistema.

    Solución: instalar el servidor MCP con uno de estos métodos:
      - pip install mcp-clickhouse          (instalación directa en el venv)
      - pip install uv && uvx mcp-clickhouse (con uv tool runner)
    """

    def __init__(self, command: str, args: list[str]):
        self.command = command
        self.args = args
        cmd_str = f"{command} {' '.join(args)}"
        super().__init__(
            f"\n\n"
            f"  ❌ Servidor MCP no encontrado: '{cmd_str}'\n\n"
            f"  El ejecutable '{command}' no está instalado o no está en el PATH.\n\n"
            f"  SOLUCIONES (elige una):\n\n"
            f"  Opción A — Instalar mcp-clickhouse directamente en el venv:\n"
            f"    .venv\\Scripts\\pip.exe install mcp-clickhouse\n"
            f"    → Luego cambia MCP_SERVER_COMMAND=mcp-clickhouse en .env\n\n"
            f"  Opción B — Instalar uv y usar uvx:\n"
            f"    pip install uv\n"
            f"    → uvx ya estará disponible automáticamente\n\n"
            f"  Opción C — Seguir en MODO DEMO (datos simulados, sin ClickHouse).\n"
            f"    → Desactiva el toggle 'ClickHouse Real' en la interfaz.\n"
        )


# =============================================================================
# DATOS DE DEMOSTRACIÓN (Mock MCP Client)
# =============================================================================
# Para desarrollo y demos sin ClickHouse real, usar MockMCPClient.
# Simula las respuestas del servidor MCP con datos de películas ficticios.

MOCK_CINEMA_DATA = {
    "tickets_por_pais": {
        "data": [
            {"country": "España", "tickets_sold": 2_847_392, "revenue_eur": 22_779_136},
            {"country": "México", "tickets_sold": 4_123_891, "revenue_eur": 30_929_182},
            {"country": "Francia", "tickets_sold": 1_983_441, "revenue_eur": 17_850_969},
            {"country": "Argentina", "tickets_sold": 2_310_007, "revenue_eur": 13_860_042},
            {"country": "Colombia", "tickets_sold": 1_456_233, "revenue_eur": 8_737_398},
        ],
        "meta": {"rows": 5, "execution_time_ms": 42},
    },
    "top_peliculas": {
        "data": [
            {"title": "Galactic Odyssey", "genre": "Sci-Fi", "opening_weekend_m": 187.4},
            {"title": "El Último Horizonte", "genre": "Drama", "opening_weekend_m": 94.2},
            {"title": "Thunder Squad 3", "genre": "Action", "opening_weekend_m": 312.1},
            {"title": "La Mansión de los Susurros", "genre": "Horror", "opening_weekend_m": 67.8},
            {"title": "Amor en Tokio", "genre": "Romance", "opening_weekend_m": 45.3},
        ],
        "meta": {"rows": 5, "execution_time_ms": 38},
    },
    "default": {
        "data": [
            {"metric": "Total tickets Q3 2025", "value": "18,432,000"},
            {"metric": "Revenue total Q3 2025", "value": "€142,800,000"},
            {"metric": "Mercados activos", "value": "47"},
            {"metric": "Películas en cartelera", "value": "183"},
        ],
        "meta": {"rows": 4, "execution_time_ms": 15},
    },
}


class MockMCPClient:
    """
    Cliente MCP simulado para desarrollo y demos sin ClickHouse.

    ÚSALO cuando:
      - No tienes ClickHouse instalado localmente.
      - Estás en una demo y quieres resultados rápidos.
      - Estás desarrollando la UI y el agente sin datos reales.

    En producción, reemplaza por MCPClickHouseClient.
    """

    async def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "run_select_query",
                "description": (
                    "Ejecuta una query SQL SELECT en la base de datos ClickHouse "
                    "de CineMetrics. Retorna filas en formato JSON. "
                    "Tablas disponibles: tickets, movies, campaigns, audiences."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query SQL SELECT válida para ClickHouse",
                        }
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "list_tables",
                "description": "Lista todas las tablas disponibles en la base de datos.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        ]

    async def call_tool(
        self, tool_name: str, tool_args: dict[str, Any]
    ) -> dict[str, Any]:
        """Retorna datos de demo según el contexto de la query."""
        if tool_name == "list_tables":
            return {
                "data": [
                    {"table": "tickets", "rows": "18,432,000", "description": "Ventas de entradas"},
                    {"table": "movies", "rows": "183", "description": "Catálogo de películas"},
                    {"table": "campaigns", "rows": "2,847", "description": "Campañas de marketing"},
                    {"table": "audiences", "rows": "94,210,000", "description": "Datos de audiencia"},
                ]
            }

        if tool_name == "run_select_query":
            query = tool_args.get("query", "").lower()
            if "spain" in query or "españa" in query or "country" in query:
                return MOCK_CINEMA_DATA["tickets_por_pais"]
            elif "movie" in query or "film" in query or "pelicula" in query or "título" in query:
                return MOCK_CINEMA_DATA["top_peliculas"]
            else:
                return MOCK_CINEMA_DATA["default"]

        return {"data": [], "meta": {"rows": 0}}

    async def run_query(self, sql: str) -> dict[str, Any]:
        return await self.call_tool("run_select_query", {"query": sql})


def get_mcp_client(use_mock: bool = False):
    """
    Factory que retorna el cliente MCP apropiado según el entorno.

    Args:
        use_mock: Si True, retorna MockMCPClient (para demos/desarrollo).
                  Si False (default), retorna MCPClickHouseClient (producción).
    """
    if use_mock:
        logger.info("Usando MockMCPClient (modo demo sin ClickHouse real).")
        return MockMCPClient()
    return MCPClickHouseClient()

"""
agent.py - Agente de IA CineMetrics (Gemini Interactions API + MCP ClickHouse)
===============================================================================
Este es el núcleo de la aplicación: un agente de IA que recibe preguntas
en lenguaje natural sobre marketing y audiencias cinematográficas, genera
queries SQL para ClickHouse vía MCP, y formula respuestas amigables.

IMPORTANTE - API DE INTERACCIONES (Interactions API):
======================================================
A partir de google-genai v1.x, la forma correcta de hacer conversaciones
multi-turno y Function Calling es mediante `client.chats.create()`,
NO mediante `client.models.generate_content()`.

Flujo con la Interactions API:
  1. Se crea un chat: client.chats.create(model=..., config=...)
  2. Se envía el mensaje del usuario: chat.send_message(user_query)
  3. Si Gemini responde con FunctionCall → ejecutar herramienta MCP
  4. Se envía el resultado al chat: chat.send_message(FunctionResponse)
  5. Gemini genera la respuesta final en lenguaje natural

REGLA DEL HACKATHON:
====================
⚠️  SOLO se usa Google AI (Gemini). NO se importa openai, anthropic, ni ningún otro SDK.
    SDK usado: google-genai (google.genai)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import google.genai as genai
import google.genai.types as genai_types

from config import get_settings
from mcp_client import get_mcp_client

logger = logging.getLogger(__name__)

# =============================================================================
# PROMPT DE SISTEMA DEL AGENTE
# =============================================================================

SYSTEM_PROMPT = """
Eres CineMetrics AI, un analista de datos experto en marketing cinematográfico
y análisis de audiencias. Trabajas para ejecutivos de estudio que necesitan
insights rápidos sobre el rendimiento de películas y campañas de marketing.

TU ROL:
- Responder preguntas de negocio en lenguaje natural sobre datos de cine.
- Generar queries SQL optimizadas para ClickHouse cuando sea necesario.
- Formular respuestas claras, concisas y accionables para ejecutivos no técnicos.
- Siempre incluir métricas relevantes (porcentajes de cambio, comparativas).

BASE DE DATOS CLICKHOUSE - ESQUEMA:
------------------------------------
Tablas disponibles en la base de datos `cinemetrics`:

1. `tickets` - Ventas de entradas
   - date Date, movie_id UInt32, country LowCardinality(String)
   - region String, tickets_sold UInt64, revenue_eur Decimal, format LowCardinality(String)

2. `movies` - Catálogo de películas
   - movie_id UInt32, title String, genre LowCardinality(String)
   - release_date Date, studio String, director String
   - budget_m Float64, opening_weekend_m Float64

3. `campaigns` - Campañas de marketing
   - campaign_id UInt32, movie_id UInt32, channel String, country String
   - spend_eur Decimal, impressions UInt64, clicks UInt64
   - start_date Date, end_date Date

4. `audiences` - Datos de audiencia
   - date Date, movie_id UInt32, age_group String, gender String
   - country String, viewers UInt64, sentiment_score Float32

REGLAS PARA QUERIES CLICKHOUSE:
---------------------------------
- Usa funciones ClickHouse: toYear(), toMonth(), toQuarter(), formatDateTime()
- Prefiere sum(), avg(), count() con GROUP BY
- Ordena resultados: ORDER BY metric DESC LIMIT 10

ESTILO DE RESPUESTA:
---------------------
- Escribe en español (o el idioma del usuario).
- Comienza con el dato clave más importante.
- Usa emojis con moderación: 🎬 📊 🎟️ 💰 📈 📉
- Finaliza con una recomendación accionable cuando sea relevante.
"""


# =============================================================================
# MODELOS DE DATOS
# =============================================================================

@dataclass
class AgentResponse:
    """Respuesta estructurada del agente de IA."""
    answer: str
    data: list[dict[str, Any]] = field(default_factory=list)
    sql_query: str | None = None
    tool_used: str | None = None
    error: str | None = None


# =============================================================================
# AGENTE PRINCIPAL
# =============================================================================

class CineMetricsAgent:
    """
    Agente de IA que combina Gemini (Interactions API) con herramientas MCP.

    Usa client.chats.create() — la Interactions API de google-genai v1.x —
    para gestionar conversaciones multi-turno y Function Calling de forma
    nativa, sin necesidad de construir manualmente el historial de mensajes.
    """

    def __init__(self, use_mock: bool = False):
        self.settings = get_settings()
        self.use_mock = use_mock

        # Inicializar cliente Google AI
        # ⚠️ REGLA DEL HACKATHON: SOLO google-genai. Nunca openai/anthropic.
        self.client = genai.Client(api_key=self.settings.google_api_key)

        # Normalizar el nombre del modelo: eliminar el prefijo "models/" si existe
        # ya que el SDK lo añade internamente
        model = self.settings.gemini_model
        self.model_id = model.removeprefix("models/")

        logger.info(
            "CineMetricsAgent inicializado. Modelo: %s | Mock: %s",
            self.model_id, use_mock,
        )

    def _build_tools(
        self, mcp_tools: list[dict[str, Any]]
    ) -> list[genai_types.Tool]:
        """Convierte herramientas MCP al formato de Function Declarations de Gemini."""
        declarations = []
        for tool in mcp_tools:
            params = dict(tool.get("parameters", {}))
            # Eliminar keys no soportadas por la API de Gemini
            params.pop("$schema", None)
            params.pop("additionalProperties", None)
            declarations.append(
                genai_types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get("description", ""),
                    parameters=params,
                )
            )
        return [genai_types.Tool(function_declarations=declarations)]

    async def run(self, user_query: str) -> AgentResponse:
        """
        Ejecuta el agente con la pregunta del usuario usando la Interactions API.

        Flujo:
          1. Obtiene herramientas del servidor MCP.
          2. Crea un chat con Gemini (Interactions API).
          3. Envía la pregunta → Gemini puede responder o pedir una FunctionCall.
          4. Si hay FunctionCall → ejecuta en MCP → envía resultado al chat.
          5. Gemini genera la respuesta final.
        """
        mcp_client = get_mcp_client(use_mock=self.use_mock)

        try:
            # ------------------------------------------------------------------
            # PASO 1: Obtener herramientas del servidor MCP
            # ------------------------------------------------------------------
            logger.info("Obteniendo herramientas del servidor MCP...")
            mcp_tools = await mcp_client.list_tools()
            gemini_tools = self._build_tools(mcp_tools)

            # ------------------------------------------------------------------
            # PASO 2: Crear el chat con la Interactions API
            # client.chats.create() gestiona el historial automáticamente
            # ------------------------------------------------------------------
            chat = self.client.chats.create(
                model=self.model_id,
                config=genai_types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=gemini_tools,
                    tool_config=genai_types.ToolConfig(
                        function_calling_config=genai_types.FunctionCallingConfig(
                            mode="AUTO",  # Gemini decide cuándo usar tools
                        )
                    ),
                    temperature=0.2,
                    max_output_tokens=2048,
                ),
            )

            # ------------------------------------------------------------------
            # Helper para reintentar llamadas ante picos de demanda temporales (503 / 429)
            # ------------------------------------------------------------------
            def _send_message_with_retry(msg_payload, retries: int = 3):
                import time
                last_exc = None
                for attempt in range(retries):
                    try:
                        return chat.send_message(msg_payload)
                    except Exception as exc:
                        err_msg = str(exc)
                        if ("503" in err_msg or "UNAVAILABLE" in err_msg or "429" in err_msg) and attempt < retries - 1:
                            wait_sec = (attempt + 1) * 2.0
                            logger.warning(
                                "Gemini API ocupado (intento %d/%d). Reintentando en %.1fs...",
                                attempt + 1, retries, wait_sec
                            )
                            time.sleep(wait_sec)
                            last_exc = exc
                        else:
                            raise exc
                if last_exc:
                    raise last_exc

            # ------------------------------------------------------------------
            # PASO 3: Enviar la pregunta del usuario
            # ------------------------------------------------------------------
            logger.info("Enviando query a Gemini: '%s'", user_query)
            response = _send_message_with_retry(user_query)

            tool_used = None
            sql_query_used = None
            table_data = []

            # ------------------------------------------------------------------
            # PASO 4: Bucle ReAct Multi-Turno (hasta 5 pasos)
            # Permite a Gemini encadenar llamadas a herramientas si es necesario
            # (ej: listar tablas primero y luego ejecutar la consulta SQL)
            # ------------------------------------------------------------------
            max_turns = 5
            curr_turn = 0
            last_tool_result = None

            while curr_turn < max_turns:
                curr_turn += 1
                candidate = response.candidates[0] if response.candidates else None
                if not candidate or not candidate.content:
                    break

                # Buscar FunctionCalls en las partes de la respuesta
                function_call_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        function_call_parts.append(part.function_call)

                if not function_call_parts:
                    # No hay más llamadas a herramientas: Gemini ha terminado
                    break

                # Procesar cada FunctionCall
                response_parts = []
                for fc in function_call_parts:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    logger.info(
                        "Paso %d: Gemini solicita herramienta MCP: '%s' | args: %s",
                        curr_turn, tool_name, tool_args,
                    )

                    if "query" in tool_args:
                        sql_query_used = tool_args["query"]
                        logger.info("SQL generado por Gemini:\n%s", sql_query_used)

                    tool_used = tool_name

                    # Ejecutar en el servidor MCP
                    tool_result = await mcp_client.call_tool(tool_name, tool_args)
                    last_tool_result = tool_result

                    # Extraer datos para la tabla en la UI
                    if isinstance(tool_result, dict) and "data" in tool_result:
                        table_data = tool_result["data"]
                    elif isinstance(tool_result, list) and tool_result:
                        table_data = tool_result

                    tool_result_str = json.dumps(tool_result, ensure_ascii=False)
                    response_parts.append(
                        genai_types.Part(
                            function_response=genai_types.FunctionResponse(
                                name=tool_name,
                                response={"result": tool_result_str},
                            )
                        )
                    )

                # Enviar los resultados de vuelta a Gemini para el siguiente turno
                logger.info("Enviando resultados de herramientas de vuelta al chat...")
                response = _send_message_with_retry(response_parts)


            # ------------------------------------------------------------------
            # PASO 5: Extraer la respuesta textual final
            # ------------------------------------------------------------------
            text_chunks = []
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "text") and part.text:
                        text_chunks.append(part.text)

            answer_text = "".join(text_chunks) if text_chunks else (response.text or "")

            # Fallback si no hay texto pero hubo un error en la herramienta
            if not answer_text and isinstance(last_tool_result, dict) and "error" in last_tool_result:
                answer_text = (
                    f"⚠️ **Error en ClickHouse:** {last_tool_result['error']}\n\n"
                    "*Sugerencia:* Si no dispones de un servidor ClickHouse en ejecución, desactiva la casilla 'ClickHouse Real' para operar con datos de muestra en Modo Demo."
                )

            return AgentResponse(
                answer=answer_text,
                data=table_data,
                sql_query=sql_query_used,
                tool_used=tool_used,
            )

        except Exception as e:
            from mcp_client import extract_clean_error_message
            clean_error = extract_clean_error_message(e)
            logger.exception("Error en CineMetricsAgent: %s", clean_error)
            return AgentResponse(
                answer=(
                    f"⚠️ **Error al procesar la consulta**\n\n"
                    f"{clean_error}\n\n"
                    f"*Tip:* Si no tienes una base de datos ClickHouse local iniciada, desactiva la casilla **'ClickHouse Real'** para consultar los datos simulados en Modo Demo."
                ),
                error=clean_error,
            )


# =============================================================================
# WRAPPER SÍNCRONO PARA STREAMLIT
# =============================================================================

def run_agent_sync(user_query: str, use_mock: bool = False) -> AgentResponse:
    """
    Wrapper síncrono del agente asíncrono para uso en Streamlit.

    Ejecuta el agente en un thread dedicado con un nuevo event loop aislado,
    garantizando que no interfiera con el loop interno de Streamlit y
    capturando limpiamente cualquier ExceptionGroup / TaskGroup de AnyIO.
    """
    import concurrent.futures
    from mcp_client import extract_clean_error_message

    def _run_in_new_loop() -> AgentResponse:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            agent = CineMetricsAgent(use_mock=use_mock)
            return loop.run_until_complete(agent.run(user_query))
        finally:
            try:
                # Cancelar tareas pendientes antes de cerrar el loop
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            loop.close()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_in_new_loop)
            return future.result(timeout=120)
    except Exception as e:
        clean_error = extract_clean_error_message(e)
        logger.exception("Error capturado en run_agent_sync: %s", clean_error)
        return AgentResponse(
            answer=(
                f"⚠️ **Error al procesar la consulta**\n\n"
                f"{clean_error}\n\n"
                f"*Sugerencia:* Si no dispones de un servidor ClickHouse activo en tu máquina, "
                f"desactiva la casilla **'ClickHouse Real'** para operar con datos de muestra en Modo Demo."
            ),
            error=clean_error,
        )


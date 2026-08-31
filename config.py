"""
config.py - Configuración centralizada de CineMetrics AI
=========================================================
Carga y valida todas las variables de entorno usando Pydantic Settings.
Este es el único lugar donde se leen las variables de entorno en la app.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta al directorio raíz del proyecto (donde está este archivo).
# CRÍTICO: Pydantic-settings usa ruta relativa al CWD por defecto, lo que
# falla cuando Streamlit ejecuta el script desde otro directorio.
# Usar Path(__file__).parent garantiza que siempre se encuentre el .env.
PROJECT_ROOT = Path(__file__).parent.resolve()
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Configuración de la aplicación validada por Pydantic.
    Los valores se leen automáticamente desde el archivo .env
    o desde las variables de entorno del sistema.

    Orden de prioridad (de mayor a menor):
      1. Variables de entorno del sistema (os.environ)
      2. Archivo .env en la raíz del proyecto
      3. Valores por defecto definidos con Field(default=...)
    """

    # -------------------------------------------------------------------------
    # Google AI (OBLIGATORIO - Regla #1 del hackathon: SOLO Google AI)
    # -------------------------------------------------------------------------
    # Nota: default="" en lugar de ... (requerido) para que Pydantic no lance
    # un ValidationError críptico cuando falta el .env. En su lugar, el
    # field_validator abajo lanza un mensaje de error claro y útil.
    google_api_key: str = Field(
        default="",
        description="API Key de Google AI Studio para acceder a Gemini",
    )
    gemini_model: str = Field(
        default="gemini-3.5-flash",
        description="Identificador del modelo Gemini a usar (sin prefijo 'models/')",
    )

    # -------------------------------------------------------------------------
    # ClickHouse (para el servidor MCP)
    # -------------------------------------------------------------------------
    clickhouse_host: str = Field(default="localhost")
    clickhouse_port: int = Field(default=8123)
    clickhouse_user: str = Field(default="default")
    clickhouse_password: str = Field(default="")
    clickhouse_database: str = Field(default="cinemetrics")
    clickhouse_use_ssl: bool = Field(default=False)

    # -------------------------------------------------------------------------
    # MCP Server (cómo lanzar el servidor mcp-clickhouse como subproceso)
    # El servidor MCP se ejecuta localmente como un proceso stdio.
    # La librería `mcp` de Python levanta este subproceso y se comunica
    # con él mediante stdin/stdout usando el protocolo JSON-RPC de MCP.
    # -------------------------------------------------------------------------
    mcp_server_command: str = Field(
        default="uvx",
        description="Comando para lanzar el servidor MCP (uvx o npx)",
    )
    mcp_server_args: str = Field(
        default="mcp-clickhouse",
        description="Argumentos del comando MCP (nombre del paquete)",
    )

    # -------------------------------------------------------------------------
    # Aplicación
    # -------------------------------------------------------------------------
    app_title: str = Field(default="CineMetrics AI")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # -------------------------------------------------------------------------
    # Configuración de pydantic-settings
    # IMPORTANTE: env_file debe ser una ruta ABSOLUTA para que funcione
    # correctamente cuando Streamlit cambia el directorio de trabajo.
    # -------------------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),   # ← Ruta absoluta, no relativa
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",                # Ignorar vars de entorno no declaradas
    )

    @field_validator("google_api_key")
    @classmethod
    def api_key_must_be_configured(cls, v: str) -> str:
        """
        Valida que la API key esté configurada.
        Da un mensaje de error claro y accionable en lugar del genérico de Pydantic.
        """
        if not v or v.strip() in ("", "your_google_api_key_here"):
            env_path = ENV_FILE_PATH
            raise ValueError(
                f"\n\n"
                f"  ❌ GOOGLE_API_KEY no está configurada.\n\n"
                f"  Pasos para solucionarlo:\n"
                f"    1. Abre el archivo: {env_path}\n"
                f"    2. Reemplaza 'your_google_api_key_here' con tu API Key real.\n"
                f"    3. Obtén tu clave gratis en: https://aistudio.google.com/app/apikey\n"
                f"    4. Reinicia la aplicación.\n"
            )
        return v.strip()

    @property
    def is_configured(self) -> bool:
        """Retorna True si la configuración mínima está completa."""
        return bool(self.google_api_key and self.google_api_key != "your_google_api_key_here")

    @property
    def mcp_server_args_list(self) -> list[str]:
        """Convierte el string de args MCP en una lista para subprocess."""
        return self.mcp_server_args.split()

    @property
    def clickhouse_env(self) -> dict[str, str]:
        """
        Variables de entorno que necesita el proceso `mcp-clickhouse`.
        El servidor MCP de ClickHouse lee su config desde variables de entorno,
        no desde argumentos de línea de comandos.
        Ref: https://github.com/ClickHouse/mcp-clickhouse#configuration
        """
        return {
            **os.environ,  # Heredar el entorno actual
            "CLICKHOUSE_HOST": self.clickhouse_host,
            "CLICKHOUSE_PORT": str(self.clickhouse_port),
            "CLICKHOUSE_USER": self.clickhouse_user,
            "CLICKHOUSE_PASSWORD": self.clickhouse_password,
            "CLICKHOUSE_DATABASE": self.clickhouse_database,
            "CLICKHOUSE_SECURE": str(self.clickhouse_use_ssl).lower(),
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Retorna la instancia de Settings (singleton con caché).
    Usar esta función en lugar de instanciar Settings directamente
    garantiza que el .env se lee solo una vez.
    """
    return Settings()


def get_settings_safe() -> tuple[Settings | None, str | None]:
    """
    Versión segura de get_settings() que captura errores de configuración.
    Úsala en la UI para mostrar mensajes amigables en lugar de crashear.

    Returns:
        (settings, None)       → Todo bien
        (None, error_message)  → Falta configuración
    """
    try:
        return get_settings(), None
    except Exception as e:
        # Limpiar el mensaje de error de Pydantic para mostrarlo en la UI
        msg = str(e)
        # Extraer solo la parte relevante del ValidationError
        if "Value error," in msg:
            msg = msg.split("Value error,")[-1].strip()
        elif "validation error" in msg.lower():
            msg = msg
        return None, msg

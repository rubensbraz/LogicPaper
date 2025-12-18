import logging
import os
from typing import List, Union

from pydantic import AnyHttpUrl, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Setup Logging Inicial
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("LogicPaper")


class Settings(BaseSettings):
    """
    Central Configuration using Pydantic Settings.
    Reads from environment variables and .env file.
    """

    # --- Meta ---
    PROJECT_NAME: str = "LogicPaper"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # --- Security ---
    LOGICPAPER_API_KEY: str
    ALLOWED_ORIGINS: Union[str, List[AnyHttpUrl]] = "*"

    @field_validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # --- Paths ---
    # Base dir is calculated relative to this file
    BASE_DIR: str = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )

    TEMP_DIR: str = "/data/temp"
    PERSISTENT_TEMPLATES_DIR: str = os.path.join(BASE_DIR, "persistent_templates")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")

    # --- Logic ---
    CLEANUP_INTERVAL_SECONDS: int = 3600
    DEFAULT_LOCALE: str = "pt_BR"
    
    # --- System ---
    TIMEZONE: str = Field(alias="TZ", default="UTC")

    # Pydantic Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignores extra variables in .env that aren't listed here
    )

    def create_dirs(self):
        """Ensures critical directories exist at startup."""
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.PERSISTENT_TEMPLATES_DIR, exist_ok=True)
        logger.info(
            f"FileSystem Check: Temp={self.TEMP_DIR}, Persistent={self.PERSISTENT_TEMPLATES_DIR}"
        )


# Global Instance (Singleton)
settings = Settings()

# Execute directory creation immediately
settings.create_dirs()

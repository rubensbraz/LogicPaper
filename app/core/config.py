import logging
import os
from pathlib import Path
from typing import List, Union

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setup Logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("LogicPaper")


class Settings(BaseSettings):
    """Central Configuration using Pydantic Settings.

    This class manages all application configuration by reading from environment
    variables and the .env file. It provides type-safe access to configuration
    values with validation and default values.

    Attributes are organized into logical groups: Meta, Security, Filesystem,
    External Tools, Worker/Jobs, Localization, and Data Layer.
    """

    # --- App Info ---
    PROJECT_NAME: str = "LogicPaper"
    VERSION: str = "1.4.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # --- Security ---
    LOGICPAPER_API_KEY: str
    ALLOWED_ORIGINS: Union[str, List[AnyHttpUrl]] = "*"

    @field_validator("ALLOWED_ORIGINS")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parses and validates the CORS configuration.

        Accepts either a comma-separated string of origins or a list of URLs.
        Supports wildcard "*" for allowing all origins (not recommended for production).

        Args:
            v: The raw value from environment variables. Can be:
                - A comma-separated string: "http://localhost:3000,https://example.com"
                - A list of URLs: ["http://localhost:3000", "https://example.com"]
                - A wildcard: "*"

        Returns:
            A list of allowed origin URLs or the wildcard string "*".

        Raises:
            ValueError: If the format is invalid or cannot be parsed.

        Example:
            >>> assemble_cors_origins("http://localhost:3000,https://example.com")
            ["http://localhost:3000", "https://example.com"]
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(f"Invalid CORS origins format: {v}")

    # --- Filesystem ---
    BASE_DIR: Path = Path(__file__).resolve().parents[2]
    TEMP_DIR: str = "/data/temp"
    PERSISTENT_TEMPLATES_DIR: str = os.path.join(BASE_DIR, "persistent_templates")
    STATIC_DIR: str = os.path.join(BASE_DIR, "static")

    # Directory Naming Conventions
    DIR_INPUTS_NAME: str = "1 Input documents"
    DIR_OUTPUTS_NAME: str = "2 Generated documents"
    DIR_ASSETS_NAME: str = ".temp_assets"

    # Internal File Paths
    OFFICE_THUMBNAIL_PATH: str = "docProps/thumbnail.jpeg"

    # --- External Tools ---
    LIBREOFFICE_BINARY: str = "soffice"
    LIBREOFFICE_TIMEOUT: int = 1800  # 30 minutes

    # --- Worker / Jobs ---
    CLEANUP_INTERVAL_SECONDS: int = 3600  # 1 hour

    # --- Localization ---
    DEFAULT_LOCALE: str = "pt_BR"
    TIMEZONE: str = Field(alias="TZ", default="UTC")

    # --- Data Layer (Redis) ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_JOB_TTL: int = 86400  # 24 hours
    REDIS_MAX_RETRIES: int = 5
    REDIS_RETRY_DELAY: int = 2  # seconds
    REDIS_LOG_CHANNEL_PREFIX: str = "logs:"

    # Pydantic Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignores extra variables in .env that aren't listed here
    )

    def create_dirs(self) -> None:
        """Ensures critical directories exist at startup.

        Creates the temporary directory and persistent templates directory
        if they don't already exist. This is an infrastructure concern that
        should ideally be called during application startup rather than
        during configuration initialization.

        Note:
            This method performs I/O operations and should be moved to the
            application startup sequence in main.py for better separation
            of concerns.
        """
        os.makedirs(self.TEMP_DIR, exist_ok=True)
        os.makedirs(self.PERSISTENT_TEMPLATES_DIR, exist_ok=True)
        logger.info(
            f"FileSystem Check: Temp={self.TEMP_DIR}, Persistent={self.PERSISTENT_TEMPLATES_DIR}"
        )


# Global Settings Instance (Singleton Pattern)
# This instance is created once and imported throughout the application
settings = Settings()

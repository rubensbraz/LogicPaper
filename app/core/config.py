import logging
import os


# --- Constants & Configuration ---

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.getenv("TEMP_DIR", "/data/temp")
STATIC_DIR = os.path.join(BASE_DIR, "static")
PERSISTENT_TEMPLATES_DIR = os.path.join(BASE_DIR, "persistent_templates")
API_KEY = os.getenv("LOGICPAPER_API_KEY", "secret-key")

# Create necessary directories
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(PERSISTENT_TEMPLATES_DIR, exist_ok=True)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("LogicPaper")

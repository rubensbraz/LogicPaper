import logging
import os
import shutil
import time
import zipfile

from apscheduler.schedulers.background import BackgroundScheduler


# Configure Logging
logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """Removes risky characters from filenames."""
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c in (" ", ".", "_", "-")]
    ).rstrip()


def extract_zip(zip_path: str, extract_to: str):
    """Extract ZIP files."""
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def cleanup_job(temp_dir: str, max_age_seconds: int = 3600):
    """
    Deletes folders older than max_age_seconds.
    """
    logger.info("Running Cleanup Job...")
    now = time.time()
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        if os.path.isdir(file_path):
            # Check creation time
            if os.stat(file_path).st_mtime < now - max_age_seconds:
                shutil.rmtree(file_path)
                logger.info(f"Deleted old session: {filename}")


def start_scheduler(temp_dir: str):
    """Start scheduler for cleaning old files."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_job, "interval", minutes=10, args=[temp_dir])
    scheduler.start()

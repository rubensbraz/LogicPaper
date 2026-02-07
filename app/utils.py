import os
import shutil
import time
import zipfile

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import logger, settings


def sanitize_filename(filename: str) -> str:
    """Removes risky characters from filenames.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    return "".join(
        [c for c in filename if c.isalpha() or c.isdigit() or c in (" ", ".", "_", "-")]
    ).rstrip()


def extract_zip(zip_path: str, extract_to: str):
    """Extract ZIP files.

    Args:
        zip_path (str): Path to the zip file.
        extract_to (str): Directory to extract to.
    """
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


def cleanup_job(
    temp_dir: str, max_age_seconds: int = settings.CLEANUP_INTERVAL_SECONDS
):
    """Deletes folders older than max_age_seconds.

    Args:
        temp_dir (str): The temporary directory path.
        max_age_seconds (int): The max age in seconds. Defaults to configured interval.
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


def start_scheduler(
    temp_dir: str, interval_seconds: int = settings.CLEANUP_INTERVAL_SECONDS
):
    """Start scheduler for cleaning old files.

    Args:
        temp_dir (str): The temporary directory path.
        interval_seconds (int): Cleanup interval in seconds. Defaults to configured interval.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_job,
        "interval",
        seconds=interval_seconds,
        args=[temp_dir, interval_seconds],
    )
    scheduler.start()
    logger.info(f"Scheduler started. Cleanup every {interval_seconds}s.")

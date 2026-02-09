import io
import json
import os
import shutil
import time
import zipfile
from typing import Optional

import anyio
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import UploadFile

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


def extract_zip(zip_path: str, extract_to: str) -> None:
    """Extracts a ZIP archive to a specified directory.

    Args:
        zip_path (str): The absolute path to the zip file.
        extract_to (str): The target directory for extraction.

    Raises:
        zipfile.BadZipFile: If the file is not a valid ZIP archive.
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


async def load_dataframe(
    file_excel: Optional[UploadFile] = None, file_json: Optional[UploadFile] = None
) -> pd.DataFrame:
    """Loads data from either Excel or JSON into a Pandas DataFrame.

    Runs blocking Pandas operations in a separate thread.

    Args:
        file_excel (Optional[UploadFile]): The uploaded Excel file. Defaults to None.
        file_json (Optional[UploadFile]): The uploaded JSON file. Defaults to None.

    Returns:
        pd.DataFrame: The loaded data as a DataFrame.

    Raises:
        ValueError: If no file is provided or if parsing fails.
    """
    if not file_excel and not file_json:
        raise ValueError("No data source provided. Please upload Excel or JSON.")

    # Handle Excel
    if file_excel:
        try:
            contents = await file_excel.read()
            await file_excel.seek(0)

            # Offload blocking pandas.read_excel
            return await anyio.to_thread.run_sync(
                lambda: pd.read_excel(io.BytesIO(contents), header=0)
            )
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")

    # Handle JSON
    if file_json:
        try:
            contents = await file_json.read()
            await file_json.seek(0)

            def _parse_json(c):
                """Parses JSON content and normalizes it to a DataFrame."""
                data = json.loads(c)
                # Case A: Single Dictionary -> Wrap in list
                if isinstance(data, dict):
                    data = [data]
                # Case B: List of Dictionaries (Standard)
                elif isinstance(data, list):
                    if not all(isinstance(i, dict) for i in data):
                        raise ValueError(
                            "JSON list must contain objects (key-value pairs)."
                        )
                else:
                    raise ValueError("JSON must be an Object or a List of Objects.")

                return pd.json_normalize(data)

            # Offload blocking JSON parsing and normalization
            return await anyio.to_thread.run_sync(_parse_json, contents)

        except json.JSONDecodeError:
            raise ValueError("Invalid JSON file format.")
        except Exception as e:
            raise ValueError(f"Error parsing JSON data: {str(e)}")

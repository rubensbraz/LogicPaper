import os
import shutil
from typing import Optional

import pandas as pd

from app.core.config import settings, logger
from app.integration.state import job_store
from app.core.batch import process_batch_core


async def run_headless_generation(
    job_id: str,
    df: pd.DataFrame,
    template_path: str,
    session_path: str,
    dir_outputs: str,
    dir_assets: str,
    to_pdf: bool,
    filename_col: Optional[str],
    group_folders: bool,
) -> None:
    """
    Background worker function. Uses the shared 'process_batch_core'.

    Args:
        job_id (str): The unique Job ID.
        df (pd.DataFrame): The data to process.
        template_path (str): Full path to the template file in the temp input dir.
        session_path (str): Root directory for this job session.
        dir_outputs (str): Directory to save generated files.
        dir_assets (str): Directory for temporary assets.
        to_pdf (bool): Whether to convert outputs to PDF.
        filename_col (Optional[str]): Column name for output filenames.
        group_folders (bool): Whether to group outputs in folders.
    """
    try:
        # Define a simplified callback for logging
        def worker_log(msg: str):
            logger.info(f"[Job {job_id}] {msg}")

        # The Core expects a list of templates, so we wrap the single path
        template_paths = [template_path]

        # Call Core
        result = await process_batch_core(
            session_id=job_id,
            df=df,
            template_paths=template_paths,
            session_path=session_path,
            dir_outputs=dir_outputs,
            dir_assets=dir_assets,
            to_pdf=to_pdf,
            filename_col=filename_col,
            group_folders=group_folders,
            log_callback=worker_log,
        )

        # Create Result ZIP
        zip_base = os.path.join(settings.TEMP_DIR, f"{job_id}_result")
        shutil.make_archive(zip_base, "zip", dir_outputs)

        # Update State: Completed
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["files_generated"] = result["total_files"]
        job_store[job_id]["download_url"] = f"/api/v1/integration/download/{job_id}"

        logger.info(f"Job {job_id} finished. Files: {result['total_files']}")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)

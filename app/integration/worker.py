from datetime import datetime
from typing import Any, Dict, List, Optional

import anyio
import pandas as pd

from app.core.config import logger, settings
from app.core.reporter import generate_styled_report
from app.core.service import BatchService
from app.integration.sse import send_log, send_log_event
from app.integration.state import RedisJobRepository


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
    batch_service: BatchService,
    job_repository: RedisJobRepository,
) -> None:
    """Background worker function for document generation.

    Orchestrates the batch processing using the `BatchService`, manages result
    archiving, and updates job status in the repository.

    Args:
        job_id (str): The unique Job ID.
        df (pd.DataFrame): The data to process.
        template_path (str): Absolute path to the template file in the inputs directory.
        session_path (str): Root directory for this job session.
        dir_outputs (str): Directory where generated files should be saved.
        dir_assets (str): Directory for temporary assets.
        to_pdf (bool): Whether to convert outputs to PDF.
        filename_col (Optional[str]): Column name for dynamic output filenames.
        group_folders (bool): Whether to group outputs in folders.
        batch_service (BatchService): The injected batch service instance.
        job_repository (RedisJobRepository): The injected job repository instance.
    """
    try:
        # Define a simplified callback for logging
        def worker_log(msg: str):
            """Sends a log message with the job ID prefix."""
            logger.info(f"[Job {job_id}] {msg}")

        # The Core expects a list of templates, so we wrap the single path
        template_paths = [template_path]

        # Call Core via Service
        result = await batch_service.process_batch(
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
        zip_base = batch_service.storage.join_path(
            settings.TEMP_DIR, f"{job_id}_result"
        )
        # Offload blocking zip
        await anyio.to_thread.run_sync(
            batch_service.storage.create_zip, dir_outputs, zip_base
        )

        # Update State: Completed
        job_repository.update_status(
            job_id,
            status="completed",
            files_generated=result["total_files"],
            download_url=f"/api/v1/integration/download/{job_id}",
        )

        logger.info(f"Job {job_id} finished. Files: {result['total_files']}")

    except Exception as e:
        job_repository.update_status(job_id, status="failed", error=str(e))


async def background_batch_processor(
    session_id: str,
    df: pd.DataFrame,
    saved_template_paths: List[str],
    session_path: str,
    dir_outputs: str,
    dir_assets_internal: str,
    output_pdf: bool,
    filename_col: str,
    group_by_folders: bool,
    input_manifest: Dict[str, Any],
    batch_service: BatchService,
    job_repository: RedisJobRepository,
):
    """Background task to process the batch, generate report, and zip.

    Args:
        session_id (str): The session ID.
        df (pd.DataFrame): The DataFrame containing data.
        saved_template_paths (List[str]): List of paths to saved templates.
        session_path (str): The session directory path.
        dir_outputs (str): The output directory path.
        dir_assets_internal (str): The internal assets directory path.
        output_pdf (bool): Whether to convert to PDF.
        filename_col (str): The column used for filenames.
        group_by_folders (bool): Whether to group by folders.
        input_manifest (Dict[str, Any]): The input manifest.
        batch_service (BatchService): The batch service instance.
        job_repository (RedisJobRepository): The job repository instance.
    """
    try:
        start_time = datetime.now()
        send_log_event(session_id, "task_started", {"count": len(df)})

        # Define callback wrapper for SSE
        def sse_callback(msg: str):
            """Bridge callback to send logs via SSE."""
            send_log(session_id, msg)

        # Execute Core batch logic via Service
        batch_result = await batch_service.process_batch(
            session_id=session_id,
            df=df,
            template_paths=saved_template_paths,
            session_path=session_path,
            dir_outputs=dir_outputs,
            dir_assets=dir_assets_internal,
            to_pdf=output_pdf,
            filename_col=filename_col,
            group_folders=group_by_folders,
            log_callback=sse_callback,
        )

        # Cleanup & Report
        if batch_service.storage.exists(dir_assets_internal):
            batch_service.storage.delete(dir_assets_internal)

        end_time = datetime.now()
        duration = end_time - start_time

        metadata = {
            "session_id": session_id,
            "start_time": start_time,
            "duration": duration,
            "total_rows": batch_result["total_rows"],
            "total_files": batch_result["total_files"],
            "success_rate": (
                (batch_result["success_rows"] / batch_result["total_rows"] * 100)
                if batch_result["total_rows"] > 0
                else 0
            ),
        }

        report_path = batch_service.storage.join_path(session_path, "job_report.xlsx")

        # Offload blocking Excel generation
        report_bytes = await anyio.to_thread.run_sync(
            generate_styled_report,
            batch_result["report"],
            metadata,
            input_manifest,
        )

        # Offload blocking write
        await anyio.to_thread.run_sync(
            batch_service.storage.write_binary, report_path, report_bytes
        )

        zip_base_name = batch_service.storage.join_path(
            settings.TEMP_DIR, f"{session_id}_result"
        )

        # Offload blocking zip
        await anyio.to_thread.run_sync(
            batch_service.storage.create_zip, session_path, zip_base_name
        )

        send_log_event(session_id, "process_complete")

        # Persistence: Update State (Completed)
        job_repository.update_status(
            session_id,
            status="completed",
            duration=str(duration),
            files_generated=batch_result["total_files"],
            download_url=f"/api/v1/integration/download/{session_id}",
        )

    except Exception as e:
        logger.error(f"Critical Batch Background Error: {e}")
        send_log_event(session_id, "process_error", {"error": str(e)})

        # Persistence: Update State (Failed)
        job_repository.update_status(session_id, status="failed", error=str(e))

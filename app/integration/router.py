import base64
import os
import uuid
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Security
from fastapi.responses import FileResponse

from app.core.config import logger, settings
from app.core.ports import StoragePort
from app.core.service import BatchService
from app.dependencies import get_batch_service, get_job_repository, get_storage_port
from app.integration.schemas import GenerationRequest, JobStatusResponse
from app.integration.security import get_api_key
from app.integration.state import RedisJobRepository
from app.integration.worker import run_headless_generation

# Router
router = APIRouter()


@router.post(
    "/generate",
    response_model=JobStatusResponse,
    summary="Start Document Generation Job",
    description="""
    Initiates an asynchronous document generation process.
    
    **Features:**
    - Supports **DOCX**, **PPTX**, **PDF**, **MD**, and **TXT** output formats.
    - Accepts a **list of data rows** (JSON) to generate multiple documents in batch.
    - Allows **dynamic image replacement** via a Base64-encoded ZIP file containing assets.
    - Returns a `job_id` immediately, allowing the client to poll for status.
    """,
    responses={
        200: {"description": "Job successfully queued."},
        403: {"description": "Access denied (e.g., Invalid template path traversal)."},
        404: {"description": "Template file not found."},
        500: {"description": "Internal server error during job initialization."},
    },
)
async def trigger_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
    batch_service: BatchService = Depends(get_batch_service),
    job_repository: RedisJobRepository = Depends(get_job_repository),
    storage: StoragePort = Depends(get_storage_port),
):
    """Trigger a document generation job via API.

    Validates inputs, sets up a temporary session workspace, and dispatches
    a background task to process the generation. Supports dynamic asset replacement
    via Base64 ZIP upload.

    Args:
        request (GenerationRequest): The request payload containing data and options.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks handler.
        api_key (str): Valid API Key.
        batch_service (BatchService): The domain service for batch processing.
        job_repository (RedisJobRepository): Repository for job state persistence.

    Returns:
        JobStatusResponse: The initial status of the created job.

    Raises:
        HTTPException: If the template path is invalid or authentication fails.
    """
    # Security & Path Validation
    base_dir = storage.join_path(
        settings.PERSISTENT_TEMPLATES_DIR
    )  # Ensure abstract path

    # Resolve and sanitize target path
    safe_template_input = (
        request.template_path.replace("..", "").lstrip("/").lstrip("\\")
    )
    target_path = storage.join_path(base_dir, safe_template_input)

    # Security Check: Ensure the resolved path is actually inside the base directory
    if not storage.is_safe_path(base_dir, target_path):
        logger.warning(
            f"SECURITY ALERT: Path traversal attempt. "
            f"Input: '{request.template_path}' | Resolved: '{target_path}'"
        )
        raise HTTPException(
            status_code=403, detail="Access denied: Invalid template path."
        )

    if not storage.exists(target_path):
        raise HTTPException(
            status_code=404, detail=f"Template not found: {request.template_path}"
        )

    # Initialize Session
    job_id = f"job_{uuid.uuid4().hex}"
    session_path = storage.join_path(settings.TEMP_DIR, job_id)

    dir_inputs = storage.join_path(session_path, settings.DIR_INPUTS_NAME)
    dir_outputs = storage.join_path(session_path, settings.DIR_OUTPUTS_NAME)
    dir_assets = storage.join_path(session_path, settings.DIR_ASSETS_NAME)

    for p in [dir_inputs, dir_outputs, dir_assets]:
        storage.make_dir(p)

    try:
        template_filename = storage.basename(target_path)
        dest_template_path = storage.join_path(dir_inputs, template_filename)
        storage.copy(target_path, dest_template_path)

        # Handle Assets (Base64 ZIP)
        if request.assets_base64:
            try:
                zip_path = storage.join_path(dir_inputs, "assets.zip")
                decoded_assets = base64.b64decode(request.assets_base64)
                storage.write_binary(zip_path, decoded_assets)
                storage.extract_zip(zip_path, dir_assets)
                logger.info(f"Assets extracted for Job {job_id}")
            except Exception as e:
                logger.error(f"Failed to process assets_base64 for Job {job_id}: {e}")
                # We log but do not fail the job immediately, though assets might be missing
                # Alternatively, we could raise an 400 error here
                pass

        df = pd.json_normalize(request.data)

        initial_state = {
            "status": "processing",
            "start_time": datetime.now().isoformat(),
            "path": session_path,
        }
        job_repository.save(job_id, initial_state)

        # Dispatch Background Task
        background_tasks.add_task(
            run_headless_generation,
            job_id,
            df,
            dest_template_path,
            session_path,
            dir_outputs,
            dir_assets,
            request.output_format == "pdf",
            request.filename_col,
            request.group_by_folders,
            batch_service,
            job_repository,
        )

        return {
            "job_id": job_id,
            "status": "processing",
            "message": "Job initiated successfully.",
        }

    except Exception as e:
        logger.error(f"Error initiating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status",
    description="Polls the status of a specific background job. Returns the current state (processing, completed, failed) and a download URL if finished.",
    responses={
        200: {"description": "Status retrieved successfully."},
        404: {"description": "Job ID not found (expired or invalid)."},
    },
)
async def check_job_status(
    job_id: str,
    api_key: str = Security(get_api_key),
    job_repository: RedisJobRepository = Depends(get_job_repository),
):
    """Polls the status of a specific generation job.

    Args:
        job_id (str): The unique job identifier.
        api_key (str): Valid API Key.
        job_repository (RedisJobRepository): Repository for job state persistence.

    Returns:
        JobStatusResponse: The current status and metadata of the job.

    Raises:
        HTTPException: If the job ID is not found in the repository.
    """
    job = job_repository.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    return {
        "job_id": job_id,
        "status": job["status"],
        "download_url": job.get("download_url"),
        "message": (
            job.get("error")
            if job["status"] == "failed"
            else "Processing..."
            if job["status"] == "processing"
            else "Completed"
        ),
        "statistics": {"files": job.get("files_generated", 0)},
    }


@router.get(
    "/download/{job_id}",
    summary="Download Job Result",
    description="Downloads the final ZIP file containing all generated documents. The file is available only after the job status is 'completed'.",
    responses={
        200: {"description": "ZIP file stream.", "content": {"application/zip": {}}},
        400: {"description": "Job is still processing or failed."},
        404: {"description": "File expired or not found."},
    },
)
async def download_integration_result(
    job_id: str,
    api_key: str = Security(get_api_key),
    job_repository: RedisJobRepository = Depends(get_job_repository),
):
    """Downloads the final ZIP file for a completed job.

    Args:
        job_id (str): The unique job identifier.
        api_key (str): Valid API Key.
        job_repository (RedisJobRepository): Repository for job state persistence.

    Returns:
        FileResponse: The ZIP file stream.

    Raises:
        HTTPException: If the job is not completed or the file is missing/expired.
    """
    file_path = os.path.join(settings.TEMP_DIR, f"{job_id}_result.zip")

    if not os.path.exists(file_path):
        job = job_repository.get(job_id)
        if job and job["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"File not ready. Current status: {job['status']}",
            )
        raise HTTPException(status_code=404, detail="File expired or not found.")

    return FileResponse(
        path=file_path, filename=f"Result_{job_id}.zip", media_type="application/zip"
    )

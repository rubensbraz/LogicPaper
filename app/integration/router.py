import os
import shutil
import uuid
from datetime import datetime

import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Security, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings, logger
from app.integration.schemas import GenerationRequest, JobStatusResponse
from app.integration.security import get_api_key
from app.integration.worker import run_headless_generation
from app.integration.state import JobRepository


router = APIRouter()


@router.post(
    "/generate",
    response_model=JobStatusResponse,
    summary="Trigger Document Generation",
    description="Accepts JSON data and a template path to start an async generation job.",
)
async def trigger_generation(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Security(get_api_key),
):
    """
    Endpoint for system-to-system integration.
    """
    # 1. Security & Validation: Path Traversal Prevention

    # Resolve the absolute path of the persistent storage
    base_dir = os.path.abspath(settings.PERSISTENT_TEMPLATES_DIR)

    # Sanitize user input (remove leading slashes to prevent absolute path override) and join with base directory
    safe_template_input = request.template_path.lstrip(os.sep)
    target_path = os.path.abspath(os.path.join(base_dir, safe_template_input))

    # Security Check: Ensure the resolved path is actually INSIDE the base directory
    # os.path.commonpath returns the longest common sub-path.
    # If the target is valid, the common path must be equal to the base_dir
    try:
        common = os.path.commonpath([base_dir, target_path])
    except ValueError:
        # Happens on Windows if paths are on different drives
        common = ""

    if common != base_dir:
        logger.warning(
            f"SECURITY ALERT: Path traversal attempt detected. "
            f"Input: '{request.template_path}' | Resolved: '{target_path}'"
        )
        raise HTTPException(
            status_code=403, detail="Access denied: Invalid template path."
        )

    # Existence Check
    if not os.path.exists(target_path):
        raise HTTPException(
            status_code=404, detail=f"Template not found: {request.template_path}"
        )

    # 2. Initialize Session
    job_id = f"job_{uuid.uuid4().hex}"
    session_path = os.path.join(settings.TEMP_DIR, job_id)

    dir_inputs = os.path.join(session_path, "inputs")
    dir_outputs = os.path.join(session_path, "outputs")
    dir_assets = os.path.join(session_path, ".temp_assets")

    for p in [dir_inputs, dir_outputs, dir_assets]:
        os.makedirs(p, exist_ok=True)

    try:
        # 3. Prepare Inputs
        template_filename = os.path.basename(target_path)
        dest_template_path = os.path.join(dir_inputs, template_filename)
        shutil.copy2(target_path, dest_template_path)

        # Convert JSON to DataFrame
        df = pd.json_normalize(request.data)

        # Initialize Job State
        initial_state = {
            "status": "processing",
            "start_time": datetime.now(),
            "path": session_path,
        }
        JobRepository.save(job_id, initial_state)

        # 4. Dispatch Background Task
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
    "/status/{job_id}", response_model=JobStatusResponse, summary="Check Job Status"
)
async def check_job_status(job_id: str, api_key: str = Security(get_api_key)):
    """
    Polls the status of a specific generation job.
    """
    job = JobRepository.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    return {
        "job_id": job_id,
        "status": job["status"],
        "download_url": job.get("download_url"),
        "message": (
            job.get("error")
            if job["status"] == "failed"
            else "Processing..." if job["status"] == "processing" else "Completed"
        ),
        "statistics": {"files": job.get("files_generated", 0)},
    }


@router.get("/download/{job_id}", summary="Download Result ZIP")
async def download_integration_result(
    job_id: str, api_key: str = Security(get_api_key)
):
    """
    Downloads the final ZIP file. Requires authentication.
    """
    file_path = os.path.join(settings.TEMP_DIR, f"{job_id}_result.zip")

    if not os.path.exists(file_path):
        job = JobRepository.get(job_id)
        if job and job["status"] != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"File not ready. Current status: {job['status']}",
            )
        raise HTTPException(status_code=404, detail="File expired or not found.")

    return FileResponse(
        path=file_path, filename=f"Result_{job_id}.zip", media_type="application/zip"
    )

import logging
import uuid
from datetime import datetime
from typing import Any, List

import anyio
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from app.core.config import settings
from app.core.ports import ProcessPort, StoragePort
from app.core.reporter import generate_styled_report
from app.core.service import BatchService
from app.core.validator import TemplateValidator
from app.dependencies import (
    get_batch_service,
    get_job_repository,
    get_process_port,
    get_storage_port,
)
from app.integration.sse import log_generator, send_log_event
from app.integration.state import RedisJobRepository
from app.integration.worker import background_batch_processor
from app.utils import load_dataframe

# Configure Logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter()


@router.get("/stream-logs/{session_id}")
async def stream_logs(session_id: str):
    """Streams real-time logs for a specific session."""
    return StreamingResponse(log_generator(session_id), media_type="text/event-stream")


@router.post("/api/preview")
async def preview_data(
    file_excel: UploadFile = File(None), file_json: UploadFile = File(None)
):
    """Parses the Excel OR JSON file and returns headers and first 5 rows."""
    try:
        df = await load_dataframe(file_excel, file_json)
        headers = df.columns.tolist()
        data_rows = df.head(5)
        preview_data = []
        for _, row in data_rows.iterrows():
            row_dict = row.where(pd.notnull(row), None).to_dict()
            for k, v in row_dict.items():
                if isinstance(v, (datetime, pd.Timestamp)):
                    row_dict[k] = str(v)
            preview_data.append(row_dict)

        return JSONResponse(
            {"status": "success", "headers": headers, "preview": preview_data}
        )
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.post("/api/validate")
async def validate_compatibility(
    file_excel: UploadFile = File(None),
    file_json: UploadFile = File(None),
    files_templates: List[UploadFile] = File(...),
    file_assets: UploadFile = File(None),
    storage: StoragePort = Depends(get_storage_port),
):
    """Validates that template tags exist in Excel/JSON headers.

    If assets.zip is provided, also validates that PPTX image placeholders exist in the zip.
    """
    session_id = f"val_{uuid.uuid4().hex[:8]}"
    session_path = storage.join_path(settings.TEMP_DIR, session_id)
    dir_assets_internal = storage.join_path(session_path, settings.DIR_ASSETS_NAME)

    storage.make_dir(session_path)

    try:
        df = await load_dataframe(file_excel, file_json)
        headers = [str(h) for h in df.columns.tolist()]

        templates_map = {}
        for tmpl in files_templates:
            t_path = storage.join_path(session_path, tmpl.filename)
            content = await tmpl.read()
            # storage.write_binary is blocking, offload it
            await anyio.to_thread.run_sync(storage.write_binary, t_path, content)
            templates_map[tmpl.filename] = t_path

        # Handle Assets (Extract if provided)
        assets_ready = False
        assets_error = None
        if file_assets:
            storage.make_dir(dir_assets_internal)
            zip_input_path = storage.join_path(session_path, file_assets.filename)
            content = await file_assets.read()
            await anyio.to_thread.run_sync(
                storage.write_binary, zip_input_path, content
            )

            try:
                await anyio.to_thread.run_sync(
                    storage.extract_zip, zip_input_path, dir_assets_internal
                )
                assets_ready = True
            except Exception as e:
                logger.error(f"Validation: Failed to extract assets zip: {e}")
                assets_error = f"Zip Extraction Failed: {str(e)}"

        validator = TemplateValidator(storage)
        result = await validator.compare(
            headers,
            templates_map,
            assets_path=dir_assets_internal if assets_ready else None,
            assets_error=assets_error,
        )

        return JSONResponse({"status": "success", "report": result})

    except Exception as e:
        logger.error(f"Validation Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
    finally:
        if storage.exists(session_path):
            storage.delete(session_path)


@router.post("/api/sample")
async def generate_sample(
    session_id: str = Form(...),
    filename_col: str = Form(...),
    output_pdf: bool = Form(False),
    file_excel: UploadFile = File(None),
    file_json: UploadFile = File(None),
    files_templates: List[UploadFile] = File(...),
    file_assets: UploadFile = File(None),
    storage: StoragePort = Depends(get_storage_port),
    process: ProcessPort = Depends(get_process_port),
    batch_service: BatchService = Depends(get_batch_service),
):
    """Processes ONLY the first data row (Dry Run) for verification."""

    start_time = datetime.now()
    sample_session_id = f"{session_id}_sample"
    session_path = storage.join_path(settings.TEMP_DIR, sample_session_id)
    dir_inputs = storage.join_path(session_path, settings.DIR_INPUTS_NAME)
    dir_output = storage.join_path(session_path, settings.DIR_OUTPUTS_NAME)
    dir_assets_internal = storage.join_path(session_path, settings.DIR_ASSETS_NAME)

    for p in [dir_inputs, dir_output, dir_assets_internal]:
        storage.make_dir(p)

    try:
        df = await load_dataframe(file_excel, file_json)
        input_filename = file_excel.filename if file_excel else file_json.filename

        # Save Templates to disk is required because Service expects paths
        saved_template_paths = []
        template_names = []
        for tmpl in files_templates:
            t_path = storage.join_path(dir_inputs, tmpl.filename)
            content = await tmpl.read()
            await anyio.to_thread.run_sync(storage.write_binary, t_path, content)
            saved_template_paths.append(t_path)
            template_names.append(tmpl.filename)

        # Handle Assets
        assets_filename = "None"
        if file_assets:
            assets_filename = file_assets.filename
            zip_input_path = storage.join_path(dir_inputs, file_assets.filename)
            content = await file_assets.read()
            await anyio.to_thread.run_sync(
                storage.write_binary, zip_input_path, content
            )
            await anyio.to_thread.run_sync(
                storage.extract_zip, zip_input_path, dir_assets_internal
            )

        input_manifest = {
            "excel": input_filename,
            "templates": template_names,
            "assets": assets_filename,
        }

        # CALL SERVICE
        result_metrics = await batch_service.process_sample(
            df=df,
            template_paths=saved_template_paths,
            session_path=session_path,
            dir_outputs=dir_output,
            dir_assets=dir_assets_internal,
            to_pdf=output_pdf,
            filename_col=filename_col,
        )

        # Generate Styled Report
        end_time = datetime.now()
        duration = end_time - start_time

        metadata = {
            "session_id": "SAMPLE_RUN",
            "start_time": start_time,
            "duration": duration,
            "total_rows": result_metrics["total_rows"],
            "total_files": result_metrics["total_files"],
            "success_rate": 100 if result_metrics["success_rows"] > 0 else 0,
        }

        report_path = storage.join_path(dir_output, "sample_report.xlsx")

        # Offload Report Generation
        report_bytes = await anyio.to_thread.run_sync(
            generate_styled_report, result_metrics["report"], metadata, input_manifest
        )
        await anyio.to_thread.run_sync(storage.write_binary, report_path, report_bytes)

        # Zip Output
        zip_base_name = storage.join_path(
            settings.TEMP_DIR, f"{session_id}_sample_result"
        )
        await anyio.to_thread.run_sync(storage.create_zip, dir_output, zip_base_name)
        zip_file_path = f"{zip_base_name}.zip"

        # Clean assets
        if storage.exists(dir_assets_internal):
            storage.delete(dir_assets_internal)

        timestamp = end_time.strftime("%Y-%m-%d_%H-%M")
        download_filename = f"LogicPaper_Sample_{timestamp}.zip"

        return FileResponse(
            path=zip_file_path, filename=download_filename, media_type="application/zip"
        )

    except Exception as e:
        logger.error(f"Sample Generation Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.post("/api/process")
async def process_batch(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    filename_col: str = Form(...),
    output_pdf: bool = Form(False),
    group_by_folders: bool = Form(True),
    file_excel: UploadFile = File(None),
    file_json: UploadFile = File(None),
    files_templates: List[UploadFile] = File(...),
    file_assets: UploadFile = File(None),
    batch_service: BatchService = Depends(get_batch_service),
    job_repository: RedisJobRepository = Depends(get_job_repository),
    storage: StoragePort = Depends(get_storage_port),
):
    """Main batch processing endpoint."""
    session_path = storage.join_path(settings.TEMP_DIR, session_id)
    dir_inputs = storage.join_path(session_path, settings.DIR_INPUTS_NAME)
    dir_outputs = storage.join_path(session_path, settings.DIR_OUTPUTS_NAME)
    dir_assets_internal = storage.join_path(session_path, settings.DIR_ASSETS_NAME)

    for p in [dir_inputs, dir_outputs, dir_assets_internal]:
        storage.make_dir(p)

    try:
        send_log_event(session_id, "session_init")

        df = await load_dataframe(file_excel, file_json)
        input_filename = file_excel.filename if file_excel else file_json.filename

        source_upload = file_excel if file_excel else file_json
        if source_upload:
            await source_upload.seek(0)
            source_path = storage.join_path(dir_inputs, source_upload.filename)
            content = await source_upload.read()
            await anyio.to_thread.run_sync(storage.write_binary, source_path, content)
            await source_upload.seek(0)

        saved_template_paths = []
        template_names = []
        for tmpl in files_templates:
            t_path = storage.join_path(dir_inputs, tmpl.filename)
            content = await tmpl.read()
            await anyio.to_thread.run_sync(storage.write_binary, t_path, content)
            saved_template_paths.append(t_path)
            template_names.append(tmpl.filename)
            send_log_event(session_id, "template_loaded", {"name": tmpl.filename})

        assets_filename = "None"
        if file_assets:
            assets_filename = file_assets.filename
            zip_input_path = storage.join_path(dir_inputs, file_assets.filename)
            content = await file_assets.read()
            await anyio.to_thread.run_sync(
                storage.write_binary, zip_input_path, content
            )
            await anyio.to_thread.run_sync(
                storage.extract_zip, zip_input_path, dir_assets_internal
            )
            send_log_event(session_id, "assets_prepared")

        total_rows = len(df)
        send_log_event(session_id, "job_queued", {"count": total_rows})

        job_repository.save(
            session_id,
            {
                "status": "processing",
                "start_time": datetime.now(),
                "total_rows": total_rows,
                "input_file": input_filename,
            },
        )
        job_repository.add_to_history(session_id)

        background_tasks.add_task(
            background_batch_processor,
            session_id,
            df,
            saved_template_paths,
            session_path,
            dir_outputs,
            dir_assets_internal,
            output_pdf,
            filename_col,
            group_by_folders,
            input_manifest={
                "excel": input_filename,
                "templates": template_names,
                "assets": assets_filename,
            },
            batch_service=batch_service,
            job_repository=job_repository,
        )

        return JSONResponse(
            {
                "status": "processing",
                "message": "Job queued for background processing.",
            },
            status_code=202,
        )

    except Exception as e:
        logger.error(f"Error initiating batch {session_id}: {e}")
        send_log_event(session_id, "process_error", {"error": str(e)})
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@router.get("/api/download/{session_id}")
async def download_result(
    session_id: str,
    storage: StoragePort = Depends(get_storage_port),
) -> Any:
    """Downloads the final ZIP file with a timestamped filename."""
    try:
        file_path = storage.join_path(settings.TEMP_DIR, f"{session_id}_result.zip")

        if storage.exists(file_path):
            now = datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M")
            filename = f"LogicPaper_{timestamp}.zip"

            return FileResponse(
                path=file_path, filename=filename, media_type="application/zip"
            )

        return JSONResponse(
            {"status": "error", "message": "File not found"}, status_code=404
        )

    except Exception as e:
        logger.error(f"Download Error: {e}")
        return JSONResponse(
            {"status": "error", "message": "Internal Server Error during download"},
            status_code=500,
        )


@router.get("/api/history")
async def get_job_history(
    job_repository: RedisJobRepository = Depends(get_job_repository),
):
    """Retrieves the list of recent jobs from Redis."""
    jobs = job_repository.get_recent_jobs(limit=10)
    return {"status": "success", "history": jobs}

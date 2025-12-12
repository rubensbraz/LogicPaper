import os
import shutil
import logging
import asyncio
from typing import List
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import anyio
import pandas as pd
from app.core.formatter import DataFormatter
from app.core.engine import DocumentEngine
from app.utils import sanitize_filename, extract_zip, start_scheduler


# Setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DocGenius")
app = FastAPI(title="DocGenius API", version="1.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.getenv("TEMP_DIR", "/data/temp")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Start Scheduler
start_scheduler(TEMP_DIR)

# Mount Static for Frontend
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Real-time Logging (SSE) ---


# Global Event Queue for SSE
# In prod, change this for Redis Pub/Sub
log_queues = {}


async def log_generator(session_id: str):
    """
    Async generator for Server-Sent Events (SSE).
    """
    queue = asyncio.Queue()
    log_queues[session_id] = queue
    try:
        while True:
            data = await queue.get()
            yield f"data: {data}\n\n"
            if "PROCESS_COMPLETE" in data or "PROCESS_ERROR" in data:
                break
    except asyncio.CancelledError:
        pass
    finally:
        if session_id in log_queues:
            del log_queues[session_id]


def send_log(session_id: str, message: str) -> None:
    """Push a log message to the specific session queue."""
    if session_id in log_queues:
        log_queues[session_id].put_nowait(message)


# --- Routes ---


@app.get("/")
async def read_root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/stream-logs/{session_id}")
async def stream_logs(session_id: str):
    return StreamingResponse(log_generator(session_id), media_type="text/event-stream")


@app.post("/api/preview")
async def preview_data(file_excel: UploadFile = File(...)):
    """
    Parses the Excel file and returns the headers, protocol, and first 5 formatted rows.
    """
    try:
        # Load Excel
        df = pd.read_excel(file_excel.file, header=None)

        # Row 1: Variables (Headers)
        headers = df.iloc[0].tolist()
        # Row 2: Protocol
        protocols_raw = df.iloc[1].tolist()
        # Row 3+: Data
        data_rows = df.iloc[2:].head(5)  # Preview only 5

        # Create Protocol Map
        formatter = DataFormatter()
        protocol_map = [formatter.parse_protocol(p) for p in protocols_raw]

        # Format Preview Data
        preview_data = []
        for _, row in data_rows.iterrows():
            row_dict = {}
            for col_idx, cell_val in enumerate(row):
                var_name = headers[col_idx]
                proto = protocol_map[col_idx]
                formatted_val = formatter.format_value(cell_val, proto)

                # Simplify image objects for JSON preview
                if (
                    isinstance(formatted_val, dict)
                    and formatted_val.get("type") == "image"
                ):
                    row_dict[var_name] = f"[Image: {formatted_val['filename']}]"
                else:
                    row_dict[var_name] = formatted_val
            preview_data.append(row_dict)

        return JSONResponse(
            {"status": "success", "headers": headers, "preview": preview_data}
        )

    except Exception as e:
        logger.error(f"Preview failed: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/api/process")
async def process_batch(
    session_id: str = Form(...),
    filename_col: str = Form(...),
    output_pdf: bool = Form(False),
    group_by_folders: bool = Form(True),
    file_excel: UploadFile = File(...),
    files_templates: List[UploadFile] = File(...),
    file_assets: UploadFile = File(None),
):
    """
    Main batch processing endpoint. Handles file naming conventions,
    folder structuring (grouped vs flat), and Excel reporting.
    """
    # 1. Setup Environment
    session_path = os.path.join(TEMP_DIR, session_id)
    assets_path = os.path.join(session_path, "assets")
    output_base_path = os.path.join(session_path, "output")
    templates_storage_path = os.path.join(session_path, "templates")

    for p in [assets_path, output_base_path, templates_storage_path]:
        os.makedirs(p, exist_ok=True)

    try:
        send_log(session_id, "🟢 Initializing session environment...")

        # 2. Save Inputs (Async I/O)
        excel_path = os.path.join(session_path, "data.xlsx")
        async with await anyio.open_file(excel_path, "wb") as f:
            await f.write(await file_excel.read())

        # Save ALL Templates
        saved_template_paths = []
        for tmpl in files_templates:
            t_path = os.path.join(templates_storage_path, tmpl.filename)
            async with await anyio.open_file(t_path, "wb") as f:
                await f.write(await tmpl.read())
            saved_template_paths.append(t_path)
            send_log(session_id, f"   ↳ Loaded template: {tmpl.filename}")

        # Handle Assets
        if file_assets:
            zip_path = os.path.join(session_path, "assets.zip")
            async with await anyio.open_file(zip_path, "wb") as f:
                await f.write(await file_assets.read())
            extract_zip(zip_path, assets_path)
            send_log(session_id, "📦 Assets library extracted.")

        # 3. Initialize Engine & Protocol
        engine = DocumentEngine(session_path)
        formatter = DataFormatter()

        # Read Excel using pandas
        df = pd.read_excel(excel_path, header=None)
        headers = df.iloc[0].tolist()
        protocol_map = [formatter.parse_protocol(p) for p in df.iloc[1].tolist()]

        total_rows = len(df) - 2
        send_log(session_id, f"🚀 Starting batch processing for {total_rows} rows.")

        # 4. Processing Loop
        report = []

        for idx, row in df.iloc[2:].iterrows():
            row_num = idx + 1
            try:
                # Build Context
                context = {}
                row_identifier = f"Row_{row_num}"

                # Extract Data
                for col_idx, cell_val in enumerate(row):
                    var_name = headers[col_idx]
                    val = formatter.format_value(cell_val, protocol_map[col_idx])
                    context[var_name] = val

                    if var_name == filename_col:
                        # Sanitize the specific identifier (e.g. "JOHN DOE")
                        row_identifier = sanitize_filename(str(val))

                # Determine Output Directory for this Row
                if group_by_folders:
                    # Option A: Create specific folder (e.g., Output/JOHN DOE/)
                    target_dir = os.path.join(output_base_path, row_identifier)
                else:
                    # Option B: Flat structure (e.g., Output/)
                    target_dir = output_base_path

                os.makedirs(target_dir, exist_ok=True)

                # Iterate through EACH template for this row
                for tmpl_path in saved_template_paths:
                    # 1. Get original template name (e.g., "Contract")
                    tmpl_filename = os.path.basename(tmpl_path)
                    tmpl_name_base, tmpl_ext = os.path.splitext(tmpl_filename)

                    # 2. Construct Filename: "Contract - JOHN DOE.docx"
                    final_filename = f"{tmpl_name_base} - {row_identifier}{tmpl_ext}"
                    doc_output_path = os.path.join(target_dir, final_filename)

                    # 3. Render
                    if tmpl_ext.lower() == ".docx":
                        await engine.process_docx(
                            tmpl_path, doc_output_path, context, assets_path
                        )
                    elif tmpl_ext.lower() == ".pptx":
                        await engine.process_pptx(tmpl_path, doc_output_path, context)

                    # 4. Convert to PDF if requested
                    if output_pdf:
                        await engine.convert_to_pdf(doc_output_path, target_dir)

                send_log(session_id, f"✅ {row_identifier} processed.")
                report.append(
                    {"Row": row_num, "Identifier": row_identifier, "Status": "Success"}
                )

            except Exception as e:
                logger.error(f"Row {row_num} failed: {e}")
                send_log(session_id, f"❌ Row {row_num} FAILED: {str(e)}")
                report.append(
                    {"Row": row_num, "Identifier": "N/A", "Status": f"Error: {str(e)}"}
                )

        # 5. Finalize - Generate Excel Report
        report_path = os.path.join(output_base_path, "job_report.xlsx")
        pd.DataFrame(report).to_excel(report_path, index=False)

        # Zip the entire 'output' folder
        zip_output_path = os.path.join(session_path, "DocGenius_Batch_Result")
        shutil.make_archive(zip_output_path, "zip", output_base_path)

        send_log(session_id, "PROCESS_COMPLETE")

        return JSONResponse(
            {"status": "success", "download_url": f"/api/download/{session_id}"}
        )

    except Exception as e:
        logger.error(f"Critical Batch Error: {e}")
        send_log(session_id, f"PROCESS_ERROR: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/download/{session_id}")
def download_result(session_id: str):
    file_path = os.path.join(TEMP_DIR, session_id, "DocGenius_Batch_Result.zip")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="DocGenius_Output.zip")
    return JSONResponse(
        {"status": "error", "message": "File not found"}, status_code=404
    )

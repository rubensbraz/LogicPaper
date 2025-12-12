import os
import uuid
import shutil
import pandas as pd
import logging
import asyncio
from typing import List
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.formatter import DataFormatter
from app.core.engine import DocumentEngine
from app.utils import sanitize_filename, extract_zip, start_scheduler


# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DocGenius")
app = FastAPI(title="DocGenius API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = "/data/temp"  # Mapped in Docker
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Start Scheduler
start_scheduler(TEMP_DIR)

# Mount Static for Frontend
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Global Event Queue for SSE
# In prod, change this for Redis Pub/Sub
log_queues = {}


async def log_generator(session_id: str):
    """Generator for Server-Sent Events."""
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
        del log_queues[session_id]


def send_log(session_id: str, message: str):
    if session_id in log_queues:
        log_queues[session_id].put_nowait(message)


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
        protocol_map = []
        for i, p_str in enumerate(protocols_raw):
            protocol_map.append(formatter.parse_protocol(p_str))

        # Format Preview Data
        preview_data = []
        for idx, row in data_rows.iterrows():
            row_dict = {}
            for col_idx, cell_val in enumerate(row):
                var_name = headers[col_idx]
                proto = protocol_map[col_idx]
                formatted_val = formatter.format_value(cell_val, proto)

                # Simplify object for JSON (handle image dicts)
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
        logger.error(f"Preview Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/api/process")
async def process_batch(
    session_id: str = Form(...),
    filename_col: str = Form(...),
    output_pdf: bool = Form(False),
    file_excel: UploadFile = File(...),
    file_template: UploadFile = File(...),
    file_assets: UploadFile = File(None),
):
    # Setup Session Paths
    session_path = os.path.join(TEMP_DIR, session_id)
    assets_path = os.path.join(session_path, "assets")
    output_path = os.path.join(session_path, "output")
    os.makedirs(assets_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    try:
        send_log(session_id, "Initializing session...")

        # 1. Save Files
        excel_path = os.path.join(session_path, "data.xlsx")
        template_path = os.path.join(session_path, file_template.filename)

        async with await anyio.open_file(excel_path, "wb") as f:  # async save
            content = await file_excel.read()
            await f.write(content)

        async with await anyio.open_file(template_path, "wb") as f:
            content = await file_template.read()
            await f.write(content)

        if file_assets:
            zip_path = os.path.join(session_path, "assets.zip")
            async with await anyio.open_file(zip_path, "wb") as f:
                content = await file_assets.read()
                await f.write(content)
            extract_zip(zip_path, assets_path)
            send_log(session_id, "Assets extracted.")

        # 2. Init Engine
        engine = DocumentEngine(session_path)
        formatter = DataFormatter()

        # 3. Read Data
        df = pd.read_excel(excel_path, header=None)
        headers = df.iloc[0].tolist()
        protocols_raw = df.iloc[1].tolist()

        # Build Protocol Map
        protocol_map = [formatter.parse_protocol(p) for p in protocols_raw]

        # 4. Iterate
        total_rows = len(df) - 2
        success_count = 0
        report = []

        send_log(session_id, f"Starting processing of {total_rows} rows...")

        for idx, row in df.iloc[2:].iterrows():
            row_num = idx + 1  # Excel row number equivalent
            try:
                # Build Context
                context = {}
                file_name_base = "doc"

                for col_idx, cell_val in enumerate(row):
                    var_name = headers[col_idx]
                    proto = protocol_map[col_idx]
                    val = formatter.format_value(cell_val, proto)
                    context[var_name] = val

                    if var_name == filename_col:
                        file_name_base = sanitize_filename(str(val))

                # Determine Output Format
                ext = os.path.splitext(template_path)[1].lower()
                doc_name = f"{file_name_base}{ext}"
                doc_output = os.path.join(output_path, doc_name)

                # Render
                if ext == ".docx":
                    await engine.process_docx(
                        template_path, doc_output, context, assets_path
                    )
                elif ext == ".pptx":
                    await engine.process_pptx(template_path, doc_output, context)

                # PDF Conversion
                if output_pdf:
                    send_log(session_id, f"Converting Row {row_num} to PDF...")
                    await engine.convert_to_pdf(doc_output, output_path)

                report.append(
                    {"Row": row_num, "File": file_name_base, "Status": "Success"}
                )
                success_count += 1
                send_log(session_id, f"Row {row_num} completed.")

            except Exception as e:
                logger.error(f"Row {row_num} failed: {e}")
                report.append(
                    {"Row": row_num, "File": "N/A", "Status": f"Error: {str(e)}"}
                )
                send_log(session_id, f"Row {row_num} FAILED.")

        # 5. Generate Report & Zip
        pd.DataFrame(report).to_csv(
            os.path.join(output_path, "job_report.csv"), index=False
        )

        zip_output = os.path.join(session_path, "result.zip")
        shutil.make_archive(zip_output.replace(".zip", ""), "zip", output_path)

        send_log(session_id, "PROCESS_COMPLETE")

        return JSONResponse(
            {"status": "success", "download_url": f"/api/download/{session_id}"}
        )

    except Exception as e:
        logger.error(f"Batch Error: {e}")
        send_log(session_id, f"PROCESS_ERROR: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/download/{session_id}")
def download_result(session_id: str):
    file_path = os.path.join(TEMP_DIR, session_id, "result.zip")
    if os.path.exists(file_path):
        return FileResponse(file_path, filename="DocGenius_Output.zip")
    return JSONResponse(
        {"status": "error", "message": "File not found"}, status_code=404
    )


import anyio  # Helper for async file I/O

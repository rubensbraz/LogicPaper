import os
import shutil
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import anyio
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

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


# Global Event Queue for SSE. In prod, change this for Redis Pub/Sub
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


# --- Reporting Engine ---


def generate_styled_report(
    path: str,
    report_data: List[Dict[str, Any]],
    metadata: Dict[str, Any],
    input_manifest: Dict[str, Any],
) -> None:
    """
    Generates a high-fidelity, styled Excel report with two sheets.
    Updated to support granular, file-level logging.

    Args:
        path (str): Output path for the .xlsx file.
        report_data (List[Dict]): The list of row results (one per file).
        metadata (Dict): Statistics like start_time, duration, file_counts.
        input_manifest (Dict): Dictionary listing input filenames.
    """
    wb = Workbook()

    # --- Styles ---
    navy_blue = "1F4E78"
    white = "FFFFFF"

    header_font = Font(name="Calibri", size=12, bold=True, color=white)
    title_font = Font(name="Calibri", size=18, bold=True, color=navy_blue)
    subtitle_font = Font(name="Calibri", size=14, bold=True, color=navy_blue)
    label_font = Font(name="Calibri", size=11, bold=True, color="555555")

    header_fill = PatternFill(
        start_color=navy_blue, end_color=navy_blue, fill_type="solid"
    )
    success_fill = PatternFill(
        start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"
    )
    success_font = Font(color="006100")
    error_fill = PatternFill(
        start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"
    )
    error_font = Font(color="9C0006")

    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    wrap_align = Alignment(vertical="top", wrap_text=True)

    # ==========================
    # SHEET 1: DASHBOARD
    # ==========================
    ws_dash = wb.active
    ws_dash.title = "Executive Summary"
    ws_dash.sheet_view.showGridLines = False

    ws_dash["B2"] = "DocGenius Execution Report"
    ws_dash["B2"].font = title_font

    # Metrics
    metrics = [
        ("Session ID", metadata["session_id"]),
        ("Date", metadata["start_time"].strftime("%Y-%m-%d")),
        ("Duration", str(metadata["duration"]).split(".")[0]),
        ("Total Rows Processed", metadata["total_rows"]),
        ("Total Files Generated", metadata["total_files"]),
        ("Success Rate", f"{metadata['success_rate']:.1f}%"),
    ]

    row_idx = 4
    for label, value in metrics:
        cell_label = ws_dash.cell(row=row_idx, column=2, value=label)
        cell_value = ws_dash.cell(row=row_idx, column=3, value=value)
        cell_label.font = label_font
        cell_label.border = thin_border
        cell_value.border = thin_border
        row_idx += 1

    # Input Manifest
    row_idx += 2
    ws_dash.cell(row=row_idx, column=2, value="Input Files Manifest").font = (
        subtitle_font
    )
    row_idx += 1

    inputs = [
        ("Data Source", input_manifest.get("excel", "N/A")),
        ("Assets Archive", input_manifest.get("assets", "None")),
        ("Templates Used", "\n".join(input_manifest.get("templates", []))),
    ]

    for label, value in inputs:
        cell_label = ws_dash.cell(row=row_idx, column=2, value=label)
        cell_value = ws_dash.cell(row=row_idx, column=3, value=value)
        cell_label.font = label_font
        cell_label.border = thin_border
        cell_label.alignment = Alignment(vertical="top")
        cell_value.border = thin_border
        cell_value.alignment = wrap_align
        row_idx += 1

    ws_dash.column_dimensions["B"].width = 25
    ws_dash.column_dimensions["C"].width = 50

    # ==========================
    # SHEET 2: DETAILED LOG
    # ==========================
    ws_log = wb.create_sheet("Detailed Logs")

    if report_data:
        df = pd.DataFrame(report_data)
        # Explicit column order
        cols = ["Row", "Identifier", "Output File", "Status", "Error Details"]
        for c in cols:
            if c not in df.columns:
                df[c] = ""
        df = df[cols]

        # Header
        for col_num, column_title in enumerate(df.columns, 1):
            cell = ws_log.cell(row=1, column=col_num, value=column_title)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # Data
        for r_idx, row in enumerate(
            dataframe_to_rows(df, index=False, header=False), 2
        ):
            for c_idx, value in enumerate(row, 1):
                cell = ws_log.cell(row=r_idx, column=c_idx, value=value)
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")

                # Status Coloring (Column 4)
                if c_idx == 4:
                    if str(value).lower() == "success":
                        cell.fill = success_fill
                        cell.font = success_font
                    else:
                        cell.fill = error_fill
                        cell.font = error_font

                # Error Details Coloring (Column 5)
                if c_idx == 5 and value:
                    cell.font = error_font

        # Column Widths
        ws_log.column_dimensions["A"].width = 8  # Row
        ws_log.column_dimensions["B"].width = 25  # Identifier
        ws_log.column_dimensions["C"].width = 50  # Output File
        ws_log.column_dimensions["D"].width = 15  # Status
        ws_log.column_dimensions["E"].width = 60  # Error Details

        # Table
        tab = Table(displayName="LogTable", ref=f"A1:E{len(df)+1}")
        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        tab.tableStyleInfo = style
        ws_log.add_table(tab)

    wb.save(path)


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
    Main batch processing endpoint.
    Refactored to handle granular file logging and clean asset management.
    """
    start_time = datetime.now()

    # 1. Setup Session & Directories
    session_path = os.path.join(TEMP_DIR, session_id)

    # Public folders (will be zipped)
    dir_inputs = os.path.join(session_path, "1 Input documents")
    dir_outputs = os.path.join(session_path, "2 Generated documents")

    # Internal folder for asset extraction (will be DELETED before zipping)
    # Using a dot prefix to denote internal use, though strict path deletion is what matters
    dir_assets_internal = os.path.join(session_path, ".temp_assets")

    for p in [dir_inputs, dir_outputs, dir_assets_internal]:
        os.makedirs(p, exist_ok=True)

    try:
        send_log(session_id, "🟢 Initializing session structure...")

        # 2. Save Inputs

        # Save Excel
        excel_path = os.path.join(dir_inputs, file_excel.filename)
        async with await anyio.open_file(excel_path, "wb") as f:
            await f.write(await file_excel.read())

        # Save Templates
        saved_template_paths = []
        template_names = []
        for tmpl in files_templates:
            t_path = os.path.join(dir_inputs, tmpl.filename)
            async with await anyio.open_file(t_path, "wb") as f:
                await f.write(await tmpl.read())
            saved_template_paths.append(t_path)
            template_names.append(tmpl.filename)
            send_log(session_id, f"   ↳ Loaded template: {tmpl.filename}")

        # Handle Assets (Save Zip to Inputs, Extract to Internal)
        assets_filename = "None"
        if file_assets:
            assets_filename = file_assets.filename

            # Save original zip to Inputs folder for user reference
            zip_input_path = os.path.join(dir_inputs, file_assets.filename)
            async with await anyio.open_file(zip_input_path, "wb") as f:
                await f.write(await file_assets.read())

            # Extract to INTERNAL folder (hidden from final output)
            extract_zip(zip_input_path, dir_assets_internal)
            send_log(session_id, "📦 Assets library prepared.")

        # Manifest
        input_manifest = {
            "excel": file_excel.filename,
            "templates": template_names,
            "assets": assets_filename,
        }

        # 3. Initialize Engine
        engine = DocumentEngine(session_path)
        formatter = DataFormatter()

        df = pd.read_excel(excel_path, header=None)
        headers = df.iloc[0].tolist()
        protocol_map = [formatter.parse_protocol(p) for p in df.iloc[1].tolist()]

        total_rows = len(df) - 2
        send_log(session_id, f"🚀 Starting processing for {total_rows} rows.")

        # 4. Processing Loop
        report = []
        total_files_generated_count = 0
        success_rows_count = 0  # Count rows where at least one file worked

        for idx, row in df.iloc[2:].iterrows():
            row_num = idx + 1
            row_success = False

            # Parsing Context
            context = {}
            row_identifier = f"Row_{row_num}"
            try:
                for col_idx, cell_val in enumerate(row):
                    var_name = headers[col_idx]
                    val = formatter.format_value(cell_val, protocol_map[col_idx])
                    context[var_name] = val
                    if var_name == filename_col:
                        row_identifier = sanitize_filename(str(val))
            except Exception as e:
                # If context parsing fails, log a generic error for the row
                logger.error(f"Row {row_num} parsing error: {e}")
                report.append(
                    {
                        "Row": row_num,
                        "Identifier": "N/A",
                        "Output File": "N/A",
                        "Status": "Error",
                        "Error Details": f"Data Parsing Error: {str(e)}",
                    }
                )
                continue

            # Output Directory
            if group_by_folders:
                target_dir = os.path.join(dir_outputs, row_identifier)
            else:
                target_dir = dir_outputs
            os.makedirs(target_dir, exist_ok=True)

            # Template Loop
            for tmpl_path in saved_template_paths:
                tmpl_filename = os.path.basename(tmpl_path)
                tmpl_name_base, tmpl_ext = os.path.splitext(tmpl_filename)

                # --- PROCESS 1: DOCX/PPTX ---
                final_filename = f"{tmpl_name_base} - {row_identifier}{tmpl_ext}"
                doc_output_path = os.path.join(target_dir, final_filename)

                try:
                    if tmpl_ext.lower() == ".docx":
                        await engine.process_docx(
                            tmpl_path, doc_output_path, context, dir_assets_internal
                        )
                    elif tmpl_ext.lower() == ".pptx":
                        await engine.process_pptx(tmpl_path, doc_output_path, context)

                    # Log Success for Document
                    report.append(
                        {
                            "Row": row_num,
                            "Identifier": row_identifier,
                            "Output File": final_filename,
                            "Status": "Success",
                            "Error Details": "",
                        }
                    )
                    total_files_generated_count += 1
                    row_success = True

                except Exception as e:
                    # Log Error for Document
                    report.append(
                        {
                            "Row": row_num,
                            "Identifier": row_identifier,
                            "Output File": final_filename,
                            "Status": "Error",
                            "Error Details": str(e),
                        }
                    )
                    logger.error(f"Error generating {final_filename}: {e}")

                # --- PROCESS 2: PDF (Optional) ---
                if output_pdf:
                    pdf_filename = f"{tmpl_name_base} - {row_identifier}.pdf"

                    # Only attempt PDF if DOCX succeeded
                    if os.path.exists(doc_output_path):
                        try:
                            await engine.convert_to_pdf(doc_output_path, target_dir)

                            report.append(
                                {
                                    "Row": row_num,
                                    "Identifier": row_identifier,
                                    "Output File": pdf_filename,
                                    "Status": "Success",
                                    "Error Details": "",
                                }
                            )
                            total_files_generated_count += 1

                        except Exception as e:
                            report.append(
                                {
                                    "Row": row_num,
                                    "Identifier": row_identifier,
                                    "Output File": pdf_filename,
                                    "Status": "Error",
                                    "Error Details": f"PDF Conversion: {str(e)}",
                                }
                            )
                    else:
                        # If DOCX failed, imply PDF fail
                        report.append(
                            {
                                "Row": row_num,
                                "Identifier": row_identifier,
                                "Output File": pdf_filename,
                                "Status": "Skipped",
                                "Error Details": "Source document failed generation",
                            }
                        )

            if row_success:
                success_rows_count += 1
            send_log(session_id, f"✅ {row_identifier} processed.")

        # 5. Cleanup Internal Assets
        # This prevents the weird folder from appearing in the output zip
        if os.path.exists(dir_assets_internal):
            shutil.rmtree(dir_assets_internal)
            send_log(session_id, "🧹 Cleaning up temporary files...")

        # 6. Finalize Report
        end_time = datetime.now()
        duration = end_time - start_time

        metadata = {
            "session_id": session_id,
            "start_time": start_time,
            "duration": duration,
            "total_rows": total_rows,
            "total_files": total_files_generated_count,
            "success_rate": (
                (success_rows_count / total_rows * 100) if total_rows > 0 else 0
            ),
        }

        report_path = os.path.join(session_path, "job_report.xlsx")
        generate_styled_report(report_path, report, metadata, input_manifest)

        # 7. Zip Result
        zip_base_name = os.path.join(TEMP_DIR, f"{session_id}_result")
        shutil.make_archive(
            base_name=zip_base_name, format="zip", root_dir=session_path
        )

        send_log(session_id, "PROCESS_COMPLETE")

        return JSONResponse(
            {"status": "success", "download_url": f"/api/download/{session_id}"}
        )

    except Exception as e:
        logger.error(f"Critical Batch Error: {e}")
        send_log(session_id, f"PROCESS_ERROR: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


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
    start_time = datetime.now()

    # 1. Setup Directory Structure
    session_path = os.path.join(TEMP_DIR, session_id)

    # Define High-Level Folders
    dir_inputs = os.path.join(session_path, "1 Input documents")
    dir_outputs = os.path.join(session_path, "2 Generated documents")

    # Define Sub-folders within Inputs
    dir_input_assets = os.path.join(dir_inputs, "assets")

    for p in [dir_inputs, dir_outputs, dir_input_assets]:
        os.makedirs(p, exist_ok=True)

    try:
        send_log(session_id, "🟢 Initializing session structure...")

        # 2. Save Inputs (Async I/O)
        # Save Excel
        excel_path = os.path.join(dir_inputs, file_excel.filename)
        async with await anyio.open_file(excel_path, "wb") as f:
            await f.write(await file_excel.read())

        # Save Templates
        saved_template_paths = []
        template_names = []
        for tmpl in files_templates:
            t_path = os.path.join(dir_inputs, tmpl.filename)
            async with await anyio.open_file(t_path, "wb") as f:
                await f.write(await tmpl.read())
            saved_template_paths.append(t_path)
            template_names.append(tmpl.filename)
            send_log(session_id, f"   ↳ Loaded template: {tmpl.filename}")

        # Handle Assets
        assets_filename = "None"
        if file_assets:
            assets_filename = file_assets.filename
            zip_path = os.path.join(dir_inputs, file_assets.filename)
            async with await anyio.open_file(zip_path, "wb") as f:
                await f.write(await file_assets.read())
            extract_zip(zip_path, dir_input_assets)
            send_log(session_id, "📦 Assets library extracted.")

        # Create Manifest for Report
        input_manifest = {
            "excel": file_excel.filename,
            "templates": template_names,
            "assets": assets_filename,
        }

        # 3. Initialize Engine & Protocol
        engine = DocumentEngine(session_path)
        formatter = DataFormatter()

        df = pd.read_excel(excel_path, header=None)
        headers = df.iloc[0].tolist()
        protocol_map = [formatter.parse_protocol(p) for p in df.iloc[1].tolist()]

        total_rows = len(df) - 2
        send_log(session_id, f"🚀 Starting batch processing for {total_rows} rows.")

        # 4. Processing Loop
        report = []
        total_files_generated_count = 0
        success_count = 0

        for idx, row in df.iloc[2:].iterrows():
            row_num = idx + 1
            row_generated_files = []  # Track filenames for this row

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
                        row_identifier = sanitize_filename(str(val))

                # Determine Output Directory (Inside '2 Generated documents')
                if group_by_folders:
                    target_dir = os.path.join(dir_outputs, row_identifier)
                else:
                    target_dir = dir_outputs

                os.makedirs(target_dir, exist_ok=True)

                # Iterate Templates
                for tmpl_path in saved_template_paths:
                    tmpl_filename = os.path.basename(tmpl_path)
                    tmpl_name_base, tmpl_ext = os.path.splitext(tmpl_filename)

                    final_filename = f"{tmpl_name_base} - {row_identifier}{tmpl_ext}"
                    doc_output_path = os.path.join(target_dir, final_filename)

                    # Render DOCX/PPTX
                    if tmpl_ext.lower() == ".docx":
                        await engine.process_docx(
                            tmpl_path, doc_output_path, context, dir_input_assets
                        )
                    elif tmpl_ext.lower() == ".pptx":
                        await engine.process_pptx(tmpl_path, doc_output_path, context)

                    row_generated_files.append(final_filename)

                    # Render PDF
                    if output_pdf:
                        await engine.convert_to_pdf(doc_output_path, target_dir)
                        pdf_name = f"{os.path.splitext(final_filename)[0]}.pdf"
                        row_generated_files.append(pdf_name)

                send_log(session_id, f"✅ {row_identifier} processed.")

                report.append(
                    {
                        "Row": row_num,
                        "Identifier": row_identifier,
                        "Status": "Success",
                        "Output Files": "\n".join(row_generated_files),
                        "Error Details": "",
                    }
                )
                success_count += 1
                total_files_generated_count += len(row_generated_files)

            except Exception as e:
                logger.error(f"Row {row_num} failed: {e}")
                send_log(session_id, f"❌ Row {row_num} FAILED: {str(e)}")
                report.append(
                    {
                        "Row": row_num,
                        "Identifier": (
                            row_identifier if "row_identifier" in locals() else "N/A"
                        ),
                        "Status": "Failed",
                        "Output Files": "",
                        "Error Details": str(e),
                    }
                )

        # 5. Finalize - Generate Report in ROOT of Session
        end_time = datetime.now()
        duration = end_time - start_time

        metadata = {
            "session_id": session_id,
            "start_time": start_time,
            "duration": duration,
            "total_rows": total_rows,
            "total_files": total_files_generated_count,
            "success_rate": (success_count / total_rows * 100) if total_rows > 0 else 0,
        }

        # Save report at Session Root (outside input/output folders)
        report_path = os.path.join(session_path, "job_report.xlsx")

        generate_styled_report(report_path, report, metadata, input_manifest)

        # 6. Create ZIP (Zipping the content of session_path)
        # We save the ZIP file to TEMP_DIR (parent) to avoid recursive zipping
        zip_base_name = os.path.join(TEMP_DIR, f"{session_id}_result")

        shutil.make_archive(
            base_name=zip_base_name, format="zip", root_dir=session_path
        )

        send_log(session_id, "PROCESS_COMPLETE")

        return JSONResponse(
            {"status": "success", "download_url": f"/api/download/{session_id}"}
        )

    except Exception as e:
        logger.error(f"Critical Batch Error: {e}")
        send_log(session_id, f"PROCESS_ERROR: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/download/{session_id}")
async def download_result(session_id: str) -> Any:
    """
    Downloads the final ZIP file with a timestamped filename.

    Format: DocGenius_YYYY-MM-DD_HH-MM.zip
    """
    try:
        file_path = os.path.join(TEMP_DIR, f"{session_id}_result.zip")

        if os.path.exists(file_path):
            # Get current time
            now = datetime.now()
            # Format: YYYY-MM-DD_HH-MM
            timestamp = now.strftime("%Y-%m-%d_%H-%M")
            filename = f"DocGenius_{timestamp}.zip"

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

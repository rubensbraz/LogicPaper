import logging
import os
import shutil
from datetime import datetime
from typing import Optional

import pandas as pd

from app.core.config import TEMP_DIR, logger
from app.core.engine import DocumentEngine
from app.utils import sanitize_filename
from app.integration.state import job_store


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
    Background worker function to process documents without blocking the API.

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
        engine = DocumentEngine(session_path)
        files_count = 0

        # Iterate through rows
        for idx, row in df.iterrows():
            row_num = idx + 1
            context = row.to_dict()
            # Clean context (NaN -> None)
            cleaned_context = {
                k: (None if pd.isna(v) else v) for k, v in context.items()
            }

            # Determine Identifier
            row_identifier = f"Row_{row_num}"
            if filename_col and filename_col in cleaned_context:
                val = str(cleaned_context[filename_col])
                if val.strip():
                    row_identifier = sanitize_filename(val)

            # Setup Target Directory
            target_dir = (
                os.path.join(dir_outputs, row_identifier)
                if group_folders
                else dir_outputs
            )
            os.makedirs(target_dir, exist_ok=True)

            # Determine Output Path
            tmpl_filename = os.path.basename(template_path)
            tmpl_name_base, tmpl_ext = os.path.splitext(tmpl_filename)
            final_filename = f"{tmpl_name_base} - {row_identifier}{tmpl_ext}"
            output_path = os.path.join(target_dir, final_filename)

            # Process based on extension
            if tmpl_ext.lower() == ".docx":
                await engine.process_docx(
                    template_path, output_path, cleaned_context, dir_assets
                )
            elif tmpl_ext.lower() == ".pptx":
                await engine.process_pptx(template_path, output_path, cleaned_context)
            elif tmpl_ext.lower() in [".md", ".txt"]:
                await engine.process_text(template_path, output_path, cleaned_context)

            # PDF Conversion
            if to_pdf and os.path.exists(output_path):
                await engine.convert_to_pdf(output_path, target_dir)

            files_count += 1

        # Create Result ZIP
        zip_base = os.path.join(TEMP_DIR, f"{job_id}_result")
        shutil.make_archive(zip_base, "zip", dir_outputs)

        # Update State: Completed
        job_store[job_id]["status"] = "completed"
        job_store[job_id]["files_generated"] = files_count
        job_store[job_id]["download_url"] = f"/api/v1/integration/download/{job_id}"

        logger.info(
            f"Job {job_id} completed successfully. Generated {files_count} files."
        )

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job_store[job_id]["status"] = "failed"
        job_store[job_id]["error"] = str(e)

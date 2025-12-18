import logging
import os
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from app.core.engine import DocumentEngine
from app.utils import sanitize_filename


# Configure Logging
logger = logging.getLogger(__name__)


async def process_batch_core(
    session_id: str,
    df: pd.DataFrame,
    template_paths: List[str],
    session_path: str,
    dir_outputs: str,
    dir_assets: str,
    to_pdf: bool,
    filename_col: Optional[str],
    group_folders: bool,
    log_callback: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Core Batch Processing Logic. Iterates through the DataFrame and applies templates.
    Used by both the Web Dashboard (main.py) and Headless API (worker.py).

    Args:
        session_id (str): Unique ID for the job/session.
        df (pd.DataFrame): The data to process.
        template_paths (List[str]): List of full paths to template files.
        session_path (str): Root directory of the session.
        dir_outputs (str): Directory where outputs should be saved.
        dir_assets (str): Directory where assets are extracted.
        to_pdf (bool): If True, converts generated docs to PDF.
        filename_col (Optional[str]): Column name to use for file naming.
        group_folders (bool): If True, creates a subfolder per row.
        log_callback (Optional[Callable]): Function to send real-time logs (e.g., SSE).

    Returns:
        Dict[str, Any]: Contains 'report' (List of dicts) and 'files_count' (int).
    """
    engine = DocumentEngine(session_path)
    report = []
    total_files_generated = 0
    success_rows_count = 0

    # Helper to send logs safely
    def send_log(msg: str):
        if log_callback:
            log_callback(msg)
        else:
            logger.info(f"[{session_id}] {msg}")

    # Iterate through Data
    for idx, row in df.iterrows():
        row_num = idx + 1  # 1-based index
        row_success = False

        # 1. Prepare Context (Sanitize NaN -> None)
        context = row.to_dict()
        cleaned_context = {k: (None if pd.isna(v) else v) for k, v in context.items()}

        # 2. Determine Filename Identifier
        row_identifier = f"Row_{row_num}"
        if filename_col and filename_col in cleaned_context:
            val = str(cleaned_context[filename_col])
            if val.strip():
                row_identifier = sanitize_filename(val)

        # 3. Setup Target Directory
        if group_folders:
            target_dir = os.path.join(dir_outputs, row_identifier)
        else:
            target_dir = dir_outputs
        os.makedirs(target_dir, exist_ok=True)

        # 4. Process Each Template
        for tmpl_path in template_paths:
            tmpl_filename = os.path.basename(tmpl_path)
            tmpl_name_base, tmpl_ext = os.path.splitext(tmpl_filename)

            # Construct Output Filename
            final_filename = f"{tmpl_name_base} - {row_identifier}{tmpl_ext}"
            doc_output_path = os.path.join(target_dir, final_filename)

            try:
                # Render Document
                if tmpl_ext.lower() == ".docx":
                    await engine.process_docx(
                        tmpl_path, doc_output_path, cleaned_context, dir_assets
                    )
                elif tmpl_ext.lower() == ".pptx":
                    await engine.process_pptx(
                        tmpl_path, doc_output_path, cleaned_context
                    )
                elif tmpl_ext.lower() in [".md", ".txt"]:
                    await engine.process_text(
                        tmpl_path, doc_output_path, cleaned_context
                    )

                # Log Success
                report.append(
                    {
                        "Row": row_num,
                        "Identifier": row_identifier,
                        "Output File": final_filename,
                        "Status": "Success",
                        "Error Details": "",
                    }
                )
                total_files_generated += 1
                row_success = True

            except Exception as e:
                # Log Failure
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

            # 5. PDF Conversion (Optional)
            if to_pdf and os.path.exists(doc_output_path):
                pdf_filename = f"{tmpl_name_base} - {row_identifier}.pdf"
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
                    total_files_generated += 1
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

        if row_success:
            success_rows_count += 1
            send_log(f"✅ {row_identifier} processed.")

    return {
        "report": report,
        "total_files": total_files_generated,
        "success_rows": success_rows_count,
        "total_rows": len(df),
    }

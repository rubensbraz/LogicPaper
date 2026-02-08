import json
import logging
import os
import shutil
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from app.core.engine import DocumentEngine
from app.core.ports import JobRepositoryPort
from app.utils import sanitize_filename


# Configure Logging
logger = logging.getLogger(__name__)


class BatchService:
    """Service for orchestrating document batch processing.

    Handles the core logic of iterating through data rows, processing templates,
    generating documents, and updating job status via the repository.
    """

    def __init__(self, job_repository: JobRepositoryPort):
        """Initializes the BatchService with dependencies.

        Args:
            job_repository (JobRepositoryPort): Port for persisting job status.
        """
        self.job_repository = job_repository

    async def process_batch(
        self,
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
        """Orchestrates the batch generation process.

        Iterates through the provided DataFrame, processes each row against the
        templates using the DocumentEngine, and handles result aggregation and
        status updates.

        Args:
            session_id (str): Unique identifier for the batch session.
            df (pd.DataFrame): Dataframe containing the data to process.
            template_paths (List[str]): List of absolute paths to template files.
            session_path (str): Path to the session's temporary directory.
            dir_outputs (str): Directory where generated files should be saved.
            dir_assets (str): Directory containing assets (images, etc.).
            to_pdf (bool): Whether to convert generated documents to PDF.
            filename_col (Optional[str]): Column name to use for dynamic file naming.
            group_folders (bool): Whether to group outputs into subfolders.
            log_callback (Optional[Callable[[str], None]], optional): Function to call
                for sending real-time logs (e.g., via SSE). Defaults to None.

        Returns:
            Dict[str, Any]: A summary dictionary containing the report list, total
            files generated, success count, and total count.
        """
        engine = DocumentEngine(session_path)
        report = []
        total_files_generated = 0
        success_rows_count = 0

        # Helper to send logs
        def send_log(msg: str):
            if log_callback:
                log_callback(msg)
            else:
                logger.info(f"[{session_id}] {msg}")

        # Iterate through Data
        total_rows = len(df)
        for idx, row in df.iterrows():
            row_num = idx + 1
            row_success = False

            # 1. Prepare Context
            context = row.to_dict()
            cleaned_context = {
                k: (None if pd.isna(v) else v) for k, v in context.items()
            }

            # 2. Determine Identifier
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

                # 5. PDF Conversion
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
                percent = int((row_num / total_rows) * 100)

                # Send progress update via callback
                progress_payload = {
                    "code": "row_processed",
                    "params": {
                        "identifier": row_identifier,
                        "current": row_num,
                        "total": total_rows,
                        "percent": percent,
                    },
                }
                send_log(json.dumps(progress_payload))

                # Update status in repository
                self.job_repository.update_status(
                    session_id, "processing", progress=percent
                )

        return {
            "report": report,
            "total_files": total_files_generated,
            "success_rows": success_rows_count,
            "total_rows": total_rows,
        }

    @staticmethod
    def create_zip_archive(source_dir: str, output_path_base: str) -> None:
        """Creates a zip archive from a directory.

        Args:
            source_dir (str): The directory to zip.
            output_path_base (str): The path for the output zip file (without extension).
        """
        shutil.make_archive(output_path_base, "zip", source_dir)

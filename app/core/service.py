import json
import logging
from typing import Any, Callable, Dict, List, Optional

import pandas as pd

from app.core.engine import DocumentEngine
from app.core.ports import JobRepositoryPort, ProcessPort, StoragePort
from app.utils import sanitize_filename

# Configure Logging
logger = logging.getLogger(__name__)


class BatchService:
    """Service for orchestrating document batch processing.

    Handles the core logic of iterating through data rows, processing templates,
    generating documents, and updating job status via the repository.
    """

    def __init__(
        self,
        job_repository: JobRepositoryPort,
        storage: StoragePort,
        process: ProcessPort,
    ):
        """Initializes the BatchService with dependencies.

        Args:
            job_repository (JobRepositoryPort): Port for persisting job status.
            storage (StoragePort): Port for file system operations.
            process (ProcessPort): Port for process execution.
        """
        self.job_repository = job_repository
        self.storage = storage
        self.process = process

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
        # Inject ports into Engine
        engine = DocumentEngine(session_path, self.storage, self.process)
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

            # Prepare Context and handle potential NaN/List issues safely
            context = row.to_dict()
            cleaned_context = {}
            for k, v in context.items():
                if isinstance(v, (list, dict)):
                    cleaned_context[k] = v
                elif pd.isna(v):
                    cleaned_context[k] = None
                else:
                    cleaned_context[k] = v

            # Determine Identifier
            row_identifier = f"Row_{row_num}"
            if filename_col and filename_col in cleaned_context:
                val = str(cleaned_context[filename_col])
                if val.strip():
                    row_identifier = sanitize_filename(val)

            # Setup Target Directory
            if group_folders:
                target_dir = self.storage.join_path(dir_outputs, row_identifier)
            else:
                target_dir = dir_outputs

            self.storage.make_dir(target_dir)

            # Process Each Template
            for tmpl_path in template_paths:
                tmpl_filename = self.storage.basename(tmpl_path)
                tmpl_name_base, tmpl_ext = self.storage.splitext(tmpl_filename)

                final_filename = f"{tmpl_name_base} - {row_identifier}{tmpl_ext}"
                doc_output_path = self.storage.join_path(target_dir, final_filename)

                try:
                    # Render Document
                    if tmpl_ext.lower() == ".docx":
                        await engine.process_docx(
                            tmpl_path, doc_output_path, cleaned_context, dir_assets
                        )
                    elif tmpl_ext.lower() == ".pptx":
                        await engine.process_pptx(
                            tmpl_path, doc_output_path, cleaned_context, dir_assets
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

                # PDF Conversion
                if to_pdf and self.storage.exists(doc_output_path):
                    pdf_result = await self._convert_to_pdf_safe(
                        engine,
                        doc_output_path,
                        target_dir,
                        tmpl_name_base,
                        row_identifier,
                        row_num,
                    )
                    report.append(pdf_result)
                    if pdf_result["Status"] == "Success":
                        total_files_generated += 1

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

    async def process_sample(
        self,
        df: pd.DataFrame,
        template_paths: List[str],
        session_path: str,
        dir_outputs: str,
        dir_assets: str,
        to_pdf: bool,
        filename_col: Optional[str],
    ) -> Dict[str, Any]:
        """Processes a single row (sample) from the DataFrame.

        Used for "Dry Run" or preview functionality. Does not update job repository.

        Args:
            df (pd.DataFrame): The DataFrame containing data (only first row is used).
            template_paths (List[str]): List of absolute paths to template files.
            session_path (str): Path to the session's temporary directory.
            dir_outputs (str): Directory where generated files should be saved.
            dir_assets (str): Directory containing assets.
            to_pdf (bool): Whether to convert generated documents to PDF.
            filename_col (Optional[str]): Column name to use for dynamic file naming.

        Returns:
            Dict[str, Any]: A summary containing the report list and counts.
        """
        engine = DocumentEngine(session_path, self.storage, self.process)
        report = []
        files_generated_count = 0
        row_success = False

        if df.empty:
            return {
                "report": [],
                "total_files": 0,
                "success_rows": 0,
                "total_rows": 0,
            }

        # Target only the first row
        row = df.iloc[0]
        row_num = 1

        # Prepare Context
        context = row.to_dict()
        cleaned_context = {}
        for k, v in context.items():
            if isinstance(v, (list, dict)):
                cleaned_context[k] = v
            elif pd.isna(v):
                cleaned_context[k] = None
            else:
                cleaned_context[k] = v

        # Determine Identifier
        row_identifier = "SAMPLE"
        if filename_col and filename_col in cleaned_context:
            val = str(cleaned_context[filename_col])
            if val.strip():
                row_identifier = sanitize_filename(val)

        # Setup Target Directory (Flat for sample)
        target_dir = dir_outputs

        # Process Each Template
        for tmpl_path in template_paths:
            tmpl_filename = self.storage.basename(tmpl_path)
            tmpl_name_base, tmpl_ext = self.storage.splitext(tmpl_filename)

            # Mark as sample
            final_filename = f"{tmpl_name_base} - {row_identifier} (SAMPLE){tmpl_ext}"
            doc_output_path = self.storage.join_path(target_dir, final_filename)

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
                        "Row": 1,
                        "Identifier": row_identifier,
                        "Output File": final_filename,
                        "Status": "Success",
                        "Error Details": "",
                    }
                )
                files_generated_count += 1
                row_success = True

            except Exception as e:
                report.append(
                    {
                        "Row": 1,
                        "Identifier": row_identifier,
                        "Output File": final_filename,
                        "Status": "Error",
                        "Error Details": str(e),
                    }
                )
                logger.error(f"Error generating sample {final_filename}: {e}")

            # PDF Conversion
            if to_pdf and self.storage.exists(doc_output_path):
                pdf_result = await self._convert_to_pdf_safe(
                    engine,
                    doc_output_path,
                    target_dir,
                    tmpl_name_base,
                    f"{row_identifier} (SAMPLE)",
                    row_num,
                )
                report.append(pdf_result)
                if pdf_result["Status"] == "Success":
                    files_generated_count += 1

        return {
            "report": report,
            "total_files": files_generated_count,
            "success_rows": 1 if row_success else 0,
            "total_rows": 1,
        }

    async def _convert_to_pdf_safe(
        self,
        engine: DocumentEngine,
        doc_path: str,
        target_dir: str,
        tmpl_base: str,
        row_id: str,
        row_num: int,
    ) -> Dict[str, Any]:
        """Helper to safely convert a document to PDF and return a report entry.

        Args:
            engine (DocumentEngine): The document engine instance.
            doc_path (str): Path to the source document.
            target_dir (str): Directory to save the PDF.
            tmpl_base (str): Base name of the template.
            row_id (str): Identifier for the data row.
            row_num (int): Row number.

        Returns:
            Dict[str, Any]: The report entry for the PDF generation.
        """
        pdf_filename = f"{tmpl_base} - {row_id}.pdf"
        try:
            await engine.convert_to_pdf(doc_path, target_dir)
            return {
                "Row": row_num,
                "Identifier": row_id,
                "Output File": pdf_filename,
                "Status": "Success",
                "Error Details": "",
            }
        except Exception as e:
            return {
                "Row": row_num,
                "Identifier": row_id,
                "Output File": pdf_filename,
                "Status": "Error",
                "Error Details": f"PDF Conversion: {str(e)}",
            }

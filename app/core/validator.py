import logging
import os
import re
from typing import Any, Dict, List, Set

from docx import Document
from pptx import Presentation


# Configure Logging
logger = logging.getLogger(__name__)


class TemplateValidator:
    """
    Analyzes template files (DOCX/PPTX) using Regex to extract expected Jinja2 variables.
    This approach is robust against custom filters (pipes) that typically crash
    standard template introspection tools.
    """

    def __init__(self):
        # Regex Explanation:
        # \{\{\s* -> Match opening braces '{{' and optional whitespace
        # ([a-zA-Z0-9_]+) -> Capture Group 1: The Variable Name (alphanumeric + underscore)
        # .*?           -> Non-greedy match of any character (filters, args, spaces)
        # \}\}          -> Match closing braces '}}'
        self.tag_pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+).*?\}\}")

    def _extract_from_text(self, text: str) -> Set[str]:
        """Helper to run regex on a string and return found variables."""
        if not text:
            return set()
        return set(self.tag_pattern.findall(text))

    def extract_tags_from_docx(self, file_path: str) -> Set[str]:
        """
        Extracts tags from a Word document by scanning paragraphs and tables.
        """
        tags = set()
        try:
            doc = Document(file_path)

            # 1. Body Paragraphs
            for paragraph in doc.paragraphs:
                tags.update(self._extract_from_text(paragraph.text))

            # 2. Tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            tags.update(self._extract_from_text(paragraph.text))

            # 3. Headers and Footers (Optional but recommended)
            for section in doc.sections:
                # Headers
                for header in [
                    section.header,
                    section.first_page_header,
                    section.even_page_header,
                ]:
                    if header:
                        for paragraph in header.paragraphs:
                            tags.update(self._extract_from_text(paragraph.text))
                        for table in header.tables:
                            for row in table.rows:
                                for cell in row.cells:
                                    for paragraph in cell.paragraphs:
                                        tags.update(
                                            self._extract_from_text(paragraph.text)
                                        )
                # Footers
                for footer in [
                    section.footer,
                    section.first_page_footer,
                    section.even_page_footer,
                ]:
                    if footer:
                        for paragraph in footer.paragraphs:
                            tags.update(self._extract_from_text(paragraph.text))
                        for table in footer.tables:
                            for row in table.rows:
                                for cell in row.cells:
                                    for paragraph in cell.paragraphs:
                                        tags.update(
                                            self._extract_from_text(paragraph.text)
                                        )

            return tags
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            return set()

    def extract_tags_from_pptx(self, file_path: str) -> Set[str]:
        """
        Extracts tags from a PowerPoint presentation.
        """
        tags = set()
        try:
            prs = Presentation(file_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    # Text Frames
                    if hasattr(shape, "text_frame") and shape.text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            # We join runs to handle cases where formatting splits the tag
                            full_text = "".join([run.text for run in paragraph.runs])
                            tags.update(self._extract_from_text(full_text))

                            # Fallback: Check raw paragraph text if runs failed to join correctly
                            if not tags:
                                tags.update(self._extract_from_text(paragraph.text))

                    # Tables
                    if hasattr(shape, "has_table") and shape.has_table:
                        for row in shape.table.rows:
                            for cell in row.cells:
                                if hasattr(cell, "text_frame") and cell.text_frame:
                                    tags.update(
                                        self._extract_from_text(cell.text_frame.text)
                                    )

            return tags
        except Exception as e:
            logger.error(f"Failed to parse PPTX {file_path}: {e}")
            return set()

    def compare(
        self, excel_headers: List[str], templates_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Compares Excel headers against variables required by templates.
        """
        # Normalize headers (strip whitespace just in case)
        available_vars = set(str(h).strip() for h in excel_headers)
        validation_report = []
        all_valid = True

        for filename, path in templates_map.items():
            ext = os.path.splitext(filename)[1].lower()
            required_vars = set()

            if ext == ".docx":
                required_vars = self.extract_tags_from_docx(path)
            elif ext == ".pptx":
                required_vars = self.extract_tags_from_pptx(path)

            # Find mismatches: Variables in Template that are NOT in Excel
            missing_in_excel = required_vars - available_vars

            status = "OK"
            if missing_in_excel:
                status = "Missing Data"
                all_valid = False

            validation_report.append(
                {
                    "template": filename,
                    "status": status,
                    "missing_vars": list(missing_in_excel),
                    "matched_vars": list(required_vars.intersection(available_vars)),
                }
            )

        return {"overall_valid": all_valid, "details": validation_report}

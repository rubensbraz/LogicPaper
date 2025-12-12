import logging
import os
import re
from typing import Any, Dict, List, Set

from docxtpl import DocxTemplate
from pptx import Presentation


# Configure Logging
logger = logging.getLogger(__name__)


class TemplateValidator:
    """
    Analyzes template files to extract expected Jinja2 variables and
    compares them against provided data headers.
    """

    def extract_tags_from_docx(self, file_path: str) -> Set[str]:
        """
        Extracts undeclared Jinja2 tags from a Word document.

        Args:
            file_path (str): Path to the .docx file.

        Returns:
            Set[str]: A set of variable names found in the template.
        """
        try:
            doc = DocxTemplate(file_path)
            # docxtpl has a built-in method to find variables
            return doc.get_undeclared_template_variables()
        except Exception as e:
            logger.error(f"Failed to parse DOCX {file_path}: {e}")
            return set()

    def extract_tags_from_pptx(self, file_path: str) -> Set[str]:
        """
        Extracts Jinja2 tags from a PowerPoint presentation using Regex.
        Matches patterns like {{ variable_name }} or {{ object.attr }}.

        Args:
            file_path (str): Path to the .pptx file.

        Returns:
            Set[str]: A set of variable names found.
        """
        tags = set()
        # Regex to capture content inside {{ }}.
        # Matches {{ name }} but tries to ignore complex logic like {% if %}
        tag_pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")

        try:
            prs = Presentation(file_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if not shape.has_text_frame:
                        continue
                    for paragraph in shape.text_frame.paragraphs:
                        # Scan the full text of the paragraph (joins runs automatically)
                        text = paragraph.text
                        matches = tag_pattern.findall(text)
                        for match in matches:
                            tags.add(match)
            return tags
        except Exception as e:
            logger.error(f"Failed to parse PPTX {file_path}: {e}")
            return set()

    def compare(
        self, excel_headers: List[str], templates_map: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Compares Excel headers against variables required by templates.

        Args:
            excel_headers (List[str]): Columns found in Excel (Row 1).
            templates_map (Dict[str, str]): Filename -> FilePath map.

        Returns:
            Dict: Report containing missing variables per file.
        """
        # Normalize headers (assuming strict matching based on project rules)
        available_vars = set(excel_headers)
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

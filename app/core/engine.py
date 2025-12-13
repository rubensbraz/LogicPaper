import asyncio
import logging
import os
import re
import subprocess
import zipfile
from typing import Any, Dict, List, Optional

from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage
from jinja2 import Environment
from pptx import Presentation

from app.core.formatter import DataFormatter


# Configure Logging
logger = logging.getLogger(__name__)


class DocumentEngine:
    """
    Core engine to manipulate DOCX/PPTX and convert to PDF.
    Template-based formatting via Jinja2 filters and custom PPTX regex parsing.
    """

    def __init__(self, temp_dir: str):
        """
        Initialize the Engine.

        Args:
            temp_dir (str): Base directory for temporary files.
        """
        self.temp_dir = temp_dir
        self.formatter = DataFormatter()

    def _get_image_object(
        self,
        tpl: DocxTemplate,
        value: Any,
        args: List[str],
        assets_path: str,
    ) -> Any:
        """
        Custom helper to generate InlineImage objects within Jinja2 templates.
        This allows: {{ my_image_filename | format_image('5', '5') }}
        """
        # Use existing strategy to parse dimensions from args
        # value is the filename (string)
        img_data = self.formatter._apply_strategy("image", value, *args)
        filename = img_data.get("filename")

        if not filename or filename == "None":
            return ""

        try:
            img_path = os.path.join(assets_path, filename)
            if not os.path.exists(img_path):
                logger.warning(f"Image not found: {img_path}")
                return "[IMAGE NOT FOUND]"

            width = Cm(float(img_data["width"])) if img_data.get("width") else None
            height = Cm(float(img_data["height"])) if img_data.get("height") else None

            return InlineImage(tpl, img_path, width=width, height=height)
        except Exception as e:
            logger.error(f"Error loading image '{filename}': {e}")
            return "[IMAGE ERROR]"

    def _remove_office_thumbnail(self, file_path: str) -> None:
        """
        Removes the 'docProps/thumbnail.jpeg' from the Office file to fix icon issues.
        """
        try:
            temp_path = f"{file_path}.tmp"
            with zipfile.ZipFile(file_path, "r") as zin:
                with zipfile.ZipFile(temp_path, "w") as zout:
                    for item in zin.infolist():
                        if "thumbnail" not in item.filename.lower():
                            buffer = zin.read(item.filename)
                            zout.writestr(item, buffer)
            os.remove(file_path)
            os.rename(temp_path, file_path)
        except Exception as e:
            logger.warning(f"Could not strip thumbnail from {file_path}: {e}")

    async def process_docx(
        self,
        template_path: str,
        output_path: str,
        context: Dict[str, Any],
        assets_path: str = None,
    ) -> bool:
        """
        Renders a DOCX template using Jinja2 context and Custom Filters.

        Args:
            template_path (str): Path to input template.
            output_path (str): Path where rendered file will be saved.
            context (Dict): Raw data dictionary.
            assets_path (str): Directory containing images.

        Returns:
            bool: True if successful.
        """
        try:
            tpl = DocxTemplate(template_path)

            # 1. Create a fresh Jinja2 Environment
            # This fixes the 'NoneType' object has no attribute 'render_context' error
            jinja_env = Environment(autoescape=True)

            # 2. Register Standard Filters (String, Date, Number, etc.)
            filters = self.formatter.get_jinja_filters()
            jinja_env.filters.update(filters)

            # 3. Register Special Image Filter (Requires closure for 'tpl' and 'assets_path')
            # Usage in DOCX: {{ image_var | format_image(width, height) }}
            def format_image_wrapper(val, *args):
                if not assets_path:
                    return "[NO ASSETS PATH]"
                return self._get_image_object(tpl, val, list(args), assets_path)

            jinja_env.filters["format_image"] = format_image_wrapper

            # 4. Render and Save (Pass the custom env here)
            tpl.render(context, jinja_env=jinja_env)
            tpl.save(output_path)
            self._remove_office_thumbnail(output_path)
            return True

        except Exception as e:
            logger.error(f"DOCX Render Error: {e}")
            raise e

    def _parse_and_replace_pptx_text(self, text: str, context: Dict[str, Any]) -> str:
        """
        Parses PPTX text for pseudo-Jinja tags: {{ var | filter('arg') }}
        and applies the formatting strategies manually.
        """
        # Regex to capture: {{ variable | filter('arg1', 'arg2') }}
        # Group 1: Variable Name
        # Group 2: Full Filter String (optional)
        pattern = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)(\s*\|.*?)?\s*\}\}")

        def replace_match(match):
            var_name = match.group(1)
            filter_part = match.group(2)  # e.g., " | format_string('upper')"

            # Get Raw Value
            value = context.get(var_name, "")

            if not filter_part:
                return str(value)

            # Parse Filter Logic
            # Expected format: | filter_name('arg1', 'arg2')
            try:
                # Remove pipe and whitespace
                content = filter_part.strip().lstrip("|").strip()
                # Split filter name from args: "format_string('upper')" -> "format_string", "'upper'"
                if "(" in content and content.endswith(")"):
                    f_name, args_raw = content.split("(", 1)
                    args_raw = args_raw[:-1]  # Remove trailing )
                else:
                    f_name = content
                    args_raw = ""

                # Parse Args (Naive split by comma, respecting basic quotes)
                # Note: This is a basic parser. Complex nested quotes in PPTX args are limited
                args = []
                if args_raw:
                    # Remove quotes and split
                    parts = args_raw.split(",")
                    args = [p.strip().strip("'").strip('"') for p in parts]

                # Map filter name to Strategy Name
                # "format_date" -> "date"
                strategy_map = {
                    "format_string": "string",
                    "format_number": "number",
                    "format_currency": "number",
                    "format_date": "date",
                    "format_bool": "bool",
                    "format_mask": "mask",
                    "format_logic": "logic",
                }

                # Special handling for aliases
                strat_key = strategy_map.get(f_name)
                final_args = args

                if f_name == "format_currency":
                    strat_key = "number"
                    final_args = ["currency"] + args
                elif f_name == "format_int":
                    strat_key = "number"
                    final_args = ["int"] + args

                if strat_key:
                    return str(
                        self.formatter._apply_strategy(strat_key, value, *final_args)
                    )
                else:
                    # Fallback if unknown filter
                    return str(value)

            except Exception as e:
                logger.error(f"PPTX Filter Error parsing '{filter_part}': {e}")
                return str(value)

        return pattern.sub(replace_match, text)

    async def process_pptx(
        self, template_path: str, output_path: str, context: Dict[str, Any]
    ) -> bool:
        """
        Renders a PPTX by text search/replace with regex support for formatting filters.
        """
        try:
            prs = Presentation(template_path)

            for slide in prs.slides:
                for shape in slide.shapes:
                    if not shape.has_text_frame:
                        continue
                    for paragraph in shape.text_frame.paragraphs:
                        for run in paragraph.runs:
                            # Apply regex replacement on run text
                            # Warning: Splitting runs might break tags if {{ is in one run and }} in another
                            # Assuming tags are within a single run for this implementation
                            if "{{" in run.text:
                                run.text = self._parse_and_replace_pptx_text(
                                    run.text, context
                                )

                    # Handle Tables (Recurse)
                    if shape.has_table:
                        for row in shape.table.rows:
                            for cell in row.cells:
                                for paragraph in cell.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        if "{{" in run.text:
                                            run.text = (
                                                self._parse_and_replace_pptx_text(
                                                    run.text, context
                                                )
                                            )

            prs.save(output_path)
            self._remove_office_thumbnail(output_path)
            return True
        except Exception as e:
            logger.error(f"PPTX Render Error: {e}")
            raise e

    async def convert_to_pdf(self, input_path: str, output_dir: str) -> bool:
        """
        Converts Office files to PDF using LibreOffice Headless via subprocess.
        """
        try:
            cmd = [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_dir,
                input_path,
            ]

            process = await asyncio.to_thread(
                subprocess.run, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if process.returncode != 0:
                logger.error(f"LibreOffice failed: {process.stderr.decode()}")
                raise Exception("PDF Conversion Failed")

            return True
        except Exception as e:
            logger.error(f"PDF Convert Error: {e}")
            raise e

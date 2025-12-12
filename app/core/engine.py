import asyncio
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List

from docx.shared import Cm
from docxtpl import DocxTemplate, InlineImage
from pptx import Presentation

from app.core.formatter import DataFormatter


# Configure Logging
logger = logging.getLogger(__name__)


class DocumentEngine:
    """
    Core engine to manipulate DOCX/PPTX and convert to PDF.
    """

    def __init__(self, temp_dir: str):
        self.temp_dir = temp_dir
        self.formatter = DataFormatter()

    def _get_image_object(self, tpl: DocxTemplate, img_data: Dict, assets_path: str):
        """Helper to create an InlineImage object for DocxTemplate."""
        try:
            img_path = os.path.join(assets_path, img_data["filename"])
            if not os.path.exists(img_path):
                logger.warning(f"Image not found: {img_path}")
                return "[IMAGE NOT FOUND]"

            width = Cm(float(img_data["width"])) if img_data.get("width") else None
            height = Cm(float(img_data["height"])) if img_data.get("height") else None

            return InlineImage(tpl, img_path, width=width, height=height)
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            return "[IMAGE ERROR]"

    async def process_docx(
        self,
        template_path: str,
        output_path: str,
        context: Dict,
        assets_path: str = None,
    ):
        """
        Renders a DOCX template using Jinja2 context.
        """
        try:
            tpl = DocxTemplate(template_path)

            # Pre-process context to look for Image instructions
            final_context = {}
            for key, val in context.items():
                if isinstance(val, dict) and val.get("type") == "image":
                    if assets_path:
                        final_context[key] = self._get_image_object(
                            tpl, val, assets_path
                        )
                    else:
                        final_context[key] = "[NO ASSETS PATH]"
                else:
                    final_context[key] = val

            tpl.render(final_context)
            tpl.save(output_path)
            return True
        except Exception as e:
            logger.error(f"DOCX Render Error: {e}")
            raise e

    async def process_pptx(self, template_path: str, output_path: str, context: Dict):
        """
        Renders a PPTX by simple text search/replace.
        Note: python-pptx does not support Jinja2 tags natively like docxtpl.
        """
        try:
            prs = Presentation(template_path)

            # Helper to replace text in a shape
            def replace_text(shape, replacement_map):
                if not shape.has_text_frame:
                    return
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        for key, val in replacement_map.items():
                            # Simple string check (naive implementation)
                            placeholder = f"{{{{ {key} }}}}"  # {{ var }}
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, str(val))

                            # Also check simple format {{key}}
                            placeholder_simple = f"{{{{{key}}}}}"
                            if placeholder_simple in run.text:
                                run.text = run.text.replace(
                                    placeholder_simple, str(val)
                                )

            for slide in prs.slides:
                for shape in slide.shapes:
                    # Handle Grouped shapes recursion could be added here
                    replace_text(shape, context)
                    # Handle Tables
                    if shape.has_table:
                        for row in shape.table.rows:
                            for cell in row.cells:
                                for (
                                    cell_shape
                                ) in (
                                    cell.text_frame.paragraphs
                                ):  # Treat cell as text frame
                                    for run in cell_shape.runs:
                                        # Re-use logic or adapt if complex
                                        pass

            prs.save(output_path)
            return True
        except Exception as e:
            logger.error(f"PPTX Render Error: {e}")
            raise e

    async def convert_to_pdf(self, input_path: str, output_dir: str):
        """
        Converts Office files to PDF using LibreOffice Headless via subprocess.
        """
        try:
            # Command: soffice --headless --convert-to pdf --outdir <dir> <file>
            # We use a specific user-installation dir to avoid permission/lock issues in Docker
            cmd = [
                "soffice",
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_dir,
                input_path,
            ]

            # Using asyncio.to_thread to not block the event loop with subprocess
            process = await asyncio.to_thread(
                subprocess.run, cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if process.returncode != 0:
                logger.error(f"LibreOffice failed: {process.stderr.decode()}")
                raise Exception("PDF Conversion Failed")

            return True
        except Exception as e:
            logger.error(f"PDF Convert Wrapper Error: {e}")
            raise e

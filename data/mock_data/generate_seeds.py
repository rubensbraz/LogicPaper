import pandas as pd
from docx import Document
from PIL import Image, ImageDraw, ImageFont
import zipfile
import os
import io
import logging
from typing import List, Any


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Determine the directory where THIS script is located
# Inside Docker, this will resolve to /data/mock_data/ because of your volume mapping
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR


def get_path(filename: str) -> str:
    """Helper to ensure file is saved in the script's directory."""
    return os.path.join(OUTPUT_DIR, filename)


def generate_excel(filename: str = "mock_data.xlsx") -> None:
    """
    Generates an Excel file with the specific 3-row structure:
    Row 1: Variable Names
    Row 2: Formatter Protocol
    Row 3+: Data

    Args:
        filename (str): The name of the output file.
    """
    file_path = get_path(filename)
    logger.info(f"Generating Excel at {file_path}...")

    try:
        # Define the structure based on the project schema
        rows: List[List[Any]] = [
            # ROW 1: Headers (Variable Names)
            [
                "client_name",
                "contract_value",
                "start_date",
                "tax_id",
                "risk_level",
                "signature_img",
            ],
            # ROW 2: Protocol (Formatter Rules)
            [
                "string;upper",
                "currency;USD",
                "date;long",
                "mask;###-##-####",
                "string;title",
                "image;4;2",
            ],
            # ROW 3+: Sample Data
            ["John Doe", 15000.50, "2024-01-15", "123456789", "low", "sig_john.png"],
            ["Jane Smith", 2500.00, "2024-02-01", "987654321", "high", "sig_jane.png"],
            ["Acme Corp", 1000000, "2024-03-10", "555666777", "medium", "sig_corp.png"],
        ]

        df_final = pd.DataFrame(rows)

        # Save without header/index because we manually built the headers in Row 1
        df_final.to_excel(file_path, header=False, index=False)
        logger.info("✅ Excel generated.")

    except Exception as e:
        logger.error(f"❌ Excel failed: {e}")


def generate_word_template(filename: str = "template.docx") -> None:
    """
    Generates a Word template with Jinja2 tags compatible with docxtpl.

    Args:
        filename (str): The name of the output file.
    """
    file_path = get_path(filename)
    logger.info(f"Generating Template at: {file_path}")

    try:
        doc = Document()
        doc.add_heading("Service Contract", 0)
        doc.add_paragraph("Agreement between DocGenius Inc. and {{ client_name }}.")

        # --- Table for Client Details ---
        table = doc.add_table(rows=1, cols=2)
        table.style = "Table Grid"
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "Field"
        hdr_cells[1].text = "Value"

        def add_row(label: str, tag: str):
            row_cells = table.add_row().cells
            row_cells[0].text = label
            row_cells[1].text = tag

        add_row("Client Name", "{{ client_name }}")
        add_row("Tax ID", "{{ tax_id }}")
        add_row("Date", "{{ start_date }}")
        add_row("Total Value", "{{ contract_value }}")

        # --- Logic Section ---
        doc.add_paragraph("\nTerms and Conditions:")
        p = doc.add_paragraph("The risk level for this contract is assessed as: ")
        p.add_run("{{ risk_level }}").bold = True

        # Jinja2 Logic Example
        doc.add_paragraph("\n{% if risk_level == 'High' %}")
        doc.add_paragraph(
            "WARNING: This contract requires executive approval due to high risk."
        )
        doc.add_paragraph("{% endif %}")

        # --- Image Section ---
        doc.add_paragraph("\nSignatures:")
        doc.add_paragraph("{{ signature_img }}")

        doc.save(file_path)
        logger.info("✅ Word Template generated.")

    except Exception as e:
        raise e


def generate_assets(zip_name: str = "assets.zip") -> None:
    """
    Generates dummy images on the fly and saves them into a ZIP file.

    Args:
        zip_name (str): The name of the output zip file.
    """
    file_path = get_path(zip_name)
    logger.info(f"Generating Assets at: {file_path}")

    images = ["sig_john.png", "sig_jane.png", "sig_corp.png"]

    try:
        with zipfile.ZipFile(file_path, "w") as zf:
            for img_name in images:
                # Create a simple image using Pillow
                img = Image.new("RGB", (200, 100), color=(240, 240, 240))
                d = ImageDraw.Draw(img)

                # Use default font or fallback logic
                try:
                    font = ImageFont.load_default()
                except IOError:
                    font = None  # Will use default internal mapping

                # Draw text roughly centered
                d.text((10, 40), img_name, fill=(0, 0, 0), font=font)

                # Save to memory buffer then write to zip
                img_buffer = io.BytesIO()
                img.save(img_buffer, format="PNG")
                zf.writestr(img_name, img_buffer.getvalue())

        logger.info("✅ Assets Zip generated.")

    except Exception as e:
        logger.error(f"❌ Assets failed: {e}")


if __name__ == "__main__":
    logger.info("🚀 Starting Seed Generation...")
    generate_excel()
    generate_word_template()
    generate_assets()
    logger.info(f"🏁 Done! Files saved to: {OUTPUT_DIR}")

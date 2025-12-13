import logging
import os
import shutil
import zipfile
from datetime import date
from typing import Tuple

import xlsxwriter
from docx import Document
from docx.shared import Pt
from PIL import Image
from pptx import Presentation

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- Constants ---
# Files will be generated in the same directory as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Temporary folder for generating raw images before zipping
ASSETS_TEMP_DIR = os.path.join(BASE_DIR, ".temp_assets_gen")


# --- Helper Functions ---


def ensure_temp_directory() -> None:
    """Creates the temporary assets directory."""
    os.makedirs(ASSETS_TEMP_DIR, exist_ok=True)


def create_dummy_image(filename: str, color: Tuple[int, int, int]) -> None:
    """
    Creates a simple colored square image for testing.

    Args:
        filename (str): Output filename.
        color (Tuple[int, int, int]): RGB color tuple.
    """
    try:
        ensure_temp_directory()
        img = Image.new("RGB", (200, 200), color)
        path = os.path.join(ASSETS_TEMP_DIR, filename)
        img.save(path)
        logger.info(f"Generated temp image: {path}")
    except Exception as e:
        logger.error(f"Error generating image {filename}: {e}")


def create_assets_zip(zip_filename: str = "assets.zip") -> None:
    """
    Generates dummy images, compresses them into a ZIP file in the base dir,
    and then deletes the source images.

    Args:
        zip_filename (str): Name of the output zip file.
    """
    # 1. Create dummy images in the temp folder
    create_dummy_image("photo_a.jpg", (52, 152, 219))  # Blue
    create_dummy_image("photo_b.jpg", (231, 76, 60))  # Red
    create_dummy_image("signature.png", (46, 204, 113))  # Green

    # 2. Zip them to the main directory
    zip_path = os.path.join(BASE_DIR, zip_filename)
    try:
        with zipfile.ZipFile(zip_path, "w") as zipf:
            for root, _, files in os.walk(ASSETS_TEMP_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Add file to zip with relative path (so they are at root of zip)
                    zipf.write(file_path, os.path.relpath(file_path, ASSETS_TEMP_DIR))
        logger.info(f"Assets ZIP created successfully: {zip_path}")
    except Exception as e:
        logger.error(f"Error creating assets ZIP: {e}")
    finally:
        # 3. Cleanup temp images immediately
        if os.path.exists(ASSETS_TEMP_DIR):
            shutil.rmtree(ASSETS_TEMP_DIR)
            logger.info("Cleaned up temporary assets folder.")


# --- Main Generation Functions ---


def create_excel_data(filename: str = "mock_data.xlsx") -> None:
    """
    Creates the Excel data source file with Header and Raw Data.

    Args:
        filename (str): Output Excel filename.
    """
    filepath = os.path.join(BASE_DIR, filename)

    try:
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet("Data")

        # 1. Define Headers (Variables)
        header_row = [
            "client_id",  # String/Number identifier
            "client_name",  # String
            "contract_date",  # Date object
            "contract_value",  # Float (Currency)
            "completion_rate",  # Float (Percentage)
            "is_active",  # Boolean
            "has_debt",  # Boolean
            "status_code",  # Integer (for Logic mapping)
            "client_photo",  # String (Filename in assets.zip)
            "signature_img",  # String (Filename in assets.zip)
        ]

        # 2. Define Raw Data Rows
        data_row_1 = [
            "CL-12345",
            "Acme Corporation International",
            date(2023, 10, 25),
            150000.50,
            0.985,
            True,
            False,
            10,  # e.g., 10 = Approved
            "photo_a.jpg",
            "signature.png",
        ]

        data_row_2 = [
            "CL-98765",
            "Jane Doe Enterprises LLC",
            date(2024, 1, 15),
            2500.00,
            0.45,
            False,
            True,
            20,  # e.g., 20 = Pending
            "photo_b.jpg",
            "None",  # No signature
        ]

        # Add formats for better readability in Excel
        bold = workbook.add_format({"bold": True})
        date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})
        money_fmt = workbook.add_format({"num_format": "$#,##0.00"})

        # Write Header
        worksheet.write_row(0, 0, header_row, bold)

        # Write Data Row 1
        worksheet.write(1, 0, data_row_1[0])
        worksheet.write(1, 1, data_row_1[1])
        worksheet.write(1, 2, data_row_1[2], date_fmt)
        worksheet.write(1, 3, data_row_1[3], money_fmt)
        worksheet.write(1, 4, data_row_1[4])
        worksheet.write(1, 5, data_row_1[5])
        worksheet.write(1, 6, data_row_1[6])
        worksheet.write(1, 7, data_row_1[7])
        worksheet.write(1, 8, data_row_1[8])
        worksheet.write(1, 9, data_row_1[9])

        # Write Data Row 2
        worksheet.write(2, 0, data_row_2[0])
        worksheet.write(2, 1, data_row_2[1])
        worksheet.write(2, 2, data_row_2[2], date_fmt)
        worksheet.write(2, 3, data_row_2[3], money_fmt)
        worksheet.write(2, 4, data_row_2[4])
        worksheet.write(2, 5, data_row_2[5])
        worksheet.write(2, 6, data_row_2[6])
        worksheet.write(2, 7, data_row_2[7])
        worksheet.write(2, 8, data_row_2[8])
        worksheet.write(2, 9, data_row_2[9])

        workbook.close()
        logger.info(f"Excel data file created successfully: {filepath}")
    except Exception as e:
        logger.error(f"Error creating Excel file: {e}")


def create_word_templates() -> None:
    """
    Creates DOCX templates with formatting tags.
    """
    # --- Template 1: Contract (String, Date, Currency focus) ---
    doc1 = Document()
    doc1.add_heading("SERVICE AGREEMENT", 0)

    p = doc1.add_paragraph("This agreement is made between ")
    # Multi-step string formatting: Title case + prefix
    p.add_run(
        "{{ client_name | format_string('title', 'prefix', 'Client: ') }}"
    ).bold = True
    p.add_run(" and DocGenius Systems.")

    doc1.add_heading("1. Contract Details", level=1)
    p = doc1.add_paragraph()
    p.add_run("Contract ID: ").bold = True
    # Simple string format
    p.add_run("{{ client_id | format_string('upper') }}")
    p.add_run("\nDate Signed: ").bold = True
    # Date format: standard long format
    p.add_run("{{ contract_date | format_date('long') }}")
    p.add_run("\n(Alternative Date Format for International filing: ")
    # Date format: extended format with specific locale (Spain)
    p.add_run("{{ contract_date | format_date('extended', 'es_ES') }}")
    p.add_run(")")

    doc1.add_heading("2. Financial Terms", level=1)
    p = doc1.add_paragraph("The total value of this contract is ")
    # Currency format: US Dollar
    run = p.add_run("{{ contract_value | format_currency('USD') }}")
    run.bold = True
    run.font.size = Pt(14)
    p.add_run(".")

    p = doc1.add_paragraph("Written amount: ")
    # Number spell-out in English
    p.add_run("{{ contract_value | format_number('spell_out', 'en') }}").italic = True
    p.add_run(" dollars.")

    doc1.add_heading("Signatures", level=1)
    p = doc1.add_paragraph("Client Representative:\n\n")
    # Dynamic Image with specific dimensions
    p.add_run("{{ signature_img | format_image('4', '2') }}")

    doc1_path = os.path.join(BASE_DIR, "template_contract.docx")
    doc1.save(doc1_path)
    logger.info(f"Word template 1 created: {doc1_path}")

    # --- Template 2: Technical Report (Advanced features focus) ---
    doc2 = Document()
    doc2.add_heading("CLIENT TECHNICAL PROFILE Status Report", 0)

    # Image with standard size
    p = doc2.add_paragraph()
    p.alignment = 1  # Center
    p.add_run("{{ client_photo | format_image('3', '3') }}")

    doc2.add_heading("System Status & Metrics", level=1)

    # Boolean Checkboxes
    p = doc2.add_paragraph()
    p.add_run("[ ")
    p.add_run("{{ is_active | format_bool('checkbox') }}")
    p.add_run(" ] Account Active status verified.")

    p = doc2.add_paragraph()
    p.add_run("Current Debt Flag: ")
    # Boolean Yes/No
    p.add_run("{{ has_debt | format_bool('yesno') }}").bold = True

    doc2.add_heading("Performance Data", level=2)
    table = doc2.add_table(rows=3, cols=2)
    table.style = "Table Grid"

    row0 = table.rows[0].cells
    row0[0].text = "Metric"
    row0[1].text = "Value / Formatting Demo"

    row1 = table.rows[1].cells
    row1[0].text = "Completion Rate"
    # Number Percentage with 1 decimal place
    row1[1].text = "{{ completion_rate | format_number('percent', '1') }}"

    row2 = table.rows[2].cells
    row2[0].text = "Workflow Status Code"
    # Logic Mapping: Maps integers to readable strings
    row2[1].text = (
        "{{ status_code | format_logic('10=Approved Process', '20=Pending Review', '30=Rejected', 'Unknown Status') }}"
    )

    doc2.add_heading("Raw Data Dump (For Verification)", level=2)
    p = doc2.add_paragraph("Raw Value: {{ contract_value }}")

    doc2_path = os.path.join(BASE_DIR, "template_brief.docx")
    doc2.save(doc2_path)
    logger.info(f"Word template 2 created: {doc2_path}")


def create_powerpoint_template(filename: str = "template_presentation.pptx") -> None:
    """
    Creates a PPTX template with formatting tags.
    """
    prs = Presentation()

    # Slide 1: Title Slide (String and Date formatting)
    slide_layout = prs.slide_layouts[0]  # Title Slide
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    subtitle = slide.placeholders[1]

    # Multi-step string: Title case + Prefix
    title.text = "Client Overview: {{ client_name | format_string('title') }}"
    # Date: Medium format
    subtitle.text = "Generated on: {{ contract_date | format_date('medium') }}"

    # Slide 2: Financial Highlights (Currency and Logic)
    slide_layout = prs.slide_layouts[1]  # Title and Content
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    content = slide.placeholders[1]

    title.text = "Financial & Status Highlights"
    tf = content.text_frame
    tf.text = "Key Metrics:"

    p = tf.add_paragraph()
    # Currency: Brazilian Real
    p.text = "Contract Value (BRL): {{ contract_value | format_currency('BRL') }}"
    p.level = 1

    p = tf.add_paragraph()
    # Logic mapping in PPTX
    p.text = "Current Status: {{ status_code | format_logic('10=Green (Go)', '20=Yellow (Hold)', 'Red (Stop)') }}"
    p.level = 1

    # Slide 3: Boolean Demonstrations
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    title = slide.shapes.title
    content = slide.placeholders[1]

    title.text = "Audit Checkpoints (Boolean Formats)"
    tf = content.text_frame

    p = tf.add_paragraph()
    # Boolean True/False string
    p.text = "Is Active User? -> {{ is_active | format_bool('truefalse') }}"

    p = tf.add_paragraph()
    # Boolean Checkbox visual
    p.text = "Debt Clearance Checkbox: [ {{ has_debt | format_bool('checkbox') }} ]"

    filepath = os.path.join(BASE_DIR, filename)
    try:
        prs.save(filepath)
        logger.info(f"PowerPoint template created: {filepath}")
    except Exception as e:
        logger.error(f"Error creating PowerPoint template: {e}")


if __name__ == "__main__":
    logger.info("--- Generating Seed Data ---")
    # 1. Create Assets Zip First (so Excel can reference images)
    create_assets_zip()
    # 2. Create Raw Excel Data
    create_excel_data()
    # 3. Create Templates
    create_word_templates()
    create_powerpoint_template()
    logger.info(f"--- Seed Generation Complete. Files located in: {BASE_DIR} ---")

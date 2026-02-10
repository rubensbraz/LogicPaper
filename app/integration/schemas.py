from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class GenerationRequest(BaseModel):
    """Schema for the document generation request body."""

    template_path: str = Field(
        ...,
        description="Relative path to the template file stored in the persistent storage volume. Example: 'contracts/v1.docx'",
        examples=["contracts/v1.docx"],
    )
    output_format: str = Field(
        "pdf",
        description="Desired output format of the generated document. Supported: 'docx', 'pptx', 'pdf', 'md', 'txt'.",
        examples=["pdf"],
    )
    filename_col: Optional[str] = Field(
        None,
        description="Column name from the 'data' payload used to generate unique output filenames. If omitted, random UUIDs are used.",
        examples=["client_id"],
    )
    group_by_folders: bool = Field(
        False,
        description="If True, creates a separate folder for each generated row based on the 'filename_col' value.",
    )
    data: List[Dict[str, Any]] = Field(
        ...,
        description="List of JSON objects representing the rows to be processed. Each key corresponds to a variable in the template.",
        examples=[
            [
                {
                    "client_name": "Acme Corp",
                    "contract_date": "2024-01-01",
                    "value": 5000.00,
                }
            ]
        ],
    )
    assets_base64: Optional[str] = Field(
        None,
        description="Base64 encoded ZIP file containing images/assets. If provided, these files within the ZIP will be used for image replacement.",
        examples=["UEsDBBQAAAAIA... (Truncated Base64 String)"],
    )

    @field_validator("output_format")
    def validate_format(cls, v: str) -> str:
        """Validates that the output format is supported."""
        allowed = ["docx", "pptx", "pdf", "md", "txt"]
        if v.lower() not in allowed:
            raise ValueError(f"Unsupported format. Allowed: {', '.join(allowed)}")
        return v.lower()


class JobStatusResponse(BaseModel):
    """Schema for the async job status response."""

    job_id: str = Field(
        ...,
        description="Unique identifier for the processing job. Use this ID to poll status or download results.",
        examples=["job_a1b2c3d4e5"],
    )
    status: str = Field(
        ...,
        description="Current status of the job. Possible values: 'processing', 'completed', 'failed'.",
        examples=["processing"],
    )
    download_url: Optional[str] = Field(
        None,
        description="URL to download the result ZIP file. Only available when status is 'completed'.",
        examples=["/download/job_a1b2c3d4e5"],
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable status message or error details providing context on the current state.",
        examples=["Job initiated successfully."],
    )
    statistics: Optional[Dict[str, Any]] = Field(
        None,
        description="Processing metrics, such as total files generated or rows processed.",
        examples=[{"files": 10, "rows": 10}],
    )

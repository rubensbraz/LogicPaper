from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class GenerationRequest(BaseModel):
    """
    Schema for the document generation request body.
    """

    template_path: str = Field(
        ...,
        description="Relative path to the template file stored in persistent storage. Example: 'contracts/v1.docx'",
    )
    output_format: str = Field(
        "pdf",
        description="Desired output format: 'docx', 'pptx', 'pdf', 'md', or 'txt'.",
    )
    filename_col: Optional[str] = Field(
        None, description="Column name from 'data' used to generate unique filenames."
    )
    group_by_folders: bool = Field(
        False, description="If True, creates a separate folder for each generated row."
    )
    data: List[Dict[str, Any]] = Field(
        ..., description="List of JSON objects representing the rows to be processed."
    )

    @field_validator("output_format")
    def validate_format(cls, v: str) -> str:
        """Validates that the output format is supported."""
        allowed = ["docx", "pptx", "pdf", "md", "txt"]
        if v.lower() not in allowed:
            raise ValueError(f"Unsupported format. Allowed: {', '.join(allowed)}")
        return v.lower()


class JobStatusResponse(BaseModel):
    """
    Schema for the async job status response.
    """

    job_id: str = Field(..., description="Unique identifier for the processing job.")
    status: str = Field(
        ..., description="Current status: 'processing', 'completed', or 'failed'."
    )
    download_url: Optional[str] = Field(
        None, description="URL to download the result ZIP if completed."
    )
    message: Optional[str] = Field(
        None, description="Human-readable status message or error details."
    )
    statistics: Optional[Dict[str, Any]] = Field(
        None, description="Processing metrics (e.g., file count)."
    )

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.core.config import API_KEY


# Define the header key expected in requests
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """
    Validates the API Key provided in the request header.

    Args:
        api_key_header (str): The value of the X-API-Key header.

    Returns:
        str: The valid API key.

    Raises:
        HTTPException: If the key is invalid or missing.
    """
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Invalid or missing API Key credentials.",
    )

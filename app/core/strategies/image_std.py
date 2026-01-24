import logging
from typing import Any, Dict, List

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class ImageStrategy(BaseStrategy):
    """
    Handles Image Metadata formatting.
    """

    def process(self, value: Any, ops: List[str]) -> Dict[str, Any]:
        """
        Parses image dimensions from operations and returns the
        structure expected by the DocumentEngine.
        """
        filename = str(value) if value else ""

        # Default dimensions
        width = None
        height = None

        try:
            # Op 0: Width (Optional)
            if len(ops) > 0:
                raw_w = ops[0].strip()
                if raw_w and raw_w.lower() != "auto":
                    try:
                        width = float(raw_w)
                    except ValueError:
                        logger.warning(f"ImageStrategy: Invalid width '{raw_w}'")

            # Op 1: Height (Optional)
            if len(ops) > 1:
                raw_h = ops[1].strip()
                if raw_h and raw_h.lower() != "auto":
                    try:
                        height = float(raw_h)
                    except ValueError:
                        logger.warning(f"ImageStrategy: Invalid height '{raw_h}'")

            return {
                "type": "image",
                "filename": filename,
                "width": width,
                "height": height,
            }

        except Exception as e:
            logger.error(f"ImageStrategy Error for '{filename}': {e}")
            # Return basic dict to avoid crashing, Engine will handle missing file
            return {
                "type": "image",
                "filename": filename,
                "width": None,
                "height": None,
            }

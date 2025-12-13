import logging
import re
from typing import Any, List

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class StringStrategy(BaseStrategy):
    """
    Handles Advanced String Manipulation with chaining support.

    Supported Operations:
    - Case: upper, lower, title, capitalize, swapcase
    - Format: snake, kebab, slug
    - Modification: trim, reverse
    - Injection (Takes Arg): prefix, suffix
    - Sizing (Takes Arg): truncate
    """

    def process(self, value: Any, ops: List[str]) -> str:
        """
        Applies string transformations based on the operations list.
        """
        # 1. Convert to string safely
        if value is None:
            return ""
        text = str(value)

        # 2. Create an iterator to allow consuming arguments dynamically
        iterator = iter(ops)

        try:
            for op in iterator:
                op = op.lower().strip()

                # --- Case Transformations ---
                if op == "upper":
                    text = text.upper()
                elif op == "lower":
                    text = text.lower()
                elif op == "title":
                    text = text.title()
                elif op == "capitalize":
                    text = text.capitalize()
                elif op == "swapcase":
                    text = text.swapcase()
                elif op == "trim":
                    text = text.strip()
                elif op == "reverse":
                    text = text[::-1]

                # --- Content Injection (Requires Argument) ---
                elif op == "prefix":
                    try:
                        prefix_val = next(iterator)
                        # Handle Excel escaping if necessary
                        prefix_val = prefix_val.replace('"', "")
                        text = f"{prefix_val}{text}"
                    except StopIteration:
                        logger.warning("StringStrategy: 'prefix' missing argument.")

                elif op == "suffix":
                    try:
                        suffix_val = next(iterator)
                        suffix_val = suffix_val.replace('"', "")
                        text = f"{text}{suffix_val}"
                    except StopIteration:
                        logger.warning("StringStrategy: 'suffix' missing argument.")

                # --- Sizing (Requires Argument) ---
                elif op == "truncate":
                    try:
                        limit = int(next(iterator))
                        if len(text) > limit:
                            text = text[:limit] + "..."
                    except (StopIteration, ValueError):
                        logger.warning("StringStrategy: 'truncate' invalid argument.")

                # --- Advanced Formats ---
                elif op == "snake":
                    # "Logic Paper" -> "logic_paper"
                    text = re.sub(r"[\s\-]+", "_", text).lower()
                elif op == "kebab":
                    # "Logic Paper" -> "logic-paper"
                    text = re.sub(r"[\s_]+", "-", text).lower()
                elif op == "slug":
                    # Remove non-alphanumeric, lowercase, dashes
                    text = re.sub(r"[^a-zA-Z0-9\s-]", "", text).lower()
                    text = re.sub(r"[\s]+", "-", text)

        except Exception as e:
            # Fail-safe: Log error but return what we have so far
            logger.error(f"StringStrategy Processing Error: {e} on value '{value}'")
            return text

        return text

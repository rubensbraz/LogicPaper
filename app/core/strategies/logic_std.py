import logging
from typing import Any, List

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class LogicStrategy(BaseStrategy):
    """
    Handles Logical operations, Defaults, and Strict Value Mapping (Switch Case).
    """

    def process(self, value: Any, ops: List[str]) -> Any:
        """
        Process the value through a list of logical operations.

        Args:
            value (Any): The raw data.
            ops (List[str]): List of operation tokens.

        Returns:
            Any: The processed value.
        """
        # Determine if "empty" (None or empty string)
        is_empty = value is None or str(value).strip() == ""

        # Normalize input to string for reliable comparison (e.g. integer 10 vs string "10")
        str_val = str(value).strip() if value is not None else ""

        current_val = value

        # Variable to store the "Else" value (if no key=value map matches)
        mapping_fallback = None

        # Create an iterator to allow consuming arguments dynamically
        iterator = iter(ops)

        try:
            for op in iterator:
                # Store original op for mapping, but use lowercase for keyword check
                raw_op = op
                op_key = op.lower().strip()

                # --- 1. Standard Logic Keywords ---
                if op_key == "default":
                    try:
                        fallback_arg = next(iterator)
                        # Remove Excel quotes if present
                        fallback_arg = fallback_arg.replace('"', "").replace("'", "")

                        # CASE A: Value is Empty -> Use Default immediately
                        if is_empty:
                            return fallback_arg

                        # CASE B: Value exists -> Store this as the potential "Else" fallback
                        # This aligns with documentation: {{ val | format_logic('1=A', 'default', 'Unknown') }}
                        mapping_fallback = fallback_arg

                    except StopIteration:
                        logger.warning("LogicStrategy: Missing 'default' value.")

                elif op_key == "empty_if":
                    try:
                        target = next(iterator)
                        # Compare normalized strings
                        if str_val == target:
                            return ""
                    except StopIteration:
                        pass

                # --- 2. Key-Value Mapping (Switch/Case) ---
                elif "=" in raw_op:
                    # Split only on the first '=' to allow '=' in the value part
                    key, output = raw_op.split("=", 1)

                    # Check if the current value matches this key
                    if str_val == key.strip():
                        # Match found! Returning immediately
                        return output.strip()

                # --- 3. Implicit Fallback Value (Standalone String) ---
                else:
                    # If it's not a keyword and has no '=', treat it as the fallback return
                    # Example: {{ val | format_logic('1=A', 'Unknown') }}
                    mapping_fallback = raw_op

        except Exception as e:
            logger.error(f"LogicStrategy Error: {e}")
            return current_val

        # --- Final Resolution ---
        # If the input was NOT empty, and we found NO mapping match,
        # but we DO have a fallback (from 'default' or implicit), return it
        if not is_empty and mapping_fallback is not None:
            return mapping_fallback

        return current_val

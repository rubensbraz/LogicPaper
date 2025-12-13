import logging
from typing import Any, List

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class LogicStrategy(BaseStrategy):
    """
    Handles Logical operations and Defaults.

    Supported Operations:
    - default;[value]: Returns [value] if input is None or Empty.
    - empty_if;[value]: Returns "" if input matches [value].
    - Mapping: "key=value". Example: "10=Approved". Returns "Approved" if input is "10".
    - Fallback: Any argument without "=" and not a keyword acts as a fallback return value.
    """

    def process(self, value: Any, ops: List[str]) -> Any:
        # Determine if "empty" (None or empty string)
        is_empty = value is None or str(value).strip() == ""

        # Normalize input to string for reliable comparison (e.g. integer 10 vs string "10")
        str_val = str(value).strip() if value is not None else ""

        current_val = value
        mapping_fallback = None  # Stores the "else" value if no map matches

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
                        default_val = next(iterator)
                        # Remove Excel quotes if present
                        default_val = default_val.replace('"', "").replace("'", "")

                        if is_empty:
                            return default_val
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
                        return output.strip()

                # --- 3. Fallback Value (Else) ---
                else:
                    # If it's not a keyword and has no '=', treat it as the fallback return
                    mapping_fallback = raw_op

        except Exception as e:
            logger.error(f"LogicStrategy Error: {e}")
            return current_val

        # If loop finished and we found a fallback (and no map matched earlier), return it
        if mapping_fallback is not None:
            return mapping_fallback

        return current_val

import logging
from typing import Any, List

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class BooleanStrategy(BaseStrategy):
    """
    Handles Boolean logic transformations.
    """

    def process(self, value: Any, ops: List[str]) -> str:
        """
        Converts input to boolean and maps to specific string representation.
        """
        # 1. Normalize Input to Boolean
        bool_val = False
        if isinstance(value, bool):
            bool_val = value
        elif isinstance(value, int):
            bool_val = value == 1
        elif isinstance(value, str):
            v_lower = value.strip().lower()
            bool_val = v_lower in ("true", "t", "yes", "y", "1", "s", "sim", "on")

        # 2. Iterate Operations
        iterator = iter(ops)
        try:
            for op in iterator:
                op = op.lower().strip()

                # --- Custom Mapping (Yes/No, Sim/Não) ---
                # Syntax: bool;TrueVal;FalseVal
                # Note: 'bool' keyword usually consumed by dispatcher, so we look at args
                # But if 'bool' is in the ops list (e.g. from 'bool;Yes;No'), we handle it
                if op == "bool":
                    try:
                        # Peek/Get next arguments
                        # We expect 2 arguments for mapping
                        true_text = next(iterator)
                        false_text = next(iterator)
                        return str(true_text) if bool_val else str(false_text)
                    except StopIteration:
                        # No args provided, return standard string
                        return str(bool_val)

                # --- Presets ---
                elif op == "check":
                    # Checkbox symbols
                    return "☑" if bool_val else "☐"

        except Exception as e:
            logger.error(f"BooleanStrategy Error for '{value}': {e}")
            return str(value)

        # Default fallback
        return str(bool_val)

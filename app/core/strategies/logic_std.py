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
    """

    def process(self, value: Any, ops: List[str]) -> Any:
        # Determine if "empty"
        is_empty = value is None or str(value).strip() == ""

        current_val = value
        iterator = iter(ops)

        try:
            for op in iterator:
                op = op.lower().strip()

                if op == "default":
                    try:
                        default_val = next(iterator)
                        # Remove Excel quotes
                        default_val = default_val.replace('"', "").replace("'", "")

                        if is_empty:
                            return default_val
                    except StopIteration:
                        logger.warning("LogicStrategy: Missing 'default' value.")

                elif op == "empty_if":
                    try:
                        target = next(iterator)
                        if str(current_val) == target:
                            return ""
                    except StopIteration:
                        pass

        except Exception as e:
            logger.error(f"LogicStrategy Error: {e}")
            return current_val

        return current_val

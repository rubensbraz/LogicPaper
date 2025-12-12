import logging
from typing import Any, Dict, List

from app.core.strategies.base import BaseStrategy
from app.core.strategies.boolean_std import BooleanStrategy
from app.core.strategies.date_std import DateStrategy
from app.core.strategies.image_std import ImageStrategy
from app.core.strategies.logic_std import LogicStrategy
from app.core.strategies.mask_std import MaskStrategy
from app.core.strategies.number_std import NumberStrategy
from app.core.strategies.string_std import StringStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class DefaultStrategy(BaseStrategy):
    """Fallback strategy that performs no operation."""

    def process(self, value: Any, ops: List[str]) -> Any:
        return value


class DataFormatter:
    """
    The Central Registry that parses the protocol string and dispatches
    execution to the correct Strategy.
    """

    def __init__(self, locale: str = "pt_BR"):
        self.locale = locale

        # Registry of Strategies
        self.strategies: Dict[str, BaseStrategy] = {
            # Text & Content
            "string": StringStrategy(),
            # Numbers & Finance
            "int": NumberStrategy(locale),
            "float": NumberStrategy(locale),
            "currency": NumberStrategy(locale),
            "percent": NumberStrategy(locale),
            # Dates
            "date": DateStrategy(locale),
            "time": DateStrategy(locale),
            # Logic & Boolean
            "bool": BooleanStrategy(),
            "logic": LogicStrategy(),
            "default": LogicStrategy(),  # Alias for convenience
            # Privacy & Security
            "mask": MaskStrategy(),
            # Rich Media
            "image": ImageStrategy(),
        }
        self.default_strategy = DefaultStrategy()

    def parse_protocol_string(self, protocol_string: str) -> Dict[str, Any]:
        """
        Parses a semi-colon separated string into a Type and a List of Operations.

        Example: "string;upper;prefix;Mr."
        Result: {"type": "string", "ops": ["upper", "prefix", "Mr."]}
        """
        if not protocol_string or str(protocol_string).strip() == "":
            return {"type": "default", "ops": []}

        # 1. Split by semicolon
        parts = str(protocol_string).split(";")

        # 2. Clean whitespace
        parts = [p.strip() for p in parts if p.strip()]

        if not parts:
            return {"type": "default", "ops": []}

        # 3. Extract Head (Type) and Tail (Operations)
        data_type = parts[0].lower()
        ops = parts[1:]

        return {"type": data_type, "ops": ops}

    def parse_protocol(self, protocol_string: str) -> Dict[str, Any]:
        """Legacy wrapper for compatibility."""
        return self.parse_protocol_string(protocol_string)

    def format_value(self, value: Any, protocol: Dict[str, Any]) -> Any:
        """
        Applies the formatting rule to a single value using the Strategy Pattern.
        """
        dtype = protocol.get("type", "default")
        ops = protocol.get("ops", [])

        # Special handling for Logic Strategy (needs to run even if value is None)
        # Other strategies might bail early if value is None
        if value is None and dtype not in ("logic", "default"):
            return ""

        try:
            # 1. Select Strategy
            strategy = self.strategies.get(dtype)

            if strategy:
                return strategy.process(value, ops)

            # 2. Fallback
            return str(value)

        except Exception as e:
            logger.error(f"Formatting failed for {value} with {protocol}: {e}")
            return str(value)

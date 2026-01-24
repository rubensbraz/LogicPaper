import logging
from typing import Any, Callable, Dict, List, Tuple

from app.core.config import settings
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


class DataFormatter:
    """
    Central Registry that acts as a bridge between Template Filters and Strategies.
    Instead of parsing Excel protocols, it now exposes strategies as callable functions
    that accept variable arguments for multi-step processing.
    """

    def __init__(self, locale: str = "pt"):
        """
        Initialize the strategies with the given locale.

        Args:
            locale (str): Locale string (e.g., 'pt', 'en').
        """
        self.locale = locale or settings.DEFAULT_LOCALE

        # Registry of Strategies
        self.strategies: Dict[str, BaseStrategy] = {
            "string": StringStrategy(),
            "number": NumberStrategy(locale),
            "date": DateStrategy(locale),
            "bool": BooleanStrategy(),
            "logic": LogicStrategy(),
            "mask": MaskStrategy(),
            "image": ImageStrategy(),
        }

    def _apply_strategy(self, strategy_name: str, value: Any, *args: str) -> Any:
        """
        Internal helper to execute a specific strategy with variable arguments.

        Args:
            strategy_name (str): The key of the strategy to use.
            value (Any): The raw value to process.
            *args (str): Variable list of operation tokens (e.g., 'upper', 'prefix', 'X').

        Returns:
            Any: The formatted result.
        """
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            logger.warning(
                f"Strategy '{strategy_name}' not found. Returning raw value."
            )
            return value

        # Convert args tuple to list for the Strategy 'process' contract
        ops_list = list(args)
        return strategy.process(value, ops_list)

    def get_jinja_filters(self) -> Dict[str, Callable]:
        """
        Returns a dictionary of filters ready to be registered in the Jinja2 environment.
        This enables syntax like: {{ value | format_string('upper', 'trim') }}

        Returns:
            Dict[str, Callable]: Map of filter name -> wrapper function.
        """
        return {
            "format_string": lambda val, *args: self._apply_strategy(
                "string", val, *args
            ),
            "format_number": lambda val, *args: self._apply_strategy(
                "number", val, *args
            ),
            # Aliases for convenience
            "format_currency": lambda val, *args: self._apply_strategy(
                "number", val, "currency", *args
            ),
            "format_date": lambda val, *args: self._apply_strategy("date", val, *args),
            "format_bool": lambda val, *args: self._apply_strategy("bool", val, *args),
            "format_logic": lambda val, *args: self._apply_strategy(
                "logic", val, *args
            ),
            "format_mask": lambda val, *args: self._apply_strategy("mask", val, *args),
            # Image is handled specially in engine, but logic remains here for parsing dims
            "parse_image_dims": lambda val, *args: self._apply_strategy(
                "image", val, *args
            ),
        }

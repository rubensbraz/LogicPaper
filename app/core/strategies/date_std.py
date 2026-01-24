import logging
from datetime import datetime, timedelta
from typing import Any, List, Union

import babel.dates

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class DateStrategy(BaseStrategy):
    """
    Handles Date and Time transformations with arithmetic support.
    """

    def __init__(self, locale: str = "pt"):
        """
        Initialize the strategies with the given locale.

        Args:
            locale (str): Default locale string (e.g., 'pt', 'en').
        """
        self.locale = locale

    def process(self, value: Any, ops: List[str]) -> str:
        """
        Applies date transformations based on the operations list.

        Args:
            value (Any): The raw input value.
            ops (List[str]): List of operation tokens.

        Returns:
            str: The formatted date string.
        """
        if value is None or str(value).strip() == "":
            return ""

        # 1. Normalize Input into DateTime object
        dt_val = value
        if not isinstance(value, datetime):
            try:
                # Attempt to parse string (ISO format preferred)
                # Excel usually passes datetime objects directly via pandas,
                # but if it's a string, we assume ISO-like format
                dt_val = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                # If fail, log and return original text (fail-safe)
                logger.warning(f"DateStrategy: Could not parse '{value}' as date.")
                return str(value)

        # 2. Pipeline Execution (Index-based for Argument Consumption)
        formatted_result: Union[datetime, str] = dt_val
        i = 0
        total_ops = len(ops)

        # Flag to track if the user explicitly requested a string format
        # If False at the end, we clean up the time component from arithmetic
        format_applied = False

        try:
            while i < total_ops:
                op = ops[i].lower().strip()
                next_token = ops[i + 1] if i + 1 < total_ops else None

                # --- ISO Format (No Arguments) ---
                if op == "iso":
                    if isinstance(formatted_result, datetime):
                        formatted_result = formatted_result.isoformat().split("T")[0]
                        format_applied = True

                # --- Localized Formats (Require Locale Argument) ---
                # Usage example: {{ date | format_date('short', 'pt') }}
                elif op in ("short", "medium", "long", "full"):
                    if next_token and isinstance(formatted_result, datetime):
                        try:
                            # Clean quotes if passed from template
                            target_locale = (
                                next_token.replace('"', "").replace("'", "").strip()
                            )

                            formatted_result = babel.dates.format_date(
                                formatted_result, format=op, locale=target_locale
                            )
                            format_applied = True
                            i += 1  # Consume the locale argument
                        except Exception as e:
                            logger.warning(
                                f"DateStrategy [{op}] error with locale '{next_token}': {e}"
                            )
                    else:
                        logger.warning(
                            f"DateStrategy: '{op}' requires a locale argument (e.g., 'pt')."
                        )

                # --- Custom Format (fmt;%d/%m/%Y) ---
                elif op == "fmt":
                    if next_token and isinstance(formatted_result, datetime):
                        try:
                            # Clean quotes from Excel if present
                            pattern = next_token.replace('"', "").replace("'", "")
                            formatted_result = formatted_result.strftime(pattern)
                            format_applied = True
                            i += 1  # Consume argument
                        except Exception as e:
                            logger.warning(f"DateStrategy [fmt] error: {e}")

                # --- Extractions ---
                elif op == "year":
                    if isinstance(formatted_result, datetime):
                        formatted_result = str(formatted_result.year)
                        format_applied = True

                elif op == "month_name":
                    # Usage example: {{ date | format_date('month_name', 'pt') }}
                    if next_token and isinstance(formatted_result, datetime):
                        try:
                            target_locale = (
                                next_token.replace('"', "").replace("'", "").strip()
                            )
                            # 'MMMM' in Babel means full month name
                            formatted_result = babel.dates.format_date(
                                formatted_result, format="MMMM", locale=target_locale
                            ).title()
                            format_applied = True
                            i += 1  # Consume the locale argument
                        except Exception as e:
                            logger.warning(
                                f"DateStrategy [month_name] error with locale '{next_token}': {e}"
                            )
                    else:
                        logger.warning(
                            "DateStrategy: 'month_name' requires a locale argument (e.g., 'pt')."
                        )

                # --- Arithmetic (Calculations) ---
                # These operations keep the result as a datetime object for further chaining
                # We DO NOT set format_applied = True here, because we want the clean-up logic to run
                elif op == "add_days":
                    if (
                        next_token
                        and self._is_int(next_token)
                        and isinstance(formatted_result, datetime)
                    ):
                        days = int(next_token)
                        formatted_result = formatted_result + timedelta(days=days)
                        i += 1  # Consume argument

                elif op == "add_years":
                    if (
                        next_token
                        and self._is_int(next_token)
                        and isinstance(formatted_result, datetime)
                    ):
                        years = int(next_token)
                        try:
                            formatted_result = formatted_result.replace(
                                year=formatted_result.year + years
                            )
                        except ValueError:
                            # Handle leap year edge case (Feb 29 -> Feb 28)
                            formatted_result = formatted_result + (
                                timedelta(days=365 * years)
                            )
                        i += 1  # Consume argument

                # Advance loop
                i += 1

        except Exception as e:
            logger.error(f"DateStrategy Pipeline Error: {e}")
            return str(value)

        # 3. Final Clean-up
        # If result is still a datetime object and NO format was explicitly requested
        # (e.g. user just did 'add_days' without 'iso'), return strictly the Date part
        # This prevents "2025-01-08 00:00:00" in documents
        if isinstance(formatted_result, datetime) and not format_applied:
            return formatted_result.date().isoformat()

        # Final check: ensure string return
        return str(formatted_result)

    def _is_int(self, val: str) -> bool:
        """Helper to check if a string is a valid integer."""
        try:
            int(val)
            return True
        except ValueError:
            return False

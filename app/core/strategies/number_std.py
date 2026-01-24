import logging
from typing import Any, List, Union

import babel.numbers
import num2words

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class NumberStrategy(BaseStrategy):
    """
    Handles Numerical formatting: Integers, Floats, Currency, and Scientific notation.
    Uses an index-based traversal to support optional arguments intelligently.
    """

    def __init__(self, locale: str = "pt"):
        self.locale = locale

    def process(self, value: Any, ops: List[str]) -> str:
        """
        Applies numerical transformations based on the operations list.

        Args:
            value (Any): The raw input value.
            ops (List[str]): List of operation tokens.

        Returns:
            str: The formatted number string.
        """
        if value is None or str(value).strip() == "":
            return ""

        # 1. Normalize Input to Float/Decimal
        # We try to be smart about "1.200,00" (EU/BR) vs "1,200.00" (US)
        try:
            num_val = self._normalize_to_float(value)
        except ValueError:
            logger.warning(f"NumberStrategy: Invalid input '{value}'")
            return str(value)

        # 2. Pipeline Execution (Index-based for Lookahead support)
        formatted_result: Union[float, int, str] = num_val
        i = 0
        total_ops = len(ops)

        try:
            while i < total_ops:
                op = ops[i].lower().strip()
                next_token = ops[i + 1] if i + 1 < total_ops else None

                # --- Integer Handling ---
                if op == "int":
                    try:
                        int_val = int(num_val)
                        formatted_result = str(int_val)

                        # Lookahead: Check if next token is a format spec (e.g., '04d')
                        # We assume format specs usually start with '0' or are digits
                        if next_token and self._is_format_spec(next_token):
                            formatted_result = format(int_val, next_token)
                            i += 1  # Consume argument
                    except Exception as e:
                        logger.error(f"NumberStrategy [int]: {e}")

                # --- Float Logic ---
                elif op == "float":
                    formatted_result = num_val
                    # Lookahead: Check if next token is precision (integer)
                    if next_token and next_token.isdigit():
                        try:
                            prec = int(next_token)
                            formatted_result = f"{num_val:.{prec}f}"
                            i += 1
                        except ValueError:
                            pass

                elif op in ("round", "precision"):
                    if next_token and next_token.isdigit():
                        try:
                            prec = int(next_token)
                            formatted_result = f"{num_val:.{prec}f}"
                            i += 1
                        except ValueError:
                            pass

                # --- Currency ---
                elif op == "currency":
                    code = "BRL"  # Default
                    if next_token and len(next_token) == 3 and next_token.isalpha():
                        code = next_token.upper()
                        i += 1

                    try:
                        formatted_result = babel.numbers.format_currency(
                            num_val, code, locale=self.locale
                        )
                    except Exception as e:
                        logger.error(f"NumberStrategy [currency]: {e}")

                # --- Percentage ---
                elif op == "percent":
                    try:
                        formatted_result = babel.numbers.format_percent(
                            num_val, locale=self.locale
                        )
                    except Exception:
                        formatted_result = f"{num_val:.0%}"

                # --- Scientific ---
                elif op == "scientific":
                    try:
                        formatted_result = babel.numbers.format_scientific(
                            num_val, locale=self.locale
                        )
                    except Exception:
                        formatted_result = f"{num_val:E}"

                # --- Humanize (1.2k, 1M) ---
                elif op == "humanize":
                    formatted_result = self._humanize_number(num_val)

                # --- Ordinal (1st, 2nd) ---
                elif op == "ordinal":
                    try:
                        # 1. Attempts to capture a specific language from the next argument (e.g., 'en')
                        # If none exists, uses the class default (self.locale)
                        target_lang = self.locale
                        if (
                            i + 1 < len(ops) and len(ops[i + 1]) <= 5
                        ):  # Detect codes like 'en', 'pt_BR'
                            target_lang = ops[i + 1].lower().strip()
                            i += 1  # Consume argument

                        # 2. Convert to int() to remove the ".0" and apply the correct language
                        formatted_result = num2words.num2words(
                            int(num_val), to="ordinal_num", lang=target_lang
                        )
                    except Exception as e:
                        logger.warning(f"Ordinal conversion failed: {e}")
                        formatted_result = f"{int(num_val)}th"

                # --- Spell Out (ten, dez) ---
                elif op == "spell_out":
                    lang = self.locale
                    if (
                        next_token and len(next_token) == 2
                    ):  # Very basic check for lang code
                        lang = next_token
                        i += 1

                    try:
                        formatted_result = num2words.num2words(num_val, lang=lang)
                    except Exception as e:
                        logger.error(f"NumberStrategy [spell_out]: {e}")

                # --- Separator Injection ---
                # Syntax: float;separator;., (Dot thousands, Comma decimal)
                elif op == "separator":
                    if next_token:
                        style = next_token
                        i += 1
                        try:
                            # Force base formatting with 2 decimals
                            val_str = f"{num_val:.2f}"

                            if style == ".,":  # EU/BR: 1.234,56
                                parts = val_str.split(".")
                                integer = "{:,}".format(int(parts[0])).replace(",", ".")
                                formatted_result = f"{integer},{parts[1]}"
                            elif style == ",.":  # US: 1,234.56
                                formatted_result = "{:,.2f}".format(num_val)
                        except Exception as e:
                            logger.error(f"NumberStrategy [separator]: {e}")

                # Advance loop
                i += 1

        except Exception as e:
            logger.error(f"NumberStrategy Pipeline Critical Error: {e}")
            return str(value)

        return str(formatted_result)

    def _normalize_to_float(self, value: Any) -> float:
        """
        Smart conversion of string inputs to float.
        Prioritizes Babel parsing based on locale, falls back to heuristics.
        """
        if isinstance(value, (int, float)):
            return float(value)

        str_val = str(value).strip()

        # 1. Try safe parsing with Babel using the strategy's locale
        try:
            # parse_decimal returns a Decimal, convert to float for consistency
            return float(babel.numbers.parse_decimal(str_val, locale=self.locale))
        except (ValueError, babel.numbers.NumberFormatError):
            pass  # Fallback to manual heuristic

        # 2. Heuristic: If comma exists but no dot, replace comma with dot (EU/BR -> ISO)
        if "," in str_val and "." not in str_val:
            str_val = str_val.replace(",", ".")

        # 3. Heuristic: If both exist, determine which is the thousands separator
        elif "," in str_val and "." in str_val:
            if str_val.find(",") < str_val.find("."):
                # "1,200.50" -> remove comma
                str_val = str_val.replace(",", "")
            else:
                # "1.200,50" -> remove dot, replace comma
                str_val = str_val.replace(".", "").replace(",", ".")

        return float(str_val)

    def _is_format_spec(self, token: str) -> bool:
        """
        Checks if a string looks like a Python format specifier (e.g., '04d', '.2f').
        """
        # Simple heuristic: starts with digit, dot, or aligns
        if not token:
            return False
        return token[0].isdigit() or token.startswith(".") or token in [">", "<", "^"]

    def _humanize_number(self, value: float) -> str:
        """
        Converts 1200 to 1.2K, 1000000 to 1M.
        """
        try:
            value = float(value)
            labels = ["", "K", "M", "B", "T"]
            label_idx = 0
            while abs(value) >= 1000 and label_idx < len(labels) - 1:
                value /= 1000
                label_idx += 1

            # Format to 1 decimal place, remove .0
            res = f"{value:.1f}"
            if res.endswith(".0"):
                res = res[:-2]
            return f"{res}{labels[label_idx]}"
        except:
            return str(value)

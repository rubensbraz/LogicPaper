import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import babel.numbers
import babel.dates


# Configure Logging
logger = logging.getLogger(__name__)


class DataFormatter:
    """
    Handles data transformation based on the 'Formatter Protocol' defined
    in the second row of the Excel file.
    """

    def __init__(self, locale: str = "pt_BR"):
        self.locale = locale

    def parse_protocol(self, protocol_string: str) -> Dict[str, Any]:
        """
        Parses a protocol string like 'currency;BRL' or 'date;%d/%m/%Y'.

        Args:
            protocol_string (str): The raw string from Excel Row 2.

        Returns:
            Dict: A dictionary containing 'type', 'format', and 'options'.
        """
        if not protocol_string or str(protocol_string).strip() == "":
            return {"type": "string", "format": None}

        parts = str(protocol_string).split(";")
        data_type = parts[0].lower().strip()
        fmt = parts[1].strip() if len(parts) > 1 else None
        options = parts[2].strip() if len(parts) > 2 else None

        return {"type": data_type, "format": fmt, "options": options}

    def format_value(self, value: Any, protocol: Dict[str, Any]) -> Any:
        """
        Applies the formatting rule to a single value.
        """
        if value is None:
            return ""

        dtype = protocol.get("type", "string")
        fmt = protocol.get("format")

        try:
            # --- String Handling ---
            if dtype == "string":
                text = str(value)
                if fmt == "upper":
                    return text.upper()
                if fmt == "lower":
                    return text.lower()
                if fmt == "title":
                    return text.title()
                return text

            # --- Integer Handling ---
            elif dtype == "int":
                try:
                    num = int(float(value))  # Handle 10.0 -> 10
                    if fmt:
                        # Handles padding like '04d' -> 0001
                        return format(num, fmt)
                    return num
                except ValueError:
                    return value

            # --- Float Handling ---
            elif dtype == "float":
                try:
                    num = float(value)
                    if fmt:
                        if fmt == ".":
                            return f"{num:.2f}".replace(",", ".")
                        if fmt == ",":
                            return f"{num:.2f}".replace(".", ",")
                        # Assume fmt is precision integer (e.g. '2')
                        try:
                            precision = int(fmt)
                            return round(num, precision)
                        except:
                            pass
                    return num
                except ValueError:
                    return value

            # --- Currency Handling ---
            elif dtype == "currency":
                try:
                    num = float(value)
                    currency_code = fmt if fmt else "BRL"
                    return babel.numbers.format_currency(
                        num, currency_code, locale=self.locale
                    )
                except Exception as e:
                    logger.error(f"Currency error: {e}")
                    return value

            # --- Date Handling ---
            elif dtype == "date":
                # Ensure value is a datetime object
                dt_val = value
                if not isinstance(value, datetime):
                    # Try minimal parsing if it's a string, or fail gracefully
                    return str(value)

                if fmt == "iso":
                    return dt_val.isoformat()
                elif fmt == "long":
                    return babel.dates.format_date(
                        dt_val, format="long", locale=self.locale
                    )
                elif fmt:
                    # Python strftime format
                    return dt_val.strftime(fmt)
                return dt_val.strftime("%d/%m/%Y")

            # --- Mask Handling (Generic) ---
            elif dtype == "mask":
                # Implementation of mask: ###.###.###-##
                if not fmt:
                    return str(value)

                raw_val = str(value)
                # Remove non-alphanumeric chars from value just in case
                clean_val = "".join(filter(str.isalnum, raw_val))

                masked_result = ""
                val_idx = 0

                for char in fmt:
                    if char == "#":
                        if val_idx < len(clean_val):
                            masked_result += clean_val[val_idx]
                            val_idx += 1
                        else:
                            break
                    else:
                        masked_result += char

                return masked_result

            # --- Image Handling ---
            elif dtype == "image":
                # For images, we just return the filename and the dimensions metadata
                # The Engine will handle the actual insertion.
                return {
                    "type": "image",
                    "filename": str(value),
                    "width": fmt,  # e.g., 5
                    "height": protocol.get("options"),  # e.g., 3
                }

            else:
                return str(value)

        except Exception as e:
            logger.error(f"Formatting failed for {value} with {protocol}: {e}")
            return str(value)

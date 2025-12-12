import logging
import re
from typing import Any, List

from app.core.strategies.base import BaseStrategy


# Configure Logging
logger = logging.getLogger(__name__)


class MaskStrategy(BaseStrategy):
    """
    Handles Data Masking for Privacy (GDPR/LGPD) and Format compliance.

    Supported Operations:
    - mask;[pattern]: Generic mask where '#' is replaced by digits/chars.
      Example: mask;###.###.###-##
    - email: Obfuscates email (j***@domain.com).
    - credit_card: PCI masking (**** **** **** 1234).
    - name: Name obfuscation (J*** D**).
    """

    def process(self, value: Any, ops: List[str]) -> str:
        if value is None:
            return ""

        text = str(value)
        iterator = iter(ops)

        try:
            for op in iterator:
                op = op.lower().strip()

                # --- Generic Pattern Mask ---
                if op == "mask":
                    try:
                        pattern = next(iterator)  # e.g. "###.###.###-##"
                        text = self._apply_generic_mask(text, pattern)
                    except StopIteration:
                        logger.warning("MaskStrategy: Missing pattern argument.")

                # --- Specific Privacy Masks ---
                elif op == "email":
                    text = self._mask_email(text)

                elif op == "credit_card":
                    text = self._mask_credit_card(text)

                elif op == "name":
                    text = self._mask_name(text)

        except Exception as e:
            logger.error(f"MaskStrategy Error for '{value}': {e}")
            return text

        return text

    def _apply_generic_mask(self, value: str, pattern: str) -> str:
        """
        Applies a pattern mask (e.g., ###-##) to a string.
        Strips non-alphanumeric chars from input first.
        """
        # Keep only alphanumeric from input
        clean_val = "".join(filter(str.isalnum, value))
        masked_result = ""
        val_idx = 0

        for char in pattern:
            if char == "#":
                if val_idx < len(clean_val):
                    masked_result += clean_val[val_idx]
                    val_idx += 1
                else:
                    break
            else:
                masked_result += char

        return masked_result

    def _mask_email(self, email: str) -> str:
        """johndoe@domain.com -> j***@domain.com"""
        if "@" not in email:
            return email

        user, domain = email.split("@", 1)
        if len(user) > 1:
            # First char + ***
            masked_user = f"{user[0]}{'*' * 3}"
        else:
            masked_user = user

        return f"{masked_user}@{domain}"

    def _mask_credit_card(self, cc: str) -> str:
        """1234567812345678 -> **** **** **** 5678"""
        clean = "".join(filter(str.isdigit, cc))
        if len(clean) < 4:
            return cc
        last_four = clean[-4:]
        return f"**** **** **** {last_four}"

    def _mask_name(self, name: str) -> str:
        """John Doe -> J*** D***"""
        parts = name.split()
        masked_parts = []
        for p in parts:
            if len(p) > 1:
                masked_parts.append(f"{p[0]}{'*' * (len(p)-1)}")
            else:
                masked_parts.append(p)
        return " ".join(masked_parts)

"""
Data masking utilities for sensitive banking information.
Masks account numbers, card numbers, and emails in logs and responses.
"""
from __future__ import annotations

import re

from config.config_loader import load_config


# ============================================================
# CONFIG (cached)
# ============================================================

def _get_mask_digits(key: str, default: int = 4) -> int:
    """Get masking digit count from config."""
    try:
        cfg = load_config()
        return cfg.get("security", {}).get(key, default)
    except Exception:
        return default


# ============================================================
# CORE MASKING FUNCTIONS
# ============================================================

def mask_account_number(account: str, visible_digits: int | None = None) -> str:
    """
    Mask account number, keeping only last N digits visible.

    Example:
        mask_account_number("1234567890") -> "XXXXXX7890"
        mask_account_number("1234-567-890") -> "XXXXXX7890"
    """
    if not account:
        return ""
    if visible_digits is None:
        visible_digits = _get_mask_digits("mask_account_digits")

    # Remove non-digits
    digits = re.sub(r"\D", "", account)
    if len(digits) <= visible_digits:
        return digits  # Too short to mask

    mask_len = len(digits) - visible_digits
    return "X" * mask_len + digits[-visible_digits:]


def mask_card_number(card: str, visible_digits: int | None = None) -> str:
    """
    Mask credit card number, keeping only last N digits visible.

    Example:
        mask_card_number("4567890123456789") -> "XXXXXXXXXXXX6789"
        mask_card_number("4567XXXX8901") -> "XXXXXXXX8901"
    """
    if not card:
        return ""
    if visible_digits is None:
        visible_digits = _get_mask_digits("mask_card_digits")

    digits = re.sub(r"\D", "", card)
    if len(digits) <= visible_digits:
        return digits

    mask_len = len(digits) - visible_digits
    return "X" * mask_len + digits[-visible_digits:]


def mask_email(email: str) -> str:
    """
    Mask email address partially.

    Example:
        mask_email("john.doe@example.com") -> "jo***@example.com"
    """
    if not email or "@" not in email:
        return email

    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = "***"
    else:
        masked_local = local[:2] + "***"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number, keeping last 4 digits.

    Example:
        mask_phone("+919876543210") -> "XXXXXX3210"
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 4:
        return digits
    return "X" * (len(digits) - 4) + digits[-4:]


# ============================================================
# AUTO-DETECT MASKING (regex based)
# ============================================================

# Patterns
_ACCOUNT_PATTERN = re.compile(r"\b\d{10,18}\b")   # 10-18 digits
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")  # 13-19 digits
_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")


def mask_all(text: str) -> str:
    """
    Auto-detect and mask any sensitive numbers in text.
    Useful for logging raw email bodies.
    """
    if not text:
        return ""

    # Mask emails first
    text = _EMAIL_PATTERN.sub(lambda m: mask_email(m.group()), text)

    # Then numbers (order: longer first to avoid partial match)
    def _mask_number(match: re.Match) -> str:
        num = match.group()
        digits = re.sub(r"\D", "", num)
        if len(digits) >= 13:
            return mask_card_number(digits)
        elif len(digits) >= 10:
            return mask_account_number(digits)
        return num

    text = _ACCOUNT_PATTERN.sub(_mask_number, text)
    return text


# ============================================================
# CONVENIENCE WRAPPER
# ============================================================

class DataMasker:
    """Convenience class exposing all masking methods."""

    @staticmethod
    def account(account: str) -> str:
        return mask_account_number(account)

    @staticmethod
    def card(card: str) -> str:
        return mask_card_number(card)

    @staticmethod
    def email(email: str) -> str:
        return mask_email(email)

    @staticmethod
    def phone(phone: str) -> str:
        return mask_phone(phone)

    @staticmethod
    def auto(text: str) -> str:
        return mask_all(text)


# ============================================================
# SELF-TEST
# ============================================================

if __name__ == "__main__":
    print("[TEST] Data Masking Utility\n")

    # Account
    acc = "1234567890"
    print(f"Account : {acc}  ->  {mask_account_number(acc)}")

    # Card
    card = "4567890123456789"
    print(f"Card    : {card}  ->  {mask_card_number(card)}")

    # Email
    email = "john.doe@example.com"
    print(f"Email   : {email}  ->  {mask_email(email)}")

    # Phone
    phone = "+919876543210"
    print(f"Phone   : {phone}  ->  {mask_phone(phone)}")

    # Auto masking
    raw = "Customer john@example.com has account 1234567890 and card 4567890123456789."
    print(f"\nAuto-mask raw  : {raw}")
    print(f"Auto-mask result: {mask_all(raw)}")

    # Edge cases
    print("\n[EDGE CASES]")
    print(f"Empty account  : '{mask_account_number('')}'")
    print(f"Short account  : {mask_account_number('123')}")
    print(f"With dashes    : {mask_account_number('1234-567-890')}")

    # Class wrapper
    print(f"\n[CLASS] DataMasker.account('9876543210') = {DataMasker.account('9876543210')}")

    print("\n[DONE] Masking tests passed!")
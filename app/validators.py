"""Input validation helpers used across service and UI layers."""

from __future__ import annotations

import re
from datetime import date

NI_PATTERN = re.compile(r"^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_PATTERN = re.compile(r"^[+\d\-\s]{7,20}$")


class ValidationError(ValueError):
    pass


def require_non_empty(value: str, field: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValidationError(f"{field} is required")
    return cleaned


def validate_email(value: str) -> str:
    email = require_non_empty(value, "Email")
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Email format is invalid")
    return email.lower()


def validate_phone(value: str) -> str:
    phone = require_non_empty(value, "Phone")
    if not PHONE_PATTERN.match(phone):
        raise ValidationError("Phone format is invalid")
    return phone


def validate_ni(value: str) -> str:
    ni = require_non_empty(value, "National Insurance number").replace(" ", "")
    if not NI_PATTERN.match(ni):
        raise ValidationError("NI number format is invalid")
    return ni.upper()


def validate_positive_money(value: str | float | int, field: str) -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be numeric") from exc

    if amount < 0:
        raise ValidationError(f"{field} must be >= 0")
    return round(amount, 2)


def validate_date_order(start_date: date, end_date: date) -> None:
    if end_date <= start_date:
        raise ValidationError("End date must be after start date")

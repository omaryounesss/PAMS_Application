"""Pure business rules for tenancy, billing, and penalties."""

from __future__ import annotations

from datetime import date


def calculate_early_leave_penalty(monthly_rent: float) -> float:
    return round(float(monthly_rent) * 0.05, 2)


def requires_notice_period(today: date, requested_end_date: date, min_days: int = 30) -> bool:
    return (requested_end_date - today).days >= min_days


def is_invoice_late(due_date: date, paid_at: date | None, today: date) -> bool:
    if paid_at:
        return paid_at > due_date
    return today > due_date

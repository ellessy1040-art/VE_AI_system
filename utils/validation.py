"""
utils/validation.py

Shared validation helpers used across the UI and engines.
"""

from __future__ import annotations

from typing import Dict, Tuple


def validate_weights_sum_100(weights: Dict[str, float]) -> Tuple[bool, str]:
    total = sum(weights.values())
    if abs(total - 100.0) > 0.01:
        return False, f"Criteria weights must sum to 100%. Current total is {total:.2f}%."
    return True, "Weights are valid."


def validate_positive(value: float, field_name: str) -> Tuple[bool, str]:
    if value < 0:
        return False, f"{field_name} cannot be negative."
    return True, "OK"


def validate_discount_rate(rate: float) -> Tuple[bool, str]:
    if not (0 <= rate < 1):
        return False, "Discount rate must be expressed as a fraction between 0 and 1 (e.g. 0.08 for 8%)."
    return True, "OK"


def validate_replacement_year(year: int, analysis_period: int) -> Tuple[bool, str]:
    if year is not None and not (1 <= year <= analysis_period):
        return False, f"Replacement year must be between 1 and {analysis_period}."
    return True, "OK"


def validate_probability_impact(value: int) -> Tuple[bool, str]:
    if not (1 <= value <= 5):
        return False, "Probability/Impact must be between 1 and 5."
    return True, "OK"

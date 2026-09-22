"""
engines/mce_engine.py

Deterministic Multi-Criteria Evaluation (MCE) engine.

Normalization:
    Benefit criteria (higher = better), e.g. Technical Performance:
        r = (x - min(x)) / (max(x) - min(x))

    Cost/Risk criteria (lower = better), e.g. LCC, Risk, Sustainability
    composite index:
        r = (max(x) - x) / (max(x) - min(x))

    Final Score = sum(weight_i * normalized_score_i)

This module NEVER calls the AI and its output is never modified by
the AI layer.
"""

from __future__ import annotations

from typing import Dict, List, Any
import pandas as pd

# Criterion configuration: which criteria are "benefit" (higher better)
# vs "cost" (lower better).
CRITERIA_DIRECTION = {
    "lcc": "cost",
    "performance": "benefit",
    "risk": "cost",
    "sustainability": "cost",  # composite sustainability index: lower = better
}

CRITERIA_LABELS = {
    "lcc": "Life Cycle Cost",
    "performance": "Technical Performance",
    "risk": "Risk",
    "sustainability": "Sustainability",
}


def validate_weights(weights: Dict[str, float]) -> tuple[bool, str]:
    total = sum(weights.values())
    if abs(total - 100.0) > 0.01:
        return False, f"Criteria weights must sum to 100%. Current total: {total:.2f}%"
    return True, "OK"


def _normalize_series(values: pd.Series, direction: str) -> pd.Series:
    vmin, vmax = values.min(), values.max()
    if vmax == vmin:
        # Degenerate case: all alternatives equal on this criterion.
        # Every alternative gets full (equal) credit to avoid div-by-zero.
        return pd.Series([1.0] * len(values), index=values.index)
    if direction == "benefit":
        return (values - vmin) / (vmax - vmin)
    else:  # cost
        return (vmax - values) / (vmax - vmin)


def run_mce(
    raw_data: pd.DataFrame,
    weights: Dict[str, float],
) -> Dict[str, Any]:
    """
    raw_data: DataFrame indexed by alternative name/id with columns
              ['lcc', 'performance', 'risk', 'sustainability'] containing
              the RAW (un-normalized) criterion values.
    weights:  dict with keys lcc/performance/risk/sustainability summing to 100.

    Returns a dict containing the normalized matrix, weighted matrix,
    final scores, and a ranking.
    """
    ok, msg = validate_weights(weights)
    if not ok:
        raise ValueError(msg)

    criteria = list(CRITERIA_DIRECTION.keys())
    normalized = pd.DataFrame(index=raw_data.index)
    weighted = pd.DataFrame(index=raw_data.index)

    for c in criteria:
        direction = CRITERIA_DIRECTION[c]
        normalized[c] = _normalize_series(raw_data[c], direction)
        weighted[c] = normalized[c] * (weights[c] / 100.0)

    final_score = weighted.sum(axis=1)

    result_df = raw_data.copy()
    for c in criteria:
        result_df[f"{c}_normalized"] = normalized[c]
        result_df[f"{c}_weighted"] = weighted[c]
    result_df["final_score"] = final_score
    result_df = result_df.sort_values("final_score", ascending=False)
    result_df["rank"] = range(1, len(result_df) + 1)

    return {
        "raw": raw_data,
        "normalized": normalized,
        "weighted": weighted,
        "result_table": result_df,
        "weights": weights,
        "ranking": list(result_df.index),
    }

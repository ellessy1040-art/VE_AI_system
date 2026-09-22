"""Unit tests for engines/mce_engine.py."""

import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import pytest

from engines.mce_engine import validate_weights, run_mce, _normalize_series


def test_weight_validation_accepts_100_total():
    ok, msg = validate_weights({"lcc": 40, "performance": 25, "risk": 20, "sustainability": 15})
    assert ok is True


def test_weight_validation_rejects_non_100_total():
    ok, msg = validate_weights({"lcc": 40, "performance": 25, "risk": 20, "sustainability": 10})
    assert ok is False
    assert "100%" in msg


def test_normalization_benefit_higher_is_better():
    values = pd.Series([50, 75, 100])
    normalized = _normalize_series(values, "benefit")
    assert normalized.iloc[0] == 0.0
    assert normalized.iloc[2] == 1.0


def test_normalization_cost_lower_is_better():
    values = pd.Series([50, 75, 100])
    normalized = _normalize_series(values, "cost")
    assert normalized.iloc[0] == 1.0
    assert normalized.iloc[2] == 0.0


def test_normalization_handles_all_equal_values_without_div_by_zero():
    values = pd.Series([10, 10, 10])
    normalized = _normalize_series(values, "benefit")
    assert (normalized == 1.0).all()


def test_run_mce_raises_on_invalid_weights():
    raw = pd.DataFrame({
        "lcc": [100, 90], "performance": [80, 90], "risk": [10, 8], "sustainability": [90, 85],
    }, index=["A", "B"])
    with pytest.raises(ValueError):
        run_mce(raw, {"lcc": 50, "performance": 25, "risk": 20, "sustainability": 10})


def test_run_mce_ranks_cheaper_better_alternative_higher_when_lcc_dominant():
    raw = pd.DataFrame({
        "lcc": [100, 50],           # lower better; B is cheaper
        "performance": [80, 80],    # equal
        "risk": [10, 10],           # equal
        "sustainability": [90, 90], # equal
    }, index=["A", "B"])
    result = run_mce(raw, {"lcc": 100, "performance": 0, "risk": 0, "sustainability": 0})
    assert result["result_table"].index[0] == "B"


def test_final_score_is_weighted_sum_of_normalized_scores():
    raw = pd.DataFrame({
        "lcc": [100, 50], "performance": [80, 100], "risk": [20, 10], "sustainability": [100, 80],
    }, index=["A", "B"])
    weights = {"lcc": 40, "performance": 25, "risk": 20, "sustainability": 15}
    result = run_mce(raw, weights)
    for alt in raw.index:
        row = result["result_table"].loc[alt]
        manual_score = sum(row[f"{c}_normalized"] * (weights[c] / 100.0) for c in
                            ["lcc", "performance", "risk", "sustainability"])
        assert math.isclose(row["final_score"], manual_score, rel_tol=1e-9)

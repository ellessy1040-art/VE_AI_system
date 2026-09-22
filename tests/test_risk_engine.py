"""Unit tests for engines/risk_engine.py."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engines.risk_engine import calculate_risk_summary
from data.demo_case import DEFAULT_ALTERNATIVES


def test_risk_score_is_probability_times_impact():
    risks = [{"risk": "Test Risk", "probability": 3, "impact": 4}]
    summary = calculate_risk_summary(risks)
    assert summary["table"].iloc[0]["Score"] == 12


def test_empty_risk_register_returns_zeroes():
    summary = calculate_risk_summary([])
    assert summary["total_risk"] == 0.0
    assert summary["average_risk"] == 0.0


def test_aggregate_metrics_match_manual_calculation():
    risks = [
        {"risk": "A", "probability": 3, "impact": 4},
        {"risk": "B", "probability": 2, "impact": 4},
        {"risk": "C", "probability": 2, "impact": 3},
    ]
    summary = calculate_risk_summary(risks)
    assert summary["total_risk"] == 12 + 8 + 6
    assert summary["average_risk"] == (12 + 8 + 6) / 3
    assert summary["peak_risk"] == 12


def test_residual_risk_lower_than_original_after_mitigation():
    risks = [{"risk": "A", "probability": 4, "impact": 4,
              "residual_probability": 2, "residual_impact": 2}]
    summary = calculate_risk_summary(risks)
    assert summary["total_residual_risk"] < summary["total_risk"]


def test_steel_box_girder_demo_risks_match_spec_example():
    steel_box = next(a for a in DEFAULT_ALTERNATIVES if a["alt_id"] == "ALT_A")
    summary = calculate_risk_summary(steel_box["risks"])
    scores = sorted(summary["table"]["Score"].tolist(), reverse=True)
    assert scores == [12, 8, 6]

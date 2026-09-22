"""Unit tests for engines/sensitivity.py and models/schemas.py validation."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import pytest
from pydantic import ValidationError

from engines.sensitivity import run_sensitivity
from data.demo_case import SENSITIVITY_SCENARIOS
from models.schemas import Alternative, RiskItem, FinancialAssumptions, AIAlternativesResponse


RAW = pd.DataFrame({
    "lcc": [1200, 1050, 1130],
    "performance": [90, 97, 99],
    "risk": [8, 12, 6],
    "sustainability": [100, 84, 91],
}, index=["Baseline", "Steel Box Girder", "Optimized PSC"])


def test_run_sensitivity_produces_result_for_every_scenario():
    result = run_sensitivity(RAW, SENSITIVITY_SCENARIOS)
    assert set(result["scenario_results"].keys()) == set(SENSITIVITY_SCENARIOS.keys())
    assert result["num_scenarios"] == len(SENSITIVITY_SCENARIOS)


def test_rank_table_has_one_row_per_alternative():
    result = run_sensitivity(RAW, SENSITIVITY_SCENARIOS)
    assert len(result["rank_table"]) == len(RAW)


def test_robust_alternative_is_valid_alternative_name():
    result = run_sensitivity(RAW, SENSITIVITY_SCENARIOS)
    assert result["robust_alternative"] in RAW.index


def test_preferred_changes_flag_is_boolean():
    result = run_sensitivity(RAW, SENSITIVITY_SCENARIOS)
    assert isinstance(result["preferred_changes"], bool)


def test_identical_scenarios_never_show_preference_change():
    scenarios = {"S1": {"lcc": 40, "performance": 25, "risk": 20, "sustainability": 15},
                 "S2": {"lcc": 40, "performance": 25, "risk": 20, "sustainability": 15}}
    result = run_sensitivity(RAW, scenarios)
    assert result["preferred_changes"] is False


# ---- Schema validation ----

def test_risk_item_rejects_out_of_range_probability():
    with pytest.raises(ValidationError):
        RiskItem(risk="X", probability=6, impact=3)


def test_financial_assumptions_rejects_invalid_discount_rate():
    with pytest.raises(ValidationError):
        FinancialAssumptions(
            initial_cost=100, annual_operating_cost=10, annual_maintenance_cost=5,
            discount_rate=1.5, analysis_period_years=50,
        )


def test_alternative_schema_accepts_valid_ai_response():
    payload = {
        "alternatives": [
            {
                "alt_id": "ALT_TEST",
                "name": "Test Alternative",
                "principle": "Test principle",
                "function_equivalence": "Equivalent function",
                "risks": [{"risk": "Test Risk", "probability": 2, "impact": 3}],
            }
        ]
    }
    parsed = AIAlternativesResponse(**payload)
    assert parsed.alternatives[0].name == "Test Alternative"
    assert parsed.alternatives[0].review_status.value == "AI_PROPOSED"

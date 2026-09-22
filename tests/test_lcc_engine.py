"""Unit tests for engines/lcc_engine.py using the synthetic demo case."""

import math
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engines.lcc_engine import calculate_lcc, lcc_saving
from data.demo_case import DEFAULT_BASELINE, DEFAULT_ALTERNATIVES


def test_discounting_matches_manual_formula():
    r = 0.08
    N = 5
    result = calculate_lcc(
        initial_cost=1000.0, annual_operating_cost=100.0, annual_maintenance_cost=50.0,
        discount_rate=r, analysis_period_years=N,
    )
    expected_pv_operating = sum(100.0 / ((1 + r) ** t) for t in range(1, N + 1))
    expected_pv_maintenance = sum(50.0 / ((1 + r) ** t) for t in range(1, N + 1))
    assert math.isclose(result["pv_operating_cost"], expected_pv_operating, rel_tol=1e-9)
    assert math.isclose(result["pv_maintenance_cost"], expected_pv_maintenance, rel_tol=1e-9)


def test_replacement_cost_applied_only_at_replacement_year():
    result = calculate_lcc(
        initial_cost=0.0, annual_operating_cost=0.0, annual_maintenance_cost=0.0,
        discount_rate=0.08, analysis_period_years=10,
        replacement_year=5, replacement_cost=1000.0,
    )
    expected_pv_replacement = 1000.0 / (1.08 ** 5)
    assert math.isclose(result["pv_replacement_cost"], expected_pv_replacement, rel_tol=1e-9)

    cashflow = result["cashflow_table"]
    assert cashflow.loc[cashflow["Year"] == 5, "Replacement Cost"].iloc[0] == 1000.0
    other_years = cashflow.loc[cashflow["Year"] != 5, "Replacement Cost"]
    assert (other_years == 0.0).all()


def test_residual_value_reduces_total_lcc():
    base_result = calculate_lcc(
        initial_cost=1000.0, annual_operating_cost=0.0, annual_maintenance_cost=0.0,
        discount_rate=0.08, analysis_period_years=10, residual_value=0.0,
    )
    with_residual = calculate_lcc(
        initial_cost=1000.0, annual_operating_cost=0.0, annual_maintenance_cost=0.0,
        discount_rate=0.08, analysis_period_years=10, residual_value=500.0,
    )
    assert with_residual["total_lcc"] < base_result["total_lcc"]
    expected_pv_residual = 500.0 / (1.08 ** 10)
    assert math.isclose(with_residual["pv_residual_value"], expected_pv_residual, rel_tol=1e-9)


def test_total_lcc_equals_component_sum():
    result = calculate_lcc(
        initial_cost=1_200_000_000.0, annual_operating_cost=5_000_000.0,
        annual_maintenance_cost=12_000_000.0, discount_rate=0.08,
        analysis_period_years=50, replacement_year=30, replacement_cost=300_000_000.0,
        residual_value=50_000_000.0,
    )
    expected_total = (
        result["initial_cost"] + result["pv_operating_cost"] + result["pv_maintenance_cost"]
        + result["pv_replacement_cost"] - result["pv_residual_value"]
    )
    assert math.isclose(result["total_lcc"], expected_total, rel_tol=1e-9)


def test_baseline_case_study_lcc_is_positive_and_reasonable():
    b = DEFAULT_BASELINE
    result = calculate_lcc(
        initial_cost=b["initial_cost"], annual_operating_cost=b["annual_operating_cost"],
        annual_maintenance_cost=b["annual_maintenance_cost"], discount_rate=b["discount_rate"],
        analysis_period_years=b["analysis_period_years"], replacement_year=b["replacement_year"],
        replacement_cost=b["replacement_cost"], residual_value=b["residual_value"],
    )
    assert result["total_lcc"] > b["initial_cost"]  # operating/maintenance add cost
    assert result["total_lcc"] < b["initial_cost"] * 3  # sanity upper bound


def test_lcc_saving_percentage_calculation():
    savings = lcc_saving(baseline_lcc=1000.0, alternative_lcc=900.0)
    assert math.isclose(savings["absolute_saving"], 100.0)
    assert math.isclose(savings["pct_saving"], 10.0)


def test_lcc_saving_handles_zero_baseline_gracefully():
    savings = lcc_saving(baseline_lcc=0.0, alternative_lcc=100.0)
    assert savings["pct_saving"] == 0.0


def test_all_demo_alternatives_calculate_without_error():
    for alt in DEFAULT_ALTERNATIVES:
        cost = alt["cost"]
        result = calculate_lcc(
            initial_cost=cost["initial_cost"], annual_operating_cost=cost["annual_operating_cost"],
            annual_maintenance_cost=cost["annual_maintenance_cost"], discount_rate=0.08,
            analysis_period_years=50, replacement_year=cost["replacement_year"],
            replacement_cost=cost["replacement_cost"], residual_value=cost["residual_value"],
        )
        assert result["total_lcc"] > 0

"""
engines/lcc_engine.py

Deterministic Life-Cycle Cost (LCC) engine.

    LCC = C0 + sum_{t=1..N} [ (Cop,t + Cm,t + Crep,t) / (1+r)^t ]  -  RV / (1+r)^N

This module NEVER calls the AI. All values are calculated from
numeric inputs supplied by the user (synthetic demo values by
default, but fully editable).
"""

from __future__ import annotations

from typing import Dict, Any
import pandas as pd


def build_cashflow_table(
    initial_cost: float,
    annual_operating_cost: float,
    annual_maintenance_cost: float,
    discount_rate: float,
    analysis_period_years: int,
    replacement_year: int | None = None,
    replacement_cost: float = 0.0,
    residual_value: float = 0.0,
) -> pd.DataFrame:
    """Builds a year-by-year (1..N) discounted cash-flow table."""
    rows = []
    for t in range(1, analysis_period_years + 1):
        op = annual_operating_cost
        mn = annual_maintenance_cost
        rep = replacement_cost if (replacement_year is not None and t == replacement_year) else 0.0
        undiscounted = op + mn + rep
        discount_factor = 1.0 / ((1.0 + discount_rate) ** t)
        pv = undiscounted * discount_factor
        rows.append({
            "Year": t,
            "Operating Cost": op,
            "Maintenance Cost": mn,
            "Replacement Cost": rep,
            "Total Cash Flow": undiscounted,
            "Discount Factor": discount_factor,
            "Present Value": pv,
        })
    df = pd.DataFrame(rows)

    # Residual value applied as a negative cash flow at year N
    N = analysis_period_years
    rv_discount_factor = 1.0 / ((1.0 + discount_rate) ** N)
    rv_pv = residual_value * rv_discount_factor
    if len(df) > 0:
        df.loc[df["Year"] == N, "Residual Value"] = residual_value
        df.loc[df["Year"] == N, "Present Value"] = (
            df.loc[df["Year"] == N, "Present Value"] - rv_pv
        )
    df["Residual Value"] = df.get("Residual Value", 0.0).fillna(0.0) if "Residual Value" in df else 0.0
    df["Cumulative PV"] = df["Present Value"].cumsum() + initial_cost
    return df


def calculate_lcc(
    initial_cost: float,
    annual_operating_cost: float,
    annual_maintenance_cost: float,
    discount_rate: float,
    analysis_period_years: int,
    replacement_year: int | None = None,
    replacement_cost: float = 0.0,
    residual_value: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculates the full discounted Life-Cycle Cost breakdown.

    Returns a dict with individual present-value components, the
    total LCC, and the year-by-year cash-flow table.
    """
    N = analysis_period_years
    r = discount_rate

    pv_operating = sum(
        annual_operating_cost / ((1 + r) ** t) for t in range(1, N + 1)
    )
    pv_maintenance = sum(
        annual_maintenance_cost / ((1 + r) ** t) for t in range(1, N + 1)
    )
    pv_replacement = 0.0
    if replacement_year is not None and 1 <= replacement_year <= N and replacement_cost:
        pv_replacement = replacement_cost / ((1 + r) ** replacement_year)

    pv_residual = residual_value / ((1 + r) ** N) if residual_value else 0.0

    total_lcc = initial_cost + pv_operating + pv_maintenance + pv_replacement - pv_residual

    cashflow_df = build_cashflow_table(
        initial_cost=initial_cost,
        annual_operating_cost=annual_operating_cost,
        annual_maintenance_cost=annual_maintenance_cost,
        discount_rate=discount_rate,
        analysis_period_years=analysis_period_years,
        replacement_year=replacement_year,
        replacement_cost=replacement_cost,
        residual_value=residual_value,
    )

    return {
        "initial_cost": initial_cost,
        "pv_operating_cost": pv_operating,
        "pv_maintenance_cost": pv_maintenance,
        "pv_replacement_cost": pv_replacement,
        "pv_residual_value": pv_residual,
        "total_lcc": total_lcc,
        "cashflow_table": cashflow_df,
        "discount_rate": discount_rate,
        "analysis_period_years": analysis_period_years,
    }


def lcc_saving(baseline_lcc: float, alternative_lcc: float) -> Dict[str, float]:
    """
    LCC Saving % = (Baseline LCC - Alternative LCC) / Baseline LCC * 100
    """
    absolute_saving = baseline_lcc - alternative_lcc
    pct_saving = (absolute_saving / baseline_lcc) * 100.0 if baseline_lcc else 0.0
    return {"absolute_saving": absolute_saving, "pct_saving": pct_saving}

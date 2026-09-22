"""
engines/risk_engine.py

Deterministic risk engine.

    Risk Score = Probability x Impact   (both on a 1-5 scale, so max = 25)

Aggregates a risk register into total / average / residual risk
metrics used both for display and as an MCE criterion input.
"""

from __future__ import annotations

from typing import List, Dict, Any
import pandas as pd


def risks_to_dataframe(risks: List[Dict[str, Any]]) -> pd.DataFrame:
    """Convert a list of risk-item dicts into a DataFrame with computed scores."""
    rows = []
    for r in risks:
        prob = int(r.get("probability", 1))
        impact = int(r.get("impact", 1))
        res_prob = int(r.get("residual_probability", prob))
        res_impact = int(r.get("residual_impact", impact))
        rows.append({
            "Risk": r.get("risk", ""),
            "Probability": prob,
            "Impact": impact,
            "Score": prob * impact,
            "Mitigation": r.get("mitigation", ""),
            "Residual Probability": res_prob,
            "Residual Impact": res_impact,
            "Residual Score": res_prob * res_impact,
            "Owner": r.get("owner", ""),
        })
    return pd.DataFrame(rows, columns=[
        "Risk", "Probability", "Impact", "Score", "Mitigation",
        "Residual Probability", "Residual Impact", "Residual Score", "Owner",
    ])


def calculate_risk_summary(risks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates aggregate risk metrics for an alternative (or the baseline)
    from its risk register.
    """
    df = risks_to_dataframe(risks)
    if df.empty:
        return {
            "table": df,
            "total_risk": 0.0,
            "average_risk": 0.0,
            "peak_risk": 0.0,
            "total_residual_risk": 0.0,
            "average_residual_risk": 0.0,
        }
    return {
        "table": df,
        "total_risk": float(df["Score"].sum()),
        "average_risk": float(df["Score"].mean()),
        "peak_risk": float(df["Score"].max()),
        "total_residual_risk": float(df["Residual Score"].sum()),
        "average_residual_risk": float(df["Residual Score"].mean()),
    }

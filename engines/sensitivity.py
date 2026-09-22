"""
engines/sensitivity.py

Sensitivity analysis: re-runs the deterministic MCE engine under
multiple weight scenarios and compares rankings.
"""

from __future__ import annotations

from typing import Dict, Any
import pandas as pd

from engines.mce_engine import run_mce


def run_sensitivity(raw_data: pd.DataFrame, scenarios: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    raw_data: DataFrame indexed by alternative, columns lcc/performance/risk/sustainability
    scenarios: dict of scenario_name -> weights dict

    Returns per-scenario MCE results, a combined ranking table, and
    robustness metrics (which alternative(s) stay on top, whether the
    top choice changes across scenarios).
    """
    scenario_results = {}
    rank_table = pd.DataFrame(index=raw_data.index)
    score_table = pd.DataFrame(index=raw_data.index)

    for scenario_name, weights in scenarios.items():
        mce_result = run_mce(raw_data, weights)
        scenario_results[scenario_name] = mce_result
        result_table = mce_result["result_table"]
        rank_table[scenario_name] = result_table["rank"].reindex(raw_data.index)
        score_table[scenario_name] = result_table["final_score"].reindex(raw_data.index)

    top_choices = {
        scenario_name: res["result_table"].index[0]
        for scenario_name, res in scenario_results.items()
    }
    unique_top_choices = set(top_choices.values())
    preferred_changes = len(unique_top_choices) > 1

    # Robust alternative = the one ranked #1 most often across scenarios
    from collections import Counter
    top_counter = Counter(top_choices.values())
    robust_alternative = top_counter.most_common(1)[0][0]
    robust_alternative_count = top_counter.most_common(1)[0][1]

    return {
        "scenario_results": scenario_results,
        "rank_table": rank_table,
        "score_table": score_table,
        "top_choices": top_choices,
        "preferred_changes": preferred_changes,
        "robust_alternative": robust_alternative,
        "robust_alternative_count": robust_alternative_count,
        "num_scenarios": len(scenarios),
    }

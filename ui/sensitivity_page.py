"""ui/sensitivity_page.py -- Sensitivity Analysis page."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.common import demo_data_banner, render_status, get_accepted_alternatives
from engines.mce_engine import validate_weights
from engines.sensitivity import run_sensitivity
from utils.audit import log_action
from ui.mce_page import build_raw_criteria_dataframe


def render():
    st.title("\U0001F4C8 Sensitivity Analysis")
    demo_data_banner()

    accepted = get_accepted_alternatives()
    if not accepted:
        st.warning("No alternatives are accepted for analysis yet. Go to **AI Alternatives** and "
                   "accept at least one alternative to run sensitivity analysis.")
        return

    if "mce_result_table" not in st.session_state:
        st.info("Run the Multi-Criteria Evaluation page at least once before running sensitivity analysis.")
        return

    scenarios = dict(st.session_state["sensitivity_scenarios"])

    st.markdown("#### Predefined Scenarios")
    st.dataframe(pd.DataFrame(scenarios).T, width='stretch')

    st.markdown("#### Custom Weight Scenario (optional)")
    cw = st.session_state["custom_weights"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cw_lcc = st.number_input("LCC (%)", min_value=0, max_value=100, value=int(cw["lcc"]), key="cw_lcc")
    with c2:
        cw_perf = st.number_input("Performance (%)", min_value=0, max_value=100, value=int(cw["performance"]), key="cw_perf")
    with c3:
        cw_risk = st.number_input("Risk (%)", min_value=0, max_value=100, value=int(cw["risk"]), key="cw_risk")
    with c4:
        cw_sust = st.number_input("Sustainability (%)", min_value=0, max_value=100, value=int(cw["sustainability"]), key="cw_sust")

    include_custom = st.checkbox("Include custom scenario in sensitivity run", value=False)
    custom_weights = {"lcc": cw_lcc, "performance": cw_perf, "risk": cw_risk, "sustainability": cw_sust}
    st.session_state["custom_weights"] = custom_weights

    if include_custom:
        ok, msg = validate_weights(custom_weights)
        if not ok:
            st.error(msg)
        else:
            scenarios["Custom Scenario"] = custom_weights

    if st.button("\u25B6 Run Sensitivity Analysis", type="primary"):
        raw_df = build_raw_criteria_dataframe(accepted)
        sensitivity_result = run_sensitivity(raw_df, scenarios)
        st.session_state["sensitivity_result"] = sensitivity_result
        st.session_state["sensitivity_summary"] = {
            "top_choices": sensitivity_result["top_choices"],
            "preferred_changes": sensitivity_result["preferred_changes"],
            "robust_alternative": sensitivity_result["robust_alternative"],
        }
        log_action("SENSITIVITY_RUN", "Sensitivity Analysis",
                   new_value=f"{len(scenarios)} scenarios, robust={sensitivity_result['robust_alternative']}",
                   source="CALCULATED")
        st.rerun()

    result = st.session_state.get("sensitivity_result")
    if not result:
        st.info("Click **Run Sensitivity Analysis** to compare rankings across scenarios.")
        return

    st.divider()
    st.markdown("#### Ranking Table (by Scenario)")
    render_status("CALCULATED")
    st.dataframe(result["rank_table"], width='stretch')

    st.markdown("#### Final Score Table (by Scenario)")
    st.dataframe(result["score_table"].style.format(precision=3), width='stretch')

    st.markdown("#### Rank Changes Across Scenarios")
    rank_change_df = result["rank_table"].copy()
    rank_change_df["Rank Range"] = rank_change_df.max(axis=1) - rank_change_df.min(axis=1)
    st.dataframe(rank_change_df[["Rank Range"]].sort_values("Rank Range"), width='stretch')

    st.markdown("#### Ranking by Scenario (Chart)")
    melted = result["rank_table"].reset_index().rename(columns={"index": "Alternative"}).melt(
        id_vars="Alternative", var_name="Scenario", value_name="Rank")
    fig = px.line(melted, x="Scenario", y="Rank", color="Alternative", markers=True,
                  title="Rank of Each Alternative Across Weighting Scenarios")
    fig.update_yaxes(autorange="reversed", dtick=1, title="Rank (1 = best)")
    st.plotly_chart(fig, width='stretch')

    st.divider()
    if result["preferred_changes"]:
        st.warning("\u26A0\uFE0F The **preferred (top-ranked) alternative changes** depending on the "
                   "criteria weights used. Review the scenario results carefully before finalizing a decision.")
    else:
        st.success("\u2705 The preferred (top-ranked) alternative is **robust**: it remains the same "
                   "across all scenarios tested.")

    st.info(f"\U0001F3C6 Most frequently top-ranked alternative: **{result['robust_alternative']}** "
            f"({result['robust_alternative_count']} of {result['num_scenarios']} scenarios)")

    st.markdown("##### Top Choice per Scenario")
    for scenario_name, alt_name in result["top_choices"].items():
        st.markdown(f"- **{scenario_name}**: {alt_name}")

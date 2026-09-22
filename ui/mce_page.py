"""ui/mce_page.py -- Multi-Criteria Evaluation (MCE) page."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.common import demo_data_banner, render_status, get_accepted_alternatives, compute_all_lcc
from engines.mce_engine import run_mce, validate_weights, CRITERIA_LABELS
from engines.risk_engine import calculate_risk_summary
from utils.audit import log_action


def build_raw_criteria_dataframe(accepted):
    compute_all_lcc()
    alt_lcc = st.session_state["alternative_lcc"]

    rows = {}
    for alt in accepted:
        lcc_total = alt_lcc[alt["alt_id"]]["total_lcc"]
        performance = alt.get("technical_performance_score") or 0.0
        risk_summary = calculate_risk_summary(alt["risks"])
        risk_value = risk_summary["average_risk"]
        sust = alt["sustainability"]
        sustainability_composite = (
            sust["embodied_carbon_index"] + sust["construction_waste_index"] + sust["operational_energy_index"]
        ) / 3.0
        rows[alt["name"]] = {
            "lcc": lcc_total,
            "performance": performance,
            "risk": risk_value,
            "sustainability": sustainability_composite,
        }
    return pd.DataFrame(rows).T


def render():
    st.title("\u2696\uFE0F Multi-Criteria Evaluation")
    demo_data_banner()

    accepted = get_accepted_alternatives()
    if not accepted:
        st.warning("No alternatives are accepted for analysis yet. Go to **AI Alternatives** and "
                   "accept at least one alternative to run the Multi-Criteria Evaluation.")
        return

    st.markdown("#### Technical Performance Score (editable, 0-100, higher = better)")
    for alt in accepted:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(alt["name"])
        with col2:
            score = st.number_input(
                "Score", min_value=0.0, max_value=100.0,
                value=float(alt.get("technical_performance_score") or 0.0),
                key=f"perf_{alt['alt_id']}", label_visibility="collapsed",
            )
            alt["technical_performance_score"] = score

    st.divider()
    st.markdown("#### Criteria Weights")
    weights = st.session_state["mce_weights"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        w_lcc = st.number_input("Life Cycle Cost (%)", min_value=0, max_value=100, value=int(weights["lcc"]))
    with c2:
        w_perf = st.number_input("Technical Performance (%)", min_value=0, max_value=100, value=int(weights["performance"]))
    with c3:
        w_risk = st.number_input("Risk (%)", min_value=0, max_value=100, value=int(weights["risk"]))
    with c4:
        w_sust = st.number_input("Sustainability (%)", min_value=0, max_value=100, value=int(weights["sustainability"]))

    new_weights = {"lcc": w_lcc, "performance": w_perf, "risk": w_risk, "sustainability": w_sust}
    ok, msg = validate_weights(new_weights)
    if not ok:
        st.error(msg)
    else:
        st.success(msg)
        if new_weights != weights:
            log_action("WEIGHTS_CHANGED", "MCE Weights", old_value=str(weights), new_value=str(new_weights), source="USER_INPUT")
            st.session_state["mce_weights"] = new_weights
            weights = new_weights

    if not ok:
        st.info("Ranking is disabled until the weights sum to exactly 100%.")
        return

    raw_df = build_raw_criteria_dataframe(accepted)
    mce_result = run_mce(raw_df, weights)
    st.session_state["mce_raw_df"] = raw_df
    st.session_state["mce_result"] = mce_result
    st.session_state["mce_result_table"] = mce_result["result_table"]

    st.divider()
    st.markdown("#### Evaluation Matrix")
    render_status("CALCULATED")

    result_table = mce_result["result_table"].copy()
    display_cols = []
    for c in ["lcc", "performance", "risk", "sustainability"]:
        display_cols += [c, f"{c}_normalized", f"{c}_weighted"]
    display_cols += ["final_score", "rank"]
    display_table = result_table[display_cols].rename(columns={
        "lcc": "LCC (raw)", "lcc_normalized": "LCC (norm.)", "lcc_weighted": "LCC (weighted)",
        "performance": "Performance (raw)", "performance_normalized": "Performance (norm.)", "performance_weighted": "Performance (weighted)",
        "risk": "Risk (raw)", "risk_normalized": "Risk (norm.)", "risk_weighted": "Risk (weighted)",
        "sustainability": "Sustainability (raw)", "sustainability_normalized": "Sustainability (norm.)", "sustainability_weighted": "Sustainability (weighted)",
        "final_score": "Final Score", "rank": "Rank",
    })
    st.dataframe(display_table.style.format(precision=3), width='stretch')

    st.markdown("#### MCE Score Comparison")
    score_chart_df = result_table.reset_index().rename(columns={"index": "Alternative"})
    fig_score = px.bar(score_chart_df, x="Alternative",
                        y="final_score", title="Final MCE Score by Alternative", text_auto=".3f")
    fig_score.update_layout(xaxis_title="Alternative", yaxis_title="Final Score")
    st.plotly_chart(fig_score, width='stretch')

    st.markdown("#### Criteria Contribution")
    contrib_df = result_table[["lcc_weighted", "performance_weighted", "risk_weighted", "sustainability_weighted"]].reset_index()
    contrib_df = contrib_df.rename(columns={"index": "Alternative"})
    contrib_melt = contrib_df.melt(id_vars="Alternative", var_name="Criterion", value_name="Weighted Score")
    contrib_melt["Criterion"] = contrib_melt["Criterion"].str.replace("_weighted", "").map(CRITERIA_LABELS)
    fig_contrib = px.bar(contrib_melt, x="Alternative", y="Weighted Score", color="Criterion",
                          title="Weighted Contribution by Criterion", barmode="stack")
    st.plotly_chart(fig_contrib, width='stretch')

    st.markdown("#### Radar Comparison (Normalized Scores)")
    radar_fig = go.Figure()
    categories = [CRITERIA_LABELS[c] for c in ["lcc", "performance", "risk", "sustainability"]]
    for alt_name in result_table.index:
        values = [result_table.loc[alt_name, f"{c}_normalized"] for c in ["lcc", "performance", "risk", "sustainability"]]
        radar_fig.add_trace(go.Scatterpolar(r=values + [values[0]], theta=categories + [categories[0]],
                                             fill="toself", name=alt_name))
    radar_fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), title="Normalized Criteria Comparison")
    st.plotly_chart(radar_fig, width='stretch')

    st.divider()
    top_alt = result_table.index[0]
    st.success(f"\U0001F3C6 Highest-ranked alternative under current weights: **{top_alt}** "
               f"(Final Score: {result_table.loc[top_alt, 'final_score']:.3f})")

    log_action("MCE_CALCULATED", "MCE Result", new_value=f"top={top_alt}", source="CALCULATED")

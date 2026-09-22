"""ui/risk_page.py -- Risk Analysis page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.common import demo_data_banner, render_status, get_accepted_alternatives
from engines.risk_engine import calculate_risk_summary
from utils.audit import log_action
from utils.validation import validate_probability_impact


def _risk_matrix_figure(all_points):
    fig = px.scatter(
        all_points, x="Probability", y="Impact", color="Alternative", text="Risk",
        size="Score", size_max=30, title="Risk Matrix (Probability x Impact)",
        range_x=[0.5, 5.5], range_y=[0.5, 5.5],
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(xaxis=dict(dtick=1), yaxis=dict(dtick=1))
    return fig


def render():
    st.title("\u26A0\uFE0F Risk Analysis")
    demo_data_banner()

    accepted = get_accepted_alternatives()
    if not accepted:
        st.warning("No alternatives are accepted for analysis yet. Go to **AI Alternatives** and "
                   "accept at least one alternative to run risk analysis.")
        return

    baseline_summary = calculate_risk_summary(st.session_state["baseline_risks"])
    st.session_state["baseline_risk_summary"] = baseline_summary

    st.markdown("#### Baseline Risk Register")
    render_status("SYNTHETIC_DEMO")
    st.dataframe(baseline_summary["table"], width='stretch')
    b1, b2, b3 = st.columns(3)
    b1.metric("Total Risk", f"{baseline_summary['total_risk']:.0f}")
    b2.metric("Average Risk", f"{baseline_summary['average_risk']:.2f}")
    b3.metric("Average Residual Risk", f"{baseline_summary['average_residual_risk']:.2f}")

    st.divider()
    st.markdown("#### Alternative Risk Registers")

    all_points_rows = []
    risk_results = {}

    for alt in accepted:
        st.markdown(f"##### {alt['name']}")
        render_status(alt.get("engineering_data_status", "SYNTHETIC_DEMO"))

        risks = alt["risks"]
        edited_risks = []
        for j, r in enumerate(risks):
            with st.container(border=True):
                c1, c2, c3, c4, c5, c6, c7 = st.columns([2, 1, 1, 2, 1, 1, 1.4])
                with c1:
                    name = st.text_input("Risk", value=r["risk"], key=f"risk_name_{alt['alt_id']}_{j}")
                with c2:
                    prob = st.number_input("Prob (1-5)", min_value=1, max_value=5, value=int(r["probability"]), key=f"risk_p_{alt['alt_id']}_{j}")
                with c3:
                    impact = st.number_input("Impact (1-5)", min_value=1, max_value=5, value=int(r["impact"]), key=f"risk_i_{alt['alt_id']}_{j}")
                with c4:
                    mitigation = st.text_input("Mitigation", value=r.get("mitigation", ""), key=f"risk_m_{alt['alt_id']}_{j}")
                with c5:
                    res_prob = st.number_input("Res. Prob", min_value=1, max_value=5, value=int(r.get("residual_probability", r["probability"])), key=f"risk_rp_{alt['alt_id']}_{j}")
                with c6:
                    res_impact = st.number_input("Res. Impact", min_value=1, max_value=5, value=int(r.get("residual_impact", r["impact"])), key=f"risk_ri_{alt['alt_id']}_{j}")
                with c7:
                    owner = st.text_input("Owner", value=r.get("owner", ""), key=f"risk_o_{alt['alt_id']}_{j}")
                edited_risks.append({
                    "risk": name, "probability": int(prob), "impact": int(impact),
                    "mitigation": mitigation, "residual_probability": int(res_prob),
                    "residual_impact": int(res_impact), "owner": owner,
                })

        if st.button("Save Risk Register", key=f"save_risks_{alt['alt_id']}"):
            alt["risks"] = edited_risks
            log_action("RISK_UPDATED", f"Alternative:{alt['alt_id']}", new_value=f"{len(edited_risks)} risks", source="USER_INPUT")
            st.success("Risk register updated.")
            st.rerun()

        summary = calculate_risk_summary(alt["risks"])
        risk_results[alt["alt_id"]] = summary
        st.dataframe(summary["table"], width='stretch')
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Risk", f"{summary['total_risk']:.0f}")
        m2.metric("Average Risk", f"{summary['average_risk']:.2f}")
        m3.metric("Peak Risk", f"{summary['peak_risk']:.0f}")
        m4.metric("Average Residual Risk", f"{summary['average_residual_risk']:.2f}")

        for r in alt["risks"]:
            all_points_rows.append({"Alternative": alt["name"], "Risk": r["risk"],
                                     "Probability": r["probability"], "Impact": r["impact"],
                                     "Score": r["probability"] * r["impact"]})
        st.divider()

    st.session_state["risk_results"] = risk_results
    st.session_state["risk_results_summary"] = {
        alt_id: {"total_risk": v["total_risk"], "average_risk": v["average_risk"],
                  "average_residual_risk": v["average_residual_risk"]}
        for alt_id, v in risk_results.items()
    }

    if all_points_rows:
        st.markdown("#### Combined Risk Matrix")
        matrix_df = pd.DataFrame(all_points_rows)
        st.plotly_chart(_risk_matrix_figure(matrix_df), width='stretch')

    log_action("RISK_CALCULATED", "All Alternatives", new_value=f"{len(accepted)} alternatives", source="CALCULATED")

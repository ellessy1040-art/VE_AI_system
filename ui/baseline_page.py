"""ui/baseline_page.py -- Baseline definition + baseline LCC calculation."""

import streamlit as st
import plotly.express as px

from ui.common import demo_data_banner, render_status, compute_baseline_lcc, currency_fmt
from utils.audit import log_action
from utils.validation import validate_discount_rate, validate_replacement_year


def render():
    st.title("\U0001F3D7\uFE0F Baseline")
    demo_data_banner()

    baseline = st.session_state["baseline"]
    st.subheader(baseline["name"])
    render_status(baseline.get("data_status", "SYNTHETIC_DEMO"))

    st.divider()
    st.markdown("#### Edit Baseline Financial Assumptions")
    with st.form("baseline_form"):
        c1, c2 = st.columns(2)
        with c1:
            initial_cost = st.number_input("Initial Construction Cost (EGP)", value=float(baseline["initial_cost"]), step=1_000_000.0, format="%.0f")
            annual_operating = st.number_input("Annual Operating Cost (EGP)", value=float(baseline["annual_operating_cost"]), step=100_000.0, format="%.0f")
            annual_maintenance = st.number_input("Annual Maintenance Cost (EGP)", value=float(baseline["annual_maintenance_cost"]), step=100_000.0, format="%.0f")
        with c2:
            replacement_year = st.number_input("Replacement Event Year", value=int(baseline["replacement_year"]), step=1)
            replacement_cost = st.number_input("Replacement Cost (EGP)", value=float(baseline["replacement_cost"]), step=1_000_000.0, format="%.0f")
            residual_value = st.number_input("Residual Value at End of Analysis Period (EGP)", value=float(baseline["residual_value"]), step=1_000_000.0, format="%.0f")

        c3, c4 = st.columns(2)
        with c3:
            discount_rate_pct = st.number_input("Discount Rate (%)", value=float(baseline["discount_rate"] * 100), step=0.5)
        with c4:
            analysis_period = st.number_input("Analysis Period (years)", value=int(baseline["analysis_period_years"]), step=1)

        submitted = st.form_submit_button("Save Baseline & Recalculate LCC")
        if submitted:
            ok1, msg1 = validate_discount_rate(discount_rate_pct / 100.0)
            ok2, msg2 = validate_replacement_year(int(replacement_year), int(analysis_period))
            if not ok1:
                st.error(msg1)
            elif not ok2:
                st.error(msg2)
            else:
                old = dict(baseline)
                baseline.update({
                    "initial_cost": initial_cost,
                    "annual_operating_cost": annual_operating,
                    "annual_maintenance_cost": annual_maintenance,
                    "replacement_year": int(replacement_year),
                    "replacement_cost": replacement_cost,
                    "residual_value": residual_value,
                    "discount_rate": discount_rate_pct / 100.0,
                    "analysis_period_years": int(analysis_period),
                    "data_status": "USER_INPUT",
                })
                st.session_state["baseline"] = baseline
                log_action("BASELINE_UPDATED", "Baseline", old_value=str(old), new_value=str(baseline), source="USER_INPUT")
                st.success("Baseline updated.")
                st.rerun()

    st.divider()
    st.markdown("#### Baseline Life-Cycle Cost (LCC)")
    render_status("CALCULATED")
    result = compute_baseline_lcc()
    log_action("LCC_CALCULATED", "Baseline LCC", new_value=f"{result['total_lcc']:.0f}", source="CALCULATED")

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Initial Cost", currency_fmt(result["initial_cost"]))
    k2.metric("PV Operating", currency_fmt(result["pv_operating_cost"]))
    k3.metric("PV Maintenance", currency_fmt(result["pv_maintenance_cost"]))
    k4.metric("PV Replacement", currency_fmt(result["pv_replacement_cost"]))
    k5.metric("PV Residual (\u2212)", currency_fmt(result["pv_residual_value"]))
    k6.metric("Total LCC", currency_fmt(result["total_lcc"]))

    st.markdown("##### 50-Year Discounted Cash-Flow Table")
    st.dataframe(result["cashflow_table"], width='stretch', height=320)

    fig = px.line(result["cashflow_table"], x="Year", y="Cumulative PV",
                   title="Cumulative Discounted Life-Cycle Cost (Baseline)")
    fig.update_layout(yaxis_title=f"Cumulative PV ({st.session_state['project']['currency']})")
    st.plotly_chart(fig, width='stretch')

"""ui/lcc_page.py -- LCC Analysis page: baseline vs. accepted alternatives."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.common import (
    demo_data_banner, render_status, compute_all_lcc, get_accepted_alternatives, currency_fmt,
)
from engines.lcc_engine import lcc_saving
from utils.audit import log_action
from utils.validation import validate_replacement_year


def render():
    st.title("\U0001F4B0 LCC Analysis")
    demo_data_banner()

    accepted = get_accepted_alternatives()
    if not accepted:
        st.warning("No alternatives are accepted for analysis yet. Go to **AI Alternatives** and "
                   "accept at least one alternative to run LCC analysis.")
        return

    st.markdown("#### Edit Alternative Financial Assumptions")
    baseline = st.session_state["baseline"]
    for alt in accepted:
        with st.expander(f"{alt['name']} \u2014 financial assumptions", expanded=False):
            render_status(alt.get("engineering_data_status", "SYNTHETIC_DEMO"))
            cost = alt["cost"]
            c1, c2, c3 = st.columns(3)
            with c1:
                initial_cost = st.number_input("Initial Cost (EGP)", value=float(cost["initial_cost"]), key=f"ic_{alt['alt_id']}", step=1_000_000.0, format="%.0f")
                op_cost = st.number_input("Annual Operating Cost (EGP)", value=float(cost["annual_operating_cost"]), key=f"op_{alt['alt_id']}", step=100_000.0, format="%.0f")
            with c2:
                maint_cost = st.number_input("Annual Maintenance Cost (EGP)", value=float(cost["annual_maintenance_cost"]), key=f"mn_{alt['alt_id']}", step=100_000.0, format="%.0f")
                rep_year = st.number_input("Replacement Year", value=int(cost.get("replacement_year") or 30), key=f"ry_{alt['alt_id']}", step=1)
            with c3:
                rep_cost = st.number_input("Replacement Cost (EGP)", value=float(cost.get("replacement_cost") or 0.0), key=f"rc_{alt['alt_id']}", step=1_000_000.0, format="%.0f")
                res_val = st.number_input("Residual Value (EGP)", value=float(cost.get("residual_value") or 0.0), key=f"rv_{alt['alt_id']}", step=1_000_000.0, format="%.0f")

            if st.button("Save", key=f"save_cost_{alt['alt_id']}"):
                ok, msg = validate_replacement_year(int(rep_year), int(baseline["analysis_period_years"]))
                if not ok:
                    st.error(msg)
                else:
                    old = dict(cost)
                    cost.update({
                        "initial_cost": initial_cost,
                        "annual_operating_cost": op_cost,
                        "annual_maintenance_cost": maint_cost,
                        "replacement_year": int(rep_year),
                        "replacement_cost": rep_cost,
                        "residual_value": res_val,
                    })
                    alt["cost"] = cost
                    alt["engineering_data_status"] = "USER_INPUT"
                    log_action("ALTERNATIVE_COST_UPDATED", f"Alternative:{alt['alt_id']}", old_value=str(old), new_value=str(cost), source="USER_INPUT")
                    st.success("Financial assumptions updated.")
                    st.rerun()

    compute_all_lcc()
    baseline_lcc = st.session_state["baseline_lcc"]
    alt_lcc = st.session_state["alternative_lcc"]

    st.divider()
    st.markdown("#### LCC Summary")
    render_status("CALCULATED")

    rows = []
    rows.append({
        "Alternative": st.session_state["baseline"]["name"],
        "Initial Cost": baseline_lcc["initial_cost"],
        "PV Operating": baseline_lcc["pv_operating_cost"],
        "PV Maintenance": baseline_lcc["pv_maintenance_cost"],
        "PV Replacement": baseline_lcc["pv_replacement_cost"],
        "PV Residual": -baseline_lcc["pv_residual_value"],
        "Total LCC": baseline_lcc["total_lcc"],
        "Saving vs Baseline": 0.0,
        "Saving % vs Baseline": 0.0,
    })
    for alt in accepted:
        r = alt_lcc[alt["alt_id"]]
        saving = lcc_saving(baseline_lcc["total_lcc"], r["total_lcc"])
        rows.append({
            "Alternative": alt["name"],
            "Initial Cost": r["initial_cost"],
            "PV Operating": r["pv_operating_cost"],
            "PV Maintenance": r["pv_maintenance_cost"],
            "PV Replacement": r["pv_replacement_cost"],
            "PV Residual": -r["pv_residual_value"],
            "Total LCC": r["total_lcc"],
            "Saving vs Baseline": saving["absolute_saving"],
            "Saving % vs Baseline": saving["pct_saving"],
        })
    summary_df = pd.DataFrame(rows)
    st.dataframe(
        summary_df.style.format({
            "Initial Cost": "{:,.0f}", "PV Operating": "{:,.0f}", "PV Maintenance": "{:,.0f}",
            "PV Replacement": "{:,.0f}", "PV Residual": "{:,.0f}", "Total LCC": "{:,.0f}",
            "Saving vs Baseline": "{:,.0f}", "Saving % vs Baseline": "{:.2f}%",
        }),
        width='stretch',
    )
    st.session_state["lcc_summary_df"] = summary_df

    kcols = st.columns(len(rows))
    for col, row in zip(kcols, rows):
        col.metric(row["Alternative"][:22], currency_fmt(row["Total LCC"]),
                   delta=f"{row['Saving % vs Baseline']:.1f}%" if row["Alternative"] != st.session_state["baseline"]["name"] else None)

    st.divider()
    st.markdown("#### LCC Comparison")
    fig_bar = px.bar(summary_df, x="Alternative", y="Total LCC", title="Total Life-Cycle Cost Comparison",
                      text_auto=".2s")
    st.plotly_chart(fig_bar, width='stretch')

    st.markdown("#### LCC Component Breakdown")
    breakdown_df = summary_df.melt(
        id_vars="Alternative",
        value_vars=["Initial Cost", "PV Operating", "PV Maintenance", "PV Replacement", "PV Residual"],
        var_name="Component", value_name="Value",
    )
    fig_stack = px.bar(breakdown_df, x="Alternative", y="Value", color="Component",
                        title="LCC Component Breakdown (Present Value)")
    st.plotly_chart(fig_stack, width='stretch')

    st.markdown("#### Cumulative Discounted Cost Over Time")
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=baseline_lcc["cashflow_table"]["Year"], y=baseline_lcc["cashflow_table"]["Cumulative PV"],
        name=st.session_state["baseline"]["name"], mode="lines",
    ))
    for alt in accepted:
        r = alt_lcc[alt["alt_id"]]
        fig_cum.add_trace(go.Scatter(x=r["cashflow_table"]["Year"], y=r["cashflow_table"]["Cumulative PV"],
                                      name=alt["name"], mode="lines"))
    fig_cum.update_layout(title="Cumulative Discounted Life-Cycle Cost", xaxis_title="Year",
                           yaxis_title=f"Cumulative PV ({st.session_state['project']['currency']})")
    st.plotly_chart(fig_cum, width='stretch')

    log_action("LCC_CALCULATED", "All Alternatives", new_value=f"{len(accepted)} alternatives", source="CALCULATED")

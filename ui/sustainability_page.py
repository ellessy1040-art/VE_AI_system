"""ui/sustainability_page.py -- Sustainability indicators page."""

import pandas as pd
import plotly.express as px
import streamlit as st

from ui.common import demo_data_banner, render_status, get_accepted_alternatives
from utils.audit import log_action


def render():
    st.title("\U0001F331 Sustainability")
    demo_data_banner()

    accepted = get_accepted_alternatives()
    if not accepted:
        st.warning("No alternatives are accepted for analysis yet. Go to **AI Alternatives** and "
                   "accept at least one alternative to view sustainability indicators.")
        return

    st.markdown("#### Raw Sustainability Indicators")
    st.caption("Baseline reference index = 100 for each indicator. Lower index = better "
               "(less embodied carbon, less waste, less operational energy).")
    render_status("SYNTHETIC_DEMO")

    baseline_sust = st.session_state["baseline_sustainability"]
    rows = [{
        "Alternative": st.session_state["baseline"]["name"],
        "Embodied Carbon Index": baseline_sust["embodied_carbon_index"],
        "Construction Waste Index": baseline_sust["construction_waste_index"],
        "Operational Energy Index": baseline_sust["operational_energy_index"],
    }]

    edited_indicators = {}
    for alt in accepted:
        with st.expander(f"{alt['name']} \u2014 edit indicators"):
            s = alt["sustainability"]
            c1, c2, c3 = st.columns(3)
            with c1:
                carbon = st.number_input("Embodied Carbon Index", value=float(s["embodied_carbon_index"]), key=f"carbon_{alt['alt_id']}")
            with c2:
                waste = st.number_input("Construction Waste Index", value=float(s["construction_waste_index"]), key=f"waste_{alt['alt_id']}")
            with c3:
                energy = st.number_input("Operational Energy Index", value=float(s["operational_energy_index"]), key=f"energy_{alt['alt_id']}")
            if st.button("Save", key=f"save_sust_{alt['alt_id']}"):
                alt["sustainability"] = {
                    "embodied_carbon_index": carbon,
                    "construction_waste_index": waste,
                    "operational_energy_index": energy,
                }
                log_action("SUSTAINABILITY_UPDATED", f"Alternative:{alt['alt_id']}", new_value=str(alt["sustainability"]), source="USER_INPUT")
                st.success("Sustainability indicators updated.")
                st.rerun()
        edited_indicators[alt["alt_id"]] = alt["sustainability"]
        rows.append({
            "Alternative": alt["name"],
            "Embodied Carbon Index": alt["sustainability"]["embodied_carbon_index"],
            "Construction Waste Index": alt["sustainability"]["construction_waste_index"],
            "Operational Energy Index": alt["sustainability"]["operational_energy_index"],
        })

    ind_df = pd.DataFrame(rows)
    st.dataframe(ind_df, width='stretch')

    fig = px.bar(
        ind_df.melt(id_vars="Alternative", var_name="Indicator", value_name="Index"),
        x="Alternative", y="Index", color="Indicator", barmode="group",
        title="Sustainability Indicators (lower = better, baseline = 100)",
    )
    st.plotly_chart(fig, width='stretch')

    st.divider()
    st.markdown("#### Composite Sustainability Index (Calculated)")
    render_status("CALCULATED")
    st.caption("Composite Index = average of the three raw indicators. Used as the "
               "'cost-type' (lower = better) Sustainability criterion in the Multi-Criteria "
               "Evaluation, after normalization.")

    ind_df["Composite Sustainability Index"] = ind_df[
        ["Embodied Carbon Index", "Construction Waste Index", "Operational Energy Index"]
    ].mean(axis=1)
    st.dataframe(ind_df[["Alternative", "Composite Sustainability Index"]], width='stretch')

    st.session_state["sustainability"] = {
        row["Alternative"]: row["Composite Sustainability Index"] for _, row in ind_df.iterrows()
    }

    log_action("SUSTAINABILITY_CALCULATED", "All Alternatives", new_value=f"{len(accepted)} alternatives", source="CALCULATED")

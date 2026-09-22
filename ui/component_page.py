"""ui/component_page.py -- Component & Function Definition page."""

import streamlit as st

from ui.common import demo_data_banner, render_status
from utils.audit import log_action


def render():
    st.title("\U0001F527 Component & Function Definition")
    demo_data_banner()

    component = st.session_state["component"]

    st.markdown("#### Current Component Data")
    render_status(component.get("data_status", "SYNTHETIC_DEMO"))

    c1, c2, c3 = st.columns(3)
    c1.metric("Component", component["component_name"])
    c1.metric("System", component["system"])
    c2.metric("Quantity", f"{component['quantity']:,} beams")
    c2.metric("Beam Weight", f"{component['beam_weight_tonnes']:.0f} t")
    c3.metric("Design Life", f"{component['required_design_life_years']} yrs")
    c3.metric("Max Deflection", f"{component['max_allowable_deflection_mm']:.0f} mm")

    st.markdown("**Dimensions:** "
                f"{component['beam_length_m']} m (L) x {component['beam_width_m']} m (W) x "
                f"{component['beam_height_m']} m (H)")
    st.markdown(f"**Baseline Material:** {component['baseline_material']}")
    st.markdown(f"**Primary Function:** {component['primary_function']}")
    st.markdown("**Secondary Functions:**")
    for fn in component["secondary_functions"]:
        st.markdown(f"- {fn}")
    st.markdown(f"**Required Load Capacity:** {component['required_load_capacity_pct']:.0f}% of baseline design requirement")
    st.markdown(f"**Safety Critical:** {'Yes' if component['safety_critical'] else 'No'}")

    st.divider()
    st.markdown("#### Edit Component & Function Data")
    with st.form("component_form"):
        c1, c2 = st.columns(2)
        with c1:
            component_name = st.text_input("Component", component["component_name"])
            system = st.text_input("System", component["system"])
            quantity = st.number_input("Quantity (beams)", value=int(component["quantity"]), step=1)
            beam_length = st.number_input("Beam Length (m)", value=float(component["beam_length_m"]))
            beam_width = st.number_input("Beam Width (m)", value=float(component["beam_width_m"]))
            beam_height = st.number_input("Beam Height (m)", value=float(component["beam_height_m"]))
            beam_weight = st.number_input("Beam Weight (tonnes)", value=float(component["beam_weight_tonnes"]))
        with c2:
            baseline_material = st.text_input("Baseline Material", component["baseline_material"])
            primary_function = st.text_area("Primary Function", component["primary_function"], height=68)
            secondary_functions_text = st.text_area(
                "Secondary Functions (one per line)",
                "\n".join(component["secondary_functions"]), height=100,
            )
            required_design_life = st.number_input("Required Design Life (years)", value=int(component["required_design_life_years"]), step=1)
            max_deflection = st.number_input("Max Allowable Deflection (mm)", value=float(component["max_allowable_deflection_mm"]))
            required_load_capacity = st.number_input("Required Load Capacity (%)", value=float(component["required_load_capacity_pct"]))
            safety_critical = st.checkbox("Safety Critical", value=component["safety_critical"])

        submitted = st.form_submit_button("Save Component Data")
        if submitted:
            old = dict(component)
            component.update({
                "component_name": component_name,
                "system": system,
                "quantity": int(quantity),
                "beam_length_m": beam_length,
                "beam_width_m": beam_width,
                "beam_height_m": beam_height,
                "beam_weight_tonnes": beam_weight,
                "baseline_material": baseline_material,
                "primary_function": primary_function,
                "secondary_functions": [s.strip() for s in secondary_functions_text.splitlines() if s.strip()],
                "required_design_life_years": int(required_design_life),
                "max_allowable_deflection_mm": max_deflection,
                "required_load_capacity_pct": required_load_capacity,
                "safety_critical": safety_critical,
                "data_status": "USER_INPUT",
            })
            st.session_state["component"] = component
            log_action("COMPONENT_UPDATED", "Component", old_value=str(old), new_value=str(component), source="USER_INPUT")
            st.success("Component data updated.")
            st.rerun()

"""ui/project_page.py -- Project Overview page."""

import streamlit as st

from ui.common import demo_data_banner, safety_notice, ai_role_notice, render_status
from utils.audit import log_action


def render():
    st.title("\U0001F4CB Project Overview")
    demo_data_banner()
    safety_notice()
    ai_role_notice()

    project = st.session_state["project"]

    st.subheader(project["project_name"])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Project Type", project["project_type"])
        st.metric("Location", project["location"])
    with col2:
        st.metric("Project Phase", project["project_phase"])
        st.metric("Analysis Scope", project["analysis_scope"])
    with col3:
        st.metric("Currency", project["currency"])
        st.metric("Base Year", project["base_year"])

    st.divider()
    st.markdown("#### Key Analysis Parameters")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    component = st.session_state["component"]
    kpi1.metric("Guideway Beams", f"{component['quantity']:,}")
    kpi2.metric("Beam Length", f"{component['beam_length_m']:.0f} m")
    kpi3.metric("Baseline Material", component["baseline_material"])
    kpi4.metric("Analysis Life", f"{project['analysis_period_years']} yrs")
    kpi5.metric("Discount Rate", f"{project['discount_rate']*100:.1f}%")

    st.divider()
    st.markdown("#### Edit Project Parameters")
    render_status("SYNTHETIC_DEMO")
    with st.form("project_form"):
        c1, c2 = st.columns(2)
        with c1:
            project_name = st.text_input("Project Name", project["project_name"])
            project_type = st.text_input("Project Type", project["project_type"])
            location = st.text_input("Location", project["location"])
            project_phase = st.text_input("Project Phase", project["project_phase"])
            analysis_scope = st.text_input("Analysis Scope", project["analysis_scope"])
        with c2:
            currency = st.text_input("Currency", project["currency"])
            base_year = st.number_input("Base Year", value=int(project["base_year"]), step=1)
            design_life = st.number_input("Design Life (years)", value=int(project["design_life_years"]), step=1)
            analysis_period = st.number_input("Analysis Period (years)", value=int(project["analysis_period_years"]), step=1)
            discount_rate_pct = st.number_input("Discount Rate (%)", value=float(project["discount_rate"] * 100), step=0.5)

        submitted = st.form_submit_button("Save Project Parameters")
        if submitted:
            old = dict(project)
            project.update({
                "project_name": project_name,
                "project_type": project_type,
                "location": location,
                "project_phase": project_phase,
                "analysis_scope": analysis_scope,
                "currency": currency,
                "base_year": int(base_year),
                "design_life_years": int(design_life),
                "analysis_period_years": int(analysis_period),
                "discount_rate": discount_rate_pct / 100.0,
            })
            st.session_state["project"] = project
            log_action("PROJECT_UPDATED", "Project", old_value=str(old), new_value=str(project), source="USER_INPUT")
            st.success("Project parameters updated.")
            st.rerun()

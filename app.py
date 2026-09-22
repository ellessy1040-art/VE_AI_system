"""
app.py -- VE-AI: AI-Assisted Value Engineering Decision Support System
          for Large Infrastructure Projects.

Master's research prototype. Case study: Egyptian Monorail --
Guideway Beam System (synthetic demonstration data).

Run with:
    streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # loads .env if present; safe no-op otherwise

from ui.common import init_session_state
from ui import (
    project_page, component_page, baseline_page, alternatives_page,
    lcc_page, risk_page, sustainability_page, mce_page, sensitivity_page,
    final_page, audit_page,
)
from ai.llm_client import is_live_mode_available

st.set_page_config(
    page_title="VE-AI | Value Engineering Decision Support",
    page_icon="\U0001F3D7\uFE0F",
    layout="wide",
)

init_session_state()

PAGES = {
    "1. Project Overview": project_page,
    "2. Component & Function": component_page,
    "3. Baseline": baseline_page,
    "4. AI Alternatives": alternatives_page,
    "5. LCC Analysis": lcc_page,
    "6. Risk Analysis": risk_page,
    "7. Sustainability": sustainability_page,
    "8. Multi-Criteria Evaluation": mce_page,
    "9. Sensitivity Analysis": sensitivity_page,
    "10. Final Recommendation": final_page,
    "11. Audit Log": audit_page,
}

with st.sidebar:
    st.markdown("## \U0001F3D7\uFE0F VE-AI")
    st.caption("AI-Assisted Value Engineering Decision Support System")
    st.caption("Case Study: Egyptian Monorail \u2014 Guideway Beam System")
    st.markdown("---")

    selection = st.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed", key="nav_radio")

    st.markdown("---")
    if is_live_mode_available():
        st.success("\U0001F310 Live LLM configured")
    else:
        st.info("\U0001F9EA Demo Mode \u2014 Mock AI\n\nSet `OPENAI_API_KEY` to enable a live LLM.")

    st.markdown("---")
    st.caption(
        "AI provides decision support and alternative suggestions. "
        "Final engineering approval remains with the responsible engineer."
    )
    st.caption("All numerical case-study data is synthetic demonstration data, "
               "not official project data.")

PAGES[selection].render()

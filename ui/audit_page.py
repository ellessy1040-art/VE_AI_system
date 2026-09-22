"""ui/audit_page.py -- Audit Log page."""

import streamlit as st

from utils.audit import audit_log_dataframe, audit_log_to_csv_bytes


def render():
    st.title("\U0001F4DC Audit Log")
    st.caption("Every important action taken in this session is recorded here for traceability: "
               "project/baseline creation, AI generation, engineer review decisions, calculations, "
               "weight changes, sensitivity runs, and the final engineer decision.")

    df = audit_log_dataframe()
    st.markdown(f"**Total entries:** {len(df)}")

    with st.expander("Filter", expanded=False):
        actions = ["(all)"] + sorted(df["action"].unique().tolist()) if not df.empty else ["(all)"]
        selected = st.selectbox("Action type", actions)
    if not df.empty and selected != "(all)":
        df = df[df["action"] == selected]

    st.dataframe(df.sort_values("timestamp", ascending=False), width='stretch', height=500)

    st.download_button(
        "\U0001F4E5 Export Audit Log to CSV",
        data=audit_log_to_csv_bytes(),
        file_name="veai_audit_log.csv",
        mime="text/csv",
    )

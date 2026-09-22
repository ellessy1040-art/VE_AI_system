"""
ui/final_page.py -- Final Recommendation dashboard, AI Explanation,
Engineer Decision, and Report Export.
"""

from datetime import datetime

import streamlit as st

from ai import llm_client
from ui.common import demo_data_banner, safety_notice, ai_role_notice, render_status, get_accepted_alternatives, currency_fmt
from engines.lcc_engine import lcc_saving
from utils.audit import log_action
from utils.export import export_json_bytes, export_csv_bytes, export_html_report
from data.demo_case import AI_ROLE_NOTICE


def render():
    st.title("\u2705 Final Recommendation")
    demo_data_banner()
    safety_notice()

    accepted = get_accepted_alternatives()
    if "mce_result_table" not in st.session_state or not accepted:
        st.warning("Complete the Multi-Criteria Evaluation page first (accept alternatives, set "
                   "weights, and let the evaluation matrix calculate) before viewing the final "
                   "recommendation.")
        return

    result_table = st.session_state["mce_result_table"]
    top_name = result_table.index[0]
    top_alt = next(a for a in accepted if a["name"] == top_name)
    baseline_lcc = st.session_state.get("baseline_lcc")
    alt_lcc = st.session_state.get("alternative_lcc", {})

    st.info("\U0001F3F7\uFE0F **AI-Assisted / MCE-Based Recommendation \u2014 Subject to Engineer Approval**")
    st.markdown(f"## Recommended Alternative: **{top_name}**")

    top_lcc_val = alt_lcc.get(top_alt["alt_id"], {}).get("total_lcc")
    saving = None
    if baseline_lcc and top_lcc_val is not None:
        saving = lcc_saving(baseline_lcc["total_lcc"], top_lcc_val)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Baseline LCC", currency_fmt(baseline_lcc["total_lcc"]) if baseline_lcc else "N/A")
    c2.metric("Recommended LCC", currency_fmt(top_lcc_val) if top_lcc_val is not None else "N/A")
    c3.metric("LCC Saving %", f"{saving['pct_saving']:.2f}%" if saving else "N/A")
    c4.metric("Final MCE Score", f"{result_table.loc[top_name, 'final_score']:.3f}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Technical Performance", f"{result_table.loc[top_name, 'performance']:.1f} / 100")
    c6.metric("Average Risk", f"{result_table.loc[top_name, 'risk']:.2f} / 25")
    c7.metric("Sustainability Index", f"{result_table.loc[top_name, 'sustainability']:.1f}")
    c8.metric("Rank", f"#{int(result_table.loc[top_name, 'rank'])}")

    sensitivity_summary = st.session_state.get("sensitivity_summary")
    if sensitivity_summary:
        if sensitivity_summary["preferred_changes"]:
            st.warning("\u26A0\uFE0F Sensitivity Analysis shows the preferred alternative CHANGES under "
                       "some weighting scenarios. Review the Sensitivity Analysis page.")
        else:
            st.success("\u2705 Sensitivity Analysis shows the preferred alternative is robust across "
                       "all tested weighting scenarios.")
    else:
        st.info("Sensitivity Analysis has not been run yet. Consider running it before final approval.")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Key Benefits")
        for b in top_alt.get("benefits", []):
            st.markdown(f"- {b}")
    with col_b:
        st.markdown("##### Key Risks / Required Verification")
        for r in top_alt.get("risks", []):
            st.markdown(f"- {r['risk']} (score {r['probability']*r['impact']})")
        for rd in top_alt.get("required_data", []):
            st.markdown(f"- \u2757 Verify: {rd}")

    st.divider()
    st.markdown("### \U0001F916 AI Explanation of Results")
    ai_role_notice()
    if st.button("Generate AI Explanation", type="primary"):
        results_summary = {
            "top_alternative": top_name,
            "top_score": float(result_table.loc[top_name, "final_score"]),
            "ranking": list(result_table.index),
            "weights": st.session_state["mce_weights"],
            "baseline_lcc": baseline_lcc["total_lcc"] if baseline_lcc else None,
            "top_lcc": top_lcc_val,
            "lcc_saving_pct": saving["pct_saving"] if saving else None,
            "sensitivity_preferred_changes": sensitivity_summary["preferred_changes"] if sensitivity_summary else None,
            "missing_data": top_alt.get("required_data", []),
            "top_risks": [r["risk"] for r in top_alt.get("risks", [])],
            "mce_evaluation_matrix": result_table.to_dict(orient="index"),
        }
        with st.spinner("Requesting explanation..."):
            response = llm_client.generate_explanation(results_summary)
        st.session_state["ai_explanation"] = response
        log_action("AI_EXPLANATION_GENERATED", "Final Recommendation",
                   source=response["source"], model_name=response.get("model_name"))
        st.rerun()

    explanation = st.session_state.get("ai_explanation")
    if explanation:
        badge = "\U0001F9EA Demo Mode - Mock AI" if explanation["source"] == "MOCK_AI" else "\U0001F310 Live LLM"
        st.caption(f"{badge} | model: `{explanation.get('model_name')}`")
        if explanation.get("error"):
            st.warning(explanation["error"])
        st.markdown(explanation["explanation"])

    st.divider()
    st.markdown("### \U0001F468\u200D\U0001F4BC Engineer Decision")
    st.caption(AI_ROLE_NOTICE)

    final_decision = st.session_state["final_decision"]
    with st.form("engineer_decision_form"):
        engineer_name = st.text_input("Engineer Name", value=final_decision.get("decided_by") or "")
        decision = st.radio("Decision", ["APPROVE", "REQUEST_MORE_INFO", "REJECT"], horizontal=True)
        comment = st.text_area("Comment (required)", value=final_decision.get("comment") or "")
        submitted = st.form_submit_button("Submit Engineer Decision")
        if submitted:
            if not comment.strip():
                st.error("A comment is required to submit an engineer decision.")
            elif not engineer_name.strip():
                st.error("Engineer name is required.")
            else:
                final_decision.update({
                    "recommended_alternative": top_name,
                    "engineer_decision": decision,
                    "comment": comment,
                    "decided_by": engineer_name,
                    "decided_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
                })
                st.session_state["final_decision"] = final_decision
                log_action("ENGINEER_DECISION", "Final Recommendation", new_value=decision,
                           source="USER_INPUT", user=engineer_name, decision=decision)
                st.success(f"Engineer decision recorded: {decision}")
                st.rerun()

    if final_decision.get("engineer_decision") != "PENDING":
        render_status("USER_INPUT")
        st.markdown(f"**Recorded decision:** {final_decision['engineer_decision']} by "
                    f"{final_decision['decided_by']} at {final_decision['decided_at']}")
        st.markdown(f"**Comment:** {final_decision['comment']}")

    st.divider()
    st.markdown("### \U0001F4E4 Export Results")
    exp1, exp2, exp3 = st.columns(3)
    with exp1:
        st.download_button("Download JSON", data=export_json_bytes(dict(st.session_state)),
                            file_name="veai_export.json", mime="application/json")
    with exp2:
        st.download_button("Download CSV", data=export_csv_bytes(dict(st.session_state)),
                            file_name="veai_export.csv", mime="text/csv")
    with exp3:
        st.download_button("Download HTML Report", data=export_html_report(dict(st.session_state)),
                            file_name="veai_final_report.html", mime="text/html")

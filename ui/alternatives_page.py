"""
ui/alternatives_page.py -- AI Alternative Generation + Engineer Review.

Combines workflow steps "AI Alternative Generation" and "Engineer
Review": the AI proposes candidate alternatives, then the engineer
must explicitly Accept / Request More Info / Reject each one before
it can enter the deterministic LCC / Risk / MCE analysis.
"""

from __future__ import annotations

import copy
from datetime import datetime

import streamlit as st

from ai import llm_client
from data.demo_case import DEFAULT_ALTERNATIVES, BASELINE_SUSTAINABILITY
from ui.common import demo_data_banner, ai_role_notice, render_status, build_ai_context
from utils.audit import log_action

DEMO_LOOKUP = {alt["alt_id"]: alt for alt in DEFAULT_ALTERNATIVES}


def _scaffold_alternative(ai_alt: dict, source: str) -> dict:
    """
    Builds the full internal alternative record from an AI-proposed
    alternative. If it matches one of the predefined demo alternatives
    (by alt_id -- true in Demo Mode), the deterministic engineering
    data (financials, risks, sustainability, technical performance) is
    attached from the synthetic case study. Otherwise (a genuinely new
    alternative from a live LLM) those fields start empty/MISSING and
    must be supplied by the engineer before LCC/Risk analysis works.
    """
    alt_id = ai_alt.get("alt_id") or f"ALT_{ai_alt.get('name', 'X')[:6].upper()}"
    demo_match = DEMO_LOOKUP.get(alt_id)

    record = {
        "alt_id": alt_id,
        "name": ai_alt.get("name", "Unnamed Alternative"),
        "principle": ai_alt.get("principle", ""),
        "function_equivalence": ai_alt.get("function_equivalence", ""),
        "technical_changes": ai_alt.get("technical_changes", []),
        "benefits": ai_alt.get("benefits", []),
        "constraints": ai_alt.get("constraints", []),
        "required_data": ai_alt.get("required_data", []),
        "risk_names": ai_alt.get("risks", []),
        "cost_estimate": ai_alt.get("cost_estimate", {"value": None, "currency": "EGP", "confidence": "low"}),
        "ai_confidence": ai_alt.get("ai_confidence", "low"),
        "review_status": "AI_PROPOSED",
        "reviewer": None,
        "review_timestamp": None,
        "review_reason": None,
        "ai_source": source,
    }

    if demo_match:
        record["cost"] = copy.deepcopy(demo_match["cost"])
        record["risks"] = copy.deepcopy(demo_match["risks"])
        record["sustainability"] = copy.deepcopy(demo_match["sustainability"])
        record["technical_performance_score"] = demo_match["technical_performance_score"]
        record["material"] = demo_match["material"]
        record["engineering_data_status"] = "SYNTHETIC_DEMO"
    else:
        record["cost"] = {
            "initial_cost": 0.0, "annual_operating_cost": 0.0, "annual_maintenance_cost": 0.0,
            "replacement_year": None, "replacement_cost": 0.0, "residual_value": 0.0,
        }
        record["risks"] = []
        record["sustainability"] = dict(BASELINE_SUSTAINABILITY)
        record["technical_performance_score"] = None
        record["material"] = ai_alt.get("material", "")
        record["engineering_data_status"] = "MISSING"

    return record


def render():
    st.title("\U0001F916 AI Alternatives & Engineer Review")
    demo_data_banner()
    ai_role_notice()

    live_available = llm_client.is_live_mode_available()
    if live_available:
        st.success("Live LLM configuration detected. The app will attempt a real API call and "
                    "automatically fall back to Mock AI if it fails.")
    else:
        st.info("\U0001F9EA **Demo Mode \u2014 Mock AI**: no `OPENAI_API_KEY` configured. "
                "Deterministic predefined alternatives will be used.")

    col_a, col_b = st.columns([1, 3])
    with col_a:
        generate_clicked = st.button("\u2699\uFE0F Generate AI Alternatives", type="primary")

    if generate_clicked:
        ai_context = build_ai_context()
        with st.spinner("Requesting candidate alternatives..."):
            response = llm_client.generate_alternatives(ai_context)

        alternatives = [_scaffold_alternative(a, response.get("source", "MOCK_AI")) for a in response["alternatives"]]
        st.session_state["alternatives"] = alternatives
        st.session_state["ai_generation_meta"] = {
            "source": response.get("source"),
            "model_name": response.get("model_name"),
            "error": response.get("error"),
            "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }
        log_action(
            "AI_ALTERNATIVES_GENERATED", "Alternatives",
            new_value=f"{len(alternatives)} alternatives",
            source=response.get("source", "MOCK_AI"),
            model_name=response.get("model_name"),
        )
        if response.get("error"):
            st.warning(response["error"])
        st.rerun()

    meta = st.session_state.get("ai_generation_meta")
    if meta:
        badge = "\U0001F9EA Demo Mode - Mock AI" if meta["source"] == "MOCK_AI" else "\U0001F310 Live LLM"
        st.caption(f"{badge} | model: `{meta.get('model_name')}` | generated: {meta.get('generated_at')}")

    alternatives = st.session_state.get("alternatives", [])
    if not alternatives:
        st.info("Click **Generate AI Alternatives** to produce candidate alternatives for this component.")
        return

    st.divider()
    st.markdown("### Candidate Alternatives")

    for i, alt in enumerate(alternatives):
        with st.container(border=True):
            top1, top2 = st.columns([4, 1])
            with top1:
                st.markdown(f"#### {alt['name']}")
                st.caption(f"ID: {alt['alt_id']}  |  Material: {alt.get('material', 'N/A')}")
            with top2:
                render_status(alt["review_status"])

            st.markdown(f"**Principle:** {alt['principle']}")
            st.markdown(f"**Function Equivalence:** {alt['function_equivalence']}")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Technical Changes**")
                for x in alt["technical_changes"]:
                    st.markdown(f"- {x}")
                st.markdown("**Benefits**")
                for x in alt["benefits"]:
                    st.markdown(f"- {x}")
                st.markdown("**Constraints**")
                for x in alt["constraints"]:
                    st.markdown(f"- {x}")
            with c2:
                st.markdown("**Required Data (still to verify)**")
                for x in alt["required_data"]:
                    st.markdown(f"- {x}")
                st.markdown("**Identified Risks**")
                risk_labels = alt.get("risk_names") or [r["risk"] for r in alt.get("risks", [])]
                for x in risk_labels:
                    st.markdown(f"- {x}")

            cost_est = alt["cost_estimate"]
            cost_val = cost_est.get("value")
            cost_str = f"{cost_val:,.0f} {cost_est.get('currency', 'EGP')}" if cost_val is not None else "N/A"
            st.markdown(
                f"**AI Cost Estimate:** {cost_str} "
                f"(confidence: {cost_est.get('confidence', 'low')}) &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"**AI Confidence:** {alt['ai_confidence']}"
            )
            if alt.get("engineering_data_status") == "MISSING":
                st.warning("This alternative has no attached deterministic engineering data yet "
                           "(financials/risks/sustainability). Supply this data before it can be "
                           "carried through LCC / Risk / MCE analysis.")

            st.markdown("---")
            r1, r2, r3, r4 = st.columns([2, 2, 3, 1])
            with r1:
                decision = st.selectbox(
                    "Reviewer Decision", ["AI_PROPOSED", "ACCEPTED_FOR_ANALYSIS", "MORE_INFO_REQUESTED", "REJECTED"],
                    index=["AI_PROPOSED", "ACCEPTED_FOR_ANALYSIS", "MORE_INFO_REQUESTED", "REJECTED"].index(alt["review_status"]),
                    key=f"decision_{alt['alt_id']}",
                )
            with r2:
                reviewer = st.text_input("Reviewer Name", value=alt.get("reviewer") or "", key=f"reviewer_{alt['alt_id']}")
            with r3:
                reason = st.text_input(
                    "Reason (required if Rejected / More Info)",
                    value=alt.get("review_reason") or "", key=f"reason_{alt['alt_id']}",
                )
            with r4:
                st.write("")
                st.write("")
                save_clicked = st.button("Save", key=f"save_{alt['alt_id']}")

            if save_clicked:
                if decision in ("REJECTED", "MORE_INFO_REQUESTED") and not reason.strip():
                    st.error("A reason is required when rejecting or requesting more information.")
                else:
                    old_status = alt["review_status"]
                    alt["review_status"] = decision
                    alt["reviewer"] = reviewer or "unspecified"
                    alt["review_timestamp"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
                    alt["review_reason"] = reason
                    st.session_state["alternatives"][i] = alt
                    action = {
                        "ACCEPTED_FOR_ANALYSIS": "ALTERNATIVE_ACCEPTED",
                        "REJECTED": "ALTERNATIVE_REJECTED",
                        "MORE_INFO_REQUESTED": "ALTERNATIVE_MORE_INFO_REQUESTED",
                        "AI_PROPOSED": "ALTERNATIVE_REVIEW_RESET",
                    }[decision]
                    log_action(
                        action, f"Alternative:{alt['alt_id']}",
                        old_value=old_status, new_value=decision,
                        source="USER_INPUT", user=reviewer or "unspecified", decision=decision,
                    )
                    st.success(f"Saved review decision for {alt['name']}: {decision}")
                    st.rerun()

    accepted = [a for a in alternatives if a["review_status"] == "ACCEPTED_FOR_ANALYSIS"]
    st.divider()
    if accepted:
        st.success(f"\u2705 {len(accepted)} alternative(s) accepted for analysis: "
                   + ", ".join(a["name"] for a in accepted))
    else:
        st.warning("No alternatives have been accepted for analysis yet. Only alternatives with "
                   "status **ACCEPTED_FOR_ANALYSIS** proceed to LCC / Risk / MCE / Ranking.")

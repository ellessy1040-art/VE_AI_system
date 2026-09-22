"""
ui/common.py

Shared helpers used by every page: session-state initialization,
data-status badges, and cross-cutting computations (running the LCC
and risk engines for every alternative + baseline so results stay in
sync as the engineer edits values).
"""

from __future__ import annotations

import copy
from typing import Dict, Any, List

import streamlit as st
import pandas as pd

from data.demo_case import (
    DEFAULT_PROJECT, DEFAULT_COMPONENT, DEFAULT_BASELINE, DEFAULT_ALTERNATIVES,
    BASELINE_SUSTAINABILITY, BASELINE_RISKS, DEFAULT_WEIGHTS, SENSITIVITY_SCENARIOS,
    VE_CONSTRAINTS, FORBIDDEN_ASSUMPTIONS, EVALUATION_CRITERIA, MISSING_DATA,
    SAFETY_NOTICE, AI_ROLE_NOTICE, DEMO_DATA_NOTICE,
)
from engines.lcc_engine import calculate_lcc, lcc_saving
from engines.risk_engine import calculate_risk_summary
from utils.audit import log_action, init_audit_log

STATUS_COLORS = {
    "VERIFIED": "#1b7f3a",
    "USER_INPUT": "#0f6cbd",
    "SYNTHETIC_DEMO": "#b8860b",
    "AI_PROPOSED": "#8a2be2",
    "CALCULATED": "#2f6f4f",
    "MISSING": "#c0392b",
}


def status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#555555")
    return (
        f"<span style='background-color:{color};color:white;padding:2px 8px;"
        f"border-radius:10px;font-size:0.75em;font-weight:600;'>{status}</span>"
    )


def render_status(status: str):
    st.markdown(status_badge(status), unsafe_allow_html=True)


def demo_data_banner():
    st.warning(f"\u26A0\uFE0F **{DEMO_DATA_NOTICE}**")


def safety_notice():
    st.info(SAFETY_NOTICE)


def ai_role_notice():
    st.info(f"\U0001F916 {AI_ROLE_NOTICE}")


# ----------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------------------------
def init_session_state():
    init_audit_log()

    if "initialized" not in st.session_state:
        st.session_state["project"] = copy.deepcopy(DEFAULT_PROJECT)
        st.session_state["component"] = copy.deepcopy(DEFAULT_COMPONENT)
        st.session_state["baseline"] = copy.deepcopy(DEFAULT_BASELINE)
        st.session_state["baseline_sustainability"] = copy.deepcopy(BASELINE_SUSTAINABILITY)
        st.session_state["baseline_risks"] = copy.deepcopy(BASELINE_RISKS)

        st.session_state["alternatives"] = []          # list of alt dicts (engineering + AI data)
        st.session_state["ai_generation_meta"] = None   # {source, model_name, error}
        st.session_state["engineer_reviews"] = {}        # alt_id -> review dict

        st.session_state["mce_weights"] = copy.deepcopy(DEFAULT_WEIGHTS)
        st.session_state["sensitivity_scenarios"] = copy.deepcopy(SENSITIVITY_SCENARIOS)
        st.session_state["custom_weights"] = copy.deepcopy(DEFAULT_WEIGHTS)

        st.session_state["ai_explanation"] = None
        st.session_state["final_decision"] = {
            "recommended_alternative": None,
            "engineer_decision": "PENDING",
            "comment": "",
            "decided_by": None,
            "decided_at": None,
        }

        log_action("PROJECT_CREATED", "Project", new_value=DEFAULT_PROJECT["project_name"], source="SYSTEM")
        log_action("BASELINE_CREATED", "Baseline", new_value=DEFAULT_BASELINE["name"], source="SYSTEM")

        st.session_state["initialized"] = True


# ----------------------------------------------------------------------
# CROSS-CUTTING COMPUTATIONS
# ----------------------------------------------------------------------
def compute_baseline_lcc() -> Dict[str, Any]:
    b = st.session_state["baseline"]
    result = calculate_lcc(
        initial_cost=b["initial_cost"],
        annual_operating_cost=b["annual_operating_cost"],
        annual_maintenance_cost=b["annual_maintenance_cost"],
        discount_rate=b["discount_rate"],
        analysis_period_years=b["analysis_period_years"],
        replacement_year=b.get("replacement_year"),
        replacement_cost=b.get("replacement_cost", 0.0),
        residual_value=b.get("residual_value", 0.0),
    )
    st.session_state["baseline_lcc"] = result
    return result


def compute_alternative_lcc(alt: Dict[str, Any]) -> Dict[str, Any]:
    cost = alt["cost"]
    b = st.session_state["baseline"]
    result = calculate_lcc(
        initial_cost=cost["initial_cost"],
        annual_operating_cost=cost["annual_operating_cost"],
        annual_maintenance_cost=cost["annual_maintenance_cost"],
        discount_rate=b["discount_rate"],
        analysis_period_years=b["analysis_period_years"],
        replacement_year=cost.get("replacement_year"),
        replacement_cost=cost.get("replacement_cost", 0.0),
        residual_value=cost.get("residual_value", 0.0),
    )
    return result


def compute_all_lcc():
    compute_baseline_lcc()
    alt_lcc = {}
    for alt in st.session_state["alternatives"]:
        alt_lcc[alt["alt_id"]] = compute_alternative_lcc(alt)
    st.session_state["alternative_lcc"] = alt_lcc


def compute_all_risk():
    baseline_summary = calculate_risk_summary(st.session_state["baseline_risks"])
    st.session_state["baseline_risk_summary"] = baseline_summary

    risk_results = {}
    for alt in st.session_state["alternatives"]:
        risk_results[alt["alt_id"]] = calculate_risk_summary(alt["risks"])
    st.session_state["risk_results"] = risk_results


def get_alternative_by_id(alt_id: str) -> Dict[str, Any]:
    for alt in st.session_state["alternatives"]:
        if alt["alt_id"] == alt_id:
            return alt
    return None


def get_accepted_alternatives() -> List[Dict[str, Any]]:
    return [a for a in st.session_state["alternatives"] if a.get("review_status") == "ACCEPTED_FOR_ANALYSIS"]


def build_ai_context() -> Dict[str, Any]:
    project = st.session_state["project"]
    component = st.session_state["component"]
    baseline = st.session_state["baseline"]

    return {
        "project_context": {
            "project_type": project["project_type"],
            "project_phase": project["project_phase"],
            "location": project["location"],
            "analysis_scope": project["analysis_scope"],
            "currency": project["currency"],
        },
        "component_data": {
            "component": component["component_name"],
            "system": component["system"],
            "quantity": component["quantity"],
            "length_m": component["beam_length_m"],
            "width_m": component["beam_width_m"],
            "height_m": component["beam_height_m"],
            "baseline_material": component["baseline_material"],
            "weight_tonnes": component["beam_weight_tonnes"],
        },
        "function_definition": {
            "primary_function": component["primary_function"],
            "secondary_functions": component["secondary_functions"],
        },
        "performance_requirements": {
            "design_life_years": component["required_design_life_years"],
            "max_deflection_mm": component["max_allowable_deflection_mm"],
            "required_load_capacity_pct": component["required_load_capacity_pct"],
            "safety_critical": component["safety_critical"],
        },
        "baseline": {
            "name": baseline["name"],
            "material": baseline["material"],
            "initial_cost": baseline["initial_cost"],
            "annual_operating_cost": baseline["annual_operating_cost"],
            "annual_maintenance_cost": baseline["annual_maintenance_cost"],
        },
        "constraints": VE_CONSTRAINTS,
        "safety_requirements": {
            "safety_critical": component["safety_critical"],
            "notice": SAFETY_NOTICE,
        },
        "evaluation_criteria": EVALUATION_CRITERIA,
        "missing_data": MISSING_DATA,
        "forbidden_assumptions": FORBIDDEN_ASSUMPTIONS,
    }


def currency_fmt(value: float, currency: str = None) -> str:
    currency = currency or st.session_state.get("project", {}).get("currency", "EGP")
    return f"{value:,.0f} {currency}"

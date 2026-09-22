"""
ai/mock_ai.py

Deterministic "Mock AI" used automatically whenever no real LLM API
key/endpoint is configured (or the real API call fails). This keeps
the prototype fully runnable offline and makes "Demo Mode" explicit
in the UI.

Mock AI never calculates LCC, risk scores, or rankings -- it only
returns the same kind of structured, qualitative content a real LLM
would be asked to produce, using the case-study's predefined demo
alternatives.
"""

from __future__ import annotations

from typing import Dict, Any, List

from data.demo_case import DEFAULT_ALTERNATIVES


def generate_mock_alternatives() -> Dict[str, Any]:
    """
    Returns alternatives in the same JSON schema a real LLM call would
    return (section 8 of the spec): name, principle, function_equivalence,
    technical_changes, benefits, constraints, required_data, risks,
    cost_estimate, ai_confidence, review_status.

    Cost figures are marked "low" confidence AI estimates -- the actual
    deterministic financial inputs used for LCC live separately in
    data/demo_case.py and are only used by the LCC engine, not invented
    here.
    """
    alternatives = []
    for alt in DEFAULT_ALTERNATIVES:
        alternatives.append({
            "alt_id": alt["alt_id"],
            "name": alt["name"],
            "principle": alt["principle"],
            "function_equivalence": alt["function_equivalence"],
            "technical_changes": alt["technical_changes"],
            "benefits": alt["benefits"],
            "constraints": alt["constraints"],
            "required_data": alt["required_data"],
            "risks": [r["risk"] for r in alt["risks"]],
            "cost_estimate": {
                "value": alt["cost"]["initial_cost"],
                "currency": "EGP",
                "confidence": "low",
            },
            "ai_confidence": alt["ai_confidence"],
            "review_status": "AI_PROPOSED",
        })
    return {"alternatives": alternatives, "source": "MOCK_AI", "model_name": "mock-ai-demo-v1"}


def generate_mock_explanation(results_summary: Dict[str, Any]) -> str:
    """
    Builds an explanation from the ACTUAL calculated results passed in
    (not hardcoded numbers), so even in Demo Mode the explanation
    reflects the real deterministic output.
    """
    top_name = results_summary.get("top_alternative", "N/A")
    top_score = results_summary.get("top_score")
    ranking = results_summary.get("ranking", [])
    weights = results_summary.get("weights", {})
    baseline_lcc = results_summary.get("baseline_lcc")
    top_lcc = results_summary.get("top_lcc")
    saving_pct = results_summary.get("lcc_saving_pct")
    sensitivity_changes = results_summary.get("sensitivity_preferred_changes")
    missing_data: List[str] = results_summary.get("missing_data", [])
    remaining_risks: List[str] = results_summary.get("top_risks", [])

    score_str = f"{top_score:.3f}" if isinstance(top_score, (int, float)) else "N/A"
    lcc_line = ""
    if baseline_lcc is not None and top_lcc is not None:
        lcc_line = (
            f"Relative to the baseline LCC of approximately {baseline_lcc:,.0f} EGP, "
            f"the recommended alternative has a calculated LCC of approximately "
            f"{top_lcc:,.0f} EGP"
        )
        if saving_pct is not None:
            lcc_line += f", a saving of about {saving_pct:.1f}% (deterministically calculated, not AI-estimated)."
        else:
            lcc_line += "."

    weight_str = ", ".join(f"{k}: {v}%" for k, v in weights.items())

    lines = [
        "**[DEMO MODE \u2014 MOCK AI EXPLANATION]** "
        "This explanation is generated locally from the deterministic results below. "
        "No external LLM call was made.",
        "",
        f"**1. Why '{top_name}' ranked first:** Under the current criteria weights "
        f"({weight_str}), '{top_name}' achieved the highest deterministically "
        f"calculated multi-criteria score ({score_str}) among the alternatives "
        f"accepted for analysis: {', '.join(ranking) if ranking else 'N/A'}.",
        "",
        f"**2. Which criteria contributed most:** The final score is a weighted sum "
        f"of Life Cycle Cost, Technical Performance, Risk, and Sustainability using "
        f"the weights above. Criteria with a higher weight and a strong normalized "
        f"score for '{top_name}' contributed the most; see the MCE evaluation matrix "
        f"for the exact weighted contribution of each criterion.",
        "",
        f"**3. What risks remain:** " + (
            "; ".join(remaining_risks) if remaining_risks
            else "See the Risk Analysis page for the full risk register of the recommended alternative."
        ),
        "",
        "**4. What information is still missing:** " + (
            "; ".join(missing_data) if missing_data
            else "Verified structural capacity, certified pricing, and code-compliance review are still outstanding for all alternatives."
        ),
        "",
        "**5. Sensitivity to weights:** " + (
            "The preferred alternative CHANGES under at least one alternative weighting "
            "scenario tested in the Sensitivity Analysis page \u2014 review that page before "
            "finalizing a decision."
            if sensitivity_changes
            else "The preferred alternative REMAINS the same across all weighting scenarios "
                 "tested in the Sensitivity Analysis page, indicating a relatively robust result."
        ),
        "",
        f"**6. What should be verified before final engineering approval:** Verified "
        f"structural capacity and deflection checks, fatigue and corrosion protection "
        f"verification (where applicable), certified market pricing, and a formal "
        f"code-compliance review by the responsible engineer. " + lcc_line,
        "",
        "This explanation does not constitute engineering, safety, or code-compliance "
        "certification. Final engineering approval remains with the responsible engineer.",
    ]
    return "\n".join(lines)

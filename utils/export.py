"""
utils/export.py

Export helpers: builds CSV / JSON / HTML exports of the full VE-AI
session (project, component, baseline, alternatives, LCC, risk,
sustainability, MCE, sensitivity, engineer review, final decision,
audit log).
"""

from __future__ import annotations

import json
import io
from datetime import datetime
from typing import Dict, Any

import pandas as pd


def _df_to_records(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records"))


def build_export_bundle(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collects a JSON-serializable snapshot of everything relevant in
    session_state for export.
    """
    bundle = {
        "export_timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "data_notice": "Synthetic Demonstration Data \u2014 Not Official Project Data",
        "project": state.get("project"),
        "component": state.get("component"),
        "baseline": state.get("baseline"),
        "baseline_lcc": {k: v for k, v in (state.get("baseline_lcc") or {}).items() if k != "cashflow_table"},
        "alternatives": state.get("alternatives"),
        "alternative_lcc": {
            alt_id: {k: v for k, v in res.items() if k != "cashflow_table"}
            for alt_id, res in (state.get("alternative_lcc") or {}).items()
        },
        "risk_results": state.get("risk_results_summary"),
        "sustainability": state.get("sustainability"),
        "mce_weights": state.get("mce_weights"),
        "mce_result_table": _df_to_records(state.get("mce_result_table")) if isinstance(state.get("mce_result_table"), pd.DataFrame) else None,
        "sensitivity_summary": state.get("sensitivity_summary"),
        "engineer_reviews": state.get("engineer_reviews"),
        "final_decision": state.get("final_decision"),
        "audit_log": state.get("audit_log"),
    }
    return bundle


def export_json_bytes(state: Dict[str, Any]) -> bytes:
    bundle = build_export_bundle(state)
    return json.dumps(bundle, indent=2, default=str).encode("utf-8")


def export_csv_bytes(state: Dict[str, Any]) -> bytes:
    """
    Flattens the key tabular pieces of the session into a single
    multi-section CSV (sections separated by a header line) since the
    dataset is heterogeneous.
    """
    buf = io.StringIO()

    def write_section(title: str, df: pd.DataFrame):
        buf.write(f"# {title}\n")
        if df is not None and not df.empty:
            df.to_csv(buf, index=False)
        else:
            buf.write("(no data)\n")
        buf.write("\n")

    alternatives = state.get("alternatives") or []
    alt_df = pd.DataFrame(alternatives) if alternatives else pd.DataFrame()
    write_section("ALTERNATIVES", alt_df)

    mce_table = state.get("mce_result_table")
    if isinstance(mce_table, pd.DataFrame):
        write_section("MCE_RESULTS", mce_table.reset_index().rename(columns={"index": "alternative"}))

    audit = state.get("audit_log") or []
    write_section("AUDIT_LOG", pd.DataFrame(audit))

    return buf.getvalue().encode("utf-8")


def export_html_report(state: Dict[str, Any]) -> bytes:
    bundle = build_export_bundle(state)
    project = bundle.get("project") or {}
    final_decision = bundle.get("final_decision") or {}
    mce_rows = bundle.get("mce_result_table") or []

    mce_html = "<p>No MCE results available.</p>"
    if mce_rows:
        cols = list(mce_rows[0].keys())
        header = "".join(f"<th>{c}</th>" for c in cols)
        body_rows = ""
        for row in mce_rows:
            body_rows += "<tr>" + "".join(f"<td>{row.get(c)}</td>" for c in cols) + "</tr>"
        mce_html = f"<table border='1' cellpadding='4' cellspacing='0'><tr>{header}</tr>{body_rows}</table>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>VE-AI Final Report \u2014 {project.get('project_name', '')}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; color: #1a1a2e; }}
h1 {{ color: #0f3460; }}
h2 {{ color: #16213e; border-bottom: 1px solid #ccc; padding-bottom: 4px; }}
table {{ border-collapse: collapse; margin-bottom: 20px; }}
th {{ background-color: #0f3460; color: white; padding: 6px; }}
td {{ padding: 6px; }}
.notice {{ background: #fff3cd; padding: 10px; border-left: 4px solid #e0a800; margin-bottom: 20px; }}
</style>
</head>
<body>
<h1>VE-AI Final Report</h1>
<div class="notice">Synthetic Demonstration Data \u2014 Not Official Project Data</div>
<p>Generated: {bundle.get('export_timestamp')}</p>

<h2>Project</h2>
<p>{project.get('project_name')} \u2014 {project.get('analysis_scope')}<br>
Type: {project.get('project_type')} | Location: {project.get('location')} | Phase: {project.get('project_phase')}<br>
Currency: {project.get('currency')} | Discount Rate: {project.get('discount_rate')} | Analysis Period: {project.get('analysis_period_years')} years</p>

<h2>Final Recommendation</h2>
<p>Recommended Alternative: <strong>{final_decision.get('recommended_alternative', 'N/A')}</strong><br>
Label: AI-Assisted / MCE-Based Recommendation \u2014 Subject to Engineer Approval<br>
Engineer Decision: <strong>{final_decision.get('engineer_decision', 'PENDING')}</strong><br>
Comment: {final_decision.get('comment', '')}</p>

<h2>Multi-Criteria Evaluation Results</h2>
{mce_html}

<h2>Disclaimer</h2>
<p>This prototype provides AI-assisted decision support for Value Engineering. It does not
replace structural analysis, engineering codes, specialist review, safety assessment, or
professional engineering judgment. AI provides decision support and alternative suggestions.
Final engineering approval remains with the responsible engineer.</p>

</body>
</html>
"""
    return html.encode("utf-8")

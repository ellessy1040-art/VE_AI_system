"""
utils/audit.py

Audit log utilities. The audit log lives in st.session_state and is
appended to by every important action across the whole application
(project creation, baseline creation, AI generation, review decisions,
LCC/risk calculations, weight changes, sensitivity runs, and the
final engineer decision).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
import io
import pandas as pd

import streamlit as st

AUDIT_KEY = "audit_log"


def init_audit_log() -> None:
    if AUDIT_KEY not in st.session_state:
        st.session_state[AUDIT_KEY] = []


def log_action(
    action: str,
    entity: str,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    source: str = "SYSTEM",
    model_name: Optional[str] = None,
    model_version: Optional[str] = None,
    decision: Optional[str] = None,
    user: str = "engineer",
) -> None:
    init_audit_log()
    entry = {
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "action": action,
        "entity": entity,
        "old_value": old_value,
        "new_value": new_value,
        "source": source,
        "model_name": model_name,
        "model_version": model_version,
        "decision": decision,
        "user": user,
    }
    st.session_state[AUDIT_KEY].append(entry)


def get_audit_log() -> List[Dict[str, Any]]:
    init_audit_log()
    return st.session_state[AUDIT_KEY]


def audit_log_dataframe() -> pd.DataFrame:
    log = get_audit_log()
    if not log:
        return pd.DataFrame(columns=[
            "timestamp", "action", "entity", "old_value", "new_value",
            "source", "model_name", "model_version", "decision", "user",
        ])
    return pd.DataFrame(log)


def audit_log_to_csv_bytes() -> bytes:
    df = audit_log_dataframe()
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

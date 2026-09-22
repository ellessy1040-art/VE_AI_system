"""
ai/llm_client.py

Thin wrapper around an OpenAI-compatible chat-completions API.
Automatically falls back to the deterministic Mock AI (ai/mock_ai.py)
whenever:
  - no API key is configured, or
  - the API call fails for any reason (network, auth, parsing, etc.)

This guarantees the Streamlit app is always runnable, even completely
offline, per the project requirements.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Any, Tuple

from ai import mock_ai
from ai.prompts import (
    ALTERNATIVES_SYSTEM_PROMPT,
    build_alternatives_user_prompt,
    EXPLANATION_SYSTEM_PROMPT,
    build_explanation_user_prompt,
)


def _get_config() -> Tuple[str | None, str, str]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip() or None
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    return api_key, base_url, model


def is_live_mode_available() -> bool:
    api_key, _, _ = _get_config()
    return api_key is not None


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def generate_alternatives(ai_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempts a real LLM call to generate structured alternatives.
    Falls back to Mock AI automatically on any failure.

    Returns a dict: {"alternatives": [...], "source": "LIVE_LLM"|"MOCK_AI",
                      "model_name": str, "error": Optional[str]}
    """
    api_key, base_url, model = _get_config()
    if not api_key:
        result = mock_ai.generate_mock_alternatives()
        result["error"] = None
        return result

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": ALTERNATIVES_SYSTEM_PROMPT},
                {"role": "user", "content": build_alternatives_user_prompt(ai_context)},
            ],
            temperature=0.3,
        )
        raw_text = response.choices[0].message.content
        parsed = json.loads(_strip_code_fences(raw_text))
        if "alternatives" not in parsed:
            raise ValueError("LLM response missing 'alternatives' key")
        # tag each alternative with an alt_id if missing
        for i, alt in enumerate(parsed["alternatives"]):
            alt.setdefault("alt_id", f"ALT_LLM_{i+1}")
            alt.setdefault("review_status", "AI_PROPOSED")
        parsed["source"] = "LIVE_LLM"
        parsed["model_name"] = model
        parsed["error"] = None
        return parsed
    except Exception as exc:  # noqa: BLE001 - intentional broad fallback
        result = mock_ai.generate_mock_alternatives()
        result["error"] = f"Live LLM call failed, fell back to Mock AI: {exc}"
        return result


def generate_explanation(results_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempts a real LLM call to explain deterministic results.
    Falls back to Mock AI automatically on any failure.

    Returns a dict: {"explanation": str, "source": "LIVE_LLM"|"MOCK_AI",
                      "model_name": str, "error": Optional[str]}
    """
    api_key, base_url, model = _get_config()
    if not api_key:
        return {
            "explanation": mock_ai.generate_mock_explanation(results_summary),
            "source": "MOCK_AI",
            "model_name": "mock-ai-demo-v1",
            "error": None,
        }

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                {"role": "user", "content": build_explanation_user_prompt(results_summary)},
            ],
            temperature=0.3,
        )
        text = response.choices[0].message.content
        return {
            "explanation": text,
            "source": "LIVE_LLM",
            "model_name": model,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "explanation": mock_ai.generate_mock_explanation(results_summary),
            "source": "MOCK_AI",
            "model_name": "mock-ai-demo-v1",
            "error": f"Live LLM call failed, fell back to Mock AI: {exc}",
        }

# VE-AI: AI-Assisted Value Engineering Decision Support System

A master's research prototype demonstrating an end-to-end **Value Engineering (VE)**
decision-support workflow for large infrastructure projects, combining a deterministic
engineering calculation core with an AI layer used strictly for **idea generation** and
**explanation** — never for calculation or final approval.

> **Synthetic Demonstration Data — Not Official Project Data.**
> Every numerical assumption in this prototype (costs, dimensions, risk scores,
> sustainability indices) is a synthetic, illustrative value created only to
> demonstrate the workflow. It does **not** represent real Egyptian Monorail project data.

## Case Study

**Egyptian Monorail — Guideway Beam System**
Baseline: 1,200 prestressed-concrete guideway beams (24 m long), 50-year analysis
period, 8% discount rate, EGP currency. Three AI-style candidate alternatives are
compared against this baseline: a **Steel Box Girder**, a **Steel-Concrete Composite
Girder**, and an **Optimized Prestressed Concrete Beam**.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in Demo Mode automatically — no API key is required. Walk through the
sidebar pages in order (1 → 11): each page builds on data from the previous one.

## Project Structure

```
app.py                  Streamlit entry point + sidebar navigation
data/demo_case.py        All synthetic demonstration data for the case study
models/schemas.py        Pydantic schemas (project, component, alternatives, audit, AI I/O)
engines/
    lcc_engine.py         Deterministic discounted Life-Cycle Cost engine
    risk_engine.py        Deterministic Probability x Impact risk engine
    mce_engine.py          Deterministic Multi-Criteria Evaluation (normalize + weight + rank)
    sensitivity.py         Re-runs MCE under multiple weight scenarios
ai/
    prompts.py            System/user prompt templates sent to the LLM
    mock_ai.py             Deterministic offline "Demo Mode" AI (used when no API key)
    llm_client.py          OpenAI-compatible client with automatic Mock AI fallback
ui/                       One module per sidebar page (Streamlit UI only, no business logic)
utils/
    audit.py               Session-based audit log (append + CSV export)
    validation.py           Shared validation helpers (weights, rates, ranges)
    export.py               JSON / CSV / HTML report export
tests/                    Pytest unit tests for every deterministic engine + schemas
```

## Configuring a Live LLM

By default the app runs in **Demo Mode — Mock AI**, which returns deterministic,
predefined alternatives so the prototype always works offline. To enable a real
OpenAI-compatible LLM:

1. Copy `.env.example` to `.env`.
2. Fill in:
   ```
   OPENAI_API_KEY=sk-...
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4o-mini
   ```
3. Restart the app. The sidebar will show "🌐 Live LLM configured".
4. If the live API call fails for any reason (network, auth, malformed JSON), the app
   **automatically falls back to Mock AI** and shows the error — it never crashes the
   workflow.

`OPENAI_BASE_URL` can point at any OpenAI-compatible endpoint (OpenAI, Azure OpenAI,
a local server such as Ollama's OpenAI shim, etc.), since `ai/llm_client.py` uses the
standard `openai` Python SDK against a configurable base URL.

## Running the Tests

```bash
pytest tests/ -v
```

Covers: discounting math, replacement-cost timing, residual value, LCC totals, risk
scoring, weight-sum validation, benefit/cost normalization (including the
divide-by-zero edge case), MCE weighted scoring, sensitivity ranking/robustness, and
Pydantic schema validation (including the AI alternatives JSON schema).

---

## 1. How Data Flows Through the System

```
Project Setup → Component & Function → Baseline
      → AI Alternative Generation → Engineer Review (Accept/More Info/Reject)
      → LCC Engine → Risk Engine → Sustainability Indicators
      → Multi-Criteria Evaluation (normalize + weight + rank)
      → Sensitivity Analysis (re-run MCE under multiple weight scenarios)
      → AI Explanation (reads the already-calculated results, changes nothing)
      → Engineer Decision (Approve / Request More Info / Reject) → Export / Audit Log
```

All of this lives in `st.session_state`, so data entered or edited on one page (e.g.
editing a beam's baseline material on the Component page, or a risk's probability on
the Risk page) is immediately reflected wherever it is used downstream (LCC, MCE,
Sensitivity, Final Recommendation). Every important action is appended to the audit
log (`utils/audit.py`) with a timestamp, actor, old/new value, and source.

## 2. Which Components Use AI

- **AI Alternative Generation** (`ai/llm_client.generate_alternatives`): proposes 2–4
  candidate design alternatives in structured JSON (name, principle, technical
  changes, benefits, constraints, required data, risks, a *low-confidence* cost
  estimate). It is explicitly instructed never to invent verified structural
  capacities, code compliance, or certified prices.
- **AI Explanation** (`ai/llm_client.generate_explanation`): after the deterministic
  ranking is complete, the AI is given the already-calculated results and asked to
  explain them in plain language (why the top alternative ranked first, which
  criteria mattered, remaining risks, missing data, sensitivity to weights, what
  still needs verification). It is explicitly instructed not to alter any number or
  the ranking.
- **Mock AI** (`ai/mock_ai.py`): a fully deterministic, offline stand-in for both of
  the above, used automatically whenever no API key is configured or a live call
  fails, so the prototype is always runnable.

## 3. Which Components Are Deterministic (Never AI)

- **LCC Engine** (`engines/lcc_engine.py`): discounted cash-flow Life-Cycle Cost,
  computed directly from numeric inputs using
  `LCC = C0 + Σ[(Cop,t + Cm,t + Crep,t)/(1+r)^t] - RV/(1+r)^N`.
- **Risk Engine** (`engines/risk_engine.py`): `Score = Probability × Impact` on a
  1–5 scale, aggregated per alternative.
- **Sustainability**: raw indicators (embodied carbon, construction waste,
  operational energy indices) are shown first; a composite index (their average) is
  then calculated for use in the MCE.
- **MCE Engine** (`engines/mce_engine.py`): min–max normalization (benefit criteria:
  higher raw value → higher normalized score; cost/risk criteria: lower raw value →
  higher normalized score), then `Final Score = Σ(weight × normalized_score)`,
  producing the ranking.
- **Sensitivity Engine** (`engines/sensitivity.py`): re-runs the MCE engine under
  multiple weight scenarios and reports rank changes and robustness — no AI involved.

The AI layer never sees or touches these calculations; it is only ever given the
**already-computed results** to explain, or asked to propose **qualitative** design
alternatives that a human then supplies real engineering numbers for.

## 4. Where the Engineer Makes Decisions

- **Engineer Review** (AI Alternatives page): every AI-proposed alternative starts as
  `AI_PROPOSED` and must be explicitly set to `ACCEPTED_FOR_ANALYSIS`,
  `MORE_INFO_REQUESTED` (reason required), or `REJECTED` (reason required) before it
  can enter LCC / Risk / MCE / Ranking.
- **Financial, risk, and sustainability inputs** are all editable by the engineer on
  their respective pages — the AI never sets or calculates these values.
- **Criteria weights** for the Multi-Criteria Evaluation are fully editable (must sum
  to 100%).
- **Final Engineer Decision** (Final Recommendation page): the highest-ranked
  accepted alternative is shown labeled *"AI-Assisted / MCE-Based Recommendation —
  Subject to Engineer Approval"*. The engineer must explicitly select **Approve /
  Request More Information / Reject**, enter their name and a comment, before the
  decision is recorded in the audit log. The AI never approves, certifies, or
  finalizes anything.

## 5. How to Run the Prototype

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then, in the browser:
1. **Project Overview / Component & Function / Baseline** — review or edit the
   synthetic case-study data.
2. **AI Alternatives** — click *Generate AI Alternatives*, then Accept/Reject each
   proposed alternative.
3. **LCC Analysis / Risk Analysis / Sustainability** — review/edit the deterministic
   engineering inputs for each accepted alternative.
4. **Multi-Criteria Evaluation** — set criteria weights (must total 100%) to see the
   calculated ranking.
5. **Sensitivity Analysis** — run the predefined and/or a custom weighting scenario
   to test how robust the ranking is.
6. **Final Recommendation** — generate the AI explanation, then record the engineer's
   Approve / Request More Info / Reject decision.
7. **Audit Log** — review every logged action, export to CSV.
8. Use the **Export Results** section on the Final Recommendation page for JSON, CSV,
   or an HTML report.

## 6. How to Switch from Mock AI to a Real LLM

Mock AI is used automatically whenever `OPENAI_API_KEY` is unset. To use a real LLM:

1. `cp .env.example .env`
2. Set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` in `.env`.
3. Restart `streamlit run app.py`. The sidebar and the AI Alternatives / Final
   Recommendation pages will show "🌐 Live LLM" instead of "🧪 Demo Mode — Mock AI",
   and generated content will be tagged with the real model name.
4. If the live call fails, the app transparently falls back to Mock AI and displays
   the error message so the failure is auditable rather than silent.

---

### Engineering Safety Notice

This prototype provides AI-assisted decision support for Value Engineering. It does
not replace structural analysis, engineering codes, specialist review, safety
assessment, or professional engineering judgment. AI provides decision support and
alternative suggestions only — final engineering approval remains with the
responsible engineer.

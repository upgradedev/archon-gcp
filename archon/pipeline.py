"""The analysis pipeline — a **Google ADK `SequentialAgent`**.

This is the course's *multi-agent* concept, and the GCP echo of the Archon
lineage (Nebius/Azure run classifier→pnl→cashflow→employee→validator→narrator).
Here three sub-agents run in order, passing state forward via `output_key`:

    reconciler ─▶ validator ─▶ narrator
       │             │            │
   restates the   confirms the   writes the CFO
   bank↔doc       R1–R4 gates    executive summary
   matches        hold

The deterministic engine (ledger + validation) computes every number first; the
pipeline's Gemini turns only *phrase* the handed-in fact sheet, so the narrative
can never contradict the books. Sub-agent models are injectable, which lets the
whole chain run **offline** in tests with scripted fakes (no API key).
"""
from __future__ import annotations

import os

from .ledger import Ledger
from .narrator import facts_sheet, narrate
from .validation import summary as validation_summary
from .validation import validate

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

_RECONCILER_INSTRUCTION = """\
You are the reconciliation stage of an accounting pipeline. You are given a fact
sheet of already-computed books. Restate, in one sentence, whether the bank lines
reconcile to their invoices and payroll. Do not invent figures."""

_VALIDATOR_INSTRUCTION = """\
You are the validation stage. Given the reconciliation note below and the fact
sheet, confirm in one sentence whether the R1–R4 consistency gates hold.
Reconciliation: {reconciliation}
Do not invent figures."""

_NARRATOR_INSTRUCTION = """\
You are the narrator stage — a CFO-level analyst. Using the validation note and
the fact sheet, write a concise 2–3 sentence executive summary. Emphasise that
payroll EXPENSE exceeds the cash that left the bank (EFKA + withheld tax settle
later). Validation: {validation}
Report only figures present in the fact sheet."""


def build_analysis_pipeline(models=None):
    """Construct the `SequentialAgent`. `models` (3 ADK models) is for offline
    tests; omit it to use Gemini (`GEMINI_MODEL`). Construction needs no API key
    — only running the pipeline against real Gemini does."""
    from google.adk.agents import LlmAgent, SequentialAgent

    m = models or [DEFAULT_MODEL, DEFAULT_MODEL, DEFAULT_MODEL]
    if len(m) != 3:
        raise ValueError("models must be a list of exactly 3 ADK models/model-names")

    reconciler = LlmAgent(name="reconciler", model=m[0],
                          instruction=_RECONCILER_INSTRUCTION, output_key="reconciliation")
    validator = LlmAgent(name="validator", model=m[1],
                         instruction=_VALIDATOR_INSTRUCTION, output_key="validation")
    narrator = LlmAgent(name="narrator", model=m[2],
                        instruction=_NARRATOR_INSTRUCTION, output_key="summary")
    return SequentialAgent(name="archon_analysis",
                           sub_agents=[reconciler, validator, narrator])


def run_analysis(ledger: Ledger, models=None, app_name: str = "archon-analysis") -> dict:
    """Run the deterministic engine, then the ADK SequentialAgent over its facts.

    Returns the three stage outputs (reconciliation / validation / summary) plus
    the deterministic fact sheet. Requires either injected `models` (tests) or a
    configured Gemini key; callers without either should use `narrate()` directly.
    """
    import asyncio

    from google.adk.runners import InMemoryRunner
    from google.genai import types

    stmt = ledger.statements()
    checks = validate(ledger)
    facts = facts_sheet(stmt, checks)

    pipeline = build_analysis_pipeline(models=models)
    runner = InMemoryRunner(agent=pipeline, app_name=app_name)
    uid, sid = "owner", "analysis-1"
    try:
        runner.session_service.create_session_sync(app_name=app_name, user_id=uid, session_id=sid)
    except AttributeError:  # pragma: no cover - version shim
        asyncio.new_event_loop().run_until_complete(
            runner.session_service.create_session(app_name=app_name, user_id=uid, session_id=sid))

    msg = types.Content(role="user", parts=[types.Part(
        text=f"Analyse this month's books.\n\n{facts}")])
    for _ in runner.run(user_id=uid, session_id=sid, new_message=msg):
        pass

    async def _state():
        s = await runner.session_service.get_session(app_name=app_name, user_id=uid, session_id=sid)
        return dict(s.state)

    state = asyncio.new_event_loop().run_until_complete(_state())
    return {
        "facts": facts,
        "reconciliation": state.get("reconciliation", ""),
        "validation": state.get("validation", ""),
        "summary": state.get("summary", "") or narrate(stmt, checks),
        "gates": validation_summary(checks),
    }

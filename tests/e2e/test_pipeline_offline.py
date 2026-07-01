"""End-to-end: the ADK SequentialAgent analysis pipeline, run fully offline.

Each of the three sub-agents gets its own scripted model, and we assert state is
handed forward via `output_key` — a real run of the multi-agent course concept
with no API key. The deterministic engine computes the numbers; the pipeline
narrates them.
"""
import pytest

pytest.importorskip("google.adk")

from adk_fakes import ScriptedText  # noqa: E402
from archon.documents import SAMPLE_DOCS  # noqa: E402
from archon.extract import extract_document  # noqa: E402
from archon.ledger import Ledger  # noqa: E402
from archon.pipeline import run_analysis  # noqa: E402


def _ledger() -> Ledger:
    led = Ledger(period="2026-01", company="Reflective IKE")
    for name, text in SAMPLE_DOCS.items():
        led.add(extract_document(text, source_file=name, period="2026-01"))
    return led


def test_sequential_pipeline_produces_all_three_stage_outputs():
    models = [
        ScriptedText("All 3 bank lines reconcile to their documents."),
        ScriptedText("R1-R4 all hold."),
        ScriptedText("Net loss of 24,249; payroll expense runs ahead of cash."),
    ]
    result = run_analysis(_ledger(), models=models)
    assert result["reconciliation"] == "All 3 bank lines reconcile to their documents."
    assert result["validation"] == "R1-R4 all hold."
    assert "payroll expense" in result["summary"]
    assert result["gates"] == "4/4 validation gates passed"
    # the fact sheet handed to the LLM stages carries the real, computed numbers
    assert "Net profit: -24249.00" in result["facts"]


def test_pipeline_summary_falls_back_to_deterministic_when_stage_empty():
    models = [ScriptedText("recon"), ScriptedText("valid"), ScriptedText("")]
    result = run_analysis(_ledger(), models=models)
    # empty narrator output → deterministic narrate() fills the summary
    assert "net loss" in result["summary"].lower()

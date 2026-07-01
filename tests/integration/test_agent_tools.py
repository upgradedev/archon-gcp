"""Integration: the real ADK conversational agent driving its tools offline.

Uses a scripted fake model (no API key, no network) so we exercise genuine ADK
function-calling against the live tool closures wired to a real Ledger + Store.
"""
import pytest

pytest.importorskip("google.adk")

from adk_fakes import ScriptedLlm  # noqa: E402
from archon.agent import ArchonAgent  # noqa: E402
from archon.documents import SAMPLE_DOCS  # noqa: E402

PAYROLL = SAMPLE_DOCS["payroll_2026-01.txt"]
SALES = SAMPLE_DOCS["sales_invoice_INV-2026-014.txt"]


def test_agent_records_document_via_tool_call():
    model = ScriptedLlm([
        ("call", "record_document", {"doc_text": PAYROLL, "source_file": "payroll.txt"}),
        ("text", "Recorded the payroll run."),
    ])
    agent = ArchonAgent(period="2026-01", company="Meridian Trading Co", model=model)
    reply = agent.send("Please record this payroll document.")
    assert "Recorded" in reply
    assert len(agent.ledger.documents) == 1
    assert agent.ledger.documents[0].doc_type.value == "payroll"


def test_agent_chains_record_validate_and_report():
    model = ScriptedLlm([
        ("call", "record_document", {"doc_text": SALES, "source_file": "sales.txt"}),
        ("call", "record_document", {"doc_text": PAYROLL, "source_file": "payroll.txt"}),
        ("call", "validate_books", {}),
        ("call", "get_books", {}),
        ("text", "Two documents booked; payroll expense exceeds cash out."),
    ])
    agent = ArchonAgent(period="2026-01", company="Meridian Trading Co", model=model)
    reply = agent.send("Record these and tell me the books.")
    assert "payroll expense" in reply.lower()
    assert len(agent.ledger.documents) == 2
    # the ledger the tools mutated is the one we can now inspect deterministically
    s = agent.ledger.statements()
    assert s.payroll_expense == 28249.00


def test_agent_offline_model_needs_no_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    # constructing with an injected model must not raise the missing-key error
    ArchonAgent(model=ScriptedLlm([("text", "ok")]))

"""Archon's conversational layer — a **Google ADK** agent on **Gemini**.

The agent holds the conversation and decides which tools to call; the tools wrap
the deterministic ledger (ledger.py) and persist to the store (Firestore/local).
Session memory means the owner can feed documents in across turns and ask for the
books at any point.

Requires `google-adk` + `GOOGLE_API_KEY` (Gemini via AI Studio). With neither,
use the deterministic pipeline in cli.py — the bookkeeping is identical.
"""
from __future__ import annotations

import os

from .extract import extract_document
from .ledger import Ledger
from .store import get_store
from .validation import summary as validation_summary
from .validation import validate

INSTRUCTION = """\
You are Archon, a unified financial intelligence agent for a small business. The owner
sends you business documents — sales invoices, purchase invoices, bank
transactions, payroll runs. For each document the user gives you, call
`record_document`. When asked about money, call `reconcile_bank` (to match bank
lines to invoices/payroll), `validate_books` (to run the R1–R4 consistency
gates), and/or `get_books` (for the P&L, cash view, AR/AP), then explain plainly.

Be precise and never invent figures — report only what the tools return.
Remember: payroll EXPENSE (true employer cost) is larger than the net amount that
leaves the bank; the difference (employer social-security contributions + withheld
tax) is a payable that settles later. Surface that cash-timing distinction when
payroll is involved. Also flag any bank line that has no matching invoice or
document — a payment with nothing behind it is exactly the kind of gap owners miss.
"""

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


class ArchonAgent:
    def __init__(self, period: str = "2026-01", company: str | None = None,
                 model: str = DEFAULT_MODEL, app_name: str = "archon"):
        try:
            from google.adk.agents import Agent
            from google.adk.runners import InMemoryRunner
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "google-adk not installed. `pip install google-adk`, or use the "
                "deterministic pipeline (python -m archon.cli)."
            ) from e
        # A string model name resolves to real Gemini and needs a key; an injected
        # model object (e.g. a scripted fake in tests) runs fully offline.
        if isinstance(model, str) and not (
            os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GENAI_USE_VERTEXAI")
        ):
            raise RuntimeError("Set GOOGLE_API_KEY (AI Studio) or configure Vertex AI for ADK.")

        self.ledger = Ledger(period=period, company=company)
        self.store = get_store()
        self._user = "owner"
        self._session_id = "session-1"
        self._app = app_name

        # ── tools (closures over session ledger + store) ──────────────────────
        def record_document(doc_text: str, source_file: str = "document.txt") -> dict:
            """Classify and post one business document to the books.

            Args:
                doc_text: the document's text (OCR/transcript).
                source_file: a short filename for traceability.
            """
            self.store.put_document(source_file, doc_text)
            doc = extract_document(doc_text, source_file=source_file, period=self.ledger.period)
            entry = self.ledger.add(doc)
            self.store.save_ledger(self.ledger)
            return {"classified_as": doc.doc_type.value, "posted_memo": entry.memo,
                    "balanced": entry.is_balanced, "documents_recorded": len(self.ledger.documents)}

        def reconcile_bank() -> dict:
            """Match every bank line to the invoice or payroll it settles."""
            return {"matches": [
                {"bank_ref": m.bank_ref, "matched": m.matched, "amount": m.amount, "note": m.note}
                for m in self.ledger.reconcile()
            ]}

        def validate_books() -> dict:
            """Run the R1–R4 cross-document consistency gates over the books."""
            results = self.ledger and validate(self.ledger)
            return {"summary": validation_summary(results),
                    "gates": [{"rule": r.rule, "passed": r.passed,
                               "severity": r.severity, "message": r.message} for r in results]}

        def get_books() -> dict:
            """Return the period P&L, cash view, AR/AP, and notes."""
            s = self.ledger.statements()
            return {
                "period": s.period, "revenue": s.revenue, "opex": s.opex,
                "payroll_expense": s.payroll_expense, "net_profit": s.net_profit,
                "cash_in": s.cash_in, "cash_out": s.cash_out, "net_cash": s.net_cash,
                "accounts_receivable": s.accounts_receivable,
                "accounts_payable": s.accounts_payable, "notes": s.notes,
            }

        self._agent = Agent(name="archon_bookkeeper", model=model,
                            instruction=INSTRUCTION,
                            tools=[record_document, reconcile_bank, validate_books, get_books])
        self._runner = InMemoryRunner(agent=self._agent, app_name=app_name)
        self._ensure_session()

    def _ensure_session(self) -> None:
        svc = self._runner.session_service
        try:  # ADK session creation is sync in some versions, async in others
            svc.create_session_sync(app_name=self._app, user_id=self._user, session_id=self._session_id)
        except AttributeError:
            import asyncio
            asyncio.get_event_loop().run_until_complete(
                svc.create_session(app_name=self._app, user_id=self._user, session_id=self._session_id))

    def send(self, message: str) -> str:
        """One conversational turn; returns Archon's final text reply."""
        from google.genai import types

        content = types.Content(role="user", parts=[types.Part(text=message)])
        final = ""
        for event in self._runner.run(user_id=self._user, session_id=self._session_id,
                                      new_message=content):
            if event.is_final_response() and event.content and event.content.parts:
                final = event.content.parts[0].text
        return final

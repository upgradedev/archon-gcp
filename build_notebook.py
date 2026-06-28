"""Assemble a self-contained Kaggle notebook from the archon source.

Inlines models + extract + ledger + documents into one cell (relative imports
stripped, since everything shares one namespace), then adds the demo and the
optional ADK+Gemini agent cell. Keeping the notebook generated from source means
it never drifts from the repo.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "archon"

CORE_MODULES = ["models.py", "extract.py", "ledger.py", "documents.py"]


def _inline(module: str) -> str:
    src = (PKG / module).read_text(encoding="utf-8")
    # drop intra-package relative imports — all symbols live in one cell now.
    # Multi-line parenthesised form first, then single-line.
    src = re.sub(r"from \.\w+ import \([^)]*\)", "", src, flags=re.DOTALL)
    src = re.sub(r"^from \.\w+ import .*$", "", src, flags=re.MULTILINE)
    src = re.sub(r"^from \. import .*$", "", src, flags=re.MULTILINE)
    src = re.sub(r"^from __future__ import .*$", "", src, flags=re.MULTILINE)  # one at the top instead
    return f"# ── archon/{module} " + "─" * (50 - len(module)) + "\n" + src.strip() + "\n"


core = "from __future__ import annotations\n\n" + "\n\n".join(_inline(m) for m in CORE_MODULES)

md_intro = """\
# Archon — the autonomous bookkeeper 🇬🇷
### Kaggle × Google AI Agents Intensive (Vibe Coding) — Capstone

Archon reads the documents a small business actually receives — **sales invoices,
purchase invoices, bank transactions, payroll** — **classifies** them, posts
**double-entry journal entries**, **reconciles** invoices against bank payments,
and rolls everything up into a **P&L, a cash view, and AR/AP**.

It's an AI **bookkeeper**, not a dashboard — and it keeps real books, so the
numbers are auditable. Built with **Google ADK + Gemini** on **GCP** (the GCP
member of the Archon family, which also runs on Nebius and Azure).

> The cell below inlines the whole engine so this notebook runs top-to-bottom
> with **zero setup**. The conversational ADK+Gemini agent is at the end (add a
> `GOOGLE_API_KEY` secret to run it)."""

demo = '''\
# Ingest a mixed month, keep the books, show the result
led = Ledger(period=GROUND_TRUTH["period"], company="Reflective IKE")
for name, text in SAMPLE_DOCS.items():
    doc = extract_document(text, source_file=name, period=led.period)
    led.add(doc)
    print(f"classified {doc.doc_type.value:<17} <- {name}")

s = led.statements()
print("\\n=== JOURNAL (double-entry) ===")
for e in led.entries:
    print(("  balanced  " if e.is_balanced else "  UNBALANCED ") + e.memo)

print("\\n=== RECONCILIATION ===")
for m in led.reconcile():
    print(f"  {'OK ' if m.matched else 'X  '}{m.bank_ref:<24} EUR {m.amount:>10,.2f}  {m.note}")

print("\\n=== P&L ===")
print(f"  Revenue            EUR {s.revenue:>12,.2f}")
print(f"  Operating expenses EUR {s.opex:>12,.2f}")
print(f"  Payroll expense    EUR {s.payroll_expense:>12,.2f}")
print(f"  Net profit         EUR {s.net_profit:>12,.2f}")
print("\\n=== CASH ===")
print(f"  In  EUR {s.cash_in:>12,.2f}   Out EUR {s.cash_out:>12,.2f}   Net EUR {s.net_cash:>12,.2f}")
print(f"  AR EUR {s.accounts_receivable:,.2f}   AP EUR {s.accounts_payable:,.2f}")
for n in s.notes:
    print("  note:", n)

assert led.all_entries_balanced()
assert s.net_profit == GROUND_TRUTH["net_profit"]
print("\\nSelf-check passed: every entry balances; figures match ground truth.")'''

md_agent = """\
## The conversational agent (Google ADK + Gemini)

Above is the deterministic engine. Archon's **agent** wraps it: the owner feeds
documents in across turns, and Gemini decides when to call `record_document`,
`reconcile_bank`, and `get_books` — with the books held in **session memory**.

Add a **`GOOGLE_API_KEY`** secret (Kaggle → Add-ons → Secrets) and run the cell
below. Without a key, the deterministic books above are identical — the agent is
the conversational layer, not the source of the numbers."""

agent_cell = '''\
import os
try:
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    HAVE_ADK = bool(os.environ.get("GOOGLE_API_KEY"))
except Exception:
    HAVE_ADK = False

if not HAVE_ADK:
    print("google-adk + GOOGLE_API_KEY not configured — skipping the live agent.")
    print("The deterministic books above are the same numbers the agent reports.")
else:
    session_ledger = Ledger(period="2026-01", company="Reflective IKE")

    def record_document(doc_text: str, source_file: str = "doc.txt") -> dict:
        """Classify and post one business document to the books."""
        doc = extract_document(doc_text, source_file=source_file, period=session_ledger.period)
        e = session_ledger.add(doc)
        return {"classified_as": doc.doc_type.value, "memo": e.memo, "balanced": e.is_balanced}

    def reconcile_bank() -> dict:
        """Match every bank line to the invoice or payroll it settles."""
        return {"matches": [
            {"bank_ref": m.bank_ref, "matched": m.matched, "amount": m.amount, "note": m.note}
            for m in session_ledger.reconcile()
        ]}

    def get_books() -> dict:
        """Return the period P&L, cash view, and AR/AP."""
        s = session_ledger.statements()
        return {"revenue": s.revenue, "opex": s.opex, "payroll_expense": s.payroll_expense,
                "net_profit": s.net_profit, "cash_in": s.cash_in, "cash_out": s.cash_out,
                "net_cash": s.net_cash, "notes": s.notes}

    agent = Agent(name="archon_bookkeeper", model="gemini-2.0-flash",
                  instruction="You are Archon, an autonomous bookkeeper. Call record_document for "
                  "each document the user provides, reconcile_bank to match bank lines to invoices "
                  "and payroll, and get_books when asked about money. Payroll "
                  "EXPENSE exceeds the net that leaves the bank; the difference (EFKA+tax) is a "
                  "payable that settles later — surface that. Never invent figures.",
                  tools=[record_document, reconcile_bank, get_books])
    runner = InMemoryRunner(agent=agent, app_name="archon")
    try:
        runner.session_service.create_session_sync(app_name="archon", user_id="owner", session_id="s1")
    except AttributeError:
        import asyncio; asyncio.get_event_loop().run_until_complete(
            runner.session_service.create_session(app_name="archon", user_id="owner", session_id="s1"))

    for _, text in list(SAMPLE_DOCS.items()):
        list(runner.run(user_id="owner", session_id="s1",
             new_message=types.Content(role="user", parts=[types.Part(text="Record:\\n"+text)])))
    for ev in runner.run(user_id="owner", session_id="s1", new_message=types.Content(
            role="user", parts=[types.Part(text="Show the P&L and cash position. What did payroll "
            "really cost vs what left the account?")])):
        if ev.is_final_response() and ev.content and ev.content.parts:
            print(ev.content.parts[0].text)'''

md_outro = """\
## How it maps to the course
- **Tools / function calling** — `record_document`, `reconcile_bank`, `get_books`
- **Memory / state** — the agent's ledger accumulates documents across turns
- **Evaluation / guardrails** — every entry must balance; bank lines must reconcile
- **Vibe coding** — each module is a one-paragraph spec, prompted against ground-truth tests

**Code:** https://github.com/upgradedev/archon-gcp · MIT · also runs on Nebius and Azure."""


def code_cell(src):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": src.splitlines(keepends=True)}


def md_cell(src):
    return {"cell_type": "markdown", "metadata": {}, "source": src.splitlines(keepends=True)}


nb = {
    "cells": [md_cell(md_intro), code_cell(core), code_cell(demo),
              md_cell(md_agent), code_cell(agent_cell), md_cell(md_outro)],
    "metadata": {"kernelspec": {"language": "python", "display_name": "Python 3", "name": "python3"},
                 "language_info": {"name": "python", "version": "3.11"}},
    "nbformat": 4, "nbformat_minor": 5,
}

out = ROOT / "notebook.ipynb"
out.write_text(json.dumps(nb, indent=1), encoding="utf-8")
print("wrote", out, "·", len(nb["cells"]), "cells · core", len(core), "chars")

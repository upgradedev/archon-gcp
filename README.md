# Archon — the autonomous bookkeeper (GCP)

Public notebook: https://www.kaggle.com/code/efthimiosfousekis/archon-autonomous-bookkeeper-gcp  
Evidence CI: https://github.com/upgradedev/archon-gcp/actions/workflows/ci.yml

> Archon reads the documents a small business actually receives — sales invoices, purchase invoices, bank transactions, payroll — **classifies** them, posts **double-entry journal entries**, **reconciles** invoices against payments, and rolls everything into a **P&L, a cash view, and AR/AP**. An AI bookkeeper, not a dashboard.

Built for the **Kaggle × Google "AI Agents Intensive (Vibe Coding)" capstone** with **Google ADK + Gemini** on **GCP**. This is the **GCP member of the Archon family** (Archon also runs on Nebius and Azure — same product, platform-native infra each time).

---

## Why this exists

Owners look at the **bank statement** and think that's the picture. It isn't. The books only exist once you **correlate documents**: an invoice is revenue *and* a receivable until the bank line settles it; a payroll run is a much bigger **expense** than the net that leaves the account, because EFKA + withheld tax are **payables that settle later**. Archon does that correlation automatically and keeps real double-entry books.

> **No "payroll truth" gimmick.** A payroll run is ordinary bookkeeping with several journal lines, and the figures are jurisdiction-specific (this build uses the Greek EFKA/ΦΜΥ flavour — swap `ledger.py` to localise).

## What the demo shows (one mixed month)

```
Revenue            €  5,000.00      Cash in   € 6,200.00
Operating expenses €  1,000.00      Cash out  €15,590.00
Payroll expense    € 28,249.00      Net cash  €-9,390.00
Net profit         €-24,249.00      AR €0.00 · AP €0.00
ⓘ Payroll expense €28,249, but only the net (€14,350) left the bank this month;
  €13,899 of EFKA+tax is still payable.
```
Every journal entry balances; every bank line reconciles to its invoice/payroll.

## Quickstart

**Deterministic books + tests — no key, runs anywhere:**
```bash
pip install -r requirements.txt
python -m archon.cli        # ingest a mixed month → journal, reconciliation, P&L, cash
pytest -q                   # 11 tests, all offline
```

**Conversational agent (ADK + Gemini, multi-turn memory):**
```bash
cp .env.example .env        # add your Google AI Studio key
python -m archon.cli --agent
```

## Architecture (GCP-native)

```
        owner (chat / Kaggle notebook)
                   │
        ┌──────────▼───────────┐
        │  Archon ADK agent     │   Google ADK · Gemini   ← orchestrator + session memory
        └──────────┬───────────┘
        tool calls │  (function calling)
   ┌───────────────┼───────────────────────┐
   ▼               ▼               ▼
record_document  reconcile_bank   get_books
   │ classify+post   match bank↔doc   P&L · cash · AR/AP
   ▼
ledger.py (deterministic double-entry)  ──persist──▶  Firestore (ledger) · GCS (raw docs)
```

| Concern | GCP service | Local fallback |
|---|---|---|
| Model | **Gemini** (AI Studio / Vertex AI) | — (deterministic path needs no model) |
| Agent framework | **Google ADK** | — |
| Ledger persistence | **Firestore** | in-memory `LocalStore` |
| Raw documents | **Cloud Storage (GCS)** | in-memory |
| Serving (target) | **Cloud Run** | local CLI / notebook |

The **LLM orchestrates; the ledger is deterministic**, so the books are auditable. Set `GOOGLE_CLOUD_PROJECT` to use Firestore/GCS; otherwise everything runs locally.

## How it maps to the course

| Course concept | Where |
|---|---|
| **Tools / function calling** | `record_document`, `reconcile_bank`, `get_books` (ADK tools) |
| **Memory / state** | the agent's `Ledger` accumulates documents across turns |
| **Evaluation / guardrails** | every entry must balance; bank lines must reconcile |
| **Vibe coding / spec-driven** | each module has a one-paragraph contract; built by prompting against ground-truth tests |

## Tests

`pytest -q` → **11 offline tests**: classification, VAT-with-rate parsing, the payroll payable split, double-entry balance, the P&L/cash roll-up, reconciliation (including an unmatched-line case).

GitHub Evidence CI also rebuilds the Kaggle notebook and runs the deterministic
CLI demo. Latest known green run: `28311852093`.

## License

MIT.

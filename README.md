# Archon — unified financial intelligence (GCP)

> **The new era of financial intelligence.**

Public notebook: https://www.kaggle.com/code/efthimiosfousekis/archon-autonomous-bookkeeper-gcp  
Evidence CI: https://github.com/upgradedev/archon-gcp/actions/workflows/ci.yml

> Archon is a **unified financial intelligence platform** for small business. It is built to ingest **all** of a company's financial documents and data — sales & purchase invoices, sales & purchase orders, receipts, payments, bank transfers & statements, payroll, expenses, sales targets — into **one environment**, and turn them into a consolidated, **period-over-period view** (P&L, EBITDA, per-period metrics, total workforce cost, cash) — **and** cross-check the whole picture to surface **missing or inconsistent information**. Not a dashboard: an agent that keeps real, auditable books and tells you what doesn't add up.

Built for the **Kaggle × Google "AI Agents Intensive (Vibe Coding)" capstone** with **Google ADK + Gemini** on **GCP**. This is the **GCP member of the Archon family** (Archon also runs on Nebius and Azure — same product, platform-native infra each time).

> **Scope note (honest):** the broad multi-document consolidation above is the product **vision and direction**. This GCP build implements the spine of it end to end — classification, double-entry posting, **bank ↔ document reconciliation with unmatched lines flagged**, the R1–R4 cross-document eval gate, and a P&L / cash view — over one worked example month. The generic categories not yet in this build (e.g. sales-target variance) are on the roadmap, not narrated as shipped.

---

## Why this exists

Owners look at the **bank statement** and think that's the picture. It isn't. The picture only exists once you **bring every document together and cross-check them**: an invoice is revenue *and* a receivable until the bank line settles it; a purchase is an expense *and* a payable; and — crucially — **a bank payment with no matching invoice** is exactly the kind of gap that hides errors (the vendor never sent it, the bookkeeper never registered it, or the payment itself is wrong). Archon does that correlation and completeness-checking automatically and keeps real double-entry books.

The **workforce-cost** insight is one illustrative example: a payroll run is a much bigger **expense** than the net that leaves the account, because employer social-security contributions + withheld tax are **payables that settle later**. The figures are jurisdiction-specific (statutory employer social-security + national tax rules — swap `ledger.py` to localise).

## What the demo shows (one mixed month)

```
Revenue            €  5,000.00      Cash in   € 6,200.00
Operating expenses €  1,000.00      Cash out  €15,590.00
Payroll expense    € 28,249.00      Net cash  €-9,390.00
Net profit         €-24,249.00      AR €0.00 · AP €0.00
ⓘ Payroll expense €28,249, but only the net (€14,350) left the bank this month;
  €13,899 of employer social-security contributions + tax is still payable.
```
Every journal entry balances; every bank line reconciles to its invoice/payroll (an unmatched line is flagged "no matching document").

## Quickstart

**Deterministic books + tests — no key, runs anywhere:**
```bash
pip install -r requirements.txt
python -m archon.cli        # ingest a mixed month → journal, reconcile, validate (R1–R4), P&L, cash, summary
pytest -q                   # 43 tests, all offline (pip install -r requirements-dev.txt for coverage/nbmake)
```

**Conversational agent (ADK + Gemini, multi-turn memory):**
```bash
cp .env.example .env        # add your Google AI Studio key
python -m archon.cli --agent
```

## Run the live agent in the published Kaggle notebook

The notebook ships **deterministic-by-default** (the agent cell skips cleanly
without a key, so it always runs top-to-bottom). To make the *published* notebook
demonstrate the **live ADK + Gemini agent**:

1. Open the kernel on Kaggle → **Add-ons → Secrets** → add a secret named
   **`GOOGLE_API_KEY`** (your Google AI Studio / Gemini key) and attach it to the
   notebook.
2. No code change needed: `enable_internet` is already `true` in
   `kernel-metadata.json`, and the agent cell pulls the secret into the environment
   via `kaggle_secrets.UserSecretsClient`.
3. Re-run / re-push the kernel (`kaggle kernels push`). The agent cell now executes
   a **real Gemini tool-calling turn** (model `gemini-2.5-flash`) instead of the
   skip message. The deterministic books above are unchanged and remain the grading
   anchor (Gemini output is non-deterministic by nature).

Model note: the agent uses **`gemini-2.5-flash`** (override with `GEMINI_MODEL`).

## Architecture (GCP-native)

```
        owner (chat / Kaggle notebook)
                   │
        ┌──────────▼───────────┐
        │  Archon ADK agent     │   Google ADK · Gemini   ← orchestrator + session memory
        └──────────┬───────────┘
        tool calls │  (function calling)
   ┌───────────────┼───────────────┬───────────────────────┐
   ▼               ▼               ▼               ▼
record_document  reconcile_bank  validate_books   get_books
   │ classify+post   match bank↔doc   R1–R4 gate     P&L · cash · AR/AP
   ▼
ledger.py (deterministic double-entry) + validation.py (R1–R4)  ──persist──▶  Firestore · GCS

analysis pipeline (ADK SequentialAgent):  reconciler ─▶ validator ─▶ narrator   (state via output_key)
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
| **Tools / function calling** | `record_document`, `reconcile_bank`, `validate_books`, `get_books` (ADK tools) |
| **Multi-agent (`SequentialAgent`)** | `pipeline.py` — reconciler → validator → narrator, state passed via `output_key` |
| **Memory / state** | the agent's `Ledger` accumulates documents across turns |
| **Evaluation / guardrails** | every entry must balance; the R1–R4 cross-document gates (`validation.py`) must hold |
| **Vibe coding / spec-driven** | each module has a one-paragraph contract; built by prompting against ground-truth tests |

## Tests & CI

`pytest` → **43 offline tests** in a unit → integration → e2e pyramid (no API key,
no network):

| Layer | Covers |
|---|---|
| **unit** (`tests/unit`) | classification & VAT-rate parsing, double-entry posting, the payroll payable split, P&L/cash roll-up, reconciliation, the **R1–R4 validation gates**, the deterministic narrator, and the local store |
| **integration** (`tests/integration`) | the **real ADK agent** driving its tools via a scripted fake model; the `SequentialAgent` pipeline's shape (stages + `output_key`) |
| **e2e** (`tests/e2e`) | the full deterministic CLI run against ground truth; the **`SequentialAgent` running end-to-end offline** with scripted models |

The ADK agent and the `SequentialAgent` are exercised **for real** offline: the
tests inject `BaseLlm` fakes (`tests/adk_fakes.py`) that script tool calls and
stage outputs, so genuine ADK function-calling and sequential state hand-off run
in CI with no key.

```bash
pip install -r requirements-dev.txt
pytest --cov=archon            # ~94% coverage
```

**Evidence CI** (`.github/workflows/`): the test pyramid, a check that
`notebook.ipynb` is in sync with source, **executing the notebook top-to-bottom**
(nbmake), the deterministic demo, and **security gates** — `gitleaks` (secrets),
**CodeQL** (Python SAST), and `pip-audit` (dependency CVEs).

## License

MIT.

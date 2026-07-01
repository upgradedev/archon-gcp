# Archon — the autonomous bookkeeper (GCP)

**Kaggle × Google AI Agents Intensive (Vibe Coding) — Capstone Writeup**
**Track:** Agents for Business

> Paste this into the Kaggle Writeup editor. The only remaining manual field is
> the final public/unlisted video URL. Attach the public notebook + the video.

---

## 1. The problem  *(rubric: innovation · real-world value)*

A small-business owner looks at the **bank statement** and thinks that's the
picture. It isn't. The books only exist once you **correlate documents**: a sales
invoice is revenue *and* a receivable until a bank line settles it; a purchase is
an expense *and* a payable; and a payroll run is a far bigger **expense** than the
net that leaves the account — because EFKA (social insurance) and withheld tax are
**payables that settle later**.

Nobody does this correlation by hand reliably, and dashboards don't do it at all —
they just chart whatever the bank exports. The result: owners misjudge both their
**profit** and their **cash**.

## 2. What I built  *(rubric: solution design)*

**Archon** — a conversational agent that does a bookkeeper's job. You hand it the
documents you receive; it:

1. **Classifies** each document (sales / purchase / bank / payroll).
2. Posts a **balanced double-entry journal entry** for it.
3. **Reconciles** every bank line to the invoice or payroll it settles.
4. Runs an **eval gate** — four cross-document consistency rules (R1–R4) that
   fail the books when the documents disagree.
5. Rolls everything up into a **P&L, a cash view, and AR/AP**, then **narrates** a
   CFO-level summary — flagging the cash-timing gap (expense booked now, EFKA/tax
   paid later).

A conversational agent with four tools handles turns and memory; a
`SequentialAgent` chain (**reconciler → validator → narrator**) does the analysis.
The LLM orchestrates; the ledger math is **deterministic and auditable** (an
accountant can trust the numbers, not just the narration).

## 3. How I vibe-coded it  *(rubric: application of course concepts · vibe coding)*

I built it natural-language-first. Each module began as a one-sentence spec —
*"`ledger.post` turns a document into a balanced double-entry posting; payroll
splits into net-pay, EFKA and tax payables"* — which I prompted into code and then
**iterated against ground-truth tests** until `pytest` was green and every entry
balanced. The reconciliation guardrail came from asking *"what would make me not
trust these books?"* → every entry must balance; every bank line must match a
document. A real bug the tests caught: my first VAT parser stopped at the rate in
`ΦΠΑ 24%: 1.200,00` — the spec-driven test pinned the correct €1,200.

Course concepts, concretely:
- **Tools / function calling:** `record_document`, `reconcile_bank`, `validate_books`, `get_books`.
- **Multi-agent (`SequentialAgent`):** reconciler → validator → narrator, passing
  state forward via `output_key`.
- **Memory / state:** the agent's ledger accumulates documents across turns.
- **Evaluation / guardrails:** every entry must balance; the R1–R4 gates must hold.
- **Spec-driven:** one-paragraph contract per module; reproducible tests.

## 4. Demo  *(rubric: communication)*

The public notebook ingests a mixed month and prints the books:

```
Revenue €5,000 · Opex €1,000 · Payroll expense €28,249 · Net profit €-24,249
Cash: in €6,200 · out €15,590 · net €-9,390 · AR €0 · AP €0
note: Payroll expense €28,249, but only €14,350 left the bank this month;
      €13,899 of EFKA+tax is still payable.
```
Every journal entry balances; all three bank lines reconcile. Video: `[[ USER: YouTube URL ]]`.

## 5. Architecture  *(rubric: solution design · application of course concepts)*

```
owner ─▶ Archon ADK agent (Gemini) ─▶ record_document · reconcile_bank · validate_books · get_books
                                            │
   SequentialAgent analysis pipeline:  reconciler ─▶ validator ─▶ narrator   (output_key state)
                                            │
                              ledger.py (deterministic double-entry) + validation.py (R1–R4 gate)
                                            │
                              Firestore (ledger) · GCS (documents)   [local fallback]
```

**GCP-native:** Gemini (AI Studio / Vertex), **Google ADK**, Firestore + GCS, Cloud
Run as the deploy target. Archon is a product family — this is the **GCP** member
(it also runs on Nebius and Azure with the same application logic, platform-native
infra each time). Swap `ledger.py` to localise the chart of accounts / tax rules.

## 6. Code & reproducibility  *(rubric: communication · real-world value)*

- Public repo (MIT): `https://github.com/upgradedev/archon-gcp` — `python -m archon.cli` runs the books;
  `pytest` → **43 offline tests** across a unit → integration → e2e pyramid (the
  ADK agent and `SequentialAgent` run offline via scripted fake models — no key).
- Public notebook: `https://www.kaggle.com/code/efthimiosfousekis/archon-autonomous-bookkeeper-gcp`
  is self-contained and runs top-to-bottom with **zero setup** (including a live,
  offline `SequentialAgent` demo); the conversational agent cell runs with a
  `GOOGLE_API_KEY` secret.
- Evidence CI: `https://github.com/upgradedev/archon-gcp/actions/workflows/ci.yml`
  runs the test pyramid, **executes the notebook top-to-bottom**, runs the demo,
  and enforces **security gates** — gitleaks (secret scan), CodeQL (Python SAST),
  and pip-audit (dependency CVEs).

## 7. Honest lessons

- **Don't market past the accounting.** An earlier version leaned on a snappy
  "28% gap"; it was *wrong* (it implied employer cost < gross). Real Greek payroll:
  gross €23,100 → net €14,350, **true employer cost €28,249**. The honest story —
  expense vs cash-timing — is both correct and more useful.
- **Let the LLM orchestrate, keep the math deterministic.** Tests on the ledger,
  not the prose, are what make the books trustworthy.
- **One vivid thread beats a platform** for a 3-minute demo: a single mixed month
  shows classification, double-entry, reconciliation, and the cash insight at once.

---
*Archon · MIT · Gemini + Google ADK on GCP · built for the course.*

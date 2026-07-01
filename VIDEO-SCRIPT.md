# Archon (GCP) — ≤3-minute capstone video script

**Target: 2:40.** Public/unlisted YouTube. One screen recording of the notebook +
a couple of talking-head or voiceover beats. Keep it plain and honest — no hype.
Tagline: **"The new era of financial intelligence."**

| # | Time | On screen | Narration (spoken) |
|---|---|---|---|
| 1 | 0:00–0:25 | A bank statement export next to a stack of invoices, orders, receipts, and a payslip. | "Every small-business owner reads the bank statement and assumes that's their financial picture. It isn't. The real picture only appears when you bring every document together and *cross-check* them against each other. That's Archon: a unified financial intelligence platform." |
| 2 | 0:25–0:50 | Title: **Archon — unified financial intelligence**. Architecture diagram (owner → ADK/Gemini agent → tools → ledger → Firestore/GCS). | "Archon is built to ingest everything a business generates — sales and purchase invoices, orders, receipts, payments, bank transfers, payroll, expenses — into one environment, and turn it into a consolidated, period-over-period view: P&L, EBITDA, cash, and the true cost of your team. It's a Gemini agent, on Google's ADK, running on GCP." |
| 3 | 0:50–1:25 | Run the notebook top cell, then the demo cell. Highlight the classified docs and the **balanced** journal lines. | "Here it goes through one month. You hand it the documents the business actually received; it classifies each one and posts a balanced double-entry journal entry. The LLM orchestrates, but the bookkeeping math is deterministic, so the numbers are auditable." |
| 4 | 1:25–1:55 | Zoom the **reconciliation** lines ticking green; call out that an unmatched bank line is flagged "no matching document". | "Then the part a dashboard never does: it cross-checks the whole picture for what's *missing or inconsistent*. Every bank line is reconciled to the document that justifies it — and a payment with no matching invoice gets flagged. Did the vendor never send it, did the bookkeeper never register it, or is the payment wrong? That completeness check is the heart of the product." |
| 5 | 1:55–2:15 | Zoom the R1–R4 eval gate, then the P&L + cash output and the payroll note. | "It also runs an evaluation gate — four cross-document consistency and reconciliation rules. And here's one insight among many: workforce cost is €28,249 — the true cost of employing the team — but only €14,350 left the bank this month. The other €13,899, employer social-security contributions and withheld tax, is a payable that settles later. Profit and cash are different stories, and Archon keeps both straight." |
| 6 | 2:15–2:45 | **★ THE AGENT, RUNNING LIVE.** With a real `GOOGLE_API_KEY` set, run the agent cell so it genuinely executes. Show: (a) documents fed in across **separate turns**; (b) the **tool-call trace** — `record_document`, `reconcile_bank`, `validate_books`, `get_books` firing; (c) the final Gemini reply. | "This is the agent itself — Google ADK on Gemini. I drop documents in across turns; it *remembers* them in session, and it decides which tools to call. Then I just ask, in plain language, and it answers from the books it kept. Tools, session memory, multi-agent orchestration, and an eval gate — the course concepts, doing a real job." |
| 7 | 2:45–2:55 | Repo + notebook links; "MIT · also runs on Nebius & Azure." | "Open source, runs in one notebook with zero setup. Thanks for watching." |

## Production checklist
- [ ] 1920×1080, run the **public notebook** live (most credible).
- [ ] **★ Set a real `GOOGLE_API_KEY` and run the agent cell LIVE in section 6** — this is the *agent requirement* evidence. The published notebook ships deterministic (internet off), so the video is where the live ADK+Gemini agent is shown actually executing. Show the tool-call trace and the across-turn memory, not just a final answer.
- [ ] First 25 seconds must land the broad story — one consolidated picture + completeness checks (judges decide fast).
- [ ] Say "consolidate," "cross-check / reconcile," "completeness," "session memory," "tool calls" — show you mean both bookkeeping AND agents.
- [ ] Keep the workforce-cost figure as *one example*, not the headline.
- [ ] Keep under 3:00. Public/unlisted YouTube; paste URL into the Writeup §4 + §6.
- [ ] Blur/clear the `GOOGLE_API_KEY` field before recording — never show the key value on screen.

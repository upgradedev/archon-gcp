# Archon (GCP) — ≤3-minute capstone video script

**Target: 2:40.** Public/unlisted YouTube. One screen recording of the notebook +
a couple of talking-head or voiceover beats. Keep it plain and honest — no hype.

| # | Time | On screen | Narration (spoken) |
|---|---|---|---|
| 1 | 0:00–0:25 | A bank statement export next to a stack of invoices + a payslip. | "Every small-business owner I know reads the bank statement and thinks that's their financial picture. It isn't. Your books only exist once you *correlate* these documents — and one of them, payroll, costs far more than what leaves your account." |
| 2 | 0:25–0:50 | Title: **Archon — the autonomous bookkeeper**. Architecture diagram (owner → ADK/Gemini agent → tools → ledger → Firestore/GCS). | "So I built Archon: a Gemini agent, on Google's ADK, running on GCP. You hand it the documents you actually receive; it classifies them, posts real double-entry journal entries, reconciles the bank, and gives you a P&L and a cash view." |
| 3 | 0:50–1:35 | Run the notebook top cell, then the demo cell. Highlight the classified docs and the **balanced** journal lines, then the reconciliation lines ticking green. | "Here it goes through one month — a sale, a purchase, three bank lines, and a payroll run. Each document becomes a balanced journal entry — the LLM orchestrates, but the bookkeeping math is deterministic, so the numbers are auditable. And every bank line reconciles to the invoice or payroll it settles." |
| 4 | 1:35–2:15 | Zoom the P&L + cash output and the payroll note. | "And here's the insight a dashboard never gives you. Payroll *expense* is €28,249 — the true employer cost. But only €14,350 left the bank this month, to the employees. The other €13,899 — EFKA and withheld tax — is a payable that settles later. Profit and cash are different stories, and Archon keeps both straight." |
| 5 | 2:15–2:35 | The agent cell: feed documents in chat, ask "what did payroll really cost vs what left the account?", show the reply. | "The same engine, as a conversation: drop documents in across turns — it remembers — and just ask. That's tools, memory, and an evaluation guardrail from the course, doing a real job." |
| 6 | 2:35–2:40 | Repo + notebook links; "MIT · also runs on Nebius & Azure." | "Open source, runs in one notebook with zero setup. Thanks for watching." |

## Production checklist
- [ ] 1920×1080, run the **public notebook** live (most credible).
- [ ] First 25 seconds must land the problem (judges decide fast).
- [ ] Say "double-entry," "reconcile," "EFKA/tax payable" — show you mean bookkeeping.
- [ ] Keep under 3:00. Public/unlisted YouTube; paste URL into the Writeup §4 + §6.
- [ ] No real API keys or company data on screen.

# Archon (GCP) — ≤3-minute capstone video script

**Target: 2:40.** Public/unlisted YouTube. One screen recording of the notebook +
a couple of talking-head or voiceover beats. Keep it plain and honest — no hype.

| # | Time | On screen | Narration (spoken) |
|---|---|---|---|
| 1 | 0:00–0:25 | A bank statement export next to a stack of invoices + a payslip. | "Every small-business owner I know reads the bank statement and thinks that's their financial picture. It isn't. Your books only exist once you *correlate* these documents — and one of them, payroll, costs far more than what leaves your account." |
| 2 | 0:25–0:50 | Title: **Archon — the autonomous bookkeeper**. Architecture diagram (owner → ADK/Gemini agent → tools → ledger → Firestore/GCS). | "So I built Archon: a Gemini agent, on Google's ADK, running on GCP. You hand it the documents you actually receive; it classifies them, posts real double-entry journal entries, reconciles the bank, and gives you a P&L and a cash view." |
| 3 | 0:50–1:35 | Run the notebook top cell, then the demo cell. Highlight the classified docs and the **balanced** journal lines, then the reconciliation lines ticking green. | "Here it goes through one month — a sale, a purchase, three bank lines, and a payroll run. Each document becomes a balanced journal entry — the LLM orchestrates, but the bookkeeping math is deterministic, so the numbers are auditable. And every bank line reconciles to the invoice or payroll it settles." |
| 4 | 1:35–2:05 | Zoom the P&L + cash output and the payroll note. | "And here's the insight a dashboard never gives you. Payroll *expense* is €28,249 — the true employer cost. But only €14,350 left the bank this month, to the employees. The other €13,899 — EFKA and withheld tax — is a payable that settles later. Profit and cash are different stories, and Archon keeps both straight." |
| 5 | 2:05–2:45 | **★ THE AGENT, RUNNING LIVE.** With a real `GOOGLE_API_KEY` set, run the agent cell so it genuinely executes (not the skip message). Show: (a) documents fed in across **separate turns**; (b) the **tool-call trace** — `record_document`, `reconcile_bank`, `get_books` firing; (c) the final Gemini reply answering "what did payroll really cost vs what left the account?". | "This is the agent itself — Google ADK on Gemini. I drop documents in across turns; it *remembers* them in session, and it decides which tools to call — record, reconcile, get-books. Then I just ask, in plain language, and it answers from the books it kept. Three tools, session memory, and a balance-guardrail — the course concepts, doing a real job." |
| 6 | 2:45–2:55 | Repo + notebook links; "MIT · also runs on Nebius & Azure." | "Open source, runs in one notebook with zero setup. Thanks for watching." |

## Production checklist
- [ ] 1920×1080, run the **public notebook** live (most credible).
- [ ] **★ Set a real `GOOGLE_API_KEY` and run the agent cell LIVE in section 5** — this is the *agent requirement* evidence. The published notebook ships deterministic (internet off), so the video is where the live ADK+Gemini agent is shown actually executing. Show the tool-call trace and the across-turn memory, not just a final answer.
- [ ] First 25 seconds must land the problem (judges decide fast).
- [ ] Say "double-entry," "reconcile," "EFKA/tax payable," "session memory," "tool calls" — show you mean both bookkeeping AND agents.
- [ ] Keep under 3:00. Public/unlisted YouTube; paste URL into the Writeup §4 + §6.
- [ ] Blur/clear the `GOOGLE_API_KEY` field before recording — never show the key value on screen.

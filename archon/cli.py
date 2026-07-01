"""Runnable demo for Archon (GCP).

    python -m archon.cli            # deterministic bookkeeping (no key) — always runs
    python -m archon.cli --agent    # conversational ADK + Gemini agent (needs GOOGLE_API_KEY)
"""
from __future__ import annotations

import argparse
import os
import sys

from .documents import GROUND_TRUTH, SAMPLE_DOCS
from .extract import extract_document
from .ledger import Ledger
from .narrator import narrate
from .store import get_store
from .validation import all_passed, validate


def _print_books(led: Ledger) -> None:
    s = led.statements()
    rec = led.reconcile()
    print("\n" + "=" * 66)
    print(f"  ARCHON — books for {led.company} · {s.period}")
    print("=" * 66)
    print("  Journal (double-entry):")
    for e in led.entries:
        mark = "balanced" if e.is_balanced else "UNBALANCED"
        print(f"    · {e.memo}  [{mark}]")
    print("-" * 66)
    print("  Reconciliation:")
    for m in rec:
        print(f"    {'✓' if m.matched else '✗'} {m.bank_ref}  €{m.amount:,.2f}  — {m.note}")
    print("-" * 66)
    print("  P&L:")
    print(f"    Revenue            €{s.revenue:>12,.2f}")
    print(f"    Operating expenses €{s.opex:>12,.2f}")
    print(f"    Payroll expense    €{s.payroll_expense:>12,.2f}")
    print(f"    Net profit         €{s.net_profit:>12,.2f}")
    print("  Cash:")
    print(f"    In                 €{s.cash_in:>12,.2f}")
    print(f"    Out                €{s.cash_out:>12,.2f}")
    print(f"    Net cash           €{s.net_cash:>12,.2f}")
    print(f"  AR €{s.accounts_receivable:,.2f}  ·  AP €{s.accounts_payable:,.2f}")
    for n in s.notes:
        print(f"  ⓘ {n}")
    print("-" * 66)
    print("  Validation (R1–R4 eval gate):")
    for r in validate(led):
        print(f"    {'✓' if r.passed else '✗'} {r.rule}  — {r.message}")
    print("-" * 66)
    print("  Executive summary:")
    print(f"    {narrate(s, validate(led))}")
    print("=" * 66 + "\n")


def run_deterministic() -> Ledger:
    store = get_store()
    led = Ledger(period=GROUND_TRUTH["period"], company="Reflective IKE")
    print(f"Store backend: {type(store).__name__}")
    print("Ingesting a mixed document set (sales, purchase, bank x3, payroll)...")
    for name, text in SAMPLE_DOCS.items():
        store.put_document(name, text)
        doc = extract_document(text, source_file=name, period=led.period)
        led.add(doc)
        print(f"  + classified {doc.doc_type.value:<17} from {name}")
    store.save_ledger(led)
    _print_books(led)

    s = led.statements()
    assert led.all_entries_balanced(), "a journal entry did not balance"
    assert s.net_profit == GROUND_TRUTH["net_profit"]
    assert s.net_cash == GROUND_TRUTH["net_cash"]
    assert s.payroll_expense > s.cash_out          # true cost exceeds month's cash out
    assert all(m.matched for m in led.reconcile())
    assert all_passed(validate(led)), "a validation gate failed"
    print("Self-check passed: every entry balances; R1–R4 gates hold; figures match ground truth.\n")
    return led


def run_agent() -> None:
    from .agent import ArchonAgent

    print("Conversational ADK + Gemini agent — feeding documents across turns\n")
    agent = ArchonAgent(period=GROUND_TRUTH["period"], company="Reflective IKE")
    docs = list(SAMPLE_DOCS.items())
    turns = [f"Please record this document:\n\n{t}" for _, t in docs]
    turns.append("Reconcile the bank lines and show me the P&L and our cash position. "
                 "What did payroll really cost vs what left the account?")
    for t in turns:
        print(f"\n[owner] {t.splitlines()[0]} ...")
        print(f"[archon] {agent.send(t)}")


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    p = argparse.ArgumentParser(description="Archon (GCP) bookkeeping agent demo")
    p.add_argument("--agent", action="store_true", help="use the ADK+Gemini agent (needs GOOGLE_API_KEY)")
    args = p.parse_args(argv)

    if args.agent and os.environ.get("GOOGLE_API_KEY"):
        run_agent()
    else:
        if args.agent:
            print("GOOGLE_API_KEY not set — running the deterministic pipeline instead.\n", file=sys.stderr)
        run_deterministic()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

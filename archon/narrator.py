"""Executive narration over the computed books.

Two layers, same facts:

* `narrate()` is deterministic — it turns the statements + validation gates into
  a short CFO-style paragraph with **zero** model calls, so the notebook and the
  tests always produce a summary offline.
* The ADK+Gemini agent (`agent.py`) and the analysis pipeline (`pipeline.py`)
  wrap the *same* numbers and let Gemini phrase them; the model never invents a
  figure, it only narrates what the deterministic engine computed.
"""
from __future__ import annotations

from .models import FinancialStatements, ValidationResult


def narrate(stmt: FinancialStatements, validation: list[ValidationResult] | None = None) -> str:
    """A concise, deterministic executive summary of one month's books."""
    verdict = "profit" if stmt.net_profit >= 0 else "loss"
    parts = [
        f"In {stmt.period} the business booked €{stmt.revenue:,.2f} of revenue against "
        f"€{stmt.opex + stmt.payroll_expense:,.2f} of operating and payroll expense, "
        f"a net {verdict} of €{abs(stmt.net_profit):,.2f}."
    ]

    if stmt.payroll_expense and stmt.payroll_expense > stmt.cash_out:
        held_back = round(stmt.payroll_expense - (stmt.cash_out - stmt.opex), 2)
        parts.append(
            f"Cash tells a different story: only €{stmt.cash_out:,.2f} actually left the "
            f"account, because EFKA and withheld tax are payables that settle later — the "
            f"P&L expense of €{stmt.payroll_expense:,.2f} runs ahead of the cash."
        )

    parts.append(
        f"The month closes with €{stmt.net_cash:,.2f} net cash movement, "
        f"AR €{stmt.accounts_receivable:,.2f} and AP €{stmt.accounts_payable:,.2f}."
    )

    if validation:
        passed = sum(1 for r in validation if r.passed)
        failed = [r for r in validation if not r.passed]
        if failed:
            parts.append(
                f"Validation: {passed}/{len(validation)} gates passed — review "
                + "; ".join(r.rule.split(':')[0] for r in failed) + "."
            )
        else:
            parts.append(
                f"All {len(validation)} cross-document validation gates passed, so the "
                f"books reconcile end to end."
            )

    return " ".join(parts)


def facts_sheet(stmt: FinancialStatements, validation: list[ValidationResult] | None = None) -> str:
    """A compact, model-friendly fact sheet the LLM narration layer reads from.

    Kept deterministic so the pipeline's Gemini turn only ever *phrases* figures
    it was handed — it can never invent one.
    """
    lines = [
        f"Period: {stmt.period}",
        f"Revenue: {stmt.revenue:.2f}",
        f"Operating expense: {stmt.opex:.2f}",
        f"Payroll expense (true employer cost): {stmt.payroll_expense:.2f}",
        f"Net profit: {stmt.net_profit:.2f}",
        f"Cash in: {stmt.cash_in:.2f}",
        f"Cash out: {stmt.cash_out:.2f}",
        f"Net cash: {stmt.net_cash:.2f}",
        f"Accounts receivable: {stmt.accounts_receivable:.2f}",
        f"Accounts payable: {stmt.accounts_payable:.2f}",
    ]
    for n in stmt.notes:
        lines.append(f"Note: {n}")
    if validation:
        for r in validation:
            lines.append(f"{'PASS' if r.passed else 'FAIL'} {r.rule} — {r.message}")
    return "\n".join(lines)

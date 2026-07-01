"""Cross-document consistency gates — the deterministic **eval gate**.

Booking numbers is not enough; the books are only trustworthy when the documents
*agree with each other*. Archon runs four rules (R1–R4) over the recorded month,
the same discipline the Archon family uses on Nebius and Azure, adapted to this
double-entry ledger:

  R1  the bank line that pays payroll ≈ the payroll run's net pay        (±2%)
  R2  employer cost / gross is a sane social-contribution ratio    (1.15–1.35)
  R3  the payroll payment lands on or before the period's last day
  R4  the payroll adds up: gross ≥ net + withheld tax (employee deductions ≥ 0)

R4 is deliberately *additive* to the double-entry balance check: a balanced
journal already forces employer_cost = gross + employer_efka, so R4 instead
guards the one identity balance does **not** guarantee — that the employee-side
deductions are non-negative and internally coherent.

Every rule degrades gracefully: if the documents a rule needs are absent it is
reported as passed-but-skipped, so a partial upload is never falsely failed.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime

from .ledger import _PAYROLL_KEYS
from .models import DocType, Document, ValidationResult

# Employer cost as a multiple of gross pay. Statutory employer social-security
# contributions are ~22%, so the ratio sits near 1.22; the band tolerates other
# jurisdictions/rounding.
_EMPLOYER_COST_BAND = (1.15, 1.35)
_BANK_TOLERANCE = 0.02  # ±2%


def _payroll(docs: list[Document]) -> Document | None:
    return next((d for d in docs if d.doc_type == DocType.PAYROLL), None)


def _payroll_bank_line(docs: list[Document]) -> Document | None:
    for d in docs:
        if d.doc_type == DocType.BANK_TRANSACTION and any(
            k in (d.reference or "") for k in _PAYROLL_KEYS
        ):
            return d
    return None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _skip(rule: str) -> ValidationResult:
    return ValidationResult(rule=rule, passed=True, severity="info",
                            message="Skipped — required documents absent.")


# ── R1 ──────────────────────────────────────────────────────────────────────
def r1_bank_matches_payroll_net(docs: list[Document]) -> ValidationResult:
    rule = "R1: bank payroll line ≈ payroll net pay (±2%)"
    payroll = _payroll(docs)
    bank = _payroll_bank_line(docs)
    if not payroll or not bank:
        return _skip(rule)
    net = payroll.net_pay_total or 0.0
    paid = bank.net_amount or 0.0
    if net == 0:
        return ValidationResult(rule, False, "error", "Payroll net pay is zero.")
    deviation = abs(paid - net) / net
    passed = deviation <= _BANK_TOLERANCE
    return ValidationResult(
        rule, passed, "info" if passed else "error",
        f"Bank paid €{paid:,.2f} vs payroll net €{net:,.2f} ({deviation * 100:.1f}% deviation)",
    )


# ── R2 ──────────────────────────────────────────────────────────────────────
def r2_employer_cost_ratio(docs: list[Document]) -> ValidationResult:
    lo, hi = _EMPLOYER_COST_BAND
    rule = f"R2: employer cost / gross in [{lo}, {hi}]"
    payroll = _payroll(docs)
    if not payroll or not payroll.gross_amount or not payroll.employer_cost_total:
        return _skip(rule)
    gross = payroll.gross_amount
    ratio = payroll.employer_cost_total / gross
    passed = lo <= ratio <= hi
    return ValidationResult(
        rule, passed, "info" if passed else "warning",
        f"employer_cost/gross = {ratio:.3f} (expected {lo}–{hi})",
    )


# ── R3 ──────────────────────────────────────────────────────────────────────
def r3_payment_within_period(docs: list[Document], period: str) -> ValidationResult:
    rule = "R3: payroll payment date ≤ period end"
    bank = _payroll_bank_line(docs)
    paid_on = _parse_date(bank.date if bank else None)
    if not bank or not paid_on or not period or len(period) < 7:
        return _skip(rule)
    try:
        year, month = int(period[:4]), int(period[5:7])
        last_day = date(year, month, monthrange(year, month)[1])
    except (ValueError, IndexError) as exc:
        return ValidationResult(rule, False, "warning", f"Bad period '{period}': {exc}")
    passed = paid_on <= last_day
    return ValidationResult(
        rule, passed, "info" if passed else "warning",
        f"Paid {paid_on.isoformat()} vs period end {last_day.isoformat()}",
    )


# ── R4 ──────────────────────────────────────────────────────────────────────
def r4_payroll_identity(docs: list[Document]) -> ValidationResult:
    rule = "R4: gross ≥ net + withheld tax (employee deductions ≥ 0)"
    payroll = _payroll(docs)
    if not payroll or not payroll.gross_amount:
        return _skip(rule)
    gross = payroll.gross_amount
    net = payroll.net_pay_total or 0.0
    tax = payroll.tax_withheld_total or 0.0
    employee_efka = round(gross - net - tax, 2)
    passed = employee_efka >= 0
    return ValidationResult(
        rule, passed, "info" if passed else "error",
        f"implied employee social-security deduction = €{employee_efka:,.2f} "
        f"(gross {gross:,.2f} − net {net:,.2f} − tax {tax:,.2f})",
    )


def validate(ledger) -> list[ValidationResult]:
    """Run every gate over a ledger's documents. Pure/deterministic — no LLM."""
    docs = ledger.documents
    return [
        r1_bank_matches_payroll_net(docs),
        r2_employer_cost_ratio(docs),
        r3_payment_within_period(docs, ledger.period),
        r4_payroll_identity(docs),
    ]


def all_passed(results: list[ValidationResult]) -> bool:
    return all(r.passed for r in results)


def summary(results: list[ValidationResult]) -> str:
    passed = sum(1 for r in results if r.passed)
    return f"{passed}/{len(results)} validation gates passed"

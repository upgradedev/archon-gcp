"""Unit tests for the R1–R4 cross-document eval gate."""
from archon.documents import SAMPLE_DOCS
from archon.extract import extract_document
from archon.ledger import Ledger
from archon.models import DocType, Document
from archon.validation import (
    all_passed,
    r1_bank_matches_payroll_net,
    r2_employer_cost_ratio,
    r3_payment_within_period,
    r4_payroll_identity,
    summary,
    validate,
)


def _full_ledger() -> Ledger:
    led = Ledger(period="2026-01", company="Meridian Trading Co")
    for name, text in SAMPLE_DOCS.items():
        led.add(extract_document(text, source_file=name, period="2026-01"))
    return led


# ── happy path: ground truth passes every gate ────────────────────────────────

def test_all_four_gates_pass_on_ground_truth():
    results = validate(_full_ledger())
    assert len(results) == 4
    assert all_passed(results), [r.message for r in results if not r.passed]
    assert summary(results) == "4/4 validation gates passed"


def test_r1_matches_bank_to_payroll_net():
    r = r1_bank_matches_payroll_net(_full_ledger().documents)
    assert r.passed and r.severity == "info"
    assert "14,350" in r.message


def test_r2_employer_cost_ratio_in_band():
    r = r2_employer_cost_ratio(_full_ledger().documents)
    assert r.passed
    assert "1.223" in r.message


def test_r3_payment_within_period():
    r = r3_payment_within_period(_full_ledger().documents, "2026-01")
    assert r.passed
    assert "2026-01-31" in r.message


def test_r4_payroll_identity_holds():
    r = r4_payroll_identity(_full_ledger().documents)
    assert r.passed
    assert "3,204" in r.message   # implied employee social-security deduction


# ── failure paths ──────────────────────────────────────────────────────────────

def _payroll(gross, net, tax, employer_cost) -> Document:
    return Document(doc_type=DocType.PAYROLL, period="2026-01", gross_amount=gross,
                    net_pay_total=net, tax_withheld_total=tax, employer_cost_total=employer_cost,
                    efka_total=employer_cost - gross)


def test_r1_fails_when_bank_underpays():
    docs = [
        _payroll(23100, 14350, 5546, 28249),
        Document(doc_type=DocType.BANK_TRANSACTION, period="2026-01",
                 net_amount=10000.0, reference="ΜΙΣΘΟΔΟΣΙΑ", direction="out", date="31/01/2026"),
    ]
    r = r1_bank_matches_payroll_net(docs)
    assert not r.passed and r.severity == "error"


def test_r2_flags_implausible_ratio():
    docs = [_payroll(10000, 6000, 2000, 20000)]   # ratio 2.0, outside band
    r = r2_employer_cost_ratio(docs)
    assert not r.passed and r.severity == "warning"


def test_r3_flags_late_payment():
    docs = [Document(doc_type=DocType.BANK_TRANSACTION, period="2026-01",
                     net_amount=14350.0, reference="ΜΙΣΘΟΔΟΣΙΑ", direction="out",
                     date="05/02/2026")]
    r = r3_payment_within_period(docs, "2026-01")
    assert not r.passed


def test_r4_fails_when_deductions_exceed_gross():
    docs = [_payroll(10000, 8000, 3000, 12000)]   # net+tax = 11000 > gross
    r = r4_payroll_identity(docs)
    assert not r.passed and r.severity == "error"


# ── graceful skips ─────────────────────────────────────────────────────────────

def test_gates_skip_cleanly_without_payroll():
    led = Ledger(period="2026-01")
    led.add(extract_document(SAMPLE_DOCS["sales_invoice_INV-2026-014.txt"]))
    results = validate(led)
    assert all_passed(results)                    # skipped == passed
    assert all("Skipped" in r.message for r in results)

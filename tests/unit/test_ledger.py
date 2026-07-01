"""Tests for the auditable bookkeeping core — extraction, double-entry posting,
reconciliation, and the rolled-up statements. No API key needed.
"""
from archon.documents import GROUND_TRUTH, SAMPLE_DOCS
from archon.extract import extract_document
from archon.ledger import Ledger
from archon.models import Account, DocType


def _ledger() -> Ledger:
    led = Ledger(period="2026-01", company="Meridian Trading Co")
    for name, text in SAMPLE_DOCS.items():
        led.add(extract_document(text, source_file=name, period="2026-01"))
    return led


# ── extraction / classification ───────────────────────────────────────────────

def test_classifies_all_doc_types():
    led = _ledger()
    types = {d.doc_type for d in led.documents}
    assert {DocType.SALES_INVOICE, DocType.PURCHASE_INVOICE,
            DocType.BANK_TRANSACTION, DocType.PAYROLL} <= types
    assert DocType.UNKNOWN not in types


def test_extracts_vat_despite_rate_on_line():
    inv = extract_document(SAMPLE_DOCS["sales_invoice_INV-2026-014.txt"])
    assert inv.net_amount == 5000.00
    assert inv.vat_amount == 1200.00       # 'ΦΠΑ 24%: 1.200,00' — rate skipped
    assert inv.gross_amount == 6200.00


def test_extracts_payroll_figures():
    pr = extract_document(SAMPLE_DOCS["payroll_2026-01.txt"])
    assert pr.gross_amount == 23100.00
    assert pr.net_pay_total == 14350.00
    assert pr.employer_cost_total == 28249.00
    assert pr.employee_count == 2


# ── double-entry integrity ─────────────────────────────────────────────────────

def test_every_journal_entry_balances():
    led = _ledger()
    assert led.all_entries_balanced(), [e.memo for e in led.entries if not e.is_balanced]


def test_payroll_entry_splits_into_payables():
    led = _ledger()
    pr = next(e for e in led.entries
              if any(ln.account == Account.PAYROLL_EXPENSE for ln in e.lines))
    by_acct = {ln.account: (ln.debit, ln.credit) for ln in pr.lines}
    assert by_acct[Account.PAYROLL_EXPENSE][0] == 28249.00          # Dr true cost
    assert by_acct[Account.NET_PAY_PAYABLE][1] == 14350.00          # Cr net to employees
    assert by_acct[Account.EFKA_PAYABLE][1] == 8353.00              # employer 5,149 + employee 3,204
    assert by_acct[Account.TAX_WITHHELD_PAYABLE][1] == 5546.00


# ── statements ─────────────────────────────────────────────────────────────────

def test_pnl_matches_ground_truth():
    s = _ledger().statements()
    assert s.revenue == GROUND_TRUTH["revenue"]
    assert s.opex == GROUND_TRUTH["opex"]
    assert s.payroll_expense == GROUND_TRUTH["payroll_expense"]
    assert s.net_profit == GROUND_TRUTH["net_profit"]              # -24,249


def test_cash_view_separates_from_pnl():
    """The month's cash out (15,590) is far less than expense, because employer
    social-security contributions + tax are still payable — the honest cash-timing insight."""
    s = _ledger().statements()
    assert s.cash_in == GROUND_TRUTH["cash_in"]                    # 6,200
    assert s.cash_out == GROUND_TRUTH["cash_out"]                  # 15,590
    assert s.net_cash == GROUND_TRUTH["net_cash"]                  # -9,390
    # payroll expense (28,249) exceeds total cash out — money still owed for social-security/tax
    assert s.payroll_expense > s.cash_out


def test_receivables_and_payables_net_to_zero_after_settlement():
    s = _ledger().statements()
    assert s.accounts_receivable == 0.0    # invoice raised then paid
    assert s.accounts_payable == 0.0       # purchase booked then paid


def test_statement_note_explains_payroll_cash_gap():
    s = _ledger().statements()
    assert any("still payable" in n for n in s.notes)


# ── reconciliation ─────────────────────────────────────────────────────────────

def test_all_bank_lines_reconcile():
    matches = _ledger().reconcile()
    assert len(matches) == 3
    assert all(m.matched for m in matches), [m.note for m in matches if not m.matched]


def test_reconcile_flags_unmatched_bank_line():
    led = Ledger(period="2026-01")
    led.add(extract_document(
        "ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ (Bank Transaction)\nΚατεύθυνση: Εισερχόμενη (in)\n"
        "Ποσό: 999,00 EUR\nΑιτιολογία: MYSTERY-1", source_file="mystery.txt"))
    matches = led.reconcile()
    assert matches[0].matched is False
    assert "no matching document" in matches[0].note

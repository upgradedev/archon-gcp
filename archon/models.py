"""Archon (GCP) — domain models for a unified financial intelligence agent.

Archon ingests the heterogeneous documents a small business actually receives
— sales invoices, purchase invoices, bank transactions, payroll — classifies
them, posts double-entry journal entries, reconciles invoices against payments,
and rolls everything up into a consolidated P&L, a cash position, and AR/AP —
then cross-checks the whole picture for missing or inconsistent information.

Payroll is just one document family here (a single payroll run is itself told by
several documents and several journal lines — net pay to the employee, employer
social-security contributions to the fund, withheld tax to the authority).
Nothing here is a single "payroll" trick; it's ordinary bookkeeping across the
full financial picture, done by an agent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DocType(str, Enum):
    SALES_INVOICE = "sales_invoice"
    PURCHASE_INVOICE = "purchase_invoice"
    BANK_TRANSACTION = "bank_transaction"
    PAYROLL = "payroll"
    UNKNOWN = "unknown"


class Account(str, Enum):
    """A minimal chart of accounts (SMB flavour, jurisdiction-pluggable)."""
    REVENUE = "Revenue"
    COGS = "Cost of Goods / Services"
    OPEX = "Operating Expenses"
    PAYROLL_EXPENSE = "Payroll Expense"            # gross + employer contributions
    VAT_OUTPUT = "VAT Payable (output)"
    VAT_INPUT = "VAT Receivable (input)"
    ACCOUNTS_RECEIVABLE = "Accounts Receivable"
    ACCOUNTS_PAYABLE = "Accounts Payable"
    BANK = "Bank"
    NET_PAY_PAYABLE = "Net Pay Payable"
    EFKA_PAYABLE = "EFKA / Social Insurance Payable"
    TAX_WITHHELD_PAYABLE = "Withheld Tax Payable"


@dataclass
class Document:
    """A classified, structured business document."""
    doc_type: DocType
    period: str                      # YYYY-MM
    counterparty: str | None = None
    document_number: str | None = None
    date: str | None = None
    currency: str = "EUR"
    # amounts (meaning depends on doc_type)
    net_amount: float | None = None      # ex-VAT for invoices; transfer amount for bank
    vat_amount: float | None = None
    gross_amount: float | None = None    # incl. VAT (invoices) / gross pay (payroll)
    # bank-specific
    direction: str | None = None         # "in" | "out"
    reference: str | None = None         # what the bank line references (invoice no., "ΜΙΣΘΟΔΟΣΙΑ")
    # payroll-specific (one fused run)
    employer_cost_total: float | None = None
    net_pay_total: float | None = None
    efka_total: float | None = None
    tax_withheld_total: float | None = None
    employee_count: int | None = None
    source_file: str | None = None


@dataclass
class JournalLine:
    account: Account
    debit: float = 0.0
    credit: float = 0.0


@dataclass
class JournalEntry:
    """A balanced double-entry posting derived from one document."""
    date: str | None
    period: str
    memo: str
    lines: list[JournalLine] = field(default_factory=list)
    source_doc: str | None = None

    @property
    def is_balanced(self) -> bool:
        return abs(sum(l.debit for l in self.lines) - sum(l.credit for l in self.lines)) < 0.01


@dataclass
class ReconciliationMatch:
    bank_ref: str
    matched_document: str | None
    amount: float
    matched: bool
    note: str


@dataclass
class ValidationResult:
    """Outcome of one cross-document consistency gate (R1–R4).

    The validator is the deterministic **eval gate**: books are only trusted
    when every rule that applies passes. A skipped rule (required documents
    absent) is reported as passed so it never blocks a partial month.
    """
    rule: str
    passed: bool
    severity: str          # "info" | "warning" | "error"
    message: str


@dataclass
class FinancialStatements:
    period: str
    revenue: float
    cogs: float
    opex: float
    payroll_expense: float
    net_profit: float
    cash_in: float
    cash_out: float
    net_cash: float
    accounts_receivable: float
    accounts_payable: float
    bank_balance_movement: float
    gross_margin_pct: float | None
    notes: list[str] = field(default_factory=list)

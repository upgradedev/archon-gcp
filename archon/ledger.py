"""The bookkeeping core — deterministic double-entry posting, reconciliation,
and statement roll-up. The LLM never touches the math; it orchestrates this.

Every document becomes a balanced journal entry; bank lines are matched to the
invoice/payroll they settle; everything rolls up to a P&L, a cash view, and
AR/AP. Country-specific posting rules live here (this is the Greek/EFKA flavour;
swap this module to localise).
"""
from __future__ import annotations

from .models import (
    Account,
    DocType,
    Document,
    FinancialStatements,
    JournalEntry,
    JournalLine,
    ReconciliationMatch,
)

Dr = lambda a, x: JournalLine(a, debit=round(x, 2))   # noqa: E731
Cr = lambda a, x: JournalLine(a, credit=round(x, 2))   # noqa: E731

_PAYROLL_KEYS = ("ΜΙΣΘΟΔ", "μισθοδ", "payroll", "PAYROLL")


class Ledger:
    def __init__(self, period: str, company: str | None = None):
        self.period = period
        self.company = company
        self.documents: list[Document] = []
        self.entries: list[JournalEntry] = []

    # ── posting ───────────────────────────────────────────────────────────────

    def add(self, doc: Document) -> JournalEntry:
        self.documents.append(doc)
        entry = self._post(doc)
        self.entries.append(entry)
        return entry

    def _post(self, doc: Document) -> JournalEntry:
        e = JournalEntry(date=doc.date, period=doc.period, memo="", source_doc=doc.source_file)

        if doc.doc_type == DocType.SALES_INVOICE:
            net = doc.net_amount or 0.0
            vat = doc.vat_amount or 0.0
            gross = doc.gross_amount or (net + vat)
            e.memo = f"Sales invoice {doc.document_number} to {doc.counterparty}"
            e.lines = [Dr(Account.ACCOUNTS_RECEIVABLE, gross),
                       Cr(Account.REVENUE, net)]
            if vat:
                e.lines.append(Cr(Account.VAT_OUTPUT, vat))

        elif doc.doc_type == DocType.PURCHASE_INVOICE:
            net = doc.net_amount or 0.0
            vat = doc.vat_amount or 0.0
            gross = doc.gross_amount or (net + vat)
            e.memo = f"Purchase invoice {doc.document_number} from {doc.counterparty}"
            e.lines = [Dr(Account.OPEX, net)]
            if vat:
                e.lines.append(Dr(Account.VAT_INPUT, vat))
            e.lines.append(Cr(Account.ACCOUNTS_PAYABLE, gross))

        elif doc.doc_type == DocType.BANK_TRANSACTION:
            amt = doc.net_amount or 0.0
            ref = doc.reference or ""
            if doc.direction == "in":
                e.memo = f"Receipt {ref}"
                e.lines = [Dr(Account.BANK, amt), Cr(Account.ACCOUNTS_RECEIVABLE, amt)]
            elif any(k in ref for k in _PAYROLL_KEYS):
                e.memo = f"Payroll net paid ({ref})"
                e.lines = [Dr(Account.NET_PAY_PAYABLE, amt), Cr(Account.BANK, amt)]
            else:
                e.memo = f"Payment {ref}"
                e.lines = [Dr(Account.ACCOUNTS_PAYABLE, amt), Cr(Account.BANK, amt)]

        elif doc.doc_type == DocType.PAYROLL:
            gross = doc.gross_amount or 0.0
            net = doc.net_pay_total or 0.0
            employer_efka = doc.efka_total or 0.0
            tax = doc.tax_withheld_total or 0.0
            employer_cost = doc.employer_cost_total or (gross + employer_efka)
            employee_efka = round(gross - net - tax, 2)        # implied employee deduction
            efka_payable = round(employer_efka + employee_efka, 2)
            e.memo = f"Payroll {doc.period} ({doc.employee_count} employees)"
            e.lines = [
                Dr(Account.PAYROLL_EXPENSE, employer_cost),
                Cr(Account.NET_PAY_PAYABLE, net),
                Cr(Account.EFKA_PAYABLE, efka_payable),
                Cr(Account.TAX_WITHHELD_PAYABLE, tax),
            ]
        else:
            e.memo = f"Unclassified document {doc.source_file}"
        return e

    # ── reconciliation ────────────────────────────────────────────────────────

    def reconcile(self) -> list[ReconciliationMatch]:
        matches: list[ReconciliationMatch] = []
        by_number = {d.document_number: d for d in self.documents if d.document_number}
        for d in self.documents:
            if d.doc_type != DocType.BANK_TRANSACTION:
                continue
            ref = d.reference or ""
            amt = d.net_amount or 0.0
            if any(k in ref for k in _PAYROLL_KEYS):
                payroll = next((x for x in self.documents if x.doc_type == DocType.PAYROLL), None)
                ok = payroll is not None and abs((payroll.net_pay_total or 0) - amt) < 0.01
                matches.append(ReconciliationMatch(ref, "payroll", amt, ok,
                               "matched payroll net" if ok else "no matching payroll net"))
            elif ref in by_number:
                inv = by_number[ref]
                ok = abs((inv.gross_amount or 0) - amt) < 0.01
                matches.append(ReconciliationMatch(ref, ref, amt, ok,
                               "matched invoice" if ok else "amount mismatch vs invoice"))
            else:
                matches.append(ReconciliationMatch(ref, None, amt, False, "no matching document"))
        return matches

    # ── statements ────────────────────────────────────────────────────────────

    def _bal(self) -> dict[Account, tuple[float, float]]:
        b: dict[Account, list[float]] = {}
        for e in self.entries:
            for ln in e.lines:
                d, c = b.setdefault(ln.account, [0.0, 0.0])
                b[ln.account] = [round(d + ln.debit, 2), round(c + ln.credit, 2)]
        return {k: (v[0], v[1]) for k, v in b.items()}

    def statements(self) -> FinancialStatements:
        b = self._bal()

        def dr(a):  # debit-minus-credit
            d, c = b.get(a, (0.0, 0.0))
            return round(d - c, 2)

        def cr(a):  # credit-minus-debit
            d, c = b.get(a, (0.0, 0.0))
            return round(c - d, 2)

        revenue = cr(Account.REVENUE)
        cogs = dr(Account.COGS)
        opex = dr(Account.OPEX)
        payroll = dr(Account.PAYROLL_EXPENSE)
        net_profit = round(revenue - cogs - opex - payroll, 2)

        cash_in, cash_out = b.get(Account.BANK, (0.0, 0.0))
        notes = []
        net_pay_payable = cr(Account.NET_PAY_PAYABLE)
        efka_payable = cr(Account.EFKA_PAYABLE)
        tax_payable = cr(Account.TAX_WITHHELD_PAYABLE)
        outstanding = round(net_pay_payable + efka_payable + tax_payable, 2)
        if payroll:
            notes.append(
                f"Payroll expense €{payroll:,.2f}, but only the net left the bank so far; "
                f"€{round(efka_payable + tax_payable, 2):,.2f} of EFKA+tax is still payable."
            )

        return FinancialStatements(
            period=self.period,
            revenue=revenue, cogs=cogs, opex=opex, payroll_expense=payroll,
            net_profit=net_profit,
            cash_in=round(cash_in, 2), cash_out=round(cash_out, 2),
            net_cash=round(cash_in - cash_out, 2),
            accounts_receivable=dr(Account.ACCOUNTS_RECEIVABLE),
            accounts_payable=cr(Account.ACCOUNTS_PAYABLE),
            bank_balance_movement=round(cash_in - cash_out, 2),
            gross_margin_pct=round((revenue - cogs) / revenue * 100, 1) if revenue else None,
            notes=notes,
        )

    def all_entries_balanced(self) -> bool:
        return all(e.is_balanced for e in self.entries)

"""Classify + extract a business document into structured fields.

In production this tool sends a scanned PDF to **Gemini** (vision) on GCP; here
it parses OCR-style text blobs deterministically so the notebook runs with no
key. Greek diacritics are folded so unaccented patterns match accented text.
"""
from __future__ import annotations

import re
import unicodedata

from .models import DocType, Document

_AMOUNT = r"([\d\.]+,\d{2})"


def _fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _eur(text: str, label: str) -> float | None:
    # Non-greedy, same-line gap so a rate between label and amount
    # ("ΦΠΑ 24%: 1.200,00") is skipped to the first properly-formatted amount.
    m = re.search(r"(?:" + label + r")[^\n]*?" + _AMOUNT, _fold(text), re.IGNORECASE)
    if not m:
        return None
    return round(float(m.group(1).replace(".", "").replace(",", ".")), 2)


def _int(text: str, label: str) -> int | None:
    m = re.search(r"(?:" + label + r")[^\d]*(\d+)", _fold(text), re.IGNORECASE)
    return int(m.group(1)) if m else None


def _str(text: str, label: str) -> str | None:
    m = re.search(r"(?:" + label + r")\s*:?\s*(.+)", text, re.IGNORECASE)
    return m.group(1).strip() if m and m.group(1) else None


def classify(text: str) -> DocType:
    t = _fold(text).lower()
    if "τιμολογιο πωλησης" in t or "sales invoice" in t:
        return DocType.SALES_INVOICE
    if "τιμολογιο αγορας" in t or "purchase invoice" in t:
        return DocType.PURCHASE_INVOICE
    if "κινηση λογαριασμου" in t or "bank transaction" in t:
        return DocType.BANK_TRANSACTION
    if "μισθοδοσια" in t or "payroll" in t:
        return DocType.PAYROLL
    return DocType.UNKNOWN


def extract_document(text: str, source_file: str = "doc.txt", period: str = "2026-01") -> Document:
    dtype = classify(text)
    doc = Document(doc_type=dtype, period=period, source_file=source_file,
                   document_number=_str(text, r"Αριθμ\w+"), date=_str(text, r"Ημερομην\w+"))

    if dtype in (DocType.SALES_INVOICE, DocType.PURCHASE_INVOICE):
        doc.counterparty = _str(text, r"Πελ\w+") or _str(text, r"Προμηθευτ\w+")
        doc.net_amount = _eur(text, r"καθαρη αξια|net")
        doc.vat_amount = _eur(text, r"φπα")
        doc.gross_amount = _eur(text, r"συνολο|total")
    elif dtype == DocType.BANK_TRANSACTION:
        tf = _fold(text).lower()
        doc.direction = "in" if ("εισερχ" in tf or "(in)" in tf) else "out"
        doc.net_amount = _eur(text, r"ποσο|amount")
        doc.reference = _str(text, r"Αιτιολογ\w+|reference")
        doc.date = _str(text, r"Ημερομην\w+")
    elif dtype == DocType.PAYROLL:
        doc.gross_amount = _eur(text, r"μικτ\w+ αποδοχ\w+|gross")
        doc.net_pay_total = _eur(text, r"καθαρ\w+ πληρωτ\w+|net")
        doc.efka_total = _eur(text, r"εργοδοτικ\w+ εισφορ\w+|employer.*efka")
        doc.tax_withheld_total = _eur(text, r"παρακρατουμεν\w+ φορ\w+|fmy|withheld")
        doc.employer_cost_total = _eur(text, r"συνολικ\w+ εργοδοτικ\w+ κοστος|employer cost")
        doc.employee_count = _int(text, r"εργαζομεν\w+|employees")
    return doc

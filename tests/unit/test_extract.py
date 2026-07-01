"""Unit tests for classification + field extraction edge cases."""
from archon.extract import classify, extract_document
from archon.models import DocType


def test_classify_folds_diacritic_accents():
    assert classify("ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ") == DocType.SALES_INVOICE
    assert classify("τιμολογιο αγορας") == DocType.PURCHASE_INVOICE
    assert classify("ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ") == DocType.BANK_TRANSACTION
    assert classify("ΜΙΣΘΟΔΟΣΙΑ") == DocType.PAYROLL
    assert classify("random noise") == DocType.UNKNOWN


def test_english_labels_classify_too():
    assert classify("Sales Invoice\nTotal: 1,00 EUR") == DocType.SALES_INVOICE
    assert classify("Bank Transaction") == DocType.BANK_TRANSACTION


def test_bank_direction_in_vs_out():
    inn = extract_document("ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ\nΚατεύθυνση: Εισερχόμενη (in)\n"
                           "Ποσό: 100,00 EUR\nΑιτιολογία: X-1")
    out = extract_document("ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ\nΚατεύθυνση: Εξερχόμενη (out)\n"
                           "Ποσό: 200,00 EUR\nΑιτιολογία: Y-2")
    assert inn.direction == "in" and inn.net_amount == 100.00
    assert out.direction == "out" and out.net_amount == 200.00


def test_vat_rate_on_line_is_not_mistaken_for_amount():
    inv = extract_document("ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ\nΚαθαρή αξία: 5.000,00 EUR\n"
                           "ΦΠΑ 24%: 1.200,00 EUR\nΣύνολο: 6.200,00 EUR")
    assert inv.vat_amount == 1200.00      # 24 (the rate) must be skipped


def test_unknown_document_extracts_without_crashing():
    doc = extract_document("hello world, not a document")
    assert doc.doc_type == DocType.UNKNOWN
    assert doc.net_amount is None

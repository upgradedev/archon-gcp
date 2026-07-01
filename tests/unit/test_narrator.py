"""Unit tests for the deterministic narrator + fact sheet."""
from archon.documents import SAMPLE_DOCS
from archon.extract import extract_document
from archon.ledger import Ledger
from archon.narrator import facts_sheet, narrate
from archon.validation import validate


def _ledger() -> Ledger:
    led = Ledger(period="2026-01", company="Meridian Trading Co")
    for name, text in SAMPLE_DOCS.items():
        led.add(extract_document(text, source_file=name, period="2026-01"))
    return led


def test_narrate_reports_net_loss_and_cash_timing():
    led = _ledger()
    text = narrate(led.statements(), validate(led))
    assert "net loss of €24,249.00" in text
    assert "settle later" in text                  # the social-security/tax cash-timing insight
    assert "gates passed" in text


def test_narrate_flags_failed_gates():
    led = _ledger()
    checks = validate(led)
    checks[0].passed = False                        # force an R1 failure
    text = narrate(led.statements(), checks)
    assert "review" in text and "R1" in text


def test_narrate_without_validation_still_summarises():
    led = _ledger()
    text = narrate(led.statements())
    assert "2026-01" in text and "revenue" in text


def test_facts_sheet_is_deterministic_and_complete():
    led = _ledger()
    sheet = facts_sheet(led.statements(), validate(led))
    for token in ("Revenue: 5000.00", "Payroll expense", "Net cash", "PASS R1"):
        assert token in sheet
    # a model reading this sheet can only phrase figures it was handed
    assert "28249.00" in sheet

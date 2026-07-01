"""Unit tests for the local store + ledger snapshot serialisation."""
from archon.documents import SAMPLE_DOCS
from archon.extract import extract_document
from archon.ledger import Ledger
from archon.store import LocalStore, get_store, ledger_snapshot


def _ledger() -> Ledger:
    led = Ledger(period="2026-01", company="Meridian Trading Co")
    for name, text in SAMPLE_DOCS.items():
        led.add(extract_document(text, source_file=name, period="2026-01"))
    return led


def test_get_store_defaults_to_local(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    assert isinstance(get_store(), LocalStore)


def test_local_store_roundtrips_ledger():
    store = LocalStore()
    led = _ledger()
    store.save_ledger(led)
    loaded = store.load_ledger("Meridian Trading Co", "2026-01")
    assert loaded is not None
    assert loaded["statements"]["net_profit"] == -24249.0
    assert len(loaded["documents"]) == len(SAMPLE_DOCS)


def test_put_document_returns_local_uri():
    store = LocalStore()
    uri = store.put_document("x.txt", "content")
    assert uri.startswith("local://documents/")


def test_ledger_snapshot_is_json_friendly():
    snap = ledger_snapshot(_ledger())
    assert snap["period"] == "2026-01"
    assert snap["reconciliation"] and snap["journal"]
    # every account/value in the journal is a plain string/number (Firestore-safe)
    for entry in snap["journal"]:
        for line in entry["lines"]:
            assert isinstance(line["account"], str)
            assert isinstance(line["debit"], (int, float))

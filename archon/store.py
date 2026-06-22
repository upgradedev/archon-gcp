"""Persistence — GCP-native (Firestore ledger + GCS documents) with a local
in-memory fallback so the demo/notebook runs with zero cloud setup.

Selection is by environment: set GOOGLE_CLOUD_PROJECT (and have
google-cloud-firestore installed) to use Firestore; otherwise LocalStore.
"""
from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any

from .ledger import Ledger
from .models import Document


def ledger_snapshot(ledger: Ledger) -> dict[str, Any]:
    """Serialise a ledger to a Firestore/JSON-friendly dict."""
    s = ledger.statements()
    return {
        "period": ledger.period,
        "company": ledger.company,
        "documents": [asdict(d) for d in ledger.documents],
        "journal": [
            {"memo": e.memo, "date": e.date, "balanced": e.is_balanced,
             "lines": [{"account": l.account.value, "debit": l.debit, "credit": l.credit}
                       for l in e.lines]}
            for e in ledger.entries
        ],
        "reconciliation": [asdict(m) for m in ledger.reconcile()],
        "statements": asdict(s),
    }


class LocalStore:
    """In-memory store (default). Mirrors the Firestore interface."""
    def __init__(self) -> None:
        self._docs: dict[str, str] = {}
        self._ledgers: dict[str, dict] = {}

    @staticmethod
    def _key(company: str | None, period: str) -> str:
        return f"{company or 'default'}::{period}"

    def put_document(self, name: str, content: str) -> str:
        self._docs[name] = content
        return f"local://documents/{name}"

    def save_ledger(self, ledger: Ledger) -> str:
        key = self._key(ledger.company, ledger.period)
        self._ledgers[key] = ledger_snapshot(ledger)
        return f"local://ledgers/{key}"

    def load_ledger(self, company: str | None, period: str) -> dict | None:
        return self._ledgers.get(self._key(company, period))


class FirestoreStore:
    """Firestore ledger + GCS raw documents. Same interface as LocalStore."""
    def __init__(self, project: str, bucket: str | None = None) -> None:
        from google.cloud import firestore  # imported lazily

        self._db = firestore.Client(project=project)
        self._project = project
        self._bucket_name = bucket or os.getenv("ARCHON_GCS_BUCKET")

    def _bucket(self):
        from google.cloud import storage
        return storage.Client(project=self._project).bucket(self._bucket_name)

    def put_document(self, name: str, content: str) -> str:
        if not self._bucket_name:
            return "gcs://(no bucket configured)"
        blob = self._bucket().blob(f"raw-docs/{name}")
        blob.upload_from_string(content)
        return f"gs://{self._bucket_name}/raw-docs/{name}"

    def save_ledger(self, ledger: Ledger) -> str:
        key = f"{ledger.company or 'default'}::{ledger.period}"
        self._db.collection("ledgers").document(key).set(ledger_snapshot(ledger))
        return f"firestore://ledgers/{key}"

    def load_ledger(self, company: str | None, period: str) -> dict | None:
        key = f"{company or 'default'}::{period}"
        snap = self._db.collection("ledgers").document(key).get()
        return snap.to_dict() if snap.exists else None


def get_store():
    """Firestore when GOOGLE_CLOUD_PROJECT is set and the lib is present; else Local."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if project:
        try:
            return FirestoreStore(project)
        except Exception:  # pragma: no cover - missing lib / creds → graceful fallback
            pass
    return LocalStore()

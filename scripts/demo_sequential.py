#!/usr/bin/env python3
"""Run the ADK `SequentialAgent` analysis pipeline **fully offline** and print the
reconciler -> validator -> narrator hand-off.

This is the honest, reproducible source for the demo video's "multi-agent" beat:
the *real* Google ADK `SequentialAgent` runs here with **scripted models** (no API
key, no network), exactly as the published notebook and the e2e tests do. The
deterministic engine (ledger + validation) computes every number first; the three
sub-agents only phrase the handed-in fact sheet, passing state forward via
`output_key`.

    python scripts/demo_sequential.py

Point the same pipeline at live Gemini by setting GOOGLE_API_KEY and calling
`archon.pipeline.run_analysis(ledger)` with no `models=` argument.
"""
from __future__ import annotations

import os
import sys

# Allow both `python scripts/demo_sequential.py` and repo-root execution.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_TESTS = os.path.join(_ROOT, "tests")
if _TESTS not in sys.path:
    sys.path.insert(0, _TESTS)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from adk_fakes import ScriptedText  # test double: a real BaseLlm subclass

    from archon.documents import SAMPLE_DOCS
    from archon.extract import extract_document
    from archon.ledger import Ledger
    from archon.pipeline import run_analysis

    led = Ledger(period="2026-01", company="Reflective IKE")
    for name, text in SAMPLE_DOCS.items():
        led.add(extract_document(text, source_file=name, period="2026-01"))

    # Scripted (offline) sub-agent models — the SequentialAgent orchestration is real.
    models = [
        ScriptedText("All 3 bank lines reconcile to their invoices and payroll."),
        ScriptedText("R1-R4 consistency gates all hold."),
        ScriptedText("Net loss of 24,249; payroll expense of 28,249 runs ahead of "
                     "the 15,590 cash out because EFKA and withheld tax settle later."),
    ]
    r = run_analysis(led, models=models)

    print("Google ADK SequentialAgent: archon_analysis   (offline, scripted models)")
    print("  reconciler -> validator -> narrator   (state via output_key)")
    print("-" * 66)
    print(f"  [reconciler] -> {r['reconciliation']}")
    print(f"  [validator ] -> {r['validation']}")
    print(f"  [narrator  ] -> {r['summary']}")
    print("-" * 66)
    print(f"  eval gate: {r['gates']}")
    print("  (same pipeline runs on live Gemini with GOOGLE_API_KEY and no models=)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""End-to-end: the deterministic pipeline (the always-runs, graded anchor)."""
from archon.cli import run_deterministic
from archon.documents import GROUND_TRUTH
from archon.validation import all_passed, validate


def test_full_deterministic_run_matches_ground_truth(capsys):
    led = run_deterministic()
    s = led.statements()
    assert s.net_profit == GROUND_TRUTH["net_profit"]
    assert s.net_cash == GROUND_TRUTH["net_cash"]
    assert led.all_entries_balanced()
    assert all(m.matched for m in led.reconcile())
    assert all_passed(validate(led))
    out = capsys.readouterr().out
    assert "Self-check passed" in out
    assert "Executive summary" in out
    assert "R1–R4 eval gate" in out

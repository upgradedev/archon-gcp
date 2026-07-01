"""Shared test configuration.

Puts the repo root and the tests dir on the path so `import archon` and
`import adk_fakes` work from any of the unit/integration/e2e subfolders.
"""
import sys
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
_ROOT = _TESTS.parent
for p in (_ROOT, _TESTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

"""Run backend tests without requiring an editable package installation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


def main() -> int:
    repository_root = Path(__file__).resolve().parents[1]
    source_directory = repository_root / "application" / "backend" / "src"
    test_directory = repository_root / "application" / "backend" / "tests"
    sys.path.insert(0, str(source_directory))

    suite = unittest.defaultTestLoader.discover(str(test_directory))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

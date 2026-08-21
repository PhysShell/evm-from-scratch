#!/usr/bin/env python3
"""Run the governor test suite offline (stdlib only, no network).

    python3 governor/run_tests.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
sys.path.insert(0, HERE)

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(
        start_dir=os.path.join(HERE, "tests"),
        pattern="test_*.py",
        top_level_dir=HERE,
    )
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

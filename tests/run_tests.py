"""
Non-interactive test runner - runs all sample tests automatically.
"""

import sys
import os

# Add parent directory to path to import core modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Use test configuration
sys.path.insert(0, os.path.dirname(__file__))
import config_test

from test_transformers import test_edi_parsing, print_results
from sample_test_data import (
    SAMPLE_PREPACK_JSON,
    SAMPLE_BULK_JSON,
    SAMPLE_MINIMAL_JSON,
    SAMPLE_INVALID_JSON
)


def run_all_tests():
    """Run all sample tests"""
    samples = [
        ("PREPACK Order", SAMPLE_PREPACK_JSON),
        ("BULK Order", SAMPLE_BULK_JSON),
        ("Minimal Order", SAMPLE_MINIMAL_JSON),
        ("Invalid Order", SAMPLE_INVALID_JSON)
    ]

    print("\n" + "="*80)
    print("RUNNING ALL SAMPLE TESTS")
    print("="*80)

    results_summary = []

    for name, json_data in samples:
        print("\n" + "="*80)
        print(f"TEST: {name}")
        print("="*80)

        try:
            results = test_edi_parsing(json_data)
            print_results(results)
            results_summary.append((name, results.get('success', False)))
        except Exception as e:
            print(f"\n[ERROR] UNEXPECTED ERROR: {str(e)}")
            results_summary.append((name, False))

        print("\n" + "-"*80)

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for name, success in results_summary:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status:8s} - {name}")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()

"""
Interactive test for a single JSON paste.
Prompts user to paste JSON, then shows the parsed results.
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


def main():
    print("="*80)
    print("EDI JSON PARSER - INTERACTIVE TEST")
    print("="*80)
    print("\nPaste your EDI JSON below.")
    print("When finished, type END on a new line and press Enter.\n")
    print("-"*80)

    # Read multi-line input until "END" is encountered
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break

    json_input = '\n'.join(lines)

    if not json_input.strip():
        print("\n[ERROR] No JSON provided.")
        return

    print("\n" + "="*80)
    print("PARSING JSON...")
    print("="*80)

    # Run test
    results = test_edi_parsing(json_input)
    print_results(results)

    # Offer to save results
    if results.get('success'):
        print("\n" + "="*80)
        try:
            save = input("\nSave results to file? (y/n): ").strip().lower()
        except EOFError:
            save = 'n'

        if save == 'y':
            import json
            from datetime import datetime

            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                # Convert datetime objects to strings for JSON serialization
                output = {
                    'success': results['success'],
                    'order_type': results['order_type'],
                    'customer_po': results['customer_po'],
                    'version': results['version'],
                    'header': {k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                              for k, v in results['header'].items()},
                    'details': [{k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                                for k, v in detail.items()}
                               for detail in results['details']],
                    'bom_components': [{k: str(v) if not isinstance(v, (str, int, float, bool, type(None))) else v
                                       for k, v in comp.items()}
                                      for comp in results['bom_components']],
                    'summary': results['summary']
                }
                json.dump(output, f, indent=2)
            print(f"\nResults saved to: {filename}")


if __name__ == "__main__":
    main()

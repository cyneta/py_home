#!/usr/bin/env python
"""
Test Sensibo component redesign (Phase 2)

Tests the new intent-based API:
- set_comfort_mode()
- set_away_mode()
- set_sleep_mode()
"""

import sys
import logging
sys.path.insert(0, '/c/git/cyneta/py_home')

from lib.logging_config import setup_logging
from components.sensibo import SensiboAPI

# Setup logging
setup_logging(log_level='DEBUG')
logger = logging.getLogger(__name__)

def test_sensibo_redesign():
    """Test new Sensibo API with dry_run"""
    print("\n=== Testing Sensibo Component Redesign (Phase 2) ===\n")

    # Create Sensibo instance with dry_run
    sensibo = SensiboAPI(dry_run=True)

    # Test 1: set_comfort_mode()
    print("Test 1: set_comfort_mode()")
    print("-" * 50)
    try:
        sensibo.set_comfort_mode()  # Should use config temp (70°F)
        print("✓ set_comfort_mode() - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_comfort_mode() - FAILED: {e}\n")

    # Test 2: set_comfort_mode() with custom temp
    print("Test 2: set_comfort_mode(72)")
    print("-" * 50)
    try:
        sensibo.set_comfort_mode(72)  # Override to 72°F
        print("✓ set_comfort_mode(72) - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_comfort_mode(72) - FAILED: {e}\n")

    # Test 3: set_away_mode()
    print("Test 3: set_away_mode()")
    print("-" * 50)
    try:
        sensibo.set_away_mode()  # Should turn off AC
        print("✓ set_away_mode() - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_away_mode() - FAILED: {e}\n")

    # Test 4: set_sleep_mode()
    print("Test 4: set_sleep_mode()")
    print("-" * 50)
    try:
        sensibo.set_sleep_mode()  # Should use config bedroom_sleep temp (66°F)
        print("✓ set_sleep_mode() - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_sleep_mode() - FAILED: {e}\n")

    # Test 5: set_sleep_mode() with custom temp
    print("Test 5: set_sleep_mode(68)")
    print("-" * 50)
    try:
        sensibo.set_sleep_mode(68)  # Override to 68°F
        print("✓ set_sleep_mode(68) - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_sleep_mode(68) - FAILED: {e}\n")

    print("=== All Tests Complete ===\n")

if __name__ == '__main__':
    test_sensibo_redesign()

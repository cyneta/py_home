#!/usr/bin/env python
"""
Test Nest component redesign (Phase 1)

Tests the new intent-based API:
- set_comfort_mode()
- set_away_mode()
- set_sleep_mode()
"""

import sys
import logging
sys.path.insert(0, '/c/git/cyneta/py_home')

from lib.logging_config import setup_logging
from components.nest import NestAPI

# Setup logging
setup_logging(log_level='DEBUG')
logger = logging.getLogger(__name__)

def test_nest_redesign():
    """Test new Nest API with dry_run"""
    print("\n=== Testing Nest Component Redesign (Phase 1) ===\n")

    # Create Nest instance with dry_run
    nest = NestAPI(dry_run=True)

    # Test 1: set_comfort_mode()
    print("Test 1: set_comfort_mode()")
    print("-" * 50)
    try:
        nest.set_comfort_mode()  # Should use config temp (70°F)
        print("✓ set_comfort_mode() - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_comfort_mode() - FAILED: {e}\n")

    # Test 2: set_comfort_mode() with custom temp
    print("Test 2: set_comfort_mode(72)")
    print("-" * 50)
    try:
        nest.set_comfort_mode(72)  # Override to 72°F
        print("✓ set_comfort_mode(72) - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_comfort_mode(72) - FAILED: {e}\n")

    # Test 3: set_away_mode()
    print("Test 3: set_away_mode()")
    print("-" * 50)
    try:
        nest.set_away_mode()  # Should use config ECO bounds
        print("✓ set_away_mode() - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_away_mode() - FAILED: {e}\n")

    # Test 4: set_sleep_mode()
    print("Test 4: set_sleep_mode()")
    print("-" * 50)
    try:
        nest.set_sleep_mode()  # Should call set_away_mode()
        print("✓ set_sleep_mode() - SUCCESS\n")
    except Exception as e:
        print(f"✗ set_sleep_mode() - FAILED: {e}\n")

    print("=== All Tests Complete ===\n")

if __name__ == '__main__':
    test_nest_redesign()

#!/usr/bin/env python
"""
Test Write Operations in Dry-Run Mode

Tests device control functions (turn_on, turn_off, set_temperature) using dry-run mode.
This allows us to verify control logic without actually changing device states.

Run with: python tests/test_write_operations.py
"""

import sys
import logging

# Configure logging to see dry-run messages
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_tapo_turn_on():
    """Test Tapo turn_on in dry-run mode"""
    print(f"\n{YELLOW}Testing Tapo turn_on (dry-run)...{RESET}")

    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=True)

        # Get first outlet from config
        first_outlet = tapo.outlets[0]
        outlet_name = first_outlet['name']

        # This should log but not execute
        tapo.turn_on(outlet_name)

        print(f"{GREEN}✓{RESET} Tapo turn_on dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Tapo turn_on dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tapo_turn_off():
    """Test Tapo turn_off in dry-run mode"""
    print(f"\n{YELLOW}Testing Tapo turn_off (dry-run)...{RESET}")

    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=True)

        # Get first outlet from config
        first_outlet = tapo.outlets[0]
        outlet_name = first_outlet['name']

        # This should log but not execute
        tapo.turn_off(outlet_name)

        print(f"{GREEN}✓{RESET} Tapo turn_off dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Tapo turn_off dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tapo_turn_on_all():
    """Test Tapo turn_on_all in dry-run mode"""
    print(f"\n{YELLOW}Testing Tapo turn_on_all (dry-run)...{RESET}")

    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI(dry_run=True)

        # This should log for each outlet but not execute
        tapo.turn_on_all()

        print(f"{GREEN}✓{RESET} Tapo turn_on_all dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Tapo turn_on_all dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nest_set_temperature():
    """Test Nest set_temperature in dry-run mode"""
    print(f"\n{YELLOW}Testing Nest set_temperature (dry-run)...{RESET}")

    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=True)

        # This should log command but not execute
        nest.set_temperature(72, mode='HEAT')

        print(f"{GREEN}✓{RESET} Nest set_temperature dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Nest set_temperature dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nest_set_temperature_cool():
    """Test Nest set_temperature in COOL mode"""
    print(f"\n{YELLOW}Testing Nest set_temperature COOL (dry-run)...{RESET}")

    try:
        from components.nest import NestAPI

        nest = NestAPI(dry_run=True)

        # This should log command for cooling
        nest.set_temperature(68, mode='COOL')

        print(f"{GREEN}✓{RESET} Nest set_temperature COOL dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Nest set_temperature COOL dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sensibo_turn_on():
    """Test Sensibo turn_on in dry-run mode"""
    print(f"\n{YELLOW}Testing Sensibo turn_on (dry-run)...{RESET}")

    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=True)

        # This should log but not execute
        sensibo.turn_on(mode='cool', temp_f=72)

        print(f"{GREEN}✓{RESET} Sensibo turn_on dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Sensibo turn_on dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sensibo_turn_off():
    """Test Sensibo turn_off in dry-run mode"""
    print(f"\n{YELLOW}Testing Sensibo turn_off (dry-run)...{RESET}")

    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=True)

        # This should log but not execute
        sensibo.turn_off()

        print(f"{GREEN}✓{RESET} Sensibo turn_off dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Sensibo turn_off dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sensibo_set_temperature():
    """Test Sensibo set_temperature in dry-run mode"""
    print(f"\n{YELLOW}Testing Sensibo set_temperature (dry-run)...{RESET}")

    try:
        from components.sensibo import SensiboAPI

        sensibo = SensiboAPI(dry_run=True)

        # This should log but not execute
        sensibo.set_temperature(70)

        print(f"{GREEN}✓{RESET} Sensibo set_temperature dry-run test passed")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Sensibo set_temperature dry-run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all write operation tests"""
    print(f"\n{BLUE}╔{'═'*68}╗{RESET}")
    print(f"{BLUE}║{' '*16}WRITE OPERATION TESTS (DRY-RUN){' '*18}║{RESET}")
    print(f"{BLUE}╚{'═'*68}╝{RESET}")

    print("\nThese tests verify control logic without changing device states.")
    print("All operations run in DRY-RUN mode.\n")

    results = []

    # Test Tapo
    print(f"\n{BLUE}{'='*70}")
    print("Tapo Smart Plugs")
    print(f"{'='*70}{RESET}")

    results.append(("Tapo turn_on", test_tapo_turn_on()))
    results.append(("Tapo turn_off", test_tapo_turn_off()))
    results.append(("Tapo turn_on_all", test_tapo_turn_on_all()))

    # Test Nest
    print(f"\n{BLUE}{'='*70}")
    print("Nest Thermostat")
    print(f"{'='*70}{RESET}")

    results.append(("Nest set_temperature HEAT", test_nest_set_temperature()))
    results.append(("Nest set_temperature COOL", test_nest_set_temperature_cool()))

    # Test Sensibo
    print(f"\n{BLUE}{'='*70}")
    print("Sensibo AC")
    print(f"{'='*70}{RESET}")

    results.append(("Sensibo turn_on", test_sensibo_turn_on()))
    results.append(("Sensibo turn_off", test_sensibo_turn_off()))
    results.append(("Sensibo set_temperature", test_sensibo_set_temperature()))

    # Summary
    print(f"\n{BLUE}{'='*70}")
    print("Test Summary")
    print(f"{'='*70}{RESET}\n")

    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"Total: {len(results)} tests")
    print(f"{GREEN}Passed: {len(passed)}{RESET}")
    print(f"{RED}Failed: {len(failed)}{RESET}")

    if failed:
        print(f"\n{RED}Failed Tests:{RESET}")
        for name, _ in failed:
            print(f"  • {name}")

    print(f"\n{BLUE}{'='*70}{RESET}\n")

    return len(failed) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

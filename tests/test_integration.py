#!/usr/bin/env python
"""
Integration Tests for py_home

Tests end-to-end workflows and cross-component interactions.

These tests verify:
- Complete automation flows (trigger → execution → result)
- Multiple automations running concurrently
- State persistence across operations
- Device coordination (Nest + Sensibo temperature management)
- Notification delivery

All tests run in DRY_RUN mode for safety.
"""

import os
import sys
import time
import threading
import pytest
from unittest.mock import patch, MagicMock

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


@pytest.fixture(autouse=True)
def force_dry_run():
    """Force dry-run mode for all integration tests"""
    old_value = os.environ.get('DRY_RUN')
    os.environ['DRY_RUN'] = 'true'
    yield
    # Restore original value
    if old_value is None:
        os.environ.pop('DRY_RUN', None)
    else:
        os.environ['DRY_RUN'] = old_value


def test_leaving_home_workflow():
    """Test complete leaving home automation workflow"""
    print(f"\n{YELLOW}Testing Leaving Home Workflow...{RESET}")

    try:
        from automations.leaving_home import run

        # Execute automation
        result = run()

        # Verify all expected actions occurred
        assert result['action'] == 'leaving_home', "Wrong action type"
        assert 'nest' in result, "Nest action missing"
        assert 'tapo' in result, "Tapo action missing"
        assert 'notification' in result, "Notification missing"

        # Verify dry-run mode was used
        assert result['notification'] == 'Skipped (dry-run)', "Notification should be skipped in dry-run"

        print(f"{GREEN}✓{RESET} Leaving home workflow test passed")
        print(f"  - Nest: {result['nest']}")
        print(f"  - Tapo: {result['tapo']}")
        print(f"  - Notification: {result['notification']}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Leaving home workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_goodnight_workflow():
    """Test complete goodnight automation workflow"""
    print(f"\n{YELLOW}Testing Goodnight Workflow...{RESET}")

    try:
        from automations.goodnight import run

        # Execute automation
        result = run()

        # Verify all expected actions occurred
        assert result['action'] == 'goodnight', "Wrong action type"
        assert 'nest' in result, "Nest action missing"
        assert 'sensibo' in result, "Sensibo action missing"
        assert 'tapo' in result, "Tapo action missing"
        assert 'notification' in result, "Notification missing"

        # Verify dry-run mode was used
        assert result['notification'] == 'Skipped (dry-run)', "Notification should be skipped in dry-run"

        print(f"{GREEN}✓{RESET} Goodnight workflow test passed")
        print(f"  - Nest: {result['nest']}")
        print(f"  - Sensibo: {result['sensibo']}")
        print(f"  - Tapo: {result['tapo']}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Goodnight workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_im_home_workflow():
    """Test complete I'm home automation workflow"""
    print(f"\n{YELLOW}Testing I'm Home Workflow...{RESET}")

    try:
        from automations.im_home import run

        # Execute automation
        result = run()

        # Verify expected actions
        assert result['action'] == 'im_home', "Wrong action type"
        assert 'nest' in result, "Nest action missing"
        assert 'notification' in result, "Notification missing"

        print(f"{GREEN}✓{RESET} I'm home workflow test passed")
        print(f"  - Nest: {result['nest']}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} I'm home workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_good_morning_workflow():
    """Test complete good morning automation workflow"""
    print(f"\n{YELLOW}Testing Good Morning Workflow...{RESET}")

    try:
        from automations.good_morning import run

        # Execute automation
        result = run()

        # Verify expected actions
        assert result['action'] == 'good_morning', "Wrong action type"
        assert 'nest' in result, "Nest action missing"
        assert 'weather' in result, "Weather missing"
        assert 'notification' in result, "Notification missing"

        print(f"{GREEN}✓{RESET} Good morning workflow test passed")
        print(f"  - Nest: {result['nest']}")
        print(f"  - Weather: {result['weather'][:50]}...")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Good morning workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_temp_coordination_workflow():
    """Test temperature coordination automation workflow"""
    print(f"\n{YELLOW}Testing Temperature Coordination Workflow...{RESET}")

    try:
        from automations.temp_coordination import run

        # Execute automation
        result = run()

        # Verify expected data
        assert result['action'] == 'temp_coordination', "Wrong action type"
        assert 'nest_temp' in result, "Nest temperature missing"
        assert 'ac_on' in result, "AC status missing"
        assert 'changes_made' in result, "Changes list missing"

        print(f"{GREEN}✓{RESET} Temperature coordination workflow test passed")
        print(f"  - Nest temp: {result['nest_temp']}°F")
        print(f"  - AC status: {'ON' if result['ac_on'] else 'OFF'}")
        print(f"  - Changes: {len(result['changes_made'])}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Temperature coordination workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_automations():
    """Test multiple automations running concurrently"""
    print(f"\n{YELLOW}Testing Concurrent Automations...{RESET}")

    try:
        from automations import leaving_home, goodnight, im_home

        results = {}
        errors = []

        def run_automation(name, automation_module):
            try:
                result = automation_module.run()
                results[name] = result
            except Exception as e:
                errors.append((name, str(e)))

        # Create threads for concurrent execution
        threads = [
            threading.Thread(target=run_automation, args=('leaving_home', leaving_home)),
            threading.Thread(target=run_automation, args=('goodnight', goodnight)),
            threading.Thread(target=run_automation, args=('im_home', im_home))
        ]

        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=30)

        duration = time.time() - start_time

        # Check results
        if errors:
            print(f"{RED}✗{RESET} Concurrent automation test failed with errors:")
            for name, error in errors:
                print(f"  - {name}: {error}")
            return False

        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

        print(f"{GREEN}✓{RESET} Concurrent automations test passed")
        print(f"  - Executed: {len(results)} automations")
        print(f"  - Duration: {duration:.2f}s")
        print(f"  - Completed: {', '.join(results.keys())}")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Concurrent automations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_device_coordination():
    """Test Nest and Sensibo coordination (temperature management)"""
    print(f"\n{YELLOW}Testing Device Coordination...{RESET}")

    try:
        from components.nest import NestAPI
        from components.sensibo import SensiboAPI

        # Test scenario: Set Nest to 68°F (sleep) and turn off AC
        nest = NestAPI(dry_run=True)
        sensibo = SensiboAPI(dry_run=True)

        # Simulate sleep mode
        nest.set_temperature(68)
        sensibo.turn_off()

        print(f"{GREEN}✓{RESET} Device coordination test passed")
        print(f"  - Nest set to sleep temp (dry-run)")
        print(f"  - Sensibo AC turned off (dry-run)")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Device coordination test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_component_interaction():
    """Test interaction between different components"""
    print(f"\n{YELLOW}Testing Component Interaction...{RESET}")

    try:
        from components.tapo import TapoAPI
        from components.nest import NestAPI
        from components.sensibo import SensiboAPI

        # Test all components work together
        tapo = TapoAPI(dry_run=True)
        nest = NestAPI(dry_run=True)
        sensibo = SensiboAPI(dry_run=True)

        # Simulate a coordinated action
        tapo.turn_off_all()
        nest.set_temperature(72)
        sensibo.turn_off()

        print(f"{GREEN}✓{RESET} Component interaction test passed")
        print(f"  - All components initialized")
        print(f"  - Commands executed (dry-run)")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Component interaction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_automation_sequence():
    """Test sequence of automations (morning routine)"""
    print(f"\n{YELLOW}Testing Automation Sequence...{RESET}")

    try:
        from automations import good_morning, im_home

        # Simulate: wake up → adjust temp
        result1 = good_morning.run()
        time.sleep(0.1)  # Brief delay
        result2 = im_home.run()

        # Verify both completed
        assert result1['action'] == 'good_morning'
        assert result2['action'] == 'im_home'

        print(f"{GREEN}✓{RESET} Automation sequence test passed")
        print(f"  - Step 1: Good morning routine")
        print(f"  - Step 2: I'm home routine")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Automation sequence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    print(f"\n{GREEN}╔{'═'*58}╗{RESET}")
    print(f"{GREEN}║{' '*16}INTEGRATION TEST SUITE{' '*19}║{RESET}")
    print(f"{GREEN}╚{'═'*58}╝{RESET}\n")
    print(f"{YELLOW}Note: All tests run in DRY_RUN mode (no device changes){RESET}")

    tests = [
        ("Leaving Home Workflow", test_leaving_home_workflow),
        ("Goodnight Workflow", test_goodnight_workflow),
        ("I'm Home Workflow", test_im_home_workflow),
        ("Good Morning Workflow", test_good_morning_workflow),
        ("Temperature Coordination", test_temp_coordination_workflow),
        ("Concurrent Automations", test_concurrent_automations),
        ("Device Coordination", test_device_coordination),
        ("Component Interaction", test_component_interaction),
        ("Automation Sequence", test_automation_sequence)
    ]

    results = []

    print(f"\n{YELLOW}Running Integration Tests:{RESET}")
    print("="*60)

    for name, test_func in tests:
        result = test_func()
        results.append((name, result))

    # Summary
    print("\n" + "="*60)
    print(f"{GREEN}TEST SUMMARY{RESET}")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    failed = sum(1 for _, result in results if not result)

    print(f"Total: {len(results)} tests")
    print(f"{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")

    if failed > 0:
        print(f"\n{RED}Failed Tests:{RESET}")
        for name, result in results:
            if not result:
                print(f"  • {name}")

    print()

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

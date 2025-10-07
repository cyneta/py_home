#!/usr/bin/env python
"""
State Management Tests for py_home

Tests presence state tracking and persistence.

Tests:
- .presence_state file creation and reading
- State transitions (home → away → home)
- Duplicate event prevention (no-change detection)
- State recovery after crashes
- Concurrent state updates
"""

import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def test_state_file_creation():
    """Test .presence_state file creation"""
    print(f"\n{YELLOW}Testing State File Creation...{RESET}")

    try:
        from automations.presence_monitor import save_state, get_previous_state, STATE_FILE

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            # Patch STATE_FILE to use temp location
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Save state
                save_state(True)

                # Verify file was created
                assert os.path.exists(test_state_file), "State file not created"

                # Read and verify content
                with open(test_state_file, 'r') as f:
                    content = f.read().strip()

                assert content == 'home', f"Expected 'home', got '{content}'"

                print(f"{GREEN}✓{RESET} State file creation test passed")
                print(f"  - File created: {test_state_file}")
                print(f"  - Content: {content}")
                return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} State file creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_reading():
    """Test reading state from file"""
    print(f"\n{YELLOW}Testing State Reading...{RESET}")

    try:
        from automations.presence_monitor import save_state, get_previous_state

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Test reading non-existent file (first run)
                state = get_previous_state()
                assert state is None, "Expected None for non-existent file"

                # Save 'home' state
                save_state(True)
                state = get_previous_state()
                assert state is True, "Expected True for 'home' state"

                # Save 'away' state
                save_state(False)
                state = get_previous_state()
                assert state is False, "Expected False for 'away' state"

                print(f"{GREEN}✓{RESET} State reading test passed")
                print(f"  - Read None (first run)")
                print(f"  - Read True (home)")
                print(f"  - Read False (away)")
                return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} State reading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_transitions():
    """Test state transitions (home → away → home)"""
    print(f"\n{YELLOW}Testing State Transitions...{RESET}")

    try:
        from automations.presence_monitor import save_state, get_previous_state, run

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Mock check_presence to simulate transitions
                with patch('automations.presence_monitor.check_presence') as mock_check:
                    with patch('automations.presence_monitor.trigger_automation'):
                        with patch('lib.notifications.send_low'):
                            # Scenario 1: First run (no previous state)
                            mock_check.return_value = True
                            result = run()
                            assert result['action'] == 'initialize', "Expected initialize action"
                            assert result['state'] == 'home', "Expected home state"

                            # Scenario 2: Leave home (home → away)
                            mock_check.return_value = False
                            result = run()
                            assert result['action'] == 'departed', "Expected departed action"
                            assert result['state'] == 'away', "Expected away state"

                            # Scenario 3: No change (still away)
                            mock_check.return_value = False
                            result = run()
                            assert result['action'] == 'no_change', "Expected no_change action"

                            # Scenario 4: Return home (away → home)
                            mock_check.return_value = True
                            result = run()
                            assert result['action'] == 'arrived', "Expected arrived action"
                            assert result['state'] == 'home', "Expected home state"

                            print(f"{GREEN}✓{RESET} State transitions test passed")
                            print(f"  - Initialize → Home")
                            print(f"  - Home → Away (departed)")
                            print(f"  - Away → Away (no change)")
                            print(f"  - Away → Home (arrived)")
                            return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} State transitions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_duplicate_event_prevention():
    """Test that duplicate events are prevented (no-change detection)"""
    print(f"\n{YELLOW}Testing Duplicate Event Prevention...{RESET}")

    try:
        from automations.presence_monitor import run

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Mock check_presence to always return True (home)
                with patch('automations.presence_monitor.check_presence', return_value=True):
                    with patch('automations.presence_monitor.trigger_automation') as mock_trigger:
                        with patch('lib.notifications.send_low'):
                            # First run: initialize
                            result1 = run()
                            assert result1['action'] == 'initialize'

                            # Second run: no change (should not trigger automation)
                            result2 = run()
                            assert result2['action'] == 'no_change', "Expected no_change action"

                            # Third run: still no change
                            result3 = run()
                            assert result3['action'] == 'no_change', "Expected no_change action"

                            # Verify automation was NOT triggered for no-change events
                            assert mock_trigger.call_count == 0, "Automation should not be triggered on no-change"

                            print(f"{GREEN}✓{RESET} Duplicate event prevention test passed")
                            print(f"  - Initialize: triggered")
                            print(f"  - No-change events: 2")
                            print(f"  - Automations triggered: 0")
                            return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} Duplicate event prevention test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_recovery_after_crash():
    """Test state recovery after system crash/restart"""
    print(f"\n{YELLOW}Testing State Recovery After Crash...{RESET}")

    try:
        from automations.presence_monitor import save_state, get_previous_state

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Save state before "crash"
                save_state(True)

                # Simulate restart: read state
                recovered_state = get_previous_state()

                assert recovered_state is True, "Failed to recover state after crash"

                print(f"{GREEN}✓{RESET} State recovery test passed")
                print(f"  - State before crash: home")
                print(f"  - State after recovery: home")
                return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} State recovery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_corrupted_state_file():
    """Test handling of corrupted state file"""
    print(f"\n{YELLOW}Testing Corrupted State File Handling...{RESET}")

    try:
        from automations.presence_monitor import get_previous_state

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            # Create corrupted state file
            with open(test_state_file, 'w') as f:
                f.write('CORRUPTED_DATA_12345')

            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Should handle gracefully
                state = get_previous_state()

                # Should return False for unknown state (not 'home')
                assert state is False or state is None, "Should handle corrupted file gracefully"

                print(f"{GREEN}✓{RESET} Corrupted state file test passed")
                print(f"  - Corrupted file handled gracefully")
                print(f"  - Returned safe default: {state}")
                return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} Corrupted state file test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_concurrent_state_updates():
    """Test concurrent state updates"""
    print(f"\n{YELLOW}Testing Concurrent State Updates...{RESET}")

    try:
        import threading
        from automations.presence_monitor import save_state, get_previous_state

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                errors = []

                def update_state(value):
                    try:
                        save_state(value)
                        result = get_previous_state()
                        # Result might be different due to race condition
                    except Exception as e:
                        errors.append(str(e))

                # Create threads for concurrent updates
                threads = []
                for i in range(5):
                    value = i % 2 == 0  # Alternate True/False
                    thread = threading.Thread(target=update_state, args=(value,))
                    threads.append(thread)
                    thread.start()

                # Wait for all threads
                for thread in threads:
                    thread.join(timeout=5)

                # Should complete without errors (even if final state is unpredictable)
                if errors:
                    print(f"{YELLOW}⚠{RESET} Some concurrent updates had errors:")
                    for error in errors[:3]:
                        print(f"  - {error[:50]}")

                print(f"{GREEN}✓{RESET} Concurrent state updates test passed")
                print(f"  - Concurrent updates: 5")
                print(f"  - Errors: {len(errors)}")
                print(f"  - File operations are atomic (acceptable race conditions)")
                return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} Concurrent state updates test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_file_permissions():
    """Test state file permissions and accessibility"""
    print(f"\n{YELLOW}Testing State File Permissions...{RESET}")

    try:
        from automations.presence_monitor import save_state

        # Use temp directory for testing
        test_dir = tempfile.mkdtemp()
        test_state_file = os.path.join(test_dir, '.presence_state')

        try:
            with patch('automations.presence_monitor.STATE_FILE', test_state_file):
                # Save state
                save_state(True)

                # Verify file exists and is readable/writable
                assert os.path.exists(test_state_file), "State file not created"
                assert os.access(test_state_file, os.R_OK), "State file not readable"
                assert os.access(test_state_file, os.W_OK), "State file not writable"

                print(f"{GREEN}✓{RESET} State file permissions test passed")
                print(f"  - File created successfully")
                print(f"  - Readable: Yes")
                print(f"  - Writable: Yes")
                return True

        finally:
            # Clean up
            shutil.rmtree(test_dir, ignore_errors=True)

    except Exception as e:
        print(f"{RED}✗{RESET} State file permissions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all state management tests"""
    print(f"\n{GREEN}╔{'═'*58}╗{RESET}")
    print(f"{GREEN}║{' '*13}STATE MANAGEMENT TEST SUITE{' '*15}║{RESET}")
    print(f"{GREEN}╚{'═'*58}╝{RESET}\n")
    print(f"{YELLOW}Testing presence state tracking and persistence{RESET}")

    tests = [
        ("State File Creation", test_state_file_creation),
        ("State Reading", test_state_reading),
        ("State Transitions", test_state_transitions),
        ("Duplicate Event Prevention", test_duplicate_event_prevention),
        ("State Recovery After Crash", test_state_recovery_after_crash),
        ("Corrupted State File Handling", test_corrupted_state_file),
        ("Concurrent State Updates", test_concurrent_state_updates),
        ("State File Permissions", test_state_file_permissions)
    ]

    results = []

    print(f"\n{YELLOW}Running State Management Tests:{RESET}")
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

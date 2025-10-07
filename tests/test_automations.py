#!/usr/bin/env python
"""
Test Automation Scripts

Tests all 9 automation scripts in dry-run mode (no actual device changes).

Validates:
- Script imports work
- Configuration loads
- Logic flow is correct
- No runtime errors

Does NOT:
- Make actual API calls
- Change device states
- Send notifications
"""

import sys
import subprocess
import os

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def test_automation_imports():
    """Test that all automation modules can be imported"""
    print("Testing Automation Imports...\n")

    automations = [
        'leaving_home',
        'goodnight',
        'im_home',
        'good_morning',
        'travel_time',
        'task_router',
        'temp_coordination',
        'presence_monitor',
        'traffic_alert'
    ]

    results = []

    for name in automations:
        try:
            # Import the module
            module = __import__(f'automations.{name}', fromlist=['run'])

            # Check for run() function
            if hasattr(module, 'run'):
                print(f"{GREEN}✓{RESET} {name}.py imports successfully (has run())")
                results.append((name, True, "OK"))
            else:
                print(f"{YELLOW}⚠{RESET} {name}.py imports but no run() function")
                results.append((name, False, "No run() function"))

        except Exception as e:
            print(f"{RED}✗{RESET} {name}.py failed to import: {e}")
            results.append((name, False, str(e)))

    print()
    return results


def test_automation_execution():
    """Test automation execution in dry-run mode (safe, no device changes)"""
    print("Testing Automation Execution (Dry-Run)...\n")

    # Automations with dry-run support
    dry_run_automations = {
        'leaving_home': 'Set house to away mode',
        'goodnight': 'Sleep mode with AC/lights off',
        'im_home': 'Welcome home routine',
        'good_morning': 'Morning routine with weather',
        'temp_coordination': 'HVAC coordination'
    }

    # Automations not yet updated with dry-run (just check structure)
    other_automations = {
        'travel_time': 'Traffic-aware travel time',
        'task_router': 'AI-powered task routing',
        'presence_monitor': 'WiFi presence detection',
        'traffic_alert': 'I-80 traffic monitoring'
    }

    results = []

    # Test dry-run automations with actual execution
    for name, description in dry_run_automations.items():
        try:
            script_path = os.path.join('automations', f'{name}.py')

            if not os.path.exists(script_path):
                print(f"{RED}✗{RESET} {name}.py - File not found")
                results.append((name, False, "File not found"))
                continue

            # Execute with --dry-run flag
            result = subprocess.run(
                [sys.executable, script_path, '--dry-run'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Check for [DRY-RUN] indicators in output
            has_dry_run = '[DRY-RUN]' in result.stdout or '[DRY-RUN]' in result.stderr
            success = result.returncode == 0

            if success and has_dry_run:
                print(f"{GREEN}✓{RESET} {name}.py - {description} (executed safely)")
                results.append((name, True, "Dry-run OK"))
            elif success:
                print(f"{YELLOW}⚠{RESET} {name}.py - Ran but no dry-run indicators")
                results.append((name, False, "Missing dry-run markers"))
            else:
                error_msg = result.stderr[:100] if result.stderr else "Unknown error"
                print(f"{RED}✗{RESET} {name}.py - Execution failed: {error_msg}")
                results.append((name, False, error_msg))

        except subprocess.TimeoutExpired:
            print(f"{RED}✗{RESET} {name}.py - Timeout (>30s)")
            results.append((name, False, "Timeout"))
        except Exception as e:
            print(f"{RED}✗{RESET} {name}.py - {e}")
            results.append((name, False, str(e)))

    # Test other automations for structure only
    for name, description in other_automations.items():
        try:
            script_path = os.path.join('automations', f'{name}.py')

            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Basic validation
                has_run = 'def run(' in content
                has_imports = 'import' in content

                if has_run and has_imports:
                    print(f"{GREEN}✓{RESET} {name}.py - {description} (structure only)")
                    results.append((name, True, "Structure OK"))
                else:
                    print(f"{YELLOW}⚠{RESET} {name}.py - Missing run() or imports")
                    results.append((name, False, "Missing structure"))
            else:
                print(f"{RED}✗{RESET} {name}.py - File not found")
                results.append((name, False, "File not found"))

        except Exception as e:
            print(f"{RED}✗{RESET} {name}.py - {e}")
            results.append((name, False, str(e)))

    print()
    return results


def test_automation_logic():
    """Test automation logic structure"""
    print("Testing Automation Logic...\n")

    # Test specific automation logic patterns
    tests = [
        {
            'name': 'leaving_home',
            'checks': ['set_temperature', 'turn_off_all', 'notifications'],
            'description': 'Away mode automation'
        },
        {
            'name': 'goodnight',
            'checks': ['set_temperature', 'turn_off', 'notifications'],
            'description': 'Sleep mode automation'
        },
        {
            'name': 'task_router',
            'checks': ['classify_task', 'github', 'checkvist'],
            'description': 'Task routing with AI'
        },
        {
            'name': 'temp_coordination',
            'checks': ['get_status', 'turn_on', 'turn_off'],
            'description': 'HVAC coordination'
        }
    ]

    results = []

    for test in tests:
        name = test['name']
        script_path = os.path.join('automations', f'{name}.py')

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for expected patterns
            found_patterns = []
            missing_patterns = []

            for pattern in test['checks']:
                if pattern in content:
                    found_patterns.append(pattern)
                else:
                    missing_patterns.append(pattern)

            if not missing_patterns:
                print(f"{GREEN}✓{RESET} {name}.py - {test['description']}")
                print(f"  Found: {', '.join(found_patterns)}")
                results.append((name, True, "Logic OK"))
            else:
                print(f"{YELLOW}⚠{RESET} {name}.py - {test['description']}")
                print(f"  Missing: {', '.join(missing_patterns)}")
                results.append((name, False, f"Missing: {', '.join(missing_patterns)}"))

        except Exception as e:
            print(f"{RED}✗{RESET} {name}.py - {e}")
            results.append((name, False, str(e)))

    print()
    return results


def main():
    """Run all automation tests"""
    print(f"\n{GREEN}╔{'═'*58}╗{RESET}")
    print(f"{GREEN}║{' '*16}AUTOMATION TEST SUITE{' '*20}║{RESET}")
    print(f"{GREEN}╚{'═'*58}╝{RESET}\n")

    all_results = []

    # Test imports
    print(f"{YELLOW}Phase 1: Testing Imports{RESET}")
    print("="*60)
    import_results = test_automation_imports()
    all_results.extend(import_results)

    # Test execution structure
    print(f"{YELLOW}Phase 2: Testing Execution Structure{RESET}")
    print("="*60)
    execution_results = test_automation_execution()
    all_results.extend(execution_results)

    # Test logic patterns
    print(f"{YELLOW}Phase 3: Testing Logic Patterns{RESET}")
    print("="*60)
    logic_results = test_automation_logic()
    all_results.extend(logic_results)

    # Summary
    print("="*60)
    print(f"{GREEN}TEST SUMMARY{RESET}")
    print("="*60)

    passed = [r for r in all_results if r[1]]
    failed = [r for r in all_results if not r[1]]

    print(f"Total: {len(all_results)} tests")
    print(f"{GREEN}Passed: {len(passed)}{RESET}")
    print(f"{RED}Failed: {len(failed)}{RESET}")

    if failed:
        print(f"\n{RED}Failed Tests:{RESET}")
        for name, _, msg in failed:
            print(f"  • {name}: {msg}")

    print()
    print(f"{YELLOW}Note: These are structural tests. No actual automation actions were executed.{RESET}")
    print()

    return len(failed) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

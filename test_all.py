#!/usr/bin/env python
"""
Comprehensive Test Suite for py_home

Tests all components, services, and automations.

Usage:
    python test_all.py              # Run all tests
    python test_all.py --quick      # Skip slow API tests
    python test_all.py --only tapo  # Test only specific component
"""

import sys
import argparse
import time
import requests
from typing import Dict, List, Optional

# ANSI color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'


class TestResult:
    """Store results for a test"""
    def __init__(self, name: str, status: str, message: str = "", details: Dict = None, duration: float = 0):
        self.name = name
        self.status = status  # 'pass', 'fail', 'skip'
        self.message = message
        self.details = details or {}
        self.duration = duration

    @property
    def passed(self):
        return self.status == 'pass'

    @property
    def skipped(self):
        return self.status == 'skip'


def print_header(text: str):
    """Print a section header"""
    print(f"\n{BLUE}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{RESET}\n")


def print_result(result: TestResult):
    """Print a test result"""
    if result.status == 'pass':
        status = f"{GREEN}✓ PASS{RESET}"
    elif result.status == 'skip':
        status = f"{YELLOW}⊘ SKIP{RESET}"
    else:
        status = f"{RED}✗ FAIL{RESET}"

    duration_str = f" ({result.duration:.2f}s)" if result.duration > 0 else ""
    print(f"{status} {result.name}{duration_str}")

    if result.message:
        print(f"  {result.message}")
    if result.details:
        for key, value in result.details.items():
            print(f"    {key}: {value}")


# ============================================================================
# CONFIGURATION TESTS
# ============================================================================

def test_config() -> TestResult:
    """Test configuration loading"""
    start = time.time()
    try:
        from lib.config import config

        # Check required sections
        required = ['nest', 'tapo', 'sensibo', 'locations']
        missing = [s for s in required if s not in config]

        if missing:
            return TestResult(
                "Configuration",
                'fail',
                f"Missing sections: {', '.join(missing)}",
                duration=time.time() - start
            )

        return TestResult(
            "Configuration",
            'pass',
            "All required sections present",
            {
                "Nest": "✓",
                "Tapo": "✓",
                "Sensibo": "✓",
                "Locations": "✓"
            },
            duration=time.time() - start
        )
    except Exception as e:
        return TestResult("Configuration", 'fail', str(e), duration=time.time() - start)


# ============================================================================
# DEVICE COMPONENT TESTS
# ============================================================================

def test_tapo(skip: bool = False) -> TestResult:
    """Test Tapo smart plugs"""
    if skip:
        return TestResult("Tapo Smart Plugs", 'skip', "Skipped by user")

    start = time.time()
    try:
        from components.tapo import TapoAPI

        tapo = TapoAPI()
        statuses = tapo.list_all_status()

        working = [s for s in statuses if 'error' not in s]
        failed = [s for s in statuses if 'error' in s]

        details = {}
        for s in working:
            name = s['device_info']['alias']
            state = "ON" if s['on'] else "OFF"
            rssi = s['device_info']['rssi']
            details[name] = f"{state} ({rssi} dBm)"

        if failed:
            for s in failed:
                details[s['name']] = f"FAILED: {s['error']}"

        passed = len(failed) == 0
        message = f"{len(working)}/{len(statuses)} plugs working"

        return TestResult(
            "Tapo Smart Plugs",
            'pass' if passed else 'fail',
            message,
            details,
            duration=time.time() - start
        )
    except Exception as e:
        return TestResult("Tapo Smart Plugs", 'fail', str(e), duration=time.time() - start)


def test_nest(skip: bool = False) -> TestResult:
    """Test Nest thermostat"""
    if skip:
        return TestResult("Nest Thermostat", 'skip', "Skipped by user")

    start = time.time()
    try:
        from components.nest import get_status

        status = get_status()

        details = {
            "Current Temp": f"{status['current_temp_f']:.1f}°F",
            "Humidity": f"{status['current_humidity']}%",
            "Mode": status['mode'],
            "HVAC": status['hvac_status']
        }

        if status['heat_setpoint_f']:
            details["Heat Target"] = f"{status['heat_setpoint_f']:.1f}°F"
        if status['cool_setpoint_f']:
            details["Cool Target"] = f"{status['cool_setpoint_f']:.1f}°F"

        return TestResult("Nest Thermostat", 'pass', "Responding", details, duration=time.time() - start)
    except Exception as e:
        return TestResult("Nest Thermostat", 'fail', str(e), duration=time.time() - start)


def test_sensibo(skip: bool = False) -> TestResult:
    """Test Sensibo AC"""
    if skip:
        return TestResult("Sensibo AC", 'skip', "Skipped by user")

    start = time.time()
    try:
        from components.sensibo import get_status

        status = get_status()

        details = {
            "Room": status['room'],
            "Power": "ON" if status['on'] else "OFF",
            "Mode": status['mode'],
            "Target": f"{status['target_temp_f']:.0f}°F",
            "Current": f"{status['current_temp_f']:.1f}°F",
            "Humidity": f"{status['current_humidity']:.1f}%"
        }

        return TestResult("Sensibo AC", 'pass', "Responding", details, duration=time.time() - start)
    except Exception as e:
        return TestResult("Sensibo AC", 'fail', str(e), duration=time.time() - start)


def test_network(skip: bool = False) -> TestResult:
    """Test network presence detection"""
    if skip:
        return TestResult("Network Presence", 'skip', "Skipped by user")

    start = time.time()
    try:
        from components.network import is_device_home

        # Test with localhost
        result = is_device_home('127.0.0.1', method='ping')

        if result:
            return TestResult(
                "Network Presence",
                'pass',
                "Localhost detection working",
                {"Method": "ping", "Result": "✓"},
                duration=time.time() - start
            )
        else:
            return TestResult(
                "Network Presence",
                'fail',
                "Localhost should be reachable",
                duration=time.time() - start
            )
    except Exception as e:
        return TestResult("Network Presence", 'fail', str(e), duration=time.time() - start)


# ============================================================================
# SERVICE API TESTS
# ============================================================================

def test_standalone_service_tests(skip: bool = False) -> List[TestResult]:
    """Run comprehensive standalone service tests"""
    if skip:
        return [TestResult("Standalone Service Tests", 'skip', "Skipped (use --quick)")]

    results = []

    # Google Maps comprehensive test
    start = time.time()
    try:
        from services import test_google_maps
        success = test_google_maps.test()
        if success:
            results.append(TestResult(
                "Google Maps (detailed)",
                'pass',
                "Comprehensive tests passed",
                duration=time.time() - start
            ))
        else:
            results.append(TestResult(
                "Google Maps (detailed)",
                'fail',
                "Some tests failed",
                duration=time.time() - start
            ))
    except Exception as e:
        results.append(TestResult("Google Maps (detailed)", 'fail', str(e), duration=time.time() - start))

    # GitHub comprehensive test
    start = time.time()
    try:
        from services import test_github
        success = test_github.test()
        if success:
            results.append(TestResult(
                "GitHub (detailed)",
                'pass',
                "Comprehensive tests passed",
                duration=time.time() - start
            ))
        else:
            results.append(TestResult(
                "GitHub (detailed)",
                'fail',
                "Some tests failed",
                duration=time.time() - start
            ))
    except Exception as e:
        results.append(TestResult("GitHub (detailed)", 'fail', str(e), duration=time.time() - start))

    # Checkvist comprehensive test
    start = time.time()
    try:
        from services import test_checkvist
        success = test_checkvist.test()
        if success:
            results.append(TestResult(
                "Checkvist (detailed)",
                'pass',
                "Comprehensive tests passed",
                duration=time.time() - start
            ))
        else:
            results.append(TestResult(
                "Checkvist (detailed)",
                'fail',
                "Some tests failed",
                duration=time.time() - start
            ))
    except Exception as e:
        results.append(TestResult("Checkvist (detailed)", 'fail', str(e), duration=time.time() - start))

    return results


def test_openweather(skip: bool = False) -> TestResult:
    """Test OpenWeather API"""
    if skip:
        return TestResult("OpenWeather API", 'skip', "Skipped (use --quick)")

    start = time.time()
    try:
        from services import get_current_weather

        weather = get_current_weather()

        details = {
            "Location": weather['city'],
            "Temp": f"{weather['temp']:.1f}°F",
            "Feels Like": f"{weather['feels_like']:.1f}°F",
            "Conditions": weather['conditions'],
            "Humidity": f"{weather['humidity']}%",
            "Wind": f"{weather['wind_speed']:.1f} mph"
        }

        return TestResult("OpenWeather API", 'pass', "Responding", details, duration=time.time() - start)
    except Exception as e:
        return TestResult("OpenWeather API", 'fail', str(e), duration=time.time() - start)


def test_google_maps(skip: bool = False) -> TestResult:
    """Test Google Maps API"""
    if skip:
        return TestResult("Google Maps API", 'skip', "Skipped (use --quick)")

    start = time.time()
    try:
        from services import get_travel_time

        result = get_travel_time("Chicago, IL", "Milwaukee, WI")

        details = {
            "Route": "Chicago → Milwaukee",
            "Duration": f"{result['duration_minutes']} min",
            "Distance": f"{result['distance_miles']:.1f} miles",
            "Traffic": result.get('traffic_level', 'N/A')
        }

        return TestResult("Google Maps API", 'pass', "Responding", details, duration=time.time() - start)
    except Exception as e:
        return TestResult("Google Maps API", 'fail', str(e), duration=time.time() - start)


def test_github(skip: bool = False) -> TestResult:
    """Test GitHub API"""
    if skip:
        return TestResult("GitHub API", 'skip', "Skipped (use --quick)")

    start = time.time()
    try:
        from services.github import GitHubAPI

        github = GitHubAPI()
        repo_info = github.get_repo_info()

        details = {
            "Repository": repo_info['full_name'],
            "Private": "Yes" if repo_info.get('private') else "No",
            "Branch": repo_info.get('default_branch', 'N/A')
        }

        return TestResult("GitHub API", 'pass', "Connected", details, duration=time.time() - start)
    except Exception as e:
        return TestResult("GitHub API", 'fail', str(e), duration=time.time() - start)


def test_checkvist(skip: bool = False) -> TestResult:
    """Test Checkvist API"""
    if skip:
        return TestResult("Checkvist API", 'skip', "Skipped (use --quick)")

    start = time.time()
    try:
        from services.checkvist import CheckvistAPI

        checkvist = CheckvistAPI()
        lists = checkvist.get_lists()

        details = {
            "Lists Found": len(lists),
            "Username": checkvist.username
        }

        return TestResult("Checkvist API", 'pass', "Connected", details, duration=time.time() - start)
    except Exception as e:
        return TestResult("Checkvist API", 'fail', str(e), duration=time.time() - start)


# ============================================================================
# LIBRARY TESTS
# ============================================================================

def test_lib_modules() -> List[TestResult]:
    """Test shared library modules"""
    results = []

    # Test config module
    start = time.time()
    try:
        from lib import config
        results.append(TestResult("lib.config", 'pass', "Module loads", duration=time.time() - start))
    except Exception as e:
        results.append(TestResult("lib.config", 'fail', str(e), duration=time.time() - start))

    # Test notifications module
    start = time.time()
    try:
        from lib import notifications
        results.append(TestResult("lib.notifications", 'pass', "Module loads", duration=time.time() - start))
    except Exception as e:
        results.append(TestResult("lib.notifications", 'fail', str(e), duration=time.time() - start))

    return results


# ============================================================================
# IMPORT TESTS
# ============================================================================

def test_imports() -> List[TestResult]:
    """Test clean imports work as expected"""
    results = []

    # Test Tapo imports
    start = time.time()
    try:
        from components.tapo import turn_on, turn_off, get_status
        results.append(TestResult("Import: components.tapo", 'pass', "Clean imports work", duration=time.time() - start))
    except Exception as e:
        results.append(TestResult("Import: components.tapo", 'fail', str(e), duration=time.time() - start))

    # Test Nest imports
    start = time.time()
    try:
        from components.nest import set_temperature, get_status
        results.append(TestResult("Import: components.nest", 'pass', "Clean imports work", duration=time.time() - start))
    except Exception as e:
        results.append(TestResult("Import: components.nest", 'fail', str(e), duration=time.time() - start))

    # Test Sensibo imports
    start = time.time()
    try:
        from components.sensibo import turn_on, turn_off
        results.append(TestResult("Import: components.sensibo", 'pass', "Clean imports work", duration=time.time() - start))
    except Exception as e:
        results.append(TestResult("Import: components.sensibo", 'fail', str(e), duration=time.time() - start))

    # Test Network imports
    start = time.time()
    try:
        from components.network import is_device_home
        results.append(TestResult("Import: components.network", 'pass', "Clean imports work", duration=time.time() - start))
    except Exception as e:
        results.append(TestResult("Import: components.network", 'fail', str(e), duration=time.time() - start))

    return results


# ============================================================================
# AUTOMATION TESTS
# ============================================================================

def test_automations(skip: bool = False) -> List[TestResult]:
    """Test automation scripts"""
    if skip:
        return [TestResult("Automation Scripts", 'skip', "Skipped by user")]

    results = []

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

    for name in automations:
        start = time.time()
        try:
            module = __import__(f'automations.{name}', fromlist=['run'])

            if hasattr(module, 'run'):
                results.append(TestResult(
                    f"automation: {name}",
                    'pass',
                    "Structure OK",
                    duration=time.time() - start
                ))
            else:
                results.append(TestResult(
                    f"automation: {name}",
                    'fail',
                    "Missing run() function",
                    duration=time.time() - start
                ))

        except Exception as e:
            results.append(TestResult(
                f"automation: {name}",
                'fail',
                str(e),
                duration=time.time() - start
            ))

    return results


# ============================================================================
# SERVER TESTS
# ============================================================================

def test_flask_server(skip: bool = False) -> TestResult:
    """Test Flask server if running"""
    if skip:
        return TestResult("Flask Server", 'skip', "Skipped by user")

    start = time.time()
    try:
        resp = requests.get("http://localhost:5000/status", timeout=2)

        if resp.status_code == 200:
            data = resp.json()
            details = {
                "Status": data.get('status', 'unknown'),
                "Endpoints": len(data.get('endpoints', []))
            }
            return TestResult(
                "Flask Server",
                'pass',
                "Server responding",
                details,
                duration=time.time() - start
            )
        else:
            return TestResult(
                "Flask Server",
                'fail',
                f"Server returned {resp.status_code}",
                duration=time.time() - start
            )

    except requests.exceptions.ConnectionError:
        return TestResult(
            "Flask Server",
            'skip',
            "Server not running (start with: python server/app.py)",
            duration=time.time() - start
        )
    except Exception as e:
        return TestResult("Flask Server", 'fail', str(e), duration=time.time() - start)


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests and generate report"""
    parser = argparse.ArgumentParser(description='py_home test suite')
    parser.add_argument('--quick', action='store_true', help='Skip slow API tests')
    parser.add_argument('--only', type=str, help='Test only specific component (tapo, nest, etc.)')
    args = parser.parse_args()

    print(f"\n{CYAN}╔{'═'*68}╗{RESET}")
    print(f"{CYAN}║{' '*20}PY_HOME TEST SUITE{' '*26}║{RESET}")
    print(f"{CYAN}╚{'═'*68}╝{RESET}")

    if args.quick:
        print(f"{YELLOW}Running in QUICK mode (skipping slow API tests){RESET}")
    if args.only:
        print(f"{YELLOW}Testing only: {args.only}{RESET}")

    all_results: List[TestResult] = []
    start_time = time.time()

    # Test configuration
    if not args.only or args.only == 'config':
        print_header("Configuration")
        result = test_config()
        print_result(result)
        all_results.append(result)

    # Test imports
    if not args.only or args.only == 'imports':
        print_header("Module Imports")
        import_results = test_imports()
        for result in import_results:
            print_result(result)
        all_results.extend(import_results)

    # Test device components
    if not args.only or args.only in ['devices', 'tapo', 'nest', 'sensibo', 'network']:
        print_header("Device Components")

        if not args.only or args.only in ['devices', 'tapo']:
            result = test_tapo(skip=(args.only and args.only != 'tapo'))
            print_result(result)
            all_results.append(result)

        if not args.only or args.only in ['devices', 'nest']:
            result = test_nest(skip=(args.only and args.only != 'nest'))
            print_result(result)
            all_results.append(result)

        if not args.only or args.only in ['devices', 'sensibo']:
            result = test_sensibo(skip=(args.only and args.only != 'sensibo'))
            print_result(result)
            all_results.append(result)

        if not args.only or args.only in ['devices', 'network']:
            result = test_network(skip=(args.only and args.only != 'network'))
            print_result(result)
            all_results.append(result)

    # Test services
    if not args.only or args.only in ['services', 'apis']:
        print_header("External Service APIs")

        result = test_openweather(skip=args.quick)
        print_result(result)
        all_results.append(result)

        result = test_google_maps(skip=args.quick)
        print_result(result)
        all_results.append(result)

        result = test_github(skip=args.quick)
        print_result(result)
        all_results.append(result)

        result = test_checkvist(skip=args.quick)
        print_result(result)
        all_results.append(result)

        # Run comprehensive standalone service tests
        print_header("Detailed Service Tests")
        standalone_results = test_standalone_service_tests(skip=args.quick)
        for result in standalone_results:
            print_result(result)
        all_results.extend(standalone_results)

    # Test library modules
    if not args.only or args.only == 'lib':
        print_header("Shared Libraries")
        lib_results = test_lib_modules()
        for result in lib_results:
            print_result(result)
        all_results.extend(lib_results)

    # Test automations
    if not args.only or args.only == 'automations':
        print_header("Automation Scripts")
        automation_results = test_automations(skip=(args.only and args.only != 'automations'))
        for result in automation_results:
            print_result(result)
        all_results.extend(automation_results)

    # Test Flask server
    if not args.only or args.only == 'server':
        print_header("Flask Server")
        result = test_flask_server(skip=(args.only and args.only != 'server'))
        print_result(result)
        all_results.append(result)

    # Summary
    total_time = time.time() - start_time

    print_header("Test Summary")

    passed = [r for r in all_results if r.passed]
    failed = [r for r in all_results if r.status == 'fail']
    skipped = [r for r in all_results if r.skipped]

    print(f"Total Tests: {len(all_results)}")
    print(f"{GREEN}Passed:  {len(passed)}{RESET}")
    print(f"{RED}Failed:  {len(failed)}{RESET}")
    print(f"{YELLOW}Skipped: {len(skipped)}{RESET}")
    print(f"\n{CYAN}Duration: {total_time:.2f}s{RESET}")

    if failed:
        print(f"\n{RED}Failed Tests:{RESET}")
        for result in failed:
            print(f"  • {result.name}: {result.message}")

    if skipped and not args.quick:
        print(f"\n{YELLOW}Skipped Tests:{RESET}")
        for result in skipped:
            print(f"  • {result.name}: {result.message}")

    print(f"\n{BLUE}{'='*70}{RESET}\n")

    # Exit code
    sys.exit(0 if len(failed) == 0 else 1)


if __name__ == '__main__':
    main()

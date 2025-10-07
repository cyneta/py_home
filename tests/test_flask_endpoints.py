#!/usr/bin/env python
"""
Test Flask Server Endpoints

Tests all webhook endpoints including POST endpoints that trigger automations.

Note: Server does NOT need to be running - this tests endpoint definitions
and routing, not actual HTTP requests.

Run with: python tests/test_flask_endpoints.py
"""

import sys
import os

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_flask_app_creation():
    """Test that Flask app can be created"""
    print(f"\n{YELLOW}Testing Flask app creation...{RESET}")

    try:
        from server.app import app

        assert app is not None
        print(f"{GREEN}✓{RESET} Flask app created successfully")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Flask app creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_routes_registered():
    """Test that all routes are registered"""
    print(f"\n{YELLOW}Testing route registration...{RESET}")

    try:
        from server.app import app

        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),
                'path': rule.rule
            })

        # Expected routes
        expected_paths = [
            '/',
            '/status',
            '/leaving-home',
            '/goodnight',
            '/im-home',
            '/good-morning',
            '/travel-time',
            '/add-task'
        ]

        # Check each expected route exists
        found_paths = [r['path'] for r in routes]
        missing = [p for p in expected_paths if p not in found_paths]

        if missing:
            print(f"{RED}✗{RESET} Missing routes: {missing}")
            return False

        print(f"{GREEN}✓{RESET} All {len(expected_paths)} routes registered")
        for route in routes:
            if route['path'] in expected_paths:
                methods = ', '.join(route['methods'])
                print(f"  {route['path']} [{methods}]")

        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Route registration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_post_endpoints():
    """Test POST endpoint definitions"""
    print(f"\n{YELLOW}Testing POST endpoint definitions...{RESET}")

    try:
        from server.app import app

        post_endpoints = [
            '/leaving-home',
            '/goodnight',
            '/im-home',
            '/good-morning',
            '/add-task'
        ]

        for path in post_endpoints:
            # Get rule for this path
            rule = None
            for r in app.url_map.iter_rules():
                if r.rule == path:
                    rule = r
                    break

            if not rule:
                print(f"{RED}✗{RESET} POST endpoint {path} not found")
                return False

            if 'POST' not in rule.methods:
                print(f"{RED}✗{RESET} POST endpoint {path} doesn't accept POST")
                return False

        print(f"{GREEN}✓{RESET} All {len(post_endpoints)} POST endpoints defined correctly")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} POST endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_endpoints():
    """Test GET endpoint definitions"""
    print(f"\n{YELLOW}Testing GET endpoint definitions...{RESET}")

    try:
        from server.app import app

        get_endpoints = [
            '/',
            '/status',
            '/travel-time'
        ]

        for path in get_endpoints:
            # Get rule for this path
            rule = None
            for r in app.url_map.iter_rules():
                if r.rule == path:
                    rule = r
                    break

            if not rule:
                print(f"{RED}✗{RESET} GET endpoint {path} not found")
                return False

            if 'GET' not in rule.methods:
                print(f"{RED}✗{RESET} GET endpoint {path} doesn't accept GET")
                return False

        print(f"{GREEN}✓{RESET} All {len(get_endpoints)} GET endpoints defined correctly")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} GET endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_automation_scripts_exist():
    """Test that automation scripts referenced by endpoints exist"""
    print(f"\n{YELLOW}Testing automation script files exist...{RESET}")

    try:
        automation_scripts = [
            'leaving_home.py',
            'goodnight.py',
            'im_home.py',
            'good_morning.py',
            'travel_time.py',
            'task_router.py'
        ]

        automations_dir = os.path.join(os.path.dirname(__file__), '..', 'automations')

        missing = []
        for script in automation_scripts:
            script_path = os.path.join(automations_dir, script)
            if not os.path.exists(script_path):
                missing.append(script)

        if missing:
            print(f"{RED}✗{RESET} Missing automation scripts: {missing}")
            return False

        print(f"{GREEN}✓{RESET} All {len(automation_scripts)} automation scripts exist")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Automation script check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test that server config loads"""
    print(f"\n{YELLOW}Testing server config loading...{RESET}")

    try:
        from server import config

        # Check required config values exist
        assert hasattr(config, 'HOST')
        assert hasattr(config, 'PORT')
        assert hasattr(config, 'DEBUG')
        assert hasattr(config, 'REQUIRE_AUTH')
        assert hasattr(config, 'AUTOMATIONS_DIR')

        print(f"{GREEN}✓{RESET} Server config loaded successfully")
        print(f"  Host: {config.HOST}")
        print(f"  Port: {config.PORT}")
        print(f"  Auth: {config.REQUIRE_AUTH}")

        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Config loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth_decorator_exists():
    """Test that require_auth decorator is defined"""
    print(f"\n{YELLOW}Testing authentication decorator...{RESET}")

    try:
        from server.routes import require_auth

        assert callable(require_auth)
        print(f"{GREEN}✓{RESET} Authentication decorator defined")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} Auth decorator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_run_automation_script_function():
    """Test that run_automation_script helper exists"""
    print(f"\n{YELLOW}Testing run_automation_script helper...{RESET}")

    try:
        from server.routes import run_automation_script

        assert callable(run_automation_script)
        print(f"{GREEN}✓{RESET} run_automation_script helper defined")
        return True

    except Exception as e:
        print(f"{RED}✗{RESET} run_automation_script test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all Flask endpoint tests"""
    print(f"\n{BLUE}╔{'═'*68}╗{RESET}")
    print(f"{BLUE}║{' '*18}FLASK ENDPOINT TESTS{' '*26}║{RESET}")
    print(f"{BLUE}╚{'═'*68}╝{RESET}")

    print("\nThese tests verify Flask server configuration and routing.")
    print("Server does NOT need to be running.\n")

    results = []

    # Test Flask app
    print(f"\n{BLUE}{'='*70}")
    print("Flask Application")
    print(f"{'='*70}{RESET}")

    results.append(("Flask app creation", test_flask_app_creation()))
    results.append(("Route registration", test_routes_registered()))
    results.append(("Config loading", test_config_loading()))

    # Test endpoints
    print(f"\n{BLUE}{'='*70}")
    print("Endpoint Definitions")
    print(f"{'='*70}{RESET}")

    results.append(("POST endpoints", test_post_endpoints()))
    results.append(("GET endpoints", test_get_endpoints()))

    # Test supporting infrastructure
    print(f"\n{BLUE}{'='*70}")
    print("Supporting Infrastructure")
    print(f"{'='*70}{RESET}")

    results.append(("Automation scripts", test_automation_scripts_exist()))
    results.append(("Auth decorator", test_auth_decorator_exists()))
    results.append(("run_automation_script", test_run_automation_script_function()))

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

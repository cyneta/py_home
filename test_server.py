#!/usr/bin/env python
"""
Test Flask Server Endpoints

Quick test to verify all endpoints are working.

Usage:
    # In terminal 1: python server/app.py
    # In terminal 2: python test_server.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"


def test_endpoint(name, method, path, data=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == 'GET':
            resp = requests.get(url, params=data, timeout=5)
        else:
            resp = requests.post(url, json=data, timeout=5)

        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"{method} {path}")
        print(f"Status: {resp.status_code}")
        print(f"Response:")
        print(json.dumps(resp.json(), indent=2))
        return resp.status_code == 200
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print(f"FAILED: {e}")
        return False


def main():
    print("Flask Server Endpoint Tests")
    print("="*60)
    print(f"Server: {BASE_URL}")
    print("="*60)

    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    for i in range(5):
        try:
            requests.get(f"{BASE_URL}/", timeout=1)
            print("✓ Server is ready\n")
            break
        except:
            time.sleep(1)
    else:
        print("✗ Server is not responding. Start it with: python server/app.py\n")
        return

    results = []

    # Test health check
    results.append(test_endpoint("Health Check", "GET", "/"))

    # Test status endpoint
    results.append(test_endpoint("Status", "GET", "/status"))

    # Test travel time (synchronous, returns data)
    results.append(test_endpoint(
        "Travel Time",
        "GET",
        "/travel-time",
        {"destination": "Milwaukee, WI"}
    ))

    # Test async endpoints (they just start scripts)
    # Note: These won't actually run the automations in test, just verify routing works
    # results.append(test_endpoint("Leaving Home", "POST", "/leaving-home"))
    # results.append(test_endpoint("Goodnight", "POST", "/goodnight"))
    # results.append(test_endpoint("I'm Home", "POST", "/im-home"))
    # results.append(test_endpoint("Good Morning", "POST", "/good-morning"))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")
    print("="*60)


if __name__ == '__main__':
    main()

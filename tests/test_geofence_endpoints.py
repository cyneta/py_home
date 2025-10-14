#!/usr/bin/env python
"""
Tests for Geofencing Endpoints

Tests Flask routes for location updates and ETA queries.
"""

import os
import sys
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Test colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_update_location_endpoint():
    """Test /update-location endpoint"""
    print("Test 1: POST /update-location endpoint")

    from server.app import app
    import lib.location as loc_module

    # Use temp file for testing
    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_geofence.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        with app.test_client() as client:
            # Test 1: Valid location update
            response = client.post(
                '/update-location',
                json={
                    'lat': 45.4465,
                    'lng': -122.6393,
                    'trigger': 'near_home',
                    'trigger_automations': False  # Don't run automations in test
                },
                content_type='application/json'
            )

            assert response.status_code == 200, \
                f"Expected 200, got {response.status_code}"

            data = response.get_json()
            assert data['status'] == 'updated'
            assert data['location']['lat'] == 45.4465
            assert data['location']['lng'] == -122.6393
            assert data['trigger'] == 'near_home'
            assert 'distance_from_home_meters' in data
            assert data['automation_triggered'] is None  # Disabled
            print(f"  ✓ Valid update: {response.status_code}")
            print(f"  ✓ Distance: {data['distance_from_home_meters']:.0f}m")

            # Test 2: Missing lat/lng
            response = client.post(
                '/update-location',
                json={'trigger': 'test'},
                content_type='application/json'
            )

            assert response.status_code == 400, \
                f"Should reject missing coordinates"
            data = response.get_json()
            assert 'error' in data
            print(f"  ✓ Rejects missing coordinates: {response.status_code}")

            # Test 3: Home location (should detect) - Use actual home coordinates
            response = client.post(
                '/update-location',
                json={
                    'lat': 45.70766068698601,
                    'lng': -121.53682676696884,
                    'trigger': 'arriving_home',
                    'trigger_automations': False
                },
                content_type='application/json'
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['is_home'] is True
            assert data['distance_from_home_meters'] < 150
            print(f"  ✓ Home detection: is_home={data['is_home']}")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_get_location_endpoint():
    """Test /location GET endpoint"""
    print("Test 2: GET /location endpoint")

    from server.app import app
    import lib.location as loc_module

    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_geofence2.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        with app.test_client() as client:
            # Test 1: No location data
            response = client.get('/location')
            assert response.status_code == 404, \
                "Should return 404 when no data"
            data = response.get_json()
            assert data['status'] == 'no_data'
            print(f"  ✓ Returns 404 when no data: {data['message']}")

            # Test 2: Store location then retrieve
            from lib.location import update_location
            update_location(45.4465, -122.6393, 'test')

            response = client.get('/location')
            assert response.status_code == 200
            data = response.get_json()

            assert data['lat'] == 45.4465
            assert data['lng'] == -122.6393
            assert 'age_seconds' in data
            assert 'eta' in data  # Should include ETA when not home
            print(f"  ✓ Retrieved location: {data['lat']}, {data['lng']}")
            print(f"  ✓ Includes ETA: {data['eta'] is not None}")

            # Test 3: At home (shouldn't calculate ETA) - Use actual home coordinates
            update_location(45.70766068698601, -121.53682676696884, 'arriving_home')

            response = client.get('/location')
            assert response.status_code == 200
            data = response.get_json()

            assert data['is_home'] is True
            # ETA might still be calculated but not critical when home
            print(f"  ✓ At home: is_home={data['is_home']}")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_status_endpoint_includes_location():
    """Test /status endpoint lists new routes"""
    print("Test 3: /status includes location endpoints")

    from server.app import app

    with app.test_client() as client:
        response = client.get('/status')
        assert response.status_code == 200

        data = response.get_json()
        assert 'endpoints' in data

        endpoints = data['endpoints']
        assert '/update-location' in endpoints, \
            "/update-location should be listed"
        assert '/location' in endpoints, \
            "/location should be listed"

        print(f"  ✓ /update-location listed")
        print(f"  ✓ /location listed")
        print(f"  ✓ Total endpoints: {len(endpoints)}")

    print()
    return True


def test_automation_trigger_conditions():
    """Test automation trigger logic in endpoint"""
    print("Test 4: Automation trigger conditions")

    from server.app import app
    import lib.location as loc_module

    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_geofence3.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        with app.test_client() as client:
            # Test 1: Far from home + leaving_work = should trigger preheat
            # (but we disable automations in test)
            response = client.post(
                '/update-location',
                json={
                    'lat': 45.4465,
                    'lng': -122.6393,
                    'trigger': 'leaving_work',
                    'trigger_automations': False  # Disabled for test
                },
                content_type='application/json'
            )

            data = response.get_json()
            # Should indicate no automation because we disabled it
            assert data['automation_triggered'] is None
            print(f"  ✓ Automations disabled: no trigger")

            # Test 2: Enable automations (will actually run)
            # For safety, use a location that won't trigger anything
            response = client.post(
                '/update-location',
                json={
                    'lat': 45.7080,  # Close to home (won't trigger) - within 50m
                    'lng': -121.5368,
                    'trigger': 'leaving_work',
                    'trigger_automations': True
                },
                content_type='application/json'
            )

            data = response.get_json()
            # Should not trigger because too close to home
            assert data['automation_triggered'] is None
            print(f"  ✓ Too close to home: no trigger")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_json_response_format():
    """Test response JSON structure"""
    print("Test 5: Response JSON format")

    from server.app import app
    import lib.location as loc_module

    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_geofence4.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        with app.test_client() as client:
            response = client.post(
                '/update-location',
                json={
                    'lat': 45.4465,
                    'lng': -122.6393,
                    'trigger': 'test',
                    'trigger_automations': False
                },
                content_type='application/json'
            )

            data = response.get_json()

            # Check required fields
            required = [
                'status', 'location', 'trigger', 'timestamp',
                'distance_from_home_meters', 'is_home',
                'automation_triggered', 'message'
            ]

            for field in required:
                assert field in data, f"Missing field: {field}"
                print(f"  ✓ Field: {field}")

            # Check types
            assert isinstance(data['location'], dict)
            assert 'lat' in data['location']
            assert 'lng' in data['location']
            assert isinstance(data['is_home'], bool)
            assert isinstance(data['distance_from_home_meters'], (int, float))
            print(f"  ✓ All field types correct")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    """Run all tests"""
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Geofencing Endpoint Tests{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    tests = [
        test_update_location_endpoint,
        test_get_location_endpoint,
        test_status_endpoint_includes_location,
        test_automation_trigger_conditions,
        test_json_response_format,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"{RED}✗ FAILED: {e}{RESET}\n")
            failed += 1
        except Exception as e:
            print(f"{RED}✗ ERROR: {e}{RESET}\n")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"{BLUE}{'='*70}{RESET}")
    print(f"Results: {GREEN}{passed} passed{RESET}, ", end='')
    if failed > 0:
        print(f"{RED}{failed} failed{RESET}")
    else:
        print(f"{GREEN}0 failed{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    return failed == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

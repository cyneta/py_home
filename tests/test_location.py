#!/usr/bin/env python
"""
Tests for Location Tracking Module

Tests GPS calculations, location storage, and ETA logic.
"""

import os
import sys
import json
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from lib.location import (
    haversine_distance,
    update_location,
    get_location,
    should_trigger_arrival,
    LOCATION_FILE
)

# Test colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_haversine_distance():
    """Test GPS distance calculation using Haversine formula"""
    print("Test 1: Haversine Distance Calculation")

    # Hood River, OR to Milwaukie, OR
    hood_river = (45.7054, -121.5215)
    milwaukie = (45.4465, -122.6393)

    distance = haversine_distance(
        hood_river[0], hood_river[1],
        milwaukie[0], milwaukie[1]
    )

    # Expected: ~92km (57 miles) - actual straight-line distance
    expected_meters = 92000  # Approximate
    tolerance = 5000  # ±5km

    assert abs(distance - expected_meters) < tolerance, \
        f"Distance {distance}m not close to expected {expected_meters}m"

    print(f"  ✓ Hood River → Milwaukie: {distance/1000:.1f} km")

    # Test same location (should be 0)
    distance = haversine_distance(
        hood_river[0], hood_river[1],
        hood_river[0], hood_river[1]
    )

    assert distance == 0, "Same location should have 0 distance"
    print(f"  ✓ Same location: {distance} m")

    # Test known short distance
    # 100m north of Hood River
    nearby = (45.7063, -121.5215)
    distance = haversine_distance(
        hood_river[0], hood_river[1],
        nearby[0], nearby[1]
    )

    # Should be ~100m
    assert 90 < distance < 110, f"Expected ~100m, got {distance}m"
    print(f"  ✓ Short distance: {distance:.1f} m")

    print()
    return True


def test_update_location():
    """Test location storage and distance calculation"""
    print("Test 2: Update Location")

    # Use temporary file for testing
    import lib.location as loc_module
    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_location.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        # Update to Milwaukie, OR
        result = update_location(
            lat=45.4465,
            lng=-122.6393,
            trigger="test"
        )

        assert result['status'] == 'updated', "Status should be 'updated'"
        assert result['location']['lat'] == 45.4465
        assert result['location']['lng'] == -122.6393
        assert result['trigger'] == 'test'
        assert 'timestamp' in result
        assert 'distance_from_home_meters' in result
        assert result['is_home'] is False  # Should be far from Hood River

        print(f"  ✓ Location updated: {result['location']}")
        print(f"  ✓ Distance from home: {result['distance_from_home_meters']:.0f} m")
        print(f"  ✓ Is home: {result['is_home']}")

        # Verify file was created
        assert os.path.exists(temp_file), "Location file should exist"

        with open(temp_file, 'r') as f:
            data = json.load(f)

        assert data['lat'] == 45.4465
        assert data['trigger'] == 'test'
        print(f"  ✓ Data persisted to file")

        # Update to home location (should mark as home) - Use actual coordinates
        result = update_location(
            lat=45.70766068698601,
            lng=-121.53682676696884,
            trigger="arriving_home"
        )

        assert result['is_home'] is True, "Should be marked as home"
        assert result['distance_from_home_meters'] < 150
        print(f"  ✓ Home detection working: {result['distance_from_home_meters']:.1f} m")

        print()
        return True

    finally:
        # Restore original file path
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_get_location():
    """Test retrieving stored location"""
    print("Test 3: Get Location")

    import lib.location as loc_module
    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_location2.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        # Should return None when no data
        result = get_location()
        assert result is None, "Should return None when no data"
        print("  ✓ Returns None when no data")

        # Store a location
        update_location(45.4465, -122.6393, "test")

        # Retrieve it
        result = get_location()
        assert result is not None
        assert result['lat'] == 45.4465
        assert result['lng'] == -122.6393
        assert 'age_seconds' in result
        assert result['age_seconds'] >= 0
        print(f"  ✓ Retrieved location: {result['lat']}, {result['lng']}")
        print(f"  ✓ Age: {result['age_seconds']:.1f} seconds")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_should_trigger_arrival():
    """Test arrival automation trigger logic"""
    print("Test 4: Arrival Trigger Logic")

    import lib.location as loc_module
    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_location3.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        # Test 1: Leaving work - far away (should preheat)
        update_location(45.4465, -122.6393, "test")  # Milwaukie (far)
        should_trigger, automation_type = should_trigger_arrival("leaving_work")

        assert should_trigger is True, "Should trigger when far from home"
        assert automation_type == 'preheat', "Should trigger preheat"
        print(f"  ✓ Leaving work (far): {automation_type}")

        # Test 2: Near home trigger (<= 1km away)
        # Simulate location ~800m from home
        update_location(45.7148, -121.5368, "test")  # ~800m away
        should_trigger, automation_type = should_trigger_arrival("near_home")

        assert should_trigger is True, "Should trigger near home"
        assert automation_type == 'lights', "Should turn on lights"
        print(f"  ✓ Near home (800m): {automation_type}")

        # Test 3: Arriving home (within radius) - Use actual coordinates
        update_location(45.70766068698601, -121.53682676696884, "test")  # At home
        should_trigger, automation_type = should_trigger_arrival("arriving_home")

        assert should_trigger is True, "Should trigger at home"
        assert automation_type == 'full_arrival', "Should run full arrival"
        print(f"  ✓ Arriving home (0m): {automation_type}")

        # Test 4: Leaving work but close to home (shouldn't preheat) - adjusted for new coords
        update_location(45.7085, -121.5368, "test")  # ~100m away
        should_trigger, automation_type = should_trigger_arrival("leaving_work")

        assert should_trigger is False, "Should not trigger when close"
        print(f"  ✓ Leaving work (near home): no trigger")

        # Test 5: Unknown trigger
        should_trigger, automation_type = should_trigger_arrival("unknown_trigger")
        assert should_trigger is False
        assert automation_type is None
        print(f"  ✓ Unknown trigger: no action")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_location_file_format():
    """Test location file JSON format"""
    print("Test 5: Location File Format")

    import lib.location as loc_module
    original_file = loc_module.LOCATION_FILE
    temp_file = os.path.join(tempfile.gettempdir(), 'test_location4.json')
    loc_module.LOCATION_FILE = temp_file

    try:
        update_location(45.4465, -122.6393, "leaving_work")

        with open(temp_file, 'r') as f:
            data = json.load(f)

        # Check required fields
        required_fields = ['lat', 'lng', 'trigger', 'timestamp',
                          'distance_from_home_meters', 'is_home']

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  ✓ Field present: {field}")

        # Check data types
        assert isinstance(data['lat'], float)
        assert isinstance(data['lng'], float)
        assert isinstance(data['trigger'], str)
        assert isinstance(data['timestamp'], str)
        assert isinstance(data['distance_from_home_meters'], (int, float))
        assert isinstance(data['is_home'], bool)
        print(f"  ✓ All field types correct")

        # Check timestamp format (ISO 8601)
        from datetime import datetime
        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        print(f"  ✓ Timestamp valid: {data['timestamp']}")

        print()
        return True

    finally:
        loc_module.LOCATION_FILE = original_file
        if os.path.exists(temp_file):
            os.remove(temp_file)


def main():
    """Run all tests"""
    print(f"{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Location Tracking Tests{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

    tests = [
        test_haversine_distance,
        test_update_location,
        test_get_location,
        test_should_trigger_arrival,
        test_location_file_format,
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

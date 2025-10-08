#!/usr/bin/env python
"""
Test Google Maps Service

Tests travel time calculations with live API calls.
"""

import sys

def test():
    print("Testing Google Maps Service...\n")

    try:
        from services import get_travel_time
        from lib.config import config

        # Test 1: Get travel time between two cities
        print("Test 1: Chicago → Milwaukee")
        result = get_travel_time("Chicago, IL", "Milwaukee, WI")

        assert 'duration_minutes' in result, "Missing duration_minutes"
        assert 'distance_miles' in result, "Missing distance_miles"
        assert result['duration_minutes'] > 0, "Duration must be positive"
        assert result['distance_miles'] > 0, "Distance must be positive"

        print(f"✓ Duration: {result['duration_minutes']} min")
        print(f"✓ Distance: {result['distance_miles']:.1f} miles")
        print(f"✓ Traffic: {result.get('traffic_level', 'N/A')}")
        print()

        # Test 2: Use default origin from config (home location)
        print("Test 2: Home location → Milwaukee")
        home = config['locations']['home']
        origin = f"{home['lat']},{home['lng']}"
        result = get_travel_time(origin=origin, destination="Milwaukee, WI")

        assert 'duration_minutes' in result, "Missing duration_minutes"
        print(f"✓ Duration: {result['duration_minutes']} min")
        print(f"✓ Origin: {config['locations']['home']}")
        print()

        # Test 3: Invalid location handling
        print("Test 3: Invalid destination handling")
        try:
            result = get_travel_time("Chicago, IL", "INVALID_LOCATION_XYZ")
            if 'error' in result or result['duration_minutes'] == 0:
                print("✓ Invalid location handled gracefully")
            else:
                print("⚠ API accepted invalid location (might be real place)")
        except Exception as e:
            print(f"✓ Exception raised for invalid location: {type(e).__name__}")

        print()

        print("✓ All Google Maps tests passed!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)

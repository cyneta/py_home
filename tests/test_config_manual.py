"""
Manual test for configuration loading

This validates that config.yaml and .env are set up correctly

Usage:
    python tests/test_config_manual.py
"""

def test_config():
    """Test that configuration loads"""
    print("\n=== Testing Configuration ===\n")

    try:
        from utils.config import config, get

        print("✓ Configuration loaded successfully")
        print(f"\nAvailable sections: {list(config.keys())}")

        # Check for required sections
        required = ['nest', 'notifications', 'locations', 'google_maps']
        missing = [s for s in required if s not in config]

        if missing:
            print(f"\n⚠ Missing sections: {missing}")
        else:
            print("\n✓ All required sections present")

        # Test get() function
        print("\n--- Testing get() function ---")
        home_lat = get('locations.home.lat')
        print(f"Home latitude: {home_lat}")

        nest_project = get('nest.project_id')
        if nest_project:
            print(f"Nest project ID: {nest_project[:20]}...")
        else:
            print("⚠ Nest project ID not configured")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_config()

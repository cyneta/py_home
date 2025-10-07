#!/usr/bin/env python
"""
Nest Configuration Utility

Interactive setup for Google Nest thermostat integration.

This utility helps you:
1. Verify your Google Cloud credentials
2. Test OAuth token refresh
3. Validate device access
4. Generate config.yaml entries

Usage:
    python -m components.nest.config
"""

import os
import sys
import json
from pathlib import Path


def print_header(text):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")


def check_credentials():
    """Check if credentials file exists"""
    creds_path = Path(__file__).parent.parent.parent / 'config' / 'google_credentials.json'

    if not creds_path.exists():
        print(f"❌ Credentials file not found: {creds_path}")
        print("\nSetup instructions:")
        print("1. Go to https://console.cloud.google.com")
        print("2. Enable Smart Device Management API")
        print("3. Create OAuth 2.0 credentials")
        print("4. Download credentials.json")
        print(f"5. Save as: {creds_path}")
        return False

    print(f"✓ Found credentials: {creds_path}")
    return True


def check_token():
    """Check if OAuth token exists and is valid"""
    token_path = Path(__file__).parent.parent.parent / 'config' / 'nest_token.json'

    if not token_path.exists():
        print(f"❌ Token file not found: {token_path}")
        print("\nYou need to run the OAuth flow to get a token.")
        print("See docs/NEST_API_SETUP.md for instructions.")
        return False

    print(f"✓ Found token: {token_path}")

    # Load and check expiry
    with open(token_path, 'r') as f:
        token_data = json.load(f)

    if 'refresh_token' in token_data:
        print("✓ Refresh token present")
    else:
        print("⚠ No refresh token (token will expire)")

    if 'expiry' in token_data:
        from datetime import datetime
        expiry = datetime.fromisoformat(token_data['expiry'].replace('Z', '+00:00'))
        now = datetime.now(expiry.tzinfo)

        if expiry > now:
            print(f"✓ Token valid until {expiry.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"⚠ Token expired on {expiry.strftime('%Y-%m-%d %H:%M')}")
            print("  (Will attempt refresh on next use)")

    return True


def test_connection():
    """Test connection to Nest API"""
    print("\nTesting Nest API connection...")

    try:
        from components.nest import get_status

        status = get_status()

        print("\n✓ Successfully connected to Nest!")
        print(f"\nDevice Status:")
        print(f"  Current Temperature: {status['current_temp_f']:.1f}°F")
        print(f"  Humidity: {status['current_humidity']}%")
        print(f"  Mode: {status['mode']}")
        print(f"  HVAC Status: {status['hvac_status']}")

        if status['heat_setpoint_f']:
            print(f"  Heat Setpoint: {status['heat_setpoint_f']:.1f}°F")
        if status['cool_setpoint_f']:
            print(f"  Cool Setpoint: {status['cool_setpoint_f']:.1f}°F")

        return True

    except Exception as e:
        print(f"\n❌ Failed to connect: {e}")
        print("\nTroubleshooting:")
        print("1. Check that credentials.json is valid")
        print("2. Run OAuth flow to get fresh token")
        print("3. Verify project_id and device_id in config.yaml")
        print("4. Check that Smart Device Management API is enabled")
        return False


def check_config():
    """Check config.yaml settings"""
    print("\nChecking config.yaml settings...")

    try:
        from lib.config import config

        if 'nest' not in config:
            print("❌ No 'nest' section in config.yaml")
            return False

        nest_config = config['nest']

        # Check required fields
        required = ['project_id', 'device_id']
        missing = [f for f in required if f not in nest_config]

        if missing:
            print(f"❌ Missing required fields: {', '.join(missing)}")
            return False

        print("✓ Config section exists")
        print(f"  Project ID: {nest_config['project_id']}")
        print(f"  Device ID: {nest_config['device_id'][:30]}...")

        return True

    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def generate_config_template():
    """Generate config.yaml template"""
    print("\nConfig Template:")
    print("-" * 70)
    print("""
nest:
  project_id: "YOUR_PROJECT_ID"              # From Google Cloud Console
  device_id: "enterprises/.../devices/..."   # From device discovery
  credentials_file: "google_credentials.json"
  token_file: "nest_token.json"
""")
    print("-" * 70)


def main():
    """Run Nest configuration utility"""
    print_header("Nest Thermostat Configuration Utility")

    print("This utility will help you set up your Nest thermostat integration.\n")

    # Step 1: Check credentials
    print_header("Step 1: Check Google Cloud Credentials")
    has_creds = check_credentials()

    # Step 2: Check token
    print_header("Step 2: Check OAuth Token")
    has_token = check_token()

    # Step 3: Check config
    print_header("Step 3: Check Configuration")
    has_config = check_config()

    # Step 4: Test connection (if everything present)
    if has_creds and has_token and has_config:
        print_header("Step 4: Test Connection")
        connection_ok = test_connection()
    else:
        print_header("Step 4: Test Connection")
        print("⊘ Skipped (missing credentials, token, or config)")
        connection_ok = False

    # Summary
    print_header("Summary")

    if connection_ok:
        print("✅ Nest thermostat is fully configured and working!")
        print("\nYou can now use:")
        print("  - python -m components.nest.demo")
        print("  - python -m components.nest.test")
        print("  - Automation scripts (leaving_home.py, etc.)")

    elif has_creds and has_token and has_config:
        print("⚠️  Configuration exists but connection failed.")
        print("\nNext steps:")
        print("1. Verify project_id and device_id are correct")
        print("2. Run OAuth flow again to refresh token")
        print("3. Check API is enabled in Google Cloud Console")

    else:
        print("❌ Nest thermostat is not configured.")
        print("\nWhat's missing:")
        if not has_creds:
            print("  ❌ Google Cloud credentials")
        if not has_token:
            print("  ❌ OAuth token")
        if not has_config:
            print("  ❌ Config.yaml settings")

        print("\nSetup guide:")
        print("See docs/NEST_API_SETUP.md for complete instructions.")

        generate_config_template()

    print("\n" + "="*70 + "\n")

    return 0 if connection_ok else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python
"""
Test Nest API Authentication

Diagnoses Nest OAuth token issues and provides steps to fix them.
"""

import requests
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import config

def test_nest_auth():
    """Test Nest API authentication and provide diagnostics"""

    print("=" * 60)
    print("Nest API Authentication Diagnostics")
    print("=" * 60)

    # Check if credentials are configured
    print("\n1. Checking configuration...")

    nest_config = config.get('nest', {})

    required_fields = ['client_id', 'client_secret', 'refresh_token', 'project_id', 'device_id']
    missing = []

    for field in required_fields:
        value = nest_config.get(field)
        if not value or value.startswith('${'):
            missing.append(field)
            print(f"   ❌ {field}: NOT SET (env var not populated)")
        else:
            # Show first/last 4 chars for security
            display = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
            print(f"   ✓ {field}: {display}")

    if missing:
        print(f"\n❌ Missing credentials: {', '.join(missing)}")
        print("\nTo fix:")
        print("1. Check config/.env file exists and has these variables set:")
        for field in missing:
            print(f"   NEST_{field.upper()}=your_value_here")
        print("\n2. If you don't have a refresh token, you need to:")
        print("   - Visit Google Cloud Console")
        print("   - Enable Smart Device Management API")
        print("   - Create OAuth 2.0 credentials")
        print("   - Run OAuth flow to get refresh token")
        print("\nSee: docs/NEST_API_SETUP.md")
        return False

    # Try to refresh the token
    print("\n2. Testing token refresh...")

    TOKEN_URL = "https://oauth2.googleapis.com/token"

    try:
        resp = requests.post(TOKEN_URL, data={
            'client_id': nest_config['client_id'],
            'client_secret': nest_config['client_secret'],
            'refresh_token': nest_config['refresh_token'],
            'grant_type': 'refresh_token'
        })

        if resp.status_code == 200:
            data = resp.json()
            print(f"   ✓ Token refresh successful!")
            print(f"   ✓ Access token: {data['access_token'][:10]}...")
            print(f"   ✓ Expires in: {data.get('expires_in', 3600)} seconds")
            print("\n✅ Nest authentication is working!")
            return True
        else:
            print(f"   ❌ Token refresh failed: {resp.status_code}")
            print(f"   Response: {resp.text}")

            if resp.status_code == 400:
                error_data = resp.json()
                error = error_data.get('error', 'unknown')
                error_desc = error_data.get('error_description', 'No description')

                print(f"\n❌ Error: {error}")
                print(f"   Description: {error_desc}")

                if error == 'invalid_grant':
                    print("\n🔧 Fix: Your refresh token has expired or been revoked.")
                    print("   You need to re-authorize the app:")
                    print("   1. Go to Google Cloud Console → APIs & Services → Credentials")
                    print("   2. Find your OAuth 2.0 Client ID")
                    print("   3. Use OAuth Playground or custom script to get new refresh token")
                    print("   4. Update NEST_REFRESH_TOKEN in config/.env")
                elif error == 'invalid_client':
                    print("\n🔧 Fix: Your client_id or client_secret is incorrect.")
                    print("   1. Check Google Cloud Console → APIs & Services → Credentials")
                    print("   2. Verify NEST_CLIENT_ID and NEST_CLIENT_SECRET in config/.env")

            return False

    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

if __name__ == '__main__':
    success = test_nest_auth()
    sys.exit(0 if success else 1)

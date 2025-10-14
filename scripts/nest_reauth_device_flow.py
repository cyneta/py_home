#!/usr/bin/env python
"""
Nest API Re-authentication Script (Device Flow)

Alternative authentication method that doesn't require redirect URIs.
This uses the OAuth device authorization flow.
"""

import sys
import os
import requests
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import config

# Get credentials from config
nest_config = config.get('nest', {})
CLIENT_ID = nest_config.get('client_id')
CLIENT_SECRET = nest_config.get('client_secret')

# OAuth settings
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/sdm.service"


def get_refresh_token_device_flow():
    """Run OAuth device flow to get a new refresh token"""

    print("=" * 70)
    print("Nest API Re-authentication (Device Flow)")
    print("=" * 70)

    # Validate credentials
    if not all([CLIENT_ID, CLIENT_SECRET]):
        print("\n❌ Error: Missing Nest credentials in config")
        print("   Check config/.env for:")
        print("   - NEST_CLIENT_ID")
        print("   - NEST_CLIENT_SECRET")
        return False

    print(f"\n✓ Client ID: {CLIENT_ID[:20]}...")

    # Step 1: Request device code
    print("\n" + "=" * 70)
    print("Step 1: Request device authorization")
    print("=" * 70)

    try:
        resp = requests.post(DEVICE_CODE_URL, data={
            'client_id': CLIENT_ID,
            'scope': SCOPE
        })

        if resp.status_code != 200:
            print(f"\n❌ Device code request failed: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False

        device_data = resp.json()
        device_code = device_data['device_code']
        user_code = device_data['user_code']
        verification_url = device_data['verification_url']
        expires_in = device_data['expires_in']
        interval = device_data.get('interval', 5)

        print(f"\n✓ Device code received")
        print(f"\n" + "=" * 70)
        print("Step 2: Authorize on another device")
        print("=" * 70)
        print(f"\n1. Go to: {verification_url}")
        print(f"2. Enter this code: {user_code}")
        print(f"3. Sign in with matthew.g.wheeler@gmail.com")
        print(f"4. Grant permissions")
        print(f"\nCode expires in {expires_in} seconds")
        print(f"\nWaiting for authorization...")

        # Step 2: Poll for authorization
        start_time = time.time()
        while time.time() - start_time < expires_in:
            time.sleep(interval)

            resp = requests.post(TOKEN_URL, data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'device_code': device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            })

            if resp.status_code == 200:
                # Success!
                tokens = resp.json()
                access_token = tokens.get('access_token')
                refresh_token = tokens.get('refresh_token')

                if not refresh_token:
                    print("\n❌ No refresh token in response")
                    print("   Response:", tokens)
                    return False

                print("\n✅ SUCCESS! New tokens received:")
                print(f"\nAccess Token: {access_token[:20]}...")
                print(f"Refresh Token: {refresh_token}")

                # Show update instructions
                print("\n" + "=" * 70)
                print("Step 3: Update your configuration")
                print("=" * 70)
                print("\nUpdate this line in config/.env:")
                print(f"\nNEST_REFRESH_TOKEN={refresh_token}")

                env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', '.env')
                print(f"\nFile location: {env_file}")

                print("\nAfter updating, restart Flask to use the new token:")
                print("  sudo systemctl restart py_home")

                return True

            elif resp.status_code == 428:
                # Still waiting for user authorization
                print(".", end="", flush=True)
                continue

            else:
                # Error
                error_data = resp.json()
                error = error_data.get('error', 'unknown')

                if error == 'authorization_pending':
                    print(".", end="", flush=True)
                    continue
                elif error == 'slow_down':
                    interval += 5
                    continue
                elif error == 'expired_token':
                    print("\n\n❌ Authorization code expired")
                    return False
                elif error == 'access_denied':
                    print("\n\n❌ Authorization denied by user")
                    return False
                else:
                    print(f"\n\n❌ Error: {error}")
                    print(f"   Response: {resp.text}")
                    return False

        print("\n\n❌ Authorization timed out")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = get_refresh_token_device_flow()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)

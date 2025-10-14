#!/usr/bin/env python
"""
Nest API Re-authentication Script (Standard Google OAuth)

Uses standard Google OAuth flow instead of Nest-specific endpoint.
"""

import sys
import os
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import config

# Get credentials from config
nest_config = config.get('nest', {})
CLIENT_ID = nest_config.get('client_id')
CLIENT_SECRET = nest_config.get('client_secret')

# OAuth settings - Use standard Google OAuth instead of Nest URL
REDIRECT_URI = "http://localhost:8080"
SCOPE = "https://www.googleapis.com/auth/sdm.service"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"  # Standard Google OAuth
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Global to store the authorization code
auth_code = None


class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""

    def do_GET(self):
        global auth_code

        # Parse the authorization code from the callback URL
        query = urlparse(self.path).query
        params = parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]

            # Send success page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = """
            <html>
            <head><title>Authorization Complete</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: green;">✓ Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        elif 'error' in params:
            error = params['error'][0]

            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            html = f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: Arial; padding: 50px; text-align: center;">
                <h1 style="color: red;">✗ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>Check the terminal for more information.</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def get_refresh_token():
    """Run OAuth flow to get a new refresh token"""

    print("=" * 70)
    print("Nest API Re-authentication (Standard Google OAuth)")
    print("=" * 70)

    # Validate credentials
    if not all([CLIENT_ID, CLIENT_SECRET]):
        print("\n❌ Error: Missing Nest credentials in config")
        print("   Check config/.env for:")
        print("   - NEST_CLIENT_ID")
        print("   - NEST_CLIENT_SECRET")
        return False

    print(f"\n✓ Client ID: {CLIENT_ID[:20]}...")

    # Build authorization URL
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': SCOPE,
        'access_type': 'offline',  # Request refresh token
        'prompt': 'consent',  # Force consent screen to get refresh token
        'login_hint': 'matthew.g.wheeler@gmail.com'
    }

    auth_url_full = AUTH_URL + "?" + urlencode(auth_params)

    print("\n" + "=" * 70)
    print("Step 1: Authorize the application")
    print("=" * 70)
    print("\nA browser window will open. Please:")
    print("1. Sign in with matthew.g.wheeler@gmail.com")
    print("2. Grant permission to access your Nest devices")
    print("3. You'll be redirected back to this script automatically")
    print("\nStarting local server on http://localhost:8080...")

    # Start local server to receive callback
    server = HTTPServer(('localhost', 8080), OAuthHandler)

    # Open browser
    print("\nOpening browser...")
    webbrowser.open(auth_url_full)

    # Wait for callback (with timeout)
    print("Waiting for authorization...\n")

    timeout = 120  # 2 minutes
    server.timeout = timeout

    try:
        server.handle_request()
    except KeyboardInterrupt:
        print("\n\n❌ Authorization cancelled by user")
        return False

    server.server_close()

    if not auth_code:
        print("\n❌ No authorization code received")
        print("   The authorization may have failed or timed out")
        return False

    print("\n✓ Authorization code received")

    # Exchange code for tokens
    print("\n" + "=" * 70)
    print("Step 2: Exchange code for refresh token")
    print("=" * 70)

    try:
        resp = requests.post(TOKEN_URL, data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        })

        if resp.status_code != 200:
            print(f"\n❌ Token exchange failed: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False

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

    except Exception as e:
        print(f"\n❌ Error exchanging code for tokens: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = get_refresh_token()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)

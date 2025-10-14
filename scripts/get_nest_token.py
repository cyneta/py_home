#!/usr/bin/env python
"""
Nest API Refresh Token Setup (Original Working Method)

This is the ORIGINAL method that successfully set up Nest authentication.
It uses manual code copy/paste from the browser redirect URL.

History: This script was created on 2025-10-06 and successfully used to get
the initial refresh token. It was later deleted during a refactor (commit d64a6bd)
but has been restored because it's the proven working method.

Steps:
1. Run this script
2. Open the URL it provides in your browser
3. Sign in with matthew.g.wheeler@gmail.com (NOT cyneta!)
4. Authorize the app (you may see "This app isn't verified" - click Advanced > Continue)
5. After authorization, you'll be redirected to https://www.google.com/?code=XXXXX&scope=...
6. Copy the 'code' parameter from the URL bar
7. Paste it back into this script
8. Script exchanges code for refresh token
9. Save the refresh token to config/.env

NOTE: This method uses https://www.google.com as the redirect URI, which is
already configured in the OAuth client. No localhost server needed!
"""

import requests
import sys

# OAuth credentials (from config/.env)
CLIENT_ID = "493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com"
CLIENT_SECRET = "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"
PROJECT_ID = "b8e3fce2-20f4-471f-80e3-d08be2432b75"

REDIRECT_URI = "https://www.google.com"
SCOPE = "https://www.googleapis.com/auth/sdm.service"

def main():
    print("\n" + "="*70)
    print("Nest API Token Setup (Original Working Method)")
    print("="*70)
    print("\nThis is the method that ORIGINALLY WORKED to set up Nest auth.")
    print("It uses manual code copy/paste - proven to work!")
    print()

    # Step 1: Build and show authorization URL
    auth_url = (
        f"https://nestservices.google.com/partnerconnections/{PROJECT_ID}/auth"
        f"?redirect_uri={REDIRECT_URI}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&scope={SCOPE}"
    )

    print("="*70)
    print("Step 1: Open this URL in your browser")
    print("="*70)
    print()
    print(auth_url)
    print()
    print("IMPORTANT: Sign in with matthew.g.wheeler@gmail.com (NOT cyneta!)")
    print()
    print("You may see 'This app isn't verified' - that's OK:")
    print("  Click 'Advanced' > 'Go to Home Automation (unsafe)' or similar")
    print()
    print("After authorizing, you'll be redirected to:")
    print("  https://www.google.com/?code=XXXXX&scope=...")
    print()
    print("="*70)

    # Step 2: Get authorization code from user
    print("\nStep 2: Copy the code from the redirect URL")
    print("="*70)
    auth_code = input("\nPaste the 'code' parameter here: ").strip()

    if not auth_code:
        print("\n❌ Error: No code provided")
        return 1

    # Remove common formatting issues
    auth_code = auth_code.split('&')[0]  # Remove anything after &
    auth_code = auth_code.split('#')[0]  # Remove fragment

    print(f"\n✓ Received code: {auth_code[:20]}...")

    # Step 3: Exchange code for tokens
    print("\n" + "="*70)
    print("Step 3: Exchanging code for tokens...")
    print("="*70)

    try:
        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        })

        if resp.status_code != 200:
            print(f"\n❌ Error: Token exchange failed ({resp.status_code})")
            print(f"Response: {resp.text}")
            print("\nCommon issues:")
            print("- Code already used (run script again, get a fresh code)")
            print("- Code expired (codes expire in ~10 minutes)")
            print("- Wrong Google account used (must use matthew.g.wheeler@gmail.com)")
            return 1

        tokens = resp.json()

        if 'refresh_token' not in tokens:
            print("\n❌ Error: No refresh token in response")
            print(f"Response: {tokens}")
            print("\nThis usually means:")
            print("- You need to revoke existing access and re-authorize")
            print("- Try going to https://myaccount.google.com/permissions")
            print("- Remove 'Sherman Automation' if it exists")
            print("- Run this script again")
            return 1

        print("\n✅ SUCCESS! Tokens received")
        print("\n" + "="*70)
        print("REFRESH TOKEN (save to config/.env):")
        print("="*70)
        print(f"\n{tokens['refresh_token']}\n")
        print("="*70)

        print(f"\nAccess token (expires in {tokens['expires_in']} seconds):")
        print(f"{tokens['access_token'][:50]}...")

        print("\n" + "="*70)
        print("Next Steps:")
        print("="*70)
        print("\n1. Copy the refresh token above")
        print("2. Edit config/.env and update:")
        print(f"   NEST_REFRESH_TOKEN={tokens['refresh_token']}")
        print("\n3. Test authentication:")
        print("   python scripts/test_nest_auth.py")
        print("\n4. Deploy to Raspberry Pi:")
        print("   scp config/.env pi@<pi-ip>:/home/pi/py_home/config/")
        print("   ssh pi@<pi-ip>")
        print("   sudo systemctl restart py_home")
        print("\n5. Verify automations work:")
        print("   curl -X POST http://localhost:5000/api/good-morning")
        print()

        return 0

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error: Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)

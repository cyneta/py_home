"""
Helper script to get Nest API refresh token

This is a one-time setup script to obtain your refresh token.

Steps:
1. Run this script
2. Open the URL in your browser
3. Authorize the app
4. Copy the code from the redirect URL
5. Paste it when prompted
6. Script will exchange code for tokens
7. Save the refresh token to config/.env
"""

import requests

# Your OAuth credentials
CLIENT_ID = "493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com"
CLIENT_SECRET = "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"
PROJECT_ID = "b8e3fce2-20f4-471f-80e3-d08be2432b75"

def main():
    print("\n=== Nest API Token Setup ===\n")

    # Step 1: Show authorization URL
    auth_url = (
        f"https://nestservices.google.com/partnerconnections/{PROJECT_ID}/auth"
        f"?redirect_uri=https://www.google.com"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&client_id={CLIENT_ID}"
        f"&response_type=code"
        f"&scope=https://www.googleapis.com/auth/sdm.service"
    )

    print("Step 1: Open this URL in your browser:\n")
    print(auth_url)
    print("\nYou'll see 'This app isn't verified' - click Advanced > Go to Home Automation")
    print("Authorize the app")
    print("\nYou'll be redirected to https://www.google.com/?code=XXXXX&scope=...")
    print("\n")

    # Step 2: Get authorization code from user
    auth_code = input("Paste the 'code' parameter from the URL here: ").strip()

    if not auth_code:
        print("Error: No code provided")
        return

    print(f"\nReceived code: {auth_code[:20]}...")

    # Step 3: Exchange code for tokens
    print("\nExchanging code for tokens...")

    try:
        resp = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": "https://www.google.com"
        })

        resp.raise_for_status()
        tokens = resp.json()

        print("\n✓ Success!\n")
        print("="*60)
        print("REFRESH TOKEN (save this to config/.env):")
        print("="*60)
        print(tokens['refresh_token'])
        print("="*60)

        print(f"\nAccess token (expires in {tokens['expires_in']} seconds):")
        print(tokens['access_token'][:50] + "...")

        print("\n\nNext steps:")
        print("1. Copy the refresh token above")
        print("2. Add to config/.env:")
        print(f"   NEST_REFRESH_TOKEN={tokens['refresh_token']}")
        print("\n3. Get your device ID:")
        print(f"   Run: python scripts/list_nest_devices.py")

    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Error: {e}")
        print(f"Response: {e.response.text}")
        print("\nCommon issues:")
        print("- Code already used (get a new one)")
        print("- Code expired (valid for 10 minutes)")
        print("- Wrong redirect_uri")

if __name__ == '__main__':
    main()

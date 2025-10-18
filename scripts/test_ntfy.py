#!/usr/bin/env python3
"""
Test ntfy notification delivery

Usage:
    python3 scripts/test_ntfy.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.notifications import send, send_automation_summary

def main():
    print("Testing ntfy notifications...\n")

    # Test 1: Simple notification
    print("Test 1: Simple notification")
    result = send("🧪 Test notification from py_home", title="ntfy Test", priority=0)
    print(f"  Result: {'✓ Success' if result else '✗ Failed'}\n")

    # Test 2: Notification with emoji in title (should strip emoji from title, keep in body)
    print("Test 2: Emoji handling")
    result = send("This is a test message", title="🏡 Home Test", priority=0)
    print(f"  Result: {'✓ Success' if result else '✗ Failed'}\n")

    # Test 3: Automation summary format (like real automations use)
    print("Test 3: Automation summary")
    result = send_automation_summary(
        "🚗 Left Home",
        ["Nest set to ECO mode", "All lights turned off", "House secured"]
    )
    print(f"  Result: {'✓ Success' if result else '✗ Failed'}\n")

    # Test 4: High priority
    print("Test 4: High priority notification")
    result = send("⚠️ This is a high priority test", title="Priority Test", priority=1)
    print(f"  Result: {'✓ Success' if result else '✗ Failed'}\n")

    print("=" * 60)
    print("Check your phone's ntfy.sh subscription!")
    print("Topic: py_home_7h3k2m9x")
    print("=" * 60)

if __name__ == '__main__':
    main()

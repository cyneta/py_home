#!/usr/bin/env python
"""
Test Notification Priorities

Sends test notifications at different priority levels to verify:
- Priority 0 (info) -> ntfy priority 3 (default)
- Priority 1 (urgent) -> ntfy priority 5 (urgent, bypass DND)

Usage:
    python scripts/test_priority_notifications.py
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.notifications import send_info, send_urgent

def main():
    print("Testing notification priority levels...")
    print()

    # Test priority 0 (info)
    print("1. Sending priority 0 (info) notification...")
    print("   Expected: Normal notification sound")
    print("   ntfy priority: 3 (default)")
    result1 = send_info("Priority 0 test - This should be a normal notification", "Test Info")
    print(f"   Result: {'✓ Sent' if result1 else '✗ Failed'}")
    print()

    # Wait between notifications
    print("   Waiting 3 seconds...")
    time.sleep(3)
    print()

    # Test priority 1 (urgent)
    print("2. Sending priority 1 (urgent) notification...")
    print("   Expected: Urgent notification, bypass DND")
    print("   ntfy priority: 5 (urgent)")
    result2 = send_urgent("Priority 1 test - This should bypass Do Not Disturb", "Test Urgent")
    print(f"   Result: {'✓ Sent' if result2 else '✗ Failed'}")
    print()

    # Summary
    print("=" * 50)
    print("Test complete!")
    print()
    print("Check your phone notifications:")
    print("  ✓ First notification should be normal priority")
    print("  ✓ Second notification should be urgent (bypass DND)")
    print()
    print("Both notifications should be delivered successfully.")
    print("=" * 50)

    # Return error if either failed
    if not (result1 and result2):
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())

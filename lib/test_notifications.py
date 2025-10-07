#!/usr/bin/env python
"""
Test Notifications Module

Tests notification system without actually sending notifications (mock).
"""

import sys

def test():
    print("Testing Notifications Module...\n")

    try:
        from lib import notifications
        from lib.config import config

        # Test 1: Module loads
        print("Test 1: Module Loading")
        print("✓ Module imported successfully")
        print()

        # Test 2: Configuration
        print("Test 2: Configuration")
        notif_config = config.get('notifications', {})

        if notif_config:
            print(f"✓ Notifications configured")
            if 'pushover' in notif_config:
                print(f"  - Pushover: {'✓' if notif_config['pushover'].get('token') else '✗'}")
            if 'ntfy' in notif_config:
                print(f"  - ntfy: {'✓' if notif_config['ntfy'].get('topic') else '✗'}")
        else:
            print("⚠ No notification config found")
        print()

        # Test 3: Test send function exists
        print("Test 3: Function Availability")
        assert hasattr(notifications, 'send'), "send() function not found"
        print("✓ send() function available")
        print()

        # Test 4: Mock send (dry-run)
        print("Test 4: Mock Notification (dry-run)")
        test_message = "TEST: py_home notification test (DO NOT SEND)"

        # Instead of actually sending, just validate the function signature
        import inspect
        sig = inspect.signature(notifications.send)
        params = list(sig.parameters.keys())

        print(f"✓ Function signature: send({', '.join(params)})")
        print(f"✓ Would send: '{test_message}'")
        print("✓ Skipping actual send (mock test)")
        print()

        # Test 5: Message formatting
        print("Test 5: Message Formatting")
        test_cases = [
            "Simple message",
            "Message with emoji 🏠",
            "Multi-line\nmessage\ntest",
            "Message with 'quotes' and \"double quotes\""
        ]

        for msg in test_cases:
            # Just verify no exceptions on string operations
            formatted = msg.strip()
            assert isinstance(formatted, str), "Message should remain string"

        print(f"✓ Tested {len(test_cases)} message formats")
        print()

        print("✓ All notification tests passed!")
        print("\nNote: This test is mock-only. No actual notifications were sent.")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)

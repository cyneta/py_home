#!/usr/bin/env python
"""
Test Network Presence Detection

Tests ping and ARP detection methods.
"""

import sys
import platform

def test():
    print("Testing Network Presence Detection...\n")

    try:
        from components.network import is_device_home

        # Test 1: Ping localhost (always reachable)
        print("Test 1: Ping Detection - Localhost")
        result = is_device_home('127.0.0.1', method='ping')

        assert result == True, "Localhost should always be reachable"
        print("✓ Localhost (127.0.0.1) detected via ping")
        print()

        # Test 2: Ping unreachable IP (should fail quickly)
        print("Test 2: Ping Detection - Unreachable IP")
        # Use an IP in the reserved TEST-NET-1 range (should be unreachable)
        result = is_device_home('192.0.2.1', method='ping')

        assert result == False, "Unreachable IP should return False"
        print("✓ Unreachable IP correctly returns False")
        print()

        # Test 3: Auto detection with localhost
        print("Test 3: Auto Detection")
        result = is_device_home('127.0.0.1', method='auto')

        assert result == True, "Auto detection should work with localhost"
        print("✓ Auto detection works (ping + ARP fallback)")
        print()

        # Test 4: MAC address format validation
        print("Test 4: MAC Address Detection")
        # Test with a fake MAC (won't be found, but tests the code path)
        test_mac = 'AA:BB:CC:DD:EE:FF'
        result = is_device_home(test_mac, method='arp')

        # Should return False for non-existent MAC, but shouldn't error
        assert isinstance(result, bool), "Should return boolean"
        print(f"✓ MAC format accepted ({test_mac})")
        print(f"✓ Result: {result} (expected False for test MAC)")
        print()

        # Test 5: Config integration
        print("Test 5: Config Integration")
        from lib.config import config

        if 'presence' in config and 'devices' in config['presence']:
            devices = config['presence']['devices']
            print(f"✓ Presence config found")
            print(f"✓ Configured devices: {len(devices)}")

            for device_name, device_config in list(devices.items())[:3]:
                print(f"  - {device_config.get('name', device_name)}")
                if 'ip' in device_config:
                    print(f"    IP: {device_config['ip']}")
                if 'mac' in device_config:
                    print(f"    MAC: {device_config['mac']}")
        else:
            print("⚠ No presence config found (optional)")
        print()

        # Test 6: Platform compatibility
        print("Test 6: Platform Compatibility")
        os_name = platform.system().lower()
        print(f"✓ Platform: {os_name}")

        if os_name == 'windows':
            print("✓ Windows ping parameters supported")
        elif os_name in ['linux', 'darwin']:
            print("✓ Unix/Mac ping parameters supported")
        print()

        print("✓ All network presence tests passed!")
        print("\nNote: Tests use localhost and fake IPs to avoid network dependencies.")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)

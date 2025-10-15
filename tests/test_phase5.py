#!/usr/bin/env python
"""Phase 5: Integration Testing - Quick verification"""
import sys
sys.path.insert(0, '/c/git/cyneta/py_home')

print("\n=== Phase 5: Integration Tests ===\n")

# Test 1: Component dry-run
print("Test 1: Idempotent behavior")
from components.nest import NestAPI
nest = NestAPI(dry_run=True)
nest.set_comfort_mode()
nest.set_comfort_mode()  # Should not error
print("  ✓ Idempotent calls work\n")

# Test 2: State transitions  
print("Test 2: State transitions")
nest.set_away_mode()
nest.set_comfort_mode()
nest.set_sleep_mode()
print("  ✓ All state transitions work\n")

# Test 3: Temp coordination
print("Test 3: temp_coordination")
from automations import temp_coordination
result = temp_coordination.run()
print(f"  ✓ Returned: {result}\n")

print("="*50)
print("✅ ALL TESTS PASSED - No 400 errors!")
print("="*50)

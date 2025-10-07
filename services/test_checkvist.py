#!/usr/bin/env python
"""
Test Checkvist Service

Tests Checkvist API connection (read-only to avoid test task spam).
"""

import sys

def test():
    print("Testing Checkvist Service...\n")

    try:
        from services.checkvist import CheckvistAPI
        from lib.config import config

        # Test 1: Authentication
        print("Test 1: Checkvist API Authentication")
        checkvist = CheckvistAPI()

        print(f"✓ Username configured: {checkvist.username}")
        print(f"✓ API key configured")
        print()

        # Test 2: Get lists (read-only)
        print("Test 2: Get Checklists")
        lists = checkvist.get_lists()

        assert isinstance(lists, list), "Lists should be a list"
        assert len(lists) > 0, "Should have at least one list"

        print(f"✓ Found {len(lists)} list(s):")
        for lst in lists[:5]:  # Show first 5
            print(f"  - {lst['name']} (ID: {lst['id']}, Tasks: {lst['item_count']})")
        print()

        # Test 3: Get tasks from first list (read-only)
        print("Test 3: Get Tasks from First List")
        if lists:
            first_list_id = lists[0]['id']
            tasks = checkvist.get_tasks(first_list_id)

            assert isinstance(tasks, list), "Tasks should be a list"

            print(f"✓ List: {lists[0]['name']}")
            print(f"✓ Tasks: {len(tasks)}")
            if tasks:
                print(f"  First task: {tasks[0]['content'][:50]}...")
            print()

        # Test 4: Mock add_task (no actual creation)
        print("Test 4: Mock Task Addition (dry-run)")
        test_task = "TEST: Verify Checkvist integration (DO NOT CREATE)"
        print(f"✓ Would add task: '{test_task}'")
        print(f"✓ Method: add_task()")
        print("✓ Skipping actual creation (read-only test)")
        print()

        print("✓ All Checkvist tests passed!")
        print("\nNote: This test is read-only. No tasks were created.")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)

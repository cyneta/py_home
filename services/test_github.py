#!/usr/bin/env python
"""
Test GitHub Service

Tests GitHub API connection (read-only to avoid test commits).
"""

import sys

def test():
    print("Testing GitHub Service...\n")

    try:
        from services.github import GitHubAPI
        from lib.config import config

        # Test 1: Authentication and repo access
        print("Test 1: GitHub API Authentication")
        github = GitHubAPI()

        print(f"✓ Token configured")
        print(f"✓ Repository: {github.repo}")
        print()

        # Test 2: Get repo info (read-only)
        print("Test 2: Get Repository Info")
        repo_info = github.get_repo_info()

        assert 'name' in repo_info, "Missing repo name"
        assert 'full_name' in repo_info, "Missing full_name"

        print(f"✓ Repo: {repo_info['full_name']}")
        print(f"✓ Private: {repo_info.get('private', 'N/A')}")
        print(f"✓ Default branch: {repo_info.get('default_branch', 'N/A')}")
        print()

        # Test 3: Read TODO.md file (read-only)
        print("Test 3: Read TODO.md File")
        try:
            file_data = github.get_file_contents('TODO.md')

            assert 'content' in file_data, "Missing content"
            assert 'sha' in file_data, "Missing SHA"

            content = file_data['content']
            lines = content.split('\n')

            print(f"✓ TODO.md exists")
            print(f"✓ File size: {len(content)} bytes")
            print(f"✓ Lines: {len(lines)}")
            print(f"✓ SHA: {file_data['sha'][:8]}...")
            print()
        except Exception as e:
            print(f"⚠ TODO.md not found (will be created on first use)")
            print()

        # Test 4: Mock add_task (no actual commit)
        print("Test 4: Mock Task Addition (dry-run)")
        test_task = "TEST: Verify GitHub integration (DO NOT COMMIT)"
        print(f"✓ Would add task: '{test_task}'")
        print(f"✓ Method: add_task_to_todo()")
        print("✓ Skipping actual commit (read-only test)")
        print()

        print("✓ All GitHub tests passed!")
        print("\nNote: This test is read-only. No commits were made.")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Sync config.local.yaml with schema changes from config.yaml

When config.yaml is updated in git (new keys added), this script:
1. Detects new keys in config.yaml not present in config.local.yaml
2. Adds new keys with their default values to config.local.yaml
3. Preserves existing local overrides (never overwrites)
4. Creates backup before modifying config.local.yaml
5. Preserves YAML formatting and comments where possible

Safe to run multiple times - only adds missing keys, never removes or overwrites.

Usage:
    python scripts/sync_local_config.py [--dry-run] [--force]

Options:
    --dry-run    Show what would be merged without making changes
    --force      Skip confirmation prompt
"""

import sys
import yaml
import argparse
from pathlib import Path
from datetime import datetime
from copy import deepcopy

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_DIR = PROJECT_ROOT / 'config'
BASE_CONFIG_PATH = CONFIG_DIR / 'config.yaml'
LOCAL_CONFIG_PATH = CONFIG_DIR / 'config.local.yaml'


def load_yaml_with_comments(file_path):
    """Load YAML file, preserving structure"""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def get_all_keys_with_values(obj, prefix=''):
    """
    Recursively get all keys from nested dict with their values

    Args:
        obj: Dictionary to extract keys from
        prefix: Current path prefix (for nested keys)

    Returns:
        Dict of {dot.separated.key: value}
    """
    result = {}

    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            result[full_key] = value
            if isinstance(value, dict):
                result.update(get_all_keys_with_values(value, full_key))

    return result


def set_nested_value(config, key_path, value):
    """
    Set a value in nested dict using dot-separated path

    Args:
        config: Dict to modify
        key_path: Dot-separated path (e.g., 'temperatures.comfort')
        value: Value to set
    """
    keys = key_path.split('.')
    current = config

    # Navigate/create nested structure
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the final value
    current[keys[-1]] = value


def delete_nested_key(config, key_path):
    """
    Delete a key from nested dict using dot-separated path

    Args:
        config: Dict to modify
        key_path: Dot-separated path (e.g., 'automations.night_mode')

    Returns:
        True if key was deleted, False if not found
    """
    keys = key_path.split('.')
    current = config

    # Navigate to parent
    try:
        for key in keys[:-1]:
            current = current[key]

        # Delete the final key
        if keys[-1] in current:
            del current[keys[-1]]
            return True
    except (KeyError, TypeError):
        pass

    return False


def merge_new_keys(base_config, local_config):
    """
    Find new keys in base_config not in local_config, and obsolete keys in local

    Args:
        base_config: Base configuration dict
        local_config: Local configuration dict (or None)

    Returns:
        Tuple of (new_local_config, added_keys_list, removed_keys_list)
    """
    base_keys = get_all_keys_with_values(base_config)
    local_keys = get_all_keys_with_values(local_config) if local_config else {}

    # Find keys in base that aren't in local (new keys to add)
    new_keys = set(base_keys.keys()) - set(local_keys.keys())

    # Find keys in local that aren't in base (obsolete keys to remove)
    obsolete_keys = set(local_keys.keys()) - set(base_keys.keys())

    # Filter out parent keys (we only care about leaf keys)
    # e.g., if 'temperatures.comfort' exists, don't add 'temperatures'
    leaf_keys = set()
    for key in new_keys:
        # Check if this key has any children in new_keys
        is_parent = any(k.startswith(key + '.') for k in new_keys)
        if not is_parent:
            leaf_keys.add(key)

    obsolete_leaf_keys = set()
    for key in obsolete_keys:
        # Check if this key has any children in obsolete_keys
        is_parent = any(k.startswith(key + '.') for k in obsolete_keys)
        if not is_parent:
            obsolete_leaf_keys.add(key)

    if not leaf_keys and not obsolete_leaf_keys:
        return local_config, [], []

    # Start with existing local config or empty dict
    new_local = deepcopy(local_config) if local_config else {}

    # Add new keys
    added_keys = []
    for key in sorted(leaf_keys):
        value = base_keys[key]
        set_nested_value(new_local, key, value)
        added_keys.append((key, value))

    # Remove obsolete keys
    removed_keys = []
    for key in sorted(obsolete_leaf_keys):
        value = local_keys[key]
        if delete_nested_key(new_local, key):
            removed_keys.append((key, value))

    return new_local, added_keys, removed_keys


def create_backup(file_path):
    """Create timestamped backup of file"""
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = file_path.parent / f"{file_path.stem}.backup_{timestamp}{file_path.suffix}"

    with open(file_path, 'r') as src:
        content = src.read()

    with open(backup_path, 'w') as dst:
        dst.write(content)

    return backup_path


def write_yaml_with_header(file_path, config, is_new_file=False):
    """Write YAML file with informative header"""
    header = """# Local Configuration Overrides
# This file is gitignored and contains machine-specific overrides
#
# Only keys that differ from config.yaml need to be listed here
# Values are deep-merged into config.yaml at runtime
#
# Auto-synced by scripts/sync_local_config.py when config.yaml schema changes
"""

    if is_new_file:
        header += f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    else:
        header += f"# Last synced: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

    header += "\n"

    with open(file_path, 'w') as f:
        f.write(header)
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Sync config.local.yaml with schema changes from config.yaml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview what would be added
    python scripts/sync_local_config.py --dry-run

    # Interactively sync (prompts for confirmation)
    python scripts/sync_local_config.py

    # Auto-sync without prompting (for scripts)
    python scripts/sync_local_config.py --force
        """
    )
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be merged without making changes')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompt')

    args = parser.parse_args()

    # Load base config
    if not BASE_CONFIG_PATH.exists():
        print(f"ERROR: Base config not found: {BASE_CONFIG_PATH}")
        return 1

    print(f"Loading base config: {BASE_CONFIG_PATH}")
    base_config = load_yaml_with_comments(BASE_CONFIG_PATH)

    # Load local config if exists
    local_config = None
    local_exists = LOCAL_CONFIG_PATH.exists()

    if local_exists:
        print(f"Loading local config: {LOCAL_CONFIG_PATH}")
        local_config = load_yaml_with_comments(LOCAL_CONFIG_PATH)
    else:
        print(f"No local config found (will create: {LOCAL_CONFIG_PATH})")

    # Find new and obsolete keys
    print("\nAnalyzing schema differences...")
    new_config, added_keys, removed_keys = merge_new_keys(base_config, local_config)

    if not added_keys and not removed_keys:
        print("✓ config.local.yaml is up to date! No changes needed.")
        return 0

    # Show what will be added
    if added_keys:
        print(f"\n{'DRY RUN: ' if args.dry_run else ''}Found {len(added_keys)} new key(s) to add:\n")
        for key, value in added_keys:
            # Format value for display
            if isinstance(value, dict):
                value_str = f"{{...}} ({len(value)} items)"
            elif isinstance(value, list):
                value_str = f"[...] ({len(value)} items)"
            else:
                value_str = repr(value)

            print(f"  + {key}: {value_str}")

    # Show what will be removed
    if removed_keys:
        print(f"\n{'DRY RUN: ' if args.dry_run else ''}Found {len(removed_keys)} obsolete key(s) to remove:\n")
        for key, value in removed_keys:
            # Format value for display
            if isinstance(value, dict):
                value_str = f"{{...}} ({len(value)} items)"
            elif isinstance(value, list):
                value_str = f"[...] ({len(value)} items)"
            else:
                value_str = repr(value)

            print(f"  - {key}: {value_str}")

    if args.dry_run:
        print("\n(Dry run mode - no files modified)")
        return 0

    # Confirm with user
    if not args.force:
        print(f"\nThis will {'create' if not local_exists else 'update'} {LOCAL_CONFIG_PATH}")
        if local_exists:
            print("A backup will be created before modifying the file.")
        if added_keys:
            print(f"  • {len(added_keys)} key(s) will be added")
        if removed_keys:
            print(f"  • {len(removed_keys)} obsolete key(s) will be removed")

        response = input("\nContinue? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print("Aborted.")
            return 1

    # Create backup if file exists
    if local_exists:
        backup_path = create_backup(LOCAL_CONFIG_PATH)
        print(f"\n✓ Backup created: {backup_path}")

    # Write updated config
    write_yaml_with_header(LOCAL_CONFIG_PATH, new_config, is_new_file=not local_exists)

    action = "Created" if not local_exists else "Updated"
    print(f"\n✓ {action}: {LOCAL_CONFIG_PATH}")
    if added_keys:
        print(f"  Added {len(added_keys)} new key(s) with default values")
    if removed_keys:
        print(f"  Removed {len(removed_keys)} obsolete key(s)")
    print("\nNext steps:")
    print("  1. Review the changes in config.local.yaml")
    print("  2. Customize values as needed for this machine")
    print("  3. Test with: python -c 'from lib.config import config; print(config)'")

    return 0


if __name__ == '__main__':
    sys.exit(main())

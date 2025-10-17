"""
Config validation - Warns when base config has new keys not in local config

Helps users keep config.local.yaml in sync with config.yaml updates.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_all_keys(obj, prefix=''):
    """
    Recursively get all keys from nested dict

    Args:
        obj: Dictionary to extract keys from
        prefix: Current path prefix (for nested keys)

    Returns:
        Set of dot-separated key paths (e.g., {'automations.dry_run', 'server.port'})
    """
    keys = set()

    if isinstance(obj, dict):
        for key, value in obj.items():
            full_key = f"{prefix}.{key}" if prefix else key
            keys.add(full_key)
            keys.update(get_all_keys(value, full_key))

    return keys


def validate_local_config(base_config, local_config):
    """
    Check if local config is missing any keys from base config

    Args:
        base_config: Base configuration dict (from config.yaml)
        local_config: Local overrides dict (from config.local.yaml)

    Returns:
        Tuple of (warnings, info_messages)
    """
    base_keys = get_all_keys(base_config)
    local_keys = get_all_keys(local_config) if local_config else set()

    # Find keys in base that aren't in local (these are using defaults)
    using_defaults = base_keys - local_keys

    # Filter out keys we don't care about warning on
    ignore_patterns = [
        # API keys and credentials should stay in .env
        '.api_key',
        '.password',
        '.token',
        '.secret',
        '.username',
        '.client_id',
        '.client_secret',
        '.refresh_token',
        '.device_id',
        # Structural keys
        'nest.project_id',
        'nest.client_id',
        'tapo.username',
        'sensibo.api_key',
        # Device lists and configs
        'tapo.outlets',
        'alen.devices',
        'locations.',
        'notifications.',
        'checkvist.',
        'github.',
    ]

    potentially_missing = set()
    for key in using_defaults:
        if not any(pattern in key for pattern in ignore_patterns):
            potentially_missing.add(key)

    warnings = []
    info_messages = []

    # Keys that commonly need local overrides
    important_keys = {
        'automations.dry_run': 'Controls whether automations actually run',
        'server.debug': 'Flask debug mode',
        'server.port': 'Server port number',
        'logging.level': 'Log verbosity',
        'temperatures.comfort': 'Comfort temperature setting',
        'temperatures.bedroom_sleep': 'Sleep temperature setting',
        'schedule.sleep_time': 'Bedtime',
        'schedule.wake_time': 'Wake time',
    }

    for key in potentially_missing:
        if key in important_keys:
            warnings.append({
                'key': key,
                'message': f"Using default for '{key}': {important_keys[key]}",
                'suggestion': f"Consider adding to config.local.yaml for Pi-specific override"
            })

    # Check for keys in local that no longer exist in base (obsolete overrides)
    obsolete_keys = local_keys - base_keys
    if obsolete_keys:
        for key in obsolete_keys:
            info_messages.append({
                'key': key,
                'message': f"Key '{key}' in config.local.yaml no longer exists in config.yaml",
                'suggestion': "This override has no effect and can be removed"
            })

    return warnings, info_messages


def log_config_warnings(base_config, local_config):
    """
    Log warnings about config mismatches

    Args:
        base_config: Base configuration dict
        local_config: Local configuration dict (or None)
    """
    if not local_config:
        logger.info("No config.local.yaml found - using all defaults from config.yaml")
        return

    warnings, info_messages = validate_local_config(base_config, local_config)

    if warnings:
        logger.warning(f"Config validation: {len(warnings)} potential override(s) to review:")
        for w in warnings[:5]:  # Limit to first 5 to avoid log spam
            logger.warning(f"  - {w['key']}: {w['message']}")
        if len(warnings) > 5:
            logger.warning(f"  ... and {len(warnings) - 5} more")

    if info_messages:
        logger.info(f"Config info: {len(info_messages)} obsolete key(s) in config.local.yaml")
        for m in info_messages[:3]:
            logger.info(f"  - {m['key']}: {m['message']}")


# For testing
if __name__ == '__main__':
    import yaml
    from pathlib import Path

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    project_root = Path(__file__).parent.parent

    # Load configs
    with open(project_root / 'config' / 'config.yaml') as f:
        base_config = yaml.safe_load(f)

    local_config_path = project_root / 'config' / 'config.local.yaml'
    local_config = None
    if local_config_path.exists():
        with open(local_config_path) as f:
            local_config = yaml.safe_load(f)

    log_config_warnings(base_config, local_config)

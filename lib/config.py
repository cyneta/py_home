"""
Configuration management for py_home

Loads configuration from:
1. config/config.yaml - Base configuration (committed to git)
2. config/config.local.yaml - Local overrides (gitignored, optional)
3. config/.env - Sensitive credentials (gitignored)

Environment variable substitution:
- ${VAR_NAME} in config files is replaced with value from .env

Local overrides:
- Create config/config.local.yaml to override specific values per instance
- Only needs to contain the values you want to override
- Useful for testing different settings on Pi vs dev machine
"""

import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Determine project root (parent of utils/)
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from .env
env_path = PROJECT_ROOT / 'config' / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try .env.example for development/testing
    example_path = PROJECT_ROOT / 'config' / '.env.example'
    if example_path.exists():
        print(f"Warning: Using .env.example. Copy to .env and add real credentials.")
        load_dotenv(example_path)


def deep_merge(base, override):
    """
    Deep merge two dictionaries (override into base)

    Args:
        base: Base dictionary
        override: Dictionary with override values

    Returns:
        Merged dictionary (modifies base in place and returns it)
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            # Recursively merge nested dicts
            deep_merge(base[key], value)
        else:
            # Override value
            base[key] = value
    return base


# Load base config.yaml
config_path = PROJECT_ROOT / 'config' / 'config.yaml'
if not config_path.exists():
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

with open(config_path) as f:
    config = yaml.safe_load(f)

# Load local overrides if they exist
local_config_path = PROJECT_ROOT / 'config' / 'config.local.yaml'
local_config_raw = None
if local_config_path.exists():
    with open(local_config_path) as f:
        local_config_raw = yaml.safe_load(f)
        if local_config_raw:  # Only merge if file has content
            config = deep_merge(config, local_config_raw)


def reload_config():
    """
    Reload configuration from disk (for hot-reload on config file changes)

    Returns:
        New config dict
    """
    global config

    # Reload base config
    with open(config_path) as f:
        new_config = yaml.safe_load(f)

    # Reload local overrides
    if local_config_path.exists():
        with open(local_config_path) as f:
            local_override = yaml.safe_load(f)
            if local_override:
                new_config = deep_merge(new_config, local_override)

    # Resolve environment variables
    new_config = resolve_env_vars(new_config)

    # Update global config
    config = new_config

    return config


def resolve_env_vars(obj):
    """
    Recursively replace ${ENV_VAR} placeholders with environment variable values

    Args:
        obj: Config object (dict, list, str, etc.)

    Returns:
        Object with environment variables substituted

    Raises:
        ValueError: If required environment variable is not set
    """
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        if obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(
                    f"Missing required environment variable: {var_name}\n"
                    f"Please add it to config/.env"
                )
            return value
    return obj


# Resolve all environment variables in config
config = resolve_env_vars(config)

# Validate config and warn about mismatches
try:
    from lib.config_validator import log_config_warnings
    log_config_warnings(config, local_config_raw)
except ImportError:
    pass  # Validator not available


def get(path, default=None):
    """
    Get configuration value by dot-separated path

    Args:
        path: Dot-separated path (e.g., 'tesla.email', 'locations.home.lat')
        default: Default value if path not found

    Returns:
        Configuration value or default

    Examples:
        >>> get('tesla.email')
        'user@example.com'
        >>> get('locations.home.lat')
        41.8781
    """
    keys = path.split('.')
    value = config

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default

    return value


# Export config for easy importing
__all__ = ['config', 'get', 'reload_config', 'PROJECT_ROOT']

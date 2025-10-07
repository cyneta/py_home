"""
Configuration management for py_home

Loads configuration from:
1. config/config.yaml - Non-sensitive settings
2. config/.env - Sensitive credentials (not committed to git)

Environment variable substitution:
- ${VAR_NAME} in config.yaml is replaced with value from .env
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

# Load config.yaml
config_path = PROJECT_ROOT / 'config' / 'config.yaml'
if not config_path.exists():
    raise FileNotFoundError(f"Configuration file not found: {config_path}")

with open(config_path) as f:
    config = yaml.safe_load(f)


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
__all__ = ['config', 'get', 'PROJECT_ROOT']

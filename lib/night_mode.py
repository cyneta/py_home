"""
Night Mode State Management

Tracks whether the system is in night mode (triggered by goodnight automation).
Uses a simple state file similar to presence detection.

Night Mode Behavior:
- Enabled by goodnight automation
- Nest in ECO mode (minimal whole-house HVAC)
- Sensibo maintains Master Suite at 66°F
- Disabled by good_morning automation
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# State file location (project root)
STATE_FILE = Path(__file__).parent.parent / '.night_mode'


def is_night_mode():
    """
    Check if night mode is currently active

    Returns:
        bool: True if night mode enabled, False otherwise

    Example:
        >>> if is_night_mode():
        ...     print("Night mode active")
    """
    return STATE_FILE.exists()


def set_night_mode(enabled):
    """
    Enable or disable night mode

    Args:
        enabled: True to enable night mode, False to disable

    Example:
        >>> set_night_mode(True)   # Enable night mode
        >>> set_night_mode(False)  # Disable night mode
    """
    if enabled:
        # Create state file
        try:
            STATE_FILE.touch()
            logger.info("Night mode enabled")
        except Exception as e:
            logger.error(f"Failed to enable night mode: {e}")
            raise
    else:
        # Remove state file
        try:
            if STATE_FILE.exists():
                STATE_FILE.unlink()
                logger.info("Night mode disabled")
            else:
                logger.debug("Night mode already disabled")
        except Exception as e:
            logger.error(f"Failed to disable night mode: {e}")
            raise


def get_night_mode_status():
    """
    Get detailed night mode status

    Returns:
        dict: {
            'enabled': bool,
            'state_file': str (path to state file)
        }

    Example:
        >>> status = get_night_mode_status()
        >>> print(f"Night mode: {status['enabled']}")
    """
    return {
        'enabled': is_night_mode(),
        'state_file': str(STATE_FILE)
    }


__all__ = ['is_night_mode', 'set_night_mode', 'get_night_mode_status']

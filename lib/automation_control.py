"""
Automation Control - Master Enable/Disable Switch

Provides a simple flag to disable all automations without unplugging the Pi.
Useful for testing, maintenance, or when you need automations to stop temporarily.

Usage in automation scripts:
    from lib.automation_control import are_automations_enabled

    if not are_automations_enabled():
        logger.info("Automations disabled, skipping")
        return
"""

import os
import logging

logger = logging.getLogger(__name__)

DISABLE_FILE = os.path.join(os.path.dirname(__file__), '..', '.automation_disabled')


def are_automations_enabled():
    """
    Check if automations are enabled

    Returns:
        bool: True if automations should run, False if disabled
    """
    return not os.path.exists(DISABLE_FILE)


def disable_automations():
    """
    Disable all automations by creating disable flag file

    Returns:
        bool: True if successfully disabled
    """
    try:
        import time
        with open(DISABLE_FILE, 'w') as f:
            f.write(f"Disabled at {time.time()}\n")
        logger.info("Automations disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable automations: {e}")
        return False


def enable_automations():
    """
    Enable all automations by removing disable flag file

    Returns:
        bool: True if successfully enabled
    """
    try:
        if os.path.exists(DISABLE_FILE):
            os.remove(DISABLE_FILE)
        logger.info("Automations enabled")
        return True
    except Exception as e:
        logger.error(f"Failed to enable automations: {e}")
        return False


__all__ = ['are_automations_enabled', 'disable_automations', 'enable_automations']

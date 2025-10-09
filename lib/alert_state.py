"""
Alert state tracking for rate limiting

Prevents notification spam by tracking when alerts were last sent.
Implements cooldown periods per alert type.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Default cooldown: 1 hour per alert type
DEFAULT_COOLDOWN_MINUTES = 60

# State file location
STATE_DIR = Path(__file__).parent.parent / '.alert_state'
STATE_FILE = STATE_DIR / 'alert_history.json'


def _ensure_state_dir():
    """Create state directory if it doesn't exist"""
    STATE_DIR.mkdir(exist_ok=True)


def _load_state():
    """Load alert state from disk"""
    _ensure_state_dir()

    if not STATE_FILE.exists():
        return {}

    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load alert state: {e}")
        return {}


def _save_state(state):
    """Save alert state to disk"""
    _ensure_state_dir()

    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save alert state: {e}")


def should_send_alert(alert_type, identifier=None, cooldown_minutes=DEFAULT_COOLDOWN_MINUTES):
    """
    Check if an alert should be sent based on cooldown period

    Args:
        alert_type: Type of alert (e.g., 'pipe_freeze', 'high_humidity')
        identifier: Optional identifier (e.g., room name, device name)
        cooldown_minutes: Minutes to wait before resending same alert

    Returns:
        bool: True if alert should be sent, False if in cooldown period

    Example:
        >>> if should_send_alert('pipe_freeze', 'Crawlspace'):
        >>>     send_high("Freeze risk!")
        >>>     record_alert_sent('pipe_freeze', 'Crawlspace')
    """
    # Build alert key
    key = alert_type
    if identifier:
        key = f"{alert_type}:{identifier}"

    # Load state
    state = _load_state()

    # Check if alert was sent recently
    if key in state:
        last_sent_str = state[key]
        try:
            last_sent = datetime.fromisoformat(last_sent_str)
            time_since = datetime.now() - last_sent

            if time_since < timedelta(minutes=cooldown_minutes):
                # Still in cooldown
                remaining = cooldown_minutes - int(time_since.total_seconds() / 60)
                logger.info(f"Alert '{key}' in cooldown: {remaining} min remaining")
                return False
        except Exception as e:
            logger.warning(f"Failed to parse last sent time for '{key}': {e}")

    # Not in cooldown or first time
    return True


def record_alert_sent(alert_type, identifier=None):
    """
    Record that an alert was sent

    Args:
        alert_type: Type of alert (e.g., 'pipe_freeze', 'high_humidity')
        identifier: Optional identifier (e.g., room name, device name)

    Example:
        >>> send_high("Freeze risk!")
        >>> record_alert_sent('pipe_freeze', 'Crawlspace')
    """
    # Build alert key
    key = alert_type
    if identifier:
        key = f"{alert_type}:{identifier}"

    # Load state
    state = _load_state()

    # Update state
    state[key] = datetime.now().isoformat()

    # Save state
    _save_state(state)

    logger.debug(f"Recorded alert sent: {key}")


def clear_alert_state(alert_type=None, identifier=None):
    """
    Clear alert state (useful for testing or when issue is resolved)

    Args:
        alert_type: Type of alert to clear (None = clear all)
        identifier: Optional identifier

    Example:
        >>> clear_alert_state('pipe_freeze', 'Crawlspace')  # Clear specific
        >>> clear_alert_state()  # Clear all
    """
    state = _load_state()

    if alert_type is None:
        # Clear all
        state = {}
        logger.info("Cleared all alert state")
    else:
        # Clear specific
        key = alert_type
        if identifier:
            key = f"{alert_type}:{identifier}"

        if key in state:
            del state[key]
            logger.info(f"Cleared alert state: {key}")

    _save_state(state)


def get_alert_history():
    """
    Get all alert history (for debugging/monitoring)

    Returns:
        dict: Alert type -> last sent timestamp
    """
    return _load_state()


__all__ = ['should_send_alert', 'record_alert_sent', 'clear_alert_state', 'get_alert_history']

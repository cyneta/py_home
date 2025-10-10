"""
Notification system for py_home

Sends notifications to user's phone via:
- Pushover (recommended, $5 one-time)
- ntfy.sh (free alternative)

Priority levels:
- -2: Lowest (no sound/vibration)
- -1: Low
-  0: Normal (default)
-  1: High (bypass quiet hours)
-  2: Emergency (repeats until acknowledged, Pushover only)
"""

import requests
import logging

logger = logging.getLogger(__name__)


def send(message, title="Home Automation", priority=0):
    """
    Send notification to user's phone

    Args:
        message: Notification text
        title: Notification title
        priority: -2=lowest, -1=low, 0=normal, 1=high, 2=emergency (Pushover only)

    Returns:
        bool: True if notification sent successfully

    Example:
        >>> send("House secured, cleaning started")
        >>> send("Tesla battery low (18%)", priority=1)
    """
    from lib.config import config

    service = config['notifications']['service']

    try:
        if service == 'pushover':
            return _send_pushover(message, title, priority, config)
        elif service == 'ntfy':
            return _send_ntfy(message, title, priority, config)
        else:
            logger.error(f"Unknown notification service: {service}")
            return False
    except Exception as e:
        logger.error(f"Failed to send notification: {e}", exc_info=True)
        return False


def _send_pushover(message, title, priority, config):
    """Send notification via Pushover"""
    pushover_config = config['notifications']['pushover']
    token = pushover_config['token']
    user = pushover_config['user']

    # Check if credentials are configured
    if not token or not user:
        logger.warning("Pushover credentials not configured, skipping notification")
        return False

    try:
        resp = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "message": message,
                "title": title,
                "priority": priority
            },
            timeout=10
        )
        resp.raise_for_status()
        logger.info(f"Pushover notification sent: {title}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Pushover API error: {e}")
        return False


def _send_ntfy(message, title, priority, config):
    """Send notification via ntfy.sh"""
    ntfy_config = config['notifications'].get('ntfy', {})
    topic = ntfy_config.get('topic', 'py_home_automation')

    # Map priority to ntfy priority (1-5)
    # Pushover: -2, -1, 0, 1, 2
    # ntfy: 1 (min), 3 (default), 5 (max)
    ntfy_priority = {
        -2: 1,
        -1: 2,
        0: 3,
        1: 4,
        2: 5
    }.get(priority, 3)

    try:
        # Remove emojis from title for HTTP header (latin-1 encoding required)
        # Keep emojis in message body which supports UTF-8
        def strip_emojis(text):
            """Remove non-latin-1 characters (emojis) from text"""
            return ''.join(char for char in text if ord(char) < 256)

        safe_title = strip_emojis(title).strip()

        # If title had only emojis, use default
        if not safe_title:
            safe_title = "Home Automation"

        full_message = f"{title}: {message}" if title != "Home Automation" else message

        resp = requests.post(
            f"https://ntfy.sh/{topic}",
            data=full_message.encode('utf-8'),
            headers={
                "Title": safe_title,
                "Priority": str(ntfy_priority),
                "Tags": "house"
            },
            timeout=10
        )
        resp.raise_for_status()
        logger.info(f"ntfy notification sent: {safe_title}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"ntfy API error: {e}")
        return False


# Convenience functions for common priority levels
def send_low(message, title="Home Automation"):
    """Send low-priority notification (no sound/vibration)"""
    return send(message, title, priority=-1)


def send_normal(message, title="Home Automation"):
    """Send normal notification"""
    return send(message, title, priority=0)


def send_high(message, title="Home Automation"):
    """Send high-priority notification (bypass quiet hours)"""
    return send(message, title, priority=1)


def send_emergency(message, title="Home Automation"):
    """Send emergency notification (repeats until acknowledged, Pushover only)"""
    return send(message, title, priority=2)


def send_automation_summary(event_title, actions, priority=0):
    """
    Send notification with event title and list of actions taken

    Args:
        event_title: Event description with emoji (e.g., "🚗 Left Home")
        actions: List of actions taken (e.g., ["Nest set to 62°F", "Lights off"])
        priority: Notification priority (-2 to 2)

    Returns:
        bool: True if notification sent successfully

    Example:
        >>> send_automation_summary(
        ...     "🚗 Left Home",
        ...     ["Nest set to 62°F", "Lights turned off", "House secured"]
        ... )
    """
    if not actions:
        # No actions, just send the event
        return send(event_title, priority=priority)

    # Build multi-line message with action list
    message = "\n".join(f"→ {action}" for action in actions)
    return send(message, title=event_title, priority=priority)


__all__ = [
    'send',
    'send_low',
    'send_normal',
    'send_high',
    'send_emergency',
    'send_automation_summary'
]

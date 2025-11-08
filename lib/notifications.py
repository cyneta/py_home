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
        priority: 0=info (default), 1=urgent (emergencies only)

    Returns:
        bool: True if notification sent successfully

    Example:
        >>> send("Backup completed")  # Info (avoid - use logs instead)
        >>> send("Pipe freeze risk", priority=1)  # Urgent
    """
    # Validate message is not empty
    if not message or (isinstance(message, str) and not message.strip()):
        logger.warning("Notification rejected: empty message")
        return False

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
    # py_home: 0 (info), 1 (urgent)
    # ntfy: 3 (default), 5 (urgent)
    ntfy_priority = {
        0: 3,  # Info - normal notification
        1: 5   # Urgent - high priority, bypass DND
    }.get(priority, 3)

    try:
        # Build headers - only include Title if one was provided
        headers = {
            "Priority": str(ntfy_priority),
            "Tags": "house"
        }

        # Only add Title header if title is not empty
        # If no title, ntfy uses first line of message (preserves emojis!)
        if title:
            # Remove emojis from title for HTTP header (latin-1 encoding required)
            def strip_emojis(text):
                """Remove non-latin-1 characters (emojis) from text"""
                return ''.join(char for char in text if ord(char) < 256)

            safe_title = strip_emojis(title).strip()
            if safe_title:
                headers["Title"] = safe_title

        # Send message as UTF-8 (supports emojis in body)
        resp = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode('utf-8'),
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        logger.info(f"ntfy notification sent: {title or 'no title'}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"ntfy API error: {e}")
        return False


# Convenience functions for common priority levels
def send_info(message, title="Home Automation"):
    """Send info notification (avoid - use logs instead per design principle)"""
    return send(message, title, priority=0)


def send_urgent(message, title="Home Automation"):
    """Send urgent notification (emergencies only)"""
    return send(message, title, priority=1)


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

    # Build multi-line message with event title (with emoji) and action list
    # Everything goes in body - no separate title needed
    message = event_title + "\n" + "\n".join(f"→ {action}" for action in actions)
    # Don't pass title - let ntfy use first line of message as notification preview
    return send(message, title="", priority=priority)


__all__ = [
    'send',
    'send_low',
    'send_normal',
    'send_high',
    'send_emergency',
    'send_automation_summary'
]

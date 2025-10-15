#!/usr/bin/env python3
"""
Preview script to transform existing logs into proposed new format.
Does not modify any production code - just shows what the new format would look like.

Usage:
    python scripts/preview_log_format.py data/logs/automations.log | head -50
"""

import sys
import re
from datetime import datetime


def extract_category(logger_name, message):
    """Determine log category from logger name and message content"""
    if 'automation=' in message or logger_name == '__main__':
        return 'AUTO'
    elif 'nest' in logger_name.lower():
        return 'NEST'
    elif 'tapo' in logger_name.lower():
        return 'TAPO'
    elif 'sensibo' in logger_name.lower():
        return 'SENSIBO'
    elif 'tempstick' in logger_name.lower():
        return 'TEMP'
    elif 'notifications' in logger_name.lower():
        return 'NTFY'
    elif 'api=' in message:
        return 'API'
    elif 'request' in message.lower():
        return 'HTTP'
    else:
        return 'SYS'


def format_duration(duration_ms):
    """Format duration nicely: 2.9s or 319ms"""
    if duration_ms >= 1000:
        return f"{duration_ms/1000:.1f}s"
    else:
        return f"{duration_ms}ms"


def simplify_message(message, level):
    """Simplify and clean up log message"""
    # Extract key=value pairs
    kvpairs = {}
    parts = message.split()

    for part in parts:
        if '=' in part:
            key, val = part.split('=', 1)
            # Remove quotes from values
            val = val.strip('"')
            kvpairs[key] = val

    # Automation events
    if 'automation=' in message and 'event=' in message:
        auto = kvpairs.get('automation', '?')
        event = kvpairs.get('event', '?')

        if event == 'start':
            stage = f" stage={kvpairs['stage']}" if 'stage' in kvpairs else ""
            dry = " [dry-run]" if kvpairs.get('dry_run') == 'True' else ""
            return f"{auto} {event}{stage}{dry}"

        elif event == 'complete':
            duration = format_duration(int(kvpairs.get('duration_ms', 0)))
            errors = kvpairs.get('errors', '0')
            actions = f" actions={kvpairs['actions_count']}" if 'actions_count' in kvpairs else ""
            err_note = f" errors={errors}" if errors != '0' else ""
            return f"{auto} {event} ({duration}){err_note}{actions}"

    # Automation device actions
    if 'automation=' in message and 'device=' in message and 'action=' in message:
        auto = kvpairs.get('automation', '?')
        device = kvpairs.get('device', '?')
        action = kvpairs.get('action', '?')
        result = kvpairs.get('result', '?')
        duration = format_duration(int(kvpairs.get('duration_ms', 0))) if 'duration_ms' in kvpairs else ""
        target = f" target={kvpairs['target']}" if 'target' in kvpairs else ""

        dur_str = f" ({duration})" if duration else ""
        return f"{auto} → {device} {action}{target} {result}{dur_str}"

    # API calls
    if 'api=' in message and 'action=' in message:
        api = kvpairs.get('api', '?')
        action = kvpairs.get('action', '?')
        result = kvpairs.get('result', '?')
        duration = format_duration(int(kvpairs.get('duration_ms', 0))) if 'duration_ms' in kvpairs else ""

        # For commands, show command name
        if 'endpoint=' in message and 'cmd:' in kvpairs.get('endpoint', ''):
            cmd = kvpairs['endpoint'].replace('cmd:', '')
            return f"{api} {cmd} {result} ({duration})"

        # For other actions
        outlet = kvpairs.get('outlet', '')
        if outlet:
            outlet = outlet.replace('_', ' ')
            return f"{api} {action} {outlet} {result} ({duration})"

        return f"{api} {action} {result} ({duration})"

    # Human-readable status messages (keep as-is if they look good)
    if any(phrase in message for phrase in ['Nest status:', 'Set temperature', 'Eco mode', 'Turned ON:', 'Turned OFF:']):
        # Clean up status message
        msg = message.replace('Nest status:', 'Status:').strip()
        return msg

    # Notification messages
    if 'ntfy notification sent' in message:
        return "Notification sent"

    # Request logging - make minimal
    if 'request_complete' in message or 'request_start' in message:
        if level != 'NOTICE':
            return None  # Skip DEBUG request logs
        method = kvpairs.get('method', '?')
        path = kvpairs.get('path', '?')
        status = kvpairs.get('status', '')
        duration = format_duration(int(kvpairs.get('duration_ms', 0))) if 'duration_ms' in kvpairs else ""
        return f"{method} {path} {status} ({duration})"

    # Token refresh
    if 'Refreshing' in message and 'access token' in message:
        return "Refreshing API token"

    # Default: return cleaned message
    return message


def transform_log_line(line):
    """Transform a single log line to new format"""
    # Parse existing format: 2025-10-14 20:41:31,589 __main__[33305] NOTICE message
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) ([^\[]+)\[\d+\] (\w+) (.+)'
    match = re.match(pattern, line.strip())

    if not match:
        return None  # Skip malformed lines

    date_time, msec, logger_name, level, message = match.groups()
    logger_name = logger_name.strip()

    # Extract just time
    time_obj = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
    time_str = time_obj.strftime('%H:%M:%S')

    # Determine category
    category = extract_category(logger_name, message)

    # Simplify message
    simplified = simplify_message(message, level)
    if simplified is None:
        return None  # Skip this line

    # Format: HH:MM:SS.mmm LEVEL [CATEGORY] message
    return f"{time_str}.{msec} {level:6s} [{category:6s}] {simplified}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/preview_log_format.py <logfile>")
        print("Example: python scripts/preview_log_format.py data/logs/automations.log | head -50")
        sys.exit(1)

    logfile = sys.argv[1]

    try:
        with open(logfile, 'r') as f:
            for line in f:
                transformed = transform_log_line(line)
                if transformed:
                    print(transformed)
    except FileNotFoundError:
        print(f"Error: Log file not found: {logfile}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing log: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

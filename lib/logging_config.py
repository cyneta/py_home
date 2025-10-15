"""
Centralized logging configuration for py_home.

Provides concise, readable logging with category tags and clean formatting.
Format: HH:MM:SS.mmm LEVEL [CATEGORY] message

Categories:
- AUTO: Automation events
- NEST/TAPO/SENSIBO/TEMP: Device-specific
- API: API calls
- HTTP: Web requests
- NTFY: Notifications
- SYS: System events
"""

import logging
import os
import sys

# Add custom NOTICE level (between INFO and WARNING)
# Used for normal operational events worth recording
logging.NOTICE = 25
logging.addLevelName(25, 'NOTICE')


class CategoryFilter(logging.Filter):
    """Add category to log records based on logger name"""

    CATEGORY_MAP = {
        '__main__': 'AUTO',
        'automations.': 'AUTO',  # Automation scripts
        'components.nest': 'NEST',
        'components.tapo': 'TAPO',
        'components.sensibo': 'SENSIBO',
        'services.tempstick': 'TEMP',
        'services.openweather': 'API',
        'lib.notifications': 'NTFY',
        'server.routes': 'HTTP',
    }

    def filter(self, record):
        # Determine category from logger name
        logger_name = record.name
        category = 'SYS'  # Default

        for prefix, cat in self.CATEGORY_MAP.items():
            if logger_name.startswith(prefix):
                category = cat
                break

        # Check message content for API calls (overrides logger-based category)
        if hasattr(record, 'msg') and 'api=' in str(record.msg):
            category = 'API'

        # Check message content for automation events
        if hasattr(record, 'msg') and 'automation=' in str(record.msg):
            category = 'AUTO'

        record.category = category
        return True


def _format_value(v):
    """
    Format value for key=value logging with RFC 5424-compatible quoting.

    Simple values (no special chars): returned as-is
    Complex values (spaces, quotes, etc.): quoted and escaped

    Examples:
        200 → 200
        "OK" → OK
        "Connection timeout" → "Connection timeout"
        'Say "hello"' → "Say \"hello\""

    Args:
        v: Value to format

    Returns:
        str: Formatted value (quoted if needed)
    """
    s = str(v)

    # Check if quoting is needed (spaces, quotes, equals, colons, newlines, tabs)
    needs_quotes = any(c in s for c in ' ":=\n\t')

    if needs_quotes:
        # Escape backslashes and quotes (RFC 5424 compatible)
        s = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{s}"'

    return s


def format_duration(duration_ms):
    """
    Format duration in human-readable form.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        str: Formatted duration (e.g., "2.9s" or "319ms")

    Examples:
        format_duration(2919) → "2.9s"
        format_duration(319) → "319ms"
        format_duration(12543) → "12.5s"
    """
    if duration_ms >= 1000:
        return f"{duration_ms/1000:.1f}s"
    else:
        return f"{duration_ms}ms"


def clean_error_message(error_msg):
    """
    Clean up error messages by removing long URLs and IDs.

    Args:
        error_msg: Raw error message string

    Returns:
        str: Cleaned error message

    Examples:
        "400 Client Error: Bad Request for url: https://...very-long-url..."
        → "400 Bad Request"

        "Connection timeout after 10s"
        → "Connection timeout after 10s"
    """
    msg = str(error_msg)

    # Remove " for url: https://..." patterns
    if ' for url: ' in msg:
        msg = msg.split(' for url: ')[0]

    # Simplify "Client Error: " prefix
    msg = msg.replace('Client Error: ', '')

    # Trim to max 150 chars
    if len(msg) > 150:
        msg = msg[:147] + '...'

    return msg


def kvlog(logger, level, **kwargs):
    """
    Log structured key=value pairs with automatic quoting.

    Values containing spaces or special characters are automatically quoted
    and escaped according to RFC 5424 standards.

    Usage:
        kvlog(logger, logging.NOTICE, automation='leaving_home', event='start')
        kvlog(logger, logging.INFO, device='nest', action='set_temp', result='ok', duration_ms=234)
        kvlog(logger, logging.ERROR, device='nest', error_type='ConnectionError', error_msg='timeout: failed after 10s')

    Args:
        logger: Python logger instance
        level: Log level (DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL)
        **kwargs: Key-value pairs to log

    Notes:
        - Values with spaces/special chars are automatically quoted
        - Quotes and backslashes within values are escaped
        - Simple values (numbers, single words) stay unquoted for readability
    """
    msg = ' '.join(f'{k}={_format_value(v)}' for k, v in kwargs.items())
    logger.log(level, msg)


def setup_logging(log_level=None, log_file=None):
    """
    Configure logging for entire application.

    Args:
        log_level: Log level string (DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL)
                   Priority: 1) parameter, 2) LOG_LEVEL env var, 3) config.yaml, 4) INFO
        log_file: Path to log file (None = stdout, recommended for systemd)
                  Priority: 1) parameter, 2) config.yaml, 3) None (stdout)
    """
    # Determine log level (parameter > env var > config > default)
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL')
        if log_level is None:
            try:
                from lib.config import get
                log_level = get('logging.level', 'INFO')
            except Exception:
                log_level = 'INFO'

    # Determine log file (parameter > config > default)
    if log_file is None:
        try:
            from lib.config import get
            log_file = get('logging.file')
        except Exception:
            log_file = None

    # Convert string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # New concise format: HH:MM:SS.mmm LEVEL [CATEGORY] message
    # %(asctime)s.%(msecs)03d → time with milliseconds
    # %(levelname)-6s → level name, left-aligned, 6 chars wide
    # [%(category)-6s] → category tag in brackets, 6 chars wide
    log_format = '%(asctime)s.%(msecs)03d %(levelname)-6s [%(category)-6s] %(message)s'
    date_format = '%H:%M:%S'  # Time only, no date

    # Configure handlers
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    # Set formatter with time-only format
    handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    # Add category filter
    handler.addFilter(CategoryFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(handler)

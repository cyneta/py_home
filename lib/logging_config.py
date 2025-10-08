"""
Centralized logging configuration for py_home.

Provides Unix-standard structured logging with syslog-compatible levels
and key=value format for easy parsing with grep/awk/journalctl.
"""

import logging
import os
import sys

# Add custom NOTICE level (between INFO and WARNING)
# Used for normal operational events worth recording
logging.NOTICE = 25
logging.addLevelName(25, 'NOTICE')


def kvlog(logger, level, **kwargs):
    """
    Log structured key=value pairs.

    Usage:
        kvlog(logger, logging.NOTICE, automation='leaving_home', event='start')
        kvlog(logger, logging.INFO, device='nest', action='set_temp', result='ok', duration_ms=234)
        kvlog(logger, logging.ERROR, device='nest', error_type='ConnectionError', error_msg='timeout')

    Args:
        logger: Python logger instance
        level: Log level (DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL)
        **kwargs: Key-value pairs to log
    """
    msg = ' '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.log(level, msg)


def setup_logging(log_level=None, log_file=None):
    """
    Configure logging for entire application.

    Args:
        log_level: Log level string (DEBUG, INFO, NOTICE, WARNING, ERROR, CRITICAL)
                   Defaults to LOG_LEVEL env var, then INFO
        log_file: Path to log file (None = stdout, recommended for systemd)
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO')

    # Convert string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Syslog-compatible format: timestamp name[pid] level message
    log_format = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'

    # Configure handlers
    if log_file:
        handler = logging.FileHandler(log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(logging.Formatter(log_format))

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(handler)

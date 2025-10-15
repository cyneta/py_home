#!/usr/bin/env python3
"""
Quick test script to verify new logging format.
"""

from lib.logging_config import setup_logging, format_duration, kvlog
import logging

# Setup logging to file
setup_logging(log_file='data/logs/automations.log')

# Get logger
logger = logging.getLogger('__main__')

# Test various log formats
logger.log(logging.NOTICE, "test_automation start stage=1")
logger.info("Testing new log format with categories")
kvlog(logger, logging.NOTICE, automation='test', device='nest', action='set_temp', result='ok', duration_ms=2500)
logger.log(logging.NOTICE, f"test_automation complete ({format_duration(3200)})")

print("✓ Test logs written to data/logs/automations.log")
print("Check with: tail data/logs/automations.log")

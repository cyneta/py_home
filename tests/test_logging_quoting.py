#!/usr/bin/env python
"""
Test script for logging value quoting functionality.

Tests RFC 5424-compatible quoting of structured log values.
"""

import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from lib.logging_config import setup_logging, kvlog

# Setup logging to capture output
setup_logging('INFO')
logger = logging.getLogger('test_quoting')

print("=" * 70)
print("Testing Logging Value Quoting")
print("=" * 70)
print()

# Test 1: Simple values (no quotes needed)
print("Test 1: Simple values (no quoting)")
kvlog(logger, logging.INFO, status=200, method='GET', device='nest')
print("✓ Expected: status=200 method=GET device=nest")
print()

# Test 2: Values with spaces (quoted)
print("Test 2: Values with spaces (should quote)")
kvlog(logger, logging.ERROR, error_msg='Connection timeout after 10s')
print("✓ Expected: error_msg=\"Connection timeout after 10s\"")
print()

# Test 3: Values with colons (quoted)
print("Test 3: Values with colons (should quote)")
kvlog(logger, logging.ERROR, error_msg='HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded')
print("✓ Expected: error_msg=\"HTTPSConnectionPool(host=api.nest.com, port=443): Max retries exceeded\"")
print()

# Test 4: Values with quotes (quoted and escaped)
print("Test 4: Values with internal quotes (should quote and escape)")
kvlog(logger, logging.INFO, task='Fix "critical" bug in parser')
print("✓ Expected: task=\"Fix \\\"critical\\\" bug in parser\"")
print()

# Test 5: Values with equals (quoted)
print("Test 5: Values with equals sign (should quote)")
kvlog(logger, logging.INFO, formula='E=mc^2', equation='a=b+c')
print("✓ Expected: formula=\"E=mc^2\" equation=\"a=b+c\"")
print()

# Test 6: Paths (typically no quotes needed)
print("Test 6: Paths without spaces (no quoting)")
kvlog(logger, logging.ERROR, path='/automation/leaving-home', script='leaving_home.py')
print("✓ Expected: path=/automation/leaving-home script=leaving_home.py")
print()

# Test 7: Mixed simple and complex
print("Test 7: Mixed simple and complex values")
kvlog(logger, logging.NOTICE, automation='test', event='start', dry_run=False, task='Review PR #123')
print("✓ Expected: automation=test event=start dry_run=False task=\"Review PR #123\"")
print()

# Test 8: Real exception message
print("Test 8: Real exception message (realistic error)")
try:
    raise ConnectionError("HTTPSConnectionPool(host='api.nest.com', port=443): Max retries exceeded with url: /enterprises/abc123/devices")
except Exception as e:
    kvlog(logger, logging.ERROR, automation='test', device='nest', action='get_status',
          error_type=type(e).__name__, error_msg=str(e))
    print("✓ Expected: error_msg with quotes and all special chars preserved")
print()

# Test 9: Newlines and tabs (quoted and escaped)
print("Test 9: Newlines and tabs (should quote)")
kvlog(logger, logging.ERROR, error_msg='Line 1\nLine 2\tTabbed')
print("✓ Expected: error_msg=\"Line 1\\nLine 2\\tTabbed\"")
print()

# Test 10: Backslashes (quoted and escaped)
print("Test 10: Backslashes (should quote and escape)")
kvlog(logger, logging.INFO, path='C:\\Users\\test\\file.txt')
print("✓ Expected: path=\"C:\\\\Users\\\\test\\\\file.txt\"")
print()

print("=" * 70)
print("All test cases executed. Review output above for correctness.")
print("=" * 70)

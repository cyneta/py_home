"""
Flask Webhook Server for py_home

Provides HTTP endpoints for iOS Shortcuts to trigger automations.

Replaces n8n webhook nodes with Flask routes.
"""

import time

__version__ = '1.0.0'

# Track Flask server start time for uptime calculation
FLASK_START_TIME = time.time()

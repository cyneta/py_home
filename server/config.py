"""
Flask Server Configuration

Settings for the webhook server.
"""

import os

# Server settings
HOST = os.getenv('FLASK_HOST', '0.0.0.0')  # Listen on all interfaces
PORT = int(os.getenv('FLASK_PORT', '5000'))
DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Security
# Set FLASK_SECRET_KEY in .env for production
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Basic authentication (optional)
# Set these in .env to require authentication
REQUIRE_AUTH = os.getenv('FLASK_REQUIRE_AUTH', 'False').lower() == 'true'
AUTH_USERNAME = os.getenv('FLASK_AUTH_USERNAME', '')
AUTH_PASSWORD = os.getenv('FLASK_AUTH_PASSWORD', '')

# Logging
LOG_LEVEL = os.getenv('FLASK_LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('FLASK_LOG_FILE', None)  # None = stdout only

# Automation script paths
AUTOMATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'automations')

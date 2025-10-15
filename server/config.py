"""
Flask Server Configuration

Settings for the webhook server.
Priority: 1) Environment variables, 2) config.yaml, 3) Defaults
"""

import os

# Import config helper
try:
    from lib.config import get
except ImportError:
    # Fallback if config not available
    def get(path, default=None):
        return default

# Server settings (env var > config > default)
HOST = os.getenv('FLASK_HOST') or get('server.host', '0.0.0.0')
PORT = int(os.getenv('FLASK_PORT') or get('server.port', 5000))
DEBUG = (os.getenv('FLASK_DEBUG') or str(get('server.debug', False))).lower() == 'true'

# Security (secrets stay in .env)
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Basic authentication (env var > config > default)
REQUIRE_AUTH = (os.getenv('FLASK_REQUIRE_AUTH') or str(get('server.require_auth', False))).lower() == 'true'
AUTH_USERNAME = os.getenv('FLASK_AUTH_USERNAME', '')
AUTH_PASSWORD = os.getenv('FLASK_AUTH_PASSWORD', '')

# Logging (env var > config > default)
LOG_LEVEL = os.getenv('FLASK_LOG_LEVEL') or get('server.log_level', 'INFO')
LOG_FILE = os.getenv('FLASK_LOG_FILE') or get('logging.file')

# Automation script paths
AUTOMATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'automations')

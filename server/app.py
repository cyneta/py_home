#!/usr/bin/env python
"""
Flask Webhook Server for py_home

Main application entry point.

Usage:
    python server/app.py

    # Or with custom port
    FLASK_PORT=8080 python server/app.py

    # Enable authentication
    FLASK_REQUIRE_AUTH=true FLASK_AUTH_USERNAME=admin FLASK_AUTH_PASSWORD=secret python server/app.py
"""

import logging
from flask import Flask
from server import config
from lib.logging_config import setup_logging, kvlog

# Configure centralized logging
setup_logging(log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Import and register routes
from server.routes import register_routes
register_routes(app)

# Start config file watcher (auto-reload on config changes)
from lib.config_watcher import start_watcher
start_watcher(app)

kvlog(logger, logging.INFO, component='flask', event='configured',
      host=config.HOST, port=config.PORT, debug=config.DEBUG, auth_required=config.REQUIRE_AUTH)


def main():
    """Run the Flask development server"""
    kvlog(logger, logging.NOTICE, component='flask', event='starting')
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()

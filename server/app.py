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
import sys
from flask import Flask
from server import config

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Import and register routes
from server.routes import register_routes
register_routes(app)

logger.info(f"Flask server configured:")
logger.info(f"  Host: {config.HOST}")
logger.info(f"  Port: {config.PORT}")
logger.info(f"  Debug: {config.DEBUG}")
logger.info(f"  Auth Required: {config.REQUIRE_AUTH}")


def main():
    """Run the Flask development server"""
    logger.info("Starting Flask webhook server...")
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()

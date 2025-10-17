"""
Flask Routes for Webhook Endpoints

Defines all HTTP endpoints for iOS Shortcuts integration.
"""

import os
import sys
import subprocess
import logging
import time
from flask import request, jsonify, render_template
from server import config
from server.helpers import require_auth, run_automation_script
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all routes with the Flask app"""

    # Register blueprints
    from server.blueprints.api_device import api_device_bp
    from server.blueprints.webhooks import webhooks_bp
    from server.blueprints.location import location_bp
    from server.blueprints.logs import logs_bp
    from server.blueprints.api_system import api_system_bp
    from server.blueprints.api_admin import api_admin_bp
    from server.blueprints.ai import ai_bp

    app.register_blueprint(api_device_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(location_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(api_system_bp)
    app.register_blueprint(api_admin_bp)
    app.register_blueprint(ai_bp)

    @app.before_request
    def log_request_start():
        """Log incoming request and start timer"""
        request.start_time = time.time()
        kvlog(logger, logging.DEBUG,
              event='request_start',
              method=request.method,
              path=request.path,
              client=request.remote_addr)

    @app.after_request
    def log_request_end(response):
        """Log request completion with timing"""
        if hasattr(request, 'start_time'):
            duration_ms = int((time.time() - request.start_time) * 1000)
            kvlog(logger, logging.NOTICE,
                  event='request_complete',
                  method=request.method,
                  path=request.path,
                  status=response.status_code,
                  duration_ms=duration_ms)
        return response

    @app.route('/')
    def index():
        """Health check endpoint"""
        return jsonify({
            'service': 'py_home webhook server',
            'status': 'running',
            'version': '1.0.0'
        })

    @app.route('/status')
    def status():
        """Detailed status endpoint"""
        return jsonify({
            'service': 'py_home',
            'status': 'running',
            'auth_required': config.REQUIRE_AUTH,
            'endpoints': [
                '/dashboard',
                '/leaving-home',
                '/goodnight',
                '/im-home',
                '/good-morning',
                '/travel-time',
                '/update-location',
                '/location',
                '/logs',
                '/logs/<filename>',
                '/status'
            ]
        })

    @app.route('/dashboard')
    def dashboard():
        """Real-time system status dashboard (HTML UI)"""
        return render_template('dashboard.html')

    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        return jsonify({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(e):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

    logger.info("Routes registered successfully")

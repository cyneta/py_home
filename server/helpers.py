"""
Flask route helper functions

Shared utilities for authentication and automation script execution.
"""

import os
import sys
import subprocess
import logging
from functools import wraps
from flask import request, jsonify
from server import config
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)


def require_auth(f):
    """Decorator to require basic authentication if enabled"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not config.REQUIRE_AUTH:
            return f(*args, **kwargs)

        auth = request.authorization
        if not auth or auth.username != config.AUTH_USERNAME or auth.password != config.AUTH_PASSWORD:
            return jsonify({'error': 'Authentication required'}), 401

        return f(*args, **kwargs)
    return decorated_function


def run_automation_script(script_name, args=None):
    """
    Run an automation script in the background

    Args:
        script_name: Name of script in automations/ directory (e.g., 'leaving_home.py')
        args: Optional list of command-line arguments

    Returns:
        dict: Response with status
    """
    script_path = os.path.join(config.AUTOMATIONS_DIR, script_name)

    if not os.path.exists(script_path):
        kvlog(logger, logging.ERROR, event='script_not_found', script=script_name, path=script_path)
        return {'error': f'Script not found: {script_name}'}, 404

    # Build command
    cmd = [sys.executable, script_path]

    # Check for dry_run query parameter (takes precedence over config)
    dry_run = request.args.get('dry_run', '').lower() == 'true'
    if dry_run:
        cmd.append('--dry-run')
        kvlog(logger, logging.INFO, event='dry_run_enabled', script=script_name, source='query_param')

    if args:
        cmd.extend(args)

    try:
        # Run in background (don't wait for completion)
        subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True  # Detach from parent process
        )

        kvlog(logger, logging.INFO, event='automation_started', script=script_name, args=str(args or []))
        return {
            'status': 'started',
            'script': script_name,
            'args': args or []
        }, 200

    except Exception as e:
        kvlog(logger, logging.ERROR, event='automation_failed', script=script_name, error_type=type(e).__name__, error_msg=str(e))
        return {'error': str(e)}, 500

"""
Flask Routes for Webhook Endpoints

Defines all HTTP endpoints for iOS Shortcuts integration.
"""

import os
import sys
import subprocess
import logging
from functools import wraps
from flask import request, jsonify
from server import config

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
        logger.error(f"Script not found: {script_path}")
        return {'error': f'Script not found: {script_name}'}, 404

    # Build command
    cmd = [sys.executable, script_path]
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

        logger.info(f"Started automation: {script_name} with args: {args}")
        return {
            'status': 'started',
            'script': script_name,
            'args': args or []
        }, 200

    except Exception as e:
        logger.error(f"Failed to run script {script_name}: {e}")
        return {'error': str(e)}, 500


def register_routes(app):
    """Register all routes with the Flask app"""

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
                '/leaving-home',
                '/goodnight',
                '/im-home',
                '/good-morning',
                '/travel-time',
                '/status'
            ]
        })

    @app.route('/leaving-home', methods=['POST'])
    @require_auth
    def leaving_home():
        """Trigger leaving home automation"""
        logger.info("Received /leaving-home request")
        result, status_code = run_automation_script('leaving_home.py')
        return jsonify(result), status_code

    @app.route('/goodnight', methods=['POST'])
    @require_auth
    def goodnight():
        """Trigger goodnight automation"""
        logger.info("Received /goodnight request")
        result, status_code = run_automation_script('goodnight.py')
        return jsonify(result), status_code

    @app.route('/im-home', methods=['POST'])
    @require_auth
    def im_home():
        """Trigger I'm home automation"""
        logger.info("Received /im-home request")
        result, status_code = run_automation_script('im_home.py')
        return jsonify(result), status_code

    @app.route('/good-morning', methods=['POST'])
    @require_auth
    def good_morning():
        """Trigger good morning automation"""
        logger.info("Received /good-morning request")
        result, status_code = run_automation_script('good_morning.py')
        return jsonify(result), status_code

    @app.route('/travel-time', methods=['GET', 'POST'])
    @require_auth
    def travel_time():
        """
        Get travel time to destination

        Query params or POST body:
            destination: Where to get travel time to (default: Milwaukee, WI)

        Returns:
            JSON with travel time information
        """
        logger.info("Received /travel-time request")

        # Get destination from query params or POST body
        if request.method == 'POST':
            data = request.get_json() or {}
            destination = data.get('destination', 'Milwaukee, WI')
        else:
            destination = request.args.get('destination', 'Milwaukee, WI')

        # Run script synchronously to get results
        script_path = os.path.join(config.AUTOMATIONS_DIR, 'travel_time.py')

        try:
            result = subprocess.run(
                [sys.executable, script_path, destination],
                capture_output=True,
                text=True,
                timeout=15
            )

            if result.returncode == 0:
                # Parse JSON output from script
                import json
                output = json.loads(result.stdout)
                logger.info(f"Travel time to {destination}: {output.get('duration_in_traffic_minutes')} mins")
                return jsonify(output), 200
            else:
                logger.error(f"Script failed: {result.stderr}")
                return jsonify({'error': result.stderr}), 500

        except subprocess.TimeoutExpired:
            logger.error("Travel time script timed out")
            return jsonify({'error': 'Request timed out'}), 504
        except Exception as e:
            logger.error(f"Failed to get travel time: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/add-task', methods=['POST'])
    @require_auth
    def add_task():
        """
        Add a task via voice/iOS Shortcut

        POST body:
            task: Task text

        Returns:
            JSON with routing decision
        """
        logger.info("Received /add-task request")

        data = request.get_json() or {}
        task_text = data.get('task', '')

        if not task_text:
            return jsonify({'error': 'Task text required'}), 400

        # Run task router script
        result, status_code = run_automation_script('task_router.py', [task_text])
        return jsonify(result), status_code

    @app.route('/ai-command', methods=['POST'])
    @require_auth
    def ai_command():
        """
        Process natural language command via AI

        POST body:
            command: Natural language command (e.g., "turn off all lights")
            dry_run: Optional, if true just parse without executing

        Returns:
            JSON with parsed command and execution result

        Examples:
            {"command": "set temperature to 72"}
            {"command": "turn off bedroom lamp"}
            {"command": "make it warmer"}
            {"command": "what's the temperature?"}
        """
        logger.info("Received /ai-command request")

        data = request.get_json() or {}
        command = data.get('command', '')
        dry_run = data.get('dry_run', False)

        if not command:
            return jsonify({'error': 'Command text required'}), 400

        try:
            from server.ai_handler import process_command
            result = process_command(command, dry_run=dry_run)

            if result['status'] == 'error':
                return jsonify(result), 400

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"AI command processing failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'Failed to process command: {str(e)}'
            }), 500

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

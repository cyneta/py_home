"""
Flask Routes for Webhook Endpoints

Defines all HTTP endpoints for iOS Shortcuts integration.
"""

import os
import sys
import subprocess
import logging
import time
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


def register_routes(app):
    """Register all routes with the Flask app"""

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

    @app.route('/update-location', methods=['POST'])
    @require_auth
    def update_location():
        """
        Update user's current location from iOS Shortcuts geofencing

        POST body:
            lat: Latitude (required)
            lng: Longitude (required)
            trigger: Geofence trigger name (e.g., "leaving_work", "near_home", "arriving_home")
            trigger_automations: Whether to run arrival automations (default: true)

        Returns:
            JSON with location update status and triggered automations

        Example:
            {"lat": 45.4465, "lng": -122.6393, "trigger": "near_home"}
        """
        logger.info("Received /update-location request")

        data = request.get_json() or {}
        lat = data.get('lat')
        lng = data.get('lng')
        trigger = data.get('trigger', 'manual')
        trigger_automations = data.get('trigger_automations', True)

        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng required'}), 400

        try:
            from lib.location import update_location as update_loc
            from lib.location import should_trigger_arrival, get_eta_home

            # Update location
            result = update_loc(lat, lng, trigger)

            # Check if we should trigger arrival automations
            if trigger_automations:
                should_trigger, automation_type = should_trigger_arrival(trigger)

                if should_trigger:
                    eta = get_eta_home()

                    # Add ETA to result
                    result['eta'] = eta

                    # Trigger appropriate automation
                    if automation_type == 'preheat':
                        # Pre-heat house (20+ min away)
                        logger.info(f"Triggering preheat automation (ETA: {eta['duration_in_traffic_minutes']} min)")
                        run_automation_script('arrival_preheat.py', [str(eta['duration_in_traffic_minutes'])])
                        result['automation_triggered'] = 'preheat'
                        result['message'] = f"Pre-heating house. ETA: {eta['duration_in_traffic_minutes']} min"

                    elif automation_type == 'lights':
                        # Turn on lights (5-10 min away)
                        logger.info(f"Triggering lights automation (ETA: {eta['duration_in_traffic_minutes']} min)")
                        run_automation_script('arrival_lights.py')
                        result['automation_triggered'] = 'lights'
                        result['message'] = f"Turning on lights. ETA: {eta['duration_in_traffic_minutes']} min"

                    elif automation_type == 'full_arrival':
                        # Full arrival automation (at home)
                        logger.info("Triggering full arrival automation")
                        run_automation_script('im_home.py')
                        result['automation_triggered'] = 'full_arrival'
                        result['message'] = "Welcome home! Running arrival automation."
                else:
                    result['automation_triggered'] = None
                    result['message'] = f"Location updated ({result['distance_from_home_meters']:.0f}m from home)"
            else:
                result['automation_triggered'] = None
                result['message'] = "Location updated (automations disabled)"

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Failed to update location: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'message': f'Failed to update location: {str(e)}'
            }), 500

    @app.route('/location', methods=['GET'])
    @require_auth
    def get_location():
        """
        Get user's last known location and ETA home

        Returns:
            JSON with location data and ETA (if available)
        """
        logger.info("Received /location request")

        try:
            from lib.location import get_location as get_loc, get_eta_home

            location = get_loc()
            if not location:
                return jsonify({
                    'status': 'no_data',
                    'message': 'No location data available'
                }), 404

            # Add ETA if not home
            if not location['is_home']:
                eta = get_eta_home()
                location['eta'] = eta

            return jsonify(location), 200

        except Exception as e:
            logger.error(f"Failed to get location: {e}")
            return jsonify({
                'status': 'error',
                'message': f'Failed to get location: {str(e)}'
            }), 500

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

    @app.route('/logs', methods=['GET'])
    def list_logs():
        """
        List all available log files with metadata

        Returns:
            JSON with list of log files and their sizes/timestamps
        """
        logger.info("Received /logs request")

        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')

        try:
            if not os.path.exists(logs_dir):
                return jsonify({
                    'status': 'no_logs',
                    'message': 'Log directory does not exist',
                    'logs': []
                }), 200

            log_files = []
            for filename in os.listdir(logs_dir):
                filepath = os.path.join(logs_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    log_files.append({
                        'name': filename,
                        'size_bytes': stat.st_size,
                        'modified': stat.st_mtime,
                        'url': f'/logs/{filename}'
                    })

            # Sort by modified time, newest first
            log_files.sort(key=lambda x: x['modified'], reverse=True)

            return jsonify({
                'status': 'success',
                'logs_directory': logs_dir,
                'count': len(log_files),
                'logs': log_files
            }), 200

        except Exception as e:
            logger.error(f"Failed to list logs: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/logs/<filename>', methods=['GET'])
    def view_log(filename):
        """
        View contents of a specific log file

        Query params:
            lines: Number of lines to return (default: 100, max: 10000)
            tail: If true, return last N lines; if false, return first N lines (default: true)

        Returns:
            JSON with log contents or plain text if ?format=text
        """
        logger.info(f"Received /logs/{filename} request")

        # Security: prevent directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': 'Invalid filename'}), 400

        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')
        filepath = os.path.join(logs_dir, filename)

        if not os.path.exists(filepath):
            return jsonify({'error': 'Log file not found'}), 404

        try:
            lines_requested = min(int(request.args.get('lines', 100)), 10000)
            tail_mode = request.args.get('tail', 'true').lower() == 'true'
            format_type = request.args.get('format', 'json')

            with open(filepath, 'r') as f:
                if tail_mode:
                    # Read last N lines
                    all_lines = f.readlines()
                    lines = all_lines[-lines_requested:] if len(all_lines) > lines_requested else all_lines
                else:
                    # Read first N lines
                    lines = [f.readline() for _ in range(lines_requested)]

            content = ''.join(lines)

            if format_type == 'text':
                from flask import Response
                return Response(content, mimetype='text/plain')
            else:
                return jsonify({
                    'status': 'success',
                    'filename': filename,
                    'lines_returned': len(lines),
                    'tail_mode': tail_mode,
                    'content': content
                }), 200

        except Exception as e:
            logger.error(f"Failed to read log file {filename}: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
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

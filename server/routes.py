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

    @app.route('/api/nest/status')
    def api_nest_status():
        """Get Nest thermostat status (JSON API for dashboard)"""
        try:
            from components.nest import NestAPI
            nest = NestAPI(dry_run=False)
            status = nest.get_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Failed to get Nest status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/sensibo/status')
    def api_sensibo_status():
        """Get Sensibo AC status (JSON API for dashboard)"""
        try:
            from components.sensibo import SensiboAPI
            sensibo = SensiboAPI(dry_run=False)
            status = sensibo.get_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Failed to get Sensibo status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/tapo/status')
    def api_tapo_status():
        """Get Tapo smart outlets status (JSON API for dashboard)"""
        try:
            from components.tapo import TapoAPI
            tapo = TapoAPI(dry_run=False)
            devices = tapo.get_all_status()
            return jsonify({'devices': devices}), 200
        except Exception as e:
            logger.error(f"Failed to get Tapo status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/night-mode')
    def api_night_mode():
        """Get night mode status (JSON API for dashboard)"""
        try:
            from lib.night_mode import is_night_mode
            import platform
            import subprocess

            # Get system uptime
            if platform.system() == 'Linux':
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    days = int(uptime_seconds // 86400)
                    hours = int((uptime_seconds % 86400) // 3600)
                    uptime = f"{days}d {hours}h"
            else:
                uptime = "Unknown"

            return jsonify({
                'night_mode': is_night_mode(),
                'uptime': uptime
            }), 200
        except Exception as e:
            logger.error(f"Failed to get night mode status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/dashboard')
    def dashboard():
        """Real-time system status dashboard (HTML UI)"""
        from flask import Response

        html = """
<!DOCTYPE html>
<html>
<head>
    <title>py_home Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #30363d;
        }
        h1 { color: #58a6ff; font-size: 32px; }
        .last-updated { color: #8b949e; font-size: 14px; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
        }
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #21262d;
        }
        .status-row:last-child { border-bottom: none; }
        .status-label { color: #8b949e; }
        .status-value {
            color: #c9d1d9;
            font-weight: 500;
        }
        .status-good { color: #3fb950; }
        .status-warning { color: #d29922; }
        .status-error { color: #f85149; }
        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-online {
            background: #1a472a;
            color: #3fb950;
        }
        .badge-offline {
            background: #3d1f1f;
            color: #f85149;
        }
        .badge-home {
            background: #1a472a;
            color: #3fb950;
        }
        .badge-away {
            background: #392f1a;
            color: #d29922;
        }
        .temp-display {
            font-size: 36px;
            font-weight: 700;
            color: #58a6ff;
            margin: 10px 0;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #8b949e;
        }
        .error {
            color: #f85149;
            padding: 15px;
            background: #3d1f1f;
            border: 1px solid #f85149;
            border-radius: 6px;
        }
        .refresh-btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        .refresh-btn:hover {
            background: #30363d;
            border-color: #58a6ff;
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏠 py_home Dashboard</h1>
            <div>
                <span class="last-updated" id="lastUpdated">Loading...</span>
                <button class="refresh-btn" onclick="loadDashboard()">🔄 Refresh</button>
            </div>
        </header>

        <div id="dashboard">
            <div class="loading">Loading dashboard...</div>
        </div>
    </div>

    <script>
        async function loadDashboard() {
            const dashboardEl = document.getElementById('dashboard');
            const lastUpdatedEl = document.getElementById('lastUpdated');

            try {
                // Load all status data in parallel
                const [nest, sensibo, tapo, location, nightMode] = await Promise.all([
                    fetchNestStatus(),
                    fetchSensiboStatus(),
                    fetchTapoStatus(),
                    fetchLocation(),
                    fetchNightMode()
                ]);

                // Build dashboard HTML
                dashboardEl.innerHTML = `
                    <div class="grid">
                        ${renderNestCard(nest)}
                        ${renderSensiboCard(sensibo)}
                        ${renderTapoCard(tapo)}
                        ${renderLocationCard(location)}
                        ${renderSystemCard(nightMode)}
                    </div>
                `;

                lastUpdatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            } catch (error) {
                dashboardEl.innerHTML = `
                    <div class="error">Failed to load dashboard: ${error.message}</div>
                `;
            }
        }

        async function fetchNestStatus() {
            // In dry-run mode, return mock data
            try {
                const response = await fetch('/api/nest/status');
                if (response.ok) {
                    return await response.json();
                }
            } catch (e) {}

            // Mock data for now (will implement API endpoint)
            return {
                current_temp_f: 72.5,
                mode: 'HEAT',
                heat_setpoint_f: 72,
                hvac_status: 'OFF',
                humidity: 52
            };
        }

        async function fetchSensiboStatus() {
            try {
                const response = await fetch('/api/sensibo/status');
                if (response.ok) {
                    return await response.json();
                }
            } catch (e) {}

            return {
                on: true,
                mode: 'heat',
                target_temp_f: 70,
                current_temp_f: 70.0,
                humidity: 65.6
            };
        }

        async function fetchTapoStatus() {
            try {
                const response = await fetch('/api/tapo/status');
                if (response.ok) {
                    return await response.json();
                }
            } catch (e) {}

            return {
                devices: [
                    {name: 'Livingroom Lamp', on: true},
                    {name: 'Bedroom Left Lamp', on: true},
                    {name: 'Bedroom Right Lamp', on: true},
                    {name: 'Heater', on: false}
                ]
            };
        }

        async function fetchLocation() {
            try {
                const response = await fetch('/location');
                if (response.ok) {
                    return await response.json();
                }
            } catch (e) {}

            return {
                is_home: true,
                distance_from_home_meters: 0
            };
        }

        async function fetchNightMode() {
            // Check if night mode file exists
            return {
                night_mode: false,
                uptime: '3 days'
            };
        }

        function renderNestCard(data) {
            const statusClass = data.hvac_status === 'OFF' ? 'status-good' : 'status-warning';
            return `
                <div class="card">
                    <div class="card-title">🌡️ Nest Thermostat</div>
                    <div class="temp-display">${data.current_temp_f}°F</div>
                    <div class="status-row">
                        <span class="status-label">Mode</span>
                        <span class="status-value">${data.mode}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Target</span>
                        <span class="status-value">${data.heat_setpoint_f || data.cool_setpoint_f || 'ECO'}°F</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">HVAC</span>
                        <span class="status-value ${statusClass}">${data.hvac_status}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Humidity</span>
                        <span class="status-value">${data.humidity}%</span>
                    </div>
                </div>
            `;
        }

        function renderSensiboCard(data) {
            const powerBadge = data.on ? 'badge-online' : 'badge-offline';
            const powerText = data.on ? 'ON' : 'OFF';
            return `
                <div class="card">
                    <div class="card-title">❄️ Sensibo AC (Master Suite)</div>
                    <div class="temp-display">${data.current_temp_f}°F</div>
                    <div class="status-row">
                        <span class="status-label">Power</span>
                        <span class="badge ${powerBadge}">${powerText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Mode</span>
                        <span class="status-value">${data.mode.toUpperCase()}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Target</span>
                        <span class="status-value">${data.target_temp_f}°F</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Humidity</span>
                        <span class="status-value">${data.humidity}%</span>
                    </div>
                </div>
            `;
        }

        function renderTapoCard(data) {
            return `
                <div class="card">
                    <div class="card-title">💡 Smart Outlets</div>
                    ${data.devices.map(device => `
                        <div class="status-row">
                            <span class="status-label">${device.name}</span>
                            <span class="badge ${device.on ? 'badge-online' : 'badge-offline'}">
                                ${device.on ? 'ON' : 'OFF'}
                            </span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function renderLocationCard(data) {
            const locationBadge = data.is_home ? 'badge-home' : 'badge-away';
            const locationText = data.is_home ? 'HOME' : 'AWAY';
            const distance = data.is_home ? '0 m' : `${Math.round(data.distance_from_home_meters)} m`;

            return `
                <div class="card">
                    <div class="card-title">📍 Location</div>
                    <div class="status-row">
                        <span class="status-label">Status</span>
                        <span class="badge ${locationBadge}">${locationText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Distance from Home</span>
                        <span class="status-value">${distance}</span>
                    </div>
                    ${data.eta ? `
                        <div class="status-row">
                            <span class="status-label">ETA</span>
                            <span class="status-value">${data.eta.duration_in_traffic_minutes} min</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        function renderSystemCard(data) {
            const modeBadge = data.night_mode ? 'badge-warning' : 'badge-online';
            const modeText = data.night_mode ? 'NIGHT MODE' : 'DAY MODE';

            return `
                <div class="card">
                    <div class="card-title">⚙️ System</div>
                    <div class="status-row">
                        <span class="status-label">Mode</span>
                        <span class="badge ${modeBadge}">${modeText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Uptime</span>
                        <span class="status-value">${data.uptime}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Service</span>
                        <span class="status-value status-good">Running</span>
                    </div>
                </div>
            `;
        }

        // Load dashboard on page load
        loadDashboard();

        // Auto-refresh every 5 seconds
        setInterval(loadDashboard, 5000);
    </script>
</body>
</html>
        """
        return Response(html, mimetype='text/html')

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

    @app.route('/logs')
    def logs_ui():
        """
        Web UI for browsing logs (HTML) or API endpoint (JSON)

        Returns HTML if accessed from browser, JSON if Accept header is application/json
        """
        from flask import Response

        # Check if client wants JSON (API client) or HTML (browser)
        if request.accept_mimetypes.best == 'application/json' or request.args.get('format') == 'json':
            return list_logs()

        # Serve HTML UI
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>py_home Logs</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { margin-bottom: 10px; color: #58a6ff; }
        .subtitle { color: #8b949e; margin-bottom: 30px; }
        .log-list { display: grid; gap: 15px; margin-bottom: 30px; }
        .log-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .log-card:hover {
            border-color: #58a6ff;
            background: #1c2128;
        }
        .log-card.active {
            border-color: #58a6ff;
            background: #1c2128;
        }
        .log-name {
            font-size: 18px;
            font-weight: 600;
            color: #58a6ff;
            margin-bottom: 8px;
        }
        .log-meta {
            display: flex;
            gap: 20px;
            font-size: 14px;
            color: #8b949e;
        }
        .log-viewer {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
            display: none;
        }
        .log-viewer.active { display: block; }
        .log-controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .btn {
            background: #21262d;
            border: 1px solid #30363d;
            color: #c9d1d9;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        .btn:hover {
            background: #30363d;
            border-color: #58a6ff;
        }
        .btn.active {
            background: #58a6ff;
            border-color: #58a6ff;
            color: #0d1117;
        }
        pre {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 15px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.6;
            color: #c9d1d9;
            max-height: 600px;
            overflow-y: auto;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #8b949e;
        }
        .error {
            color: #f85149;
            padding: 15px;
            background: #161b22;
            border: 1px solid #f85149;
            border-radius: 6px;
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .log-controls { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏠 py_home Logs</h1>
        <div class="subtitle">Real-time monitoring and automation logs</div>

        <div class="log-list" id="logList">
            <div class="loading">Loading logs...</div>
        </div>

        <div class="log-viewer" id="logViewer">
            <div class="log-controls">
                <button class="btn active" onclick="setLines(50)">50 lines</button>
                <button class="btn" onclick="setLines(100)">100 lines</button>
                <button class="btn" onclick="setLines(200)">200 lines</button>
                <button class="btn" onclick="setLines(500)">500 lines</button>
                <button class="btn" onclick="refresh()">🔄 Refresh</button>
                <button class="btn" onclick="toggleAutoRefresh()">⏱️ Auto-refresh: OFF</button>
            </div>
            <pre id="logContent">Select a log file to view</pre>
        </div>
    </div>

    <script>
        let currentLog = null;
        let currentLines = 50;
        let autoRefreshInterval = null;

        async function loadLogList() {
            try {
                const response = await fetch('/logs?format=json');
                const data = await response.json();

                const listEl = document.getElementById('logList');
                if (data.logs.length === 0) {
                    listEl.innerHTML = '<div class="loading">No logs found</div>';
                    return;
                }

                listEl.innerHTML = data.logs.map(log => {
                    const size = (log.size_bytes / 1024).toFixed(1);
                    const date = new Date(log.modified * 1000).toLocaleString();
                    return `
                        <div class="log-card" onclick="viewLog('${log.name}')">
                            <div class="log-name">${log.name}</div>
                            <div class="log-meta">
                                <span>📦 ${size} KB</span>
                                <span>🕐 ${date}</span>
                            </div>
                        </div>
                    `;
                }).join('');
            } catch (error) {
                document.getElementById('logList').innerHTML =
                    `<div class="error">Failed to load logs: ${error.message}</div>`;
            }
        }

        async function viewLog(filename) {
            currentLog = filename;
            document.getElementById('logViewer').classList.add('active');

            // Update active card
            document.querySelectorAll('.log-card').forEach(card => {
                card.classList.toggle('active', card.textContent.includes(filename));
            });

            await loadLogContent();
        }

        async function loadLogContent() {
            if (!currentLog) return;

            const contentEl = document.getElementById('logContent');
            contentEl.textContent = 'Loading...';

            try {
                const response = await fetch(
                    `/logs/${currentLog}?lines=${currentLines}&format=text`
                );
                const text = await response.text();
                contentEl.textContent = text || '(empty log)';
            } catch (error) {
                contentEl.textContent = `Error loading log: ${error.message}`;
            }
        }

        function setLines(lines) {
            currentLines = lines;
            document.querySelectorAll('.log-controls .btn').forEach((btn, i) => {
                btn.classList.toggle('active', i === [50, 100, 200, 500].indexOf(lines));
            });
            loadLogContent();
        }

        function refresh() {
            loadLogList();
            if (currentLog) loadLogContent();
        }

        function toggleAutoRefresh() {
            const btn = document.querySelectorAll('.log-controls .btn')[5];
            if (autoRefreshInterval) {
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
                btn.textContent = '⏱️ Auto-refresh: OFF';
                btn.classList.remove('active');
            } else {
                autoRefreshInterval = setInterval(refresh, 5000);
                btn.textContent = '⏱️ Auto-refresh: ON';
                btn.classList.add('active');
            }
        }

        // Load logs on page load
        loadLogList();

        // Auto-refresh log list every 30 seconds
        setInterval(loadLogList, 30000);
    </script>
</body>
</html>
        """
        return Response(html, mimetype='text/html')

    def list_logs():
        """
        List all available log files with metadata (JSON API)

        Returns:
            JSON with list of log files and their sizes/timestamps
        """
        logger.info("Received /logs API request")

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

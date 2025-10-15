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

    @app.route('/api/tempstick/status')
    def api_tempstick_status():
        """Get TempStick sensor status (JSON API for dashboard)"""
        try:
            from services.tempstick import TempStickAPI
            tempstick = TempStickAPI()
            status = tempstick.get_sensor_data()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Failed to get TempStick status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/night-mode')
    def api_night_mode():
        """Get sleep time status (DEPRECATED - use /api/system-status)"""
        try:
            from lib.hvac_logic import is_sleep_time
            from server import FLASK_START_TIME

            # Calculate Flask uptime (not Pi uptime)
            uptime_seconds = time.time() - FLASK_START_TIME
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)

            if days > 0:
                uptime = f"{days}d {hours}h"
            else:
                uptime = f"{hours}h"

            # Return sleep_time status (replaces old night_mode flag)
            return jsonify({
                'night_mode': is_sleep_time(),  # Keep key name for backward compatibility
                'sleep_time': is_sleep_time(),  # New name for clarity
                'uptime': uptime
            }), 200
        except Exception as e:
            logger.error(f"Failed to get sleep time status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/presence')
    def api_presence():
        """Get current presence status from .presence_state file"""
        try:
            state_file = os.path.join(os.path.dirname(__file__), '..', '.presence_state')

            if not os.path.exists(state_file):
                return jsonify({
                    'is_home': None,
                    'state': 'unknown',
                    'source': 'unknown',
                    'last_updated': None,
                    'age_seconds': None
                }), 200

            # Read state
            with open(state_file, 'r') as f:
                state = f.read().strip().lower()

            # Get file modification time
            mtime = os.path.getmtime(state_file)
            from datetime import datetime
            age_seconds = time.time() - mtime
            last_updated = datetime.fromtimestamp(mtime).isoformat()

            return jsonify({
                'is_home': state == 'home',
                'state': state,
                'source': 'legacy',  # Deprecated: was presence_monitor, now using iOS geofencing
                'last_updated': last_updated,
                'age_seconds': round(age_seconds, 1)
            }), 200

        except Exception as e:
            logger.error(f"Failed to get presence status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/system-status')
    def api_system_status():
        """Get comprehensive system status with Flask uptime"""
        try:
            from server import FLASK_START_TIME
            import platform

            # Calculate Flask uptime
            uptime_seconds = time.time() - FLASK_START_TIME
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)

            if days > 0:
                uptime = f"{days}d {hours}h"
            elif hours > 0:
                uptime = f"{hours}h {minutes}m"
            else:
                uptime = f"{minutes}m"

            # Get sleep time status (replaces old night_mode flag system)
            from lib.hvac_logic import is_sleep_time
            night_mode = is_sleep_time()  # Variable name kept for backward compatibility

            # Check system health
            health_status = 'operational'
            services = {}

            # Note: presence_monitor health check removed (deprecated component)
            # iOS geofencing via /update-location is now used for presence detection

            # Check automation disable flag
            disable_file = os.path.join(os.path.dirname(__file__), '..', '.automation_disabled')
            automations_enabled = not os.path.exists(disable_file)

            return jsonify({
                'status': health_status,
                'flask_uptime': uptime,
                'flask_uptime_seconds': int(uptime_seconds),
                'night_mode': night_mode,
                'automations_enabled': automations_enabled,
                'services': services,
                'platform': platform.system()
            }), 200

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/automation-control', methods=['GET', 'POST'])
    def api_automation_control():
        """Enable/disable all automations (master switch)"""
        disable_file = os.path.join(os.path.dirname(__file__), '..', '.automation_disabled')

        if request.method == 'GET':
            # Get current status
            enabled = not os.path.exists(disable_file)
            return jsonify({
                'automations_enabled': enabled,
                'status': 'enabled' if enabled else 'disabled'
            }), 200

        elif request.method == 'POST':
            # Set status
            data = request.get_json() or {}
            enable = data.get('enable', True)

            try:
                if enable:
                    # Enable automations (remove disable file)
                    if os.path.exists(disable_file):
                        os.remove(disable_file)
                    kvlog(logger, logging.NOTICE, event='automations_enabled', user='api')
                    return jsonify({
                        'automations_enabled': True,
                        'status': 'enabled',
                        'message': 'Automations enabled'
                    }), 200
                else:
                    # Disable automations (create disable file)
                    with open(disable_file, 'w') as f:
                        f.write(f"Disabled at {time.time()}\n")
                    kvlog(logger, logging.NOTICE, event='automations_disabled', user='api')
                    return jsonify({
                        'automations_enabled': False,
                        'status': 'disabled',
                        'message': 'Automations disabled'
                    }), 200

            except Exception as e:
                logger.error(f"Failed to change automation status: {e}")
                return jsonify({'error': str(e)}), 500

    @app.route('/api/shutdown', methods=['POST'])
    def api_shutdown():
        """
        Safely shutdown the Raspberry Pi

        Returns:
            JSON with shutdown status

        Note: After triggering shutdown, LED will stop blinking within 30-60 seconds.
              Wait for LED to go dark before unplugging power.
        """
        kvlog(logger, logging.WARNING, event='shutdown_requested', user='api', source=request.remote_addr)

        try:
            # Trigger shutdown in background (gives us time to return response)
            import platform
            if platform.system() == 'Linux':
                subprocess.Popen(['sudo', 'shutdown', '-h', 'now'])
                return jsonify({
                    'status': 'shutdown_initiated',
                    'message': 'System shutting down. Wait for LED to stop blinking before unplugging power.',
                    'estimated_time_seconds': 60
                }), 200
            else:
                return jsonify({
                    'status': 'not_supported',
                    'message': 'Shutdown only supported on Linux/Raspberry Pi',
                    'platform': platform.system()
                }), 400

        except Exception as e:
            kvlog(logger, logging.ERROR, event='shutdown_failed', error_type=type(e).__name__, error_msg=str(e))
            return jsonify({'error': str(e)}), 500

    @app.route('/api/git-pull', methods=['POST'])
    def api_git_pull():
        """
        Pull latest changes from git repository (includes updated .env with new tokens)

        POST body (optional):
            restart_after: Boolean, whether to restart Flask after pull (default: false)

        Returns:
            JSON with git pull status

        Use case: Self-recovery when tokens are updated in repo
        """
        data = request.get_json() or {}
        restart_after = data.get('restart_after', False)

        kvlog(logger, logging.WARNING, event='git_pull_requested', user='api', source=request.remote_addr, restart_after=restart_after)

        try:
            import platform
            repo_dir = os.path.dirname(os.path.dirname(__file__))

            # Run git pull
            result = subprocess.run(
                ['git', 'pull'],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                kvlog(logger, logging.NOTICE, event='git_pull_success', output=result.stdout.strip())

                response = {
                    'status': 'success',
                    'message': 'Git pull completed successfully',
                    'output': result.stdout.strip(),
                    'restarting': restart_after
                }

                # Optionally restart service after pull
                if restart_after and platform.system() == 'Linux':
                    subprocess.Popen(['sudo', 'systemctl', 'restart', 'py_home'])
                    response['message'] += '. Flask restarting...'

                return jsonify(response), 200
            else:
                kvlog(logger, logging.ERROR, event='git_pull_failed', error=result.stderr.strip())
                return jsonify({
                    'status': 'error',
                    'message': 'Git pull failed',
                    'error': result.stderr.strip()
                }), 500

        except subprocess.TimeoutExpired:
            kvlog(logger, logging.ERROR, event='git_pull_timeout')
            return jsonify({'error': 'Git pull timed out after 30s'}), 504
        except Exception as e:
            kvlog(logger, logging.ERROR, event='git_pull_failed', error_type=type(e).__name__, error_msg=str(e))
            return jsonify({'error': str(e)}), 500

    @app.route('/api/service-control', methods=['POST'])
    def api_service_control():
        """
        Control py_home Flask service (stop/start/restart)

        POST body:
            action: 'stop', 'start', or 'restart'

        Returns:
            JSON with service control status
        """
        data = request.get_json() or {}
        action = data.get('action', '').lower()

        if action not in ['stop', 'start', 'restart']:
            return jsonify({'error': 'Invalid action. Must be stop, start, or restart'}), 400

        kvlog(logger, logging.WARNING, event='service_control_requested', action=action, user='api', source=request.remote_addr)

        try:
            import platform
            if platform.system() == 'Linux':
                # Trigger service control in background (gives us time to return response)
                subprocess.Popen(['sudo', 'systemctl', action, 'py_home'])

                return jsonify({
                    'status': 'initiated',
                    'action': action,
                    'message': f'Service {action} initiated. Flask will {action} shortly.',
                    'note': 'Restart' if action == 'restart' else f'Service will {action}'
                }), 200
            else:
                return jsonify({
                    'status': 'not_supported',
                    'message': 'Service control only supported on Linux',
                    'platform': platform.system()
                }), 400

        except Exception as e:
            kvlog(logger, logging.ERROR, event='service_control_failed', action=action, error_type=type(e).__name__, error_msg=str(e))
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
        .card-wide {
            grid-column: span 4;
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
        .log-preview {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 10px;
            font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 11px;
            line-height: 1.4;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
            margin-bottom: 10px;
        }
        .view-logs-link {
            display: inline-block;
            color: #58a6ff;
            text-decoration: none;
            font-size: 13px;
            margin-top: 5px;
        }
        .view-logs-link:hover {
            text-decoration: underline;
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
        // Fetch with timeout helper
        async function fetchWithTimeout(url, timeout = 5000) {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);

            try {
                const response = await fetch(url, { signal: controller.signal });
                clearTimeout(id);
                return response;
            } catch (error) {
                clearTimeout(id);
                throw error;
            }
        }

        async function loadDashboard() {
            const dashboardEl = document.getElementById('dashboard');
            const lastUpdatedEl = document.getElementById('lastUpdated');

            try {
                // Load all status data in parallel
                const [nest, sensibo, tapo, tempstick, presence, systemStatus, logs] = await Promise.all([
                    fetchNestStatus(),
                    fetchSensiboStatus(),
                    fetchTapoStatus(),
                    fetchTempStickStatus(),
                    fetchPresence(),
                    fetchSystemStatus(),
                    fetchAutomationLogs()
                ]);

                // Build dashboard HTML
                dashboardEl.innerHTML = `
                    <div class="grid">
                        ${renderNestCard(nest)}
                        ${renderSensiboCard(sensibo)}
                        ${renderTempStickCard(tempstick)}
                        ${renderTapoCard(tapo)}
                        ${renderPresenceCard(presence)}
                        ${renderSystemCard(systemStatus)}
                        ${renderLogsCard(logs)}
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
            try {
                const response = await fetchWithTimeout('/api/nest/status', 10000);
                if (response.ok) {
                    const data = await response.json();
                    data._stale = false;
                    data._error = false;
                    return data;
                }
            } catch (e) {
                return {
                    _error: true,
                    error: e.message,
                    current_temp_f: 0,
                    mode: 'UNKNOWN',
                    hvac_status: 'ERROR'
                };
            }

            // Fallback mock data
            return {
                current_temp_f: 72.5,
                mode: 'HEAT',
                heat_setpoint_f: 72,
                hvac_status: 'OFF',
                humidity: 52,
                _stale: false,
                _error: false
            };
        }

        async function fetchSensiboStatus() {
            try {
                const response = await fetchWithTimeout('/api/sensibo/status', 10000);
                if (response.ok) {
                    const data = await response.json();
                    data._stale = false;
                    data._error = false;
                    return data;
                }
            } catch (e) {
                return {
                    _error: true,
                    error: e.message,
                    on: false,
                    mode: 'unknown',
                    current_temp_f: 0
                };
            }

            return {
                on: true,
                mode: 'heat',
                target_temp_f: 70,
                current_temp_f: 70.0,
                current_humidity: 65.6,
                _stale: false,
                _error: false
            };
        }

        async function fetchTapoStatus() {
            try {
                const response = await fetchWithTimeout('/api/tapo/status', 30000);
                if (response.ok) {
                    const data = await response.json();
                    data._stale = false;
                    data._error = false;
                    return data;
                }
            } catch (e) {
                return {
                    _error: true,
                    error: e.message,
                    devices: []
                };
            }

            return {
                devices: [
                    {name: 'Livingroom Lamp', on: true},
                    {name: 'Bedroom Left Lamp', on: true},
                    {name: 'Bedroom Right Lamp', on: true},
                    {name: 'Heater', on: false}
                ],
                _stale: false,
                _error: false
            };
        }

        async function fetchTempStickStatus() {
            try {
                const response = await fetchWithTimeout('/api/tempstick/status', 10000);
                if (response.ok) {
                    const data = await response.json();
                    data._stale = false;
                    data._error = false;
                    return data;
                }
            } catch (e) {
                return {
                    _error: true,
                    error: e.message,
                    temperature_f: 0,
                    humidity: 0,
                    is_online: false
                };
            }

            return {
                temperature_f: 72.0,
                humidity: 45.0,
                battery_pct: 100,
                is_online: true,
                sensor_name: 'TempStick',
                _stale: false,
                _error: false
            };
        }

        async function fetchPresence() {
            try {
                const response = await fetchWithTimeout('/api/presence', 5000);
                if (response.ok) {
                    const data = await response.json();

                    // Check staleness (5 minutes = 300 seconds)
                    if (data.age_seconds !== null && data.age_seconds > 300) {
                        data._stale = true;
                    } else {
                        data._stale = false;
                    }
                    data._error = false;
                    return data;
                }
            } catch (e) {
                return {
                    _error: true,
                    error: e.message,
                    state: 'unknown',
                    is_home: null
                };
            }

            return {
                is_home: null,
                state: 'unknown',
                source: 'unknown',
                _stale: true,
                _error: false
            };
        }

        async function fetchSystemStatus() {
            try {
                const response = await fetchWithTimeout('/api/system-status', 5000);
                if (response.ok) {
                    const data = await response.json();
                    data._stale = false;
                    data._error = false;
                    return data;
                }
            } catch (e) {
                return {
                    _error: true,
                    error: e.message,
                    status: 'error',
                    flask_uptime: 'unknown',
                    night_mode: false,
                    automations_enabled: false
                };
            }

            return {
                status: 'unknown',
                flask_uptime: 'unknown',
                night_mode: false,
                automations_enabled: true,
                _stale: false,
                _error: false
            };
        }

        async function fetchAutomationLogs() {
            try {
                const response = await fetchWithTimeout('/logs/automations.log?lines=20&format=text', 5000);
                if (response.ok) {
                    const text = await response.text();
                    // Reverse lines so newest appears first
                    const reversedText = text.trim().split('\\n').reverse().join('\\n');
                    return {
                        content: reversedText,
                        _error: false
                    };
                }
            } catch (e) {
                return {
                    content: '',
                    _error: true,
                    error: e.message
                };
            }

            return {
                content: 'No logs available',
                _error: false
            };
        }

        function formatAge(ageSeconds) {
            if (ageSeconds === null) return 'unknown';
            if (ageSeconds < 60) return `${Math.round(ageSeconds)}s ago`;
            if (ageSeconds < 3600) return `${Math.round(ageSeconds / 60)}m ago`;
            return `${Math.round(ageSeconds / 3600)}h ago`;
        }

        function renderNestCard(data) {
            const statusClass = data.hvac_status === 'OFF' ? 'status-good' : 'status-warning';
            const staleWarning = data._stale ? '<div class="status-row"><span class="status-warning">⚠️ Data may be stale</span></div>' : '';
            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading data</span></div>' : '';

            // Determine target temperature display
            let targetTemp = '';
            if (data.eco_mode === 'MANUAL_ECO' && data.eco_heat_f && data.eco_cool_f) {
                // In ECO mode: show range
                targetTemp = `ECO (${data.eco_heat_f}-${data.eco_cool_f}°F)`;
            } else if (data.heat_setpoint_f) {
                targetTemp = `${data.heat_setpoint_f}°F`;
            } else if (data.cool_setpoint_f) {
                targetTemp = `${data.cool_setpoint_f}°F`;
            } else {
                targetTemp = 'N/A';
            }

            return `
                <div class="card">
                    <div class="card-title">🌡️ Nest Thermostat</div>
                    ${errorWarning}
                    ${staleWarning}
                    <div class="temp-display">${data.current_temp_f}°F</div>
                    <div class="status-row">
                        <span class="status-label">Mode</span>
                        <span class="status-value">${data.mode}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Target</span>
                        <span class="status-value">${targetTemp}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">HVAC</span>
                        <span class="status-value ${statusClass}">${data.hvac_status}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Humidity</span>
                        <span class="status-value">${data.current_humidity != null ? data.current_humidity + '%' : 'N/A'}</span>
                    </div>
                </div>
            `;
        }

        function renderSensiboCard(data) {
            const hvacStatus = data.on ? 'RUNNING' : 'OFF';
            const statusClass = data.on ? 'status-warning' : 'status-good';
            const staleWarning = data._stale ? '<div class="status-row"><span class="status-warning">⚠️ Data may be stale</span></div>' : '';
            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading data</span></div>' : '';

            return `
                <div class="card">
                    <div class="card-title">❄️ Sensibo AC (Master Suite)</div>
                    ${errorWarning}
                    ${staleWarning}
                    <div class="temp-display">${data.current_temp_f}°F</div>
                    <div class="status-row">
                        <span class="status-label">Mode</span>
                        <span class="status-value">${data.mode.toUpperCase()}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Target</span>
                        <span class="status-value">${data.target_temp_f}°F</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">HVAC</span>
                        <span class="status-value ${statusClass}">${hvacStatus}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Humidity</span>
                        <span class="status-value">${data.current_humidity != null ? data.current_humidity + '%' : 'N/A'}</span>
                    </div>
                </div>
            `;
        }

        function renderTempStickCard(data) {
            const statusBadge = data.is_online ? 'badge-online' : 'badge-offline';
            const statusText = data.is_online ? 'ONLINE' : 'OFFLINE';
            const staleWarning = data._stale ? '<div class="status-row"><span class="status-warning">⚠️ Data may be stale</span></div>' : '';
            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading data</span></div>' : '';

            // Battery level color
            let batteryClass = 'status-good';
            if (data.battery_pct < 20) batteryClass = 'status-error';
            else if (data.battery_pct < 50) batteryClass = 'status-warning';

            return `
                <div class="card">
                    <div class="card-title">🌡️ ${data.sensor_name || 'TempStick'}</div>
                    ${errorWarning}
                    ${staleWarning}
                    <div class="temp-display">${data.temperature_f}°F</div>
                    <div class="status-row">
                        <span class="status-label">Humidity</span>
                        <span class="status-value">${data.humidity}%</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Status</span>
                        <span class="badge ${statusBadge}">${statusText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Battery</span>
                        <span class="status-value ${batteryClass}">${data.battery_pct}%</span>
                    </div>
                </div>
            `;
        }

        function renderTapoCard(data) {
            const staleWarning = data._stale ? '<div class="status-row"><span class="status-warning">⚠️ Data may be stale</span></div>' : '';
            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading data</span></div>' : '';

            return `
                <div class="card">
                    <div class="card-title">💡 Smart Outlets</div>
                    ${errorWarning}
                    ${staleWarning}
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

        function renderPresenceCard(data) {
            const locationBadge = data.is_home === true ? 'badge-home' :
                                  data.is_home === false ? 'badge-away' : 'badge-offline';
            const locationText = data.is_home === true ? 'HOME' :
                                 data.is_home === false ? 'AWAY' : 'UNKNOWN';

            // Check if data is stale (>5 minutes)
            const isStale = data.age_seconds !== null && data.age_seconds > 300;
            const ageText = formatAge(data.age_seconds);
            const staleClass = isStale ? 'status-warning' : '';
            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading presence</span></div>' : '';

            // Map source to user-friendly name
            const sourceMap = {
                'presence_monitor': 'iOS Geofencing',
                'legacy': 'iOS Geofencing',
                'unknown': 'Unknown'
            };
            const sourceName = sourceMap[data.source] || data.source || 'Unknown';

            return `
                <div class="card">
                    <div class="card-title">📍 Presence</div>
                    ${errorWarning}
                    <div class="status-row">
                        <span class="status-label">Status</span>
                        <span class="badge ${locationBadge}">${locationText}</span>
                    </div>
                    ${data.last_updated ? `
                        <div class="status-row">
                            <span class="status-label">Last Checked</span>
                            <span class="status-value ${staleClass}">${isStale ? '⚠️ ' : ''}${ageText}</span>
                        </div>
                    ` : ''}
                    <div class="status-row">
                        <span class="status-label">Source</span>
                        <span class="status-value">${sourceName}</span>
                    </div>
                </div>
            `;
        }

        function renderSystemCard(data) {
            const modeBadge = data.night_mode ? 'badge-warning' : 'badge-online';
            const modeText = data.night_mode ? 'NIGHT MODE' : 'DAY MODE';

            const statusBadge = data.status === 'operational' ? 'badge-online' :
                               data.status === 'degraded' ? 'badge-warning' : 'badge-offline';
            const statusText = data.status === 'operational' ? 'OPERATIONAL' :
                              data.status === 'degraded' ? 'DEGRADED' : 'ERROR';

            const automationsBadge = data.automations_enabled ? 'badge-online' : 'badge-offline';
            const automationsText = data.automations_enabled ? 'ENABLED' : 'DISABLED';

            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading system status</span></div>' : '';

            return `
                <div class="card">
                    <div class="card-title">⚙️ System</div>
                    ${errorWarning}
                    <div class="status-row">
                        <span class="status-label">Status</span>
                        <span class="badge ${statusBadge}">${statusText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Mode</span>
                        <span class="badge ${modeBadge}">${modeText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Automations</span>
                        <span class="badge ${automationsBadge}">${automationsText}</span>
                    </div>
                    <div class="status-row">
                        <span class="status-label">Flask Uptime</span>
                        <span class="status-value">${data.flask_uptime || 'unknown'}</span>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #21262d;">
                        <div style="display: flex; gap: 5px; margin-bottom: 10px;">
                            <button
                                onclick="toggleAutomations(${data.automations_enabled})"
                                id="automationToggleBtn"
                                style="
                                    flex: 1;
                                    background: ${data.automations_enabled ? '#392f1a' : '#1a472a'};
                                    border: 1px solid ${data.automations_enabled ? '#d29922' : '#3fb950'};
                                    color: ${data.automations_enabled ? '#d29922' : '#3fb950'};
                                    padding: 8px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 12px;
                                    font-weight: 600;
                                "
                                onmouseover="this.style.opacity='0.8'"
                                onmouseout="this.style.opacity='1'"
                            >
                                ${data.automations_enabled ? '⏸️ Disable Automations' : '▶️ Enable Automations'}
                            </button>
                            <button
                                onclick="controlService('restart')"
                                style="
                                    flex: 1;
                                    background: #21262d;
                                    border: 1px solid #30363d;
                                    color: #c9d1d9;
                                    padding: 8px;
                                    border-radius: 6px;
                                    cursor: pointer;
                                    font-size: 12px;
                                    font-weight: 600;
                                "
                                onmouseover="this.style.background='#30363d'"
                                onmouseout="this.style.background='#21262d'"
                            >
                                🔄 Restart Flask
                            </button>
                        </div>
                        <button
                            onclick="shutdownPi()"
                            id="shutdownBtn"
                            style="
                                width: 100%;
                                background: #3d1f1f;
                                border: 1px solid #f85149;
                                color: #f85149;
                                padding: 10px;
                                border-radius: 6px;
                                cursor: pointer;
                                font-size: 14px;
                                font-weight: 600;
                            "
                            onmouseover="this.style.background='#4a2626'"
                            onmouseout="this.style.background='#3d1f1f'"
                        >
                            🔌 Shutdown Pi
                        </button>
                        <div id="serviceStatus" style="margin-top: 10px; text-align: center; font-size: 12px; color: #8b949e;"></div>
                    </div>
                </div>
            `;
        }

        function renderLogsCard(data) {
            const errorWarning = data._error ? '<div class="status-row"><span class="status-error">❌ Error loading logs</span></div>' : '';
            const logContent = data.content || 'No logs available';

            return `
                <div class="card card-wide">
                    <div class="card-title">📜 Recent Activity</div>
                    ${errorWarning}
                    <div class="log-preview">${logContent}</div>
                    <a href="/logs" class="view-logs-link">View Full Logs →</a>
                </div>
            `;
        }

        async function controlService(action) {
            const status = document.getElementById('serviceStatus');
            const actionText = action === 'stop' ? 'Stop' : action === 'restart' ? 'Restart' : 'Start';

            if (!confirm(`${actionText} Flask server?\\n\\n${action === 'stop' ? 'Dashboard will become unavailable.' : action === 'restart' ? 'Dashboard will reload in ~5 seconds.' : 'Flask will start.'}`)) {
                return;
            }

            status.innerHTML = `<span style="color: #d29922;">⏳ ${actionText}ing Flask...</span>`;

            try {
                const response = await fetch('/api/service-control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                const data = await response.json();

                if (response.ok) {
                    status.innerHTML = `<span style="color: #3fb950;">✓ ${actionText} initiated</span>`;

                    if (action === 'restart') {
                        setTimeout(() => {
                            status.innerHTML = '<span style="color: #d29922;">⏳ Waiting for Flask...</span>';
                            setTimeout(() => window.location.reload(), 5000);
                        }, 2000);
                    } else if (action === 'stop') {
                        clearInterval(window.dashboardRefreshInterval);
                        setTimeout(() => {
                            status.innerHTML = '<span style="color: #8b949e;">Flask stopped. Refresh page to reconnect.</span>';
                        }, 2000);
                    }
                } else {
                    status.innerHTML = `<span style="color: #f85149;">❌ ${data.message || 'Failed'}</span>`;
                }
            } catch (error) {
                status.innerHTML = `<span style="color: #f85149;">❌ ${error.message}</span>`;
            }
        }

        async function toggleAutomations(currentlyEnabled) {
            const status = document.getElementById('serviceStatus');
            const action = currentlyEnabled ? 'disable' : 'enable';

            if (!confirm(`${action === 'disable' ? 'Disable' : 'Enable'} all automations?\\n\\n${action === 'disable' ? 'Home automations will stop running but dashboard stays active.' : 'Home automations will resume normal operation.'}`)) {
                return;
            }

            status.innerHTML = `<span style="color: #d29922;">⏳ ${action === 'disable' ? 'Disabling' : 'Enabling'} automations...</span>`;

            try {
                const response = await fetch('/api/automation-control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enable: !currentlyEnabled })
                });
                const data = await response.json();

                if (response.ok) {
                    status.innerHTML = `<span style="color: #3fb950;">✓ Automations ${action === 'disable' ? 'disabled' : 'enabled'}</span>`;
                    // Reload dashboard to show new status
                    setTimeout(() => loadDashboard(), 1000);
                } else {
                    status.innerHTML = `<span style="color: #f85149;">❌ ${data.message || 'Failed'}</span>`;
                }
            } catch (error) {
                status.innerHTML = `<span style="color: #f85149;">❌ ${error.message}</span>`;
            }
        }

        async function shutdownPi() {
            const btn = document.getElementById('shutdownBtn');
            const status = document.getElementById('serviceStatus');

            if (!confirm('Shutdown the Raspberry Pi?\\n\\nThe system will power down. Wait for the LED to stop blinking before unplugging power.')) {
                return;
            }

            btn.disabled = true;
            btn.textContent = '⏳ Shutting down...';
            btn.style.cursor = 'not-allowed';
            btn.style.opacity = '0.6';

            try {
                const response = await fetch('/api/shutdown', { method: 'POST' });
                const data = await response.json();

                if (response.ok) {
                    status.innerHTML = '<span style="color: #d29922;">⚠️ System shutting down<br>Wait for LED to stop blinking<br>Then safe to unplug power</span>';

                    // Stop auto-refresh
                    clearInterval(window.dashboardRefreshInterval);

                    // Show countdown
                    let seconds = 60;
                    const countdown = setInterval(() => {
                        status.innerHTML = `<span style="color: #d29922;">⚠️ Shutdown in progress (${seconds}s)<br>LED will stop blinking soon<br>Then safe to unplug</span>`;
                        seconds--;
                        if (seconds < 0) {
                            clearInterval(countdown);
                            status.innerHTML = '<span style="color: #3fb950;">✓ System halted<br>LED should be OFF<br>Safe to unplug power now</span>';
                        }
                    }, 1000);
                } else {
                    status.innerHTML = `<span style="color: #f85149;">❌ ${data.message || 'Shutdown failed'}</span>`;
                    btn.disabled = false;
                    btn.textContent = '🔌 Shutdown Pi';
                    btn.style.cursor = 'pointer';
                    btn.style.opacity = '1';
                }
            } catch (error) {
                status.innerHTML = `<span style="color: #f85149;">❌ ${error.message}</span>`;
                btn.disabled = false;
                btn.textContent = '🔌 Shutdown Pi';
                btn.style.cursor = 'pointer';
                btn.style.opacity = '1';
            }
        }

        // Load dashboard on page load
        loadDashboard();

        // Auto-refresh every 5 seconds
        window.dashboardRefreshInterval = setInterval(loadDashboard, 5000);
    </script>
</body>
</html>
        """
        return Response(html, mimetype='text/html')

    @app.route('/pre-arrival', methods=['POST'])
    @require_auth
    def pre_arrival():
        """Trigger pre-arrival automation (Stage 1: HVAC + outdoor lights)"""
        logger.info("Received /pre-arrival request")
        result, status_code = run_automation_script('pre_arrival.py')
        return jsonify(result), status_code

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
            <div class="log-controls" style="margin-top: 10px;">
                <select class="btn" id="logLevelFilter" onchange="applyFilters()" style="min-width: 120px;">
                    <option value="">All Levels</option>
                    <option value="ERROR">ERROR</option>
                    <option value="WARNING">WARNING</option>
                    <option value="NOTICE">NOTICE</option>
                    <option value="INFO">INFO</option>
                    <option value="DEBUG">DEBUG</option>
                </select>
                <input type="text" class="btn" id="automationFilter" placeholder="Filter by automation..."
                       style="flex: 1; min-width: 150px;" oninput="applyFilters()">
                <input type="text" class="btn" id="keywordFilter" placeholder="Search keyword..."
                       style="flex: 1; min-width: 150px;" oninput="applyFilters()">
                <button class="btn" onclick="clearFilters()">✕ Clear</button>
            </div>
            <pre id="logContent">Select a log file to view</pre>
        </div>
    </div>

    <script>
        let currentLog = null;
        let currentLines = 50;
        let autoRefreshInterval = null;
        let rawLogContent = '';

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

            // Clear previous content and force reload
            rawLogContent = '';
            await loadLogContent();
        }

        async function loadLogContent() {
            if (!currentLog) return;

            const contentEl = document.getElementById('logContent');

            try {
                const response = await fetch(
                    `/logs/${currentLog}?lines=${currentLines}&format=text`
                );
                const text = await response.text();
                const newContent = text || '(empty log)';

                // Only update if content has changed
                if (newContent !== rawLogContent) {
                    rawLogContent = newContent;
                    applyFilters();
                }
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

        function applyFilters() {
            const contentEl = document.getElementById('logContent');
            const logLevelFilter = document.getElementById('logLevelFilter').value;
            const automationFilter = document.getElementById('automationFilter').value.toLowerCase();
            const keywordFilter = document.getElementById('keywordFilter').value.toLowerCase();

            // Split into lines
            let lines = rawLogContent.split('\\n');

            // Apply log level filter
            if (logLevelFilter) {
                const levelRegex = new RegExp(`level=${logLevelFilter}\\b`, 'i');
                lines = lines.filter(line => levelRegex.test(line));
            }

            // Apply automation filter
            if (automationFilter) {
                const autoRegex = new RegExp(`automation=[^\\s]*${automationFilter}`, 'i');
                lines = lines.filter(line => autoRegex.test(line));
            }

            // Apply keyword filter
            if (keywordFilter) {
                lines = lines.filter(line => line.toLowerCase().includes(keywordFilter));
            }

            // Update display
            const filteredContent = lines.join('\\n');
            contentEl.textContent = filteredContent || '(no matching logs)';
        }

        function clearFilters() {
            document.getElementById('logLevelFilter').value = '';
            document.getElementById('automationFilter').value = '';
            document.getElementById('keywordFilter').value = '';
            applyFilters();
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

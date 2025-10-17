"""
Flask blueprint for administrative API endpoints

Provides system administration endpoints:
- Raspberry Pi shutdown
- Git pull (code updates)
- Service control (restart Flask)
"""

import os
import subprocess
import logging
from flask import Blueprint, request, jsonify
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# Create blueprint
api_admin_bp = Blueprint('api_admin', __name__)


@api_admin_bp.route('/api/shutdown', methods=['POST'])
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


@api_admin_bp.route('/api/git-pull', methods=['POST'])
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
        repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

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


@api_admin_bp.route('/api/service-control', methods=['POST'])
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

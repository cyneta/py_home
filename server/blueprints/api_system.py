"""
Flask blueprint for system status API endpoints

Provides endpoints for system health, uptime, and monitoring:
- Night mode / sleep time status
- Presence status
- System status (uptime, health)
- Automation control (enable/disable master switch)
"""

import os
import time
import logging
from flask import Blueprint, request, jsonify
from server import config
from lib.logging_config import kvlog

logger = logging.getLogger(__name__)

# Create blueprint
api_system_bp = Blueprint('api_system', __name__)


@api_system_bp.route('/api/night-mode')
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


@api_system_bp.route('/api/presence')
def api_presence():
    """Get current presence status from .presence_state file"""
    try:
        state_file = os.path.join(os.path.dirname(__file__), '..', '..', '.presence_state')

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


@api_system_bp.route('/api/system-status')
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

        # Check dry-run mode
        from lib.config import get
        dry_run = get('automations.dry_run', False)

        return jsonify({
            'status': health_status,
            'flask_uptime': uptime,
            'flask_uptime_seconds': int(uptime_seconds),
            'night_mode': night_mode,
            'dry_run': dry_run,
            'services': services,
            'platform': platform.system()
        }), 200

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return jsonify({'error': str(e)}), 500


@api_system_bp.route('/api/automation-control', methods=['GET', 'POST'])
def api_automation_control():
    """Get/set dry-run mode for automations"""
    from lib.config import get

    if request.method == 'GET':
        # Get current dry-run status
        dry_run = get('automations.dry_run', False)
        return jsonify({
            'dry_run': dry_run,
            'status': 'dry_run' if dry_run else 'active',
            'message': 'Automations log actions but do not execute' if dry_run else 'Automations actively controlling devices'
        }), 200

    elif request.method == 'POST':
        # Cannot set dry-run via API - must edit config.yaml
        # This is intentional to prevent accidental production changes
        return jsonify({
            'error': 'Cannot change dry-run mode via API',
            'message': 'Edit config/config.yaml and set automations.dry_run, then restart service',
            'current_dry_run': get('automations.dry_run', False)
        }), 403

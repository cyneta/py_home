"""
Flask blueprint for iOS Shortcuts webhook endpoints

Provides webhook endpoints that trigger home automation scripts:
- Pre-arrival
- Leaving home
- Goodnight
- I'm home
- Good morning
- Travel time
- Add task
"""

import os
import sys
import subprocess
import logging
import json
from flask import Blueprint, request, jsonify
from server import config
from server.helpers import require_auth, run_automation_script

logger = logging.getLogger(__name__)

# Create blueprint
webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/pre-arrival', methods=['POST'])
@require_auth
def pre_arrival():
    """Trigger pre-arrival automation (Stage 1: HVAC + outdoor lights)"""
    logger.info("Received /pre-arrival request")
    result, status_code = run_automation_script('pre_arrival.py')
    return jsonify(result), status_code


@webhooks_bp.route('/leaving-home', methods=['POST'])
@require_auth
def leaving_home():
    """Trigger leaving home automation"""
    logger.info("Received /leaving-home request")
    result, status_code = run_automation_script('leaving_home.py')
    return jsonify(result), status_code


@webhooks_bp.route('/goodnight', methods=['POST'])
@require_auth
def goodnight():
    """Trigger goodnight automation"""
    logger.info("Received /goodnight request")
    result, status_code = run_automation_script('goodnight.py')
    return jsonify(result), status_code


@webhooks_bp.route('/im-home', methods=['POST'])
@require_auth
def im_home():
    """Trigger I'm home automation"""
    logger.info("Received /im-home request")
    result, status_code = run_automation_script('im_home.py')
    return jsonify(result), status_code


@webhooks_bp.route('/good-morning', methods=['POST'])
@require_auth
def good_morning():
    """Trigger good morning automation"""
    logger.info("Received /good-morning request")
    result, status_code = run_automation_script('good_morning.py')
    return jsonify(result), status_code


@webhooks_bp.route('/travel-time', methods=['GET', 'POST'])
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


@webhooks_bp.route('/add-task', methods=['POST'])
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

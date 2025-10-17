"""
Flask blueprint for AI command processing endpoint

Provides natural language command processing via OpenAI
"""

import logging
import traceback
from flask import Blueprint, request, jsonify
from server.helpers import require_auth

logger = logging.getLogger(__name__)

# Create blueprint
ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai-command', methods=['POST'])
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
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Failed to process command: {str(e)}'
        }), 500

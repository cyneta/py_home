"""
Flask blueprint for log viewing endpoints

Provides web UI and API endpoints for browsing application logs
"""

import os
import logging
from flask import Blueprint, request, jsonify, render_template

logger = logging.getLogger(__name__)

# Create blueprint
logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs')
def logs_ui():
    """
    Web UI for browsing logs (HTML) or API endpoint (JSON)

    Returns HTML if accessed from browser, JSON if Accept header is application/json
    """
    # Check if client wants JSON (API client) or HTML (browser)
    if request.accept_mimetypes.best == 'application/json' or request.args.get('format') == 'json':
        return list_logs()

    # Serve HTML UI
    return render_template('logs.html')


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


@logs_bp.route('/logs/<filename>', methods=['GET'])
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

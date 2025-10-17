"""
Flask blueprint for device status API endpoints

Provides JSON APIs for querying status of smart home devices:
- Nest thermostat
- Sensibo AC
- Tapo smart outlets
- TempStick temperature sensors
"""

import logging
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
api_device_bp = Blueprint('api_device', __name__)


@api_device_bp.route('/api/nest/status')
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


@api_device_bp.route('/api/sensibo/status')
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


@api_device_bp.route('/api/tapo/status')
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


@api_device_bp.route('/api/tempstick/status')
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

"""
Flask blueprint for location/geofencing endpoints

Provides endpoints for iOS Shortcuts geofencing integration:
- Update user location
- Get current location and ETA
"""

import logging
import traceback
from flask import Blueprint, request, jsonify
from server.helpers import require_auth, run_automation_script

logger = logging.getLogger(__name__)

# Create blueprint
location_bp = Blueprint('location', __name__)


@location_bp.route('/update-location', methods=['POST'])
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
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Failed to update location: {str(e)}'
        }), 500


@location_bp.route('/location', methods=['GET'])
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

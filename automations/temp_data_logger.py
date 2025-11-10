#!/usr/bin/env python3
"""
Temperature Data Logger

Collects comprehensive temperature, HVAC, and environmental data
from all sensors and logs to CSV for analysis.

Usage:
    python automations/temp_data_logger.py [--dry-run]

Schedule:
    */15 * * * * cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py
"""

import sys
import os
import csv
import argparse
from datetime import datetime
import logging
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.config import get, PROJECT_ROOT
from lib.logging_config import setup_logging, kvlog

logger = logging.getLogger(__name__)

# CSV columns
CSV_COLUMNS = [
    'timestamp',
    'outdoor_f', 'outdoor_condition', 'wind_mph', 'cloud_pct', 'sunrise', 'sunset',
    'living_tempstick_f', 'living_tempstick_humidity',
    'living_nest_f', 'living_nest_target_f', 'living_nest_mode',
    'living_alen_pm25', 'living_alen_aqi',
    'bedroom_sensibo_f', 'bedroom_sensibo_target_f', 'bedroom_sensibo_humidity',
    'bedroom_sensibo_on', 'bedroom_sensibo_mode',
    'bedroom_alen_pm25', 'bedroom_alen_aqi',
    'heater_on',
    'presence', 'transition_state'
]


def collect_outdoor_weather():
    """Collect outdoor weather data from OpenWeather API"""
    from services.openweather import get_current_weather

    weather = get_current_weather()

    # Convert sunrise/sunset to time strings
    sunrise_dt = datetime.fromtimestamp(weather.get('sunrise', 0))
    sunset_dt = datetime.fromtimestamp(weather.get('sunset', 0))

    return {
        'outdoor_f': weather.get('temp', 'N/A'),
        'outdoor_condition': weather.get('conditions', 'N/A'),
        'wind_mph': weather.get('wind_speed', 'N/A'),
        'cloud_pct': weather.get('clouds', 'N/A'),
        'sunrise': sunrise_dt.strftime('%H:%M:%S') if weather.get('sunrise') else 'N/A',
        'sunset': sunset_dt.strftime('%H:%M:%S') if weather.get('sunset') else 'N/A',
    }


def collect_tempstick():
    """Collect TempStick sensor data (Living Room)"""
    from services.tempstick import get_sensor_data

    data = get_sensor_data()

    return {
        'living_tempstick_f': data.get('temp_f', 'N/A'),
        'living_tempstick_humidity': data.get('humidity', 'N/A'),
    }


def collect_nest():
    """Collect Nest thermostat data (Living Room)"""
    from components.nest.client import get_status

    status = get_status()

    # Extract current temperature if available
    current_temp = status.get('current_temperature_f', 'N/A')

    # Get target temperature (may be in different fields depending on mode)
    target_temp = 'N/A'
    if 'target_temperature_f' in status:
        target_temp = status['target_temperature_f']
    elif 'heat_setpoint_f' in status:
        target_temp = status['heat_setpoint_f']
    elif 'cool_setpoint_f' in status:
        target_temp = status['cool_setpoint_f']

    # Get mode
    mode = status.get('mode', 'N/A')

    return {
        'living_nest_f': current_temp,
        'living_nest_target_f': target_temp,
        'living_nest_mode': mode,
    }


def collect_sensibo():
    """Collect Sensibo mini-split data (Bedroom)"""
    from components.sensibo.client import get_status

    bedroom_id = get('sensibo.bedroom_ac_id')
    status = get_status(bedroom_id)

    return {
        'bedroom_sensibo_f': status.get('current_temp_f', 'N/A'),
        'bedroom_sensibo_target_f': status.get('target_temp_f', 'N/A'),
        'bedroom_sensibo_humidity': status.get('current_humidity', 'N/A'),
        'bedroom_sensibo_on': 1 if status.get('on') else 0,
        'bedroom_sensibo_mode': status.get('mode', 'N/A'),
    }


def collect_alen_living():
    """Collect Alen air purifier data (Living Room)"""
    try:
        from components.tuya.client import get_tuya_client

        # Check if living room device is configured
        device_id = get('alen.devices.living_room.device_id')
        if not device_id or device_id.startswith('${'):
            return None

        client = get_tuya_client()
        status = client.get_device_status(device_id)

        return {
            'living_alen_pm25': status.get('pm25', 'N/A'),
            'living_alen_aqi': status.get('aqi', 'N/A'),
        }
    except ImportError:
        # Tuya component not available
        return None


def collect_alen_bedroom():
    """Collect Alen air purifier data (Bedroom)"""
    try:
        from components.tuya.client import get_tuya_client

        # Check if bedroom device is configured
        device_id = get('alen.devices.bedroom.device_id')
        if not device_id or device_id.startswith('${'):
            return None

        client = get_tuya_client()
        status = client.get_device_status(device_id)

        return {
            'bedroom_alen_pm25': status.get('pm25', 'N/A'),
            'bedroom_alen_aqi': status.get('aqi', 'N/A'),
        }
    except ImportError:
        # Tuya component not available
        return None


def collect_tapo_heater():
    """Collect Tapo heater outlet state"""
    from components.tapo.client import get_status

    # Get status for Master Heater outlet
    status = get_status('Master Heater')

    return {
        'heater_on': 1 if status.get('device_on') else 0,
    }


def collect_system_state():
    """Determine current system state"""
    from lib.transitions import is_sleep_time
    from datetime import datetime

    # Get presence from state file
    state_file = os.path.join(PROJECT_ROOT, '.presence_state')
    presence = 'unknown'
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                presence = f.read().strip()
        except:
            pass

    # Determine transition state based on time
    # wake: 05:00-09:00, day: 09:00-22:30, sleep: 22:30-05:00
    now = datetime.now().time()
    wake_time = datetime.strptime(get('schedule.wake_time', '05:00'), '%H:%M').time()
    sleep_time = datetime.strptime(get('schedule.sleep_time', '22:30'), '%H:%M').time()

    # Create wake transition window (wake_time to wake_time + 4 hours)
    wake_end = datetime.strptime(get('schedule.wake_time', '05:00'), '%H:%M')
    wake_end = wake_end.replace(hour=(wake_end.hour + 4) % 24).time()

    if presence == 'away':
        transition_state = 'away'
    elif is_sleep_time():
        transition_state = 'sleep'
    elif wake_time <= now < wake_end:
        transition_state = 'wake'
    else:
        transition_state = 'day'

    return {
        'presence': presence,
        'transition_state': transition_state,
    }


def write_csv_row(csv_path, data, dry_run=False):
    """
    Write data row to CSV file (append mode)

    Args:
        csv_path: Path to CSV file
        data: Dict with all CSV columns
        dry_run: If True, don't actually write
    """
    # Check if file exists
    file_exists = os.path.exists(csv_path)

    if dry_run:
        kvlog(logger, logging.INFO, automation='temp_data_logger',
              event='dry_run_write', csv_path=csv_path, fields=len([v for v in data.values() if v != 'N/A']))
        return

    # Create directory if needed
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Write to CSV (append mode)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)

        # Write header if new file
        if not file_exists:
            writer.writeheader()

        # Write data row
        writer.writerow(data)


def main():
    parser = argparse.ArgumentParser(description='Temperature Data Logger')
    parser.add_argument('--dry-run', action='store_true',
                        help='Test mode - no actual data written')
    args = parser.parse_args()

    # Setup logging
    setup_logging(get('logging.level', 'INFO'))

    start_time = time.time()

    kvlog(logger, logging.NOTICE, automation='temp_data_logger',
          event='start', dry_run=args.dry_run)

    # Check if enabled
    if not get('data_collection.temperature_logging.enabled', True):
        logger.info("Temperature logging disabled in config")
        return 0

    # Get config
    csv_path = os.path.join(PROJECT_ROOT, get('data_collection.temperature_logging.file',
                                               'data/logs/temp_analysis.csv'))
    continue_on_error = get('data_collection.temperature_logging.continue_on_error', True)

    # Initialize data dict with timestamp
    data = {col: 'N/A' for col in CSV_COLUMNS}
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Collect from each source
    collectors = [
        ('outdoor_weather', collect_outdoor_weather),
        ('tempstick', collect_tempstick),
        ('nest', collect_nest),
        ('sensibo', collect_sensibo),
        ('alen_living', collect_alen_living),
        ('alen_bedroom', collect_alen_bedroom),
        ('tapo_heater', collect_tapo_heater),
        ('system_state', collect_system_state),
    ]

    errors = []
    success_count = 0

    for source_name, collector_func in collectors:
        # Check if source enabled
        source_enabled = get(f'data_collection.temperature_logging.sources.{source_name}', True)

        if not source_enabled:
            kvlog(logger, logging.DEBUG, automation='temp_data_logger',
                  source=source_name, result='disabled')
            continue

        try:
            source_data = collector_func()
            if source_data:
                data.update(source_data)
                success_count += 1
                kvlog(logger, logging.DEBUG, automation='temp_data_logger',
                      source=source_name, result='ok', fields=len(source_data))
        except Exception as e:
            error_msg = f"{source_name}: {type(e).__name__}"
            errors.append(error_msg)
            kvlog(logger, logging.WARNING, automation='temp_data_logger',
                  source=source_name, error_type=type(e).__name__, error_msg=str(e))

            if not continue_on_error:
                raise

    # Write to CSV
    try:
        write_csv_row(csv_path, data, dry_run=args.dry_run)

        duration_ms = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.NOTICE, automation='temp_data_logger',
              event='complete', sources_ok=success_count, errors_count=len(errors),
              duration_ms=duration_ms, csv_path=csv_path if not args.dry_run else 'N/A')
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='temp_data_logger',
              event='write_error', error_type=type(e).__name__, error_msg=str(e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

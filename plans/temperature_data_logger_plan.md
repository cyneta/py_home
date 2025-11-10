# Temperature Data Logger - Implementation Plan

**Version:** 1.0
**Date:** 2025-11-08
**Estimated Time:** 2-3 hours
**Status:** Ready to implement

## Overview

Implementation plan for the temperature and environmental data logger system. See `specs/temperature_data_logger.md` for complete specification.

## Prerequisites

### Already Available
- ✅ OpenWeather API (configured)
- ✅ TempStick API (configured)
- ✅ Nest API (configured)
- ✅ Sensibo API (configured)
- ✅ Tapo API (configured)

### Future Dependencies
- ❌ Alen air purifier configuration (optional - skip if not configured)

## Implementation Steps

### Step 1: Update Configuration (10 min)

**File:** `config/config.yaml`

**Add section:**
```yaml
# Data Collection for Analysis
data_collection:
  temperature_logging:
    enabled: true
    interval_minutes: 15
    file: "data/logs/temp_analysis.csv"
    continue_on_error: true
    sources:
      outdoor_weather: true
      tempstick: true
      nest: true
      sensibo: true
      alen_living: true  # Will skip if not configured
      alen_bedroom: true  # Will skip if not configured
      tapo_heater: true
      system_state: true
```

**File:** `config/config.local.yaml`

Keep same defaults (no overrides needed).

---

### Step 2: Create Data Logger Script (60 min)

**File:** `automations/temp_data_logger.py`

**Structure:**
```python
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
    # Implementation: Call OpenWeather API
    # Return dict with: outdoor_f, outdoor_condition, wind_mph, cloud_pct, sunrise, sunset
    pass


def collect_tempstick():
    """Collect TempStick sensor data (Living Room)"""
    # Implementation: Call TempStick API
    # Return dict with: living_tempstick_f, living_tempstick_humidity
    pass


def collect_nest():
    """Collect Nest thermostat data (Living Room)"""
    # Implementation: Call Nest API
    # Return dict with: living_nest_f, living_nest_target_f, living_nest_mode
    pass


def collect_sensibo():
    """Collect Sensibo mini-split data (Bedroom)"""
    # Implementation: Call Sensibo API
    # Return dict with: bedroom_sensibo_f, bedroom_sensibo_target_f,
    #                   bedroom_sensibo_humidity, bedroom_sensibo_on, bedroom_sensibo_mode
    pass


def collect_alen_living():
    """Collect Alen air purifier data (Living Room)"""
    # Implementation: Call Tuya API for living room purifier
    # Return dict with: living_alen_pm25, living_alen_aqi
    # Return None if not configured
    pass


def collect_alen_bedroom():
    """Collect Alen air purifier data (Bedroom)"""
    # Implementation: Call Tuya API for bedroom purifier
    # Return dict with: bedroom_alen_pm25, bedroom_alen_aqi
    # Return None if not configured
    pass


def collect_tapo_heater():
    """Collect Tapo heater outlet state"""
    # Implementation: Call Tapo API for Master Heater
    # Return dict with: heater_on (1/0)
    pass


def collect_system_state():
    """Determine current system state"""
    # Implementation: Check if home/away, wake/sleep/day
    # Return dict with: presence, transition_state
    pass


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
        logger.info(f"[DRY-RUN] Would write to {csv_path}: {data}")
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

    for source_name, collector_func in collectors:
        # Check if source enabled
        source_enabled = get(f'data_collection.temperature_logging.sources.{source_name}', True)

        if not source_enabled:
            logger.debug(f"Source disabled: {source_name}")
            continue

        try:
            source_data = collector_func()
            if source_data:
                data.update(source_data)
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
        kvlog(logger, logging.NOTICE, automation='temp_data_logger',
              event='complete', errors_count=len(errors), csv_path=csv_path)
    except Exception as e:
        kvlog(logger, logging.ERROR, automation='temp_data_logger',
              event='write_error', error_type=type(e).__name__, error_msg=str(e))
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

**Testing:**
```bash
# Test locally
python automations/temp_data_logger.py --dry-run

# Test on Pi
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py --dry-run"
```

---

### Step 3: Implement Collector Functions (45 min)

Each collector function should:
1. Try to collect data from API/service
2. Return dict with relevant fields
3. Return None or empty dict if source unavailable
4. Let exceptions bubble up (caught by main loop)

**Example: `collect_outdoor_weather()`**
```python
def collect_outdoor_weather():
    """Collect outdoor weather data from OpenWeather API"""
    from services.openweather import get_current_weather
    from datetime import datetime

    weather = get_current_weather()

    # Convert sunrise/sunset to time strings
    sunrise_dt = datetime.fromtimestamp(weather.get('sunrise', 0))
    sunset_dt = datetime.fromtimestamp(weather.get('sunset', 0))

    return {
        'outdoor_f': weather.get('temp', 'N/A'),
        'outdoor_condition': weather.get('conditions', 'N/A'),
        'wind_mph': weather.get('wind_speed', 'N/A'),
        'cloud_pct': weather.get('clouds', 'N/A'),
        'sunrise': sunrise_dt.strftime('%H:%M:%S'),
        'sunset': sunset_dt.strftime('%H:%M:%S'),
    }
```

Repeat for all 8 collector functions.

---

### Step 4: Add Cron Job (5 min)

**File:** `/etc/cron.d/py_home` (on Pi)

**Add line:**
```bash
# Temperature data logger - every 15 minutes
*/15 * * * * matt.wheeler cd /home/matt.wheeler/py_home && /usr/bin/python3 automations/temp_data_logger.py >> data/logs/temp_data_logger.log 2>&1
```

**Deploy:**
```bash
# SSH to Pi
ssh matt.wheeler@100.107.121.6

# Edit cron
sudo nano /etc/cron.d/py_home

# Add the line above

# Restart cron
sudo systemctl restart cron

# Verify cron installed
cat /etc/cron.d/py_home
```

---

### Step 5: Test & Verify (30 min)

**5.1 Local Testing:**
```bash
# Dry run
python automations/temp_data_logger.py --dry-run

# Real run (creates CSV)
python automations/temp_data_logger.py

# Check CSV created
cat data/logs/temp_analysis.csv
```

**5.2 Deploy to Pi:**
```bash
# Commit and push
git add .
git commit -m "Add temperature data logger"
git push

# Pull on Pi
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && git pull"

# Test on Pi
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py --dry-run"

# Real run
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py"

# Check CSV
ssh matt.wheeler@100.107.121.6 "cat /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"
```

**5.3 Wait for Cron:**
- Wait 15 minutes for first cron execution
- Check log: `ssh matt.wheeler@100.107.121.6 "tail -20 /home/matt.wheeler/py_home/data/logs/temp_data_logger.log"`
- Check CSV grew: `ssh matt.wheeler@100.107.121.6 "wc -l /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"`

**5.4 Validate Data:**
```bash
# Check for N/A values (should be minimal)
ssh matt.wheeler@100.107.121.6 "grep 'N/A' /home/matt.wheeler/py_home/data/logs/temp_analysis.csv | wc -l"

# Check CSV can be loaded
python -c "import pandas as pd; df = pd.read_csv('data/logs/temp_analysis.csv'); print(df.head())"
```

---

### Step 6: Monitor for 24 Hours (passive)

**Check after 24 hours:**
- CSV file should have ~96 rows (one per 15 min)
- File size should be ~14 KB
- Log file should show successful executions
- N/A values should be <5% per column

**If issues:**
- Check temp_data_logger.log for errors
- Check individual API services
- Verify cron is running: `systemctl status cron`

---

## Rollback Plan

If issues occur:

**1. Disable cron job:**
```bash
sudo nano /etc/cron.d/py_home
# Comment out the temp data logger line
sudo systemctl restart cron
```

**2. Keep CSV data:**
- Data already logged is safe
- Can re-run script manually to fill gaps

**3. Fix and redeploy:**
- Fix issues in temp_data_logger.py
- Test locally
- Deploy to Pi
- Re-enable cron

---

## Success Criteria

- ✅ CSV file created with header row
- ✅ Data logged every 15 minutes
- ✅ All configured sensors appear in CSV
- ✅ N/A values <5% per sensor
- ✅ File grows by ~14 KB/day
- ✅ No errors in temp_data_logger.log
- ✅ No impact on other py_home functions
- ✅ CSV can be loaded into Excel/pandas

---

## Timeline

| Task | Estimated Time | Total Time |
|------|----------------|------------|
| Update configuration | 10 min | 10 min |
| Create script structure | 20 min | 30 min |
| Implement collectors | 45 min | 75 min |
| Add cron job | 5 min | 80 min |
| Test locally | 15 min | 95 min |
| Deploy to Pi | 10 min | 105 min |
| Verify cron execution | 5 min | 110 min |

**Total:** ~2 hours active work + 24 hours passive monitoring

---

## Dependencies

### Python Packages (already installed)
- csv (stdlib)
- datetime (stdlib)
- logging (stdlib)

### py_home Components (already implemented)
- services/openweather.py
- services/tempstick.py
- components/nest/
- components/sensibo/
- components/tapo/
- components/tuya/ (for Alen, when configured)

### System Requirements
- Cron (already configured)
- ~10 MB disk space (plenty available)

---

## Post-Implementation

### Week 1: Monitor
- Check logs daily for errors
- Verify data quality
- Adjust interval if needed (15 min → 30 min to reduce API calls)

### Month 1: First Analysis
- Load CSV into Excel/pandas
- Create basic charts (outdoor vs indoor temp over time)
- Validate data makes sense
- Identify any sensor calibration issues

### Month 3: Optimization
- Analyze HVAC efficiency
- Determine optimal temperature boost logic
- Tune comfort setpoints based on real data

---

## Future Enhancements (Not in This Plan)

- Real-time dashboard (Grafana/InfluxDB)
- Automated weekly reports
- Machine learning for predictive setpoints
- API endpoint for data export
- Alert on unusual patterns

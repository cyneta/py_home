# Temperature Data Logger - Development Plan

**Version:** 1.0
**Date:** 2025-11-08
**Estimated Time:** 2-3 hours
**Status:** Ready to implement

## Prerequisites

- ✅ All required APIs configured (OpenWeather, TempStick, Nest, Sensibo, Tapo)
- ✅ Python 3.x on Raspberry Pi
- ✅ Existing py_home infrastructure (logging, config, services)

## Development Workflow

### Phase 1: Configuration (10 min)

#### Task 1.1: Add data collection config to config.yaml

**File:** `config/config.yaml`

**Add after line 145 (after tempstick section):**

```yaml
# Data Collection for Analysis
data_collection:
  temperature_logging:
    enabled: true
    interval_minutes: 15
    file: "data/logs/temp_analysis.csv"
    continue_on_error: true  # Continue logging even if some sensors fail

    # Individual source toggles
    sources:
      outdoor_weather: true
      tempstick: true
      nest: true
      sensibo: true
      alen_living: true      # Skip if not configured
      alen_bedroom: true     # Skip if not configured
      tapo_heater: true
      system_state: true
```

**Testing:**
```bash
# Verify config loads
python -c "from lib.config import get; print(get('data_collection.temperature_logging.enabled'))"
# Expected: True
```

---

### Phase 2: Create Script Structure (20 min)

#### Task 2.1: Create automations/temp_data_logger.py

**File:** `automations/temp_data_logger.py`

**Complete script structure (copy this):**

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
from lib.transitions import is_sleep_time

logger = logging.getLogger(__name__)

# CSV column order (must match exactly)
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
    # TODO: Implement in Phase 3
    return {}


def collect_tempstick():
    """Collect TempStick sensor data (Living Room)"""
    # TODO: Implement in Phase 3
    return {}


def collect_nest():
    """Collect Nest thermostat data (Living Room)"""
    # TODO: Implement in Phase 3
    return {}


def collect_sensibo():
    """Collect Sensibo mini-split data (Bedroom)"""
    # TODO: Implement in Phase 3
    return {}


def collect_alen_living():
    """Collect Alen air purifier data (Living Room)"""
    # TODO: Implement in Phase 3
    return {}


def collect_alen_bedroom():
    """Collect Alen air purifier data (Bedroom)"""
    # TODO: Implement in Phase 3
    return {}


def collect_tapo_heater():
    """Collect Tapo heater outlet state"""
    # TODO: Implement in Phase 3
    return {}


def collect_system_state():
    """Determine current system state (presence, transition)"""
    # TODO: Implement in Phase 3
    return {}


def write_csv_row(csv_path, data, dry_run=False):
    """
    Write data row to CSV file (append mode)

    Args:
        csv_path: Path to CSV file
        data: Dict with all CSV columns
        dry_run: If True, don't actually write
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Would write to {csv_path}")
        logger.info(f"[DRY-RUN] Data: {data}")
        return

    # Check if file exists
    file_exists = os.path.exists(csv_path)

    # Create directory if needed
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Write to CSV (append mode)
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)

        # Write header if new file
        if not file_exists:
            writer.writeheader()
            logger.info(f"Created new CSV with header: {csv_path}")

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

    # Initialize data dict with timestamp and N/A defaults
    data = {col: 'N/A' for col in CSV_COLUMNS}
    data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Define collectors
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

    # Collect from each source
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
                      source=source_name, result='ok', fields_count=len(source_data))
        except Exception as e:
            error_msg = f"{source_name}: {type(e).__name__}"
            errors.append(error_msg)
            kvlog(logger, logging.WARNING, automation='temp_data_logger',
                  source=source_name, error_type=type(e).__name__,
                  error_msg=str(e)[:100])

            if not continue_on_error:
                raise

    # Write to CSV
    try:
        write_csv_row(csv_path, data, dry_run=args.dry_run)
        kvlog(logger, logging.NOTICE, automation='temp_data_logger',
              event='complete', errors_count=len(errors), csv_path=csv_path)

        if errors:
            logger.warning(f"Completed with {len(errors)} errors: {', '.join(errors)}")

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
# Syntax check
python automations/temp_data_logger.py --dry-run

# Expected output:
# - Script runs without errors
# - Logs show all sources returning empty dicts
# - No CSV created (dry-run mode)
```

---

### Phase 3: Implement Collectors (60 min)

#### Task 3.1: collect_outdoor_weather() (10 min)

**Replace TODO with:**

```python
def collect_outdoor_weather():
    """Collect outdoor weather data from OpenWeather API"""
    from services.openweather import get_current_weather
    from datetime import datetime

    try:
        weather = get_current_weather()

        # Convert sunrise/sunset timestamps to time strings
        sunrise_dt = datetime.fromtimestamp(weather.get('sunrise', 0))
        sunset_dt = datetime.fromtimestamp(weather.get('sunset', 0))

        return {
            'outdoor_f': round(weather.get('temp', 0), 1),
            'outdoor_condition': weather.get('conditions', 'N/A'),
            'wind_mph': round(weather.get('wind_speed', 0), 1),
            'cloud_pct': weather.get('clouds', 0),
            'sunrise': sunrise_dt.strftime('%H:%M:%S'),
            'sunset': sunset_dt.strftime('%H:%M:%S'),
        }
    except Exception as e:
        logger.warning(f"Failed to collect outdoor weather: {e}")
        raise
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_outdoor_weather
print(collect_outdoor_weather())
"
```

---

#### Task 3.2: collect_tempstick() (5 min)

**Replace TODO with:**

```python
def collect_tempstick():
    """Collect TempStick sensor data (Living Room)"""
    from services.tempstick import get_sensor_data

    try:
        data = get_sensor_data()

        return {
            'living_tempstick_f': round(data['temperature_f'], 1),
            'living_tempstick_humidity': round(data['humidity'], 1),
        }
    except Exception as e:
        logger.warning(f"Failed to collect TempStick data: {e}")
        raise
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_tempstick
print(collect_tempstick())
"
```

---

#### Task 3.3: collect_nest() (10 min)

**Replace TODO with:**

```python
def collect_nest():
    """Collect Nest thermostat data (Living Room)"""
    from components.nest import NestAPI

    try:
        nest = NestAPI()
        status = nest.get_status()

        # Note: Nest API may not provide current temp, only target
        # If current_temp available, use it; otherwise N/A
        current_temp = status.get('current_temp_f', 'N/A')
        if current_temp != 'N/A':
            current_temp = round(current_temp, 1)

        return {
            'living_nest_f': current_temp,
            'living_nest_target_f': round(status.get('target_temp_f', 0), 1),
            'living_nest_mode': status.get('hvac_mode', 'N/A'),
        }
    except Exception as e:
        logger.warning(f"Failed to collect Nest data: {e}")
        raise
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_nest
print(collect_nest())
"
```

---

#### Task 3.4: collect_sensibo() (5 min)

**Replace TODO with:**

```python
def collect_sensibo():
    """Collect Sensibo mini-split data (Bedroom)"""
    from components.sensibo import SensiboAPI

    try:
        sensibo = SensiboAPI()
        status = sensibo.get_status()

        return {
            'bedroom_sensibo_f': round(status['current_temp_f'], 1),
            'bedroom_sensibo_target_f': round(status['target_temp_f'], 1),
            'bedroom_sensibo_humidity': round(status['current_humidity'], 1),
            'bedroom_sensibo_on': 1 if status['on'] else 0,
            'bedroom_sensibo_mode': status['mode'],
        }
    except Exception as e:
        logger.warning(f"Failed to collect Sensibo data: {e}")
        raise
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_sensibo
print(collect_sensibo())
"
```

---

#### Task 3.5: collect_alen_living() (10 min)

**Replace TODO with:**

```python
def collect_alen_living():
    """Collect Alen air purifier data (Living Room)"""
    from components.tuya import TuyaAPI

    try:
        tuya = TuyaAPI()

        # Check if living room purifier configured
        # This will raise exception if not configured
        aq = tuya.get_air_quality('living_room')

        return {
            'living_alen_pm25': aq['pm25'],
            'living_alen_aqi': aq['aqi'],
        }
    except Exception as e:
        # Not configured or API error - return N/A
        logger.debug(f"Alen living room not available: {e}")
        return {}  # Will use N/A defaults
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_alen_living
print(collect_alen_living())
"
# Expected: {} (empty dict, not configured yet)
```

---

#### Task 3.6: collect_alen_bedroom() (5 min)

**Replace TODO with:**

```python
def collect_alen_bedroom():
    """Collect Alen air purifier data (Bedroom)"""
    from components.tuya import TuyaAPI

    try:
        tuya = TuyaAPI()
        aq = tuya.get_air_quality('bedroom')

        return {
            'bedroom_alen_pm25': aq['pm25'],
            'bedroom_alen_aqi': aq['aqi'],
        }
    except Exception as e:
        logger.debug(f"Alen bedroom not available: {e}")
        return {}
```

**Test:** Same as 3.5

---

#### Task 3.7: collect_tapo_heater() (5 min)

**Replace TODO with:**

```python
def collect_tapo_heater():
    """Collect Tapo heater outlet state"""
    from components.tapo import TapoAPI

    try:
        tapo = TapoAPI()
        status = tapo.get_status('Master Heater')

        return {
            'heater_on': 1 if status['on'] else 0,
        }
    except Exception as e:
        logger.warning(f"Failed to collect heater status: {e}")
        raise
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_tapo_heater
print(collect_tapo_heater())
"
```

---

#### Task 3.8: collect_system_state() (10 min)

**Replace TODO with:**

```python
def collect_system_state():
    """Determine current system state (presence, transition)"""
    from lib.transitions import is_sleep_time
    from datetime import datetime

    # Determine presence (home/away)
    # TODO: Add actual presence detection when available
    # For now, assume home
    presence = 'home'

    # Determine transition state
    now = datetime.now()
    current_hour = now.hour

    if is_sleep_time():
        transition_state = 'sleep'
    elif 5 <= current_hour < 22:
        transition_state = 'wake'
    else:
        transition_state = 'sleep'

    return {
        'presence': presence,
        'transition_state': transition_state,
    }
```

**Test:**
```python
python -c "
import sys
sys.path.insert(0, '.')
from automations.temp_data_logger import collect_system_state
print(collect_system_state())
"
```

---

### Phase 4: Integration Testing (30 min)

#### Task 4.1: Test full script locally (10 min)

```bash
# Dry run - see what would be collected
python automations/temp_data_logger.py --dry-run

# Real run - create CSV
python automations/temp_data_logger.py

# Check CSV created
cat data/logs/temp_analysis.csv

# Verify header row
head -1 data/logs/temp_analysis.csv

# Verify data row
tail -1 data/logs/temp_analysis.csv

# Count N/A values
grep -o "N/A" data/logs/temp_analysis.csv | wc -l
```

**Expected:**
- CSV created with 2 rows (header + 1 data row)
- Alen columns show N/A (not configured)
- All other sensors have real values
- No errors in output

---

#### Task 4.2: Deploy to Pi (10 min)

```bash
# Commit changes
git add -A
git commit -m "Add temperature data logger

- Collect all temp/HVAC/environmental data every 15min
- CSV output for analysis (Excel, Python, pandas)
- Graceful degradation if sensors unavailable
- ~5 MB/year storage footprint"

git push

# Pull on Pi
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && git pull"
```

---

#### Task 4.3: Test on Pi (10 min)

```bash
# Dry run
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py --dry-run"

# Real run
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py"

# Check CSV
ssh matt.wheeler@100.107.121.6 "cat /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"

# Run twice more to get 3 samples
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py"
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 automations/temp_data_logger.py"

# Verify 4 rows (1 header + 3 data)
ssh matt.wheeler@100.107.121.6 "wc -l /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"
```

**Expected:** `4 /home/matt.wheeler/py_home/data/logs/temp_analysis.csv`

---

### Phase 5: Cron Setup (10 min)

#### Task 5.1: Add cron job

```bash
# SSH to Pi
ssh matt.wheeler@100.107.121.6

# Edit cron file
sudo nano /etc/cron.d/py_home
```

**Add this line:**
```cron
# Temperature data logger - every 15 minutes
*/15 * * * * matt.wheeler cd /home/matt.wheeler/py_home && /usr/bin/python3 automations/temp_data_logger.py >> data/logs/temp_data_logger.log 2>&1
```

**Save and exit** (Ctrl+X, Y, Enter)

```bash
# Restart cron
sudo systemctl restart cron

# Verify cron file
cat /etc/cron.d/py_home

# Check cron is running
systemctl status cron
```

---

#### Task 5.2: Wait for first cron execution (15 min)

```bash
# Note current time
date

# Wait up to 15 minutes for next cron execution

# Check log file created
ssh matt.wheeler@100.107.121.6 "ls -la /home/matt.wheeler/py_home/data/logs/temp_data_logger.log"

# View log
ssh matt.wheeler@100.107.121.6 "cat /home/matt.wheeler/py_home/data/logs/temp_data_logger.log"

# Check CSV grew
ssh matt.wheeler@100.107.121.6 "wc -l /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"
```

**Expected:** Row count increased by 1

---

### Phase 6: Validation (24 hours passive)

#### Task 6.1: Check after 24 hours

```bash
# Check row count (should be ~100: 1 header + ~96 data rows + previous test rows)
ssh matt.wheeler@100.107.121.6 "wc -l /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"

# Check file size (should be ~15 KB)
ssh matt.wheeler@100.107.121.6 "ls -lh /home/matt.wheeler/py_home/data/logs/temp_analysis.csv"

# Check for errors in log
ssh matt.wheeler@100.107.121.6 "grep -i error /home/matt.wheeler/py_home/data/logs/temp_data_logger.log"

# Count N/A values per column
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && python3 -c \"
import csv
with open('data/logs/temp_analysis.csv') as f:
    reader = csv.DictReader(f)
    cols = reader.fieldnames
    na_counts = {col: 0 for col in cols}
    total = 0
    for row in reader:
        total += 1
        for col in cols:
            if row[col] == 'N/A':
                na_counts[col] += 1
    for col, count in na_counts.items():
        if count > 0:
            print(f'{col}: {count}/{total} ({100*count/total:.1f}%)')
\""
```

**Expected:**
- Alen columns: 100% N/A (not configured)
- All others: <5% N/A

---

## Rollback Procedure

If issues occur:

### 1. Disable cron
```bash
ssh matt.wheeler@100.107.121.6
sudo nano /etc/cron.d/py_home
# Comment out temp data logger line with #
sudo systemctl restart cron
```

### 2. Keep CSV data
- CSV file is safe to keep
- Contains valuable data already collected

### 3. Fix and redeploy
```bash
# Fix issues locally
# Test thoroughly
python automations/temp_data_logger.py --dry-run
python automations/temp_data_logger.py

# Commit and deploy
git add automations/temp_data_logger.py
git commit -m "Fix data logger issue"
git push

# Pull on Pi
ssh matt.wheeler@100.107.121.6 "cd /home/matt.wheeler/py_home && git pull"

# Re-enable cron
sudo nano /etc/cron.d/py_home
# Uncomment line
sudo systemctl restart cron
```

---

## Checklist

### Pre-Implementation
- [ ] Read specification (`specs/temperature_data_logger.md`)
- [ ] Understand CSV column structure
- [ ] Verify all APIs working (OpenWeather, TempStick, Nest, Sensibo, Tapo)

### Phase 1: Config
- [ ] Add data_collection section to config.yaml
- [ ] Test config loads

### Phase 2: Script Structure
- [ ] Create temp_data_logger.py with full structure
- [ ] Test dry-run (all collectors return empty)

### Phase 3: Collectors
- [ ] Implement collect_outdoor_weather()
- [ ] Implement collect_tempstick()
- [ ] Implement collect_nest()
- [ ] Implement collect_sensibo()
- [ ] Implement collect_alen_living()
- [ ] Implement collect_alen_bedroom()
- [ ] Implement collect_tapo_heater()
- [ ] Implement collect_system_state()
- [ ] Test each collector individually

### Phase 4: Integration
- [ ] Test full script locally (dry-run)
- [ ] Test full script locally (real run)
- [ ] Verify CSV created
- [ ] Commit and push
- [ ] Deploy to Pi
- [ ] Test on Pi (dry-run)
- [ ] Test on Pi (real run)
- [ ] Run 3 times, verify 4 rows total

### Phase 5: Cron
- [ ] Add cron job
- [ ] Restart cron
- [ ] Verify cron installed
- [ ] Wait for first execution
- [ ] Check log created
- [ ] Verify CSV grew

### Phase 6: Validation
- [ ] Check after 24 hours
- [ ] Verify ~96 new rows
- [ ] Check file size ~15 KB
- [ ] Verify <5% N/A (except Alen)
- [ ] No errors in log

### Post-Implementation
- [ ] Remove test CSV rows if needed
- [ ] Document in README
- [ ] Update backlog (remove task)

---

## Troubleshooting

### CSV not created
- Check directory permissions: `ls -la data/logs/`
- Check script runs: `python automations/temp_data_logger.py --dry-run`
- Check for errors in output

### Cron not running
- Check cron status: `systemctl status cron`
- Check cron file syntax: `cat /etc/cron.d/py_home`
- Check log file: `tail -20 data/logs/temp_data_logger.log`

### Too many N/A values
- Check individual collector functions
- Test APIs manually
- Check API rate limits
- Verify credentials in .env

### High error rate
- Check temp_data_logger.log
- Identify failing source
- Test that source independently
- Consider disabling source in config

---

## Success Criteria

- ✅ CSV file exists at `data/logs/temp_analysis.csv`
- ✅ New row every 15 minutes
- ✅ Header row matches CSV_COLUMNS exactly
- ✅ All configured sensors (except Alen) have <5% N/A
- ✅ File grows by ~14 KB/day
- ✅ No errors in temp_data_logger.log
- ✅ Cron running every 15 minutes
- ✅ Can load CSV into Excel/pandas without errors

---

## Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | Configuration | 10 min | 10 min |
| 2 | Script structure | 20 min | 30 min |
| 3 | Collectors (8 functions) | 60 min | 90 min |
| 4 | Integration testing | 30 min | 120 min |
| 5 | Cron setup | 10 min | 130 min |
| 6 | Wait for cron | 15 min | 145 min |

**Total active work:** ~2.5 hours
**Plus:** 24 hours passive monitoring

---

## References

- **Specification:** `specs/temperature_data_logger.md`
- **Implementation Plan:** `plans/temperature_data_logger_plan.md`
- **This Dev Plan:** `dev/designs/temp_data_logger_dev_plan.md`

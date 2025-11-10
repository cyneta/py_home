# Temperature and Environmental Data Logger - Specification

**Version:** 1.0
**Date:** 2025-11-08
**Status:** Draft

## Overview

A comprehensive data collection system that logs all temperature, HVAC, and environmental sensor data to CSV files for long-term analysis and optimization of comfort and efficiency.

## Purpose

Enable data-driven optimization by:
1. **Comfort Analysis** - Correlate outdoor conditions with indoor temperature stability
2. **Efficiency Analysis** - Track HVAC runtime vs outdoor temperature
3. **Pattern Detection** - Identify daily/weekly trends and anomalies
4. **System Validation** - Verify thermostat accuracy vs independent sensors
5. **Air Quality Tracking** - Monitor indoor air quality and purifier effectiveness

## Scope

### In Scope
- Periodic data collection from all environmental sensors
- CSV output for easy analysis (Excel, Python, R)
- Graceful error handling (continue logging even if some sensors fail)
- Configurable logging interval
- Minimal performance impact (<1% CPU, <5 MB/year storage)
- Run indefinitely without manual intervention

### Out of Scope
- Real-time analysis or visualization (future enhancement)
- Alerts or notifications based on data (use existing monitoring)
- Historical data backfill (starts logging from deployment date)
- Data retention policies (keep all data indefinitely for now)

## Data Sources

### Temperature Sensors
1. **OpenWeather API** - Outdoor conditions
   - Temperature (°F)
   - Weather condition (clear/cloudy/rain/etc.)
   - Wind speed (mph)
   - Cloud cover (%)
   - Sunrise/sunset times

2. **TempStick** (Living Room)
   - Indoor temperature (°F)
   - Humidity (%)
   - Location: Near workspace in living room

3. **Nest Thermostat** (Living Room)
   - Current temperature (°F) - if available from API
   - Target temperature (°F)
   - HVAC mode (HEAT/COOL/OFF/ECO)

4. **Sensibo Mini-Split** (Bedroom)
   - Current temperature (°F)
   - Target temperature (°F)
   - Humidity (%)
   - On/off state
   - HVAC mode (heat/cool/fan/dry/auto)

### Air Quality Sensors (Future)
5. **Alen Air Purifier - Living Room** (when configured)
   - PM2.5 (μg/m³)
   - AQI (US EPA scale)

6. **Alen Air Purifier - Bedroom** (when configured)
   - PM2.5 (μg/m³)
   - AQI (US EPA scale)

### Device States
7. **Tapo Smart Outlet** - Master Heater
   - On/off state

8. **System State**
   - Presence (home/away)
   - Transition state (wake/sleep/day)

## Data Format

### CSV File Structure

**Location:** `data/logs/temp_analysis.csv`

**Format:** CSV with header row

**Columns:**
```csv
timestamp,outdoor_f,outdoor_condition,wind_mph,cloud_pct,sunrise,sunset,living_tempstick_f,living_tempstick_humidity,living_nest_f,living_nest_target_f,living_nest_mode,living_alen_pm25,living_alen_aqi,bedroom_sensibo_f,bedroom_sensibo_target_f,bedroom_sensibo_humidity,bedroom_sensibo_on,bedroom_sensibo_mode,bedroom_alen_pm25,bedroom_alen_aqi,heater_on,presence,transition_state
```

**Example Row:**
```csv
2025-11-08 14:00:00,52.6,scattered clouds,8.5,40,07:15:00,16:45:00,67.5,53.0,68.1,70,HEAT,12,50,68.2,70,63.1,1,heat,15,55,0,home,day
```

### Field Definitions

| Field | Type | Description | Source | Fallback |
|-------|------|-------------|--------|----------|
| `timestamp` | datetime | ISO 8601 format | System clock | N/A |
| `outdoor_f` | float | Outdoor temperature (°F) | OpenWeather | N/A |
| `outdoor_condition` | string | Weather description | OpenWeather | N/A |
| `wind_mph` | float | Wind speed (mph) | OpenWeather | N/A |
| `cloud_pct` | int | Cloud cover 0-100% | OpenWeather | N/A |
| `sunrise` | time | Sunrise time (HH:MM:SS) | OpenWeather | N/A |
| `sunset` | time | Sunset time (HH:MM:SS) | OpenWeather | N/A |
| `living_tempstick_f` | float | Living room temp (°F) | TempStick | N/A |
| `living_tempstick_humidity` | float | Living room humidity (%) | TempStick | N/A |
| `living_nest_f` | float | Nest current temp (°F) | Nest | N/A |
| `living_nest_target_f` | float | Nest target temp (°F) | Nest | N/A |
| `living_nest_mode` | string | Nest mode (HEAT/COOL/ECO/OFF) | Nest | N/A |
| `living_alen_pm25` | int | Living room PM2.5 (μg/m³) | Alen | N/A |
| `living_alen_aqi` | int | Living room AQI (0-500) | Alen | N/A |
| `bedroom_sensibo_f` | float | Bedroom current temp (°F) | Sensibo | N/A |
| `bedroom_sensibo_target_f` | float | Bedroom target temp (°F) | Sensibo | N/A |
| `bedroom_sensibo_humidity` | float | Bedroom humidity (%) | Sensibo | N/A |
| `bedroom_sensibo_on` | int | Sensibo on/off (1/0) | Sensibo | N/A |
| `bedroom_sensibo_mode` | string | Sensibo mode (heat/cool/fan/dry/auto) | Sensibo | N/A |
| `bedroom_alen_pm25` | int | Bedroom PM2.5 (μg/m³) | Alen | N/A |
| `bedroom_alen_aqi` | int | Bedroom AQI (0-500) | Alen | N/A |
| `heater_on` | int | Heater outlet state (1/0) | Tapo | N/A |
| `presence` | string | home/away | System state | N/A |
| `transition_state` | string | wake/sleep/day/away | System state | N/A |

**Note:** All fields use `N/A` if sensor unavailable or API error occurs.

## Configuration

### Config File Location
`config/config.yaml`

### New Configuration Section
```yaml
# Data Collection for Analysis
data_collection:
  temperature_logging:
    enabled: true
    interval_minutes: 15
    file: "data/logs/temp_analysis.csv"

    # Graceful degradation - continue logging even if some sources fail
    continue_on_error: true

    # Data sources to collect (can disable individually)
    sources:
      outdoor_weather: true      # OpenWeather API
      tempstick: true           # Living room TempStick
      nest: true                # Living room Nest
      sensibo: true             # Bedroom Sensibo
      alen_living: true         # Living room Alen (skip if not configured)
      alen_bedroom: true        # Bedroom Alen (skip if not configured)
      tapo_heater: true         # Master heater outlet
      system_state: true        # Presence and transition state
```

## Execution Schedule

### Cron Job
```bash
# Temperature data logger - every 15 minutes
*/15 * * * * cd /home/matt.wheeler/py_home && /usr/bin/python3 automations/temp_data_logger.py >> data/logs/temp_data_logger.log 2>&1
```

### Timing
- **Interval:** 15 minutes (configurable)
- **Daily samples:** 96 (24 hours × 4 samples/hour)
- **Annual samples:** 35,040

## Data Volume Estimates

### Per Sample
- **Row size:** ~150 bytes (with CSV overhead)

### Storage Requirements
- **Per day:** 96 samples × 150 bytes = 14.4 KB
- **Per month:** ~432 KB
- **Per year:** ~5 MB
- **5 years:** ~25 MB
- **10 years:** ~50 MB

**Conclusion:** Storage is negligible. Log indefinitely without rotation.

## Error Handling

### API Failures
- Log `N/A` for failed sensor
- Continue collecting from other sensors
- Log error to `temp_data_logger.log`
- Do NOT send notifications (this is passive monitoring)

### Rate Limiting
- All sensors already have rate limit handling
- OpenWeather: 1,000 calls/day free tier (we use 96/day = OK)
- TempStick: Unknown limits (monitor for errors)
- Nest: 5 calls/min, 500/day (we use 96/day = OK)
- Sensibo: Unknown limits (monitor for errors)
- Tapo: Local API (no rate limits)

### File I/O Errors
- Retry once on write failure
- Log error and skip this sample if retry fails
- Continue on next scheduled run

## Performance Impact

### CPU Usage
- **Per execution:** <100ms total
- **Impact:** <0.003% CPU (100ms every 15 min)

### Memory Usage
- **Script runtime:** <50 MB
- **File growth:** 14 KB/day

### Network Usage
- **Per execution:** ~10 KB (5 API calls)
- **Per day:** ~1 MB (96 executions)
- **Per month:** ~30 MB

## Security & Privacy

### Data Sensitivity
- **Public data:** Weather (already public)
- **Private data:** Home temperature, presence, HVAC usage
- **No PII:** No names, locations (other than city), or identifiable info

### Access Control
- **File permissions:** 644 (readable by pi user)
- **Location:** Inside py_home project (not web-accessible)
- **Backups:** Included in daily USB backup

### Data Retention
- **Keep all data** - no automatic deletion
- **Manual cleanup** - user can delete old CSV files if needed

## Use Cases

### 1. Temperature Boost Optimization
**Question:** When outdoor temp rises during the day, how long does it take for indoor temp to warm up?

**Analysis:**
```python
# Load CSV
df = pd.read_csv('temp_analysis.csv')

# Filter morning hours when boost was active
morning = df[(df['transition_state'] == 'wake') & (df['outdoor_f'] < 40)]

# Track indoor temp rise vs outdoor temp rise
# Determine optimal boost duration
```

### 2. HVAC Efficiency
**Question:** How much does Nest run when outdoor temp is X°F?

**Analysis:**
```python
# Calculate runtime by checking mode changes
# Group by outdoor temp ranges
# Identify inefficient temperature ranges
```

### 3. Sensor Accuracy
**Question:** Does Nest thermostat read accurately vs TempStick?

**Analysis:**
```python
# Compare living_nest_f vs living_tempstick_f
# Calculate average delta
# Identify if Nest sensor has bias
```

### 4. Air Quality vs HVAC
**Question:** Does running heat/AC affect indoor PM2.5?

**Analysis:**
```python
# Correlate bedroom_alen_pm25 with bedroom_sensibo_on
# Check if HVAC filters improve air quality
```

### 5. Comfort Correlation
**Question:** What indoor temp is comfortable when outdoor is 35°F vs 55°F?

**Analysis:**
```python
# User manually notes comfort level in separate file
# Correlate with indoor/outdoor temps at those times
# Optimize setpoints for comfort
```

## Success Criteria

1. ✅ Data logger runs continuously without intervention
2. ✅ CSV file grows by ~14 KB/day
3. ✅ All configured sensors logged every 15 minutes
4. ✅ Missing data (N/A) is <5% of samples for each sensor
5. ✅ No performance impact on other py_home functions
6. ✅ Data can be loaded into Excel/Python without errors

## Future Enhancements (Out of Scope)

- **Real-time dashboard** - Web UI showing current trends
- **Automated analysis** - Weekly reports on efficiency/comfort
- **Alerts** - Notify when patterns change (e.g., HVAC runtime increases)
- **Data export** - API endpoint for retrieving analysis data
- **Machine learning** - Predict optimal setpoints based on historical data
- **Integration** - Push data to InfluxDB/Grafana for visualization

## References

- **Design Rationale:** `dev/designs/temperature_data_logger_design.md` (this document)
- **Implementation Plan:** `plans/temperature_data_logger_plan.md`
- **OpenWeather API:** https://openweathermap.org/api
- **TempStick API:** Via services/tempstick.py
- **Nest API:** Via components/nest/
- **Sensibo API:** Via components/sensibo/

# TempStick Thermostat Implementation Plan

**Date:** 2025-11-05
**Status:** Design Phase
**Goal:** Create temperature-controlled heater using TempStick sensor + Tapo smart outlet

---

## Executive Summary

Build a thermostat controller using existing TempStick WiFi sensor to control a heater plugged into a Tapo smart outlet. The system uses 5-minute polling (TempStick's minimum) with hysteresis control algorithm and comprehensive safety features.

**Key Constraint:** TempStick reports every 5-15 minutes (not 1-minute as initially hoped)
**Solution:** Use larger deadband (4°F) and proper control algorithm to compensate

---

## 1. System Architecture

```
TempStick Sensor (Crawl Space)
        ↓ (Cloud API, 5-min intervals)
    Flask Server
        ↓ (Thermostat Logic)
    Tapo Smart Outlet
        ↓ (Power Control)
    Space Heater
```

### Components

1. **Sensor:** Existing TempStick (TS00EMA9JZ) - currently monitoring crawl space
2. **Controller:** New thermostat automation (Python)
3. **Actuator:** Tapo smart outlet (plug name: TBD)
4. **Load:** Space heater (manual thermostat set to max, controlled by outlet power)

---

## 2. Control Algorithm

### Hysteresis (Deadband) Control

**Why hysteresis?**
- Simple and robust
- Prevents rapid on/off cycling
- Tolerates polling delays
- Industry standard for thermostats

**Parameters:**
```python
SETPOINT = 68.0°F          # Target temperature
DEADBAND = 4.0°F           # Total range (±2°F from setpoint)

HEAT_ON_TEMP = 66.0°F      # Turn heater ON when below this
HEAT_OFF_TEMP = 70.0°F     # Turn heater OFF when above this
```

**Logic:**
```
if temp < 66°F:  heater = ON
if temp > 70°F:  heater = OFF
if 66°F ≤ temp ≤ 70°F:  heater = (maintain current state)
```

### Timing Constraints

```python
MIN_CYCLE_TIME = 600 sec    # 10 min - heater must run at least this long
MIN_OFF_TIME = 300 sec      # 5 min - minimum time between cycles
MAX_RUN_TIME = 3600 sec     # 1 hour - safety shutoff
MAX_CYCLES_PER_HOUR = 6     # Typical HVAC limit
```

---

## 3. Safety Features

### Critical Safety Checks

1. **Sensor Health Monitoring**
   - Check `is_online` flag from API
   - Check `last_checkin` timestamp (must be <10 min old)
   - **Action:** Turn OFF heater if sensor offline/stale

2. **Maximum Run Time**
   - 1 hour continuous operation limit
   - **Action:** Force heater OFF, require manual reset
   - **Alert:** Send high-priority notification

3. **Temperature Limits**
   - Emergency shutoff at 85°F (absolute maximum)
   - Freeze warning at 50°F (sensor may be malfunctioning)
   - **Action:** Turn OFF heater, send alert

4. **Cycle Rate Limiting**
   - Maximum 6 cycles per hour
   - **Alert:** Warn if cycling too frequently (may indicate problem)

5. **Sensor Data Staleness**
   - Reject readings older than 10 minutes
   - **Action:** Turn OFF heater until fresh data available

6. **Minimum Cycle Times**
   - Heater must run at least 10 minutes once started
   - Heater must stay off at least 5 minutes between cycles
   - **Purpose:** Prevent equipment damage

### Fail-Safe Behavior

**Default action on ANY error:** Turn heater OFF
- Sensor API error → OFF
- Tapo control error → OFF (log failure)
- Uncaught exception → OFF + alert

---

## 4. Implementation Tasks

### Phase 1: Core Infrastructure (Week 1)

**Files to create:**

1. **services/thermostat.py** (~200 lines)
   - `Thermostat` class with hysteresis control
   - State tracking (heater on/off, cycle times, cycle count)
   - Safety checks (max run time, cycle rate, minimum times)
   - Setpoint management
   - Comprehensive logging

2. **automations/thermostat_control.py** (~150 lines)
   - Main automation script (runs every 5 minutes via cron)
   - Integrates: TempStick sensor + Thermostat controller + Tapo outlet
   - Sensor health validation
   - Temperature safety checks
   - Error handling with fail-safe shutoff
   - Notification on safety events

**Files to modify:**

3. **config/config.yaml**
   - Add `thermostat` section with setpoint, deadband, timing params
   - Add heater outlet configuration

4. **components/tapo.py** (if needed)
   - Verify `control_outlet()` or equivalent function exists
   - Add heater-specific control function if needed

**Configuration:**

5. **TempStick sensor reconfiguration**
   - Change from 30-min interval to 5-min alert mode (via TempStick mobile app)
   - Verify sensor location appropriate for space being heated

**Deployment:**

6. **Cron job**
   ```bash
   */5 * * * * cd /home/pi/py_home && python automations/thermostat_control.py
   ```

**Testing:**

7. **Unit tests** - `tests/test_thermostat.py`
   - Test hysteresis logic (on/off transitions)
   - Test safety features (max run time, cycle rate)
   - Test minimum cycle time enforcement
   - Test sensor health checks

8. **Integration test** - `tests/test_thermostat_integration.py`
   - Mock TempStick API responses
   - Mock Tapo outlet control
   - Verify end-to-end behavior

### Phase 2: Monitor-Only Testing (1 week)

**Purpose:** Validate algorithm without controlling actual heater

**Implementation:**
- Add `DRY_RUN` flag to thermostat_control.py
- Log what decisions WOULD be made
- Don't actually control Tapo outlet
- Collect data on:
  - Temperature trends
  - Predicted cycle frequency
  - Predicted cycle durations
  - Sensor reliability

**Success criteria:**
- Sensor reports reliably every 5 minutes
- Algorithm makes sensible decisions
- No excessive cycling predicted
- Temperature stays within expected range

### Phase 3: Supervised Operation (1 week)

**Purpose:** Test with real heater under supervision

**Implementation:**
- Enable heater control during daytime only (8am-10pm)
- Monitor closely for issues
- Verify safety features work
- Physical checks:
  - Heater responds to outlet control
  - No overheating
  - No electrical issues
  - Outlet handles heater load

**Success criteria:**
- Temperature controlled within ±2-3°F of setpoint
- No short-cycling
- Safety features activate correctly
- No equipment issues

### Phase 4: Full Deployment

**Purpose:** 24/7 autonomous operation

**Implementation:**
- Enable continuous operation
- Set up monitoring dashboard
- Configure alerts
- Document manual override procedures

**Ongoing monitoring:**
- Daily log review (first week)
- Weekly log review (first month)
- Alert on anomalies

---

## 5. Configuration Schema

### config/config.yaml additions

```yaml
thermostat:
  enabled: true

  # Control parameters
  setpoint: 68.0              # Target temperature (°F)
  deadband: 4.0               # Hysteresis range (°F)

  # Timing constraints
  min_cycle_time: 600         # Minimum heater run time (seconds)
  min_off_time: 300           # Minimum time between cycles (seconds)
  max_run_time: 3600          # Maximum continuous run time (seconds)
  max_cycles_per_hour: 6      # Alert threshold

  # Safety limits
  max_safe_temp: 85.0         # Emergency shutoff temperature (°F)
  min_safe_temp: 45.0         # Freeze protection (°F)
  max_sensor_age: 600         # Maximum sensor data age (seconds)

  # Hardware
  sensor: tempstick            # Sensor type (currently only 'tempstick')
  heater_outlet: "Space Heater"  # Tapo outlet name/device_id

  # Operation modes
  mode: auto                   # auto, off, manual
  schedule_enabled: false      # Future: time-based setpoint schedules
```

---

## 6. API Endpoints (Future Enhancement)

### Dashboard Integration

**GET /api/thermostat/status**
```json
{
  "enabled": true,
  "mode": "auto",
  "setpoint": 68.0,
  "current_temp": 67.5,
  "heater_on": true,
  "cycle_start_time": "2025-11-05T14:30:00Z",
  "time_in_state": 420,
  "cycles_this_hour": 2,
  "sensor_healthy": true,
  "last_update": "2025-11-05T14:37:00Z"
}
```

**POST /api/thermostat/setpoint**
```json
{
  "setpoint": 70.0
}
```

**POST /api/thermostat/mode**
```json
{
  "mode": "off"  // auto, off, manual
}
```

---

## 7. Logging and Monitoring

### Log Events

**INFO level:**
- Heater state changes (on→off, off→on)
- Setpoint changes
- Mode changes
- Normal operation summary every hour

**WARNING level:**
- High cycle rate (>6/hour)
- Sensor data staleness (>5 min old)
- Temperature approaching limits

**ERROR level:**
- Sensor offline
- Tapo control failure
- Temperature limit exceeded
- Max run time exceeded

### Log Format (kvlog)

```python
kvlog(logger, logging.INFO,
      automation='thermostat_control',
      event='heater_on',
      temp=67.5,
      setpoint=68.0,
      threshold=66.0,
      cycle_count=2)
```

### Alerts

**High priority (send_high):**
- Sensor offline >10 minutes
- Temperature >85°F (emergency)
- Max run time exceeded
- Control failure

**Medium priority (send_automation_summary):**
- Sensor data stale (5-10 min)
- High cycle rate
- Temperature approaching limits

**Low priority (daily digest):**
- Operation summary
- Statistics (avg temp, cycle count, run time)

---

## 8. Dashboard Enhancements

### New Card: Thermostat Status

```html
<div class="card">
  <h3>🌡️ Thermostat</h3>
  <div class="thermostat-display">
    <div class="current-temp">67.5°F</div>
    <div class="setpoint">Target: 68°F</div>
    <div class="status heater-on">🔥 Heating</div>
    <div class="cycle-info">On for 7 min</div>
  </div>
  <div class="controls">
    <button onclick="adjustSetpoint(-1)">-</button>
    <button onclick="adjustSetpoint(1)">+</button>
  </div>
</div>
```

---

## 9. Testing Strategy

### Unit Tests

**Test cases:**
1. Hysteresis logic (transitions at correct temperatures)
2. State maintenance in deadband
3. Minimum cycle time enforcement
4. Minimum off time enforcement
5. Maximum run time safety shutoff
6. Cycle rate counting
7. Setpoint changes recalculate thresholds
8. Safety overrides

### Integration Tests

**Test scenarios:**
1. Normal heating cycle (cold→warm→maintain)
2. Sensor goes offline mid-cycle
3. Sensor data becomes stale
4. Temperature exceeds safety limit
5. Max run time exceeded
6. Rapid temperature fluctuations
7. API errors (TempStick, Tapo)

### Manual Testing Checklist

**Phase 2 (Monitor-Only):**
- [ ] Algorithm runs every 5 minutes
- [ ] Logs show correct decisions
- [ ] Sensor data fresh and reliable
- [ ] No exceptions in logs

**Phase 3 (Supervised):**
- [ ] Heater responds to on commands
- [ ] Heater responds to off commands
- [ ] Temperature reaches setpoint
- [ ] Heater cycles off when warm
- [ ] Minimum cycle times enforced
- [ ] Manual override works (turn off via Tapo app)
- [ ] Safety shutoff at max run time
- [ ] Sensor offline triggers shutoff
- [ ] Alerts received for safety events

**Phase 4 (Full Deployment):**
- [ ] 24-hour continuous operation successful
- [ ] Temperature stable overnight
- [ ] No spurious alerts
- [ ] Dashboard shows correct status
- [ ] Logs show healthy operation

---

## 10. Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Sensor reports too slowly | HIGH | Medium | Use 4°F deadband, accept variation |
| Sensor goes offline | Medium | HIGH | Fail-safe shutoff, alerts |
| Tapo control fails | Low | HIGH | Error detection, alerts, manual override |
| Heater stuck on | Low | CRITICAL | Max run time, temperature limits |
| Short-cycling damages heater | Medium | Medium | Minimum cycle times, rate monitoring |
| Temperature overshoot | Medium | Low | Proper deadband tuning |

### Safety Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Fire hazard (heater malfunction) | Very Low | CRITICAL | Max run time, temp limits, manual override |
| Freeze damage (system fails off) | Low | Medium | Fail-safe prefers OFF, low-temp alerts |
| Carbon monoxide (if gas heater) | N/A | CRITICAL | Use electric heater only |
| Electrical overload | Low | Medium | Use properly rated outlet, check heater specs |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Poor comfort (wide temp swings) | Medium | Low | Tune deadband based on testing |
| Excessive energy use | Low | Low | Monitor cycle times, adjust setpoint |
| Alert fatigue | Medium | Medium | Rate-limit alerts, tune thresholds |
| System complexity | Low | Low | Comprehensive docs, simple algorithm |

---

## 11. Future Enhancements

### Short-term (Phase 5)

1. **Dashboard integration** - Real-time thermostat card
2. **Setpoint adjustment API** - Change target via web/Shortcuts
3. **Statistics tracking** - Daily summaries (run time, cycles, avg temp)
4. **Multiple sensors** - Average crawl space + bedroom sensors

### Medium-term

1. **Schedule support** - Lower setpoint at night, raise in morning
2. **Occupancy integration** - Lower when away, raise before arrival
3. **Weather-based control** - Preheat if cold weather forecast
4. **Energy monitoring** - Track heater power usage (if Tapo outlet supports)

### Long-term

1. **PID control** - More sophisticated algorithm for tighter control
2. **Predictive heating** - Learn thermal characteristics, preheat
3. **Multi-zone** - Control multiple heaters independently
4. **Machine learning** - Optimize for comfort + efficiency

---

## 12. Estimated Effort

### Development Time

| Phase | Tasks | Estimated Hours |
|-------|-------|----------------|
| Phase 1: Core Implementation | Code + tests + config | 6-8 hours |
| Phase 2: Monitor-Only Testing | Deploy + observe + tune | 1 week (passive) |
| Phase 3: Supervised Operation | Deploy + monitor + validate | 1 week (active) |
| Phase 4: Full Deployment | Enable + document + monitor | 1 week (passive) |
| **Total active development** | | **6-8 hours** |
| **Total testing/validation** | | **3 weeks** |

### Maintenance

- **Weekly:** Review logs for first month
- **Monthly:** Check performance, tune if needed
- **As needed:** Respond to alerts

---

## 13. Success Criteria

### Technical Success

- ✅ Temperature maintained within ±3°F of setpoint
- ✅ Heater cycles 3-6 times per hour (normal range)
- ✅ No short-cycling (<5 min cycles)
- ✅ Sensor reports reliably every 5 minutes
- ✅ Safety features activate when triggered
- ✅ No unhandled exceptions in logs

### Operational Success

- ✅ System runs autonomously for 1 week without intervention
- ✅ User comfort acceptable (temperature feels stable)
- ✅ Energy usage reasonable (not excessive cycling)
- ✅ Alerts timely and actionable (not too many/few)

### Code Quality

- ✅ All unit tests pass
- ✅ Integration tests pass
- ✅ Code follows project conventions (kvlog, error handling)
- ✅ Documentation complete (docstrings, README)
- ✅ Configuration clear and commented

---

## 14. Decision Log

### Design Decisions

**Decision:** Use hysteresis control instead of PID
- **Rationale:** Simple, robust, tolerates 5-min polling delay
- **Tradeoff:** Wider temperature swings vs. complexity

**Decision:** 4°F deadband (±2°F from setpoint)
- **Rationale:** Compensates for 5-min sensor delay, prevents short-cycling
- **Tradeoff:** Less tight control vs. equipment protection

**Decision:** 10-minute minimum cycle time
- **Rationale:** Protect heater equipment, allow thermal mass to respond
- **Tradeoff:** Slower response to disturbances vs. equipment longevity

**Decision:** Fail-safe shutoff on any error
- **Rationale:** Safety first - prefer cold vs. fire hazard
- **Tradeoff:** May shut off unnecessarily vs. safety risk

**Decision:** No local control/override in Phase 1
- **Rationale:** Simplify implementation, can add later
- **Tradeoff:** Must use Tapo app for manual control vs. development time

### Open Questions

1. **Which Tapo outlet?** - Need to identify/configure heater outlet name
2. **Which heater?** - Confirm heater specs (wattage, manual thermostat)
3. **Sensor location?** - Is crawl space sensor appropriate, or need new location?
4. **Alert preferences?** - What notification priority for different events?

---

## 15. References

### Internal Documentation

- **TempStick API:** `dev/apis/TEMPSTICK_API.md`
- **TempStick Service:** `services/tempstick.py`
- **TempStick Monitor:** `automations/tempstick_monitor.py`
- **Tapo Component:** `components/tapo.py`

### External Resources

- **HVAC Best Practices:** Short-cycling prevention, cycle rate limits
- **Thermostat Control Theory:** Hysteresis, deadband, PID controllers
- **TempStick Docs:** Sensor specs, API rate limits, alert mode configuration

---

## Appendix: Code Snippets

### Thermostat Class Interface

```python
class Thermostat:
    def __init__(self, setpoint, deadband, min_cycle_time, max_run_time):
        """Initialize thermostat controller"""

    def update(self, current_temp):
        """
        Update heater state based on temperature

        Returns:
            dict: {
                'heater_on': bool,
                'reason': str,
                'safety_override': bool
            }
        """

    def set_setpoint(self, new_setpoint):
        """Update target temperature"""

    def get_status(self):
        """Get current thermostat status"""
```

### Main Automation Loop

```python
def main():
    # Initialize thermostat
    thermostat = Thermostat(setpoint=68.0, deadband=4.0)

    # Get sensor data
    sensor_data = tempstick.get_sensor_data()

    # Safety checks
    if not validate_sensor(sensor_data):
        shutdown_heater()
        send_alert()
        return

    # Update thermostat logic
    result = thermostat.update(sensor_data['temperature_f'])

    # Control heater
    tapo.control_outlet('heater', result['heater_on'])

    # Log and alert
    log_status(result)
    if result['safety_override']:
        send_alert()
```

---

**END OF PLAN**

# HVAC Coordination Plan

## System Architecture

### Physical Layout

**Upstairs Zone (Main House)**
- **Controller**: Nest Thermostat
- **Heating**: Furnace
- **Cooling**: Central AC (integrated with furnace)
- **Coverage**: HVAC vents throughout upstairs and downstairs

**Master Suite Zone (New Addition)**
- **Controller**: Sensibo (smart controller for legacy mini-split)
- **Heating/Cooling**: Mini-split heat pump
- **Coverage**: Master Suite only (no ductwork connection to main HVAC)
- **Note**: Master Bath has radiant floor heat (not automated currently)

### Current Problem

The existing `automations/temp_coordination.py` has these issues:
1. Uses only Nest temperature to control Sensibo (ignores Master Suite temp)
2. Doesn't check Nest's HVAC status (heating/cooling/off)
3. Hardcodes AC target to 72°F instead of matching Nest target
4. Runs even when nobody home

## Coordination Strategy

### Goals

1. **Comfort consistency** - Master Suite matches Nest target temperature
2. **Energy efficiency** - Turn off mini-split when nobody home
3. **Night mode** - Use mini-split only at night, Nest in ECO mode (save whole-house energy)
4. **Simplicity** - Set targets, let thermostats do the work

### Operating Modes

**Day Mode** (default):
- Sensibo target = Nest target
- Both zones maintain same temperature
- Nest manages upstairs/downstairs, mini-split manages Master Suite

**Night Mode** (triggered by goodnight):
- Nest in ECO mode (minimal whole-house conditioning)
- Sensibo target = 66°F (Master Suite only)
- Saves energy - only condition occupied zone (bedroom)
- Exit when `good_morning` runs

### Decision Logic

```python
# Read Nest target
nest_status = nest.get_status()
nest_target = nest_status['heat_setpoint_f'] or nest_status['cool_setpoint_f']

# Read Sensibo current target
sensibo_status = sensibo.get_status()
sensibo_target = sensibo_status['target_temp_f']

is_home = is_device_home('192.168.50.189')  # iPhone presence
night_mode = check_night_mode()  # Read flag set by goodnight/good_morning

# Priority 1: Turn off mini-split if nobody home
if not is_home:
    if sensibo_status['on']:
        sensibo.turn_off()
        send_notification("Mini-split OFF (nobody home)")
    return
    # Exception: When geofencing implemented, allow pre-arrival conditioning

# Priority 2: Night Mode (goodnight automation triggered)
if night_mode:
    target_temp = 66

    # Only update if different
    if sensibo_target != target_temp or not sensibo_status['on']:
        # Determine mode based on current Master Suite temp
        master_suite_temp = sensibo_status['current_temp_f']
        mode = 'cool' if master_suite_temp > target_temp else 'heat'

        sensibo.turn_on(mode=mode, target_temp_f=target_temp)
        send_notification(f"Night mode: Master Suite → {target_temp}°F")

    return  # Skip day-mode coordination

# Priority 3: Day Mode - Sync Sensibo target to Nest target
if sensibo_target != nest_target:
    # Determine mode based on current Master Suite temp
    master_suite_temp = sensibo_status['current_temp_f']
    mode = 'cool' if master_suite_temp > nest_target else 'heat'

    sensibo.turn_on(mode=mode, target_temp_f=nest_target)
    send_notification(f"Master Suite → {nest_target}°F (following Nest)")

# else: Targets already match, nothing to do
```

### How It Works

**No thresholds needed!** Just set the target and let Sensibo's thermostat handle cycling:
- Sensibo turns on/off automatically to maintain its target
- Sensibo has built-in hysteresis to prevent excessive cycling
- We only intervene when targets need to change

**When does coordination run?**
- Every 15 minutes via cron (check if sync needed)
- When goodnight/good_morning runs (mode change)
- When user changes Nest (future: webhook/polling)

**What about conflicts?**
- Not needed! Both thermostats work independently to their targets
- If Nest heating to 68°F and Sensibo cooling to 68°F = no actual conflict
- They'll both reach 68°F and turn off

### Presence Integration

**Nobody home:**
- Turn OFF mini-split (check if already off to avoid unnecessary API calls)
- Let Nest run normally (it has its own away/eco modes)
- Rationale: Mini-split in single zone (Master Suite), likely unoccupied when away

**Future: Geofencing integration**
- When "arriving home" event triggers (see `GEOFENCING_SCENARIOS.md`)
- Allow pre-conditioning Master Suite based on ETA
- Flag: `preparing_for_arrival = True` to bypass presence check

## Task List

### Phase 1: Simple Target Sync + Night Mode (Immediate)
- [ ] Update `config/config.yaml` with new coordination settings
  - [ ] Add `night_mode_temp_f: 66`
  - [ ] Remove deprecated `trigger_ac_above_f` and `turn_off_ac_below_f`
  - [ ] Remove `zone_temp_threshold_f` (no longer needed)
- [ ] Create night mode state file mechanism
  - [ ] Add `.night_mode` state file (similar to `.presence_state`)
  - [ ] Helper functions: `set_night_mode(enabled)`, `is_night_mode()`
  - [ ] Store in project root or temp directory
- [ ] Update `automations/goodnight.py`
  - [ ] Set Nest to ECO mode instead of sleep_temp: `nest.set_eco_mode(True)`
  - [ ] Set night mode flag: `set_night_mode(True)`
  - [ ] Update notification to mention "Night mode - Nest ECO, Master Suite 66°F"
- [ ] Update `automations/good_morning.py`
  - [ ] Disable Nest ECO mode: `nest.set_eco_mode(False)`
  - [ ] Clear night mode flag: `set_night_mode(False)`
  - [ ] Set Nest to comfort_temp as usual
- [ ] Rewrite `automations/temp_coordination.py`
  - [ ] Import presence detection: `from components.network import is_device_home`
  - [ ] Import night mode helpers: `from lib.night_mode import is_night_mode`
  - [ ] Read Nest target: `heat_setpoint_f` or `cool_setpoint_f`
  - [ ] Read Sensibo current target: `target_temp_f`, `on`, `current_temp_f`
  - [ ] Implement Priority 1: Turn off mini-split if nobody home (check if already off)
  - [ ] Implement Priority 2: Night mode - Set Sensibo to 66°F if different
  - [ ] Implement Priority 3: Day mode - Set Sensibo target = Nest target if different
  - [ ] Determine heat/cool mode based on current Master Suite temp vs target
  - [ ] Update logging to show mode (day/night), targets (Nest vs Sensibo), and actions
  - [ ] Send notification only when taking action (not on every run)
  - [ ] Handle edge case: Nest in OFF mode (keep Sensibo off or use last known target)
- [ ] Test in dry-run mode
  - [ ] Test case 1: Day mode - Nest changes, Sensibo should sync
  - [ ] Test case 2: Day mode - Targets already match (no action)
  - [ ] Test case 3: Night mode - Sensibo set to 66°F
  - [ ] Test case 4: Exit night mode - Sensibo syncs back to Nest
  - [ ] Test case 5: Nobody home - Sensibo turns off
  - [ ] Test case 6: Nest in OFF mode - Sensibo behavior
- [ ] Deploy to Pi and test in production
  - [ ] Monitor logs for 24 hours
  - [ ] Check for excessive cycling
  - [ ] Verify notifications are clear and actionable
- [ ] Update `docs/NOTIFICATION_DESIGN.md` with new temp coordination notification examples
- [ ] Commit changes with descriptive message

### Phase 2: Monitoring & Tuning (After Testing)
- [ ] Monitor coordination logs for 1 week
  - [ ] Track how often targets change
  - [ ] Verify Sensibo's built-in thermostat prevents excessive cycling
  - [ ] Check if any scenarios cause issues
- [ ] If cycling detected (unlikely)
  - [ ] Add debounce logic (don't change target more than once per hour)
  - [ ] Or add threshold back (only sync if >2°F different)
- [ ] Document actual behavior in plan
- [ ] Commit tuning changes if needed

## Implementation Status

### Phase 1: Simple Target Sync + Night Mode (Immediate)
**Goal**: Replace buggy coordination logic with simple target mirroring

**Status**: Not started

**Files to create**:
- `lib/night_mode.py` - State management helpers

**Files to modify**:
- `config/config.yaml` - Add night_mode_temp_f
- `automations/goodnight.py` - Enable night mode, Nest ECO
- `automations/good_morning.py` - Disable night mode, Nest ECO off
- `automations/temp_coordination.py` - Simple target sync logic
- `docs/NOTIFICATION_DESIGN.md` - Update examples

**Estimated effort**: 1-2 hours coding + 24 hours monitoring

**Key simplifications**:
- No thresholds - just sync targets
- No conflict detection - thermostats work independently
- Sensibo handles its own cycling
- Only send notifications when taking action

### Phase 2: Monitoring & Tuning (After Testing)
**Goal**: Verify no cycling issues, tune if needed

**Status**: Waiting for Phase 1

**Prerequisites**: Phase 1 deployed and monitored for 1 week

**Estimated effort**: Minimal (monitoring only, tuning if needed)

## Testing Plan

### Test Cases

**Day Mode Tests:**

1. **Nest target changes**
   - Day mode active, Nest currently 68°F, Sensibo currently 68°F
   - Change Nest to 72°F
   - Wait for coordination (15 min or manual trigger)
   - Verify Sensibo target changes to 72°F
   - Verify notification sent: "Master Suite → 72°F (following Nest)"

2. **Targets already match**
   - Day mode, Nest 70°F, Sensibo 70°F
   - Run coordination
   - Verify no API calls made to Sensibo
   - Verify no notification sent (silent operation)

3. **Sensibo chooses correct mode**
   - Nest target 68°F, Master Suite currently 72°F (warm)
   - Coordination sets Sensibo to 68°F in COOL mode
   - Verify mode='cool' sent to Sensibo API

   - Nest target 72°F, Master Suite currently 68°F (cold)
   - Coordination sets Sensibo to 72°F in HEAT mode
   - Verify mode='heat' sent to Sensibo API

**Night Mode Tests:**

4. **Enter night mode**
   - Run goodnight automation
   - Verify Nest set to ECO mode
   - Verify night mode flag set (.night_mode file exists)
   - Verify Sensibo set to 66°F (cool or heat based on current temp)
   - Verify notification: "Night mode - Nest ECO, Master Suite 66°F"

5. **Night mode maintains 66°F**
   - Night mode active, Sensibo already at 66°F
   - Run coordination
   - Verify no API calls (target already correct)
   - Verify no notification

6. **Exit night mode**
   - Run good_morning automation
   - Verify Nest ECO mode disabled
   - Verify Nest set to comfort_temp (72°F)
   - Verify night mode flag cleared
   - Next coordination run: Sensibo syncs to Nest (72°F)

**Presence Tests:**

7. **Nobody home - turn off**
   - Sensibo currently ON
   - Turn off WiFi (simulate leaving)
   - Wait for presence detection (2 min)
   - Run coordination
   - Verify Sensibo turned OFF
   - Verify notification: "Mini-split OFF (nobody home)"

8. **Nobody home - already off**
   - Sensibo already OFF, nobody home
   - Run coordination
   - Verify no API call (already off)
   - Verify no notification

**Edge Cases:**

9. **Nest in OFF mode**
   - Set Nest mode to OFF
   - Run coordination in day mode
   - Verify behavior: [TBD - keep Sensibo off? use last target?]

10. **First run after deploy**
   - Fresh deploy, no state files
   - Night mode flag doesn't exist
   - Verify defaults to day mode, works correctly

## Configuration

### Current Settings (config.yaml)

```yaml
automation:
  temp_coordination:
    trigger_ac_above_f: 76  # OLD - will be removed
    turn_off_ac_below_f: 74  # OLD - will be removed
```

### New Settings (config.yaml)

```yaml
automation:
  temp_coordination:
    # Night mode temperature for Master Suite
    night_mode_temp_f: 66

    # Future: per-zone settings
    # master_suite:
    #   night_offset_f: -2  # Cooler at night (alternative to fixed 66°F)
    #   occupied_only: true
```

### Important: Disable Nest Scheduling

**Before deploying**, disable Nest's built-in temperature schedule:
- Nest app → Settings → Schedule → Disable
- Reason: Nest schedule will conflict with goodnight/good_morning automations
- We control temps via automations, not Nest's schedule

**Alternative**: Keep Nest schedule as backup if automations fail

## Future Considerations

### Geofencing Pre-Conditioning
- See `GEOFENCING_PLAN.md` for detailed scenarios
- Integration point: Bypass presence check when `preparing_for_arrival` flag set
- Pre-condition Master Suite 15-30 min before arrival

### Master Bath Radiant Floor Heat
- Currently not automated
- Separate thermostat or manual control
- Could integrate later if needed
- Unlikely to affect zone coordination (bathroom is small)

### Seasonal Behavior
- Winter: Nest heats with furnace, mini-split supplements Master Suite
- Summer: Nest cools with central AC, mini-split supplements Master Suite
- Spring/Fall: Minimal coordination needed (mild temps)

### Energy Efficiency Priority
- Mini-split heat pump is efficient for heating (better than furnace for small zone)
- Consider preferring mini-split heat over furnace heat for Master Suite
- Would require reversing master/slave relationship

### Multi-Device Presence
- Currently uses single iPhone (primary occupant)
- Could add Kate's device for better occupancy detection
- Per-zone occupancy would enable more sophisticated control

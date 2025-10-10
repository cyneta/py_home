# Comfort & Efficiency Optimization

Future enhancements for home automation beyond basic coordination

## Time-Based Zone Preferences

### Concept
Different temperature preferences at different times of day

### Master Suite Cooler at Night
**Config**:
```yaml
automation:
  temp_coordination:
    master_suite:
      night_offset_f: -2
      night_hours:
        start: "22:00"  # 10 PM
        end: "06:00"    # 6 AM
```

**Logic**:
- During night hours: Master Suite targets Nest temp - 2°F
- Example: Nest at 68°F → Master Suite targets 66°F
- Better sleep quality (cooler bedroom)

**Implementation**:
```python
nest_target = 68  # From Nest API
current_hour = datetime.now().hour

if 22 <= current_hour or current_hour < 6:  # Night time
    master_suite_target = nest_target - 2
else:
    master_suite_target = nest_target
```

### Living Room Warmer During Day
**Use case**: Working from home, want living room warmer than bedroom

**Future expansion**: Multiple zones with different preferences

## Seasonal Logic

### Skip Coordination in Mild Weather
**Problem**: Running coordination year-round wastes API calls and energy

**Solution**: Only coordinate during heating/cooling seasons

#### Option A: Month-Based
```yaml
automation:
  temp_coordination:
    active_months: [4, 5, 6, 7, 8, 9, 10]  # Apr-Oct
```

**Pros**: Simple, predictable
**Cons**: Doesn't account for early/late season temperature swings

#### Option B: Mode-Based (Recommended)
```python
# Check if Nest is in HEAT or COOL mode
if nest_mode == 'OFF':
    # Skip coordination, mild weather
    return
```

**Pros**: Adapts to actual usage
**Cons**: User must remember to turn off Nest in spring/fall

#### Option C: Weather-Based
```python
outdoor_temp = get_weather()['temp_f']

if 60 <= outdoor_temp <= 75:
    # Mild weather, skip coordination
    return
```

**Pros**: Fully automatic
**Cons**: Requires weather API, may not match user preference

### Winter vs Summer Strategies

**Winter** (Heating):
- Mini-split heat pump very efficient for small zones
- Consider using mini-split MORE than furnace
- Furnace heats whole house (wasteful for single zone)

**Summer** (Cooling):
- Central AC already running for whole house
- Mini-split supplements only when needed
- Current strategy is good

**Potential improvement**: Prefer mini-split in winter, supplement central AC in summer

## Energy Monitoring

### Track HVAC Energy Usage

#### Hardware Options
1. **Smart plugs with power monitoring** (~$15-25)
   - Tapo P115 (have similar models)
   - Measures mini-split power draw
   - Can't measure furnace/central AC (hardwired)

2. **Whole-home energy monitor** (~$150-300)
   - Sense Energy Monitor
   - Emporia Vue
   - Tracks all circuits including HVAC
   - More expensive, complex install

#### Metrics to Track
- Mini-split runtime hours per day
- Power consumption per zone
- Cost per day/month
- Coordination decisions vs energy used
- Outdoor temp vs energy consumption

#### Use Cases
- Identify excessive cycling
- Compare before/after coordination changes
- Optimize thresholds based on actual costs
- Generate monthly reports

### Log Coordination Decisions
**Add to temp_coordination.py**:
```python
# Log every coordination decision
log_entry = {
    'timestamp': datetime.now(),
    'nest_target': nest_target,
    'nest_hvac_status': hvac_status,
    'upstairs_temp': upstairs_temp,
    'master_suite_temp': master_suite_temp,
    'action': 'turned_on_cooling',  # or 'no_action', 'conflict_prevented'
    'reason': 'master_suite 3F above target'
}
```

**Analysis**:
- How often does coordination take action?
- Most common scenarios?
- How effective is conflict prevention?
- Opportunities for optimization?

## Weather-Based Adjustments

### Pre-Cooling Before Hot Afternoons
**Scenario**: Hot summer day, house will heat up in afternoon

**Strategy**:
- Check weather forecast in morning
- If forecast > 90°F: Pre-cool house to 70°F at 2 PM
- House drifts up to 74°F by evening (within tolerance)
- Less energy than trying to cool from 78°F at 5 PM

**Implementation**:
```python
forecast = get_weather_forecast(hours=6)
afternoon_high = max(f['temp'] for f in forecast)

if afternoon_high > 90 and current_hour < 14:  # Before 2 PM
    # Pre-cool more aggressively
    target_offset = -2
```

### Wider Tolerance on Mild Days
**Concept**: Don't need tight coordination when it's 70°F outside

**Logic**:
```python
outdoor_temp = get_weather()['temp_f']

if 65 <= outdoor_temp <= 75:
    # Mild weather, use wider tolerance
    zone_threshold = 4  # Instead of 2°F
else:
    zone_threshold = 2
```

**Benefit**: Less mini-split cycling, energy savings

### Humidity-Based Cooling
**Problem**: Hot humid days feel worse than hot dry days

**Enhancement**: Factor in humidity when deciding to cool
```python
indoor_humidity = nest_status['current_humidity']
outdoor_humidity = get_weather()['humidity']

# Adjust effective temperature based on humidity
feels_like_temp = calculate_heat_index(temp, humidity)

if feels_like_temp > nest_target + 3:
    # More aggressive cooling on humid days
    sensibo.turn_on(mode='cool')
```

## Nest Eco Mode Integration

### Coordinate with Nest Away Mode
**Current**: Mini-split turns off when nobody home, Nest runs normally

**Enhancement**: Check if Nest is in Eco mode
```python
nest_eco_mode = nest_status.get('eco_mode')  # Check API

if nest_eco_mode:
    # Nest already in energy-saving mode
    # Match mini-split to Nest's eco temp
    master_suite_target = nest_status['eco_temp_f']
```

**Benefit**: Consistent energy-saving behavior across all zones

## Multi-Device Presence Refinement

### Track Kate's Phone Too
**Current**: Only track user's iPhone

**Enhancement**:
```python
matt_home = is_device_home('192.168.50.189')
kate_home = is_device_home('192.168.50.XXX')  # Kate's iPhone IP

anyone_home = matt_home or kate_home

if not anyone_home:
    sensibo.turn_off()
```

### First/Last Person Logic
**More sophisticated**:
```python
if kate_home and not matt_home:
    # Only Kate home, maybe different preferences
    master_suite_target = kate_preferred_temp
elif matt_home and not kate_home:
    # Only Matt home
    master_suite_target = matt_preferred_temp
else:
    # Both home or both away
    master_suite_target = nest_target
```

## Fan Circulation

### Use Nest Fan for Evening Out Temps
**Problem**: Upstairs and Master Suite can have large delta even within 2°F tolerance

**Solution**: Run Nest fan to circulate air
```python
upstairs_temp = 72
master_suite_temp = 70
delta = abs(upstairs_temp - master_suite_temp)

if delta >= 2 and delta < 3:
    # Within tolerance but significant delta
    # Run fan to even out temps instead of mini-split
    nest.set_fan(duration_seconds=900)  # 15 minutes
```

**Benefit**:
- Fan uses less energy than mini-split
- May avoid mini-split cycling
- More even comfort throughout house

## Predictive Pre-Conditioning

### Learn Daily Patterns
**Concept**: Learn when user typically arrives home, pre-condition in advance

**Example**:
- User arrives home 6:00 PM ± 15 min on weekdays
- System automatically starts pre-conditioning at 5:30 PM
- No geofencing needed for predictable patterns

**Implementation**: Track arrival times over 2-4 weeks, identify patterns

**Fallback**: If user doesn't arrive by expected time + 30 min, turn off

## Priority Ranking

Based on impact vs effort:

### High Impact, Low Effort
1. **Seasonal logic (mode-based)** - Skip coordination when Nest OFF
2. **Nest Eco mode integration** - Match energy-saving behavior
3. **Logging coordination decisions** - Data for future optimization

### Medium Impact, Medium Effort
4. **Time-based Master Suite offset** - Cooler bedroom at night
5. **Weather-based tolerance** - Wider tolerance on mild days
6. **Multi-device presence** - Track Kate's phone too

### High Impact, High Effort
7. **Energy monitoring** - Requires hardware, data analysis
8. **Predictive pre-conditioning** - Requires learning algorithm
9. **Humidity-based cooling** - Complex feel-like calculations

### Low Priority
10. **Pre-cooling before hot afternoons** - Marginal benefit
11. **Fan circulation** - May not work well with zoned HVAC

## Recommendation

Focus on HVAC Coordination Phase 1 & 2 first. Once stable, revisit this list and pick 1-2 high-impact enhancements.

Don't optimize prematurely - need real usage data to know what's worth the effort.

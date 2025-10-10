# Per-Zone Presence Detection

Future enhancement for more granular HVAC control

## Concept

Instead of whole-house presence (WiFi-based), detect occupancy in individual zones:
- **Upstairs** (Nest zone)
- **Master Suite** (Sensibo zone)

Only condition occupied zones, save energy on unoccupied zones.

## Technology Options

### Option 1: Motion Sensors (Recommended)
**Hardware**: Zigbee/Z-Wave motion sensors
- Hue Motion Sensor (~$40)
- Aqara Motion Sensor (~$20)
- SmartThings Motion Sensor (~$25)

**Pros**:
- Reliable detection
- Battery powered (6-12 months)
- No privacy concerns
- Low latency

**Cons**:
- Requires hub (Zigbee/Z-Wave)
- False negatives if sitting still
- Need multiple sensors per large zone

**Implementation**:
- Mount sensor in each zone
- Timeout: 2 hours (zone considered "unoccupied" after 2hr of no motion)
- Override: Manual thermostat changes = treat zone as occupied

### Option 2: Smart Thermostats with Occupancy
**Hardware**: Nest/Ecobee already have occupancy sensors

**Pros**:
- No additional hardware
- Already integrated

**Cons**:
- Only works for Nest zone (upstairs)
- Sensibo doesn't have motion sensor
- May need additional sensors for large zones

### Option 3: Smart Outlets with Power Monitoring
**Hardware**: Tapo smart outlets (already have some)

**Concept**: Detect occupancy by device usage
- Bedroom lamp on = Master Suite occupied
- TV on = Living room occupied

**Pros**:
- Already have hardware
- No additional cost
- Reliable for certain use cases

**Cons**:
- Indirect measurement
- Doesn't work for all scenarios (reading in dark room)
- Requires mapping devices to zones

### Option 4: Bluetooth Beacons
**Hardware**: BLE beacons, track phone location within house

**Pros**:
- Precise location tracking
- Can distinguish between rooms

**Cons**:
- Battery drain on phone
- Privacy concerns
- Complex setup
- Requires phone to always have Bluetooth on

## Use Cases

### Scenario 1: Working from Home
**Pattern**: Upstairs occupied during day, Master Suite unoccupied
**Benefit**: Don't heat/cool Master Suite during work hours
**Savings**: ~30-40% mini-split energy (assume 8hr workday)

### Scenario 2: Sleeping
**Pattern**: Master Suite occupied at night, upstairs may be unoccupied
**Current behavior**: Nest heats whole house to sleep temp (68°F)
**Improved behavior**:
- Heat Master Suite to 68°F (mini-split)
- Allow upstairs to drop to 65°F (save furnace energy)
- Requires Nest setback coordination

### Scenario 3: Watching TV Upstairs
**Pattern**: Upstairs occupied, Master Suite unoccupied
**Benefit**: Turn off mini-split even if home WiFi connected
**Savings**: Don't condition empty bedroom

### Scenario 4: Nobody Home
**Current**: Already handled by whole-house presence (WiFi)
**No change needed**

## State Tracking

### Zone Occupancy States
```python
zone_state = {
    'upstairs': {
        'occupied': True/False,
        'last_motion': datetime,
        'timeout': timedelta(hours=2)
    },
    'master_suite': {
        'occupied': True/False,
        'last_motion': datetime,
        'timeout': timedelta(hours=2)
    }
}
```

### Override Conditions
**Treat zone as occupied even without motion**:
1. Manual thermostat adjustment (user touched Nest/Sensibo)
2. Recent automation trigger (good_morning, goodnight, im_home)
3. First 30 min after arriving home
4. Whole-house "away" mode OFF

## Integration with HVAC Coordination

### Current Logic
```python
if not is_home:  # Whole-house WiFi presence
    sensibo.turn_off()
```

### New Logic
```python
if not is_home:  # Whole-house presence
    sensibo.turn_off()
    # Nest has its own away mode
elif not zone_occupied('master_suite'):  # Per-zone occupancy
    sensibo.turn_off()
    # But keep Nest running (upstairs may be occupied)
else:
    # Normal coordination (maintain 2°F tolerance)
```

## Hardware Requirements

### Minimum Setup
- **1x Motion sensor**: Master Suite
- **Cost**: ~$20-40
- **Benefit**: Prevent cooling/heating empty bedroom

### Full Setup
- **2x Motion sensors**: Master Suite, Upstairs
- **1x Zigbee hub**: If using Zigbee sensors
- **Cost**: ~$60-100
- **Benefit**: Full per-zone control

### Already Have
- Nest thermostat (may have occupancy feature)
- Tapo smart outlets (power monitoring alternative)
- WiFi (whole-house presence working)

## Implementation Steps

### Phase 1: Research
- [ ] Check if Nest has occupancy API
- [ ] Research Zigbee sensor options (Hue, Aqara, SmartThings)
- [ ] Check if Tapo outlets support power monitoring API
- [ ] Determine if need Zigbee hub

### Phase 2: Prototype
- [ ] Purchase 1x motion sensor for Master Suite
- [ ] Add component for motion sensor API integration
- [ ] Track occupancy state (in-memory or file)
- [ ] Test occupancy detection accuracy
- [ ] Measure false positive/negative rates

### Phase 3: Integration
- [ ] Update temp_coordination.py with per-zone logic
- [ ] Add config for occupancy timeout
- [ ] Add override conditions (manual adjustments)
- [ ] Test with real usage patterns

### Phase 4: Expansion (Optional)
- [ ] Add upstairs motion sensor
- [ ] Add per-zone occupancy to other automations
- [ ] Create occupancy dashboard/monitoring

## Energy Savings Estimate

### Assumptions
- Master Suite empty 6 hours/day on average
- Mini-split uses 1kW when running
- Runs 30% of time when conditioning (cycling on/off)
- Energy cost: $0.12/kWh

### Calculation
- Hours saved: 6 hr/day × 30% duty cycle = 1.8 hr/day
- Energy saved: 1.8 hr × 1 kW = 1.8 kWh/day
- Cost saved: 1.8 kWh × $0.12 = $0.22/day
- **Annual savings**: $0.22 × 365 = ~$80/year

### ROI
- Hardware cost: ~$40 (1 sensor)
- Payback period: ~6 months
- 5-year savings: ~$400

**Note**: Savings depend heavily on usage patterns. Working from home = higher savings.

## Alternative: Schedule-Based (Simpler)

Instead of motion sensors, use time-based rules:
```yaml
master_suite:
  occupied_hours:
    - start: "22:00"  # 10 PM
      end: "08:00"    # 8 AM
      days: [0,1,2,3,4]  # Mon-Fri
    - start: "20:00"  # 8 PM
      end: "10:00"    # 10 AM
      days: [5,6]  # Sat-Sun
```

**Pros**:
- No hardware needed
- Simple implementation
- Predictable behavior

**Cons**:
- Inflexible (doesn't adapt to schedule changes)
- Less accurate
- Wastes energy on exceptions (work from home, sick day, vacation)

## Recommendation

**Start simple**: Wait until HVAC coordination Phase 1 is stable and working well.

**Then evaluate**: Monitor logs to see how often mini-split runs when Master Suite is empty.

**If significant waste**: Implement per-zone detection starting with 1 motion sensor in Master Suite.

**Don't over-engineer**: Schedule-based may be good enough if patterns are consistent.

# Geofencing Scenarios

Related: See `GEOFENCING_PLAN.md` for implementation details

## Use Cases

### 1. Leaving Work
**Trigger**: Exit work geofence
**Actions**:
- Start pre-conditioning home (Nest + Master Suite)
- Calculate ETA based on distance/traffic
- Send notification: "Left work, ETA 25 min. Pre-heating to 72°F"

**Integration with HVAC**:
- Set `preparing_for_arrival = True` flag
- Bypass "nobody home" presence check in temp coordination
- Allow mini-split to run even though iPhone not on WiFi yet

### 2. Arriving Near Home
**Trigger**: Enter "Near Home" geofence (~1 mile radius)
**Actions**:
- Refine ETA to 5-10 minutes
- Verify home conditioning is active
- Send notification: "5 min away, home is 68°F and warming"

**Edge case - Driving past home**:
- If exit "Near Home" without entering "Home" geofence
- Wait 30 min, then timeout and turn off conditioning
- Send notification: "Changed plans? Turned off heating"

### 3. Arriving Home
**Trigger**: Enter "Home" geofence (~150m radius)
**Actions**:
- Clear `preparing_for_arrival` flag
- Switch to normal presence-based control
- Run "im_home" automation (Nest to comfort temp, check lights, etc.)
- Send notification: "🏡 Arrived Home" with action summary

### 4. Leaving Home
**Trigger**: Exit "Home" geofence
**Actions**:
- Wait for confirmation (5 min delay to prevent false triggers)
- Run "leaving_home" automation (Nest to away temp, turn off mini-split, lights off)
- Send notification: "🚗 Left Home" with action summary

**Integration with presence**:
- Geofence exit is instant (no 2-min polling delay)
- More reliable than WiFi disconnect (iPhone may disconnect while still home)

### 5. Leaving Kate's House
**Trigger**: Exit Kate's location geofence
**Actions**:
- Similar to "Leaving Work" scenario
- Start pre-conditioning based on ETA
- Different notification: "Left Kate's, ETA 15 min"

## Didn't Come Home Scenario

### Problem
User leaves work, system starts pre-conditioning, but user goes somewhere else instead of home.

### Solution Options

#### Option A: Simple Timeout (Recommended)
- After entering "Near Home" geofence, start 30-min timeout
- If don't enter "Home" geofence within 30 min, assume plans changed
- Turn off all pre-conditioning
- Send notification: "Didn't arrive home, turned off heating/cooling"
- Clear `preparing_for_arrival` flag

#### Option B: Explicit "Cancel" Action
- Notification includes action button: "Cancel pre-heating"
- User can manually cancel from phone
- More control, but requires user action

#### Option C: Distance-Based Logic
- Monitor distance from home
- If distance starts increasing instead of decreasing, cancel pre-conditioning
- More complex, requires continuous location tracking (battery drain)

**Recommendation**: Use Option A (simple timeout). Simple, reliable, no extra battery drain.

## Geofence Definitions

### Work
- **Location**: User's workplace address
- **Radius**: 100-200m
- **Purpose**: Trigger pre-conditioning when leaving work

### Near Home
- **Location**: Home address
- **Radius**: ~1 mile (1600m)
- **Purpose**:
  - Refine ETA
  - Start timeout for "didn't come home" scenario
  - Provide arrival notification

### Home
- **Location**: Home address
- **Radius**: 150m (from config.yaml)
- **Purpose**:
  - Detect actual arrival
  - Switch from geofence to WiFi-based presence
  - Trigger "im_home" automation

### Kate's House (Optional)
- **Location**: Kate's address
- **Radius**: 100-200m
- **Purpose**: Similar to work geofence, trigger pre-conditioning when leaving

## State Machine

```
States:
- AT_WORK: At workplace
- COMMUTING_HOME: Left work, heading home (preparing_for_arrival=True)
- NEAR_HOME: Within 1 mile of home, refining ETA
- AT_HOME: WiFi connected, normal presence control
- AWAY: Not at any known location

Transitions:
AT_WORK → COMMUTING_HOME: Exit work geofence
COMMUTING_HOME → NEAR_HOME: Enter "Near Home" geofence
NEAR_HOME → AT_HOME: Enter "Home" geofence + WiFi connected
AT_HOME → AWAY: Exit "Home" geofence (5 min delay)
COMMUTING_HOME → AWAY: Timeout (30 min, didn't arrive home)
NEAR_HOME → AWAY: Timeout (30 min) OR exit "Near Home" without entering "Home"
```

## Privacy Considerations

- **Minimal tracking**: Only track geofence enter/exit events, not continuous location
- **Local storage**: Location state stored on home server, not cloud
- **Battery efficient**: iOS geofencing uses ~2-3% battery per day
- **No history**: Don't log location history, only current state

## Future Enhancements

### Multiple Occupants
- Track both user's iPhone and Kate's phone
- Pre-condition when either person heading home
- More complex: Only pre-condition if first person arriving (house currently empty)

### Time-of-Day Logic
- Different pre-conditioning based on time
- Morning: Less aggressive (house may still be warm)
- Evening: More aggressive (house cooled down all day)
- Night: Minimal (going to bed soon anyway)

### Weather-Based Adjustments
- Hot day: Start cooling earlier (house heats up during day)
- Cold day: Start heating earlier (house cools down)
- Mild day: Skip pre-conditioning (waste of energy)

### Learning ETA
- Track typical commute times
- Adjust pre-conditioning start time based on historical data
- Example: Friday traffic is worse, start earlier

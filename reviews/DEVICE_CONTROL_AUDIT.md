# Device Control Sources Audit

Comprehensive list of all systems that can control smart home devices, for cleanup and migration to py_home.

---

## Current Device Inventory

### Smart Outlets (Tapo TP-Link)
- **Heater** (192.168.50.135)
- **Bedroom Right Lamp** (192.168.50.143)
- **Livingroom Lamp** (192.168.50.162)
- **Bedroom Left Lamp** (192.168.50.93)

### Climate Control
- **Nest Thermostat** - Living room
- **Sensibo AC** - Bedroom (matt's device)

### Other Devices
- Roborock vacuum (credentials in config but not active)
- Alen air purifiers (Tuya - credentials empty)

---

## Control Source 1: HomeKit (Apple Home)

**Status:** UNKNOWN - Need to audit

**Potential Automations:**
- [ ] Time-based scenes (morning, night)
- [ ] Location-based automations (arrive/leave home)
- [ ] Accessory triggers (motion sensors, etc.)
- [ ] Manual scenes/shortcuts

**Devices Likely Added:**
- Tapo outlets (if using HomeKit bridge/plugin)
- Possibly Nest (via Google integration)
- Possibly Sensibo (native HomeKit support)

**Action Items:**
1. Open Apple Home app
2. Check "Automation" tab
3. List all automations
4. Check "Scenes" for manual controls
5. Document which devices are added

**Migration Strategy:**
- Disable/delete HomeKit automations
- Keep manual scenes if desired (complementary to py_home)
- Remove devices if causing conflicts

---

## Control Source 2: Google Home

**Status:** UNKNOWN - Need to audit

**Potential Routines:**
- [ ] Voice command routines
- [ ] Scheduled routines (morning, bedtime)
- [ ] Location-based routines
- [ ] Sunrise/sunset triggers

**Devices Likely Added:**
- Nest Thermostat (native Google integration)
- Tapo outlets (via Google Home integration)
- Sensibo AC (if integrated)

**Action Items:**
1. Open Google Home app
2. Check "Automations" section
3. List all routines
4. Check "Devices" for what's linked
5. Document voice commands configured

**Migration Strategy:**
- Keep voice commands if desired (can work alongside py_home)
- Delete duplicate automations
- Ensure no conflicts with py_home schedules

---

## Control Source 3: n8n on Raspberry Pi

**Status:** ACTIVE - Migrating from

**Known Workflows (from project history):**
- Previously had automation workflows
- This is what we're replacing with py_home
- Location: `/home/pi/n8n` (assumed)

**Action Items:**
1. SSH to Raspberry Pi
2. Check n8n workflows: `http://raspberrypi.local:5678`
3. Export all workflows for documentation
4. List all active automations
5. Map to py_home equivalents

**Migration Strategy:**
- **Already in progress** - py_home is the replacement
- Document what n8n was doing
- Disable n8n workflows after py_home is running
- Keep n8n for other non-home-automation tasks (if any)

**Status on Pi:**
```bash
# Check if n8n is running
systemctl status n8n

# Check workflows
curl http://localhost:5678/api/v1/workflows
```

---

## Control Source 4: Tapo Native App (TP-Link/Kasa)

**Status:** LIKELY ACTIVE - Need to verify

**App:** TP-Link Tapo or Kasa app on phone

**Potential Automations:**
- [ ] Schedules (turn on/off at specific times)
- [ ] Smart Actions (if this, then that)
- [ ] Timers
- [ ] Away mode

**Action Items:**
1. Open Tapo app
2. Check each outlet's schedule
3. Check "Smart Actions" section
4. List all automations

**Migration Strategy:**
- Delete ALL schedules/automations in Tapo app
- Use py_home for all automation
- Keep app for manual control only

**Cleanup Commands:**
```python
# Can check current outlet schedules via Tapo API if needed
from components.tapo import get_outlet_info
info = get_outlet_info("192.168.50.135")
# Check info['schedules']
```

---

## Control Source 5: Nest App (Google Nest)

**Status:** LIKELY ACTIVE - Need to verify

**App:** Google Nest app

**Potential Automations:**
- [ ] Temperature schedules (home/away/sleep)
- [ ] Eco mode settings
- [ ] Auto-away detection
- [ ] Home/Away Assist

**Action Items:**
1. Open Google Nest app
2. Check thermostat schedule
3. Check Home/Away Assist settings
4. List eco temperatures

**Current Config (from py_home):**
```yaml
nest:
  away_temp: 62
  sleep_temp: 68
  comfort_temp: 72
```

**Migration Strategy:**
- **Keep basic schedules** in Nest app (fallback)
- Use py_home for smart arrival/departure
- Disable Home/Away Assist (conflicts with py_home geofencing)
- Keep Eco mode for safety

---

## Control Source 6: Sensibo App

**Status:** LIKELY ACTIVE - Need to verify

**App:** Sensibo app

**Potential Automations:**
- [ ] Climate React (auto temp adjustment)
- [ ] Schedules (timer on/off)
- [ ] Geofencing (location-based)
- [ ] Temperature-based triggers

**Action Items:**
1. Open Sensibo app
2. Check "Climate React" settings
3. Check "Schedules"
4. Check "Geofencing" (disable if active!)
5. List all automations

**Migration Strategy:**
- **Disable geofencing** in Sensibo (conflicts with py_home)
- Delete all schedules
- Disable Climate React (py_home will handle)
- Keep app for manual control only

---

## Control Source 7: IFTTT (If This Then That)

**Status:** UNKNOWN - Likely inactive

**Potential Integrations:**
- [ ] Location-based triggers (phone location)
- [ ] Time-based applets
- [ ] Weather-based triggers
- [ ] Voice assistant integrations

**Action Items:**
1. Check IFTTT account (if exists)
2. List all applets
3. Identify home automation applets

**Migration Strategy:**
- Delete all home automation applets
- Keep non-home applets if desired

---

## Control Source 8: iOS Shortcuts (Current/Manual)

**Status:** ACTIVE - Migrating to py_home

**Current Shortcuts:**
- Manual voice commands (leaving home, goodnight, etc.)
- **Being replaced** with py_home Flask endpoints

**Migration Strategy:**
- **Already in progress** - documented in `IOS_SHORTCUTS_GUIDE.md`
- Replace manual shortcuts with Flask API calls
- Add geofencing automations (new capability)

---

## Control Source 9: SmartThings / Samsung Home

**Status:** UNKNOWN - Likely inactive

**Action Items:**
- Check if SmartThings hub exists
- Check if any devices linked

**Migration Strategy:**
- Remove all devices if found
- Disable hub

---

## Control Source 10: Alexa Routines

**Status:** UNKNOWN - Likely inactive

**Potential Automations:**
- [ ] Voice command routines
- [ ] Scheduled routines
- [ ] Smart home groups

**Action Items:**
1. Check Amazon Alexa app (if installed)
2. List all routines
3. Check linked devices

**Migration Strategy:**
- Delete all home automation routines
- Keep non-home Alexa features if desired

---

## Audit Checklist

### Phase 1: Discovery (Do Now)
- [ ] Check HomeKit automations in Apple Home app
- [ ] Check Google Home routines
- [ ] Check n8n workflows on Pi (SSH required)
- [ ] Check Tapo app schedules
- [ ] Check Nest app schedule
- [ ] Check Sensibo app automations (especially geofencing!)
- [ ] Check IFTTT applets
- [ ] Check for SmartThings
- [ ] Check Alexa routines

### Phase 2: Documentation
- [ ] List all found automations
- [ ] Map to py_home equivalents
- [ ] Identify conflicts (duplicate automations)
- [ ] Identify gaps (automations not in py_home)

### Phase 3: Cleanup
- [ ] Disable/delete HomeKit automations
- [ ] Disable/delete Google Home routines
- [ ] Stop n8n workflows (after py_home deployed)
- [ ] Delete Tapo schedules
- [ ] Disable Nest Home/Away Assist
- [ ] Disable Sensibo geofencing/schedules
- [ ] Delete IFTTT applets
- [ ] Remove SmartThings devices
- [ ] Delete Alexa routines

### Phase 4: Verification
- [ ] Test that only py_home controls devices
- [ ] Monitor for unexpected changes (indicates missed source)
- [ ] Document final state

---

## Migration Priority

**High Priority (Do First):**
1. **Sensibo geofencing** - Will conflict with py_home geofencing
2. **Google Home/HomeKit location routines** - Will conflict with py_home
3. **n8n workflows** - Direct replacement

**Medium Priority:**
4. Tapo schedules - May cause unexpected behavior
5. Nest Home/Away Assist - May conflict with py_home

**Low Priority:**
6. Manual shortcuts (already migrating)
7. Voice commands (can coexist)
8. IFTTT (likely inactive)

---

## Conflict Detection

**Signs of conflicting automations:**
- Devices turning on/off unexpectedly
- Temperature changes without py_home logs
- Lights turning on when arriving home BEFORE py_home triggers
- Multiple arrival automations firing

**How to diagnose:**
1. Check py_home logs: `journalctl -u py_home -f`
2. Check device state changes in native apps
3. Cross-reference with py_home automation times
4. Look for state changes that don't match py_home logic

---

## Post-Cleanup State

**Goal:** Single source of truth = py_home

**Allowed controls:**
- ✅ py_home automations (only source)
- ✅ Manual controls (apps, voice, switches)
- ✅ Voice commands that call py_home API
- ❌ Duplicate automations
- ❌ Location-based automations (except py_home)
- ❌ Schedules in native apps

**Exception:** Keep basic Nest schedule as failsafe (manual backup).

---

## Next Steps

1. **Start audit** - Go through each source above
2. **Document findings** - Add notes to this file
3. **Create cleanup plan** - Based on what's found
4. **Execute cleanup** - Systematically disable old automations
5. **Deploy py_home** - Once cleanup complete
6. **Monitor** - Ensure no conflicts after deployment

**Start with:** Check Sensibo app for geofencing (highest conflict risk)

# Notification Coverage Analysis

## SUPERFLUOUS NOTIFICATIONS

### 1. Presence Monitor (presence_monitor.py)
**Current:**
- "🏡 Home (WiFi)" - LOW priority
- "🚗 Left (WiFi)" - LOW priority

**Issue:** Duplicates iOS location-based automations
- iOS already triggers /im-home and /leaving-home
- WiFi presence is a BACKUP, not primary

**Recommendation:**
- ✗ Remove these notifications (redundant)
- OR keep but only notify on DISAGREEMENT:
  - ✓ "⚠️ WiFi disagrees with iOS location"

### 2. Temperature Coordination (temp_coordination.py)
**Current:**
- "🌡️ AC on (78°F)" - NORMAL priority
- "🌡️ AC off (72°F)" - LOW priority

**Question:** Do you want to know every time AC turns on/off?
- Runs every 15 minutes
- Could be spammy in summer

**Recommendation:**
- ✗ Remove AC off notification (too frequent)
- ✓ Keep AC on (useful to know when it kicks in)
- OR add rate limiting (max 1 per hour)

### 3. Task Router (task_router.py)
**Current:**
- "✓ Added: Buy milk" - LOW priority

**Question:** Do you need confirmation?
- You just said the task via Siri
- You know it was captured

**Recommendation:**
- ✓ Keep it - good feedback that voice command worked
- LOW priority is appropriate

---

## MISSING NOTIFICATIONS

### 1. Air Quality (Tuya/Alen purifiers) ⭐ HIGH VALUE
**Missing:**
- "🔴 Air quality unhealthy: PM2.5 150 (Bedroom)"
- "⚠️ Air quality moderate: PM2.5 45 (Living Room)"

**Recommendation:** Add monitoring automation like tempstick
- Check PM2.5 every 30 minutes
- Alert if > 100 (unhealthy)
- Alert if > 50 (moderate, for sensitive groups)

### 2. Nest Thermostat
**Missing:**
- Temperature set failures
- Thermostat offline
- Unexpected mode changes

**Recommendation:** Add health check
- "⚠️ Nest offline"
- "❌ Failed to set temperature"

**BUT:** Already handled by automation errors
- goodnight/leaving_home report errors
- May be sufficient

### 3. Sensibo AC
**Missing:**
- AC failures (won't turn on)
- Filter needs cleaning
- Device offline

**Recommendation:** Add health check
- "⚠️ Sensibo offline"
- "🔧 AC filter needs cleaning"

**BUT:** temp_coordination already handles failures
- Logs errors when can't control AC
- Just doesn't notify about them

### 4. Tapo Smart Plugs
**Missing:**
- Device offline
- Unexpected state changes
- Power monitoring (if devices support it)

**Recommendation:** Low priority
- Plugs are simple, rarely fail
- Automations will log errors
- Only notify if critical device (heater in winter?)

### 5. General System Health
**Missing:**
- Daily summary: "All systems normal"
- Weekly battery report: "Temp Stick: 85%, replace in ~2mo"
- Internet connectivity issues
- Raspberry Pi disk space low
- Python automation failures/crashes

**Recommendation:** Add system health monitor
- Daily digest (email, not push)
- "✓ All sensors reporting, 0 errors today"
- Useful for peace of mind

---

## PRIORITY RECOMMENDATIONS

### REMOVE:
1. ✗ WiFi presence notifications (redundant with iOS)
2. ✗ AC off notifications (too frequent)

### ADD (HIGH VALUE):
1. ⭐ Air quality monitoring (you have the sensors!)
   - PM2.5 > 100 = HIGH priority alert
   - PM2.5 > 50 = NORMAL priority alert

2. ⭐ Device offline alerts for critical components
   - Nest offline = problem
   - Sensibo offline = less critical (backup HVAC)

3. Daily summary (email or LOW priority)
   - "✓ All systems normal: 71°F, 48% humidity, PM2.5: 12"
   - Only if you want peace of mind

### ADD (NICE TO HAVE):
4. Filter cleaning reminders
   - Alen purifiers need filter changes
   - "🔧 Bedroom purifier: Filter 90% used"

5. System health dashboard
   - Not notifications, but web page
   - View all sensors at a glance

---

## DECISIONS MADE:

1. ✓ Keep WiFi presence notifications (useful backup)
2. ✅ Removed AC on/off notifications (too frequent, automatic)
3. ✅ Added air quality monitoring (HIGH VALUE)
4. ✗ No daily summary (not needed)

## IMPLEMENTED:

### ✅ Air Quality Monitor (automations/air_quality_monitor.py)
**New notifications:**
- 🔴 HIGH: "🔴 Air unhealthy: PM2.5 150 (Bedroom)" - PM2.5 > 100
- ⚠️ NORMAL: "⚠️ Air moderate: PM2.5 55 (Living Room)" - PM2.5 > 50
- ⚠️ NORMAL: "⚠️ Air purifier offline (Bedroom)" - Device error

**Schedule:** Every 30 minutes via cron
```bash
*/30 * * * * cd /home/pi/py_home && python automations/air_quality_monitor.py
```

### ✅ Removed Temperature Coordination Notifications
- No longer notifies when AC turns on/off
- Still logs all actions
- Errors are still logged (but not notified unless critical)

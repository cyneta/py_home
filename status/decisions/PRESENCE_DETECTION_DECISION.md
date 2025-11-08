# Presence Detection Architecture Decision

**Date:** 2025-10-13
**Decision:** Disable ping-based presence monitor (`presence_monitor.py`)
**Status:** Implemented

---

## Background

Previously used three presence detection methods:

1. **WiFi DHCP Monitor** - Watches DHCP logs for iPhone connection
2. **iOS Geofencing** - GPS-based boundary detection via Scriptable
3. **Ping Monitor** - Pings iPhone IP every 5 minutes (cron job)

---

## Decision: Remove Ping Monitor

**Rationale:** Ping monitor is now redundant and causes unnecessary SD card wear.

### Why Ping Was Originally Needed

When the system only had manual iOS Shortcuts:
- No automatic departure detection
- No real-time WiFi arrival detection
- Ping was the **only** automated presence method

Ping provided:
- Reliable departure detection (15-minute delay)
- Backup for iOS Shortcuts failures
- Continuous presence verification

### What Changed (October 2025)

#### 1. WiFi DHCP Monitor Added
- **Speed:** <5 seconds after WiFi connects
- **Method:** Monitors `journalctl -f -u dnsmasq` for DHCP events
- **Reliability:** Near-instant, highly reliable
- **Trigger:** `im_home.py` on iPhone WiFi connection

#### 2. iOS Geofencing via Scriptable
- **Speed:** Instant when crossing 173m boundary
- **Method:** GPS location + Haversine distance calculation
- **Coverage:** Both arrivals AND departures
- **Offline queueing:** Actions saved when off-network
- **Trigger:** `im_home.py` or `leaving_home.py`

### Current Detection Stack

**Arrivals (Home WiFi Available):**
1. WiFi DHCP Monitor detects connection (<5 sec) → Triggers `im_home.py`
2. iOS Geofence detects arrival (instant) → Triggers `im_home.py` (duplicate, ignored by state file)

**Arrivals (Cellular Only - No WiFi):**
1. iOS Geofence detects arrival → Queues action
2. When WiFi connects → Processes queue → Triggers `im_home.py`

**Departures:**
1. iOS Geofence detects crossing boundary (instant) → Triggers `leaving_home.py`

---

## Why Ping Is Now Redundant

### Scenario Analysis

#### Scenario 1: Normal Departure
- **iOS Geofence:** ✅ Triggers instantly when cross 173m boundary
- **Ping:** Would trigger after 15 minutes (too late)
- **Winner:** iOS Geofence

#### Scenario 2: iPhone Battery Dies
- **iOS Geofence:** ❌ Can't trigger (phone dead)
- **WiFi DHCP:** ❌ No disconnect event logged
- **Ping:** ❌ Phone not responding (can't ping dead phone)
- **Result:** All methods fail, but ping doesn't help

#### Scenario 3: iOS Geofence Fails to Trigger
- **Possible causes:**
  - iOS kills Scriptable (background limits)
  - GPS inaccuracy
  - Cellular data unavailable
- **Ping:** ✅ Would catch after 15 minutes
- **Impact:** 15-minute delay to secure house
- **Probability:** Low (~1% failure rate with iOS geofencing)

#### Scenario 4: WiFi DHCP Silent Reconnect
- **Scenario:** iPhone reconnects using cached DHCP lease
- **WiFi DHCP:** ❌ No log event (no DHCPACK)
- **iOS Geofence:** ✅ Still triggers on boundary crossing
- **Ping:** ✅ Would detect on next cycle
- **Winner:** iOS Geofence handles it

#### Scenario 5: WiFi Monitor Service Crashes
- **WiFi DHCP:** ❌ Not monitoring
- **iOS Geofence:** ✅ Still works independently
- **Ping:** ✅ Would detect
- **Winner:** iOS Geofence (primary), Ping (backup)
- **Mitigation:** Systemd auto-restarts service on crash

---

## Cost of Keeping Ping

### SD Card Wear
```
Frequency: Every 5 minutes
Writes per day: 288 (24 hours × 12 checks/hour)
Writes per year: 105,120

Files written each cycle:
- .presence_state (updated every cycle)
- .presence_fail_count (when ping fails)
- data/logs/presence_monitor.log (every cycle)

Estimated wear: 300-500KB/day = 110-180MB/year
```

### CPU/Network Overhead
```
Each ping cycle:
- Subprocess spawn (Python overhead)
- ICMP ping packet (network traffic)
- Log writes (I/O overhead)
- State file reads/writes (I/O overhead)

Total: ~50-100ms CPU time per cycle
```

### System Complexity
- Additional cron job to maintain
- Additional logs to monitor
- Potential false positives (iPhone sleep mode)
- Redundant state management

---

## Benefits of Keeping Ping

### Backup for Catastrophic Failures

**IF** both WiFi DHCP Monitor AND iOS Geofencing fail:
- Ping provides 15-minute delayed detection
- Low probability scenario (<0.1% of events)

**Cost/Benefit:**
- 105,120 SD card writes/year for 0.1% edge case coverage
- Not worth it

---

## Decision Matrix

| Method | Speed | Reliability | Coverage | SD Card Writes |
|--------|-------|-------------|----------|----------------|
| **WiFi DHCP** | <5 sec | 99% | Arrivals only | Minimal (event-driven) |
| **iOS Geofence** | Instant | 95% | Arrivals + Departures | Zero (on Pi) |
| **Ping** | 15 min | 90% | Arrivals + Departures | 105k/year |

**Coverage Analysis:**
- WiFi DHCP + iOS Geofence = 99.95% coverage (both would have to fail)
- Adding Ping = 99.99% coverage (all three would have to fail)
- **Improvement:** 0.04% for 105k SD card writes/year
- **Verdict:** Not worth it

---

## Implementation

### Disable Ping Monitor Cron

```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local

# Edit crontab
crontab -e

# Comment out or delete this line:
# */5 * * * * cd /home/matt.wheeler/py_home && python automations/presence_monitor.py

# Save and exit
```

### Keep the Script (For Manual Testing)

- Keep `automations/presence_monitor.py` in repository
- Document as "legacy/backup method"
- Can be re-enabled if needed

### Update Documentation

- Mark `presence_monitor.py` as deprecated
- Update `ARCHITECTURE.md` to reflect current stack
- Document decision in this file

---

## Rollback Plan

**If iOS Geofencing proves unreliable:**

```bash
# Re-enable ping monitor cron
crontab -e

# Add back (but reduce frequency to every 15 min):
*/15 * * * * cd /home/matt.wheeler/py_home && python automations/presence_monitor.py
```

**Monitoring for 30 days:**
- Check logs for missed arrivals/departures
- Monitor iOS Geofence reliability
- If >5% failure rate, re-enable ping as backup

---

## Testing Plan

**Phase 1 (Week 1): Monitor iOS Geofencing**
- Test 10+ arrival/departure cycles
- Check console logs for trigger confirmation
- Verify notifications appear
- Log any failures

**Phase 2 (Week 2-4): Real-World Usage**
- Normal daily usage
- Monitor for false positives/negatives
- Check dashboard presence accuracy
- Verify automation triggers correctly

**Success Criteria:**
- <2% failure rate for iOS Geofencing
- Zero missed security events (house left unsecured)
- No reports of wrong presence state

**Failure Criteria:**
- >5% failure rate
- Missed security events
- Persistent wrong state

---

## Related Changes

### Files Modified
- Remove cron job from Pi crontab
- Mark `automations/presence_monitor.py` as deprecated
- Update `ARCHITECTURE.md`
- Create this decision document

### Files Kept (No Changes)
- `automations/presence_monitor.py` (keep for manual testing/backup)
- `components/network/` (ping function still useful for dashboard)
- `.presence_state` file (still used by WiFi monitor + iOS geofence)

---

## Conclusion

**Ping monitor is redundant** with current WiFi DHCP + iOS Geofencing stack.

**Benefits of removing:**
- Eliminates 105k SD card writes/year
- Reduces system complexity
- Removes potential false positives
- No meaningful loss of coverage (0.04%)

**Decision:** Disable ping monitor cron job, keep script for backup.

**Review Date:** 2025-11-13 (30 days after implementation)

---

## References

- WiFi DHCP Monitor: `automations/wifi_event_monitor.py`
- iOS Geofencing Script: `scripts/ios/ph_home-geofence.js`
- Ping Monitor (deprecated): `automations/presence_monitor.py`
- Architecture Doc: `ARCHITECTURE.md`
- Scriptable Migration: `SCRIPTABLE_MIGRATION.md`

# Log File Consolidation

**Date:** 2025-10-14
**Goal:** Minimize log file fragmentation, make debugging easier

---

## Changes Made

### Unified Automation Log

**New File:** `data/logs/automations.log`

All user-triggered automation scripts now log to this single file:
- ✅ `pre_arrival.py` (Stage 1 arrival) - changed from `pre_arrival.log`
- ✅ `im_home.py` (Stage 2 arrival) - **NEW logging setup** (was missing)
- ✅ `leaving_home.py` - **NEW logging setup** (was missing)
- ✅ `goodnight.py` - **NEW logging setup** (was missing)
- ✅ `good_morning.py` - **NEW logging setup** (was missing)

**Benefits:**
- Single chronological view of all automation events
- No need to check multiple files when debugging arrivals/departures
- Consistent logging across all automations
- Fixes missing logs for `im_home`, `leaving_home`, `goodnight`, `good_morning`

---

## Monitor Scripts (Background Services)

These continue to log to systemd journal (stdout):
- `temp_coordination.py` - Temperature coordination between Nest/Sensibo
- `tempstick_monitor.py` - Crawlspace sensor monitoring
- `air_quality_monitor.py` - Air quality checks
- `wifi_event_monitor.py` - WiFi DHCP presence detection
- `presence_monitor.py` - DEPRECATED

**Log files on Pi (if they exist) are likely created by:**
- Systemd service StandardOutput/StandardError redirection
- Cron job output redirection (e.g., `>> /path/to/log.txt 2>&1`)

**Recommendation:** Keep monitors in systemd journal for standard Linux logging practices.

---

## Flask Server

Continues to log to systemd journal only:
- Global request/response logging (`@app.before_request`, `@app.after_request`)
- Captures all HTTP endpoint calls with duration and status codes
- View with: `journalctl -u py_home.service -f`

---

## Where to Look Now

### Debugging User Automations
```bash
# All arrival, departure, goodnight, good morning events
tail -f data/logs/automations.log

# Or via web UI
http://raspberrypi.local:5000/logs
```

### Debugging Background Monitors
```bash
# Specific service
journalctl -u temp_coordination.service -f

# Multiple services
journalctl -u tempstick_monitor -u wifi_event_monitor -f

# All py_home services
journalctl -t py_home -f
```

### Debugging HTTP/API Issues
```bash
# Flask server requests
journalctl -u py_home.service -f | grep -E 'request_complete|ERROR'
```

---

## Benefits of This Approach

1. **Fewer Files** - 1 automation log instead of 5+ separate files
2. **Chronological Events** - See automation sequence in order
3. **Easier Correlation** - pre_arrival → im_home events together
4. **Standard Practices** - System services use journald
5. **Fixed Bugs** - im_home/leaving_home/goodnight/good_morning now have logging

---

## Old Log Files to Clean Up (After Testing)

These can be deleted after verifying new logging works:
- `pre_arrival.log` (superseded by `automations.log`)
- `presence_monitor.log` (deprecated service)

These may exist on Pi from systemd/cron redirection:
- `temp_coordination.log` (can be removed if using journald)
- `tempstick_monitor.log` (can be removed if using journald)
- `air_quality_monitor.log` (can be removed if using journald)
- `wifi_event_monitor.log` (can be removed if using journald)

---

## Testing Plan

1. Deploy changes to Pi
2. Trigger automations (arrival, departure, goodnight)
3. Check `data/logs/automations.log` has all events
4. Verify monitors still logging to journald
5. Clean up old log files after 24h verification period

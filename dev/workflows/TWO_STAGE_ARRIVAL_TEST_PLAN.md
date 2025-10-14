# Two-Stage Arrival Test Plan

**Date Created:** 2025-10-13
**Status:** ✅ Deployed and Basic Testing Complete (2025-10-13)
**Prerequisites:** Must be on home network to access Pi

**Deployment Status:**
- ✅ Files deployed to Pi
- ✅ Flask restarted successfully
- ✅ `/pre-arrival` endpoint verified working
- ✅ `/im-home` endpoint verified working
- ⏳ Awaiting real-world arrival test

---

## Overview

This test plan validates the two-stage arrival system:
- **Stage 1 (Pre-Arrival):** iOS geofence crossing (~173m, ~60 sec before home) → HVAC + outdoor lights
- **Stage 2 (Physical Arrival):** WiFi connect → Indoor lights + notification

---

## Pre-Test Setup

### 1. Deploy Code to Pi

**Location:** Must be on home network (or via VPN once configured)

```bash
# From laptop (Windows Git Bash)
cd /c/git/cyneta/py_home

# Deploy modified files
scp automations/pre_arrival.py matt.wheeler@raspberrypi.local:~/py_home/automations/
scp automations/im_home.py matt.wheeler@raspberrypi.local:~/py_home/automations/
scp server/routes.py matt.wheeler@raspberrypi.local:~/py_home/server/

# Verify files copied
ssh matt.wheeler@raspberrypi.local "ls -la ~/py_home/automations/pre_arrival.py ~/py_home/automations/im_home.py"
```

**Expected Output:**
```
-rwxr-xr-x 1 matt.wheeler matt.wheeler [size] [date] pre_arrival.py
-rwxr-xr-x 1 matt.wheeler matt.wheeler [size] [date] im_home.py
```

---

### 2. Restart Flask Server

```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local

# Restart Flask to pick up new routes.py
sudo systemctl restart py_home

# Verify service is running
sudo systemctl status py_home

# Should show "active (running)" in green
```

**Expected Output:**
```
● py_home.service - py_home Flask Server
   Active: active (running) since [timestamp]
```

---

### 3. Verify Endpoint Exists

```bash
# Test /pre-arrival endpoint exists
curl -X POST http://raspberrypi.local:5000/pre-arrival

# Should return JSON response (not 404)
```

**Expected Output:**
```json
{
  "action": "pre_arrival",
  "stage": 1,
  "status": "success",
  "actions": ["Nest set to 70°F", ...],
  "duration_ms": 2500
}
```

**If 404 Error:**
- Check Flask restarted successfully
- Check routes.py deployed correctly
- Check Flask logs: `sudo journalctl -u py_home -n 50`

---

## Test 1: Manual Stage 1 (Pre-Arrival)

**Purpose:** Verify pre-arrival endpoint works and only runs Stage 1 actions

**Prerequisites:**
- On home network
- Automations enabled (check dashboard)
- Note current Nest temp before test

### Steps

```bash
# Check current state before test
curl http://raspberrypi.local:5000/api/nest/status
curl http://raspberrypi.local:5000/api/presence

# Trigger Stage 1
curl -X POST http://raspberrypi.local:5000/pre-arrival

# Check logs
ssh matt.wheeler@raspberrypi.local
tail -f ~/py_home/data/logs/pre_arrival.log
```

### Expected Results

**✅ PASS Criteria:**
1. Nest set to comfort temp (70°F)
2. If night mode active: Sensibo turned on to 66°F
3. If after 6pm: Living room lamp turned on (outdoor lights placeholder)
4. Presence state file updated to "home"
5. **NO notification sent** (this is correct - waits for Stage 2)
6. Log shows: `automation=pre_arrival event=complete stage=1`

**❌ FAIL Indicators:**
- 404 error (endpoint not found)
- Nest not changed
- Error in logs
- Notification sent (should not happen in Stage 1)

**Verify on Dashboard:**
- Visit http://raspberrypi.local:5000/dashboard
- Check Nest shows comfort temp
- Check Presence shows "HOME"

---

## Test 2: Manual Stage 2 (Physical Arrival)

**Purpose:** Verify im_home detects Stage 1 already ran and only runs Stage 2 actions

**Prerequisites:**
- Test 1 completed successfully
- Presence state = "home" (from Test 1)

### Steps

```bash
# Wait 10 seconds after Test 1

# Trigger Stage 2
curl -X POST http://raspberrypi.local:5000/im-home

# Check logs
tail -f ~/py_home/data/logs/im_home.log
```

### Expected Results

**✅ PASS Criteria:**
1. Living room lamp turned on
2. If after 6pm: Bedroom lamps turned on
3. Notification sent: "🏡 Welcome Home!" with action summary
4. Log shows: `automation=im_home event=start stage=2`
5. Log shows: `state=home` (detected Stage 1 already ran)
6. **Nest NOT touched** (already set in Stage 1)

**❌ FAIL Indicators:**
- Nest settings changed (should skip HVAC)
- No notification (Stage 2 should always notify)
- Error in logs

**Verify Notification:**
- Check iPhone for "Welcome Home!" notification
- Should list actions from both stages

---

## Test 3: WiFi-Only Arrival (Fallback)

**Purpose:** Verify im_home runs both stages if geofence didn't trigger

**Prerequisites:**
- Manually reset presence state to simulate geofence failure

### Steps

```bash
# Reset presence state (simulate geofence didn't trigger)
ssh matt.wheeler@raspberrypi.local
echo "away" > ~/py_home/.presence_state

# Verify state
cat ~/py_home/.presence_state
# Should show: away

# Trigger im_home (simulating WiFi-only arrival)
curl -X POST http://raspberrypi.local:5000/im-home

# Check logs
tail -f ~/py_home/data/logs/im_home.log
```

### Expected Results

**✅ PASS Criteria:**
1. Log shows: `event=fallback reason=pre_arrival_not_run state=away`
2. Stage 1 actions execute (Nest, outdoor lights)
3. Stage 2 actions execute (indoor lights, notification)
4. Notification includes actions from **both stages**
5. Log shows: `event=fallback_complete`

**❌ FAIL Indicators:**
- No fallback detected (should see `event=fallback` in logs)
- Only Stage 2 actions run (HVAC missed)
- Error during fallback

**Verify:**
- Nest changed to comfort temp
- All lights turned on
- Notification received with full action list

---

## Test 4: Real-World Two-Stage Arrival

**Purpose:** End-to-end test with actual geofence and WiFi triggers

**Prerequisites:**
- iOS automation configured for "Arrive" at home
- home-geofence.js deployed to iCloud Drive (already done)
- Currently away from home (>200m)

### Steps

**Stage 0: Departure**
```
1. Leave home (drive/walk >200m away)
2. Wait for "🚗 Left Home" notification from iOS
3. Verify leaving_home automation ran
4. Check dashboard shows "AWAY"
```

**Stage 1: Pre-Arrival (Geofence)**
```
5. Return home, approach within 173m boundary
6. iOS automation triggers home-geofence.js
7. Wait ~5 seconds
8. Check iPhone for Scriptable notification (if configured)
9. **NO "Welcome Home" notification yet** (correct behavior)
```

**Stage 2: Physical Arrival (WiFi)**
```
10. Continue to home, enter house
11. iPhone connects to home WiFi
12. Wait ~5 seconds
13. Check for "🏡 Welcome Home!" notification
14. Verify all lights on
15. Check dashboard shows "HOME"
```

### Expected Results

**✅ PASS Criteria:**

**Stage 1 (Geofence @ ~173m):**
- Time: ~60 seconds before entering house
- Nest starts heating/cooling to 70°F
- If after 6pm: Outdoor lights turn on
- Presence state updated to "home"
- NO notification yet

**Stage 2 (WiFi Connect @ ~5 sec):**
- Time: <5 seconds after WiFi connects
- Living room lamp turns on
- If after 6pm: Bedroom lamps turn on
- Notification: "🏡 Welcome Home!" with action summary
- Dashboard shows "HOME"

**Timing:**
- Total time from geofence to notification: ~60-65 seconds
- HVAC has ~60 second head start (optimal)
- Lights immediate feedback on entry

**❌ FAIL Indicators:**
- Both stages trigger simultaneously (geofence radius too large?)
- Lights turn on before arrival (security concern)
- No notification (Stage 2 didn't run)
- Duplicate notifications (both stages sent notification)

### Verification Commands

```bash
# Check logs after arrival
ssh matt.wheeler@raspberrypi.local

# Stage 1 logs
tail -20 ~/py_home/data/logs/pre_arrival.log

# Stage 2 logs
tail -20 ~/py_home/data/logs/im_home.log

# WiFi monitor logs
tail -20 ~/py_home/data/logs/wifi_event_monitor.log

# Look for timing
grep "event=complete" ~/py_home/data/logs/pre_arrival.log | tail -1
grep "event=complete" ~/py_home/data/logs/im_home.log | tail -1
```

---

## Test 5: Dry-Run Testing (Optional)

**Purpose:** Test without actually controlling devices

**When to Use:**
- Testing logic without affecting HVAC
- Validating code changes
- Debugging issues

### Steps

```bash
# Test Stage 1 dry-run
ssh matt.wheeler@raspberrypi.local
cd ~/py_home
DRY_RUN=true python automations/pre_arrival.py

# Check output
# Should show: dry_run=True in logs
# No actual device changes

# Test Stage 2 dry-run
DRY_RUN=true python automations/im_home.py
```

### Expected Results

**✅ PASS Criteria:**
1. Both scripts execute without errors
2. Logs show `dry_run=True`
3. Actions logged but not executed
4. No notifications sent (dry-run mode)
5. State files NOT updated

---

## Test 6: Edge Case - Simultaneous Triggers

**Purpose:** Verify state file prevents duplicate actions if both triggers fire quickly

**Scenario:** Geofence and WiFi trigger within seconds of each other

### Steps

**Difficult to simulate - observe in real world:**
```
1. Approach home rapidly (driving)
2. Cross geofence while WiFi is connecting
3. Both triggers may fire within 1-5 seconds
```

### Expected Results

**✅ PASS Criteria:**
1. First trigger (geofence): Runs Stage 1, sets presence = "home"
2. Second trigger (WiFi): Detects presence = "home", skips Stage 1, runs Stage 2
3. Only ONE notification received
4. HVAC only set once
5. Lights still turn on

**❌ FAIL Indicators:**
- Two notifications
- HVAC set twice (wasted API call)
- Lights turn on before WiFi connects

**Check Logs:**
```bash
grep "event=start" ~/py_home/data/logs/pre_arrival.log | tail -1
grep "event=start" ~/py_home/data/logs/im_home.log | tail -1

# Compare timestamps - should be 1-5 seconds apart
```

---

## Test 7: Night Mode Behavior

**Purpose:** Verify Sensibo enabled during night mode arrivals

**Prerequisites:**
- Night mode active (created by goodnight automation)

### Steps

```bash
# Enable night mode
curl -X POST http://raspberrypi.local:5000/goodnight

# Wait for automation to complete

# Verify night mode active
ssh matt.wheeler@raspberrypi.local
ls -la ~/py_home/.night_mode
# File should exist

# Trigger arrival
curl -X POST http://raspberrypi.local:5000/pre-arrival

# Check Sensibo status
curl http://raspberrypi.local:5000/api/sensibo/status
```

### Expected Results

**✅ PASS Criteria:**
1. Nest set to 70°F (comfort temp)
2. Sensibo turned on
3. Sensibo set to 66°F (night mode temp)
4. Log shows: `device=sensibo action=enable_night target=66`

**❌ FAIL Indicators:**
- Sensibo not turned on (should enable during night mode)
- Wrong temperature
- Error in logs

---

## Test 8: Daytime vs Evening Behavior

**Purpose:** Verify bedroom lamps only turn on after 6pm

### Test 8a: Daytime Arrival (Before 6pm)

```bash
# Ensure it's before 6pm
date

# Trigger arrival
curl -X POST http://raspberrypi.local:5000/im-home

# Check Tapo status
curl http://raspberrypi.local:5000/api/tapo/status
```

**Expected:**
- Living room lamp: ON
- Bedroom lamps: OFF (not after 6pm)

### Test 8b: Evening Arrival (After 6pm)

```bash
# Ensure it's after 6pm
date

# Trigger arrival
curl -X POST http://raspberrypi.local:5000/im-home

# Check Tapo status
curl http://raspberrypi.local:5000/api/tapo/status
```

**Expected:**
- Living room lamp: ON
- Bedroom lamps: ON (evening arrival)

---

## Test 9: Automation Master Switch

**Purpose:** Verify two-stage arrival respects automation disable flag

### Steps

```bash
# Disable all automations via dashboard
# OR manually:
ssh matt.wheeler@raspberrypi.local
touch ~/py_home/.automation_disabled

# Verify disabled
curl http://raspberrypi.local:5000/api/automation-control

# Try to trigger arrival
curl -X POST http://raspberrypi.local:5000/pre-arrival
curl -X POST http://raspberrypi.local:5000/im-home
```

### Expected Results

**✅ PASS Criteria:**
1. Both endpoints return: `"status": "skipped"`
2. Reason: "Automations disabled via master switch"
3. No device changes
4. No notifications
5. Logs show: `event=skipped reason=automations_disabled`

**Re-enable:**
```bash
rm ~/py_home/.automation_disabled
# OR via dashboard toggle
```

---

## Test 10: Long-Duration Testing (10+ Cycles)

**Purpose:** Verify reliability over multiple arrival/departure cycles

**Duration:** 1 week

### Procedure

```
For each departure/arrival over 1 week:

1. Note time of departure
2. Verify "Left Home" notification
3. Note time of arrival (geofence cross)
4. Note time of WiFi connect
5. Verify "Welcome Home" notification
6. Check dashboard presence state
7. Note any failures or issues
```

### Success Metrics

**Target Reliability:**
- ≥95% successful Stage 1 triggers
- ≥99% successful Stage 2 triggers (WiFi more reliable)
- <5% false positives (trigger when not actually home)
- 0% duplicate notifications

**Track in Spreadsheet:**
```
| Date | Time | Stage 1 OK? | Stage 2 OK? | Notes |
|------|------|-------------|-------------|-------|
| 10/13 | 5:30pm | ✅ | ✅ | Perfect |
| 10/13 | 9:15pm | ❌ (no geofence) | ✅ (fallback) | WiFi-only |
```

**Acceptable Failures:**
- iOS geofence: 5% miss rate acceptable (WiFi fallback handles)
- WiFi DHCP: 1% miss rate (requires manual trigger)

---

## Troubleshooting

### Issue: 404 Error on /pre-arrival

**Cause:** Endpoint not registered

**Fix:**
```bash
# Verify routes.py deployed
ssh matt.wheeler@raspberrypi.local
grep "pre-arrival" ~/py_home/server/routes.py

# Should show route definition

# Restart Flask
sudo systemctl restart py_home
```

---

### Issue: Stage 1 Runs But HVAC Doesn't Change

**Cause:** Nest API error or dry-run mode active

**Check:**
```bash
# Check logs for errors
tail -50 ~/py_home/data/logs/pre_arrival.log | grep -i error

# Check Nest API manually
curl http://raspberrypi.local:5000/api/nest/status

# Test Nest component directly
ssh matt.wheeler@raspberrypi.local
cd ~/py_home
python -c "from components.nest import NestAPI; n = NestAPI(); print(n.get_status())"
```

---

### Issue: Stage 2 Always Runs Fallback

**Cause:** Presence state not being set by Stage 1

**Check:**
```bash
# Check presence state file
ssh matt.wheeler@raspberrypi.local
cat ~/py_home/.presence_state

# Should show: home

# Check Stage 1 logs
grep "update_state" ~/py_home/data/logs/pre_arrival.log
```

**Fix:**
```bash
# Manually set state to test
echo "home" > ~/py_home/.presence_state
```

---

### Issue: No Notification on Stage 2

**Cause:** Notification system error or dry-run

**Check:**
```bash
# Check logs
tail -50 ~/py_home/data/logs/im_home.log | grep notification

# Test notification manually
ssh matt.wheeler@raspberrypi.local
cd ~/py_home
python -c "from lib.notifications import send_automation_summary; send_automation_summary('Test', ['Action 1'])"
```

---

### Issue: Both Stages Trigger Simultaneously

**Cause:** Geofence radius too large, or very fast approach

**Analysis:**
```bash
# Check timing in logs
grep "event=start" ~/py_home/data/logs/pre_arrival.log | tail -1
grep "event=start" ~/py_home/data/logs/im_home.log | tail -1

# If <5 seconds apart, this is expected behavior
# State file should still prevent duplicates
```

**Adjust if needed:**
```javascript
// In home-geofence.js
homeRadius: 150,  // Reduce from 200 to 150 or 100
```

---

## Success Criteria Summary

### Deployment Phase
- ✅ Files deployed to Pi without errors
- ✅ Flask restarts successfully
- ✅ /pre-arrival endpoint returns 200 OK

### Manual Testing Phase
- ✅ Test 1: Stage 1 works, no notification
- ✅ Test 2: Stage 2 works, notification sent
- ✅ Test 3: WiFi-only fallback works

### Real-World Testing Phase
- ✅ Test 4: Two-stage arrival works end-to-end
- ✅ Timing correct (~60 sec between stages)
- ✅ Single notification received
- ✅ All actions execute correctly

### Edge Cases
- ✅ Test 5: Dry-run mode works
- ✅ Test 6: Simultaneous triggers handled
- ✅ Test 7: Night mode behavior correct
- ✅ Test 8: Time-based logic correct
- ✅ Test 9: Master disable switch respected

### Long-Term Validation
- ✅ Test 10: 10+ cycles with ≥95% success rate

---

## Rollback Plan

If tests fail or issues arise:

### Quick Rollback (Restore Previous Behavior)

```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local
cd ~/py_home

# Restore from git (if needed)
git stash  # Save any local changes
git checkout HEAD~1  # Go back one commit

# OR restore specific files
git checkout HEAD~1 automations/im_home.py
git checkout HEAD~1 server/routes.py

# Remove new file
rm automations/pre_arrival.py

# Restart Flask
sudo systemctl restart py_home
```

### Update iOS Automation

```
1. Open iPhone Shortcuts app
2. Go to Automation tab
3. Find "Arrive at [Home]" automation
4. Edit the URL back to: /im-home
5. Save
```

### Verify Rollback

```bash
# Test old behavior works
curl -X POST http://raspberrypi.local:5000/im-home

# Should run all actions immediately
```

---

## Next Steps After Testing

### If All Tests Pass

1. **Update documentation:**
   - Mark TWO_STAGE_ARRIVAL_PROPOSAL.md as "IMPLEMENTED"
   - Update CHANGELOG.md with deployment date

2. **Monitor for 1 week:**
   - Track reliability metrics
   - Note any issues
   - Gather user feedback

3. **Cleanup deprecated code:**
   - Archive old im_home.py version
   - Remove presence_monitor.py after 30 days

### If Tests Fail

1. **Document failures:**
   - Which tests failed
   - Error messages
   - Log snippets

2. **Analyze root cause:**
   - Code bug?
   - Configuration issue?
   - Design flaw?

3. **Fix or rollback:**
   - If quick fix: Patch and retest
   - If complex: Rollback and redesign

---

## Test Log Template

```markdown
# Two-Stage Arrival Test Results

**Date:** [Date]
**Tester:** [Name]
**Environment:** Production Pi + iPhone

## Pre-Test Setup
- [ ] Code deployed to Pi
- [ ] Flask restarted successfully
- [ ] /pre-arrival endpoint responds

## Manual Tests
- [ ] Test 1: Stage 1 (Pre-Arrival) - PASS/FAIL
- [ ] Test 2: Stage 2 (Physical Arrival) - PASS/FAIL
- [ ] Test 3: WiFi-Only Fallback - PASS/FAIL

## Real-World Tests
- [ ] Test 4: Two-Stage Arrival - PASS/FAIL
  - Stage 1 time: [time]
  - Stage 2 time: [time]
  - Total time: [time]
  - Notification received: YES/NO

## Edge Cases
- [ ] Test 5: Dry-Run - PASS/FAIL
- [ ] Test 6: Simultaneous Triggers - PASS/FAIL
- [ ] Test 7: Night Mode - PASS/FAIL
- [ ] Test 8: Time-Based Logic - PASS/FAIL
- [ ] Test 9: Master Disable - PASS/FAIL

## Long-Term Testing
- [ ] Test 10: 10+ Cycles - [X/10 passed]

## Issues Found
[List any issues, errors, or unexpected behavior]

## Overall Result
- [ ] PASS - Ready for production
- [ ] FAIL - Needs fixes
- [ ] PARTIAL - Minor issues, acceptable

## Notes
[Additional observations]
```

---

## Test 11: Tailscale VPN Connectivity

**Purpose:** Verify geofencing works over cellular via Tailscale VPN

**Prerequisites:**
- Tailscale installed on Pi, laptop, iPhone (completed 2025-10-13)
- Pi Tailscale IP: `100.107.121.6`
- home-geofence.js updated with Tailscale IP

### Steps

**From Laptop:**
```bash
# Test Tailscale connectivity
ping 100.107.121.6

# Test Pi endpoint over Tailscale
curl http://100.107.121.6:5000/status
```

**From iPhone (cellular only):**
```
1. Disable WiFi on iPhone
2. Ensure Tailscale VPN is active (check status bar)
3. Open Scriptable app
4. Run home-geofence script manually
5. Check console output
```

### Expected Results

**✅ PASS Criteria:**

**Laptop Test:**
- Ping successful (~10-50ms latency)
- `/status` endpoint returns: `{"status": "running"}`

**iPhone Test:**
```
=== Home Geofence Check ===
Triggered by: manual
Home network: false  ← Using cellular, not WiFi
Calling: http://100.107.121.6:5000/pre-arrival  ← Using Tailscale IP
✓ Success: {"status": "started"}
=== Complete ===
```

**Key indicators:**
- "Home network: false" (not on WiFi)
- URL shows Tailscale IP `100.107.121.6`
- "✓ Success" (endpoint reached)
- No queue messages (action executed immediately)

**❌ FAIL Indicators:**
- Connection timeout or error
- "Queueing action for later" (means offline)
- Wrong IP in URL (should be 100.107.121.6, not raspberrypi.local)

### Troubleshooting

**If fails:**
1. Check Tailscale running on iPhone (VPN icon in status bar)
2. Verify Pi shows "online" in Tailscale app
3. Test Pi is reachable: `tailscale ping raspberrypi` (from laptop)
4. Verify home-geofence.js has correct IP (`100.107.121.6`)

### Real-World Validation

**Next departure/arrival test:**
- Geofencing should work automatically over cellular
- No need to be on home WiFi
- Actions execute immediately (not queued)

**Benefits:**
- Automations work from anywhere
- Can deploy code remotely
- Can access dashboard while traveling

---

## Related Documents

- **Design:** [TWO_STAGE_ARRIVAL_PROPOSAL.md](./TWO_STAGE_ARRIVAL_PROPOSAL.md)
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Endpoints:** [ENDPOINTS_OVERVIEW.md](./ENDPOINTS_OVERVIEW.md)
- **iOS Setup:** [IOS_AUTOMATION.md](./IOS_AUTOMATION.md)
- **Tailscale Setup:** [TAILSCALE_SETUP_GUIDE.md](./TAILSCALE_SETUP_GUIDE.md)
- **VPN Decision:** [VPN_SETUP_DECISION.md](./VPN_SETUP_DECISION.md)

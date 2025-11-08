# Automation Control Removal Test Plan

**Date:** 2025-11-05
**Change:** Removed `lib/automation_control.py` and `.automation_disabled` mechanism
**Risk Level:** Medium-High (affects all automation scripts)

## Summary of Changes

**Removed:**
- `lib/automation_control.py` (68 lines)
- `are_automations_enabled()` checks from 5 automation scripts
- `.automation_disabled` state file
- `/api/automation-control` POST ability to toggle

**Kept:**
- `dry_run` mechanism via `config.yaml`
- All device control logic
- All automation behavior

**Simplified:**
- One control mechanism instead of two
- Clearer logs (`[DRY-RUN]` prefix)
- Standard software pattern

---

## Test Execution Checklist

### Phase 1: Unit Tests ✓
**Objective:** Verify code still works in isolation

- [✓] Run automation tests: `pytest tests/test_missing_automations.py`
- [✓] Run presence tests: `pytest tests/test_presence_automation_updates.py`
- [✓] Run API endpoint tests: `pytest tests/test_all_endpoints.py`
- [✓] Full test suite: `pytest`

**Expected:** All tests pass
**Result:** ___

---

### Phase 2: Dry-Run Mode Verification
**Objective:** Verify dry-run protects against real actions

#### Test 2.1: Config Setting Check
```bash
# On local machine
grep 'dry_run' config/config.yaml
```
**Expected:** `dry_run: true` (current safe state)
**Result:** ___

#### Test 2.2: Manual Script Execution (Dry-Run)
```bash
# Run leaving_home manually in dry-run
cd /c/git/cyneta/py_home
python automations/leaving_home.py
```
**Expected Output:**
- `[DRY-RUN]` messages in logs
- No actual device changes
- Returns success status

**Result:** ___

#### Test 2.3: Manual Script Execution (Real Mode Override)
```bash
# Test override works
DRY_RUN=false python automations/leaving_home.py
```
**Expected Output:**
- No `[DRY-RUN]` messages
- Would attempt real device control (abort if not desired)

**Result:** ___

---

### Phase 3: Flask API Verification
**Objective:** Verify endpoints still work correctly

#### Test 3.1: System Status Endpoint
```bash
curl http://raspberrypi.local:5000/api/status
```
**Expected JSON contains:**
- `"dry_run": true` (replaced old `automations_enabled`)
- `"status": "operational"`

**Result:** ___

#### Test 3.2: Automation Control GET
```bash
curl http://raspberrypi.local:5000/api/automation-control
```
**Expected JSON:**
```json
{
  "dry_run": true,
  "status": "dry_run",
  "message": "Automations log actions but do not execute"
}
```
**Result:** ___

#### Test 3.3: Automation Control POST (Should Reject)
```bash
curl -X POST http://raspberrypi.local:5000/api/automation-control \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```
**Expected:**
- HTTP 403 Forbidden
- Error message about editing config.yaml

**Result:** ___

---

### Phase 4: Integration Tests (On Pi)
**Objective:** Verify deployed code works in production environment

#### Test 4.1: Deploy to Pi
```bash
# From local machine
cd /c/git/cyneta/py_home
git status  # Verify all changes staged
# Commit changes (use /scommit)
git push

# SSH to Pi
ssh matt.wheeler@100.107.121.6
cd /home/matt.wheeler/py_home
git pull
sudo systemctl restart py_home
```
**Expected:** Service restarts successfully
**Result:** ___

#### Test 4.2: Verify Service Health
```bash
# On Pi
systemctl status py_home
journalctl -u py_home -n 20
```
**Expected:**
- Service: `active (running)`
- No import errors
- Flask starts successfully

**Result:** ___

#### Test 4.3: Check Dry-Run Config on Pi
```bash
# On Pi
grep 'dry_run' /home/matt.wheeler/py_home/config/config.yaml
```
**Expected:** `dry_run: true` (safe state)
**Result:** ___

#### Test 4.4: Test Flask Endpoint from Local
```bash
# From local machine
curl http://raspberrypi:5000/api/automation-control
```
**Expected:** Returns dry-run status
**Result:** ___

---

### Phase 5: Real Automation Tests (Dry-Run on Pi)
**Objective:** Verify automations work end-to-end but don't execute

#### Test 5.1: Trigger Leaving Home from iOS
**Steps:**
1. User runs "Leaving Home" Scriptable script on iPhone
2. Check logs on Pi

```bash
# On Pi
tail -20 /home/matt.wheeler/py_home/data/logs/automations.log
```
**Expected:**
- `event=start` for leaving_home
- `[DRY-RUN]` messages for Nest, Sensibo, Tapo
- `event=complete` status=success
- Devices NOT actually changed

**Result:** ___

#### Test 5.2: Trigger Pre-Arrival via iOS Geofence
**Steps:**
1. User crosses geofence boundary (173m radius)
2. iOS automation triggers ph_home-geofence.js
3. Script calls `/pre-arrival`

```bash
# On Pi
tail -30 /home/matt.wheeler/py_home/data/logs/automations.log | grep pre_arrival
```
**Expected:**
- Stage 1 pre-arrival runs
- `[DRY-RUN]` messages for HVAC/lights
- Presence state NOT updated (dry-run)

**Result:** ___

#### Test 5.3: Trigger Im Home via WiFi
**Steps:**
1. Connect iPhone to home WiFi
2. WiFi event monitor triggers `/im-home`

```bash
# On Pi
tail -30 /home/matt.wheeler/py_home/data/logs/automations.log | grep im_home
```
**Expected:**
- Stage 2 im_home runs
- Checks presence state (may run Stage 1 fallback)
- `[DRY-RUN]` messages for lights
- No notification sent (dry-run)

**Result:** ___

---

### Phase 6: Dashboard Verification
**Objective:** Verify dashboard still displays status correctly

#### Test 6.1: Load Dashboard
**Steps:**
1. Open browser: http://raspberrypi.local:5000
2. Check system status section

**Expected:**
- Dashboard loads
- System status shows operational
- (May need to check if dashboard uses removed fields)

**Result:** ___

---

### Phase 7: Rollback Dry-Run (OPTIONAL - Only if user approves)
**Objective:** Enable real device control

⚠️ **WARNING: Only proceed if user explicitly approves**

#### Test 7.1: Disable Dry-Run on Pi
```bash
# On Pi
nano /home/matt.wheeler/py_home/config/config.yaml
# Change line 20: dry_run: true → dry_run: false
# Save and exit

sudo systemctl restart py_home
```
**Expected:** Service restarts with dry-run disabled
**Result:** ___

#### Test 7.2: Test Real Action (Small Scale)
```bash
# On Pi - test manually with smallest action
python /home/matt.wheeler/py_home/automations/goodnight.py
```
**Expected:**
- No `[DRY-RUN]` messages
- Devices actually change (Nest, Sensibo, Tapo)
- User observes physical changes

**Result:** ___

#### Test 7.3: Re-Enable Dry-Run
```bash
# On Pi - restore safe state
nano /home/matt.wheeler/py_home/config/config.yaml
# Change line 20: dry_run: false → dry_run: true
sudo systemctl restart py_home
```
**Result:** ___

---

## Test Execution Results

### Summary
- **Total Tests:** 18
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___

### Issues Found
(List any issues discovered during testing)

1. ___
2. ___

### Risk Assessment
- **Low Risk:** Unit tests, API endpoints
- **Medium Risk:** Pi deployment, dry-run verification
- **High Risk:** Real device control (Phase 7 - requires approval)

### Rollback Plan
If critical issues found:
1. `git revert HEAD` (undo commit)
2. `git push`
3. SSH to Pi, `git pull`, `sudo systemctl restart py_home`
4. Old `automation_control.py` restored

---

## Sign-Off

**Tested By:** Claude
**Date:** ___
**Status:** ⬜ Pass / ⬜ Fail / ⬜ Pass with Issues

**User Approval for Production:**
- ⬜ Approved to commit changes
- ⬜ Approved to disable dry-run (enable real actions)
- ⬜ Keep dry-run enabled (safe testing mode)

**Notes:**

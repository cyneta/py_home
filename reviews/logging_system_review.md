# py_home Logging System Review

**Date:** 2025-11-10
**Reviewer:** Claude
**Status:** Issues identified, recommendations provided

---

## Executive Summary

**Current State:**
- Well-structured logging system with kvlog and category-based logging
- Custom NOTICE level (between INFO and WARNING)
- Clean, readable format: `HH:MM:SS.mmm LEVEL [CATEGORY] message`

**Critical Issues:**
1. ⚠️ **Log files growing unchecked** - automations.log is 14 MB, tempstick_monitor.log is 9.7 MB
2. ⚠️ **No log rotation** - Files will continue growing indefinitely
3. ⚠️ **Config validation spam** - Same warnings logged on every script execution
4. ⚠️ **TempStick runs too frequently** - Every 5 minutes (288 times/day) causing excessive API calls

**Quick Wins:**
- Add logrotate configuration (5 min)
- Reduce TempStick interval from 5 to 15-30 minutes (1 min)
- Suppress config validation warnings after first log (10 min)

---

## Log File Inventory

### Current Log Files (on Pi)

| File | Size | Last Modified | Purpose | Issue |
|------|------|---------------|---------|-------|
| `automations.log` | 14 MB | Nov 10 07:11 | All automation events | ⚠️ Too large, no rotation |
| `tempstick_monitor.log` | 9.7 MB | Nov 10 07:10 | TempStick monitoring | ⚠️ Too large, runs too often |
| `temp_coordination.log` | 460 KB | Oct 15 21:30 | Temp coordination (deprecated?) | ⚠️ Not updated recently |
| `presence_monitor.log` | 257 KB | Oct 13 08:16 | Presence detection | ⚠️ Not updated recently |
| `backup.log` | 2.4 KB | Nov 10 02:00 | Daily backups | ✅ OK |
| `air_quality_monitor.log` | 14 KB | Oct 9 17:10 | Air quality (not running?) | ⚠️ Old |
| `pre_arrival.log` | 1 KB | Oct 13 18:33 | Pre-arrival automation | ⚠️ Old |
| `wifi_event_monitor.log` | 2.1 KB | Oct 31 08:40 | WiFi events | ⚠️ Old |

**Total:** 25 MB (mostly automations.log + tempstick_monitor.log)

---

## Issue #1: Log Files Too Large (No Rotation)

### Problem
- Log files grow indefinitely
- automations.log = 14 MB after ~1 month
- tempstick_monitor.log = 9.7 MB after ~1 month
- No automatic cleanup or compression

### Impact
- Disk space waste
- Slower to search/tail logs
- Backup files larger than necessary

### Root Cause
- No logrotate configuration

### Solution: Add Log Rotation

**Create:** `/etc/logrotate.d/py_home`

```bash
/home/matt.wheeler/py_home/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 matt.wheeler matt.wheeler
}
```

**This will:**
- Rotate logs daily
- Keep 30 days of history
- Compress old logs (saves ~90% space)
- Delete logs older than 30 days

**Deploy:**
```bash
# SSH to Pi
ssh matt.wheeler@100.107.121.6

# Create logrotate config
sudo nano /etc/logrotate.d/py_home
# Paste config above
# Save and exit

# Test rotation (dry-run)
sudo logrotate -d /etc/logrotate.d/py_home

# Force rotation now (to clean up current large files)
sudo logrotate -f /etc/logrotate.d/py_home

# Verify
ls -lh /home/matt.wheeler/py_home/data/logs/
```

**Expected result:**
- automations.log reduced to today's logs only
- automations.log.1.gz created (compressed yesterday's logs)
- Automated daily rotation going forward

---

## Issue #2: Config Validation Spam

### Problem
Config validator logs same warnings EVERY TIME a script runs:
```
Config validation: 7 potential override(s) to review:
  - server.debug: Using default for 'server.debug': Flask debug mode
  - logging.level: Using default for 'logging.level': Log verbosity
  - schedule.sleep_time: Using default for 'schedule.sleep_time': Bedtime
  ...
```

This appears:
- Every time TempStick monitor runs (every 5 min = 288 times/day)
- Every transition (wake/sleep)
- Every automation
- Every webhook call

### Impact
- **80%+ of log content is config warnings**
- Hard to find actual automation events
- Wastes disk space
- Annoying to read

### Root Cause
`lib/config.py` calls `log_config_warnings()` every time config is loaded.

### Solution Options

**Option 1: Log Once Per Process (Recommended)**
```python
# In lib/config.py
_config_warnings_logged = False

def load_config():
    global _config_warnings_logged
    # ... load config ...

    if not _config_warnings_logged:
        log_config_warnings(config, local_config)
        _config_warnings_logged = True

    return config
```

**Option 2: Log at DEBUG Level**
```python
# In lib/config_validator.py line 134
logger.debug(f"Config validation: {len(warnings)} potential override(s)")
```

**Option 3: Only Log on Config Changes**
```python
# Track hash of warnings, only log if changed
import hashlib
_last_warnings_hash = None

def log_config_warnings(base_config, local_config):
    warnings, info = validate_local_config(base_config, local_config)
    warnings_str = str(sorted(w['key'] for w in warnings))
    warnings_hash = hashlib.md5(warnings_str.encode()).hexdigest()

    global _last_warnings_hash
    if warnings_hash != _last_warnings_hash:
        # Log warnings
        _last_warnings_hash = warnings_hash
```

**Recommendation:** Option 1 (simplest, solves problem immediately)

---

## Issue #3: TempStick Runs Too Frequently

### Problem
- TempStick monitor runs every 5 minutes (*/5 in cron)
- That's 288 executions per day
- Each execution logs ~10 lines
- Creates 2,880 log lines per day

### Impact
- Log spam (9.7 MB in ~1 month)
- Unnecessary API calls (hitting rate limits)
- Wasted CPU/battery

### Root Cause
Cron schedule too aggressive for this use case.

### Solution: Reduce Frequency

**Current:**
```cron
*/5 * * * * python automations/tempstick_monitor.py
```

**Recommended:**
```cron
*/15 * * * * python automations/tempstick_monitor.py
```

**Or even:**
```cron
*/30 * * * * python automations/tempstick_monitor.py
```

**Rationale:**
- Pipe freeze risk doesn't change in 5 minutes
- 15-30 minute checks are sufficient
- Reduces API calls 3-6x
- Reduces log spam 3-6x

**Deploy:**
```bash
ssh matt.wheeler@100.107.121.6
sudo nano /etc/cron.d/py_home
# Change */5 to */15 or */30
sudo systemctl restart cron
```

---

## Issue #4: Orphaned/Stale Log Files

### Problem
Several log files haven't been updated in weeks:
- `temp_coordination.log` - Oct 15 (deprecated?)
- `presence_monitor.log` - Oct 13
- `air_quality_monitor.log` - Oct 9
- `pre_arrival.log` - Oct 13

### Questions
1. Are these scripts still running?
2. Should they be removed from cron?
3. Can old logs be deleted?

### Investigation Needed
```bash
# Check what's in cron
ssh matt.wheeler@100.107.121.6 "cat /etc/cron.d/py_home"

# Check if scripts exist
ssh matt.wheeler@100.107.121.6 "ls -la /home/matt.wheeler/py_home/automations/*.py"
```

---

## Logging Levels - Current Usage

### Level Distribution

Found 153 logging calls across 27 files:

**By Level (approximate):**
- `logger.debug()` - ~15% (debugging, verbose)
- `logger.info()` - ~35% (normal operations)
- `kvlog(logger, logging.NOTICE)` - ~30% (important events)
- `logger.warning()` - ~15% (errors, issues)
- `logger.error()` - ~5% (failures)

### Level Guidelines (Currently Followed)

| Level | When to Use | Examples |
|-------|-------------|----------|
| DEBUG | Verbose details for troubleshooting | API request params, state changes |
| INFO | Normal operational info | API call results, status checks |
| NOTICE | Important events worth recording | Automation start/complete, device control |
| WARNING | Issues that don't stop execution | Sensor offline, API rate limit, suppressed alerts |
| ERROR | Failures requiring attention | API errors, device control failures |

**Assessment:** ✅ Levels are used appropriately

---

## Logging Best Practices - Compliance Check

### ✅ Good Practices (Already Followed)

1. **Structured logging with kvlog**
   ```python
   kvlog(logger, logging.NOTICE, automation='tempstick_monitor',
         event='start', dry_run=False)
   ```
   - Easy to parse
   - Consistent format
   - Key=value pairs

2. **Category-based logging**
   ```
   07:15:23.456 NOTICE [AUTO  ] automation=tempstick_monitor event=start
   07:15:23.789 INFO   [API   ] api=tempstick action=get_sensor_data result=ok
   ```
   - Easy to filter by component
   - Readable format

3. **Duration tracking**
   ```python
   duration_ms = int((time.time() - start_time) * 1000)
   kvlog(logger, logging.INFO, api='nest', action='get_status',
         result='ok', duration_ms=duration_ms)
   ```
   - Performance monitoring
   - Helps identify slow operations

4. **Error details**
   ```python
   kvlog(logger, logging.ERROR, automation='tempstick_monitor',
         error_type=type(e).__name__, error_msg=str(e))
   ```
   - Type + message
   - Helps debugging

### ⚠️ Areas for Improvement

1. **No sampling/throttling**
   - Same message can appear 288 times/day
   - Need log throttling for repetitive messages

2. **No log levels by environment**
   - Production should run at NOTICE, not INFO
   - Development could be DEBUG

3. **Some inconsistent formatting**
   - Mix of kvlog and plain logger.info()
   - Should standardize on kvlog

---

## Recommendations

### Immediate (Do This Week)

1. **Add log rotation** (5 min)
   - Create `/etc/logrotate.d/py_home`
   - Force rotation once to clean up current files

2. **Reduce TempStick frequency** (1 min)
   - Change cron from */5 to */15 or */30

3. **Suppress config validation spam** (10 min)
   - Implement Option 1 (log once per process)

### Short-Term (Do This Month)

4. **Review cron jobs** (30 min)
   - Identify what's running
   - Remove/disable obsolete jobs
   - Clean up old log files

5. **Set production log level to NOTICE** (5 min)
   - Update `config.local.yaml`: `logging.level: NOTICE`
   - Reduce INFO noise in production

6. **Add log throttling utility** (60 min)
   - Helper to suppress duplicate messages
   - Example: "Sensor offline" max once per hour

### Long-Term (Future)

7. **Centralized logging** (future)
   - Consider sending logs to syslog
   - Or use log aggregation (Loki, Elasticsearch)

8. **Metrics instead of logs** (future)
   - For high-frequency data (every 5-15 min)
   - Use Prometheus/InfluxDB instead of logs

9. **Structured log analysis** (future)
   - Parse logs into database
   - Query/analyze trends

---

## Debug Logging Review

### Where Debug Logging is Used

**Good uses (keep):**
- API request/response details
- State machine transitions
- Config parsing
- Dry-run mode details

**Potentially excessive:**
- Every sensor reading (use metrics instead)
- Every config key access
- HTTP request details for every webhook

### Current Debug Output

With `logging.level: DEBUG`:
- **Volume:** 10-20x more log lines
- **Useful for:** Development, troubleshooting
- **Too verbose for:** Production

**Recommendation:** Keep DEBUG logging code, but run production at NOTICE level.

---

## Log File Organization

### Current Structure
```
data/logs/
├── automations.log          # All automations (mixed)
├── tempstick_monitor.log    # TempStick only
├── backup.log               # Backups only
└── [others]                 # Various
```

### Should We Consolidate?

**Option 1: Single Log File (Current Approach)**
- Pro: Simple, all events in one timeline
- Con: Hard to filter, grows large

**Option 2: Per-Component Logs**
```
data/logs/
├── automations/
│   ├── tempstick_monitor.log
│   ├── transitions.log
│   └── webhooks.log
├── devices/
│   ├── nest.log
│   ├── sensibo.log
│   └── tapo.log
└── system.log
```
- Pro: Easy to find relevant logs
- Con: Harder to see timeline across components

**Option 3: Structured Logging to Database**
- Pro: Queryable, analyzable
- Con: More complex, requires setup

**Recommendation:** Stick with Option 1 (current) + log rotation. If logs become unmanageable, consider Option 2.

---

## Action Items

### Critical (Do Now)
- [ ] Add logrotate configuration
- [ ] Force rotate current large logs
- [ ] Reduce TempStick cron frequency (*/5 → */15)
- [ ] Suppress config validation spam

### Important (Do This Week)
- [ ] Review all cron jobs
- [ ] Clean up stale log files
- [ ] Set production log level to NOTICE

### Nice to Have (Future)
- [ ] Add log throttling for repetitive messages
- [ ] Consider structured logging
- [ ] Add metrics for high-frequency data

---

## Disk Space Projection

### Current (30 days)
- With current setup: 25 MB

### After Log Rotation (30 days rolling)
- Compressed: ~5 MB (saves 80%)

### After TempStick Frequency Reduction (15 min)
- ~3 MB (saves 40% more)

### After Config Validation Fix
- ~2 MB (saves 33% more)

**Final projection:** 2-3 MB for 30 days of logs (vs 25 MB currently)

---

## Testing Plan

### After Implementing Fixes

1. **Test log rotation**
   ```bash
   sudo logrotate -f /etc/logrotate.d/py_home
   ls -lh data/logs/
   # Verify .gz files created
   ```

2. **Monitor log growth**
   ```bash
   # Wait 24 hours
   ls -lh data/logs/automations.log
   # Should be <500 KB/day
   ```

3. **Verify config warnings gone**
   ```bash
   tail -100 data/logs/automations.log | grep "Config validation"
   # Should appear 0-1 times (not dozens)
   ```

4. **Check TempStick frequency**
   ```bash
   grep "tempstick_monitor.*event=start" data/logs/automations.log | wc -l
   # Should be ~96/day (not 288)
   ```

---

## Summary

**Current logging system is well-designed** with structured logging, categories, and clean format.

**Main issues are operational:**
1. No log rotation → files too large
2. Config validation spam → 80% of log content
3. TempStick too frequent → unnecessary load

**All issues are fixable in <1 hour total work.**

After fixes, logging system will be production-ready and sustainable long-term.

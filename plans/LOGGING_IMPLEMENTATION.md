# Unified Structured Logging Implementation

**Status:** Ready for implementation
**Estimated time:** 3-4 hours
**Files impacted:** 22 modified, 2 created

---

## Overview

Implement Unix-standard structured logging across entire py_home codebase using Python's built-in logging module with syslog-compatible levels and key=value format.

**Core principles:**
- Built-in Python logging (no dependencies)
- Syslog-compatible levels with custom NOTICE (25)
- Structured key=value format (grep/awk/journalctl friendly)
- Complete audit trail (actions + responses + timing)
- Centralized configuration

---

## Current State Problems

### 1. Inconsistent Logging Setup
- Each file does `logging.basicConfig()` independently
- Hardcoded log levels instead of env var

### 2. Mixed print() and logger Statements
Production code files with print():
- `automations/arrival_lights.py` - line 71
- `automations/arrival_preheat.py` - line 87
- `automations/presence_monitor.py` - lines 240-245
- `automations/task_router.py` - lines 238-251
- `automations/traffic_alert.py` - lines 140-144
- `automations/travel_time.py` - line 105

### 3. Unstructured Log Messages
**Current:** `logger.info("✓ Nest set to away temp: 62°F")`
**Target:** `kvlog(logger, NOTICE, automation='leaving_home', device='nest', action='set_temp', target=62, result='ok')`

### 4. Missing Response Logging
- API calls logged (action) but not responses (result)
- No timing data (duration_ms)
- No structured error details

### 5. No Central Log Level Control
- Each file hardcodes `logging.INFO`
- Should read from `LOG_LEVEL` env var

---

## Design

### Log Levels (Syslog-Compatible)
```
CRITICAL = 50  # System failure
ERROR = 40     # Operation failed
WARNING = 30   # Degraded operation
NOTICE = 25    # Normal operations (NEW - DEFAULT)
INFO = 20      # Detailed information
DEBUG = 10     # Developer debugging
```

**Key addition:** Custom NOTICE level (25) between INFO and WARNING
- **NOTICE** = Normal operational events worth recording (default)
- **INFO** = Verbose details you don't usually need
- **DEBUG** = Developer troubleshooting

### Structured Format (Key=Value)
```
2025-10-08 14:23:45 py_home.automation[1234] NOTICE automation=leaving_home event=start
2025-10-08 14:23:45 py_home.nest[1234] NOTICE device=nest action=set_temp result=ok duration_ms=234
2025-10-08 14:23:46 py_home.automation[1234] NOTICE automation=leaving_home event=complete duration_ms=891
```

**Format benefits:**
- Grep-friendly: `grep device=nest`
- Awk-friendly: `awk -F'=' '/duration_ms/ {sum+=$2}'`
- Journalctl-compatible
- Human-readable
- No JSON parsing needed

---

## Implementation Plan

### Phase 1: Core Infrastructure

**Create:** `lib/logging_config.py`
```python
import logging
import os

# Add custom NOTICE level
logging.NOTICE = 25
logging.addLevelName(25, 'NOTICE')

def kvlog(logger, level, **kwargs):
    """Log structured key=value pairs"""
    msg = ' '.join(f'{k}={v}' for k, v in kwargs.items())
    logger.log(level, msg)

def setup_logging():
    """Configure logging for entire application"""
    log_level = os.getenv('LOG_LEVEL', 'NOTICE')
    log_format = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    logging.basicConfig(level=log_level, format=log_format)
```

**Update:** `server/app.py`
```python
from lib.logging_config import setup_logging

# Call at startup (replace existing logging.basicConfig)
setup_logging()
```

**Remove all other `logging.basicConfig()` calls** from remaining files.

### Phase 2: Remove Print Statements

Replace all `print()` in production code with `kvlog()` calls:
- `automations/arrival_lights.py`
- `automations/arrival_preheat.py`
- `automations/presence_monitor.py`
- `automations/task_router.py`
- `automations/traffic_alert.py`
- `automations/travel_time.py`

Keep `print()` in test/demo files only.

### Phase 3: Convert Automations to Structured Logging

**Pattern for all automations:**
```python
from lib.logging_config import kvlog
import time

logger = logging.getLogger(__name__)

def run():
    start_time = time.time()
    kvlog(logger, logging.NOTICE, automation='leaving_home', event='start', dry_run=DRY_RUN)

    errors = []

    # Device operations
    try:
        api_start = time.time()
        result = nest.set_temperature(62)
        duration = int((time.time() - api_start) * 1000)
        kvlog(logger, logging.NOTICE, device='nest', action='set_temp',
              target=62, result='ok', duration_ms=duration)
    except Exception as e:
        kvlog(logger, logging.ERROR, device='nest', action='set_temp',
              error_type=type(e).__name__, error_msg=str(e))
        errors.append(str(e))

    # Complete
    total_duration = int((time.time() - start_time) * 1000)
    kvlog(logger, logging.NOTICE, automation='leaving_home', event='complete',
          duration_ms=total_duration, errors=len(errors))
```

**Files to convert (9):**
1. `automations/arrival_lights.py`
2. `automations/arrival_preheat.py`
3. `automations/good_morning.py`
4. `automations/goodnight.py`
5. `automations/im_home.py`
6. `automations/leaving_home.py`
7. `automations/presence_monitor.py`
8. `automations/task_router.py`
9. `automations/traffic_alert.py`

### Phase 4: Add Response/Timing Logging to API Clients

**Pattern for components/services:**
```python
from lib.logging_config import kvlog
import time

def set_temperature(self, temp):
    start_time = time.time()
    kvlog(logger, logging.DEBUG, api='nest', action='set_temp', target=temp)

    try:
        response = self._api_call(temp)
        duration = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.INFO, api='nest', action='set_temp',
              result='ok', duration_ms=duration)
        return response
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        kvlog(logger, logging.ERROR, api='nest', action='set_temp',
              error_type=type(e).__name__, error_msg=str(e), duration_ms=duration)
        raise
```

**Components to update (3):**
1. `components/nest/client.py`
2. `components/tapo/client.py`
3. `components/sensibo/client.py`

**Services to update (4):**
1. `services/openweather.py`
2. `services/google_maps.py`
3. `services/github.py`
4. `services/checkvist.py`

### Phase 5: Add Request Timing Middleware

**Update:** `server/routes.py`
```python
import time
from lib.logging_config import kvlog

@app.before_request
def log_request_start():
    request.start_time = time.time()
    kvlog(logger, logging.DEBUG,
          method=request.method,
          path=request.path,
          client=request.remote_addr)

@app.after_request
def log_request_end(response):
    duration = int((time.time() - request.start_time) * 1000)
    kvlog(logger, logging.NOTICE,
          method=request.method,
          path=request.path,
          status=response.status_code,
          duration_ms=duration)
    return response
```

### Phase 6: Update Core Library

**Update:** `lib/location.py`
- Replace string logging with kvlog()
- Add timing to API calls

### Phase 7: Documentation & Configuration

**Update:** `.env.example`
```bash
# Logging (Unix syslog-compatible)
LOG_LEVEL=NOTICE  # DEBUG, INFO, NOTICE(default), WARNING, ERROR, CRITICAL
```

**Create:** `docs/LOGGING.md` (see Query Examples section below)

---

## Target Log Format Examples

### Automation Start/Complete
```
2025-10-08 14:23:45 py_home.automation[1234] NOTICE automation=leaving_home event=start dry_run=false
2025-10-08 14:23:46 py_home.automation[1234] NOTICE automation=leaving_home event=complete duration_ms=1234 errors=0
```

### Device Operations
```
2025-10-08 14:23:45 py_home.nest[1234] NOTICE device=nest action=set_temp target=62 result=ok duration_ms=234
2025-10-08 14:23:45 py_home.tapo[1234] NOTICE device=tapo_livingroom action=turn_off result=ok duration_ms=123
```

### API Calls
```
2025-10-08 14:23:45 py_home.openweather[1234] DEBUG api=openweather endpoint=current lat=45.7054 lng=-121.5215
2025-10-08 14:23:45 py_home.openweather[1234] INFO api=openweather result=ok temp=48 conditions=clear duration_ms=342
```

### Errors
```
2025-10-08 14:23:45 py_home.nest[1234] ERROR device=nest action=set_temp error_type=ConnectionError error_msg="timeout after 10s" duration_ms=10234
```

### Flask Requests
```
2025-10-08 14:23:45 py_home.server[1234] DEBUG method=POST path=/automation/leaving_home client=192.168.1.100
2025-10-08 14:23:46 py_home.server[1234] NOTICE method=POST path=/automation/leaving_home status=200 duration_ms=1234
```

---

## Query Examples (for docs/LOGGING.md)

### Basic Queries
```bash
# All automation runs today
grep "automation=" py_home.log | grep "event=start"

# All errors
grep "ERROR" py_home.log

# Specific device operations
grep "device=nest" py_home.log

# Specific automation
grep "automation=leaving_home" py_home.log
```

### Performance Analysis
```bash
# Slow API calls (>500ms)
grep "duration_ms=" py_home.log | awk -F'duration_ms=' '{print $2}' | awk '{if($1>500) print}'

# Average request duration
grep "path=/automation" py_home.log | grep "duration_ms=" | awk -F'duration_ms=' '{print $2}' | awk '{sum+=$1; n++} END {print sum/n " ms"}'

# Request timing percentiles
grep "path=/automation" py_home.log | grep "duration_ms=" | awk -F'duration_ms=' '{print $2}' | awk '{print $1}' | sort -n

# 95th percentile (after running above, count lines and multiply by 0.95)
grep "path=/automation" py_home.log | grep "duration_ms=" | awk -F'duration_ms=' '{print $2}' | awk '{print $1}' | sort -n | tail -n +95 | head -1
```

### Success Rate
```bash
# Automation success rate
total=$(grep "leaving_home" py_home.log | grep -c "event=complete")
success=$(grep "leaving_home" py_home.log | grep "event=complete" | grep -c "errors=0")
echo "Success: $success/$total = $(echo "scale=2; $success*100/$total" | bc)%"
```

### Error Analysis
```bash
# Nest operations with errors
grep "device=nest" py_home.log | grep "ERROR"

# Error types frequency
grep "ERROR" py_home.log | grep -o "error_type=[^ ]*" | sort | uniq -c | sort -rn

# Most common errors
grep "ERROR" py_home.log | grep -o "error_msg=\"[^\"]*\"" | sort | uniq -c | sort -rn
```

### Real-time Monitoring
```bash
# Tail logs in real-time
tail -f py_home.log

# Only show errors in real-time
tail -f py_home.log | grep ERROR

# Only show automation events
tail -f py_home.log | grep "automation=" | grep -E "(event=start|event=complete)"

# Only show slow operations (>1000ms)
tail -f py_home.log | grep "duration_ms=" | awk -F'duration_ms=' '{if($2>1000) print}'
```

### Systemd Journal (after Pi deployment)
```bash
# All py_home logs
journalctl -u py_home

# Only NOTICE level and above
journalctl -u py_home PRIORITY=5

# Follow in real-time
journalctl -u py_home -f

# Last hour
journalctl -u py_home --since "1 hour ago"

# Today's errors
journalctl -u py_home --since today | grep ERROR

# Structured queries (if using systemd journal format)
journalctl -u py_home DEVICE=nest
journalctl -u py_home AUTOMATION=leaving_home
```

---

## Implementation Checklist

### Phase 1: Foundation (3 tasks)
- [ ] Create `lib/logging_config.py` with NOTICE level + kvlog()
- [ ] Update `server/app.py` to use setup_logging()
- [ ] Remove all `logging.basicConfig()` from other files

### Phase 2: Remove Print (6 tasks)
- [ ] `automations/arrival_lights.py`
- [ ] `automations/arrival_preheat.py`
- [ ] `automations/presence_monitor.py`
- [ ] `automations/task_router.py`
- [ ] `automations/traffic_alert.py`
- [ ] `automations/travel_time.py`

### Phase 3: Convert Automations (4 tasks)
- [ ] `automations/leaving_home.py`
- [ ] `automations/good_morning.py`
- [ ] `automations/goodnight.py`
- [ ] `automations/im_home.py`

### Phase 4: Add Response Logging (7 tasks)
- [ ] `components/nest/client.py`
- [ ] `components/tapo/client.py`
- [ ] `components/sensibo/client.py`
- [ ] `services/openweather.py`
- [ ] `services/google_maps.py`
- [ ] `services/github.py`
- [ ] `services/checkvist.py`

### Phase 5: Core Infrastructure (2 tasks)
- [ ] `server/routes.py` - Add request timing middleware
- [ ] `lib/location.py` - Convert to structured logging

### Phase 6: Documentation (3 tasks)
- [ ] Update `.env.example` with LOG_LEVEL
- [ ] Create `docs/LOGGING.md` with query examples
- [ ] Test grep/awk queries on actual log output

### Phase 7: Testing & Commit (2 tasks)
- [ ] Run full test suite to verify no breakage
- [ ] Commit unified logging system

**Total:** 27 tasks

---

## Benefits

- ✅ Built-in Python logging (no dependencies)
- ✅ Grep/awk/journalctl compatible
- ✅ Complete audit trail (actions + responses)
- ✅ Performance monitoring (duration_ms everywhere)
- ✅ Unified format across entire codebase
- ✅ Production-ready (follows 50 years of Unix patterns)
- ✅ Centralized configuration via env var
- ✅ Backward compatible (old logs still work)

---

## References

- RFC 5424 (Syslog Protocol): https://tools.ietf.org/html/rfc5424
- Systemd Journal Fields: `man systemd.journal-fields`
- Python Logging: https://docs.python.org/3/library/logging.html
- Advanced Python Logging: https://docs.python.org/3/howto/logging-cookbook.html

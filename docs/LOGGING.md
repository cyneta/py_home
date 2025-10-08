# Logging System Guide

**Status:** Production-ready
**Format:** Unix-standard structured key=value logging
**Compatibility:** grep, awk, journalctl

---

## Quick Start

### View Logs
```bash
# Run server and view logs
python server/app.py

# Run automation and view logs
python automations/leaving_home.py

# Tail logs in real-time
tail -f logs/py_home.log  # If LOG_FILE configured
```

### Set Log Level
```bash
# In .env file
LOG_LEVEL=INFO    # Verbose (default for initial rollout)
LOG_LEVEL=NOTICE  # Normal operations
LOG_LEVEL=DEBUG   # Full debugging

# Or via environment
LOG_LEVEL=DEBUG python server/app.py
```

---

## Log Format

### Structure
```
TIMESTAMP NAME[PID] LEVEL key1=value1 key2=value2 ...
```

### Example Logs
```
2025-10-08 14:23:45 py_home.automation[1234] NOTICE automation=leaving_home event=start dry_run=False
2025-10-08 14:23:45 py_home.nest[1234] NOTICE automation=leaving_home device=nest action=set_temp target=62 result=ok duration_ms=234
2025-10-08 14:23:46 py_home.automation[1234] NOTICE automation=leaving_home event=complete duration_ms=1234 errors=0
```

---

## Log Levels

| Level | Value | Usage | Example |
|-------|-------|-------|---------|
| **DEBUG** | 10 | Developer troubleshooting | API request details, internal state |
| **INFO** | 20 | Detailed information | API responses, timing data |
| **NOTICE** | 25 | Normal operations (custom) | Automation start/complete, state changes |
| **WARNING** | 30 | Degraded operation | Retries, fallbacks, config issues |
| **ERROR** | 40 | Operation failed | API errors, device failures |
| **CRITICAL** | 50 | System failure | Fatal errors requiring immediate action |

**Default:** INFO (verbose initially, will tune to NOTICE after validation)

---

## Query Examples

### Basic Searches

```bash
# All automation runs
grep "automation=" py_home.log | grep "event=start"

# All errors today
grep "ERROR" py_home.log

# Specific device operations
grep "device=nest" py_home.log

# Specific automation
grep "automation=leaving_home" py_home.log

# Flask requests
grep "path=/automation" py_home.log
```

### Performance Analysis

```bash
# Find slow API calls (>500ms)
grep "duration_ms=" py_home.log | awk -F'duration_ms=' '{print $2}' | awk '{if($1>500) print $0}'

# Average API response time
grep "duration_ms=" py_home.log | awk -F'duration_ms=' '{print $2}' | awk '{sum+=$1; n++} END {print "Average: " sum/n " ms"}'

# Show all durations sorted
grep "duration_ms=" py_home.log | grep -o "duration_ms=[0-9]*" | cut -d= -f2 | sort -n

# 95th percentile response time
grep "duration_ms=" py_home.log | grep -o "duration_ms=[0-9]*" | cut -d= -f2 | sort -n | awk 'BEGIN{c=0} {a[c]=$1; c++} END{print a[int(c*0.95)]}'
```

### Automation Success Rate

```bash
# Count leaving_home runs
total=$(grep "leaving_home" py_home.log | grep -c "event=complete")
success=$(grep "leaving_home" py_home.log | grep "event=complete" | grep -c "errors=0")

# Calculate percentage
echo "Leaving Home Success Rate: $success/$total"
echo "scale=2; $success*100/$total" | bc | awk '{print $1"%"}'
```

### Error Analysis

```bash
# Nest operation errors
grep "device=nest" py_home.log | grep "ERROR"

# Count error types
grep "ERROR" py_home.log | grep -o "error_type=[^ ]*" | sort | uniq -c | sort -rn

# Most common error messages
grep "ERROR" py_home.log | grep -o 'error_msg="[^"]*"' | sort | uniq -c | sort -rn

# Errors by automation
grep "ERROR" py_home.log | grep -o "automation=[^ ]*" | sort | uniq -c | sort -rn
```

### Device Monitoring

```bash
# All Nest temperature changes today
grep "device=nest" py_home.log | grep "action=set_temp"

# Tapo outlet on/off operations
grep "device=tapo" py_home.log | grep -E "(action=turn_on|action=turn_off)"

# Sensibo AC operations
grep "device=sensibo" py_home.log
```

### Real-time Monitoring

```bash
# Tail all logs
tail -f py_home.log

# Only errors
tail -f py_home.log | grep --line-buffered ERROR

# Only automation events
tail -f py_home.log | grep --line-buffered "automation=" | grep --line-buffered -E "(event=start|event=complete)"

# Only slow operations (>1s)
tail -f py_home.log | grep --line-buffered "duration_ms=" | awk -F'duration_ms=' '{if($2>1000) print $0}'

# Automation start/complete with timing
tail -f py_home.log | grep --line-buffered "event=" | grep --line-buffered -E "(start|complete)"
```

### Traffic Analysis

```bash
# Request counts by endpoint
grep "path=" py_home.log | grep -o "path=[^ ]*" | sort | uniq -c | sort -rn

# Requests per hour
grep "event=request_complete" py_home.log | awk '{print $1" "$2}' | cut -d: -f1 | uniq -c

# HTTP status code distribution
grep "status=" py_home.log | grep -o "status=[^ ]*" | sort | uniq -c

# Failed requests (4xx/5xx)
grep "status=" py_home.log | grep -E "status=(4[0-9]{2}|5[0-9]{2})"
```

---

## Systemd Journal Queries (After Pi Deployment)

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

# Specific automation
journalctl -u py_home | grep "automation=leaving_home"

# Boot logs
journalctl -u py_home -b
```

---

## Common Use Cases

### Debugging Failed Automation

```bash
# 1. Find the failed run
grep "automation=leaving_home" py_home.log | grep "errors=" | grep -v "errors=0"

# 2. Get the timestamp
grep "automation=leaving_home" py_home.log | grep "event=start" | tail -1

# 3. View all logs from that run (replace timestamp)
grep "2025-10-08 14:23" py_home.log | grep "leaving_home"

# 4. Check for errors
grep "2025-10-08 14:23" py_home.log | grep "ERROR"
```

### Performance Regression Detection

```bash
# Compare average response times
echo "Last hour:"
grep "duration_ms=" py_home.log --since="1 hour ago" | awk -F'duration_ms=' '{sum+=$2; n++} END {print sum/n " ms"}'

echo "Last 24 hours:"
grep "duration_ms=" py_home.log --since="24 hours ago" | awk -F'duration_ms=' '{sum+=$2; n++} END {print sum/n " ms"}'
```

### Device Availability Check

```bash
# Check if Nest is responding
grep "device=nest" py_home.log | tail -10

# Count recent Nest errors
grep "device=nest" py_home.log | grep "ERROR" --since="1 hour ago" | wc -l

# Last successful Nest operation
grep "device=nest" py_home.log | grep "result=ok" | tail -1
```

---

## Log Fields Reference

### Common Fields

| Field | Description | Example Values |
|-------|-------------|----------------|
| `automation` | Automation name | `leaving_home`, `goodnight`, `im_home` |
| `event` | Event type | `start`, `complete`, `failed` |
| `device` | Device name | `nest`, `tapo`, `sensibo` |
| `action` | Operation performed | `set_temp`, `turn_on`, `get_status` |
| `result` | Operation outcome | `ok`, `failed`, `skipped` |
| `duration_ms` | Time taken (milliseconds) | `234`, `1250` |
| `error_type` | Exception class name | `ConnectionError`, `TimeoutError` |
| `error_msg` | Error message | `timeout after 10s` |
| `dry_run` | Dry-run mode flag | `True`, `False` |

### HTTP Request Fields

| Field | Description | Example Values |
|-------|-------------|----------------|
| `method` | HTTP method | `GET`, `POST` |
| `path` | Request path | `/automation/leaving_home` |
| `status` | HTTP status code | `200`, `404`, `500` |
| `client` | Client IP address | `192.168.1.100` |

### Automation-Specific Fields

| Field | Description | Example Values |
|-------|-------------|----------------|
| `target` | Target temperature | `62`, `72` |
| `temp` | Current temperature | `48`, `75` |
| `errors` | Error count | `0`, `1`, `2` |
| `trigger` | Geofence trigger | `leaving_work`, `near_home` |
| `classification` | Task classification | `github`, `work`, `personal` |

---

## Tips & Best Practices

### Filtering by Time

```bash
# Last N lines
tail -100 py_home.log

# Since specific time (requires GNU grep)
grep --since="2025-10-08 14:00" py_home.log

# Between times (manual)
awk '/2025-10-08 14:00/,/2025-10-08 15:00/' py_home.log
```

### Combining Filters

```bash
# Nest errors in last 100 lines
tail -100 py_home.log | grep "device=nest" | grep "ERROR"

# Slow automation runs
grep "automation=" py_home.log | grep "event=complete" | grep "duration_ms=" | awk -F'duration_ms=' '{if($2>5000) print $0}'

# Failed requests to specific endpoint
grep "path=/automation/leaving_home" py_home.log | grep "status=500"
```

### Export for Analysis

```bash
# Export to CSV (duration data)
grep "duration_ms=" py_home.log | awk -F' ' '{print $1","$2","$NF}' > durations.csv

# Export errors to file
grep "ERROR" py_home.log > errors_$(date +%Y%m%d).log

# Daily summary
date=$(date +%Y-%m-%d)
echo "=== Summary for $date ===" > summary.txt
echo "Total automations:" >> summary.txt
grep "event=start" py_home.log | grep "$date" | wc -l >> summary.txt
echo "Errors:" >> summary.txt
grep "ERROR" py_home.log | grep "$date" | wc -l >> summary.txt
```

---

## Troubleshooting

### No Logs Appearing

```bash
# Check log level
echo $LOG_LEVEL

# Test with DEBUG
LOG_LEVEL=DEBUG python automations/leaving_home.py

# Verify logging is working
python -c "from lib.logging_config import setup_logging, kvlog; import logging; setup_logging(); logger = logging.getLogger('test'); kvlog(logger, logging.INFO, test='working')"
```

### Too Verbose

```bash
# Reduce to NOTICE level (only operations, not details)
export LOG_LEVEL=NOTICE

# Or edit .env
echo "LOG_LEVEL=NOTICE" >> .env
```

### Finding Specific Issues

```bash
# Connection errors
grep "error_type=ConnectionError" py_home.log

# Timeout issues
grep "error_msg.*timeout" py_home.log -i

# Configuration problems
grep "error_type=ConfigError" py_home.log
```

---

## Future Enhancements

Planned improvements:
- Log rotation with logrotate
- Prometheus metrics export
- Grafana dashboards
- Alert rules for ERROR/CRITICAL
- Structured JSON output option
- Log aggregation to central server

---

## References

- **RFC 5424 (Syslog Protocol):** https://tools.ietf.org/html/rfc5424
- **Systemd Journal:** `man systemd.journal-fields`
- **Python Logging:** https://docs.python.org/3/library/logging.html
- **Implementation:** See `dev/LOGGING_IMPLEMENTATION.md`

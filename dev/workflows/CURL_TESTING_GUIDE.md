# curl Testing Guide for py_home

**curl** is a command-line tool for making HTTP requests. Think of it as your "screwdriver" for testing the Flask server - quick, simple, and always available.

---

## Why Use curl?

- **Fast testing** - No need to create iOS Shortcuts first
- **Debugging** - Test endpoints when SSH'd into server
- **Scripting** - Automate testing in bash scripts
- **Always available** - Pre-installed on Linux/Mac, easy on Windows

---

## Installation

### Linux/Mac
Already installed! Just use it.

### Windows (Git Bash)
Already installed with Git! Use Git Bash terminal.

### Windows (PowerShell)
Windows 10+ has curl built-in:
```powershell
curl.exe --version
```

---

## Basic Usage

### Health Check
```bash
# Is the server running?
curl http://localhost:5000/

# Expected output:
# {
#   "service": "py_home webhook server",
#   "status": "running",
#   "version": "1.0.0"
# }
```

### Status Endpoint
```bash
# Get detailed server status
curl http://localhost:5000/status

# Expected output:
# {
#   "service": "py_home",
#   "status": "running",
#   "auth_required": false,
#   "endpoints": ["/leaving-home", "/goodnight", ...]
# }
```

---

## Testing Automation Endpoints

### Leaving Home
```bash
# Trigger leaving home automation
curl -X POST http://localhost:5000/leaving-home

# Expected output:
# {
#   "status": "started",
#   "script": "leaving_home.py",
#   "args": []
# }
```

### Goodnight
```bash
# Trigger goodnight automation
curl -X POST http://localhost:5000/goodnight

# Expected output:
# {
#   "status": "started",
#   "script": "goodnight.py",
#   "args": []
# }
```

### I'm Home
```bash
# Trigger welcome home automation
curl -X POST http://localhost:5000/im-home
```

### Good Morning
```bash
# Trigger morning routine
curl -X POST http://localhost:5000/good-morning
```

---

## Testing Travel Time (Returns Data)

### Basic Travel Time
```bash
# Get travel time to default destination (Milwaukee)
curl "http://localhost:5000/travel-time"

# Expected output (formatted for readability):
# {
#   "destination": "Milwaukee, WI",
#   "distance_miles": 92.1,
#   "duration_minutes": 104,
#   "duration_in_traffic_minutes": 94,
#   "duration_text": "1 hour 34 mins",
#   "traffic_level": "light",
#   "delay_minutes": -10,
#   "message": "Travel time to Milwaukee: 94 minutes (light traffic)",
#   "timestamp": "2025-10-07T09:37:59.388575"
# }
```

### Travel Time to Custom Destination
```bash
# URL encode spaces as %20
curl "http://localhost:5000/travel-time?destination=Madison,%20WI"

# Or use POST with JSON
curl -X POST http://localhost:5000/travel-time \
  -H "Content-Type: application/json" \
  -d '{"destination": "Madison, WI"}'
```

### Pretty Print JSON Output
```bash
# Use jq for formatted output (install: apt install jq)
curl -s "http://localhost:5000/travel-time" | jq

# Or use Python
curl -s "http://localhost:5000/travel-time" | python -m json.tool
```

---

## Testing Add Task

### Add Task with POST
```bash
# Add a task via voice/shortcut simulation
curl -X POST http://localhost:5000/add-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Fix bug in leaving_home.py"}'

# Expected output:
# {
#   "status": "started",
#   "script": "task_router.py",
#   "args": ["Fix bug in leaving_home.py"]
# }
```

---

## Testing with Authentication

If you enable authentication (`FLASK_REQUIRE_AUTH=true`):

### Basic Auth
```bash
# Include username and password
curl -u admin:password http://localhost:5000/status

# Or use Authorization header
curl -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" http://localhost:5000/status
```

### Generate Base64 for Auth Header
```bash
# Create base64 encoded credentials
echo -n "admin:password" | base64
# Output: YWRtaW46cGFzc3dvcmQ=

# Use in header
curl -H "Authorization: Basic YWRtaW46cGFzc3dvcmQ=" http://localhost:5000/status
```

---

## Testing Remote Server

### Test from Another Computer
```bash
# Replace localhost with server IP
curl http://192.168.1.100:5000/status

# Or use hostname
curl http://raspberrypi.local:5000/status
```

### Test External Access
```bash
# If you have port forwarding or VPN
curl http://your-domain.com:5000/status
```

---

## Common curl Options

### Useful Flags
```bash
# -X POST          Specify HTTP method
# -H "Header"      Add header
# -d "data"        Send data (makes it POST automatically)
# -u user:pass     Basic authentication
# -s               Silent mode (no progress bar)
# -i               Include response headers
# -v               Verbose (show full request/response)
# --max-time 10    Timeout after 10 seconds
```

### Examples
```bash
# Verbose output (see full request/response)
curl -v http://localhost:5000/status

# Include response headers
curl -i http://localhost:5000/status

# Silent with timeout
curl -s --max-time 5 http://localhost:5000/travel-time

# Follow redirects
curl -L http://localhost:5000/some-redirect
```

---

## Testing Workflow

### 1. Start the Server
```bash
# Terminal 1
cd /c/git/cyneta/py_home
python server/app.py
```

### 2. Test Health in Another Terminal
```bash
# Terminal 2
curl http://localhost:5000/status
```

### 3. Test Each Endpoint
```bash
# Test travel time (returns data)
curl "http://localhost:5000/travel-time?destination=Milwaukee"

# Test automation trigger (starts background script)
curl -X POST http://localhost:5000/goodnight

# Check server logs in Terminal 1 to verify script ran
```

### 4. Verify Automation Ran
```bash
# Check logs from automation script
# Look in Terminal 1 for output like:
# INFO:server.routes:Received /goodnight request
# INFO:server.routes:Started automation: goodnight.py
```

---

## Scripted Testing

### Bash Script for Testing All Endpoints
```bash
#!/bin/bash
# test_endpoints.sh

BASE_URL="http://localhost:5000"

echo "Testing Flask Server Endpoints"
echo "=============================="

echo -e "\n1. Health Check"
curl -s $BASE_URL/ | python -m json.tool

echo -e "\n2. Status"
curl -s $BASE_URL/status | python -m json.tool

echo -e "\n3. Travel Time"
curl -s "$BASE_URL/travel-time?destination=Milwaukee" | python -m json.tool

echo -e "\n4. Trigger Goodnight (background)"
curl -s -X POST $BASE_URL/goodnight | python -m json.tool

echo -e "\n5. Trigger Leaving Home (background)"
curl -s -X POST $BASE_URL/leaving-home | python -m json.tool

echo -e "\nDone!"
```

Run it:
```bash
chmod +x test_endpoints.sh
./test_endpoints.sh
```

---

## Troubleshooting with curl

### Server Not Responding
```bash
# Test if server is running
curl http://localhost:5000/

# If it fails:
# - Check server/app.py is running
# - Check port 5000 isn't blocked
# - Try: netstat -an | grep 5000
```

### Connection Refused
```bash
# Server not running or wrong port
curl http://localhost:5000/
# curl: (7) Failed to connect to localhost port 5000: Connection refused

# Solution: Start the server
python server/app.py
```

### 404 Not Found
```bash
# Wrong endpoint path
curl http://localhost:5000/wrong-path
# {"error": "Endpoint not found"}

# Solution: Check available endpoints
curl http://localhost:5000/status
```

### 401 Unauthorized
```bash
# Authentication required
curl http://localhost:5000/status
# {"error": "Authentication required"}

# Solution: Add credentials
curl -u admin:password http://localhost:5000/status
```

### Timeout
```bash
# Script taking too long (shouldn't happen with background execution)
curl --max-time 5 http://localhost:5000/travel-time

# If it times out, check:
# - Server logs for errors
# - Google Maps API key is valid
# - Network connectivity
```

---

## Comparison: curl vs Alternatives

### curl (Command Line)
```bash
curl -X POST http://localhost:5000/goodnight
```
**Pros:** Fast, always available, scriptable
**Cons:** Less user-friendly, no GUI

### Browser (GUI)
```
http://localhost:5000/status
```
**Pros:** Visual, easy for GET requests
**Cons:** Can't easily do POST, no auth

### Postman (GUI Tool)
**Pros:** Beautiful UI, save requests, testing suites
**Cons:** Heavy, requires installation

### Python requests (Code)
```python
import requests
response = requests.post('http://localhost:5000/goodnight')
print(response.json())
```
**Pros:** Programmatic, full control
**Cons:** Requires writing code

### iOS Shortcuts (End Goal)
**Pros:** Voice control, mobile, user-friendly
**Cons:** Requires setup, can't test until deployed

---

## Quick Reference Card

```bash
# Health check
curl http://localhost:5000/

# Status
curl http://localhost:5000/status

# Trigger automation (POST)
curl -X POST http://localhost:5000/leaving-home
curl -X POST http://localhost:5000/goodnight
curl -X POST http://localhost:5000/im-home
curl -X POST http://localhost:5000/good-morning

# Get data (GET)
curl "http://localhost:5000/travel-time?destination=Milwaukee"

# Add task (POST with JSON)
curl -X POST http://localhost:5000/add-task \
  -H "Content-Type: application/json" \
  -d '{"task": "Buy groceries"}'

# With auth
curl -u admin:password http://localhost:5000/status

# Remote server
curl http://192.168.1.100:5000/status

# Pretty print JSON
curl -s http://localhost:5000/status | python -m json.tool
```

---

## Advanced: curl as a Monitoring Tool

### Check if Server is Up (Script)
```bash
#!/bin/bash
# monitor.sh - Check if py_home server is healthy

if curl -s -f http://localhost:5000/status > /dev/null; then
    echo "✓ Server is healthy"
    exit 0
else
    echo "✗ Server is down!"
    # Send alert or restart service
    systemctl restart py_home
    exit 1
fi
```

### Automated Health Checks (Cron)
```bash
# Check every 5 minutes
*/5 * * * * /home/pi/py_home/monitor.sh
```

---

## When NOT to Use curl

- **Creating workflows** - Use Python scripts instead
- **User interface** - Use iOS Shortcuts or web UI
- **Persistent monitoring** - Use proper monitoring tools (Prometheus, etc.)
- **Complex testing** - Use pytest with requests library

---

## Summary

**curl is your quick testing screwdriver:**
- ✅ Fast endpoint testing during development
- ✅ Debugging on remote servers via SSH
- ✅ Scripted health checks
- ✅ Verifying server before creating iOS Shortcuts

**Not for:**
- ❌ End-user interaction (use iOS Shortcuts)
- ❌ Complex automation (use Python scripts)
- ❌ Production monitoring (use proper tools)

**Pro tip:** Use curl during development, iOS Shortcuts in production!

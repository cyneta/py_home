# Status Dashboard Implementation Plan

## Overview

Real-time web dashboard showing complete py_home state with event log browser.

**Goal:** Single-page view of all system state + browsable event history

**Access:** Web browser (desktop/mobile) at `http://raspberrypi.local:5001/`

---

## Architecture

```
┌─────────────────────────────────────────┐
│   Frontend (Single HTML Page)          │
│   - Live state display                 │
│   - Event log browser                  │
│   - Auto-refresh (polling)             │
└─────────────────────────────────────────┘
              ↓ HTTP/JSON
┌─────────────────────────────────────────┐
│   Flask Backend (web/status_server.py)  │
│   - GET / → HTML dashboard             │
│   - GET /api/state → JSON state        │
│   - GET /api/events → JSON event log   │
└─────────────────────────────────────────┘
              ↓ reads
┌─────────────────────────────────────────┐
│   State Providers                       │
│   - lib/night_mode.py                  │
│   - components/nest/                    │
│   - components/sensibo/                 │
│   - components/tapo/                    │
│   - components/network/                 │
│   - Log files (recent events)          │
└─────────────────────────────────────────┘
```

---

## Phase 1: Backend API (Flask)

### Task 1.1: Create Flask server structure
**File:** `web/status_server.py`

```python
#!/usr/bin/env python
"""
Status Dashboard Server

Provides real-time view of py_home system state.

Usage:
    python web/status_server.py
    python web/status_server.py --port 5001
"""

from flask import Flask, render_template, jsonify
import os
import sys

app = Flask(__name__,
    template_folder='templates',
    static_folder='static')

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/state')
def api_state():
    """Get current system state as JSON"""
    return jsonify(get_system_state())

@app.route('/api/events')
def api_events():
    """Get recent events"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(get_recent_events(limit))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
```

**Acceptance:**
- Flask server starts on port 5001
- Routes return placeholder data
- Accessible from browser

---

### Task 1.2: Implement state providers
**File:** `web/state.py`

```python
"""System state aggregation"""

def get_system_state():
    """Get complete system state"""
    return {
        'timestamp': datetime.now().isoformat(),
        'presence': get_presence_state(),
        'climate': get_climate_state(),
        'devices': get_device_state(),
        'system': get_system_info()
    }

def get_presence_state():
    """Get presence information"""
    from lib.night_mode import is_night_mode
    from components.network import is_device_home
    from lib.config import config

    device_ip = config['presence']['devices']['primary']['ip']
    is_home = is_device_home(device_ip)

    # Read last change from .presence_state file
    state_file = Path('.presence_state')
    last_change = None
    if state_file.exists():
        last_change = datetime.fromtimestamp(
            state_file.stat().st_mtime
        ).isoformat()

    return {
        'is_home': is_home,
        'last_change': last_change,
        'device_name': config['presence']['devices']['primary']['name']
    }

def get_climate_state():
    """Get climate system state"""
    from components.nest import NestAPI
    from components.sensibo import SensiboAPI
    from lib.night_mode import is_night_mode

    nest = NestAPI(dry_run=False)
    sensibo = SensiboAPI(dry_run=False)

    return {
        'nest': nest.get_status(),
        'sensibo': sensibo.get_status(),
        'night_mode': is_night_mode()
    }

def get_device_state():
    """Get all device states"""
    from components.tapo import TapoAPI

    tapo = TapoAPI(dry_run=False)
    outlets = tapo.get_all_status()

    return {
        'outlets': outlets,
        'total': len(outlets),
        'on': sum(1 for o in outlets if o['on'])
    }

def get_system_info():
    """Get system information"""
    import platform

    return {
        'python_version': platform.python_version(),
        'platform': platform.system(),
        'hostname': platform.node(),
        'uptime': get_uptime()  # Read from /proc/uptime on Linux
    }
```

**Acceptance:**
- `/api/state` returns real data from all systems
- All API calls have error handling
- Response time < 2 seconds

---

### Task 1.3: Implement event log reader
**File:** `web/events.py`

```python
"""Event log parsing and aggregation"""

import re
from datetime import datetime
from pathlib import Path

def get_recent_events(limit=50):
    """
    Parse recent automation events from logs

    Returns list of events sorted by timestamp (newest first)
    """
    events = []

    # Parse structured logs (kvlog format)
    log_dir = Path('data/logs')
    if log_dir.exists():
        for log_file in sorted(log_dir.glob('*.log'), reverse=True):
            events.extend(parse_log_file(log_file))
            if len(events) >= limit:
                break

    # Sort by timestamp, newest first
    events.sort(key=lambda e: e['timestamp'], reverse=True)
    return events[:limit]

def parse_log_file(log_file):
    """Parse kvlog format log file"""
    events = []

    with open(log_file) as f:
        for line in f:
            event = parse_kvlog_line(line)
            if event:
                events.append(event)

    return events

def parse_kvlog_line(line):
    """
    Parse kvlog format:
    2025-10-10 14:32:15 NOTICE automation=leaving_home event=start dry_run=False
    """
    match = re.match(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (\w+) (.+)',
        line
    )
    if not match:
        return None

    timestamp_str, level, kv_pairs = match.groups()

    # Parse key=value pairs
    data = {
        'timestamp': timestamp_str,
        'level': level
    }

    for pair in kv_pairs.split():
        if '=' in pair:
            key, value = pair.split('=', 1)
            data[key] = value

    return data
```

**Acceptance:**
- Parses recent automation runs from logs
- Returns structured event data
- Handles missing/malformed logs gracefully

---

## Phase 2: Frontend (HTML/CSS/JS)

### Task 2.1: Create dashboard HTML
**File:** `web/templates/dashboard.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>py_home Status</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/dashboard.css">
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <h1>🏡 py_home Status</h1>
            <div class="last-update">Updated: <span id="last-update">--</span></div>
        </header>

        <!-- Live State Panel -->
        <section class="state-panel">
            <div class="state-card presence">
                <h2>Presence</h2>
                <div class="status" id="presence-status">Loading...</div>
            </div>

            <div class="state-card climate">
                <h2>Climate</h2>
                <div id="climate-status">Loading...</div>
            </div>

            <div class="state-card devices">
                <h2>Devices</h2>
                <div id="devices-status">Loading...</div>
            </div>

            <div class="state-card system">
                <h2>System</h2>
                <div id="system-status">Loading...</div>
            </div>
        </section>

        <!-- Event Log Browser -->
        <section class="event-log">
            <h2>Recent Events</h2>
            <div class="filters">
                <label>
                    <input type="checkbox" id="filter-errors" checked>
                    Show Errors
                </label>
                <label>
                    <input type="checkbox" id="filter-success" checked>
                    Show Success
                </label>
                <label>
                    Limit: <input type="number" id="limit" value="50" min="10" max="200">
                </label>
            </div>
            <table id="event-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Automation</th>
                        <th>Event</th>
                        <th>Status</th>
                        <th>Duration</th>
                    </tr>
                </thead>
                <tbody id="event-tbody">
                    <tr><td colspan="5">Loading...</td></tr>
                </tbody>
            </table>
        </section>
    </div>

    <script src="/static/dashboard.js"></script>
</body>
</html>
```

**Acceptance:**
- HTML structure complete
- Placeholder content displays
- Mobile-responsive layout

---

### Task 2.2: Style with CSS
**File:** `web/static/dashboard.css`

```css
/* Modern, clean dashboard styling */
:root {
    --bg: #1a1a1a;
    --surface: #2d2d2d;
    --primary: #4a9eff;
    --success: #4caf50;
    --warning: #ff9800;
    --error: #f44336;
    --text: #e0e0e0;
    --text-dim: #999;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
}

.state-panel {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
}

.state-card {
    background: var(--surface);
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid var(--primary);
}

.event-log table {
    width: 100%;
    background: var(--surface);
    border-collapse: collapse;
}

.event-log th {
    background: #333;
    padding: 12px;
    text-align: left;
}

.event-log td {
    padding: 10px 12px;
    border-top: 1px solid #444;
}

.status-home { color: var(--success); }
.status-away { color: var(--warning); }
.status-error { color: var(--error); }

/* Mobile responsive */
@media (max-width: 768px) {
    .state-panel {
        grid-template-columns: 1fr;
    }
}
```

**Acceptance:**
- Clean, modern dark theme
- Good contrast for readability
- Mobile-responsive

---

### Task 2.3: Add JavaScript for live updates
**File:** `web/static/dashboard.js`

```javascript
// Auto-refresh dashboard every 10 seconds
let refreshInterval = 10000; // ms

async function fetchState() {
    try {
        const response = await fetch('/api/state');
        const state = await response.json();
        updateStateDisplay(state);
        updateLastUpdate();
    } catch (error) {
        console.error('Failed to fetch state:', error);
    }
}

async function fetchEvents() {
    try {
        const limit = document.getElementById('limit').value;
        const response = await fetch(`/api/events?limit=${limit}`);
        const events = await response.json();
        updateEventTable(events);
    } catch (error) {
        console.error('Failed to fetch events:', error);
    }
}

function updateStateDisplay(state) {
    // Presence
    const presenceEl = document.getElementById('presence-status');
    const isHome = state.presence.is_home;
    presenceEl.innerHTML = `
        <div class="${isHome ? 'status-home' : 'status-away'}">
            ${isHome ? '🏡 Home' : '🚗 Away'}
        </div>
        <div class="text-dim">Since: ${formatTime(state.presence.last_change)}</div>
    `;

    // Climate
    const climateEl = document.getElementById('climate-status');
    climateEl.innerHTML = `
        <div>Nest: ${state.climate.nest.current_temp_f}°F → ${state.climate.nest.target_temp_f}°F</div>
        <div>Sensibo: ${state.climate.sensibo.current_temp_f}°F (${state.climate.sensibo.on ? 'ON' : 'OFF'})</div>
        <div>Night Mode: ${state.climate.night_mode ? 'Yes' : 'No'}</div>
    `;

    // Devices
    const devicesEl = document.getElementById('devices-status');
    devicesEl.innerHTML = `
        <div>${state.devices.on} / ${state.devices.total} outlets ON</div>
        ${state.devices.outlets.map(o => `
            <div>${o.name}: ${o.on ? '✓ ON' : '✗ OFF'}</div>
        `).join('')}
    `;

    // System
    const systemEl = document.getElementById('system-status');
    systemEl.innerHTML = `
        <div>${state.system.hostname}</div>
        <div>Python ${state.system.python_version}</div>
        <div>Uptime: ${formatUptime(state.system.uptime)}</div>
    `;
}

function updateEventTable(events) {
    const tbody = document.getElementById('event-tbody');
    const showErrors = document.getElementById('filter-errors').checked;
    const showSuccess = document.getElementById('filter-success').checked;

    const filtered = events.filter(e => {
        if (e.level === 'ERROR' && !showErrors) return false;
        if (e.level !== 'ERROR' && !showSuccess) return false;
        return true;
    });

    tbody.innerHTML = filtered.map(e => `
        <tr class="status-${e.level.toLowerCase()}">
            <td>${formatTime(e.timestamp)}</td>
            <td>${e.automation || '--'}</td>
            <td>${e.event || e.action || '--'}</td>
            <td>${e.result || e.level}</td>
            <td>${e.duration_ms ? e.duration_ms + 'ms' : '--'}</td>
        </tr>
    `).join('');
}

function formatTime(isoString) {
    if (!isoString) return '--';
    const date = new Date(isoString);
    return date.toLocaleString();
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return `${days}d ${hours}h`;
}

function updateLastUpdate() {
    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
}

// Initial load
fetchState();
fetchEvents();

// Auto-refresh
setInterval(fetchState, refreshInterval);
setInterval(fetchEvents, refreshInterval * 2); // Events refresh slower

// Filter changes
document.getElementById('filter-errors').addEventListener('change', fetchEvents);
document.getElementById('filter-success').addEventListener('change', fetchEvents);
document.getElementById('limit').addEventListener('change', fetchEvents);
```

**Acceptance:**
- State updates every 10 seconds
- Events update every 20 seconds
- Filters work correctly
- Smooth, no flicker

---

## Phase 3: Integration & Deployment

### Task 3.1: Add systemd service
**File:** `systemd/py_home_status.service`

```ini
[Unit]
Description=py_home Status Dashboard
After=network.target

[Service]
Type=simple
User=matt.wheeler
WorkingDirectory=/home/matt.wheeler/py_home
Environment="PYTHONPATH=/home/matt.wheeler/py_home"
ExecStart=/home/matt.wheeler/py_home/venv/bin/python web/status_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Install:**
```bash
sudo cp systemd/py_home_status.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable py_home_status
sudo systemctl start py_home_status
```

**Acceptance:**
- Service starts on boot
- Auto-restarts on crash
- Accessible at http://raspberrypi.local:5001/

---

### Task 3.2: Add configuration
**File:** `config/config.yaml`

Add section:
```yaml
status_dashboard:
  enabled: true
  port: 5001
  host: "0.0.0.0"  # Listen on all interfaces
  auto_refresh_seconds: 10
  max_events: 200
```

**Acceptance:**
- Dashboard respects config settings
- Can disable via config
- Port configurable

---

### Task 3.3: Add README documentation
**File:** `web/README.md`

```markdown
# Status Dashboard

Real-time web dashboard for py_home system monitoring.

## Access

Open in browser: http://raspberrypi.local:5001/

## Features

- Live system state (presence, climate, devices)
- Event log browser with filtering
- Auto-refresh every 10 seconds
- Mobile-responsive design

## Management

Start: `sudo systemctl start py_home_status`
Stop: `sudo systemctl stop py_home_status`
Restart: `sudo systemctl restart py_home_status`
Logs: `sudo journalctl -u py_home_status -f`

## Development

Run locally:
```bash
cd /home/matt.wheeler/py_home
python web/status_server.py
```

Test API:
```bash
curl http://localhost:5001/api/state | jq
curl http://localhost:5001/api/events | jq
```
```

**Acceptance:**
- Clear usage instructions
- Development workflow documented
- Troubleshooting section

---

## Testing Checklist

### Manual Testing
- [ ] Dashboard loads in browser
- [ ] All state cards show correct data
- [ ] Presence updates when WiFi on/off
- [ ] Climate shows Nest/Sensibo real values
- [ ] Devices show correct on/off status
- [ ] Event log shows recent automations
- [ ] Filters work (errors, success, limit)
- [ ] Auto-refresh works (visible updates)
- [ ] Mobile layout works on phone
- [ ] Multiple browsers work (Chrome, Safari, Firefox)

### API Testing
- [ ] `/api/state` returns valid JSON
- [ ] `/api/state` completes < 2 seconds
- [ ] `/api/events` returns sorted events
- [ ] `/api/events?limit=10` respects limit
- [ ] Error handling works (device offline)

### Integration Testing
- [ ] Service starts on Pi boot
- [ ] Service auto-restarts after crash
- [ ] Dashboard accessible from other devices on network
- [ ] No memory leaks (run 24 hours)

---

## Success Metrics

- Dashboard loads in < 3 seconds
- State updates visible within 10 seconds of change
- No errors in 24-hour run
- Mobile usable (can read all text, tap buttons)
- Event log useful for debugging automations

---

## Future Enhancements

- WebSocket for instant updates (no polling)
- Charts/graphs (temperature over time)
- Push notifications when viewing dashboard
- Device control (turn on/off from dashboard)
- Multi-day event history
- Export events to CSV
- Dark/light theme toggle

# Dashboard Implementation - Complete Code Changes

## Files Modified

### 1. ✅ server/__init__.py
Already added Flask start time tracking.

### 2. ✅ automations/presence_monitor.py
Already added:
- Logging setup
- Robustness with 3-failure threshold
- Fail count tracking

### 3. server/routes.py - NEW API ENDPOINTS NEEDED

Add these endpoints after line 195 (after /api/night-mode):

```python
@app.route('/api/presence')
def api_presence():
    """Get current presence status from .presence_state file"""
    try:
        import os
        state_file = os.path.join(os.path.dirname(__file__), '..', '.presence_state')

        if not os.path.exists(state_file):
            return jsonify({
                'is_home': None,
                'state': 'unknown',
                'source': 'unknown',
                'last_updated': None,
                'age_seconds': None
            }), 200

        # Read state
        with open(state_file, 'r') as f:
            state = f.read().strip().lower()

        # Get file modification time
        mtime = os.path.getmtime(state_file)
        import time
        from datetime import datetime
        age_seconds = time.time() - mtime
        last_updated = datetime.fromtimestamp(mtime).isoformat()

        return jsonify({
            'is_home': state == 'home',
            'state': state,
            'source': 'presence_monitor',
            'last_updated': last_updated,
            'age_seconds': round(age_seconds, 1)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get presence status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/system-status')
def api_system_status():
    """Get comprehensive system status with Flask uptime"""
    try:
        from server import FLASK_START_TIME
        import platform

        # Calculate Flask uptime
        uptime_seconds = time.time() - FLASK_START_TIME
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        if days > 0:
            uptime = f"{days}d {hours}h"
        elif hours > 0:
            uptime = f"{hours}h {minutes}m"
        else:
            uptime = f"{minutes}m"

        # Get night mode
        from lib.night_mode import is_night_mode
        night_mode = is_night_mode()

        # Check system health
        health_status = 'operational'
        services = {}

        # Note: Can't check Pi services from Windows, will show "unknown"
        # These checks work when Flask runs on Pi
        services['presence_monitor'] = {'status': 'unknown', 'type': 'cron'}
        services['wifi_monitor'] = {'status': 'unknown', 'type': 'systemd'}

        # Check if presence state is stale
        state_file = os.path.join(os.path.dirname(__file__), '..', '.presence_state')
        if os.path.exists(state_file):
            age = time.time() - os.path.getmtime(state_file)
            if age > 600:  # 10 minutes
                health_status = 'degraded'
                services['presence_monitor']['status'] = 'stale'
                services['presence_monitor']['age_seconds'] = int(age)

        return jsonify({
            'status': health_status,
            'flask_uptime': uptime,
            'flask_uptime_seconds': int(uptime_seconds),
            'night_mode': night_mode,
            'services': services,
            'platform': platform.system()
        }), 200

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        return jsonify({'error': str(e)}), 500
```

### 4. server/routes.py - UPDATE /api/night-mode

Replace lines 171-195 with:

```python
@app.route('/api/night-mode')
def api_night_mode():
    """Get night mode status (DEPRECATED - use /api/system-status)"""
    try:
        from lib.night_mode import is_night_mode
        from server import FLASK_START_TIME

        # Calculate Flask uptime (not Pi uptime)
        uptime_seconds = time.time() - FLASK_START_TIME
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)

        if days > 0:
            uptime = f"{days}d {hours}h"
        else:
            uptime = f"{hours}h"

        return jsonify({
            'night_mode': is_night_mode(),
            'uptime': uptime
        }), 200
    except Exception as e:
        logger.error(f"Failed to get night mode status: {e}")
        return jsonify({'error': str(e)}), 500
```

### 5. Dashboard JavaScript - COMPLETE REPLACEMENT

Replace the entire `<script>` section in the dashboard (lines 169-401) with this:

```javascript
<script>
    async function loadDashboard() {
        const dashboardEl = document.getElementById('dashboard');
        const lastUpdatedEl = document.getElementById('lastUpdated');

        try {
            // Load all status data in parallel
            const [nest, sensibo, tapo, presence, systemStatus] = await Promise.all([
                fetchNestStatus(),
                fetchSensiboStatus(),
                fetchTapoStatus(),
                fetchPresence(),        // NEW: Use presence API
                fetchSystemStatus()      // NEW: Use system status API
            ]);

            // Build dashboard HTML
            dashboardEl.innerHTML = `
                <div class="grid">
                    ${renderNestCard(nest)}
                    ${renderSensiboCard(sensibo)}
                    ${renderTapoCard(tapo)}
                    ${renderPresenceCard(presence)}
                    ${renderSystemCard(systemStatus)}
                </div>
            `;

            lastUpdatedEl.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        } catch (error) {
            dashboardEl.innerHTML = `
                <div class="error">Failed to load dashboard: ${error.message}</div>
            `;
        }
    }

    async function fetchNestStatus() {
        try {
            const response = await fetch('/api/nest/status');
            if (response.ok) {
                const data = await response.json();
                data._stale = false;
                data._error = null;
                return data;
            }
        } catch (e) {
            return {
                _error: e.message,
                _stale: true,
                current_temp_f: null,
                mode: 'UNKNOWN',
                hvac_status: 'UNKNOWN'
            };
        }

        // Mock data fallback
        return {
            _stale: true,
            current_temp_f: 72.5,
            mode: 'HEAT',
            heat_setpoint_f: 72,
            hvac_status: 'OFF',
            humidity: 52
        };
    }

    async function fetchSensiboStatus() {
        try {
            const response = await fetch('/api/sensibo/status');
            if (response.ok) {
                const data = await response.json();
                data._stale = false;
                data._error = null;
                return data;
            }
        } catch (e) {
            return {
                _error: e.message,
                _stale: true,
                on: false,
                current_temp_f: null
            };
        }

        return {
            _stale: true,
            on: true,
            mode: 'heat',
            target_temp_f: 70,
            current_temp_f: 70.0,
            humidity: 65.6
        };
    }

    async function fetchTapoStatus() {
        try {
            const response = await fetch('/api/tapo/status');
            if (response.ok) {
                const data = await response.json();
                data._stale = false;
                data._error = null;
                return data;
            }
        } catch (e) {
            return {
                _error: e.message,
                _stale: true,
                devices: []
            };
        }

        return {
            _stale: true,
            devices: [
                {name: 'Livingroom Lamp', on: null},
                {name: 'Bedroom Left Lamp', on: null},
                {name: 'Bedroom Right Lamp', on: null},
                {name: 'Heater', on: null}
            ]
        };
    }

    async function fetchPresence() {
        try {
            const response = await fetch('/api/presence');
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {}

        return {
            is_home: null,
            state: 'unknown',
            source: 'error',
            last_updated: null,
            age_seconds: null
        };
    }

    async function fetchSystemStatus() {
        try {
            const response = await fetch('/api/system-status');
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {}

        return {
            status: 'unknown',
            flask_uptime: 'Unknown',
            night_mode: false,
            services: {}
        };
    }

    function renderNestCard(data) {
        const statusClass = data.hvac_status === 'OFF' ? 'status-good' : 'status-warning';
        const staleWarning = data._stale ? '<div class="status-row"><span class="status-value status-warning">⚠️ Data may be stale</span></div>' : '';
        const errorWarning = data._error ? `<div class="status-row"><span class="status-value status-error">❌ ${data._error}</span></div>` : '';

        return `
            <div class="card">
                <div class="card-title">🌡️ Nest Thermostat</div>
                ${data.current_temp_f ? `<div class="temp-display">${data.current_temp_f}°F</div>` : '<div class="temp-display status-error">--°F</div>'}
                <div class="status-row">
                    <span class="status-label">Mode</span>
                    <span class="status-value">${data.mode}</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Target</span>
                    <span class="status-value">${data.heat_setpoint_f || data.cool_setpoint_f || 'ECO'}°F</span>
                </div>
                <div class="status-row">
                    <span class="status-label">HVAC</span>
                    <span class="status-value ${statusClass}">${data.hvac_status}</span>
                </div>
                ${data.humidity ? `<div class="status-row"><span class="status-label">Humidity</span><span class="status-value">${data.humidity}%</span></div>` : ''}
                ${staleWarning}
                ${errorWarning}
            </div>
        `;
    }

    function renderSensiboCard(data) {
        const powerBadge = data.on ? 'badge-online' : 'badge-offline';
        const powerText = data.on === null ? 'UNKNOWN' : (data.on ? 'ON' : 'OFF');
        const staleWarning = data._stale ? '<div class="status-row"><span class="status-value status-warning">⚠️ Data may be stale</span></div>' : '';
        const errorWarning = data._error ? `<div class="status-row"><span class="status-value status-error">❌ ${data._error}</span></div>` : '';

        return `
            <div class="card">
                <div class="card-title">❄️ Sensibo AC (Master Suite)</div>
                ${data.current_temp_f ? `<div class="temp-display">${data.current_temp_f}°F</div>` : '<div class="temp-display status-error">--°F</div>'}
                <div class="status-row">
                    <span class="status-label">Power</span>
                    <span class="badge ${powerBadge}">${powerText}</span>
                </div>
                ${data.mode ? `<div class="status-row"><span class="status-label">Mode</span><span class="status-value">${data.mode.toUpperCase()}</span></div>` : ''}
                ${data.target_temp_f ? `<div class="status-row"><span class="status-label">Target</span><span class="status-value">${data.target_temp_f}°F</span></div>` : ''}
                ${data.humidity ? `<div class="status-row"><span class="status-label">Humidity</span><span class="status-value">${data.humidity}%</span></div>` : ''}
                ${staleWarning}
                ${errorWarning}
            </div>
        `;
    }

    function renderTapoCard(data) {
        const staleWarning = data._stale ? '<div class="status-row"><span class="status-value status-warning">⚠️ Data may be stale</span></div>' : '';
        const errorWarning = data._error ? `<div class="status-row"><span class="status-value status-error">❌ ${data._error}</span></div>` : '';

        return `
            <div class="card">
                <div class="card-title">💡 Smart Outlets</div>
                ${data.devices && data.devices.length > 0 ? data.devices.map(device => `
                    <div class="status-row">
                        <span class="status-label">${device.name}</span>
                        <span class="badge ${device.on === null ? 'badge-offline' : (device.on ? 'badge-online' : 'badge-offline')}">
                            ${device.on === null ? 'UNKNOWN' : (device.on ? 'ON' : 'OFF')}
                        </span>
                    </div>
                `).join('') : '<div class="status-row"><span class="status-value status-error">No devices found</span></div>'}
                ${staleWarning}
                ${errorWarning}
            </div>
        `;
    }

    function renderPresenceCard(data) {
        let statusBadge, statusText, statusDetail;

        if (data.is_home === null) {
            statusBadge = 'badge-offline';
            statusText = 'UNKNOWN';
            statusDetail = 'No presence data available';
        } else if (data.age_seconds > 300) {  // 5 minutes
            statusBadge = 'badge-warning';
            statusText = data.is_home ? 'HOME' : 'AWAY';
            statusDetail = `⚠️ Last checked ${Math.round(data.age_seconds / 60)} min ago`;
        } else {
            statusBadge = data.is_home ? 'badge-home' : 'badge-away';
            statusText = data.is_home ? 'HOME' : 'AWAY';
            statusDetail = `✓ Checked ${Math.round(data.age_seconds)}s ago`;
        }

        return `
            <div class="card">
                <div class="card-title">📍 Presence</div>
                <div class="status-row">
                    <span class="status-label">Status</span>
                    <span class="badge ${statusBadge}">${statusText}</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Source</span>
                    <span class="status-value">${data.source || 'unknown'}</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Last Check</span>
                    <span class="status-value ${data.age_seconds > 300 ? 'status-warning' : 'status-good'}">${statusDetail}</span>
                </div>
            </div>
        `;
    }

    function renderSystemCard(data) {
        const statusBadge = data.status === 'operational' ? 'badge-online' :
                          data.status === 'degraded' ? 'badge-warning' : 'badge-offline';
        const statusText = data.status.toUpperCase();

        const modeBadge = data.night_mode ? 'badge-warning' : 'badge-online';
        const modeText = data.night_mode ? 'NIGHT MODE' : 'DAY MODE';

        return `
            <div class="card">
                <div class="card-title">⚙️ System</div>
                <div class="status-row">
                    <span class="status-label">Status</span>
                    <span class="badge ${statusBadge}">${statusText}</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Mode</span>
                    <span class="badge ${modeBadge}">${modeText}</span>
                </div>
                <div class="status-row">
                    <span class="status-label">Flask Uptime</span>
                    <span class="status-value">${data.flask_uptime}</span>
                </div>
                ${Object.keys(data.services).length > 0 ? Object.entries(data.services).map(([name, service]) => `
                    <div class="status-row">
                        <span class="status-label">${name}</span>
                        <span class="status-value ${service.status === 'active' || service.status === 'enabled' ? 'status-good' :
                                                   service.status === 'stale' ? 'status-warning' : 'status-error'}">
                            ${service.status}
                        </span>
                    </div>
                `).join('') : ''}
            </div>
        `;
    }

    // Load dashboard on page load
    loadDashboard();

    // Auto-refresh every 5 seconds
    setInterval(loadDashboard, 5000);
</script>
```

## Summary of Changes

1. ✅ **Flask uptime tracking** - Added `FLASK_START_TIME` in server/__init__.py
2. ✅ **Robust presence detection** - Modified presence_monitor.py with 3-failure threshold
3. 🔄 **NEW /api/presence endpoint** - Reads .presence_state file (not stale GPS data)
4. 🔄 **NEW /api/system-status endpoint** - Comprehensive system health with Flask uptime
5. 🔄 **Dashboard uses presence API** - Changed from /location to /api/presence
6. 🔄 **Per-item staleness warnings** - Each card shows "⚠️ Data may be stale" if applicable
7. 🔄 **Flask uptime (not Pi uptime)** - System card shows Flask server uptime
8. 🔄 **Presence card shows age** - "Last checked Xs ago" or "⚠️ Last checked 10 min ago"

## Next Steps

1. Apply the route changes (add new endpoints)
2. Replace dashboard JavaScript
3. Deploy to Pi
4. Test each card shows correct data + staleness warnings
5. Verify Flask uptime resets when server restarts (not when Pi reboots)

## Testing Checklist

- [ ] Dashboard shows "HOME" when .presence_state = "home"
- [ ] Dashboard shows "AWAY" when .presence_state = "away"
- [ ] Presence card shows "⚠️ Last checked X min ago" when data >5min old
- [ ] Flask uptime shows server uptime (not Pi uptime)
- [ ] System card shows "OPERATIONAL" or "DEGRADED"
- [ ] Each card shows stale data warning when API fails
- [ ] Presence monitor doesn't trigger false "away" until 3 failures (6 minutes)

# py_home Architecture

**Status:** Production
**Last Updated:** 2025-10-13
**For historical design doc, see:** [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md)

---

## Overview

py_home is a Python-based home automation system running on Raspberry Pi, controlled via iOS (Scriptable scripts and Shortcuts) and Siri voice commands.

**Core Principle:** Lightweight, code-first automation using Python + HTTP APIs + cron scheduling.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     iOS Layer (iPhone)                       │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Scriptable Scripts (Background)                     │   │
│  │  - home-geofence.js  → Arrival/departure detection  │   │
│  │  - [Future scripts...]                               │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │  iOS Shortcuts (Manual Triggers)                     │   │
│  │  - Good Morning    - Goodnight                       │   │
│  │  - [Voice commands via Siri]                         │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
└───────────────────────┼──────────────────────────────────────┘
                        │ HTTP (WiFi/VPN)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 Pi Layer (Raspberry Pi 4)                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Flask API Server (Port 5000)                        │   │
│  │  - Webhook endpoints (/leaving-home, /im-home, etc.) │   │
│  │  - Dashboard UI (/dashboard)                         │   │
│  │  - System status API                                 │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │  Python Automations (automations/)                   │   │
│  │  - leaving_home.py    - im_home.py                   │   │
│  │  - goodnight.py       - good_morning.py              │   │
│  │  - temp_coordination.py (cron: */15 min)             │   │
│  │  - presence_monitor.py (cron: */5 min)               │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │  Device Components (components/)                     │   │
│  │  - nest/      - sensibo/     - tapo/                 │   │
│  │  - network/   - notifications/                       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS APIs
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Nest   │  │ Sensibo  │  │   Tapo   │  │   ntfy   │    │
│  │   API    │  │   API    │  │   API    │  │  (Notif) │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Layers

### iOS Layer (User Interface)

**Purpose:** User interaction and location-based triggers

#### Scriptable Scripts (Automated)
- **Location monitoring** - Background geofencing
- **Offline queueing** - Actions saved when off-network
- **Network detection** - VPN vs local WiFi
- **Status:** Migrating from iOS Shortcuts (see [SCRIPTABLE_MIGRATION.md](./SCRIPTABLE_MIGRATION.md))

**Current Scripts:**
- `home-geofence.js` - Arrival/departure detection (planned)

#### iOS Shortcuts (Manual)
- **Manual triggers** - Voice commands, buttons
- **No background execution** - User-initiated only
- **Direct HTTP calls** - To Flask API endpoints

**Current Shortcuts:**
- Good Morning - Morning routine
- Goodnight - Evening routine
- Manual home/away triggers

**See:** [IOS_AUTOMATION.md](./IOS_AUTOMATION.md) for details

---

### Pi Layer (Automation Engine)

**Purpose:** Home automation logic, device control, scheduling

#### Flask API Server
- **Port:** 5000
- **Endpoints:** Webhook receivers for iOS
- **Dashboard:** Web UI at `/dashboard`
- **Status API:** System health monitoring

**Key Endpoints:**
```
POST /pre-arrival    → triggers pre_arrival.py (Stage 1 - geofence crossing)
POST /im-home        → triggers im_home.py (Stage 2 - WiFi connect)
POST /leaving-home   → triggers leaving_home.py
POST /goodnight      → triggers goodnight.py
POST /good-morning   → triggers good_morning.py
GET  /dashboard      → Web UI
GET  /api/system-status
GET  /api/automation-control
```

**See:** `server/routes.py`

#### Python Automations

**Event-Driven (Webhooks):**
- `pre_arrival.py` - **Stage 1 arrival**: HVAC prep, outdoor lights (~60 sec before home)
- `im_home.py` - **Stage 2 arrival**: Indoor lights, welcome notification (WiFi connect)
- `leaving_home.py` - Secure house, turn off devices
- `goodnight.py` - Sleep mode, turn off lights
- `good_morning.py` - Wake up routine

**Scheduled (Cron):**
- `temp_coordination.py` - Nest + Sensibo coordination (every 15 min)
- ~~`presence_monitor.py`~~ - **DEPRECATED** (replaced by WiFi DHCP + iOS geofencing)

**See:** `automations/` directory

#### Device Components

**Smart Home Devices:**
- `nest/` - Nest thermostat (whole house HVAC)
- `sensibo/` - Sensibo mini-split (bedroom AC)
- `tapo/` - TP-Link Tapo smart outlets (4x)

**System Components:**
- `network/` - Presence detection via ping
- `notifications/` - ntfy.sh push notifications

**Configuration:**
- `config/config.yaml` - Device IPs, settings
- `config/.env` - API credentials (gitignored)

**See:** `components/` directory, [Configuration README](../config/README.md)

---

### External Services Layer

**Cloud APIs:**
- **Nest API** - Thermostat control
- **Sensibo API** - Mini-split AC control
- **Tapo API** - Smart outlet control (local network)
- **ntfy.sh** - Push notifications

**Deferred:**
- Tesla API (see [TESLA_STATUS.md](./TESLA_STATUS.md))

---

## Data Flow Examples

### Example 1: Voice Command → "Hey Siri, I'm leaving"

```
1. User speaks to iPhone/HomePod
   ↓
2. iOS Shortcut triggers
   ↓
3. HTTP POST → http://raspberrypi.local:5000/leaving-home
   ↓
4. Flask spawns subprocess: python3 leaving_home.py
   (Returns 200 OK immediately)
   ↓
5. leaving_home.py executes:
   - Set Nest to away mode (62°F)
   - Turn off all Tapo outlets
   - Turn off Sensibo AC
   ↓
6. Send ntfy notification: "House secured"
   ↓
7. User receives notification on iPhone

Total time: ~2-5 seconds
```

### Example 2: Scheduled Temperature Coordination

```
1. Cron triggers: */15 * * * * temp_coordination.py
   ↓
2. Check presence state (.presence_state file)
   ↓
3. If away: Turn off Sensibo, exit
   ↓
4. Check night mode (.night_mode file)
   ↓
5. If night mode:
   - Read Nest mode (HEAT/COOL/HEATCOOL)
   - Set Sensibo to match Nest mode
   - Set Sensibo target = 66°F
   ↓
6. If day mode:
   - Read Nest target temperature
   - Set Sensibo to match Nest (same temp/mode)
   ↓
7. Send notification if changes made

Total time: ~1-3 seconds
Runs every 15 minutes
```

### Example 3: Two-Stage Arrival Detection (Scriptable + WiFi DHCP)

**Stage 1: Pre-Arrival (Geofence Crossing)**
```
1. iPhone crosses 173m geofence boundary (~60 sec before home)
   ↓
2. iOS triggers Scriptable automation
   ↓
3. home-geofence.js executes:
   - Gets current location
   - Calculates distance (Haversine formula)
   - Confirms within 150m
   ↓
4. HTTP POST → /pre-arrival
   ↓
5. Flask spawns: python3 pre_arrival.py
   ↓
6. pre_arrival.py executes:
   - Set Nest to comfort temp (70°F) - needs 5-15 min lead time
   - Enable Sensibo if night mode (66°F) - needs 10-20 min
   - Turn on outdoor lights if dark (after 6pm)
   - Update .presence_state = "home"
   ↓
7. NO notification sent (waiting for Stage 2)

Stage 1 time: ~2-3 seconds
Lead time before arrival: ~60 seconds
```

**Stage 2: Physical Arrival (WiFi Connect)**
```
1. iPhone connects to home WiFi (~5 sec after entering home)
   ↓
2. WiFi DHCP monitor (systemd service) detects DHCP lease
   ↓
3. Spawns: python3 im_home.py
   ↓
4. im_home.py checks .presence_state:
   - If "home" → Stage 1 already ran, skip HVAC
   - If not "home" → Run Stage 1 first (WiFi-only arrival fallback)
   ↓
5. im_home.py Stage 2 actions:
   - Turn on living room lamp (always)
   - Turn on bedroom lamps if evening (after 6pm)
   - Send "Welcome Home!" notification with action summary
   ↓
6. User receives notification

Stage 2 time: ~2-3 seconds
Total arrival time: ~60-65 seconds (geofence to notification)
```

**WiFi-Only Arrival (Fallback if geofence fails):**
```
1. WiFi connects without geofence trigger
   ↓
2. im_home.py detects .presence_state ≠ "home"
   ↓
3. Calls pre_arrival.run() inline (Stage 1 actions)
   ↓
4. Continues with Stage 2 actions
   ↓
5. Both stages complete in ~3-5 seconds
```

---

## State Management

### File-Based State

**Why files?** Simple, persistent, no database needed.

**State Files:**
- `.presence_state` - Current location (home/away)
- `.night_mode` - Night mode enabled (created by automations)
- `.presence_fail_count` - Consecutive ping failures
- `.alert_state/` - Notification cooldown tracking

**Location:** Project root directory

**Format:** Plain text, one value per file

**Example:**
```bash
# .presence_state
home

# .night_mode
(file exists = night mode on)
```

---

## Scheduling

### Cron Jobs (Pi)

```bash
# Temperature coordination (every 15 minutes)
*/15 * * * * cd /home/matt.wheeler/py_home && python automations/temp_coordination.py

# Presence monitoring (every 5 minutes)
*/5 * * * * cd /home/matt.wheeler/py_home && python automations/presence_monitor.py
```

### iOS Automation (Time-Based)

```
Time-based automation → Every 5-15 minutes
  → Run Scriptable: home-geofence.js
  → Background execution (no user interaction)
```

---

## Configuration

### Layered Configuration System

1. **`config/config.yaml`** - Base configuration (committed to git)
   - Device IPs and names
   - Temperature thresholds
   - Geofence coordinates
   - Default settings

2. **`config/config.local.yaml`** - Local overrides (gitignored, optional)
   - Per-instance customization
   - Testing values
   - Deep merges with base config

3. **`config/.env`** - Sensitive credentials (gitignored)
   - API keys
   - Passwords
   - Auth tokens

**See:** [Configuration README](../config/README.md)

---

## Network Architecture

```
Internet
    │
    ├─ Nest Cloud API
    ├─ Sensibo Cloud API
    └─ ntfy.sh
         ↑
         │ HTTPS
         │
    ┌────┴─────┐
    │  Router  │
    └────┬─────┘
         │
    ┌────┴────────────────────────┐
    │  Home Network (WiFi)         │
    │                              │
    │  ┌──────────────┐            │
    │  │ Raspberry Pi │            │
    │  │ 192.168.50.189 (static)  │
    │  └──────────────┘            │
    │                              │
    │  ┌──────────────────────┐   │
    │  │ Tapo Outlets (4x)    │   │
    │  │ 192.168.50.162, etc. │   │
    │  └──────────────────────┘   │
    │                              │
    │  ┌──────────────┐            │
    │  │ Matt's iPhone│            │
    │  │ (Scriptable) │            │
    │  └──────────────┘            │
    │                              │
    └──────────────────────────────┘
```

**Key Points:**
- Pi has static IP (192.168.50.189)
- Accessible via `raspberrypi.local` (mDNS)
- iOS Shortcuts work on local WiFi only
- Scriptable will work via VPN (future)

**See:** [Configuration README](../config/README.md#network-configuration-raspberry-pi)

---

## Implementation Status

### ✅ Implemented (Production)

**Pi Layer:**
- Flask API server (systemd service)
- Dashboard UI with live status
- Webhook endpoints
- Master automation disable switch
- Notification system (ntfy.sh)
- Logging with kvlog format

**Automations:**
- leaving_home.py
- im_home.py
- goodnight.py
- good_morning.py
- temp_coordination.py (Nest + Sensibo)
- presence_monitor.py (network ping)

**Device Control:**
- Nest thermostat
- Sensibo mini-split
- Tapo outlets (4x)

**iOS:**
- Shortcuts for manual triggers
- Voice commands via Siri

### 🚧 In Progress

**iOS Migration:**
- Scriptable geofencing script (replacing Shortcuts)
- Background location monitoring
- Offline action queueing
- VPN connectivity

**See:** [SCRIPTABLE_MIGRATION.md](./SCRIPTABLE_MIGRATION.md)

### 📋 Planned

**Phase 2:**
- VPN setup (Tailscale or WireGuard)
- Additional Scriptable automations
- Time-based triggers in Scriptable
- Weather-based automation

**Phase 3:**
- Air quality monitoring (future hardware)
- Energy usage tracking
- More device integrations

### ⏸️ Deferred

- Tesla integration (see [TESLA_STATUS.md](./TESLA_STATUS.md))
- Roborock vacuum
- Alen air purifiers

---

## Development Workflow

### On Laptop (Windows)

```bash
# Edit code in VS Code
cd C:\git\cyneta\py_home

# Test changes (most APIs work over internet)
python automations/leaving_home.py --dry-run

# Commit and push
git add .
git commit -m "Add feature"
git push
```

### On Pi (Raspberry Pi)

```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local

# Pull updates
cd ~/py_home
git pull

# Restart Flask if needed
sudo systemctl restart py_home

# Check logs
tail -f data/logs/*.log
```

### For iOS Scripts (Scriptable)

```bash
# Edit on laptop
code /c/Users/matt.wheeler/iCloudDrive/iCloud~dk~simonbs~Scriptable/home-geofence.js

# iCloud syncs automatically (~30 seconds)
# Script appears in Scriptable app on iPhone

# Test in Scriptable app
# Check console output for errors
```

**See:** [IOS_AUTOMATION.md](./IOS_AUTOMATION.md#development-workflow)

---

## Monitoring & Debugging

### Dashboard

**URL:** http://raspberrypi.local:5000/dashboard

**Shows:**
- Nest status (temp, mode, HVAC state)
- Sensibo status (temp, mode, on/off)
- Tapo outlets (on/off state)
- Presence (home/away, last check)
- System status (uptime, night mode, automation state)

**Updates:** Auto-refresh every 5 seconds

### Logs

**Location:** `data/logs/`

**Log Files:**
- `flask.log` - Flask server
- `presence_monitor.log` - Presence detection
- `automation.log` - General automations
- `[automation_name].log` - Individual scripts

**Format:** kvlog (key-value structured logging)

**Example:**
```
2025-10-13T14:30:00 automation=leaving_home event=start dry_run=False
2025-10-13T14:30:01 api=nest action=set_mode mode=away temp=62 result=ok duration_ms=450
```

**See:** [LOGGING.md](./LOGGING.md)

### Notifications

**Service:** ntfy.sh (push notifications)

**Topic:** `py_home_7h3k2m9x`

**Priority Levels:**
- **Default** - Normal status updates
- **High** - Important changes
- **Max** - Errors, alerts

**See:** [NOTIFICATION_DESIGN.md](./NOTIFICATION_DESIGN.md)

---

## Troubleshooting

### Flask Server Not Responding

```bash
# Check service status
sudo systemctl status py_home

# View recent logs
sudo journalctl -u py_home -n 50

# Restart service
sudo systemctl restart py_home
```

### Automation Not Running

1. Check dry-run mode: `grep 'dry_run' config/config.yaml` (should be `false` for production)
2. Check automation logs: `tail -f data/logs/[automation].log` (look for `[DRY-RUN]` messages)
3. Run manually: `python automations/[script].py`
4. Override config: `python automations/[script].py --dry-run` (force dry-run for testing)

### iOS Shortcuts Not Working

1. Check Pi is reachable: `ping raspberrypi.local`
2. Test endpoint: `curl http://raspberrypi.local:5000/status`
3. Check Flask logs for requests
4. Verify WiFi connection (local network only)

### Device Control Not Working

1. Check device API credentials in `.env`
2. Test device component directly
3. Check API rate limits
4. Verify network connectivity

**See:** [DEPLOYMENT.md](./DEPLOYMENT.md#troubleshooting)

---

## Security

### Local Network Only
- Flask server not exposed to internet
- No port forwarding configured
- iOS Shortcuts work on home WiFi only
- Future: VPN for remote access

### Credentials Management
- API keys in `.env` (gitignored)
- Never committed to repository
- Backed up to encrypted storage (1Password)

### Authentication
- Flask endpoints currently open (local network trust)
- Optional: Add basic auth if needed

---

## References

- **Configuration:** [config/README.md](../config/README.md)
- **Deployment:** [DEPLOYMENT.md](./DEPLOYMENT.md)
- **iOS Layer:** [IOS_AUTOMATION.md](./IOS_AUTOMATION.md)
- **Scriptable Migration:** [SCRIPTABLE_MIGRATION.md](./SCRIPTABLE_MIGRATION.md)
- **Notifications:** [NOTIFICATION_DESIGN.md](./NOTIFICATION_DESIGN.md)
- **Logging:** [LOGGING.md](./LOGGING.md)
- **Historical Design:** [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md)

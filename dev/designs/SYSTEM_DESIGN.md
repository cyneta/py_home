# Python-Based Home Automation System Design

**Version**: 1.0
**Date**: 2025-10-06
**Status**: Design Phase

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Equipment & Services](#3-equipment--services)
4. [Use Cases & Workflows](#4-use-cases--workflows)
5. [User Interaction](#5-user-interaction)
6. [Development & Deployment](#6-development--deployment)
7. [Future Considerations](#7-future-considerations)

---

## 1. Project Overview

### 1.1 Motivation

**Why Python + curl/requests instead of n8n?**

- **Code-first approach**: User prefers writing code over visual workflow editors
- **Lightweight**: No Node.js/Docker overhead for workflow engine
- **Direct API control**: Python's `requests` library is simpler than n8n HTTP nodes
- **Version control friendly**: Python files in git vs exported JSON workflows
- **Faster development**: Write/test scripts on laptop, deploy to Pi
- **Minimal dependencies**: Python + standard libraries + `requests`
- **Better debugging**: Stack traces and print statements vs visual node inspection
- **Educational**: Learn APIs directly instead of through abstraction layers

**Core insight**: Most home automation is just HTTP API calls + scheduling + conditional logic. Python does this natively without a heavyweight orchestration platform.

### 1.2 Goals

**Primary Goals**:
1. **Siri voice control** for home automation via iOS Shortcuts → Python webhooks
2. **Automated scenes**: "Leaving Home", "Goodnight", "I'm Home", etc.
3. **Smart Tesla integration**: Climate control, charging, presence detection
4. **Travel intelligence**: Traffic queries, travel time, route conditions
5. **Task management**: Voice-to-Git TODO capture, Checkvist integration
6. **Air quality automation**: Coordinate HVAC + air purifiers based on sensor data

**Secondary Goals**:
- Minimal maintenance (set and forget)
- Low cost (leverage free API tiers)
- Privacy-focused (local processing where possible)
- Extensible (easy to add new devices/workflows)

### 1.3 Non-Goals

**What we're NOT building**:
- ❌ Full HomeKit replacement (may use HomeKit for simple scenes in parallel)
- ❌ Custom mobile app (use iOS Shortcuts + notifications)
- ❌ Real-time dashboard/UI (n8n would be better for this)
- ❌ Multi-user authentication (single-user home automation)
- ❌ Cloud-hosted service (runs locally on Pi)
- ❌ Commercial/production-grade system (personal use, best-effort reliability)

---

## 2. System Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                            │
│                                                              │
│  Siri Voice Commands → iOS Shortcuts → HTTP Webhooks        │
│                                                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Raspberry Pi 4 (24/7)                      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Flask Webhook Server (Port 5000)                    │   │
│  │  - /leaving-home                                     │   │
│  │  - /warm-car                                         │   │
│  │  - /travel-time                                      │   │
│  │  - /add-task                                         │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Python Automation Scripts                           │   │
│  │  - tesla_preheat.py                                  │   │
│  │  - leaving_home.py                                   │   │
│  │  - travel_time.py                                    │   │
│  │  - task_router.py                                    │   │
│  │  - air_quality_monitor.py                           │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│  ┌────────────────────┴─────────────────────────────────┐   │
│  │  Utility Modules                                     │   │
│  │  - tesla_api.py    - nest_api.py                     │   │
│  │  - tapo_api.py     - sensibo_api.py                  │   │
│  │  - notifications.py - google_maps.py                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cron Scheduler                                      │   │
│  │  - 0 7 * * 1-5 → tesla_preheat.py                    │   │
│  │  - */5 * * * * → tesla_presence.py                   │   │
│  │  - */15 * * * * → air_quality_check.py               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  Tesla   │  │   Nest   │  │  Google  │  │ Pushover │    │
│  │   API    │  │   API    │  │   Maps   │  │  (Notif) │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Tapo   │  │ Sensibo  │  │  GitHub  │  │Checkvist │    │
│  │   API    │  │   API    │  │   API    │  │   API    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│                                                              │
│  ┌──────────┐  ┌──────────┐                                 │
│  │  Tuya    │  │  OpenWx  │                                 │
│  │ (Alen)   │  │ (Weather)│                                 │
│  └──────────┘  └──────────┘                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Components

#### 2.2.1 Flask Webhook Server

**Purpose**: Listen for incoming HTTP requests from iOS Shortcuts

**Key Features**:
- Lightweight HTTP server (Flask)
- Runs 24/7 on Pi (systemd service)
- Exposes REST endpoints for each automation
- Async execution (return immediately, run script in background)
- Basic authentication (optional, for security)

**Endpoints**:
```python
POST /leaving-home      → triggers leaving_home.py
POST /warm-car          → triggers tesla_preheat.py
POST /travel-time       → triggers travel_time.py (returns JSON)
POST /add-task          → triggers task_router.py
POST /goodnight         → triggers goodnight.py
POST /im-home           → triggers arrival.py
```

**Why Flask?**:
- Minimal overhead
- Easy to deploy
- Built-in development server
- Production-ready with gunicorn/waitress

#### 2.2.2 Python Automation Scripts

**Purpose**: Execute specific automation workflows

**Design Pattern**:
```python
# leaving_home.py
from utils import nest_api, tapo_api, notifications

def main():
    # Set Nest to away mode
    nest_api.set_mode('away', temp=62)

    # Turn off all outlets
    tapo_api.turn_off_all()

    # Start vacuum (via Roborock API)
    roborock_api.start_cleaning()

    # Send notification
    notifications.send("House secured, cleaning started")

if __name__ == '__main__':
    main()
```

**Key Scripts**:
- `leaving_home.py` - Complete departure routine
- `goodnight.py` - Evening routine
- `tesla_preheat.py` - Smart climate control with weather check
- `tesla_presence.py` - Location-based arrival/departure detection
- `travel_time.py` - Google Maps traffic query
- `task_router.py` - Voice task capture to Git/Checkvist
- `air_quality_monitor.py` - Poll Alen sensors, coordinate HVAC

#### 2.2.3 Utility Modules

**Purpose**: Reusable API clients for external services

**Structure**:
```
utils/
├── __init__.py
├── tesla_api.py          # Tesla API wrapper
├── nest_api.py           # Nest API wrapper
├── tapo_api.py           # Tapo outlet control
├── sensibo_api.py        # Sensibo AC control
├── roborock_api.py       # Vacuum control
├── tuya_api.py           # Alen air purifiers
├── google_maps.py        # Travel time, traffic
├── weather.py            # OpenWeatherMap
├── notifications.py      # Pushover/ntfy.sh
├── github_api.py         # TODO.md commits
├── checkvist_api.py      # Task management
└── config.py             # Load .env, config.yaml
```

**Design Philosophy**:
- Each module = single responsibility
- Clean abstractions (hide API complexity)
- Error handling built-in
- Logging for debugging
- Retry logic for flaky APIs

#### 2.2.4 Scheduler (Cron)

**Purpose**: Time-based automation triggers

**Crontab Examples**:
```bash
# Smart workday pre-heat (7:00 AM Monday-Friday)
0 7 * * 1-5 /usr/bin/python3 /home/pi/automation/scripts/tesla_preheat.py

# Tesla presence detection (every 5 minutes)
*/5 * * * * /usr/bin/python3 /home/pi/automation/scripts/tesla_presence.py

# Air quality monitoring (every 15 minutes)
*/15 * * * * /usr/bin/python3 /home/pi/automation/scripts/air_quality_monitor.py

# Nest + Sensibo coordination (every 15 minutes)
*/15 * * * * /usr/bin/python3 /home/pi/automation/scripts/temp_coordination.py

# Grow light schedule
0 6 * * * /usr/bin/python3 /home/pi/automation/scripts/grow_light.py --on
0 20 * * * /usr/bin/python3 /home/pi/automation/scripts/grow_light.py --off
```

**Alternative**: Python `schedule` library for more complex timing logic

#### 2.2.5 Configuration Management

**Config Files**:
```yaml
# config/config.yaml
tesla:
  email: "user@example.com"
  refresh_token: "${TESLA_REFRESH_TOKEN}"

nest:
  access_token: "${NEST_ACCESS_TOKEN}"
  device_id: "xyz123"

locations:
  home:
    lat: 41.8781
    lng: -87.6298
  milwaukee:
    address: "Milwaukee, WI"

notifications:
  service: "pushover"  # or "ntfy"
  pushover:
    token: "${PUSHOVER_TOKEN}"
    user: "${PUSHOVER_USER}"

tapo:
  outlets:
    - name: "Coffee Maker"
      ip: "192.168.1.100"
    - name: "Grow Light"
      ip: "192.168.1.101"
```

**Environment Variables** (`.env`):
```bash
# Sensitive credentials (not committed to git)
TESLA_REFRESH_TOKEN=abc123
NEST_ACCESS_TOKEN=xyz789
GOOGLE_MAPS_API_KEY=def456
PUSHOVER_TOKEN=ghi789
PUSHOVER_USER=jkl012
```

**Loading**:
```python
# utils/config.py
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Substitute environment variables
def resolve_env(obj):
    if isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
        return os.getenv(obj[2:-1])
    # ... recursive resolution
```

### 2.3 Data Flow

#### Example: "Hey Siri, I'm leaving"

```
1. User speaks to HomePod/iPhone
   ↓
2. Siri recognizes custom shortcut
   ↓
3. iOS Shortcut executes:
   - HTTP POST to http://raspberrypi.local:5000/leaving-home
   ↓
4. Flask webhook receives request:
   - Spawns subprocess: python3 leaving_home.py
   - Returns 200 OK immediately
   ↓
5. leaving_home.py executes:
   - nest_api.set_mode('away', temp=62)
   - tapo_api.turn_off_all()
   - roborock_api.start_cleaning()
   - tesla_api.stop_charging(if_battery_above=80)
   - tesla_api.enable_sentry_mode()
   ↓
6. Each API call:
   - HTTP request to device/service
   - Receive response
   - Log success/failure
   ↓
7. Send notification:
   - notifications.send("House secured")
   ↓
8. User receives notification on iPhone
```

**Timing**: ~2-5 seconds total (most API calls in parallel)

#### Example: Scheduled Tesla Pre-Heat

```
1. Cron triggers at 7:00 AM (Monday-Friday)
   ↓
2. tesla_preheat.py executes:
   - weather.get_current_temp()
   ↓
3. Conditional logic:
   IF temp < 40°F OR precipitation detected:
     ↓
     - tesla_api.get_location()
     - tesla_api.get_battery()
     ↓
     IF at_home AND battery > 30%:
       ↓
       - tesla_api.wake_vehicle()
       - tesla_api.start_climate(temp=72)
       - tesla_api.enable_defrost()
       ↓
       - notifications.send("Car warming, ready in 15 min")
   ELSE:
     - notifications.send("Nice weather, car ready!")
```

---

## 3. Equipment & Services

### 3.1 Hardware

| Device | Purpose | Status | Integration Method |
|--------|---------|--------|-------------------|
| **Raspberry Pi 4 (8GB)** | 24/7 automation server | Ordered | Runs Python scripts |
| **Tesla** | Vehicle climate, charging, location | Owned | Unofficial Tesla API (Python) |
| **Nest Thermostat (3rd gen)** | Whole-house HVAC control | Owned | Nest API (Python requests) |
| **Tapo P125M Outlets** | Smart plugs (coffee, lights, grow light) | Owned | Tapo API (Python library) |
| **Sensibo Air** | Mini-split AC control | Ordered | Sensibo API (Python requests) |
| **Roborock Qrevo Master** | Robot vacuum/mop | Owned | Roborock API (Python library) |
| **Alen BreatheSmart 75i (x2)** | Air quality monitoring/purification | Owned | Tuya API (Python) |
| **HomePods** | Siri voice interface (optional) | Owned | iOS Shortcuts bridge |
| **AirTags** | NFC triggers (optional) | Owned | iOS Shortcuts NFC automation |

### 3.2 External Services & APIs

#### Free Tier APIs (No Cost)

| Service | Purpose | Free Tier Limit | Python Library |
|---------|---------|-----------------|----------------|
| **Tesla API** | Vehicle control | Unlimited (unofficial) | `teslapy`, DIY wrapper |
| **Nest API** | Thermostat control | Unlimited | DIY requests wrapper |
| **Google Maps Distance Matrix** | Travel time queries | 40,000 requests/month | `googlemaps` |
| **OpenWeatherMap** | Weather data | 1,000 calls/day | `pyowm` |
| **GitHub API** | TODO.md commits | 5,000 requests/hour | `PyGithub` |
| **Checkvist API** | Task management | Unlimited (free tier) | DIY requests wrapper |
| **Tuya IoT Platform** | Alen air purifiers | Free tier | `tinytuya` |

#### Paid/One-Time Services

| Service | Purpose | Cost | Python Library |
|---------|---------|------|----------------|
| **Pushover** | iOS notifications | $5 one-time | `python-pushover` |
| **ntfy.sh** | iOS notifications (alternative) | Free (self-host option) | `requests` |

#### Optional Future Services

| Service | Purpose | Cost |
|---------|---------|------|
| **OpenAI API** | AI task classification | ~$0.0001/task |
| **Twilio SMS** | Text alerts | $0.0075/SMS |
| **Google Calendar API** | Calendar-aware automation | Free (personal use) |

### 3.3 Network Architecture

```
Internet
    ├─ Tesla Cloud API
    ├─ Nest Cloud API
    ├─ Google Maps API
    ├─ Pushover API
    └─ GitHub API
         ↑
         │ (HTTPS)
         │
    ┌────┴─────┐
    │  Router  │
    └────┬─────┘
         │
    ┌────┴────────────────────────┐
    │    Local Network (WiFi)      │
    │                              │
    │  ┌──────────────┐            │
    │  │ Raspberry Pi │ (Ethernet) │
    │  │ 192.168.1.50 │            │
    │  └──────────────┘            │
    │                              │
    │  ┌──────────┐  ┌──────────┐ │
    │  │   Tapo   │  │ Sensibo  │ │
    │  │ Outlets  │  │   Air    │ │
    │  └──────────┘  └──────────┘ │
    │                              │
    │  ┌──────────┐  ┌──────────┐ │
    │  │  Alen    │  │ Roborock │ │
    │  │  75i x2  │  │  Vacuum  │ │
    │  └──────────┘  └──────────┘ │
    │                              │
    └──────────────────────────────┘
```

**Key Points**:
- Pi has static IP (192.168.1.50) or `raspberrypi.local` mDNS
- iOS Shortcuts call Pi via local network
- Pi proxies requests to cloud APIs (Tesla, Nest)
- Local devices controlled via LAN (Tapo, Sensibo, Alen, Roborock)

---

## 4. Use Cases & Workflows

### 4.1 Priority Use Cases (MVP - Phase 1)

#### UC-1: "Leaving Home" Scene

**Trigger**: Voice command "Hey Siri, I'm leaving" OR AirTag NFC tap

**Actions**:
1. Set Nest thermostat to away mode (62-65°F)
2. Turn off all Tapo outlets (coffee maker, lamps, etc.)
3. Start Roborock vacuum cleaning
4. Stop Tesla charging (if battery > 80%)
5. Enable Tesla Sentry Mode
6. Send iOS notification: "House secured, cleaning started"

**Script**: `scripts/leaving_home.py`

**Expected Execution Time**: 2-5 seconds

---

#### UC-2: "Warm Up My Car"

**Trigger**: Voice command "Hey Siri, warm up my car"

**Actions**:
1. Wake up Tesla
2. Start climate control (72°F)
3. Enable seat heaters
4. Send notification: "Car warming, ready in 15 min"

**Script**: `scripts/tesla_warm.py`

**Expected Execution Time**: 3-10 seconds (wake is slow)

---

#### UC-3: Travel Time to Milwaukee

**Trigger**: Voice command "Hey Siri, travel time to Milwaukee"

**Actions**:
1. Query Google Maps Distance Matrix API
2. Get current traffic conditions
3. Calculate travel time with traffic
4. Return spoken result via iOS Shortcut: "1 hour 45 minutes in current traffic"

**Script**: `scripts/travel_time.py` (returns JSON to iOS Shortcut)

**Expected Execution Time**: 1-2 seconds

---

#### UC-4: "Goodnight" Scene

**Trigger**: Voice command "Hey Siri, goodnight" OR time-based (10:30 PM)

**Actions**:
1. Set Nest to sleep temperature (68°F)
2. Turn off Sensibo bedroom AC
3. Turn off all Tapo outlets
4. Set Alen air purifiers to Whisper mode (bedroom) and Low (living room)
5. Start Roborock cleaning
6. Send notification: "Goodnight, house secured"

**Script**: `scripts/goodnight.py`

**Expected Execution Time**: 2-5 seconds

---

#### UC-5: Voice Task Capture

**Trigger**: Voice command "Hey Siri, add task [task text]"

**Actions**:
1. iOS Shortcut captures task text via voice dictation
2. Send to webhook: `/add-task` with task text
3. Python script routes task based on keywords:
   - Contains "home" / "automation" / "tesla" → `siri_n8n/TODO.md` (Git commit)
   - Contains "work" / "client" → Checkvist work list
   - Other → Checkvist personal list
4. Send confirmation notification

**Script**: `scripts/task_router.py`

**Expected Execution Time**: 1-3 seconds

---

### 4.2 Planned Use Cases (Phase 2)

#### UC-6: Smart Workday Pre-Heat

**Trigger**: Schedule (7:00 AM Monday-Friday)

**Logic**:
```python
weather = get_current_weather()
if weather.temp < 40 or weather.precipitation:
    tesla_location = tesla.get_location()
    tesla_battery = tesla.get_battery()

    if tesla_location.distance_from_home < 150m and tesla_battery > 30:
        tesla.wake()
        tesla.start_climate(temp=72)
        tesla.enable_defrost()
        tesla.enable_seat_heaters()

        send_notification(f"Car warming. Outside: {weather.temp}°F, ready in 15 min")
else:
    send_notification(f"Nice weather ({weather.temp}°F), car ready!")
```

**Script**: `scripts/tesla_preheat.py`

**Cron**: `0 7 * * 1-5`

---

#### UC-7: Tesla Presence Detection

**Trigger**: Schedule (every 5 minutes)

**Logic**:
```python
tesla_location = tesla.get_location()
distance_from_home = calculate_distance(tesla_location, home_coords)

if distance_from_home < 150 and previous_state == 'away':
    # Just arrived home
    trigger_arrival_scene()
    tesla.start_charging(if_battery_below=80)
    send_notification("Welcome home! Charging started")

elif distance_from_home > 500 and previous_state == 'home':
    # Just left home
    trigger_leaving_scene()
    send_notification("Have a safe trip!")
```

**Script**: `scripts/tesla_presence.py`

**Cron**: `*/5 * * * *`

---

#### UC-8: Temperature Coordination (Nest + Sensibo)

**Trigger**: Schedule (every 15 minutes)

**Logic**:
```python
nest_temp = nest.get_current_temp()

if nest_temp > 76:
    sensibo.turn_on(mode='cool', temp=72)
    send_notification(f"House is {nest_temp}°F, bedroom AC turned on")

elif nest_temp < 74 and sensibo.is_on():
    sensibo.turn_off()
    send_notification(f"House cooled to {nest_temp}°F, bedroom AC turned off")
```

**Script**: `scripts/temp_coordination.py`

**Cron**: `*/15 * * * *`

---

#### UC-9: Air Quality Monitoring & HVAC Coordination

**Trigger**: Schedule (every 15 minutes)

**Logic**:
```python
bedroom_pm25 = alen_bedroom.get_pm25()
living_pm25 = alen_living.get_pm25()
avg_pm25 = (bedroom_pm25 + living_pm25) / 2

if avg_pm25 > 50:  # Moderate pollution
    alen_bedroom.set_mode('turbo')
    alen_living.set_mode('turbo')
    nest.set_fan_mode('on')  # Circulate through HVAC filter
    sensibo.turn_off()  # Don't bring in outside air

    send_notification(f"Poor air quality (PM2.5: {avg_pm25}). Purifiers on Turbo.")

elif avg_pm25 < 25:  # Good air
    alen_bedroom.set_mode('auto')
    alen_living.set_mode('auto')
    nest.set_fan_mode('auto')
```

**Script**: `scripts/air_quality_monitor.py`

**Cron**: `*/15 * * * *`

---

#### UC-10: I-80 Traffic Check

**Trigger**: Voice command "Hey Siri, check I-80"

**Actions**:
1. Query Google Maps Directions API for I-80 West route
2. Parse warnings for construction, accidents, closures
3. Return summary:
   - "✅ I-80 West clear, no construction"
   - "⚠️ Construction at Mile 45, left lane closed, +15 min delay"

**Script**: `scripts/check_i80.py`

**Expected Execution Time**: 1-2 seconds

---

### 4.3 Future Use Cases (Phase 3+)

- Calendar-aware pre-heat (check first meeting time)
- Share ETA with Kate (iMessage via iOS Shortcut)
- "Leaving for Milwaukee" combined scene (traffic + car prep + house secure + ETA share)
- Solar-optimized Tesla charging (if solar panels installed)
- Energy usage tracking (Tapo outlet monitoring)
- Wildfire smoke emergency mode (sustained high PM2.5)
- Seasonal allergy defense (pollen forecast + purifier boost)
- Grow light automation (14-hour cycle, 6 AM - 8 PM)

---

## 5. User Interaction

### 5.1 Siri Voice Commands

**How it works**:
1. User creates iOS Shortcut with custom phrase
2. Shortcut sends HTTP POST to Flask webhook on Pi
3. Pi executes Python script
4. User receives notification when complete

**Example Shortcuts**:

| Voice Command | iOS Shortcut Name | Webhook Endpoint |
|---------------|-------------------|------------------|
| "Hey Siri, I'm leaving" | Leaving Home | `/leaving-home` |
| "Hey Siri, warm up my car" | Warm Car | `/warm-car` |
| "Hey Siri, goodnight" | Goodnight | `/goodnight` |
| "Hey Siri, travel time to Milwaukee" | Travel Time | `/travel-time` |
| "Hey Siri, check I-80" | Check Traffic | `/check-i80` |
| "Hey Siri, add task [text]" | Quick Task | `/add-task` |

**iOS Shortcut Template**:
```
1. Get contents of URL: http://raspberrypi.local:5000/leaving-home
   Method: POST
   Headers: (none, or Authorization if using auth)

2. Show notification: "Running automation..."

3. (Optional) Show result from webhook
```

### 5.2 iOS Shortcuts Design

**Webhook-Based Shortcuts** (Most common):
- Simple HTTP POST to Pi
- No return data needed (fire-and-forget)
- Notification sent from Pi when complete

**Data-Returning Shortcuts** (For queries):
- HTTP POST to Pi, receive JSON response
- Parse JSON and display/speak result
- Example: Travel time query

**Example: Travel Time Shortcut**
```
1. Get contents of URL: http://raspberrypi.local:5000/travel-time
   Method: POST
   Request Body: JSON
   {
     "destination": "Milwaukee, WI"
   }

2. Get dictionary value for "travel_time_minutes" in response

3. Speak text: "Travel time is [travel_time_minutes] minutes"
```

**NFC-Triggered Shortcuts** (Optional):
- Tap AirTag to trigger automation
- Silent execution (no voice needed)
- Useful when leaving/arriving home

### 5.3 Notifications

**Primary Method**: Pushover or ntfy.sh

**Notification Types**:

1. **Action Confirmations**
   - "House secured, cleaning started"
   - "Car warming, ready in 15 min"
   - "Task added to TODO"

2. **Status Updates**
   - "Welcome home! Charging started"
   - "Bedroom AC turned on (house is 77°F)"
   - "Poor air quality detected (PM2.5: 58)"

3. **Alerts**
   - "Tesla battery low (18%)"
   - "Wildfire smoke detected! Stay indoors"
   - "Leave NOW for Milwaukee meeting (heavy traffic)"

**Notification Priorities** (Pushover):
- Low: Routine confirmations (no sound/vibration)
- Normal: Status updates (default)
- High: Alerts requiring attention (bypass quiet hours)
- Emergency: Critical alerts (repeats until acknowledged)

**Python Example**:
```python
# utils/notifications.py
import requests
from utils.config import config

def send(message, title="Home Automation", priority=0):
    """
    Send notification via Pushover

    priority: -2=lowest, -1=low, 0=normal, 1=high, 2=emergency
    """
    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": config['notifications']['pushover']['token'],
        "user": config['notifications']['pushover']['user'],
        "message": message,
        "title": title,
        "priority": priority
    })
```

---

## 6. Development & Deployment

### 6.1 Development Environment (Laptop)

**Platform**: Windows laptop with Git Bash

**Directory Structure**:
```
C:\git\cyneta\siri_n8n\
├── scripts/
│   ├── leaving_home.py
│   ├── goodnight.py
│   ├── tesla_preheat.py
│   ├── tesla_presence.py
│   ├── tesla_warm.py
│   ├── travel_time.py
│   ├── check_i80.py
│   ├── task_router.py
│   ├── air_quality_monitor.py
│   ├── temp_coordination.py
│   └── grow_light.py
│
├── utils/
│   ├── __init__.py
│   ├── tesla_api.py
│   ├── nest_api.py
│   ├── tapo_api.py
│   ├── sensibo_api.py
│   ├── roborock_api.py
│   ├── tuya_api.py
│   ├── google_maps.py
│   ├── weather.py
│   ├── notifications.py
│   ├── github_api.py
│   ├── checkvist_api.py
│   └── config.py
│
├── server/
│   └── webhook_server.py
│
├── config/
│   ├── config.yaml
│   └── .env.example
│
├── tests/
│   ├── test_tesla_api.py
│   ├── test_notifications.py
│   └── ...
│
├── requirements.txt
├── README.md
└── docs/
    ├── SYSTEM_DESIGN.md (this file)
    └── ...
```

**Development Workflow**:
1. Write Python scripts in VS Code or preferred IDE
2. Test API calls directly (Tesla, Google Maps, etc. work over internet)
3. Use `.env` file for API keys (never commit)
4. Run scripts locally: `python scripts/leaving_home.py`
5. Git commit when working
6. Push to GitHub

**Testing on Laptop**:
- All API integrations work over internet (Tesla, Nest, Google Maps, etc.)
- Notifications work (Pushover/ntfy.sh)
- Only limitations: Can't control local devices (Tapo, Sensibo) unless on same network

### 6.2 Production Environment (Pi)

**Platform**: Raspberry Pi 4 (8GB RAM) running Raspberry Pi OS Lite (64-bit)

**Setup Steps**:
1. Flash SD card with Raspberry Pi OS Lite
2. Enable SSH and configure WiFi during imaging
3. Boot Pi, SSH in: `ssh pi@raspberrypi.local`
4. Install Python 3, pip, git: `sudo apt install python3-pip git`
5. Clone repository: `git clone https://github.com/your-repo/siri_n8n.git`
6. Install dependencies: `pip3 install -r requirements.txt`
7. Copy `.env` file with API credentials
8. Test scripts: `python3 scripts/leaving_home.py`
9. Set up Flask webhook server as systemd service
10. Configure cron jobs for scheduled tasks

**Systemd Service for Flask Webhook Server**:
```ini
# /etc/systemd/system/home-automation-webhooks.service
[Unit]
Description=Home Automation Webhook Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/siri_n8n
ExecStart=/usr/bin/python3 /home/pi/siri_n8n/server/webhook_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl enable home-automation-webhooks
sudo systemctl start home-automation-webhooks
sudo systemctl status home-automation-webhooks
```

**Crontab Setup**:
```bash
crontab -e

# Add scheduled tasks
0 7 * * 1-5 /usr/bin/python3 /home/pi/siri_n8n/scripts/tesla_preheat.py
*/5 * * * * /usr/bin/python3 /home/pi/siri_n8n/scripts/tesla_presence.py
*/15 * * * * /usr/bin/python3 /home/pi/siri_n8n/scripts/air_quality_monitor.py
*/15 * * * * /usr/bin/python3 /home/pi/siri_n8n/scripts/temp_coordination.py
0 6 * * * /usr/bin/python3 /home/pi/siri_n8n/scripts/grow_light.py --on
0 20 * * * /usr/bin/python3 /home/pi/siri_n8n/scripts/grow_light.py --off
```

### 6.3 Deployment Process

**Simple Git-Based Deployment**:

```bash
# On laptop: develop and commit
git add scripts/new_feature.py
git commit -m "Add new automation feature"
git push origin main

# On Pi: pull updates
ssh pi@raspberrypi.local
cd ~/siri_n8n
git pull origin main

# Restart webhook server if needed
sudo systemctl restart home-automation-webhooks
```

**Alternative: Automated Deployment Script**:
```bash
# deploy.sh (run on Pi)
#!/bin/bash
cd /home/pi/siri_n8n
git pull origin main
pip3 install -r requirements.txt
sudo systemctl restart home-automation-webhooks
echo "Deployment complete"
```

### 6.4 Configuration Management

**Two-Tier Config**:

1. **`config/config.yaml`** - Non-sensitive settings (committed to Git)
   - Device IDs
   - Locations
   - Thresholds
   - Preferences

2. **`.env`** - Sensitive credentials (NOT committed, .gitignored)
   - API keys
   - Access tokens
   - Passwords

**Config Loading Pattern**:
```python
# utils/config.py
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Substitute ${ENV_VAR} placeholders
def resolve_env_vars(obj):
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
        return os.getenv(obj[2:-1])
    return obj

config = resolve_env_vars(config)
```

**`.env.example`** (committed to Git as template):
```bash
# Copy this file to .env and fill in your credentials

# Tesla
TESLA_REFRESH_TOKEN=

# Nest
NEST_ACCESS_TOKEN=

# Google Maps
GOOGLE_MAPS_API_KEY=

# Notifications
PUSHOVER_TOKEN=
PUSHOVER_USER=

# GitHub (for TODO.md commits)
GITHUB_TOKEN=

# Checkvist
CHECKVIST_USERNAME=
CHECKVIST_API_KEY=
```

---

## 7. Future Considerations

### 7.1 Scaling

**Current Design**: Single Pi, single-threaded Flask, synchronous scripts

**If Performance Becomes an Issue**:
- Move Flask to async framework (FastAPI, Sanic)
- Use task queue (Celery, RQ) for long-running jobs
- Separate webhook server from script execution
- Add caching for API responses (Redis)
- Run multiple workers (gunicorn)

**Estimated Load**:
- ~10-20 webhook calls per day
- ~100-200 scheduled tasks per day
- Total: ~300 Python executions/day
- Well within Pi 4 capabilities

### 7.2 Error Handling & Reliability

**Strategies**:

1. **Retry Logic** (in utility modules)
   ```python
   def api_call_with_retry(func, max_retries=3):
       for attempt in range(max_retries):
           try:
               return func()
           except Exception as e:
               if attempt == max_retries - 1:
                   raise
               time.sleep(2 ** attempt)  # Exponential backoff
   ```

2. **Graceful Degradation**
   - If one API fails, continue with others
   - Log error, send notification, but don't crash

3. **Logging**
   ```python
   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('/var/log/home-automation.log'),
           logging.StreamHandler()
       ]
   )
   ```

4. **Health Checks**
   - Webhook endpoint: `/health` returns 200 OK
   - Cron job monitors webhook server, restarts if down
   - Daily self-test: Send test notification

### 7.3 Logging & Monitoring

**Logging Levels**:
- DEBUG: API requests/responses
- INFO: Script execution, actions taken
- WARNING: Retries, degraded functionality
- ERROR: Failures, exceptions

**Log Rotation**:
```bash
# /etc/logrotate.d/home-automation
/var/log/home-automation.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

**Basic Monitoring**:
- Weekly summary email/notification:
  - Total automations run
  - Success rate
  - Top errors
- Prometheus + Grafana (overkill for this project, but possible)

### 7.4 Backup & Recovery

**What to Back Up**:
- `config/config.yaml` - Device settings
- `.env` - Credentials (encrypted)
- Crontab: `crontab -l > crontab_backup.txt`
- Logs (last 7 days)

**Backup Strategy**:
- Git repository backs up all scripts
- Config files committed to Git (except `.env`)
- `.env` backed up to encrypted cloud storage (1Password, Bitwarden)
- Pi SD card image every 3 months (in case of SD card failure)

**Recovery Plan**:
1. Flash new SD card with Pi OS
2. Clone git repository
3. Restore `.env` from encrypted backup
4. Run setup script (install deps, configure systemd, crontab)
5. Test webhooks and scheduled tasks

### 7.5 Security

**Considerations**:

1. **Webhook Authentication** (Optional)
   - Add API key to webhook calls
   - iOS Shortcut sends `Authorization: Bearer TOKEN` header
   - Prevents unauthorized access if Pi exposed to internet

2. **Local Network Only**
   - Keep Pi on local network (no port forwarding)
   - iOS Shortcuts only work on home WiFi (or VPN)
   - Reduces attack surface

3. **Credentials Management**
   - Never commit `.env` to Git
   - Use environment variables for all secrets
   - Rotate API tokens periodically

4. **HTTPS** (Optional)
   - Use self-signed cert for Flask
   - Or expose via Cloudflare Tunnel for remote access

### 7.6 Testing Strategy

**Unit Tests** (for utility modules):
```python
# tests/test_tesla_api.py
import pytest
from utils import tesla_api

def test_wake_vehicle():
    result = tesla_api.wake_vehicle()
    assert result['state'] == 'online'
```

**Integration Tests** (for complete workflows):
```python
# tests/test_leaving_home.py
def test_leaving_home_workflow():
    # Mock API calls
    with patch('utils.nest_api.set_mode') as mock_nest, \
         patch('utils.tapo_api.turn_off_all') as mock_tapo:

        from scripts import leaving_home
        leaving_home.main()

        mock_nest.assert_called_once_with('away', temp=62)
        mock_tapo.assert_called_once()
```

**Manual Testing**:
- Test each script individually before deployment
- Test webhook endpoints with `curl`:
  ```bash
  curl -X POST http://raspberrypi.local:5000/leaving-home
  ```
- Test scheduled tasks manually:
  ```bash
  python3 scripts/tesla_preheat.py
  ```

---

## Appendix A: Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Hardware** | Raspberry Pi 4 (8GB) | Low power, 24/7 operation, sufficient performance |
| **OS** | Raspberry Pi OS Lite (64-bit) | Lightweight, official support, Debian-based |
| **Language** | Python 3.9+ | Rich library ecosystem, easy API integration |
| **Web Framework** | Flask | Lightweight, simple webhooks, minimal overhead |
| **HTTP Client** | `requests` | De facto standard, simple API |
| **Scheduler** | cron | Built-in, reliable, no dependencies |
| **Config** | YAML + `.env` | Human-readable, env var substitution |
| **Logging** | Python `logging` module | Built-in, flexible, standard |
| **Version Control** | Git + GitHub | Code backup, deployment mechanism |
| **Notifications** | Pushover or ntfy.sh | Reliable, low-cost, simple API |

**Key Python Libraries**:
- `requests` - HTTP client
- `flask` - Webhook server
- `python-dotenv` - Environment variable loading
- `pyyaml` - Config file parsing
- `teslapy` or DIY wrapper - Tesla API
- `googlemaps` - Google Maps API
- `tinytuya` - Tuya/Alen API
- `python-pushover` or `requests` - Notifications

---

## Appendix B: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-10-06 | Use Python instead of n8n | Code-first preference, lighter weight, easier development |
| 2025-10-06 | Flask for webhooks | Lightweight, simple, sufficient for low-volume webhooks |
| 2025-10-06 | cron for scheduling | Built-in, reliable, no additional dependencies |
| 2025-10-06 | Pushover for notifications | $5 one-time, reliable, simple API |
| 2025-10-06 | YAML + .env for config | Separate sensitive/non-sensitive, readable, env var substitution |
| 2025-10-06 | Git-based deployment | Simple, version-controlled, no complex CI/CD needed |

---

**End of Document**

# py_home - Python Home Automation System

**Pure Python home automation** replacing n8n visual workflows with code-first architecture.

Voice control via iOS Shortcuts → Flask webhooks → Python automation scripts → Smart devices

---

## 🚀 Quick Start

### Run the Server
```bash
# Install dependencies
pip install -r requirements.txt

# Start Flask webhook server
python server/app.py

# Server running at http://localhost:5000
```

### Test Endpoints
```bash
# Health check
curl http://localhost:5000/status

# Trigger automation
curl -X POST http://localhost:5000/goodnight

# Get travel time
curl "http://localhost:5000/travel-time?destination=Milwaukee"
```

### Use Components Directly
```python
from components.tapo import turn_on, turn_off
from components.nest import set_temperature
from components.sensibo import turn_on as ac_on
from components.tuya import get_air_quality

# Control devices
turn_on("Heater")
set_temperature(72)
ac_on(mode='cool', target_temp_f=70)

# Monitor air quality
aq = get_air_quality('bedroom')
print(f"PM2.5: {aq['pm25']}, AQI: {aq['aqi']}, Quality: {aq['quality']}")
```

### Run Automations
```bash
# Run automation scripts directly
python automations/leaving_home.py
python automations/goodnight.py
python automations/travel_time.py Milwaukee
```

---

## 📐 Architecture

### Old: n8n/Homebridge
```
Voice → Homebridge → n8n workflows → HTTP calls → Devices
```

### New: py_home
```
Voice → iOS Shortcuts → Flask server → Python scripts → Components → Devices
                            ↓
                    Background execution
                            ↓
                    Push notification
```

**Key Benefits:**
- 🔧 **Code-first** - No visual editor, just Python
- 🧪 **Testable** - pytest, automated testing
- 📦 **Self-contained** - Each device is an independent package
- 🔄 **Version controlled** - git tracks everything
- ⚡ **Fast** - No Docker overhead, native Python

---

## 📁 Project Structure

```
py_home/
├── server/              # Flask webhook server
│   ├── app.py          # Main Flask application
│   ├── routes.py       # 7 webhook endpoints
│   ├── config.py       # Environment configuration
│   ├── README.md       # Server documentation
│   └── py_home.service # Systemd service file
│
├── automations/         # Home automation scripts
│   ├── leaving_home.py         # Away mode (Nest away, outlets off)
│   ├── goodnight.py            # Sleep mode (AC off, outlets off)
│   ├── im_home.py              # Welcome home (Nest comfort)
│   ├── good_morning.py         # Morning routine (weather + Nest)
│   ├── travel_time.py          # Traffic-aware travel time
│   ├── task_router.py          # Smart task routing
│   ├── temp_coordination.py    # HVAC coordination (cron)
│   ├── tempstick_monitor.py    # Temp/humidity monitoring (cron)
│   ├── air_quality_monitor.py  # PM2.5 air quality monitoring (cron)
│   └── presence_monitor.py     # WiFi presence detection (cron)
│
├── components/          # Self-contained device packages
│   ├── tapo/           # TP-Link Tapo smart plugs (4 devices)
│   ├── nest/           # Google Nest thermostat
│   ├── sensibo/        # Sensibo mini-split AC controller
│   ├── tuya/           # Alen air purifiers (Tuya Cloud API)
│   └── network/        # WiFi presence detection
│
├── services/            # External API services
│   ├── google_maps.py  # Travel time & traffic (Google Maps API)
│   ├── openweather.py  # Weather data (OpenWeatherMap API)
│   ├── tempstick.py    # WiFi temperature/humidity sensor API
│   ├── github.py       # Voice task → GitHub commits
│   └── checkvist.py    # Task management (Checkvist API)
│
├── lib/                 # Shared utilities
│   ├── config.py       # Configuration loader (YAML + .env)
│   ├── logging_config.py # Structured logging (RFC 5424-compatible)
│   ├── notifications.py # Push notifications (Pushover/ntfy)
│   └── alert_state.py  # Rate limiting for notifications
│
├── config/              # Configuration
│   ├── config.yaml     # Device configs, thresholds, locations
│   └── .env            # Credentials (gitignored)
│
├── docs/                # Documentation
│   ├── CURL_TESTING_GUIDE.md  # Testing with curl
│   ├── LOGGING.md             # Structured logging guide
│   ├── TAPO_GUIDE.md          # Tapo setup
│   └── TAPO_INTEGRATION.md    # Integration details
│
├── dev/                 # Implementation plans
│   ├── LOGGING_IMPLEMENTATION.md     # Logging system design
│   ├── LOGGING_QUOTING_PLAN.md       # RFC 5424 quoting
│   ├── TUYA_IMPLEMENTATION_PLAN.md   # Tuya integration design
│   └── APPLE_MUSIC_PLAN.md           # Apple Music voice control
│
├── test_all.py          # Comprehensive test suite
├── test_server.py       # Flask endpoint tests
├── MIGRATION_PLAN.md    # Migration roadmap
├── MIGRATION_LOG.md     # Progress tracking
└── SESSION_SUMMARY.md   # Latest session summary
```

---

## 🏠 Devices & Services

### Smart Devices (4 types, 8 devices)
- **Google Nest Thermostat** (1) - Heating/cooling control
- **Sensibo AC Controller** (1) - Bedroom mini-split AC
- **TP-Link Tapo Smart Plugs** (4):
  - Heater (192.168.50.135)
  - Bedroom Right Lamp (192.168.50.143)
  - Livingroom Lamp (192.168.50.162)
  - Bedroom Left Lamp (192.168.50.93)
- **Alen Air Purifiers** (2) - PM2.5/AQI monitoring via Tuya Cloud
  - Bedroom 75i
  - Living Room 75i

### External Services (5 APIs)
- **Google Maps** - Travel time with traffic
- **OpenWeatherMap** - Current weather & forecasts
- **Pushover/ntfy** - Push notifications to phone
- **GitHub** - Voice task commits to TODO.md
- **Checkvist** - Task management lists

### Planned (Hardware-Dependent)
- **Roborock Vacuum** - Cleaning automation
- **Apple Music** - Voice control & automation integration

---

## 🔌 Flask Webhook Server

### Endpoints
```bash
GET  /                    # Health check
GET  /status              # Server status + available endpoints

POST /leaving-home        # Trigger leaving home automation
POST /goodnight           # Trigger goodnight automation
POST /im-home             # Trigger welcome home automation
POST /good-morning        # Trigger morning routine

GET  /travel-time         # Get travel time with traffic (returns JSON)
POST /add-task            # Add task via voice (smart routing)
```

### Features
- ✅ Background script execution (doesn't block)
- ✅ Optional basic authentication
- ✅ Environment-based configuration
- ✅ Systemd service for auto-start
- ✅ Comprehensive error handling

### Example: iOS Shortcut
```
User says: "Hey Siri, I'm leaving"
    ↓
iOS Shortcut sends: POST http://your-server:5000/leaving-home
    ↓
Flask server: Returns 200 OK immediately
    ↓
Background: python automations/leaving_home.py
    ↓
Actions: Nest→away, outlets→off, notification→sent
```

See `server/README.md` for complete server documentation.

---

## 🤖 Automation Scripts

### Home Scenes
- **leaving_home.py** - Set Nest to away (62°F), turn off outlets, notify
- **goodnight.py** - Set Nest to sleep (68°F), turn off AC & outlets, notify
- **im_home.py** - Set Nest to comfort (72°F), welcome notification
- **good_morning.py** - Set Nest to 70°F, get weather, send morning summary

### Intelligence
- **travel_time.py** - Get travel time with traffic (Google Maps API)
- **traffic_alert.py** - Check I-80 for construction/delays
- **task_router.py** - AI-powered task routing (Claude AI + keywords)

### Scheduled (Cron Jobs)
- **temp_coordination.py** - Coordinate Nest + Sensibo every 15 minutes
- **tempstick_monitor.py** - Temperature/humidity alerts every 30 minutes
- **air_quality_monitor.py** - PM2.5 air quality monitoring every 30 minutes
- **presence_monitor.py** - WiFi-based home/away detection every 5 minutes

All scripts include:
- Error handling
- Structured logging
- Notification integration with rate limiting
- Results summary

---

## 🧩 Component Pattern

Each device is a **self-contained package** with clean imports:

```python
# Import what you need
from components.tapo import turn_on, turn_off, get_status
from components.nest import set_temperature, get_status
from components.sensibo import turn_on, turn_off, set_ac_state
from components.tuya import get_air_quality, set_power

from services import get_current_weather, get_travel_time, add_task
from lib.notifications import send, send_high
from lib.logging_config import kvlog

# Use anywhere in your code
turn_on("Heater")
set_temperature(72)
air_quality = get_air_quality("bedroom")  # {'pm25': 15, 'aqi': 55, 'quality': 'good'}
weather = get_current_weather("Portland, OR")
send(f"House is {weather['temp']}°F, PM2.5: {air_quality['pm25']}")

# Structured logging
kvlog(logger, logging.INFO, automation='leaving_home', event='start', dry_run=False)
```

**Component Structure:**
```
components/tapo/
├── __init__.py      # Clean exports
├── client.py        # TapoAPI class
├── demo.py          # Interactive demos
├── test.py          # Smoke tests
├── README.md        # Quick start
├── GUIDE.md         # User guide
└── API.md           # API reference
```

---

## ⚙️ Configuration

### Setup
```bash
# 1. Copy environment template
cp config/.env.example config/.env

# 2. Add credentials to .env
# NEST_PROJECT_ID=...
# SENSIBO_API_KEY=...
# TAPO_USERNAME=...
# etc.

# 3. Update config.yaml with device IPs
nano config/config.yaml
```

### Configuration Files
- **config.yaml** - Device IPs, thresholds, locations (committed to git)
- **.env** - API keys, credentials (gitignored, never committed)

See component READMEs for credential setup.

---

## 🧪 Testing

### Run All Tests
```bash
# Comprehensive test suite with pytest
python -m pytest tests/ -v

# Expected: 115+ passing tests
# ✓ Configuration & config loading
# ✓ All component integrations (Tapo, Nest, Sensibo, Tuya, Temp Stick)
# ✓ Automation workflows
# ✓ Error handling
# ✓ Flask endpoints
# ✓ AI handler
# ✓ Notification system (validation, rate limiting, backends)
# ✓ Logging system (including RFC 5424 quoting)

# Quick smoke test
python test_all.py
```

### Test Flask Server
```bash
# Terminal 1: Start server
python server/app.py

# Terminal 2: Test endpoints
python test_server.py

# Or use curl
curl http://localhost:5000/status
```

### Test Individual Components
```bash
# Component smoke tests
python -m components.tapo.test
python -m components.nest.test
python -m components.sensibo.test

# Interactive demos
python components/tapo/demo.py
```

---

## 🚀 Deployment

### Local Development
```bash
python server/app.py
# Server at http://localhost:5000
```

### Raspberry Pi / Linux Server
```bash
# 1. Copy project to server
scp -r py_home/ pi@raspberrypi:~/

# 2. Install dependencies
cd ~/py_home
pip install -r requirements.txt

# 3. Install systemd service
sudo cp server/py_home.service /etc/systemd/system/
sudo systemctl enable py_home
sudo systemctl start py_home

# 4. Check status
sudo systemctl status py_home
sudo journalctl -u py_home -f
```

### Cron Jobs
```bash
# Edit crontab
crontab -e

# Temperature coordination (every 15 min)
*/15 * * * * cd /home/pi/py_home && python automations/temp_coordination.py

# Temp Stick monitoring (every 30 min)
*/30 * * * * cd /home/pi/py_home && python automations/tempstick_monitor.py

# Air quality monitoring (every 30 min)
*/30 * * * * cd /home/pi/py_home && python automations/air_quality_monitor.py

# Presence detection (every 5 min)
*/5 * * * * cd /home/pi/py_home && python automations/presence_monitor.py

# Good morning (7 AM weekdays)
0 7 * * 1-5 cd /home/pi/py_home && python automations/good_morning.py
```

See `server/README.md` for complete deployment guide.

---

## 📱 iOS Shortcuts Integration

### Automatic Location-Based Triggers (Best)

**Create Automations** (not shortcuts) for automatic presence detection:

```
iOS Shortcuts → Automation tab

1. "When I arrive" at Home
   → Run: POST http://your-server:5000/im-home
   → Turn OFF "Ask Before Running" (automatic)

2. "When I leave" Home
   → Run: POST http://your-server:5000/leaving-home
   → Turn OFF "Ask Before Running" (automatic)
```

**Fully automatic - no "Hey Siri" needed!**

### Manual Voice Shortcuts (Backup)

**"I'm Leaving" Shortcut:**
1. Create new shortcut
2. Add "Get Contents of URL":
   - URL: `http://your-server-ip:5000/leaving-home`
   - Method: POST
3. Add "Show Notification"
4. Activate: "Hey Siri, I'm leaving"

**"Travel Time" Shortcut:**
1. Add "Ask for Input" (destination)
2. Add "Get Contents of URL":
   - URL: `http://your-server-ip:5000/travel-time?destination=[input]`
3. Add "Get Dictionary Value" → `duration_in_traffic_minutes`
4. Add "Speak Text": "Travel time is [value] minutes"

### WiFi Presence Detection (Tertiary Backup)

Automatic monitoring via cron job (runs every 5 minutes):

```bash
# Add to crontab
*/5 * * * * cd /home/pi/py_home && python automations/presence_monitor.py
```

Detects when your iPhone connects/disconnects from home WiFi.

**Three layers of detection = maximum reliability!**

See `server/README.md` and `components/network/README.md` for complete guides.

---

## 📊 System Status

**Architecture:** Pure Python + Flask + iOS Shortcuts (replacing n8n visual workflows)

### ✅ Complete & Tested (97%)
- ✅ 6 device components (Tapo, Nest, Sensibo, Tuya, Temp Stick, Network)
- ✅ 6 services (Maps, Weather, Temp Stick API, Notifications, GitHub, Checkvist)
- ✅ Flask webhook server (7 endpoints)
- ✅ 10 automation scripts (home scenes, monitoring, AI routing, traffic)
- ✅ 115+ passing tests (pytest suite)
- ✅ Notification system with rate limiting
- ✅ Temperature/humidity monitoring (Temp Stick)
- ✅ Air quality monitoring (Tuya/Alen)
- ✅ Structured logging system (RFC 5424-compatible)
- ✅ Systemd service
- ✅ Comprehensive documentation
- ✅ Claude AI integration

### 🚧 Ready to Deploy (3%)
- 🚧 iOS Shortcuts creation (docs ready, user action required)
- 🚧 Production deployment (ready to deploy)
- 🚧 Cron job setup (scripts ready)

### 📋 Planned (2%)
- 📋 Roborock vacuum component (config ready, needs implementation)
- 📋 Apple Music voice control (plan complete, ready to implement)

See `MIGRATION_LOG.md` for detailed progress tracking.

---

## 📚 Documentation

### Getting Started
- **README.md** (this file) - Overview & quick start
- **SESSION_SUMMARY.md** - Latest session accomplishments
- **MIGRATION_PLAN.md** - Complete migration roadmap

### Server & Deployment
- **server/README.md** - Flask server documentation
- **docs/CURL_TESTING_GUIDE.md** - Testing with curl

### Components
- **components/tapo/README.md** - Tapo smart plugs
- **components/nest/README.md** - Nest thermostat
- **components/sensibo/README.md** - Sensibo AC
- **components/tuya/README.md** - Tuya/Alen air purifiers
- **docs/LOGGING.md** - Structured logging guide

### Migration Tracking
- **MIGRATION_LOG.md** - What's been completed
- **MIGRATION_PLAN.md** - 5-week roadmap
- **CONTINUATION_PROMPT.md** - Context for future sessions

---

## 🛠️ Tech Stack

- **Python 3.9+** - Core language
- **Flask 3.1** - Webhook server
- **python-kasa** - Tapo local control (KLAP protocol)
- **tinytuya** - Tuya Cloud API (Alen air purifiers)
- **requests** - REST API calls
- **PyYAML** - Configuration files
- **googlemaps** - Google Maps API client
- **pytest** - Testing framework (115+ tests)

---

## 📋 Next Steps

1. **Create iOS Shortcuts** - Use examples in server/README.md
2. **Deploy to server** - Raspberry Pi or always-on PC
3. **Set up cron jobs** - For scheduled automations
4. **Test end-to-end** - Voice → automation → devices → notification

---

## 🔗 Related Projects

**siri_n8n** - Original n8n workflow project (archived)
- Location: `C:\git\cyneta\siri_n8n\`
- Contains n8n workflows for reference
- py_home replaces this with pure Python

---

## 📧 Contact

Matt Wheeler - matt@wheelers.us

---

**🎉 py_home is production-ready and waiting for iOS Shortcuts integration!**

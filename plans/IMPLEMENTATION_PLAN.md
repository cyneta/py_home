# Python Home Automation - Implementation Plan

**Version**: 1.0
**Date**: 2025-10-06
**Status**: Planning Phase

---

## Table of Contents

1. [Overview](#1-overview)
2. [Phase 0: Foundation (Laptop Development)](#phase-0-foundation-laptop-development)
3. [Phase 1: Core Infrastructure](#phase-1-core-infrastructure)
4. [Phase 2: Essential Automations (MVP)](#phase-2-essential-automations-mvp)
5. [Phase 3: Advanced Automations](#phase-3-advanced-automations)
6. [Phase 4: Polish & Optimization](#phase-4-polish--optimization)
7. [Testing Strategy](#testing-strategy)
8. [Success Criteria](#success-criteria)

---

## 1. Overview

### 1.1 Implementation Approach

**Incremental Development**:
- Build utility modules first (API clients)
- Test each API integration independently
- Create simple scripts, then combine into workflows
- Deploy to Pi only after laptop testing proves functionality

**Development Timeline**:
- **Phase 0**: Before Pi arrives (1-2 weeks) - Build on laptop
- **Phase 1**: Pi setup + infrastructure (Week 1 with Pi)
- **Phase 2**: MVP automations (Weeks 2-3)
- **Phase 3**: Advanced features (Weeks 4-6)
- **Phase 4**: Polish (Ongoing)

### 1.2 Prioritization

**Must Have (MVP)**:
- ✅ Siri voice triggers via webhooks
- ✅ Tesla climate control
- ✅ "Leaving Home" scene
- ✅ Notifications
- ✅ Basic error handling

**Should Have (Phase 3)**:
- ⭐ Scheduled automations (cron)
- ⭐ Tesla presence detection
- ⭐ Air quality monitoring
- ⭐ Task routing to Git/Checkvist

**Nice to Have (Phase 4)**:
- 💡 Advanced error recovery
- 💡 Logging dashboard
- 💡 Performance optimization
- 💡 Comprehensive test coverage

---

## Phase 0: Foundation (Laptop Development)

**Goal**: Build and test core components before Pi arrives

**Timeline**: Start immediately, 1-2 weeks (before Pi hardware arrives)

**Environment**: Windows laptop with Git Bash

---

### Task 0.1: Project Setup

**Acceptance Criteria**:
- [x] `py_home/` directory structure created
- [x] `requirements.txt` with dependencies
- [x] `.env.example` template
- [x] `config.yaml` with placeholder values
- [x] `.gitignore` protecting credentials
- [ ] Git repository initialized
- [ ] First commit pushed to GitHub

**Steps**:
```bash
cd py_home
git init
git add .
git commit -m "Initial py_home project setup"
git remote add origin <your-repo-url>
git push -u origin main
```

**Estimated Time**: 15 minutes ✅ (mostly complete)

---

### Task 0.2: Configuration System

**File**: `utils/config.py`

**Acceptance Criteria**:
- [ ] Loads `config.yaml` with YAML parser
- [ ] Loads `.env` with python-dotenv
- [ ] Substitutes `${ENV_VAR}` placeholders in config.yaml
- [ ] Raises clear error if required env vars missing
- [ ] Provides `config` dict accessible to all modules
- [ ] Unit test validates config loading

**Implementation**:
```python
# utils/config.py
import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / 'config' / '.env')

# Load config.yaml
with open(project_root / 'config' / 'config.yaml') as f:
    config = yaml.safe_load(f)

def resolve_env_vars(obj):
    """Recursively replace ${VAR} with env var values"""
    if isinstance(obj, dict):
        return {k: resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        if obj.startswith('${') and obj.endswith('}'):
            var_name = obj[2:-1]
            value = os.getenv(var_name)
            if value is None:
                raise ValueError(f"Missing environment variable: {var_name}")
            return value
    return obj

config = resolve_env_vars(config)
```

**Test**:
```python
# tests/test_config.py
from utils.config import config

def test_config_loads():
    assert config is not None
    assert 'tesla' in config
    assert 'notifications' in config

def test_env_var_substitution():
    # Assumes .env has PUSHOVER_TOKEN set
    assert not config['notifications']['pushover']['token'].startswith('${')
```

**Estimated Time**: 1 hour

---

### Task 0.3: Notifications Module

**File**: `utils/notifications.py`

**Acceptance Criteria**:
- [ ] Sends notification via Pushover
- [ ] Falls back to ntfy.sh if Pushover not configured
- [ ] Supports priority levels (low, normal, high, emergency)
- [ ] Handles API errors gracefully
- [ ] Manual test sends notification to phone

**Implementation**:
```python
# utils/notifications.py
import requests
import logging
from utils.config import config

logger = logging.getLogger(__name__)

def send(message, title="Home Automation", priority=0):
    """
    Send notification to user's phone

    Args:
        message: Notification text
        title: Notification title
        priority: -2=lowest, -1=low, 0=normal, 1=high, 2=emergency
    """
    service = config['notifications']['service']

    try:
        if service == 'pushover':
            _send_pushover(message, title, priority)
        elif service == 'ntfy':
            _send_ntfy(message, title, priority)
        else:
            logger.error(f"Unknown notification service: {service}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")

def _send_pushover(message, title, priority):
    resp = requests.post("https://api.pushover.net/1/messages.json", data={
        "token": config['notifications']['pushover']['token'],
        "user": config['notifications']['pushover']['user'],
        "message": message,
        "title": title,
        "priority": priority
    }, timeout=10)
    resp.raise_for_status()
    logger.info(f"Pushover notification sent: {title}")

def _send_ntfy(message, title, priority):
    # ntfy.sh implementation
    topic = config['notifications']['ntfy']['topic']
    requests.post(f"https://ntfy.sh/{topic}",
        data=f"{title}: {message}".encode('utf-8'),
        timeout=10
    )
    logger.info(f"ntfy notification sent: {title}")
```

**Test**:
```bash
# Create .env with Pushover credentials
python -c "from utils.notifications import send; send('Test notification from py_home')"
# Check phone for notification
```

**Estimated Time**: 1 hour

---

### Task 0.4: Tesla API Client

**File**: `utils/tesla_api.py`

**Acceptance Criteria**:
- [ ] Authenticate with Tesla API (refresh token flow)
- [ ] Wake vehicle
- [ ] Get vehicle location
- [ ] Get battery level
- [ ] Start/stop climate control
- [ ] Enable/disable defrost
- [ ] Enable/disable sentry mode
- [ ] Start/stop charging
- [ ] Handles "vehicle asleep" errors with retry
- [ ] Manual test successfully warms car

**Implementation**:
```python
# utils/tesla_api.py
import requests
import time
import logging
from utils.config import config

logger = logging.getLogger(__name__)

class TeslaAPI:
    BASE_URL = "https://owner-api.teslamotors.com/api/1"

    def __init__(self):
        self.access_token = None
        self.vehicle_id = None
        self._authenticate()

    def _authenticate(self):
        """Get access token from refresh token"""
        # Tesla OAuth implementation
        # Use refresh token from config
        pass

    def wake_vehicle(self, max_retries=5):
        """Wake vehicle from sleep"""
        for i in range(max_retries):
            resp = self._post(f"/vehicles/{self.vehicle_id}/wake_up")
            if resp['state'] == 'online':
                logger.info("Vehicle is awake")
                return True
            time.sleep(5)
        raise Exception("Failed to wake vehicle")

    def get_location(self):
        """Get current vehicle location"""
        data = self._get(f"/vehicles/{self.vehicle_id}/vehicle_data")
        return {
            'lat': data['drive_state']['latitude'],
            'lng': data['drive_state']['longitude']
        }

    def get_battery(self):
        """Get battery level percentage"""
        data = self._get(f"/vehicles/{self.vehicle_id}/vehicle_data")
        return data['charge_state']['battery_level']

    def start_climate(self, temp_c=22):
        """Start HVAC system"""
        self._post(f"/vehicles/{self.vehicle_id}/command/auto_conditioning_start")
        self._post(f"/vehicles/{self.vehicle_id}/command/set_temps", {
            'driver_temp': temp_c,
            'passenger_temp': temp_c
        })
        logger.info(f"Climate started, target: {temp_c}°C")

    def enable_defrost(self):
        """Enable max defrost mode"""
        self._post(f"/vehicles/{self.vehicle_id}/command/set_preconditioning_max", {
            'on': True
        })

    # ... more methods

    def _get(self, endpoint):
        """GET request with auth"""
        resp = requests.get(f"{self.BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()['response']

    def _post(self, endpoint, data=None):
        """POST request with auth"""
        resp = requests.post(f"{self.BASE_URL}{endpoint}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            json=data,
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()['response']

# Singleton instance
tesla = TeslaAPI()
```

**Test**:
```bash
python -c "from utils.tesla_api import tesla; tesla.wake_vehicle(); print('Battery:', tesla.get_battery(), '%')"
```

**Estimated Time**: 3-4 hours (Tesla API is complex)

**Note**: Consider using `teslapy` library instead of DIY wrapper to save time

---

### Task 0.5: Google Maps API Client

**File**: `utils/google_maps.py`

**Acceptance Criteria**:
- [ ] Get travel time between two locations
- [ ] Get current traffic conditions
- [ ] Parse construction/incident warnings
- [ ] Returns JSON with travel_time_minutes, traffic_level, warnings
- [ ] Manual test returns accurate I-80 traffic

**Implementation**:
```python
# utils/google_maps.py
import googlemaps
from datetime import datetime
from utils.config import config

gmaps = googlemaps.Client(key=config['google_maps']['api_key'])

def get_travel_time(origin, destination):
    """
    Get travel time with current traffic

    Returns:
        {
            'distance_miles': float,
            'travel_time_minutes': int,
            'travel_time_text': str,
            'traffic_level': 'light' | 'moderate' | 'heavy'
        }
    """
    result = gmaps.distance_matrix(
        origins=origin,
        destinations=destination,
        mode="driving",
        departure_time="now"
    )

    element = result['rows'][0]['elements'][0]

    if element['status'] != 'OK':
        raise Exception(f"Maps API error: {element['status']}")

    duration = element['duration']['value']  # seconds
    duration_traffic = element.get('duration_in_traffic', {}).get('value', duration)

    # Determine traffic level
    delay_ratio = duration_traffic / duration
    if delay_ratio < 1.1:
        traffic = 'light'
    elif delay_ratio < 1.3:
        traffic = 'moderate'
    else:
        traffic = 'heavy'

    return {
        'distance_miles': element['distance']['value'] / 1609.34,
        'travel_time_minutes': duration_traffic // 60,
        'travel_time_text': element['duration_in_traffic']['text'],
        'traffic_level': traffic
    }

def check_route_warnings(origin, destination):
    """Check for construction, accidents on route"""
    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        departure_time="now"
    )

    warnings = []
    if directions:
        for warning in directions[0].get('warnings', []):
            warnings.append(warning)

    return warnings
```

**Test**:
```bash
python -c "from utils.google_maps import get_travel_time; print(get_travel_time('Chicago, IL', 'Milwaukee, WI'))"
```

**Estimated Time**: 2 hours

---

### Task 0.6: Weather API Client

**File**: `utils/weather.py`

**Acceptance Criteria**:
- [ ] Get current temperature
- [ ] Get precipitation status
- [ ] Returns simple dict with temp_f, precipitation, conditions
- [ ] Manual test returns current Chicago weather

**Implementation**:
```python
# utils/weather.py
import requests
from utils.config import config

def get_current_weather(lat=None, lng=None):
    """
    Get current weather for location

    Returns:
        {
            'temp_f': float,
            'temp_c': float,
            'precipitation': bool,
            'conditions': str (e.g., 'Clear', 'Rain', 'Snow')
        }
    """
    if lat is None:
        lat = config['locations']['home']['lat']
        lng = config['locations']['home']['lng']

    api_key = config['openweather']['api_key']
    url = f"https://api.openweathermap.org/data/2.5/weather"

    resp = requests.get(url, params={
        'lat': lat,
        'lon': lng,
        'appid': api_key,
        'units': 'imperial'
    }, timeout=10)

    resp.raise_for_status()
    data = resp.json()

    # Check for precipitation
    weather_id = data['weather'][0]['id']
    precipitation = 200 <= weather_id < 700  # Rain, snow, etc.

    return {
        'temp_f': data['main']['temp'],
        'temp_c': (data['main']['temp'] - 32) * 5/9,
        'precipitation': precipitation,
        'conditions': data['weather'][0]['main']
    }
```

**Test**:
```bash
python -c "from utils.weather import get_current_weather; print(get_current_weather())"
```

**Estimated Time**: 1 hour

---

### Task 0.7: First Automation Script - Tesla Pre-Heat

**File**: `scripts/tesla_preheat.py`

**Acceptance Criteria**:
- [ ] Checks current weather
- [ ] Only pre-heats if temp < 40°F or precipitation
- [ ] Verifies Tesla is at home
- [ ] Verifies battery > 30%
- [ ] Wakes vehicle and starts climate
- [ ] Sends notification with status
- [ ] Can be run manually from laptop
- [ ] Handles errors gracefully (logs + notification)

**Implementation**:
```python
#!/usr/bin/env python3
# scripts/tesla_preheat.py

import logging
from utils import tesla_api, weather, notifications, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Smart Tesla pre-heat based on weather"""
    try:
        # Get current weather
        wx = weather.get_current_weather()
        logger.info(f"Current weather: {wx['temp_f']}°F, {wx['conditions']}")

        # Check if pre-heat needed
        cold_threshold = config.config['automation']['tesla_preheat']['cold_threshold_f']

        if wx['temp_f'] >= cold_threshold and not wx['precipitation']:
            msg = f"Nice weather ({wx['temp_f']}°F), car ready!"
            logger.info(msg)
            notifications.send(msg)
            return

        # Check Tesla location
        tesla = tesla_api.tesla
        location = tesla.get_location()

        # Calculate distance from home
        from math import radians, sin, cos, sqrt, atan2
        home = config.config['locations']['home']

        # Haversine formula
        lat1, lng1 = radians(home['lat']), radians(home['lng'])
        lat2, lng2 = radians(location['lat']), radians(location['lng'])
        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance_m = 6371000 * c  # Earth radius in meters

        if distance_m > 500:
            msg = f"Car is away ({distance_m:.0f}m from home), skipping pre-heat"
            logger.info(msg)
            notifications.send(msg)
            return

        # Check battery
        battery = tesla.get_battery()
        min_battery = config.config['automation']['tesla_preheat']['min_battery_percent']

        if battery < min_battery:
            msg = f"Battery too low ({battery}%), skipping pre-heat"
            logger.warning(msg)
            notifications.send(msg, priority=1)
            return

        # All checks passed - pre-heat!
        logger.info(f"Pre-heating car (weather: {wx['temp_f']}°F, battery: {battery}%)")

        tesla.wake_vehicle()
        target_temp_f = config.config['automation']['tesla_preheat']['target_temp_f']
        target_temp_c = (target_temp_f - 32) * 5/9

        tesla.start_climate(temp_c=target_temp_c)

        if wx['temp_f'] < 32 or wx['precipitation']:
            tesla.enable_defrost()

        msg = f"🚗 Car warming! Outside: {wx['temp_f']}°F, ready in 15 min (Battery: {battery}%)"
        notifications.send(msg)
        logger.info("Pre-heat complete")

    except Exception as e:
        logger.error(f"Pre-heat failed: {e}", exc_info=True)
        notifications.send(f"⚠️ Tesla pre-heat error: {str(e)}", priority=1)

if __name__ == '__main__':
    main()
```

**Test**:
```bash
# Run manually
python scripts/tesla_preheat.py

# Should:
# 1. Check weather
# 2. Check Tesla location/battery
# 3. Pre-heat if conditions met OR send notification explaining why not
# 4. You receive notification on phone
```

**Estimated Time**: 2 hours

---

### Phase 0 Summary

**Total Estimated Time**: 10-15 hours

**Deliverables**:
- ✅ Project structure
- ✅ Configuration system
- ✅ Notifications working
- ✅ Tesla API client functional
- ✅ Google Maps integration
- ✅ Weather API integration
- ✅ First complete automation (tesla_preheat.py)

**At this point**: You can develop and test automations entirely on your laptop before Pi arrives!

---

## Phase 1: Core Infrastructure

**Goal**: Set up Raspberry Pi and deploy working webhook server

**Timeline**: Week 1 after Pi arrives

**Prerequisites**: Phase 0 complete, Pi hardware arrived

---

### Task 1.1: Raspberry Pi Initial Setup

**Acceptance Criteria**:
- [ ] Raspberry Pi OS Lite flashed to SD card
- [ ] SSH enabled, WiFi configured
- [ ] Pi boots and accessible via `ssh pi@raspberrypi.local`
- [ ] Static IP configured (optional but recommended)
- [ ] System updated: `sudo apt update && sudo apt upgrade`

**Steps**:
```bash
# On Windows laptop:
# 1. Download Raspberry Pi Imager
# 2. Flash "Raspberry Pi OS Lite (64-bit)"
# 3. Configure WiFi and enable SSH in imager settings
# 4. Insert SD card into Pi and power on

# SSH into Pi
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3-pip git -y

# Set static IP (optional)
# Edit /etc/dhcpcd.conf
```

**Estimated Time**: 1 hour

---

### Task 1.2: Deploy Code to Pi

**Acceptance Criteria**:
- [ ] Git repository cloned to `/home/pi/py_home`
- [ ] Python dependencies installed
- [ ] `.env` file copied with credentials
- [ ] Config loaded successfully
- [ ] Test script runs: `python3 scripts/tesla_preheat.py`

**Steps**:
```bash
# On Pi
cd ~
git clone https://github.com/your-username/siri_n8n.git
cd siri_n8n/py_home

# Install dependencies
pip3 install -r requirements.txt

# Copy .env (from laptop via scp or manual editing)
nano config/.env
# Paste credentials

# Test
python3 -c "from utils.config import config; print('Config loaded:', config['notifications']['service'])"
python3 -c "from utils.notifications import send; send('Pi is online!')"
```

**Estimated Time**: 30 minutes

---

### Task 1.3: Flask Webhook Server

**File**: `server/webhook_server.py`

**Acceptance Criteria**:
- [ ] Flask server listens on 0.0.0.0:5000
- [ ] Endpoints: `/leaving-home`, `/warm-car`, `/travel-time`, `/health`
- [ ] Each endpoint spawns subprocess to run script
- [ ] Returns 200 OK immediately (async execution)
- [ ] `/health` endpoint returns system status
- [ ] Manual test with curl succeeds

**Implementation**:
```python
#!/usr/bin/env python3
# server/webhook_server.py

from flask import Flask, request, jsonify
import subprocess
import logging
from pathlib import Path

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / 'scripts'

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'py_home webhook server'
    })

@app.route('/leaving-home', methods=['POST'])
def leaving_home():
    """Trigger leaving home automation"""
    logger.info("Received leaving-home trigger")
    _run_script('leaving_home.py')
    return jsonify({'status': 'triggered', 'script': 'leaving_home.py'})

@app.route('/warm-car', methods=['POST'])
def warm_car():
    """Trigger Tesla pre-heat"""
    logger.info("Received warm-car trigger")
    _run_script('tesla_warm.py')
    return jsonify({'status': 'triggered', 'script': 'tesla_warm.py'})

@app.route('/travel-time', methods=['POST'])
def travel_time():
    """Get travel time to destination"""
    logger.info("Received travel-time query")

    # This one returns data instead of just triggering
    data = request.get_json() or {}
    destination = data.get('destination', 'Milwaukee, WI')

    # Run script and capture output
    result = subprocess.run(
        ['python3', str(SCRIPTS_DIR / 'travel_time.py'), destination],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode == 0:
        import json
        return jsonify(json.loads(result.stdout))
    else:
        logger.error(f"travel_time.py failed: {result.stderr}")
        return jsonify({'error': 'Script failed'}), 500

@app.route('/goodnight', methods=['POST'])
def goodnight():
    """Trigger goodnight automation"""
    logger.info("Received goodnight trigger")
    _run_script('goodnight.py')
    return jsonify({'status': 'triggered', 'script': 'goodnight.py'})

def _run_script(script_name):
    """Run automation script in background"""
    script_path = SCRIPTS_DIR / script_name

    # Run in background (don't wait for completion)
    subprocess.Popen(
        ['python3', str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    logger.info(f"Started {script_name}")

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Test**:
```bash
# On Pi
python3 server/webhook_server.py

# On laptop (or another terminal on Pi)
curl -X POST http://raspberrypi.local:5000/health
curl -X POST http://raspberrypi.local:5000/warm-car

# Should receive notification on phone
```

**Estimated Time**: 2 hours

---

### Task 1.4: Systemd Service for Webhook Server

**Acceptance Criteria**:
- [ ] Webhook server runs as systemd service
- [ ] Starts automatically on boot
- [ ] Restarts on failure
- [ ] Logs to systemd journal
- [ ] `systemctl status py-home-webhooks` shows running

**Implementation**:
```bash
# Create systemd service file
sudo nano /etc/systemd/system/py-home-webhooks.service
```

```ini
[Unit]
Description=Python Home Automation Webhook Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/siri_n8n/py_home
ExecStart=/usr/bin/python3 /home/pi/siri_n8n/py_home/server/webhook_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable py-home-webhooks
sudo systemctl start py-home-webhooks
sudo systemctl status py-home-webhooks

# Test
curl -X POST http://localhost:5000/health

# View logs
sudo journalctl -u py-home-webhooks -f
```

**Estimated Time**: 30 minutes

---

### Task 1.5: First iOS Shortcut

**Acceptance Criteria**:
- [ ] iOS Shortcut created: "Warm Car"
- [ ] Calls `http://raspberrypi.local:5000/warm-car`
- [ ] Siri phrase: "Hey Siri, warm up my car"
- [ ] End-to-end test: Voice command → webhook → script → notification

**Steps**:
1. Open Shortcuts app on iPhone
2. Create new shortcut
3. Add action: "Get contents of URL"
   - URL: `http://raspberrypi.local:5000/warm-car`
   - Method: POST
4. Add to Siri: "Warm up my car"
5. Test: "Hey Siri, warm up my car"
6. Should receive notification within 30 seconds

**Estimated Time**: 15 minutes

---

### Phase 1 Summary

**Total Estimated Time**: 4-5 hours

**Deliverables**:
- ✅ Pi running and accessible
- ✅ Code deployed
- ✅ Webhook server running as service
- ✅ First Siri voice command working end-to-end

**Milestone**: Can trigger Python scripts via Siri voice commands!

---

## Phase 2: Essential Automations (MVP)

**Goal**: Build core automation workflows

**Timeline**: Weeks 2-3 after Pi arrives

---

### Task 2.1: Additional API Clients

Build remaining API wrappers:

**Files to create**:
- [ ] `utils/nest_api.py` - Thermostat control
- [ ] `utils/tapo_api.py` - Smart outlet control
- [ ] `utils/sensibo_api.py` - Mini-split AC control
- [ ] `utils/roborock_api.py` - Vacuum control

**Acceptance Criteria** (for each):
- [ ] Authentication works
- [ ] Basic control functions implemented
- [ ] Error handling with retries
- [ ] Manual test from laptop/Pi succeeds

**Estimated Time**: 6-8 hours total (1.5-2 hours each)

---

### Task 2.2: "Leaving Home" Automation

**File**: `scripts/leaving_home.py`

**Acceptance Criteria**:
- [ ] Sets Nest to away mode (62°F)
- [ ] Turns off all Tapo outlets
- [ ] Starts Roborock cleaning
- [ ] Stops Tesla charging if battery > 80%
- [ ] Enables Tesla Sentry Mode
- [ ] Sends notification: "House secured, cleaning started"
- [ ] Handles partial failures gracefully
- [ ] iOS Shortcut created with Siri phrase

**Implementation Pattern**:
```python
#!/usr/bin/env python3
# scripts/leaving_home.py

import logging
from utils import nest_api, tapo_api, roborock_api, tesla_api, notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Complete leaving home automation"""
    errors = []

    try:
        # Nest to away mode
        nest_api.nest.set_mode('away', temp=62)
        logger.info("Nest set to away mode")
    except Exception as e:
        logger.error(f"Nest failed: {e}")
        errors.append("thermostat")

    try:
        # Turn off all outlets
        tapo_api.turn_off_all()
        logger.info("All outlets turned off")
    except Exception as e:
        logger.error(f"Tapo failed: {e}")
        errors.append("outlets")

    # ... similar for other devices

    # Send notification
    if errors:
        msg = f"⚠️ House secured (errors: {', '.join(errors)})"
        notifications.send(msg, priority=1)
    else:
        msg = "✅ House secured, cleaning started"
        notifications.send(msg)

if __name__ == '__main__':
    main()
```

**Estimated Time**: 2 hours

---

### Task 2.3: "Goodnight" Automation

**File**: `scripts/goodnight.py`

**Acceptance Criteria**:
- [ ] Sets Nest to sleep temp (68°F)
- [ ] Turns off Sensibo AC
- [ ] Turns off all outlets
- [ ] Starts Roborock cleaning
- [ ] Sends notification
- [ ] iOS Shortcut + Siri phrase
- [ ] Optional: Time-based trigger (10:30 PM cron)

**Estimated Time**: 1.5 hours

---

### Task 2.4: "Travel Time" Query

**File**: `scripts/travel_time.py`

**Acceptance Criteria**:
- [ ] Takes destination as command-line arg
- [ ] Queries Google Maps API
- [ ] Returns JSON with travel time
- [ ] iOS Shortcut speaks result
- [ ] Siri phrase: "Hey Siri, travel time to Milwaukee"

**Implementation**:
```python
#!/usr/bin/env python3
# scripts/travel_time.py

import sys
import json
from utils import google_maps, config

def main():
    destination = sys.argv[1] if len(sys.argv) > 1 else "Milwaukee, WI"
    origin = config.config['locations']['home']
    origin_str = f"{origin['lat']},{origin['lng']}"

    result = google_maps.get_travel_time(origin_str, destination)

    # Print JSON for iOS Shortcut to parse
    print(json.dumps(result))

if __name__ == '__main__':
    main()
```

**iOS Shortcut**:
- Get URL (POST to /travel-time)
- Parse JSON response
- Speak: "Travel time is [X] minutes with [traffic_level] traffic"

**Estimated Time**: 1 hour

---

### Task 2.5: "Tesla Warm" (On-Demand)

**File**: `scripts/tesla_warm.py`

**Acceptance Criteria**:
- [ ] Wakes Tesla
- [ ] Starts climate immediately (no weather check)
- [ ] Sends notification
- [ ] Siri phrase: "Hey Siri, warm up my car"

**Estimated Time**: 30 minutes (reuse tesla_preheat.py logic)

---

### Phase 2 Summary

**Total Estimated Time**: 12-15 hours

**Deliverables**:
- ✅ All device API clients working
- ✅ 4 core automations: Leaving Home, Goodnight, Travel Time, Warm Car
- ✅ iOS Shortcuts for each
- ✅ End-to-end Siri voice control

**Milestone**: MVP complete! Daily home automation working.

---

## Phase 3: Advanced Automations

**Goal**: Scheduled tasks, presence detection, air quality

**Timeline**: Weeks 4-6

---

### Task 3.1: Cron-Based Scheduling

**Acceptance Criteria**:
- [ ] Crontab configured on Pi
- [ ] Tesla pre-heat runs 7 AM weekdays
- [ ] Grow light turns on 6 AM, off 8 PM daily
- [ ] Logs working (check `/var/log/syslog` or script output)

**Crontab**:
```bash
crontab -e

# Tesla pre-heat (7 AM Monday-Friday)
0 7 * * 1-5 /usr/bin/python3 /home/pi/siri_n8n/py_home/scripts/tesla_preheat.py >> /var/log/py_home_cron.log 2>&1

# Grow light on (6 AM daily)
0 6 * * * /usr/bin/python3 /home/pi/siri_n8n/py_home/scripts/grow_light.py --on >> /var/log/py_home_cron.log 2>&1

# Grow light off (8 PM daily)
0 20 * * * /usr/bin/python3 /home/pi/siri_n8n/py_home/scripts/grow_light.py --off >> /var/log/py_home_cron.log 2>&1
```

**Estimated Time**: 1 hour

---

### Task 3.2: Tesla Presence Detection

**File**: `scripts/tesla_presence.py`

**Acceptance Criteria**:
- [ ] Runs every 5 minutes (cron)
- [ ] Checks Tesla location
- [ ] Detects arrival (triggers "I'm Home" scene)
- [ ] Detects departure (triggers "Leaving Home" scene)
- [ ] Stores state in `/tmp/tesla_presence_state.json`
- [ ] Only triggers once per state change

**Estimated Time**: 2 hours

---

### Task 3.3: Temperature Coordination (Nest + Sensibo)

**File**: `scripts/temp_coordination.py`

**Acceptance Criteria**:
- [ ] Runs every 15 minutes
- [ ] Reads Nest current temp
- [ ] Turns on Sensibo if temp > 76°F
- [ ] Turns off Sensibo if temp < 74°F
- [ ] Sends notification on state change

**Estimated Time**: 1.5 hours

---

### Task 3.4: Air Quality Monitoring

**File**: `scripts/air_quality_monitor.py`

**Acceptance Criteria**:
- [ ] Queries both Alen 75i units via Tuya API
- [ ] Gets PM2.5, TVOC readings
- [ ] Coordinates with Nest/Sensibo if poor air quality
- [ ] Sends alert if PM2.5 > 50
- [ ] Runs every 15 minutes

**Prerequisites**:
- [ ] `utils/tuya_api.py` created
- [ ] Tuya developer account set up
- [ ] Alen devices linked to Tuya

**Estimated Time**: 3-4 hours (Tuya setup is complex)

---

### Task 3.5: Task Routing (Voice to Git/Checkvist)

**File**: `scripts/task_router.py`

**Acceptance Criteria**:
- [ ] Receives task text from iOS Shortcut
- [ ] Routes based on keywords
- [ ] Commits to `TODO.md` for home automation tasks
- [ ] Adds to Checkvist for work/personal tasks
- [ ] Sends confirmation notification
- [ ] Siri phrase: "Hey Siri, add task [text]"

**Prerequisites**:
- [ ] `utils/github_api.py` created
- [ ] `utils/checkvist_api.py` created

**Estimated Time**: 3 hours

---

### Phase 3 Summary

**Total Estimated Time**: 10-12 hours

**Deliverables**:
- ✅ Scheduled automations running
- ✅ Tesla presence detection
- ✅ Multi-device coordination
- ✅ Air quality monitoring
- ✅ Voice task capture

**Milestone**: Advanced automation complete!

---

## Phase 4: Polish & Optimization

**Goal**: Improve reliability, logging, error handling

**Timeline**: Ongoing

---

### Task 4.1: Centralized Logging

**File**: `utils/logger.py`

**Acceptance Criteria**:
- [ ] All scripts use consistent logging format
- [ ] Logs rotate daily (logrotate)
- [ ] Error logs trigger notifications
- [ ] `/var/log/py_home.log` created

**Estimated Time**: 2 hours

---

### Task 4.2: Error Recovery & Retries

**Enhancements**:
- [ ] All API calls wrapped in retry logic
- [ ] Graceful degradation (continue if one device fails)
- [ ] Dead letter queue for failed notifications
- [ ] Health monitoring script (runs daily)

**Estimated Time**: 4 hours

---

### Task 4.3: Unit Tests

**Test Coverage**:
- [ ] Config loading
- [ ] Each API client
- [ ] Notification system
- [ ] pytest runs in CI (optional)

**Estimated Time**: 6-8 hours

---

### Task 4.4: Documentation

**Files to create/update**:
- [ ] `docs/API_CLIENTS.md` - How to use each API wrapper
- [ ] `docs/DEPLOYMENT.md` - Pi setup guide
- [ ] `docs/TROUBLESHOOTING.md` - Common issues

**Estimated Time**: 3 hours

---

## Testing Strategy

### Unit Testing

**Framework**: pytest

**Coverage**:
```python
# tests/test_config.py
def test_config_loads()
def test_env_var_substitution()
def test_missing_env_var_raises()

# tests/test_notifications.py
def test_pushover_sends()
def test_fallback_to_ntfy()

# tests/test_tesla_api.py
@pytest.mark.integration
def test_wake_vehicle()
def test_get_location()
```

**Run tests**:
```bash
pytest tests/
pytest tests/test_config.py -v
```

### Integration Testing

**Manual test plan**:

| Test | Steps | Expected Result |
|------|-------|-----------------|
| **Siri → Tesla** | "Hey Siri, warm up my car" | Car wakes, climate starts, notification received |
| **Leaving Home** | "Hey Siri, I'm leaving" | Nest away, outlets off, vacuum starts, notification |
| **Travel Time** | "Hey Siri, travel time to Milwaukee" | Siri speaks travel time |
| **Scheduled Pre-Heat** | Wait for 7 AM Monday | Car pre-heats if cold, notification |
| **Presence Detection** | Drive away with Tesla | "Leaving Home" scene triggers |
| **Error Handling** | Disconnect Tesla from internet, trigger warm-car | Notification says "error warming car" |

### System Testing

**Weekly health check**:
```bash
# On Pi
python3 -c "
from utils import tesla_api, nest_api, notifications
notifications.send('Weekly health check: All systems OK')
"
```

---

## Success Criteria

### Phase 0 Success
- [x] Project structure complete
- [ ] Can send notifications from laptop
- [ ] Tesla API working from laptop
- [ ] Google Maps working from laptop
- [ ] First automation script runs successfully

### Phase 1 Success (MVP Infrastructure)
- [ ] Pi accessible and running
- [ ] Webhook server running as systemd service
- [ ] At least one Siri voice command triggers Python script
- [ ] Notification received on phone

### Phase 2 Success (Core Automations)
- [ ] "Leaving Home" complete workflow works
- [ ] "Goodnight" complete workflow works
- [ ] "Warm Car" voice command works
- [ ] "Travel Time" query returns accurate data
- [ ] All 4 core automations working reliably

### Phase 3 Success (Advanced Features)
- [ ] Scheduled Tesla pre-heat working
- [ ] Presence detection triggers scenes
- [ ] Air quality monitoring active
- [ ] Voice task capture to Git/Checkvist

### Phase 4 Success (Production Ready)
- [ ] All automations run for 1 week without manual intervention
- [ ] Error rate < 5%
- [ ] Average response time < 5 seconds
- [ ] Notification delivery rate > 95%

---

## Appendix: Estimated Total Time

| Phase | Tasks | Time |
|-------|-------|------|
| **Phase 0** | Foundation (laptop) | 10-15 hours |
| **Phase 1** | Pi setup + webhooks | 4-5 hours |
| **Phase 2** | Core automations | 12-15 hours |
| **Phase 3** | Advanced features | 10-12 hours |
| **Phase 4** | Polish | 15-20 hours |
| **Total** | | **51-67 hours** |

**Timeline**:
- Part-time (10 hrs/week): 5-7 weeks
- Full-time focus (40 hrs/week): 1.5-2 weeks

---

## Next Steps

1. **Immediate** (Today):
   - [ ] Initialize git repo in `py_home/`
   - [ ] Create `.env` with your API credentials
   - [ ] Start Task 0.2 (config system)

2. **This Week** (Phase 0):
   - [ ] Complete all Phase 0 tasks
   - [ ] Have working Tesla/notifications/weather on laptop

3. **When Pi Arrives** (Phase 1):
   - [ ] Set up Pi (1 day)
   - [ ] Deploy code (1 hour)
   - [ ] First Siri command working (same day)

4. **Next 2-3 Weeks** (Phase 2):
   - [ ] Build core automations
   - [ ] Use daily, refine based on real usage

5. **Month 2** (Phase 3-4):
   - [ ] Add advanced features as needed
   - [ ] Polish and optimize

---

**End of Implementation Plan**

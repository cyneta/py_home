# py_home - Task List

**Status Key**: ❌ Not Started | 🔄 In Progress | ✅ Done

---

## Phase 0: Foundation (Laptop Development - Before Pi Arrives)

### Setup
- [x] ✅ Create py_home directory structure
- [x] ✅ Create requirements.txt
- [x] ✅ Create .env.example template
- [x] ✅ Create config.yaml
- [x] ✅ Create .gitignore
- [x] ✅ Initialize git repo
- [x] ✅ First commit to GitHub

### Core Utilities
- [x] ✅ `utils/config.py` - Load config.yaml and .env
- [x] ✅ `utils/notifications.py` - Send notifications (Pushover/ntfy)
- [ ] ❌ Test notifications from laptop

### API Clients (Tesla SKIPPED - API deprecated)
- [ ] 🔄 `utils/google_maps.py` - Travel time queries
- [ ] ❌ Test Google Maps from laptop
- [ ] ❌ `utils/weather.py` - Weather data
- [ ] ❌ Test weather API from laptop
- [ ] ❌ `utils/nest_api.py` - Thermostat control
- [ ] ❌ `utils/tapo_api.py` - Smart outlets

### First Automation
- [ ] ❌ `scripts/leaving_home.py` - Leaving home scene (Nest + Tapo + notifications)
- [ ] ❌ Test complete workflow from laptop

---

## Phase 1: Pi Infrastructure (When Pi Arrives)

### Pi Setup
- [ ] ❌ Flash Raspberry Pi OS to SD card
- [ ] ❌ SSH into Pi
- [ ] ❌ Update system packages
- [ ] ❌ Install Python 3, pip, git

### Deployment
- [ ] ❌ Clone repo to Pi
- [ ] ❌ Install Python dependencies
- [ ] ❌ Copy .env file to Pi
- [ ] ❌ Test: Run tesla_preheat.py on Pi
- [ ] ❌ Verify notification received

### Webhook Server
- [ ] ❌ `server/webhook_server.py` - Flask server with endpoints
- [ ] ❌ Test with curl: `/health`, `/warm-car`
- [ ] ❌ Create systemd service
- [ ] ❌ Enable service to start on boot
- [ ] ❌ Verify service running

### First Siri Command
- [ ] ❌ Create iOS Shortcut: "Warm Car"
- [ ] ❌ Test: "Hey Siri, warm up my car"
- [ ] ❌ Verify end-to-end: voice → webhook → script → notification

---

## Phase 2: Core Automations (MVP)

### Additional API Clients
- [ ] ❌ `utils/nest_api.py` - Thermostat control
- [ ] ❌ `utils/tapo_api.py` - Smart outlets
- [ ] ❌ `utils/sensibo_api.py` - Mini-split AC
- [ ] ❌ `utils/roborock_api.py` - Vacuum

### Automation Scripts
- [ ] ❌ `scripts/leaving_home.py` - Complete departure routine
- [ ] ❌ `scripts/goodnight.py` - Evening routine
- [ ] ❌ `scripts/travel_time.py` - Traffic query (returns JSON)
- [ ] ❌ `scripts/tesla_warm.py` - On-demand climate control

### iOS Shortcuts
- [ ] ❌ "Leaving Home" shortcut + Siri phrase
- [ ] ❌ "Goodnight" shortcut + Siri phrase
- [ ] ❌ "Travel Time to Milwaukee" shortcut + Siri phrase

### Webhook Endpoints
- [ ] ❌ Add `/leaving-home` endpoint
- [ ] ❌ Add `/goodnight` endpoint
- [ ] ❌ Add `/travel-time` endpoint

---

## Phase 3: Advanced Features

### Scheduled Tasks
- [ ] ❌ Set up crontab on Pi
- [ ] ❌ `scripts/grow_light.py` - On/off control
- [ ] ❌ Schedule grow light: on 6 AM, off 8 PM

### Tesla Integration (DEFERRED - API deprecated)
- [ ] 🔮 Research Tesla Fleet API or Teslemetry service
- [ ] 🔮 Decide on Tesla integration approach
- [ ] 🔮 `utils/tesla_api.py` - If feasible
- [ ] 🔮 `scripts/tesla_preheat.py` - Weather-aware pre-heat
- [ ] 🔮 `scripts/tesla_presence.py` - Location-based automation

### Multi-Device Coordination
- [ ] ❌ `scripts/temp_coordination.py` - Nest + Sensibo logic
- [ ] ❌ Schedule every 15 minutes

### Air Quality
- [ ] ❌ `utils/tuya_api.py` - Alen purifier control
- [ ] ❌ Set up Tuya developer account
- [ ] ❌ Link Alen devices to Tuya
- [ ] ❌ `scripts/air_quality_monitor.py` - PM2.5 monitoring + HVAC coordination
- [ ] ❌ Schedule every 15 minutes

### Task Management
- [ ] ❌ `utils/github_api.py` - Commit to TODO.md
- [ ] ❌ `utils/checkvist_api.py` - Task list integration
- [ ] ❌ `scripts/task_router.py` - Route based on keywords
- [ ] ❌ iOS Shortcut: "Add Task"
- [ ] ❌ Webhook endpoint: `/add-task`

---

## Phase 4: Polish

### Logging
- [ ] ❌ `utils/logger.py` - Centralized logging
- [ ] ❌ Set up log rotation (logrotate)
- [ ] ❌ All scripts use consistent logging

### Error Handling
- [ ] ❌ Add retry logic to all API calls
- [ ] ❌ Graceful degradation (continue on partial failure)
- [ ] ❌ Health check script (test all integrations)

### Testing
- [ ] ❌ Unit tests for config loading
- [ ] ❌ Unit tests for each API client
- [ ] ❌ Unit tests for notifications
- [ ] ❌ Integration test: end-to-end automation

### Documentation
- [ ] ❌ `docs/API_CLIENTS.md` - Usage guide for each API wrapper
- [ ] ❌ `docs/DEPLOYMENT.md` - Pi setup instructions
- [ ] ❌ `docs/TROUBLESHOOTING.md` - Common issues

---

## Current Status

**Phase**: 0 (Foundation)
**Next Task**: Initialize git repo + first commit

---

## Notes

- Phase 0 can be completed entirely on laptop before Pi arrives
- Phase 1 requires Pi hardware
- Phases can overlap (continue building scripts while testing on Pi)
- Tasks within a phase can be done in any order unless dependencies exist

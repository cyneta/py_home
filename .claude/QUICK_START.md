# py_home Quick Start Guide
**For new Claude Code session after WSL2 migration**

## 🔴 CRITICAL: Nest API Authentication Broken
- **Status**: Refresh token expired
- **Impact**: All heating/cooling automation blocked
- **Next Step**: Wait for Google OAuth propagation (5min-few hours), then retry OAuth Playground
- **Full Details**: See PROJECT_STATE.md → "Nest OAuth Troubleshooting"

## 📍 Quick Facts
- **Project**: Home automation on Raspberry Pi 4
- **Location**: 2480 Sherman Ave, Hood River, OR
- **Coordinates**: `45.70766068698601, -121.53682676696884`
- **Recent Work**: Test suite complete (207 passing), two-stage arrival implemented
- **Environment**: Migrating Git Bash → WSL2

## 🎯 Pending Tasks (Priority Order)
1. **CRITICAL**: Fix Nest OAuth (blocks automation)
2. Fix Nest dashboard showing 72°F
3. Fix Sensibo humidity undefined
4. Fix DEGRADED system status
5. Remove presence_monitor label (deprecated)
6. Add TempStick panel to dashboard

## 🚀 Common Commands

### WSL2 Paths
```bash
cd /mnt/c/git/cyneta/py_home
```

### Testing
```bash
pytest                     # Run all tests (207 should pass)
pytest -v                  # Verbose output
python tests/test_*.py     # Standalone mode
```

### Service Management (on Pi)
```bash
sudo systemctl restart py_home          # Restart service
sudo journalctl -u py_home -f          # View logs
curl http://localhost:5000/api/health  # Health check
```

### Nest OAuth Playground (After Propagation)
1. Go to: https://developers.google.com/oauthplayground/
2. Gear icon → "Use your own OAuth credentials"
3. Client ID: `493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com`
4. Client Secret: `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`
5. Scope: `https://www.googleapis.com/auth/sdm.service`
6. Authorize with **matthew.g.wheeler@gmail.com** (NOT cyneta)
7. Get refresh_token → update `config/.env`

## 📂 Critical Files
- `config/.env` - Secrets (NOT in git)
- `.claude/PROJECT_STATE.md` - Full context (READ THIS)
- `tests/` - 207 passing tests
- `automations/pre_arrival.py` - Stage 1 arrival (geofence)
- `automations/im_home.py` - Stage 2 arrival (WiFi)

## 🔑 Key Credentials (in config/.env)
- **Nest OAuth**: matthew.g.wheeler@gmail.com
- **Client ID**: 493001564141-vbibre8...
- **Client Secret**: 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
- **Refresh Token**: EXPIRED - needs replacement

## ⚠️ Important Context
- **Two-Stage Arrival**: Geofence (pre-heat) → WiFi (full arrival)
- **Deprecated**: ping monitoring, arrival_preheat.py, arrival_lights.py
- **Test Suite**: SAFE - all tests use dry_run or mocking, no real device control
- **Old Home Coords**: 45.7054, -121.5215 (WRONG - 1216m off, updated in tests)

## 📖 Full Documentation
Read `.claude/PROJECT_STATE.md` for complete context (architecture, troubleshooting, design decisions)

---
*Created: 2025-10-14*
*For: WSL2 migration handoff*

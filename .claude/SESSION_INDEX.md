# Claude Code Session Index
**For Context Transfer Between Sessions**

This directory (`.claude/`) contains session handoff documentation specifically for Claude Code. These are NOT project docs - they're for transferring context between Claude instances.

---

## 📚 Documentation Index

### Start Here 👈
**New to this session?** Read in this order:

1. **`QUICK_START.md`** (2 min read)
   - Essential facts and commands
   - Critical issues
   - Immediate next steps

2. **`SESSION_HANDOFF.md`** (5 min read)
   - What happened in last session
   - What's pending
   - Why we're at this stopping point

3. **`PROJECT_STATE.md`** (20 min read - reference)
   - Complete project context
   - Architecture details
   - Configuration reference
   - Troubleshooting guides

---

## 🎯 Quick Navigation

### Current Status
- ✅ **Test Suite**: Complete (207 passing, 0 failing)
- ✅ **Two-Stage Arrival**: Implemented and tested
- ✅ **Tailscale VPN**: Set up for remote access
- 🔴 **Nest OAuth**: BROKEN - refresh token expired (CRITICAL)

### Priority Tasks
1. **CRITICAL**: Fix Nest OAuth authentication
2. Fix Nest dashboard showing 72°F
3. Fix Sensibo humidity undefined
4. Fix DEGRADED system status
5. Remove presence_monitor label
6. Add TempStick panel

### Key Files to Know
- `config/.env` - Secrets (NOT in git, needs new NEST_REFRESH_TOKEN)
- `automations/pre_arrival.py` - Stage 1 arrival (geofence trigger)
- `automations/im_home.py` - Stage 2 arrival (WiFi trigger)
- `tests/` - 207 passing tests (all safe, no device control)
- `scripts/test_nest_auth.py` - Nest auth diagnostics

---

## 🚀 Quick Start Commands

### Testing
```bash
cd /mnt/c/git/cyneta/py_home  # WSL2
pytest                         # Should show 207 passing
```

### Nest OAuth (When Ready)
1. Wait for Google propagation (may be ready now)
2. Go to: https://developers.google.com/oauthplayground/
3. Use Client ID: `493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com`
4. Use Client Secret: `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`
5. Scope: `https://www.googleapis.com/auth/sdm.service`
6. Sign in with: **matthew.g.wheeler@gmail.com** (NOT cyneta)
7. Get refresh_token → Update `config/.env`

### Service Management (Raspberry Pi)
```bash
ssh pi@<pi-ip>
sudo systemctl restart py_home
sudo journalctl -u py_home -f
```

---

## 📖 Documentation Files

### Claude Code Session Docs (.claude/)
- **`README.md`** - This file (index)
- **`QUICK_START.md`** - Essential info (start here)
- **`SESSION_HANDOFF.md`** - Last session summary
- **`PROJECT_STATE.md`** - Complete context (comprehensive reference)

### Project Documentation (docs/)
- **`ARCHITECTURE.md`** - System architecture overview
- **`IOS_AUTOMATION.md`** - iOS Scriptable integration
- **`TWO_STAGE_ARRIVAL_PROPOSAL.md`** - Two-stage arrival design
- **`PRESENCE_DETECTION_DECISION.md`** - Why we use geofencing
- Various other design docs and proposals

### Development Docs (dev/)
- **`dev/workflows/TEST_SYSTEM_NOTES.md`** - Test system architecture

---

## ⚠️ Important Warnings

### Account Confusion 🚨
- **Use**: matthew.g.wheeler@gmail.com for Nest OAuth
- **DON'T USE**: matt@cyneta.com (wrong account)
- Browser keeps defaulting to cyneta - use incognito!

### Test Safety ✅
- All tests verified SAFE
- No tests control real devices
- All use `dry_run=True` or mocking
- Can run with confidence

### Deprecated Components 🗑️
- `presence_monitor.py` → Replaced by iOS geofencing
- `arrival_preheat.py` → Replaced by `pre_arrival.py`
- `arrival_lights.py` → Replaced by `im_home.py`
- Ping monitoring → Replaced by geofencing

---

## 🏠 Project Quick Facts

**What**: Home automation system on Raspberry Pi 4
**Where**: 2480 Sherman Ave, Hood River, OR
**Coordinates**: `45.70766068698601, -121.53682676696884`
**Stack**: Python, Flask, systemd, iOS Scriptable
**Devices**: Google Nest, TP-Link Tapo, Sensibo, TempStick

**Recent Work**:
- ✅ Test suite complete (159 → 207 tests)
- ✅ Two-stage arrival implemented
- ✅ Tailscale VPN installed
- 🔄 Nest OAuth troubleshooting (waiting for Google)

---

## 🔧 Environment Info

**Transition**: Git Bash → WSL2
**Git Bash Path**: `/c/git/cyneta/py_home`
**WSL2 Path**: `/mnt/c/git/cyneta/py_home`
**Production**: `/home/pi/py_home/` on Raspberry Pi

**Python**: 3.9+
**Service**: `py_home.service` (systemd)
**API**: Flask on port 5000

---

## 📞 Quick Help

**Stuck?** Check these in order:
1. `QUICK_START.md` - Common tasks and commands
2. `SESSION_HANDOFF.md` - Context about last session
3. `PROJECT_STATE.md` - Comprehensive troubleshooting

**Common Issues**:
- Nest auth failing → See "Nest OAuth Troubleshooting" in PROJECT_STATE.md
- Tests failing → Should be 207 passing (check you're in right directory)
- Can't access Pi → Check Tailscale VPN or local network
- OAuth wrong account → Use matthew.g.wheeler@gmail.com, try incognito

---

## ✅ Success Checklist

New session checklist:
- [ ] Read QUICK_START.md
- [ ] Run `pytest` (verify 207 passing)
- [ ] Fix Nest OAuth (get new refresh_token)
- [ ] Test Nest auth: `python scripts/test_nest_auth.py`
- [ ] Deploy to Pi and verify
- [ ] Address dashboard issues
- [ ] Keep tests passing!

---

**Last Updated**: 2025-10-14
**For**: WSL2 migration
**Status**: Ready for handoff 🚀

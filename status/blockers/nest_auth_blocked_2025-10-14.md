# BLOCKER: Nest OAuth Authentication Expired
**Date**: 2025-10-14
**Status**: ✅ RESOLVED - OAuth fixed and deployed to production
**Impact**: CRITICAL - All heating/cooling automation non-functional (WAS BROKEN, NOW FIXED)
**Owner**: Resolved
**Related**: `dev/debug/nest_oauth_troubleshooting_2025-10-14.md` (full troubleshooting journal)

---

## Problem Statement

Nest API refresh token expired (`invalid_grant` error), blocking all thermostat control automations.

## Impact

**Broken Automations**:
- ❌ Good morning (can't heat to comfort temp)
- ❌ Goodnight (can't lower temp)
- ❌ Arrival pre-heat (Stage 1 two-stage arrival)
- ❌ Departure away mode
- ❌ Temperature coordination

**Workaround**: Manual control via Google Home app works (uses different auth)

## Root Cause

OAuth2 refresh token stored in `config/.env` has been revoked or expired.

**Most Likely Cause**: Manual revocation in Google Account permissions (someone clicked "Remove Access" on "Sherman Automation")

## Current Status

**What We've Done**:
1. ✅ Diagnosed issue (refresh token expired)
2. ✅ Created diagnostic script (`scripts/test_nest_auth.py`)
3. ✅ Identified solution (re-authenticate via OAuth Playground)
4. ✅ Added OAuth Playground redirect URI to Google Cloud Console
5. ⏳ **WAITING**: Google OAuth propagation (5min - few hours)

**What We're Blocked On**:
- Google Cloud Console redirect URI changes take 5min - few hours to propagate
- Changed at ~21:15 on 2025-10-14
- Cannot proceed with OAuth flow until propagation complete

**Next Action** (After Propagation):
1. Test OAuth Playground: https://developers.google.com/oauthplayground/
2. Get new refresh_token
3. Update `config/.env`
4. Deploy to Raspberry Pi
5. Verify automations work

## Timeline

**~20:30** - Issue discovered (good morning automation failed)
**~20:35** - Root cause identified (refresh token expired)
**~20:40-21:15** - Multiple OAuth re-authentication attempts (all failed: redirect_uri_mismatch)
**~21:15** - Added OAuth Playground redirect URI to Google Cloud Console
**~21:18** - Tested too soon (still failing - propagation not complete)
**~21:25** - Session end (waiting for propagation)

**Total Time Spent**: ~90 minutes

## Resolution Plan

### Step 1: Wait for Google Propagation
- **ETA**: Could be ready now, or up to few hours from 21:15
- **How to Check**: Try OAuth Playground, if redirect_uri_mismatch gone = propagated

### Step 2: OAuth Playground Flow
1. https://developers.google.com/oauthplayground/
2. Gear icon → "Use your own OAuth credentials"
3. Client ID: `493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com`
4. Client Secret: `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`
5. Scope: `https://www.googleapis.com/auth/sdm.service`
6. Authorize with **matthew.g.wheeler@gmail.com** (NOT cyneta)
7. Exchange for tokens
8. Copy `refresh_token`

### Step 3: Update Configuration
```bash
# Edit config/.env
NEST_REFRESH_TOKEN=<new-refresh-token>
```

### Step 4: Test Locally
```bash
python scripts/test_nest_auth.py
# Should show: ✅ Nest authentication is working!
```

### Step 5: Deploy to Production
```bash
scp config/.env pi@<pi-ip>:/home/pi/py_home/config/
ssh pi@<pi-ip>
sudo systemctl restart py_home
curl -X POST http://localhost:5000/api/good-morning
```

**Estimated Time to Resolve**: 10-15 minutes (once propagation complete)

## Prevention

**Short Term**:
- Back up working refresh token (encrypted)
- Document working OAuth flow

**Long Term**:
- Monitor token expiration (add health check)
- Alert on `invalid_grant` errors
- Create `docs/NEST_OAUTH_SETUP.md` with step-by-step instructions

## References

- **Full Troubleshooting Journal**: `dev/debug/nest_oauth_troubleshooting_2025-10-14.md`
- **Diagnostic Script**: `scripts/test_nest_auth.py`
- **OAuth Reauth Scripts**: `scripts/nest_reauth*.py` (created during troubleshooting)
- **Session Handoff**: `.claude/SESSION_HANDOFF.md`

## Questions

1. What caused the original refresh token to expire? (Check Google Account permissions)
2. When was it last working? (Check logs)
3. Who has access to matthew.g.wheeler@gmail.com? (Could someone have revoked?)
4. Are there any Google security emails? (Check inbox)

---

## ✅ RESOLUTION (Morning of 2025-10-14)

**What Worked**: Standard Google OAuth flow with `https://www.google.com` redirect URI

**Process**:
1. Used standard OAuth endpoint (not Nest-specific)
2. Got authorization code from user
3. Exchanged for new refresh token
4. Deployed to Raspberry Pi at 192.168.50.189
5. Verified authentication working on Pi

**Verification**:
- ✅ Local test passed (`scripts/test_nest_auth.py`)
- ✅ Deployed to Pi successfully
- ✅ Service restarted
- ✅ Token validated on Pi
- ✅ Good morning automation triggered successfully

**Resolution Time**: 10 minutes (after overnight wait)

**BLOCKER STATUS**: ✅ RESOLVED - All automations operational

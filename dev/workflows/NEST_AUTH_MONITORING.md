# Nest OAuth Authentication Monitoring

**Purpose**: Prevent future Nest OAuth token expiration from causing extended outages

**Background**: On 2025-10-14, the Nest refresh token expired unexpectedly, breaking all heating/cooling automations for several hours. This document outlines monitoring and prevention strategies.

---

## Why Tokens Expire

OAuth2 refresh tokens can expire/revoke due to:

1. **Manual Revocation** - User removes access at https://myaccount.google.com/permissions
2. **Token Limit** - Google limits 50 refresh tokens per user/client (oldest revoked when limit hit)
3. **Security Events** - Google detects suspicious activity and revokes automatically
4. **Consent Screen Changes** - Modifying OAuth scopes or settings
5. **Inactivity** - Not used for 6+ months (unlikely for daily-use systems)

**Most Likely Cause for 2025-10-14**: Manual revocation or security event

---

## Prevention Strategy 1: Health Check Monitoring

### Automated Daily Check

Create a cron job on the Raspberry Pi to test Nest authentication daily:

```bash
# On Raspberry Pi
crontab -e

# Add this line (runs at 3 AM daily)
0 3 * * * /home/matt.wheeler/py_home/venv/bin/python /home/matt.wheeler/py_home/scripts/test_nest_auth.py || echo "ALERT: Nest auth failed at $(date)" | mail -s "Nest Auth Failure" matthew.g.wheeler@gmail.com
```

**Benefits**:
- Catch token expiration within 24 hours
- Automatic notification via email
- Fix before users notice automation failures

**Implementation Status**: ⏳ Not yet implemented

---

## Prevention Strategy 2: Enhanced Error Logging

### Add Critical Alerts to NestAPI

Modify `components/nest/client.py` to send notifications on auth failures:

```python
# In _ensure_token() method
except Exception as e:
    duration_ms = int((time.time() - api_start) * 1000)
    kvlog(logger, logging.ERROR, api='nest', action='token_refresh',
          error_type=type(e).__name__, error_msg=str(e), duration_ms=duration_ms)

    # NEW: Send critical alert if token invalid
    if 'invalid_grant' in str(e):
        logger.critical("Nest refresh token expired - manual intervention required")
        # Optional: Send push notification via ntfy
        try:
            import requests
            requests.post('https://ntfy.sh/py_home_7h3k2m9x',
                         data='CRITICAL: Nest refresh token expired. Re-auth required.',
                         headers={'Title': 'Nest Auth Failure'})
        except:
            pass  # Don't fail automation if notification fails

    raise
```

**Benefits**:
- Immediate notification when token expires
- Push notification to phone via ntfy
- Clear error message for troubleshooting

**Implementation Status**: ⏳ Not yet implemented

---

## Prevention Strategy 3: Token Backup

### Secure Backup of Working Token

When token is working, back it up securely:

```bash
# On development machine
cd /c/git/cyneta/py_home

# Create encrypted backup
gpg --symmetric --cipher-algo AES256 config/.env
# Enter strong passphrase when prompted
# This creates config/.env.gpg

# Store backup in secure location (password manager, encrypted USB, etc.)
# DO NOT commit .env.gpg to git!
```

**Restore Process** (if token expires):
```bash
# Decrypt backup
gpg config/.env.gpg
# Enter passphrase
# This creates config/.env with old token

# Test if old token still works
python scripts/test_nest_auth.py

# If old token works: deploy to Pi
# If old token also expired: follow OAuth re-authentication process
```

**Benefits**:
- Quick recovery if token accidentally revoked
- No need to go through OAuth flow if backup token still valid
- Secure storage (encrypted with GPG)

**Implementation Status**: ⏳ Not yet implemented

---

## Prevention Strategy 4: Documentation

### Quick Recovery Guide

Already created: `dev/debug/nest_oauth_troubleshooting_2025-10-14.md`

Contains:
- Step-by-step OAuth re-authentication process
- Common errors and solutions
- Complete troubleshooting timeline
- Prevention strategies

**Location**: `dev/debug/nest_oauth_troubleshooting_2025-10-14.md`

**Status**: ✅ Complete

---

## Prevention Strategy 5: Check Account Permissions

### Regular Audit of Google Account

Periodically check what has access:

1. Go to: https://myaccount.google.com/permissions
2. Find "Sherman Automation"
3. Verify it shows:
   - Access to "Google Nest Device Access"
   - Last used: recent date
   - Status: Active

**If missing**:
- Was manually revoked → Re-authenticate immediately
- Never listed → OAuth client may have issues

**Frequency**: Check monthly or after any Google security emails

**Implementation Status**: ⏳ Manual process, not automated

---

## Recovery Process (When Token Expires)

### Quick Steps

1. **Diagnose**:
   ```bash
   python scripts/test_nest_auth.py
   # Look for: "invalid_grant - Token has been expired or revoked"
   ```

2. **Re-authenticate**:
   - Use `dev/debug/nest_oauth_url.md` for clean OAuth URL
   - Sign in with `matthew.g.wheeler@gmail.com` (NOT cyneta)
   - Copy authorization code from redirect
   - Exchange for new refresh token

3. **Update Config**:
   ```bash
   # Edit config/.env
   NEST_REFRESH_TOKEN=<new-token>
   ```

4. **Test Locally**:
   ```bash
   python scripts/test_nest_auth.py
   # Should show: ✅ Nest authentication is working!
   ```

5. **Deploy to Pi**:
   ```bash
   scp config/.env matt.wheeler@192.168.50.189:/home/matt.wheeler/py_home/config/
   ssh matt.wheeler@192.168.50.189 "sudo systemctl restart py_home"
   ```

**Time to Recovery**: 10-15 minutes (if you follow the documented process)

---

## Implementation Priority

### High Priority (Recommended)
1. ✅ Document recovery process (DONE)
2. ⏳ Add daily health check cron job
3. ⏳ Create encrypted token backup

### Medium Priority
4. ⏳ Add critical alert notifications to NestAPI class
5. ⏳ Monthly audit of Google Account permissions

### Low Priority (Nice to Have)
6. Monitor for Google security emails
7. Add monitoring dashboard with auth status
8. Implement token expiration prediction (track age)

---

## Monitoring Checklist

### Monthly
- [ ] Check https://myaccount.google.com/permissions for "Sherman Automation"
- [ ] Verify no Google security emails received
- [ ] Test Nest automation manually (good morning/goodnight)

### After Google Security Emails
- [ ] Check if "Sherman Automation" still authorized
- [ ] Test Nest authentication immediately
- [ ] Re-authenticate if needed

### After OAuth Changes
- [ ] Back up working refresh token (encrypted)
- [ ] Update documentation if process changed
- [ ] Test recovery process to ensure it works

---

## Success Metrics

**Before (2025-10-14)**:
- ❌ Token expired without warning
- ❌ No monitoring - discovered only when user tried automation
- ❌ Took 2.5 hours to diagnose + overnight wait + 10 min to fix
- ❌ No documentation existed

**After (With Monitoring)**:
- ✅ Daily health check detects failure within 24 hours
- ✅ Automatic notification sent to phone
- ✅ Documented recovery process = 10-15 min recovery time
- ✅ Encrypted backup token for quick recovery

**Goal**: Reduce unplanned outage duration from hours to minutes

---

## References

- **Troubleshooting Journal**: `dev/debug/nest_oauth_troubleshooting_2025-10-14.md`
- **OAuth URL Template**: `dev/debug/nest_oauth_url.md`
- **Diagnostic Script**: `scripts/test_nest_auth.py`
- **Deployment Guide**: `dev/setup/DEPLOYMENT.md`

---

**Status**: Documented, not yet fully implemented
**Owner**: Unassigned
**Next Action**: Implement daily health check cron job on Raspberry Pi

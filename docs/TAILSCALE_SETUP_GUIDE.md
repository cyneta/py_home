# Tailscale Setup Guide

**Date:** 2025-10-13
**Status:** Ready to execute
**Time Required:** 30 minutes total
**Prerequisites:** Home network access initially, then test remotely

---

## Overview

This guide walks through setting up Tailscale VPN to enable remote access to py_home Pi endpoints when away from home.

**What You'll Get:**
- Access Pi from anywhere (cellular, public WiFi, traveling)
- Deploy code remotely via scp/ssh
- Access dashboard at `http://[tailscale-ip]:5000/dashboard`
- iOS geofencing works over cellular (not just queued)
- SSH to Pi from laptop anywhere

**What Tailscale Is:**
Zero-config VPN built on WireGuard. Creates secure mesh network between your devices with automatic NAT traversal. No port forwarding, no config files, just install and login.

---

## Phase 1: Install Tailscale (15 minutes)

### Step 1: Install on Raspberry Pi (5 min)

**Prerequisites:** Must be on home network initially

```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local

# Install Tailscale (single command)
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
sudo tailscale up

# You'll see output like:
# To authenticate, visit:
# https://login.tailscale.com/a/1234567890abcdef
```

**Action Required:**
1. Copy the URL from terminal
2. Open URL in browser on laptop
3. Create Tailscale account (or login with Google/GitHub)
4. Approve the Pi device

**Back in Pi terminal:**
```bash
# Check status (after approving in browser)
tailscale status

# Should show:
# 100.64.0.x    raspberrypi         matt.wheeler@   linux   -
#                                   Connected

# Note this IP address! You'll need it for home-geofence.js
```

**Save the IP:**
```bash
# Get your Pi's Tailscale IP
tailscale ip -4

# Example output: 100.64.0.2
# Write this down or save to file
```

**✅ Success Criteria:**
- `tailscale status` shows "Connected"
- You have the Tailscale IP (e.g., 100.64.0.2)
- Pi appears in Tailscale web admin: https://login.tailscale.com/admin/machines

---

### Step 2: Install on Windows Laptop (5 min)

```bash
# Open browser and download
https://tailscale.com/download/windows

# Or use winget (if installed)
winget install tailscale.tailscale
```

**Installation Steps:**
1. Run the installer (Tailscale-Setup.exe)
2. Follow installation wizard (default options)
3. App will launch automatically
4. Click "Login with Tailscale"
5. Login with same account as Pi (Google/GitHub/email)
6. Approve device in browser

**Verify:**
```bash
# Open PowerShell or Git Bash
tailscale status

# Should show both laptop and Pi:
# 100.64.0.1    LAPTOP-NAME         matt.wheeler@   windows online
# 100.64.0.2    raspberrypi         matt.wheeler@   linux   online
```

**✅ Success Criteria:**
- Tailscale icon in system tray (Windows taskbar)
- `tailscale status` shows both devices
- Both show "online" status

---

### Step 3: Install on iPhone (5 min)

**Installation Steps:**
1. Open App Store
2. Search "Tailscale"
3. Install official app (Tailscale Inc.)
4. Open app
5. Tap "Login with Tailscale"
6. Login with same account
7. iOS will prompt to add VPN configuration
8. Tap "Allow" (required for VPN)

**Verify:**
1. In Tailscale app, tap "Machines" tab
2. Should see 3 devices:
   - Your iPhone
   - Your laptop
   - raspberrypi

**Enable on Demand (Recommended):**
1. In Tailscale app → Settings
2. Enable "On Demand"
3. This keeps VPN active automatically

**✅ Success Criteria:**
- Tailscale app shows all 3 devices
- VPN indicator appears in status bar
- Can see Pi's IP in app (100.64.0.x)

---

## Phase 2: Test Basic Connectivity (10 minutes)

### Test 1: Ping from Laptop (On Home WiFi)

```bash
# From laptop terminal
ping 100.64.0.2

# Should get replies:
# Reply from 100.64.0.2: bytes=32 time=2ms TTL=64
# Reply from 100.64.0.2: bytes=32 time=1ms TTL=64
```

**If ping fails:**
- Check `tailscale status` on both devices
- Verify both show "online"
- Try restarting Tailscale on laptop

---

### Test 2: HTTP Endpoint Access (On Home WiFi)

```bash
# From laptop
curl http://100.64.0.2:5000/status

# Expected output:
# {"status": "ok"}
```

```bash
# Test dashboard
# Open browser to:
http://100.64.0.2:5000/dashboard

# Should load py_home dashboard
```

**✅ Success Criteria:**
- `/status` returns JSON
- Dashboard loads in browser
- Same as `raspberrypi.local:5000` but using Tailscale IP

---

### Test 3: SSH Access (On Home WiFi)

```bash
# From laptop
ssh matt.wheeler@100.64.0.2

# Should connect without issues
# Same as ssh to raspberrypi.local
```

**✅ Success Criteria:**
- SSH connects successfully
- Can run commands on Pi

---

### Test 4: Remote Access (AWAY from Home WiFi)

**Important: This is the real test**

```bash
# Disconnect laptop from home WiFi
# Use cellular hotspot OR go to coffee shop

# Test 4a: Ping
ping 100.64.0.2

# Should still work (may be 20-50ms latency)

# Test 4b: HTTP Endpoint
curl http://100.64.0.2:5000/status

# Should return: {"status": "ok"}

# Test 4c: Dashboard
# Open browser to:
http://100.64.0.2:5000/dashboard

# Should load (may take 2-3 seconds)

# Test 4d: SSH
ssh matt.wheeler@100.64.0.2

# Should connect
```

**✅ Success Criteria:**
- All 4 tests work when away from home
- Latency acceptable (~10-50ms)
- No connection errors

**If tests fail:**
- Verify laptop Tailscale is running (check system tray)
- Check `tailscale status` shows Pi as "online"
- Try `tailscale ping 100.64.0.2`
- Check Tailscale logs: `tailscale debug --logs`

---

## Phase 3: Update home-geofence.js (5 minutes)

### Step 1: Update Git Repo Version

```bash
# On laptop
cd /c/git/cyneta/py_home/scripts/ios

# Open home-geofence.js in editor
# Find line 7:
# piVPN: "http://100.64.0.2:5000",

# Replace 100.64.0.2 with YOUR Pi's actual Tailscale IP
# (from Step 1 where you saved it)
```

**Example:**
```javascript
const config = {
  // Pi server URLs
  piLocal: "http://raspberrypi.local:5000",
  piVPN: "http://100.64.0.2:5000",  // ← YOUR ACTUAL TAILSCALE IP HERE

  // Home location (must match config/config.yaml)
  homeLat: 45.70766068698601,
  homeLng: -121.53682676696884,
  homeRadius: 150,  // meters

  // Auth (if enabled on Pi)
  authUser: "",
  authPass: ""
};
```

**Save the file**

---

### Step 2: Update iCloud Drive Version

```bash
# Copy to iCloud Drive location
cp /c/git/cyneta/py_home/scripts/ios/home-geofence.js \
   "C:/Users/matt.wheeler/iCloudDrive/iCloud~dk~simonbs~Scriptable/home-geofence.js"

# Or manually edit the iCloud version with same IP
```

**Verify:**
```bash
# Check both files have same IP
grep "piVPN" /c/git/cyneta/py_home/scripts/ios/home-geofence.js
grep "piVPN" "C:/Users/matt.wheeler/iCloudDrive/iCloud~dk~simonbs~Scriptable/home-geofence.js"

# Both should show your Tailscale IP
```

**✅ Success Criteria:**
- Line 7 in both files updated with correct Tailscale IP
- IP matches what `tailscale ip -4` showed on Pi

---

## Phase 4: Test iOS Geofencing Over Cellular (10 minutes)

### Test 1: Manual Script Run Over Cellular

```
1. On iPhone, disable WiFi (use cellular only)
2. Open Scriptable app
3. Find "home-geofence" script
4. Tap to run manually
5. Check console output
```

**Expected Output:**
```
=== Home Geofence Check ===
Triggered by: manual
Location: 45.7076, -121.5368
At home: true  (or false if away)
Previous state: null
Home network: false  ← This is key - not on WiFi
Calling: http://100.64.0.2:5000/pre-arrival  ← Using Tailscale!
✓ Success: {...}
=== Complete ===
```

**✅ Success Criteria:**
- "Home network: false" (using cellular)
- "Calling: http://100.64.0.2..." (using Tailscale IP, not local)
- "✓ Success" (endpoint reached)
- No errors

**If it fails:**
- Check iPhone Tailscale app shows Pi as online
- Verify VPN is active (check status bar)
- Try disabling/enabling Tailscale VPN toggle
- Check home-geofence.js has correct IP

---

### Test 2: Real-World Geofence Over Cellular

**Setup:**
```
1. Leave home (>200m away)
2. Ensure iPhone on cellular (WiFi OFF)
3. Wait for iOS automation to trigger
4. Check for notification
```

**Expected:**
```
iOS Notification:
"🚗 Left Home"
"Automation triggered" (or "Will sync when network available")
```

**Verify on Pi:**
```bash
# SSH to Pi (over Tailscale from laptop)
ssh matt.wheeler@100.64.0.2

# Check logs
tail -20 /home/matt.wheeler/py_home/data/logs/leaving_home.log

# Should see recent entry with your Tailscale connection
```

**✅ Success Criteria:**
- Geofence triggers when leaving
- Notification appears
- Pi logs show automation ran
- Happened over cellular (not WiFi)

---

## Phase 5: Advanced Configuration (Optional)

### Enable MagicDNS (Recommended)

**Benefit:** Use hostname instead of IP address

```bash
# SSH to Pi
ssh matt.wheeler@100.64.0.2

# Enable MagicDNS
sudo tailscale up --accept-dns

# Verify
tailscale status

# Should show domain suffix like:
# tail-scale.ts.net
```

**Update home-geofence.js:**
```javascript
// Change from:
piVPN: "http://100.64.0.2:5000",

// To:
piVPN: "http://raspberrypi:5000",

// No IP needed!
```

**Test:**
```bash
# From laptop on cellular
curl http://raspberrypi:5000/status

# Should work without IP
```

**✅ Success Criteria:**
- Can access Pi by name, not IP
- More resilient if Tailscale IP changes

---

### Configure Access Control Lists (Optional)

**When needed:** If you want to restrict which devices can access Pi

**Steps:**
1. Go to https://login.tailscale.com/admin/acls
2. Click "Edit ACLs"
3. Add rules (JSON format)

**Example - Allow only your devices:**
```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["autogroup:member"],
      "dst": ["raspberrypi:*"]
    }
  ]
}
```

**Save and test:**
```bash
# From laptop
curl http://100.64.0.2:5000/status

# Should still work
```

---

### Enable Pi as Exit Node (Optional, Advanced)

**Benefit:** Route ALL laptop/iPhone traffic through home network

**Use Cases:**
- Secure public WiFi usage
- Access home network resources
- Appear as if browsing from home

**Setup:**
```bash
# On Pi
ssh matt.wheeler@100.64.0.2

# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Advertise as exit node
sudo tailscale up --advertise-exit-node --accept-routes

# Approve in admin console
# Go to: https://login.tailscale.com/admin/machines
# Find raspberrypi → ... → Edit route settings
# Enable "Use as exit node"
```

**Use on iPhone:**
```
1. Open Tailscale app
2. Tap Exit Node
3. Select "raspberrypi"
4. Enable

Now ALL iPhone traffic goes through home network
```

**Use on Laptop:**
```bash
tailscale up --exit-node=raspberrypi
```

**Disable:**
```bash
tailscale up --exit-node=
```

---

## Troubleshooting

### Issue: Pi shows "offline" in tailscale status

**Possible Causes:**
- Pi not running
- Tailscale service stopped on Pi
- Network issue on Pi side

**Fix:**
```bash
# If you can still access Pi locally
ssh matt.wheeler@raspberrypi.local

# Restart Tailscale
sudo systemctl restart tailscaled

# Check status
sudo systemctl status tailscaled

# Should show "active (running)"

# Verify
tailscale status
```

---

### Issue: "Connection refused" when accessing Pi

**Check 1: Is Flask running?**
```bash
ssh matt.wheeler@100.64.0.2
sudo systemctl status py_home

# Should show "active (running)"

# If not:
sudo systemctl start py_home
```

**Check 2: Is port 5000 listening?**
```bash
ssh matt.wheeler@100.64.0.2
sudo netstat -tlnp | grep 5000

# Should show Flask listening on 0.0.0.0:5000
```

**Check 3: Firewall blocking?**
```bash
# Pi likely doesn't have firewall, but check:
ssh matt.wheeler@100.64.0.2
sudo iptables -L

# Should show ACCEPT policies
```

---

### Issue: iPhone geofencing not using Tailscale

**Symptom:** Actions queued instead of executing immediately

**Check 1: Is Tailscale VPN active on iPhone?**
```
Look for VPN icon in status bar
If not there:
1. Open Tailscale app
2. Toggle VPN on
3. Enable "On Demand" in settings
```

**Check 2: Is home-geofence.js updated?**
```
Open Scriptable app → Scripts → home-geofence → Edit
Check line 7 has correct piVPN IP
```

**Check 3: Test manually**
```
1. Disable WiFi (cellular only)
2. Run home-geofence script manually
3. Check console for errors
```

---

### Issue: Slow connection (>100ms latency)

**Symptom:** Tailscale working but very slow

**Cause:** Using DERP relay instead of direct connection

**Check:**
```bash
# On laptop
tailscale status

# Look for raspberrypi line
# If shows "relay:..." → Using relay (slower)
# If shows "direct" → Direct P2P connection (faster)
```

**Why relay is used:**
- Firewall/NAT preventing direct connection
- Geographic distance requiring relay
- Network topology complexity

**Usually acceptable for home automation** - 50ms vs 10ms doesn't matter for turning on lights

**To force direct connection (advanced):**
- Configure port forwarding on router (defeats purpose of Tailscale)
- Not recommended - relay works fine

---

### Issue: Tailscale account locked out

**Prevention:**
- Save recovery codes when creating account
- Use SSO (Google/GitHub) for easy recovery

**Recovery:**
- Use account recovery flow at https://login.tailscale.com/admin
- Contact Tailscale support

---

## Success Metrics

### Week 1: Installation Phase

**Day 1:**
- ✅ Installed on all 3 devices (Pi, laptop, iPhone)
- ✅ All devices show "online" in `tailscale status`
- ✅ Can ping Pi from laptop over Tailscale
- ✅ Can access Pi endpoints over Tailscale

**Day 2-3:**
- ✅ Updated home-geofence.js with Tailscale IP
- ✅ Tested geofencing over cellular
- ✅ Verified automation triggers work remotely

**Day 4-7:**
- ✅ Used SSH remotely 3+ times
- ✅ Accessed dashboard remotely 3+ times
- ✅ Deployed code remotely 1+ time

### Week 2: Evaluation Phase

**Questions to Answer:**
1. Did Tailscale work reliably? (Target: >95% uptime)
2. Was setup time worth it? (Target: yes)
3. Did you actually use remote access? (Target: 3+ times)
4. Any major issues? (Target: 0 blockers)

**If YES to 1-3 and NO to 4:** Keep using Tailscale ✅
**If multiple NOs:** Re-evaluate if VPN needed

---

## Cost Analysis

### Tailscale Free Tier (What You're Using)

**Included:**
- Up to 100 devices
- Unlimited bandwidth
- 1 user (you can invite 2 more users)
- All features except SSO/audit logs
- No time limit - free forever

**Cost:** $0/month

**Upgrade Options (If Needed Later):**
- Personal Pro: $6/month (100+ devices, subnet routing)
- Team: $15/user/month (business features)

**For py_home:** Free tier is perfect forever

---

## Security Best Practices

### 1. Use Strong Authentication

**Do:**
- Use Google/GitHub SSO for easy 2FA
- Enable 2FA on your Tailscale account
- Save recovery codes securely

**Don't:**
- Use weak passwords
- Share Tailscale account credentials

---

### 2. Review Device List Regularly

**Monthly Check:**
```
Go to: https://login.tailscale.com/admin/machines

Review list:
- Remove old devices
- Revoke lost/stolen devices
- Verify only YOUR devices listed
```

---

### 3. Monitor Access Logs (Optional)

**Where:** Tailscale admin console → Activity

**What to look for:**
- Unexpected devices joining
- Access from unfamiliar locations
- Failed authentication attempts

---

### 4. Keep Software Updated

**Pi:**
```bash
# Monthly maintenance
ssh matt.wheeler@100.64.0.2
sudo apt update && sudo apt upgrade -y
sudo systemctl restart tailscaled
```

**Laptop/iPhone:**
- Enable auto-updates for Tailscale app
- Update when notified

---

## Backup Plan / Rollback

### If Tailscale Stops Working

**Option 1: Offline Queueing (Already Built In)**
```javascript
// home-geofence.js already has this
if (!result.success) {
  console.log("Queueing action for later...");
  state.queue.push({endpoint, timestamp, transition});
}

// Actions execute when back on home WiFi
```

**Fallback:** Automations queue and execute when home

---

### If You Want to Remove Tailscale

**Uninstall:**
```bash
# Pi
ssh matt.wheeler@raspberrypi.local
sudo tailscale down
sudo apt remove tailscale

# Laptop
# Windows Settings → Apps → Uninstall Tailscale

# iPhone
# Long-press Tailscale app → Delete App
```

**Revert home-geofence.js:**
```javascript
// Change line 7 back to placeholder
piVPN: "http://100.64.0.2:5000",  // Not used without VPN
```

**Impact:** Lose remote access, but local automation still works

---

## Next Steps After Setup

### Week 1: Use It

**Try these activities:**
1. Deploy code from coffee shop
2. Check dashboard while away
3. SSH to Pi from cellular
4. Trigger goodnight routine remotely
5. Monitor logs when traveling

**Goal:** Build confidence in system

---

### Week 2: Optimize

**Consider:**
1. Enable MagicDNS (hostname instead of IP)
2. Set up ACLs (if security conscious)
3. Configure exit node (if traveling frequently)

**Goal:** Tune to your workflow

---

### Week 3: Document

**Update your notes:**
- What works well?
- What's annoying?
- Would you recommend to friend?
- Any issues encountered?

**Goal:** Decide if keeping long-term

---

## Quick Reference

### Essential Commands

```bash
# Check Tailscale status
tailscale status

# Get Pi IP
tailscale ip -4

# Restart Tailscale
sudo systemctl restart tailscaled

# View Tailscale logs
sudo journalctl -u tailscaled -n 50

# Test connectivity
tailscale ping 100.64.0.2

# Access Pi remotely
ssh matt.wheeler@100.64.0.2
curl http://100.64.0.2:5000/status
```

---

### Key URLs

- Admin Console: https://login.tailscale.com/admin
- Documentation: https://tailscale.com/kb
- Download Page: https://tailscale.com/download
- Support: https://tailscale.com/contact/support

---

## Related Documents

- **Decision Doc:** [VPN_SETUP_DECISION.md](./VPN_SETUP_DECISION.md) - Why Tailscale over WireGuard
- **Architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md) - System overview
- **Geofencing:** [IOS_AUTOMATION.md](./IOS_AUTOMATION.md) - iOS automation setup
- **Test Plan:** [TWO_STAGE_ARRIVAL_TEST_PLAN.md](./TWO_STAGE_ARRIVAL_TEST_PLAN.md) - Arrival system testing

---

## Completion Checklist

Copy this to track your progress:

```markdown
## Tailscale Setup Progress

### Phase 1: Installation (15 min)
- [ ] Install on Pi
- [ ] Install on Windows laptop
- [ ] Install on iPhone
- [ ] Note Pi's Tailscale IP: _______________

### Phase 2: Test Connectivity (10 min)
- [ ] Ping from laptop (home WiFi)
- [ ] Access endpoint (home WiFi)
- [ ] SSH to Pi (home WiFi)
- [ ] Ping from laptop (cellular)
- [ ] Access endpoint (cellular)
- [ ] SSH to Pi (cellular)

### Phase 3: Update Geofence Script (5 min)
- [ ] Update git repo home-geofence.js
- [ ] Update iCloud home-geofence.js
- [ ] Verify both files match

### Phase 4: Test iOS Geofencing (10 min)
- [ ] Run script manually over cellular
- [ ] Verify uses Tailscale IP
- [ ] Real-world geofence test
- [ ] Check Pi logs show connection

### Optional: Advanced Config
- [ ] Enable MagicDNS
- [ ] Configure ACLs
- [ ] Set up exit node

### Week 1 Usage Goals
- [ ] SSH remotely 3+ times
- [ ] Access dashboard remotely 3+ times
- [ ] Deploy code remotely 1+ time
- [ ] Geofencing works over cellular

### Evaluation (Week 2)
- [ ] >95% uptime
- [ ] Used remote access regularly
- [ ] No major issues
- [ ] Decision: Keep ✅ or Remove ❌
```

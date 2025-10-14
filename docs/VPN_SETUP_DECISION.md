# VPN Setup Decision: Tailscale vs WireGuard

**Date:** 2025-10-13
**Status:** Decision needed
**Purpose:** Enable remote access to py_home Pi endpoints when away from home network

---

## Current Situation

**Works Now:**
- ✅ iOS Scriptable geofencing with offline queueing
- ✅ Local network access via `raspberrypi.local:5000`
- ✅ Network detection in home-geofence.js (lines 62-72, 150)

**Problem:**
- ❌ Cannot access Pi endpoints when away from home
- ❌ Cannot deploy code remotely
- ❌ Cannot test endpoints without being home
- ❌ Cannot debug issues while traveling

**Current Code Already Supports VPN:**
```javascript
// home-geofence.js line 74-76
async function callPiEndpoint(endpoint, isHomeNetwork) {
  const baseUrl = isHomeNetwork ? config.piLocal : config.piVPN;
  const url = `${baseUrl}${endpoint}`;
```

**Placeholder VPN URL:**
```javascript
// line 7
piVPN: "http://100.64.0.2:5000",  // Update with your Tailscale IP when VPN configured
```

---

## Why VPN Matters

### Current Use Cases

**1. Remote Debugging**
- Check Pi logs when away from home
- Test endpoint changes without being home
- Monitor system health remotely

**2. Remote Deployment**
- Deploy code changes from laptop anywhere
- Restart Flask service remotely
- Update configuration files

**3. Enhanced Geofencing**
- Process queued actions when on cellular
- Trigger automations from anywhere
- Fallback when home WiFi fails

**4. Manual Control**
- Trigger goodnight routine when traveling
- Pre-heat house when returning from trip
- Check thermostat status remotely

### Future Use Cases

**5. Off-site Monitoring**
- Check home status while away
- Verify automations ran correctly
- Get alerts for system issues

**6. Remote Administration**
- SSH to Pi from anywhere
- Update system packages
- Check service status

---

## Option 1: Tailscale (Recommended)

### What It Is

Tailscale is a **zero-config VPN** built on WireGuard that creates a secure mesh network between your devices. It's WireGuard under the hood, but with automatic configuration and NAT traversal.

**Think of it as:** "WireGuard with training wheels and autopilot"

### Pros

**✅ Easiest Setup (Critical for Success)**
```bash
# On Pi (literally 2 commands)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# On laptop
# Download app, install, login
# That's it - devices auto-discover each other
```

**✅ No Port Forwarding Required**
- Works behind CGNAT (Carrier-Grade NAT)
- Works with restrictive ISP setups
- No router configuration needed
- No security risk from open ports

**✅ Automatic NAT Traversal**
- Devices connect peer-to-peer when possible
- Falls back to relay (DERP) servers when needed
- Handles complex network situations automatically

**✅ Works Everywhere**
- Home WiFi → Direct connection
- Cellular → Via Tailscale relay
- Public WiFi → Encrypted tunnel
- Behind corporate firewall → Still works

**✅ Device Management Dashboard**
- Web UI to see all devices
- Easy to add/remove devices
- Access control lists (ACLs)
- Can share access with others

**✅ Built-in DNS**
- Access Pi by name: `raspberrypi.tail-scale.net`
- No need to remember IPs
- Automatically updated if IP changes

**✅ Cross-Platform**
- iOS (native app)
- Windows (native app)
- Linux (native package)
- Android, macOS, etc.

**✅ MagicDNS**
- Access devices by hostname
- Automatic DNS resolution
- Works across all devices

**✅ Free Tier Generous**
- Up to 100 devices
- Unlimited bandwidth
- 1 user (personal use)
- Perfect for home setup

### Cons

**❌ Requires Tailscale Account**
- Must create account (email or SSO)
- Devices tied to account
- Could be seen as "vendor lock-in"

**❌ Slight Performance Overhead**
- If peer-to-peer fails, uses relay servers
- Adds ~10-50ms latency via DERP relay
- Not an issue for home automation (not latency-sensitive)

**❌ Relies on Tailscale Infrastructure**
- DERP relay servers owned by Tailscale
- If Tailscale goes down, relay unavailable
- Direct peer-to-peer still works
- Can self-host DERP servers (advanced)

**❌ Privacy Consideration**
- Tailscale servers see connection metadata (not content)
- Content is end-to-end encrypted
- Tailscale can see: which devices connect, when
- Tailscale cannot see: what data is transferred

### Setup Complexity

**Time:** 15-30 minutes total
**Difficulty:** Easy (1/5)

**Steps:**
1. Create Tailscale account (5 min)
2. Install on Pi (5 min)
3. Install on Windows laptop (5 min)
4. Install on iPhone (5 min)
5. Update home-geofence.js with Tailscale IP (2 min)
6. Test connection (5 min)

**No Configuration Files Needed**

---

## Option 2: Vanilla WireGuard

### What It Is

WireGuard is a **modern VPN protocol** that's fast, secure, and uses minimal resources. You configure it manually with keys and config files.

**Think of it as:** "Manual transmission race car - fast but requires skill"

### Pros

**✅ Maximum Performance**
- Minimal overhead (~5-10ms latency)
- Faster than Tailscale relay mode
- Leaner code, less processing

**✅ No Third-Party Service**
- Self-hosted entirely
- No external dependencies
- Complete control and privacy

**✅ More Secure (Arguably)**
- No relay servers in the middle
- Smaller attack surface
- Audited and trusted protocol

**✅ Static IP Addresses**
- Predictable network topology
- Easier to debug connection issues
- No DNS resolution delays

**✅ No Account Required**
- No email, no login
- Just keys and configs

### Cons

**❌ Complex Setup**
```bash
# Generate keys for each device
wg genkey | tee privatekey | wg pubkey > publickey

# Create config file for Pi (server)
# Create config file for laptop (client)
# Create config file for iPhone (client)
# Exchange keys manually
# Configure IP addresses
# Set up routing rules
```

**❌ Requires Port Forwarding**
- Must configure router
- Potential security risk (open UDP port)
- May not work with CGNAT ISP
- Blocked by some corporate networks

**❌ Manual Key Management**
- Generate key pairs for each device
- Exchange public keys manually
- Store private keys securely
- Update configs if keys rotate

**❌ Static Configuration**
- Adding new device requires editing all configs
- IP addresses must be managed manually
- DNS not automatic

**❌ iPhone Config More Complex**
- Must use third-party app or QR code
- Config file must be perfect
- Harder to debug connection issues

**❌ No Automatic NAT Traversal**
- Both devices must have static IPs OR
- One device must have public IP + port forward
- Doesn't work behind double NAT easily

**❌ Maintenance Burden**
- Must troubleshoot connectivity issues
- Router firmware updates may break port forwarding
- ISP changes may require reconfiguration

### Setup Complexity

**Time:** 2-4 hours (first time)
**Difficulty:** Hard (4/5)

**Steps:**
1. Install WireGuard on Pi (10 min)
2. Generate server keys (5 min)
3. Create server config file (15 min)
4. Configure router port forwarding (20 min)
5. Test port forwarding (10 min)
6. Install WireGuard on Windows (10 min)
7. Generate client keys (5 min)
8. Create client config file (15 min)
9. Exchange keys (10 min)
10. Configure iPhone client (20 min)
11. Test connection (20 min)
12. Debug inevitable issues (1-2 hours)

**Requires:** Text editing, networking knowledge, patience

---

## Option 3: Hybrid (Tailscale + Self-Hosted DERP)

### What It Is

Use Tailscale for easy setup and management, but run your own relay servers for privacy.

**Best of Both Worlds:**
- Tailscale's easy config
- Your own relay infrastructure
- Maximum privacy

### Pros

**✅ Easy Setup (from Tailscale)**
**✅ Privacy Control (from self-hosted)**
**✅ No Reliance on Tailscale Infrastructure**

### Cons

**❌ Most Complex Option**
- Must run DERP server (additional VPS cost)
- Must configure Tailscale to use custom DERP
- Maintenance overhead

**❌ Cost**
- Need separate VPS for DERP server
- $5-10/month cloud hosting

**❌ Overkill for Home Automation**
- Home automation isn't high-security
- External APIs (Nest, Sensibo) already cloud-based
- No sensitive data transmitted

---

## Comparison Matrix

| Criteria | Tailscale | WireGuard | Hybrid |
|----------|-----------|-----------|--------|
| **Setup Time** | 15-30 min | 2-4 hours | 4-6 hours |
| **Setup Difficulty** | ⭐ Easy | ⭐⭐⭐⭐ Hard | ⭐⭐⭐⭐⭐ Expert |
| **Maintenance** | ⭐ Minimal | ⭐⭐⭐ Moderate | ⭐⭐⭐⭐ High |
| **Performance (latency)** | ~10-50ms relay | ~5-10ms direct | ~10-50ms relay |
| **Performance (bandwidth)** | Unlimited | Unlimited | Unlimited |
| **Works behind CGNAT** | ✅ Yes | ❌ No | ✅ Yes |
| **Requires port forward** | ❌ No | ✅ Yes | ❌ No |
| **Privacy** | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Excellent |
| **iPhone setup** | ⭐⭐⭐⭐⭐ Install app | ⭐⭐⭐ Manual config | ⭐⭐⭐⭐⭐ Install app |
| **Cost** | Free (personal) | Free | ~$5-10/mo VPS |
| **Debugging ease** | ⭐⭐⭐⭐⭐ Web UI | ⭐⭐ Command line | ⭐⭐⭐ Mixed |
| **Adding new device** | ⭐⭐⭐⭐⭐ Install + login | ⭐⭐ Edit configs | ⭐⭐⭐⭐ Install + login |
| **Works on cellular** | ✅ Yes | ✅ Yes* | ✅ Yes |
| **No external dependency** | ❌ No | ✅ Yes | ⭐ Partial |
| **Auto DNS** | ✅ MagicDNS | ❌ Manual | ✅ MagicDNS |

*WireGuard on cellular requires Pi to have public IP + port forward

---

## Decision Factors

### Choose Tailscale If:

✅ You want it working in <30 minutes
✅ You don't want to configure router
✅ Your ISP uses CGNAT
✅ You value ease over control
✅ You want automatic device discovery
✅ You might add more devices later
✅ You don't want to debug network issues
✅ You're okay with Tailscale seeing connection metadata

**This is probably you.**

### Choose WireGuard If:

✅ You have networking experience
✅ You can configure router port forwarding
✅ You have a public IP (not CGNAT)
✅ You want maximum performance (<10ms latency)
✅ You want complete self-hosting
✅ You enjoy learning networking
✅ You have 4+ hours to set up initially
✅ You're comfortable troubleshooting connectivity

**This is for networking enthusiasts.**

### Choose Hybrid If:

✅ You need Tailscale's ease AND maximum privacy
✅ You're willing to pay for VPS
✅ You have advanced technical skills
✅ You want to run corporate-grade infrastructure

**This is overkill for py_home.**

---

## Recommendation: Tailscale

**Rationale:**

1. **Time Value:** 15 minutes vs 4 hours - spend time on features, not VPN config
2. **Reliability:** Works everywhere (CGNAT, cellular, public WiFi)
3. **Maintenance:** Zero ongoing maintenance
4. **home-geofence.js Already Designed for It:** Network detection, automatic fallback
5. **Not Security-Critical:** Home automation, not banking or medical records
6. **External APIs Already Cloud-Based:** Nest/Sensibo already send data to cloud
7. **Proven Track Record:** Used by developers worldwide

**Privacy Note:**
Tailscale can see connection metadata (when devices connect), but NOT the content (end-to-end encrypted). Since your home automation already relies on cloud APIs (Nest, Sensibo, ntfy.sh), adding Tailscale doesn't meaningfully change your privacy posture.

**Performance Note:**
Home automation is not latency-sensitive. 50ms vs 10ms latency doesn't matter when turning on lights or adjusting thermostat. User won't notice.

---

## Implementation Plan: Tailscale Setup

### Phase 1: Basic Setup (30 minutes)

**Step 1: Install on Pi (5 min)**
```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
sudo tailscale up

# Copy the URL shown and open in browser to authenticate
# Note the Tailscale IP assigned (e.g., 100.64.0.2)

# Verify
tailscale status
# Should show: connected
```

**Step 2: Install on Windows (5 min)**
```bash
# Download from: https://tailscale.com/download/windows
# Install exe
# Login with same account
# Verify Pi appears in device list
```

**Step 3: Install on iPhone (5 min)**
```
1. App Store → Search "Tailscale"
2. Install official Tailscale app
3. Open app → Login with same account
4. Enable VPN profile when prompted
5. Verify Pi appears in device list
```

**Step 4: Test Connection (5 min)**
```bash
# From laptop (on cellular or away from home WiFi)
ping 100.64.0.2

# Should get replies

# Test Pi endpoint
curl http://100.64.0.2:5000/status

# Should return: {"status": "ok"}
```

**Step 5: Update home-geofence.js (2 min)**
```javascript
// Update line 7 with actual Tailscale IP
piVPN: "http://100.64.0.2:5000",  // ← Replace with your Pi's Tailscale IP
```

**Step 6: Test iOS Geofencing Over VPN (5 min)**
```
1. Disable home WiFi on iPhone (use cellular)
2. Open Scriptable app
3. Run home-geofence.js manually
4. Check console output
5. Should see: "Home network: false" and call to VPN URL
```

---

### Phase 2: Advanced Configuration (Optional, 15 minutes)

**Enable MagicDNS (easier than IPs)**
```bash
# On Pi
sudo tailscale up --accept-dns

# Update home-geofence.js to use hostname
piVPN: "http://raspberrypi:5000",  // No need for IP!
```

**Configure ACLs (restrict access)**
```
# Go to: https://login.tailscale.com/admin/acls
# Add rules to restrict which devices can access Pi
```

**Enable Exit Node (optional - route all traffic through Pi)**
```bash
# On Pi
sudo tailscale up --advertise-exit-node

# On iPhone/laptop, enable exit node in Tailscale app
# Now ALL traffic goes through home network
```

---

### Phase 3: Testing (30 minutes)

**Test 1: Remote Deployment**
```bash
# From laptop on cellular (away from home)
scp automations/test.py matt.wheeler@100.64.0.2:~/py_home/automations/

# Should work!
```

**Test 2: Remote Debugging**
```bash
# From laptop on cellular
ssh matt.wheeler@100.64.0.2
tail -f ~/py_home/data/logs/automation.log

# Should work!
```

**Test 3: Geofencing Over Cellular**
```
1. Leave home (>200m)
2. Ensure iPhone on cellular (not WiFi)
3. iOS automation triggers home-geofence.js
4. Check logs on Pi
5. Should see: /leaving-home endpoint hit via Tailscale IP
```

**Test 4: Dashboard Access**
```
# From laptop on cellular
http://100.64.0.2:5000/dashboard

# Should load dashboard!
```

---

## Cost Comparison

| Option | Setup Cost | Monthly Cost | Time Cost |
|--------|-----------|--------------|-----------|
| **Tailscale** | $0 | $0 (free tier) | 30 min setup |
| **WireGuard** | $0 | $0 | 4 hours setup + 1 hour/year maintenance |
| **Hybrid** | $0 | $5-10 (VPS) | 6 hours setup + 2 hours/year maintenance |

**Tailscale free tier:**
- Up to 100 devices
- Unlimited bandwidth
- 1 user (3 users on free plan)
- Permanent free for personal use

---

## Security Considerations

### Tailscale Security Model

**Encrypted:**
- WireGuard encryption (ChaCha20-Poly1305)
- Keys exchanged automatically
- End-to-end encryption (Tailscale can't decrypt)

**Authentication:**
- OAuth/SSO (Google, GitHub, etc.)
- Device authorization required
- Can revoke devices anytime

**Attack Surface:**
- No open ports on router
- No exposed services to internet
- Devices only accessible within Tailscale network

**Metadata Visible to Tailscale:**
- Which devices connected
- Connection timestamps
- IP addresses

**Data Invisible to Tailscale:**
- Actual traffic content
- API calls
- Passwords/credentials

**Threat Model:**
- ✅ Protects against: Internet attackers, MITM, eavesdropping
- ✅ Protects against: ISP snooping (content encrypted)
- ⚠️ Does NOT protect against: Tailscale company being compromised (metadata exposed)
- ⚠️ Does NOT protect against: Tailscale company complying with government requests (metadata)

**For py_home:**
- Home automation data is low-sensitivity
- Already using cloud APIs (Nest, Sensibo)
- Threat model doesn't require hiding metadata
- **Tailscale security adequate**

---

## Alternative: Do Nothing (Current State)

### Pros

**✅ No Setup Time**
**✅ No New Dependencies**
**✅ Zero Cost**
**✅ Offline Queueing Already Works**

### Cons

**❌ Cannot Access Pi When Away**
- No remote debugging
- No remote deployment
- Must be home to test changes

**❌ Cannot Use Dashboard Remotely**
- Can't check home status while traveling
- Can't manually trigger automations remotely

**❌ Cannot SSH Remotely**
- Must be home for maintenance
- Can't fix issues while away

**Is This Acceptable?**
Maybe! If you're mostly home and offline queueing handles arrivals/departures, VPN might not be urgent. But it's very convenient to have.

---

## Next Steps

### Recommended: Start with Tailscale

**Week 1: Basic Setup**
1. Install Tailscale on Pi, laptop, iPhone (30 min)
2. Update home-geofence.js with Tailscale IP (2 min)
3. Test basic connectivity (10 min)

**Week 2: Real-World Testing**
1. Use VPN for deployment from away (try 3x)
2. Access dashboard remotely (try 5x)
3. Verify geofencing works over cellular (1-2 cycles)

**Week 3: Evaluate**
1. Did it work reliably?
2. Was setup pain worth convenience?
3. Any issues encountered?

**If Satisfied: Keep Using**
**If Issues: Consider WireGuard** (but unlikely)

---

## Resources

### Tailscale
- **Website:** https://tailscale.com
- **Docs:** https://tailscale.com/kb
- **Pi Guide:** https://tailscale.com/kb/1131/raspberry-pi
- **iOS App:** https://apps.apple.com/us/app/tailscale/id1470499037

### WireGuard
- **Website:** https://www.wireguard.com
- **Pi Guide:** https://www.wireguard.com/install/
- **Config Examples:** https://github.com/pirate/wireguard-docs

### Comparison Articles (2025)
- Tailscale vs WireGuard: https://tailscale.com/compare/wireguard
- XDA: 6 Reasons to Use Tailscale: https://www.xda-developers.com/reasons-use-tailscale-instead-wireguard/

---

## Related Files

- **Scriptable with VPN:** `scripts/ios/home-geofence.js` (lines 7, 74-76)
- **Architecture:** `docs/ARCHITECTURE.md`
- **Test Plan:** `docs/TWO_STAGE_ARRIVAL_TEST_PLAN.md`

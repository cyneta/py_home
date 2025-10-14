# Migrating Geofencing to Scriptable

## Overview

This guide walks through migrating home/away geofencing from iOS Shortcuts to Scriptable for more reliable automation.

**Why Scriptable?**
- JavaScript-based - real programming instead of visual blocks
- Background execution - no user interaction needed
- Better debugging - console logs and error messages
- Works offline - can queue actions until network available
- Version control - scripts are text files you can backup

## Current Architecture

**iOS Shortcuts (Current)**
```
iPhone Automation → Shortcuts → HTTP Request → Pi Flask Server
```

**Problems:**
- Only works when on home WiFi
- No banner notifications (silent failures)
- Can't queue actions when offline
- Hard to debug
- Shortcuts are complex visual flows

## Target Architecture

**Scriptable (Target)**
```
iPhone Location → Scriptable → Queue → VPN/Local Network → Pi Flask Server
```

**Improvements:**
- Works from anywhere (via VPN)
- Queues actions when offline
- Console logging for debugging
- Version control via iCloud
- Can add retry logic

---

## Prerequisites

### 1. Install Scriptable
- Download from App Store (free)
- Open and grant location permissions when prompted

### 2. Set Up VPN (Recommended)
See [VPN_SETUP.md](./VPN_SETUP.md) for detailed instructions.

**Quick options:**
- **Tailscale** (easiest) - Zero-config mesh VPN
- **WireGuard** (fast) - Modern VPN protocol
- **Skip VPN** (local only) - Only works on home WiFi

---

## Migration Steps

### Phase 1: Create Scriptable Geofence Script

#### 1.1 Create New Script in Scriptable

Open Scriptable app → Tap `+` → Name it "Home Geofence"

#### 1.2 Copy Base Script

```javascript
// Home Geofence Monitor
// Runs in background to detect home/away transitions

const config = {
  // Pi server URLs
  piLocal: "http://raspberrypi.local:5000",
  piVPN: "http://100.64.0.2:5000",  // Update with your Tailscale IP

  // Home location
  homeLat: 45.7054,
  homeLng: -121.5215,
  homeRadius: 150,  // meters

  // Auth (if enabled)
  authUser: "",  // Leave empty if auth disabled
  authPass: ""
};

// State management
const STATE_FILE = "geofence-state.json";

function getState() {
  const fm = FileManager.iCloud();
  const path = fm.joinPath(fm.documentsDirectory(), STATE_FILE);

  if (!fm.fileExists(path)) {
    return { isHome: null, lastCheck: null, queue: [] };
  }

  const data = fm.readString(path);
  return JSON.parse(data);
}

function saveState(state) {
  const fm = FileManager.iCloud();
  const path = fm.joinPath(fm.documentsDirectory(), STATE_FILE);
  fm.writeString(path, JSON.stringify(state));
}

function isAtHome(location) {
  const lat1 = location.latitude;
  const lon1 = location.longitude;
  const lat2 = config.homeLat;
  const lon2 = config.homeLng;

  // Haversine formula
  const R = 6371e3; // Earth radius in meters
  const φ1 = lat1 * Math.PI / 180;
  const φ2 = lat2 * Math.PI / 180;
  const Δφ = (lat2 - lat1) * Math.PI / 180;
  const Δλ = (lon2 - lon1) * Math.PI / 180;

  const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
            Math.cos(φ1) * Math.cos(φ2) *
            Math.sin(Δλ/2) * Math.sin(Δλ/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distance = R * c;

  return distance <= config.homeRadius;
}

async function callPiEndpoint(endpoint, isHomeNetwork) {
  const baseUrl = isHomeNetwork ? config.piLocal : config.piVPN;
  const url = `${baseUrl}${endpoint}`;

  console.log(`Calling: ${url}`);

  const req = new Request(url);
  req.method = "POST";
  req.headers = { "Content-Type": "application/json" };

  if (config.authUser && config.authPass) {
    const auth = btoa(`${config.authUser}:${config.authPass}`);
    req.headers["Authorization"] = `Basic ${auth}`;
  }

  try {
    const response = await req.loadJSON();
    console.log(`✓ Success: ${JSON.stringify(response)}`);
    return { success: true, response };
  } catch (error) {
    console.error(`✗ Failed: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function processQueue(state, isHomeNetwork) {
  console.log(`Processing queue: ${state.queue.length} items`);

  const processed = [];
  for (const item of state.queue) {
    const result = await callPiEndpoint(item.endpoint, isHomeNetwork);
    if (result.success) {
      processed.push(item);
    }
  }

  // Remove successful items
  state.queue = state.queue.filter(item => !processed.includes(item));
  console.log(`Processed ${processed.length}, ${state.queue.length} remaining`);
}

async function main() {
  console.log("=== Home Geofence Check ===");

  // Get current location
  Location.setAccuracyToThreeKilometers();
  const location = await Location.current();
  console.log(`Location: ${location.latitude}, ${location.longitude}`);

  // Check if at home
  const atHome = isAtHome(location);
  console.log(`At home: ${atHome}`);

  // Load state
  const state = getState();
  console.log(`Previous state: ${state.isHome}`);

  // Check for state change
  const changed = state.isHome !== atHome;

  if (changed) {
    console.log(`STATE CHANGE: ${state.isHome} → ${atHome}`);

    // Determine endpoint
    const endpoint = atHome ? "/im-home" : "/leaving-home";

    // Try to call Pi (might fail if off-network)
    const isHomeNetwork = false;  // TODO: Add network detection
    const result = await callPiEndpoint(endpoint, isHomeNetwork);

    if (!result.success) {
      // Queue for later
      console.log("Queueing action for later...");
      state.queue.push({
        endpoint,
        timestamp: new Date().toISOString(),
        transition: atHome ? "arrived" : "departed"
      });
    }

    // Update state
    state.isHome = atHome;
    state.lastCheck = new Date().toISOString();
    saveState(state);

    // Show notification
    const notification = new Notification();
    notification.title = atHome ? "🏠 Arrived Home" : "🚗 Left Home";
    notification.body = result.success
      ? "Automation triggered"
      : "Will sync when network available";
    notification.schedule();
  } else {
    console.log("No change");

    // Try to process queue if any
    if (state.queue.length > 0) {
      const isHomeNetwork = false;  // TODO: Add network detection
      await processQueue(state, isHomeNetwork);
      saveState(state);
    }
  }

  console.log("=== Complete ===");
}

// Run
await main();
Script.complete();
```

#### 1.3 Update Configuration

Edit these values in the script:

```javascript
const config = {
  piLocal: "http://raspberrypi.local:5000",
  piVPN: "http://YOUR_VPN_IP:5000",  // Get from VPN setup

  homeLat: 45.7054,   // Your home coordinates
  homeLng: -121.5215,  // (same as config.yaml)
  homeRadius: 150,

  authUser: "",  // Leave empty if auth disabled on Pi
  authPass: ""
};
```

### Phase 2: Set Up Background Automation

#### 2.1 Create iOS Automation

1. Open **Shortcuts** app
2. Go to **Automation** tab
3. Tap `+` → **Create Personal Automation**
4. Choose **Time of Day**
5. Set to **Daily** at current time
6. **Repeat** → Every 5 minutes (or 15 minutes to save battery)
7. Add action: **Run Script**
8. Choose your "Home Geofence" script
9. **Disable** "Ask Before Running"
10. Tap **Done**

**Note:** iOS will run this every 5-15 minutes in the background.

#### 2.2 Test Manual Run

1. Open Scriptable
2. Select "Home Geofence" script
3. Tap ▶️ to run
4. Check console output for errors
5. Verify notification appears

### Phase 3: Add Network Detection

Enhance the script to detect if you're on home WiFi:

```javascript
async function isOnHomeNetwork() {
  try {
    // Quick ping to Pi local address
    const req = new Request(`${config.piLocal}/status`);
    req.timeoutInterval = 2;  // 2 second timeout
    await req.load();
    return true;
  } catch {
    return false;
  }
}

async function main() {
  // ... existing code ...

  // Detect network
  const isHomeNetwork = await isOnHomeNetwork();
  console.log(`Home network: ${isHomeNetwork}`);

  // Use correct URL
  const result = await callPiEndpoint(endpoint, isHomeNetwork);

  // ... rest of code ...
}
```

### Phase 4: Migrate Endpoints

Update Scriptable script to call the same endpoints as your Shortcuts:

**Current Shortcuts:**
- Leaving Home → `/leaving-home` ✓ (already in script)
- I'm Home → `/im-home` ✓ (already in script)
- Good Morning → `/good-morning` (add if needed)
- Goodnight → `/goodnight` (add if needed)

**To add more endpoints:**

```javascript
// Add to callPiEndpoint function
const endpoints = {
  imHome: "/im-home",
  leavingHome: "/leaving-home",
  goodMorning: "/good-morning",
  goodnight: "/goodnight"
};

// Call like this:
await callPiEndpoint(endpoints.goodMorning, isHomeNetwork);
```

### Phase 5: Test & Validate

#### 5.1 Test Arrival
1. Walk/drive away from home (>150m)
2. Wait 5-15 minutes for automation to run
3. Check Scriptable console logs
4. Verify Pi received request (check dashboard or logs)

#### 5.2 Test Departure
1. Return home
2. Wait for automation
3. Check notification appears
4. Verify automation triggered

#### 5.3 Test Offline Queue
1. Enable Airplane Mode
2. Manually run script (simulate geofence trigger)
3. Check that action is queued
4. Disable Airplane Mode
5. Run script again
6. Verify queued action executes

### Phase 6: Decommission iOS Shortcuts

Once Scriptable is working reliably:

1. **Keep these Shortcuts** (manual triggers):
   - Good Morning (manual button)
   - Goodnight (manual button)
   - Any voice command shortcuts

2. **Delete these Shortcuts** (now handled by Scriptable):
   - Leaving Home (location automation)
   - I'm Home (location automation)
   - Any geofence-triggered automations

3. **Disable location automations:**
   - Open Shortcuts → Automation tab
   - Delete or disable all location-based automations

---

## Troubleshooting

### Script doesn't run in background
- Check iOS Automation is enabled
- Verify "Ask Before Running" is OFF
- Check Scriptable has location permissions: Settings → Scriptable → Location → Always

### Can't reach Pi when away from home
- Verify VPN is connected (check Tailscale/WireGuard app)
- Test VPN URL in Safari: `http://YOUR_VPN_IP:5000/status`
- Check `piVPN` URL in script matches VPN IP

### Geofence too sensitive (false triggers)
- Increase `homeRadius` from 150 to 200-300 meters
- iOS location updates can be inaccurate indoors

### Battery drain
- Reduce automation frequency from 5min to 15min
- Use `Location.setAccuracyToThreeKilometers()` instead of high accuracy

### Notifications not appearing
- Check iOS Settings → Notifications → Scriptable → Allow Notifications
- Check "Show Previews" is enabled

### Queue not processing
- Add logging to verify queue persistence
- Check iCloud sync is enabled for Scriptable
- Manually run script when network available

---

## Advanced Features

### Add Time-Based Logic

Only trigger automations during certain hours:

```javascript
function shouldTriggerAutomation() {
  const hour = new Date().getHours();

  // Don't trigger leaving_home at night
  if (endpoint === "/leaving-home" && (hour < 6 || hour > 23)) {
    console.log("Skipping: Too late/early");
    return false;
  }

  return true;
}
```

### Add Cooldown Period

Prevent rapid re-triggers:

```javascript
function needsCooldown(state) {
  if (!state.lastCheck) return false;

  const lastCheck = new Date(state.lastCheck);
  const now = new Date();
  const minutesSince = (now - lastCheck) / 1000 / 60;

  return minutesSince < 10;  // 10 minute cooldown
}
```

### Add Retry Logic

Retry failed requests with exponential backoff:

```javascript
async function callWithRetry(endpoint, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const result = await callPiEndpoint(endpoint, false);
    if (result.success) return result;

    // Exponential backoff: 1s, 2s, 4s
    await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
  }

  return { success: false, error: "Max retries exceeded" };
}
```

---

## Next Steps

After Scriptable is stable:

1. **Set up VPN** - See [VPN_SETUP.md](./VPN_SETUP.md)
2. **Add more automations** - Time-based, weather-based triggers
3. **Create Scriptable widgets** - Show home status on home screen
4. **Sync across devices** - Scripts sync via iCloud automatically

---

## Rollback Plan

If you need to revert to iOS Shortcuts:

1. Re-enable location automations in Shortcuts
2. Disable Scriptable time-based automation
3. Keep Scriptable installed for testing/debugging
4. Your Pi endpoints haven't changed, so Shortcuts will work immediately

---

## References

- [Scriptable Documentation](https://docs.scriptable.app)
- [Scriptable Community](https://talk.automators.fm/c/scriptable)
- [iOS Background Automation Limits](https://support.apple.com/guide/shortcuts/run-automations-apd602971e63/ios)

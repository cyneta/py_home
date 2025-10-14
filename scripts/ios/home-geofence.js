// Home Geofence Monitor
// Runs in background to detect home/away transitions

const config = {
  // Pi server URLs
  piLocal: "http://raspberrypi.local:5000",
  piVPN: "http://100.107.121.6:5000",  // Tailscale IP (or use "raspberrypi" with MagicDNS)

  // Home location (must match config/config.yaml)
  homeLat: 45.70766068698601,
  homeLng: -121.53682676696884,
  homeRadius: 150,  // meters

  // Auth (if enabled on Pi)
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

  // Haversine formula for distance calculation
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
  if (state.queue.length === 0) return;

  console.log(`Processing queue: ${state.queue.length} items`);

  const processed = [];
  for (const item of state.queue) {
    const result = await callPiEndpoint(item.endpoint, isHomeNetwork);
    if (result.success) {
      console.log(`✓ Processed queued action: ${item.endpoint}`);
      processed.push(item);
    }
  }

  // Remove successful items
  state.queue = state.queue.filter(item => !processed.includes(item));
  console.log(`Processed ${processed.length}, ${state.queue.length} remaining`);
}

async function main() {
  console.log("=== Home Geofence Check ===");

  // Get parameter from iOS automation (if provided)
  const trigger = args.plainTexts[0] || "manual";
  console.log(`Triggered by: ${trigger}`);

  // Get current location
  Location.setAccuracyToThreeKilometers();
  const location = await Location.current();
  console.log(`Location: ${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`);

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
    // Arrival: Use pre-arrival (Stage 1 - HVAC + outdoor lights)
    // Departure: Use leaving-home
    const endpoint = atHome ? "/pre-arrival" : "/leaving-home";

    // Detect network
    const isHomeNetwork = await isOnHomeNetwork();
    console.log(`Home network: ${isHomeNetwork}`);

    // Try to call Pi
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
      const isHomeNetwork = await isOnHomeNetwork();
      console.log(`Home network: ${isHomeNetwork}`);
      await processQueue(state, isHomeNetwork);
      saveState(state);
    }

    // Update last check timestamp
    state.lastCheck = new Date().toISOString();
    saveState(state);
  }

  console.log("=== Complete ===");
}

// Run
await main();
Script.complete();

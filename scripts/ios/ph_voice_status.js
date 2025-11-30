// py_home Voice Status
// Returns speakable house status for Siri
//
// Usage:
// 1. Copy to Scriptable app
// 2. Create Shortcut: Run Script → Speak Text
// 3. "Hey Siri, house status"

const config = {
  piLocal: "http://raspberrypi.local:5000",
  piVPN: "http://100.107.121.6:5000"
};

async function getStatus() {
  // Try local first, fall back to VPN
  const urls = [config.piLocal, config.piVPN];

  for (const baseUrl of urls) {
    try {
      const req = new Request(`${baseUrl}/voice-status`);
      req.timeoutInterval = 5;
      const response = await req.loadJSON();

      if (response.speech) {
        return response.speech;
      }
    } catch (e) {
      console.log(`Failed ${baseUrl}: ${e.message}`);
    }
  }

  return "Sorry, could not connect to home server.";
}

// Main
const speech = await getStatus();
console.log(speech);

// Return for Shortcuts to speak
Script.setShortcutOutput(speech);
Script.complete();

# iOS Shortcuts Setup Guide

Complete guide to setting up voice-controlled home automation via iOS Shortcuts and Siri.

---

## Overview

**Hybrid Approach:**
- **Direct shortcuts** for common commands (fast, free, reliable)
- **AI-powered shortcut** for complex/flexible commands (smart, costs ~$0.01/command)

---

## Prerequisites

1. ✅ py_home deployed to Raspberry Pi
2. ✅ Flask server running on Pi
3. ✅ Pi accessible via `raspberrypi.local` (mDNS)
4. ✅ iPhone on same WiFi network as Pi
5. ✅ iOS Shortcuts app installed (built-in on iOS 13+)

---

## Part 1: Direct Shortcuts (Recommended for Common Tasks)

These shortcuts are **instant, free, and work offline** (once created).

### Voice Feedback Pattern

All shortcuts below include **Siri voice feedback** using this pattern:

```
1. Get Contents of URL → Call API
2. Get Dictionary from Input → Parse JSON response
3. Get Dictionary Value → Extract "message" field
4. Speak Text → Siri speaks the message
```

**Why this matters:**
- ✅ Siri confirms the action completed
- ✅ You hear the result without looking at your phone
- ✅ Errors are spoken (e.g., "Device not responding")
- ✅ Two-way conversation (you speak, Siri responds)

**Optional:** Toggle "Wait Until Finished" in Speak Text action:
- **ON:** Siri finishes speaking before shortcut completes
- **OFF:** Siri speaks while other actions continue (faster)

### Shortcut 1: "I'm Leaving" (with Voice Feedback)

**Steps:**
1. Open **Shortcuts** app
2. Tap **+** (new shortcut)
3. Tap **Add Action**
4. Search for **"Get Contents of URL"**
5. Configure:
   - **URL:** `http://raspberrypi.local:5000/leaving-home`
   - **Method:** POST
   - **Headers:** (if auth enabled) `Authorization: Bearer YOUR_API_KEY`
6. Tap **Add Action** → Search for **"Get Dictionary from Input"**
7. Tap **Add Action** → Search for **"Get Dictionary Value"**
   - Key: `message`
8. Tap **Add Action** → Search for **"Speak Text"**
   - Text: `Dictionary Value`
   - Wait Until Finished: ON (optional)
9. Tap shortcut name → Rename to **"I'm Leaving"**
10. Tap **Done**

**Test:**
- Tap the shortcut → Should turn off outlets, set Nest to 62°F
- Say **"Hey Siri, I'm leaving"** → Siri speaks: *"Leaving home activated. House secured."*

**What it does:**
- Sets Nest to away temp (62°F)
- Turns off all Tapo outlets
- Sends notification
- **Siri speaks confirmation**

---

### Shortcut 2: "Goodnight" (with Voice Feedback)

**Steps:**
1. Create new shortcut
2. Add action: **Get Contents of URL**
   - **URL:** `http://raspberrypi.local:5000/goodnight`
   - **Method:** POST
3. Add action: **Get Dictionary from Input**
4. Add action: **Get Dictionary Value**
   - Key: `message`
5. Add action: **Speak Text**
   - Text: `Dictionary Value`
6. Rename to **"Goodnight"**

**Voice trigger:** "Hey Siri, goodnight"

**Siri response:** *"Sleep mode activated. Goodnight."*

**What it does:**
- Sets Nest to sleep temp (68°F)
- Turns off Sensibo AC
- Turns off all outlets
- Sends notification
- **Siri speaks confirmation**

---

### Shortcut 3: "I'm Home" (with Voice Feedback)

**Steps:**
1. Create new shortcut
2. Add action: **Get Contents of URL**
   - **URL:** `http://raspberrypi.local:5000/im-home`
   - **Method:** POST
3. Add action: **Get Dictionary from Input**
4. Add action: **Get Dictionary Value**
   - Key: `message`
5. Add action: **Speak Text**
   - Text: `Dictionary Value`
6. Rename to **"I'm Home"**

**Voice trigger:** "Hey Siri, I'm home"

**Siri response:** *"Welcome home! House is ready."*

**What it does:**
- Sets Nest to comfort temp (72°F)
- Sends welcome notification
- **Siri speaks welcome message**

---

### Shortcut 4: "Good Morning" (with Voice Feedback)

**Steps:**
1. Create new shortcut
2. Add action: **Get Contents of URL**
   - **URL:** `http://raspberrypi.local:5000/good-morning`
   - **Method:** POST
3. Add action: **Get Dictionary from Input**
4. Add action: **Get Dictionary Value**
   - Key: `message`
5. Add action: **Speak Text**
   - Text: `Dictionary Value`
6. Rename to **"Good Morning"**

**Voice trigger:** "Hey Siri, good morning"

**Siri response:** *"Good morning! Portland: 74°F, scattered clouds. High 74°, Low 74°."*

**What it does:**
- Sets Nest to 70°F
- Gets weather forecast
- Sends morning summary notification
- **Siri speaks weather report**

---

### Shortcut 5: "What's the Traffic?" (with Voice Feedback)

**Steps:**
1. Create new shortcut
2. Add action: **Get Contents of URL**
   - **URL:** `http://raspberrypi.local:5000/travel-time`
   - **Method:** GET
3. Add action: **Get Dictionary from Input**
4. Add action: **Get Dictionary Value**
   - Key: `summary`
5. Add action: **Speak Text**
   - Text: `Dictionary Value`
6. Rename to **"Traffic to Work"**

**Voice trigger:** "Hey Siri, what's the traffic?"

**Siri response:** *"23 minutes to work. Light traffic on I-80."*

**What it does:**
- Gets current travel time to work (Google Maps)
- Checks traffic conditions
- **Siri speaks travel time and conditions**

---

## Part 2: AI-Powered Shortcut (Flexible Natural Language)

This shortcut handles **any command** via natural language.

### "Ask Home" Shortcut

**Steps:**
1. Create new shortcut named **"Ask Home"**
2. Add action: **Ask for Input**
   - Prompt: "What would you like to do?"
   - Input type: Text
3. Add action: **Get Contents of URL**
   - URL: `http://raspberrypi.local:5000/ai-command`
   - Method: POST
   - Request Body: JSON
   - Add field: `command` = `Provided Input`
4. Add action: **Get Dictionary from Input**
5. Add action: **Get Value for Key** → `message` from dictionary
6. Add action: **Show Notification**
   - Title: "Home Automation"
   - Body: `Dictionary Value` (the message)

**Usage:**
- Say **"Hey Siri, ask home"**
- Siri asks: "What would you like to do?"
- You say:
  - "Turn off all the lights"
  - "Set temperature to 72"
  - "Make it warmer"
  - "What's the bedroom temperature?"
  - "Turn on the heater"
  - "Turn everything off"

**What it does:**
- Sends your text to Claude AI
- AI parses intent and parameters
- Executes appropriate automation/device command
- Returns result message

**Advantages:**
- ✅ Say it however you want (flexible phrasing)
- ✅ One shortcut handles everything
- ✅ Can handle complex requests
- ✅ Understands context ("make it warmer" knows to increase temp)

**Disadvantages:**
- ❌ Slower (adds 1-2 second AI processing)
- ❌ Costs ~$0.01 per command (Claude API)
- ❌ Requires internet connection
- ❌ Two-step process (Siri asks what you want)

---

## Part 3: Advanced Shortcuts

### Shortcut: "Set Temperature"

**More interactive - asks for temperature value**

**Steps:**
1. Create new shortcut **"Set Temperature"**
2. Add action: **Ask for Input**
   - Prompt: "What temperature?"
   - Input type: Number
3. Add action: **URL**
   - URL: `http://raspberrypi.local:5000/ai-command`
4. Add action: **Get Contents of URL**
   - Method: POST
   - Request Body: JSON
   - Add field: `command` = `Set temperature to [Provided Input]`
5. Add confirmation notification

**Usage:**
- Say **"Hey Siri, set temperature"**
- Siri asks: "What temperature?"
- You say: "72"
- Nest sets to 72°F

---

### Shortcut: "Control Outlet"

**Interactive - asks which outlet and action**

**Steps:**
1. Create new shortcut **"Control Outlet"**
2. Add action: **Choose from List**
   - Prompt: "Which outlet?"
   - List items: Heater, Bedroom Right Lamp, Livingroom Lamp, Bedroom Left Lamp
3. Add action: **Choose from Menu**
   - Prompt: "What action?"
   - Menu items: Turn On, Turn Off
4. Add action: **Get Contents of URL**
   - URL: `http://raspberrypi.local:5000/ai-command`
   - Method: POST
   - Request Body: JSON
   - Add field: `command` = `[Menu Item] [Chosen Item]`

**Usage:**
- Say **"Hey Siri, control outlet"**
- Choose outlet from list
- Choose Turn On or Turn Off
- Outlet is controlled

---

## Part 4: Automation Shortcuts

### Auto-trigger shortcuts based on location or time

**Automation: Arrive Home**

**Steps:**
1. Open **Shortcuts** app
2. Go to **Automation** tab
3. Tap **+** → **Create Personal Automation**
4. Choose **Arrive**
5. Choose **Home** location
6. Tap **Next**
7. Add action: **Run Shortcut** → select "I'm Home" shortcut
8. **Disable "Ask Before Running"** (optional - runs automatically)
9. Tap **Done**

**Result:** When you arrive home (iPhone detects home WiFi/GPS), automatically:
- Sets Nest to 72°F
- Sends welcome notification

---

**Automation: Leave Home**

Same process, but:
- Trigger: **Leave** home
- Action: Run **"I'm Leaving"** shortcut

---

**Automation: Bedtime**

Same process, but:
- Trigger: **Time of Day** → 10:30 PM
- Action: Run **"Goodnight"** shortcut

---

## Part 5: Troubleshooting

### "Could not connect to server"

**Check:**
1. Is Pi on and connected to WiFi?
   ```bash
   ping raspberrypi.local
   ```
2. Is Flask server running?
   ```bash
   ssh pi@raspberrypi.local
   sudo systemctl status py_home
   ```
3. Is iPhone on same WiFi network?

**Fix:**
- Restart Pi: `sudo reboot`
- Restart Flask: `sudo systemctl restart py_home`
- Use IP instead of hostname: `http://192.168.1.100:5000/...`

---

### "Request timed out"

**Check:**
1. Automation taking too long to execute?
2. Device not responding?

**Fix:**
- Check Flask logs: `sudo journalctl -u py_home -f`
- Test automation manually: `python automations/leaving_home.py`

---

### "Invalid response"

**Check:**
1. Is Flask returning JSON?
2. Is endpoint correct?

**Fix:**
- Test endpoint with curl:
  ```bash
  curl -X POST http://raspberrypi.local:5000/leaving-home
  ```
- Check for errors in Flask logs

---

### AI commands not working

**Check:**
1. Is ANTHROPIC_API_KEY set in `.env`?
2. Do you have API credits?

**Fix:**
- Test AI handler:
  ```bash
  cd ~/py_home
  source venv/bin/activate
  python server/ai_handler.py "turn on the heater" --dry-run
  ```
- Check API key is valid
- Check Claude API status

---

## Part 6: Cost Analysis

### Direct Shortcuts (Free)
- No API calls
- No cost
- **Recommended for:** All common tasks

### AI-Powered Shortcut
- Uses Claude API
- Cost: ~$0.01 per command (varies by complexity)
- Example usage: 10 AI commands/day = $3/month
- **Recommended for:** Rare/complex commands only

**Cost Optimization:**
- Use direct shortcuts for 90% of commands
- Use AI only for complex/one-off requests
- Set API usage alerts in Anthropic console

---

## Part 7: Security Considerations

### Current Setup (Local Network Only)
- Flask server only accessible on local WiFi
- No internet exposure
- No authentication required (trusted network)

**Risk:** Anyone on your WiFi can control your home

### Add Authentication (Optional)

**1. Generate API key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**2. Add to Pi's .env:**
```bash
API_KEY=your-generated-key-here
```

**3. Update Flask to check API key** (server/routes.py already has @require_auth)

**4. Update shortcuts:**
- In "Get Contents of URL" action
- Add **Header**:
  - Name: `Authorization`
  - Value: `Bearer your-api-key`

**Result:** Shortcuts require API key to work

---

## Part 8: Tips & Tricks

### Tip 1: Combine Shortcuts
Create a "Movie Time" shortcut that:
- Sets Nest to 70°F
- Turns off all lights
- Turns on livingroom lamp at 20%

### Tip 2: Use Conditional Logic
Add "If" conditions to shortcuts:
- Only run if time is after 6 PM
- Only run if temperature below 65°F

### Tip 3: Share Shortcuts
Export and share with family:
- Tap shortcut → ⋯ → Share
- Send via AirDrop/Messages

### Tip 4: Siri Phrase Alternatives
Add multiple phrases for same shortcut:
- Settings → Siri & Search → My Shortcuts
- Tap shortcut → Add to Siri
- Record alternate phrase

### Tip 5: Widget Access
Add shortcuts to home screen:
- Long press home screen → Widgets
- Search "Shortcuts"
- Add Shortcuts widget
- Select your shortcuts

---

## Quick Reference

### Direct Shortcut URLs
```
Status:        http://raspberrypi.local:5000/status
Leaving home:  http://raspberrypi.local:5000/leaving-home
Goodnight:     http://raspberrypi.local:5000/goodnight
I'm home:      http://raspberrypi.local:5000/im-home
Good morning:  http://raspberrypi.local:5000/good-morning
Travel time:   http://raspberrypi.local:5000/travel-time
Add task:      http://raspberrypi.local:5000/add-task
AI command:    http://raspberrypi.local:5000/ai-command
```

### AI Command Examples
```
"Turn off all lights"
"Set temperature to 72"
"Make it warmer" (increases by 2°F)
"Make it cooler" (decreases by 2°F)
"What's the temperature?"
"Turn on the heater"
"Turn off bedroom lamp"
"Turn everything off"
"Set AC to 70 in cool mode"
```

---

**End of Guide**

**Next Steps:**
1. Create 4-5 direct shortcuts for common tasks
2. Test with voice commands
3. Create "Ask Home" AI shortcut for rare/complex commands
4. Set up location-based automations
5. Share shortcuts with family

**Estimated Setup Time:** 20-30 minutes for all shortcuts

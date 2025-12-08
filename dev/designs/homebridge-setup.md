# Homebridge Setup Plan

## Overview
Install and configure Homebridge on py5-home to enable Siri/HomeKit control of:
- Nest thermostat
- Sensibo AC controller
- Roborock vacuum

## Installation Status
- [x] Homebridge 1.7.17 installed via apt
- [x] systemd service running
- [x] Web UI accessible at http://py5-home.local:8581
- [ ] Initial login and password change
- [ ] Plugin installation
- [ ] Plugin configuration
- [ ] HomeKit pairing

## Required Plugins

### 1. Nest Thermostat
**Plugin name:** `homebridge-nest`
**NPM:** https://www.npmjs.com/package/homebridge-nest
**GitHub:** https://github.com/chrisjshull/homebridge-nest

**Configuration needed:**
- Google account (already using Google SDM API)
- Project ID: From config/.env NEST_PROJECT_ID
- Client ID: From config/.env NEST_CLIENT_ID
- Client Secret: From config/.env NEST_CLIENT_SECRET
- Refresh token: From config/.env NEST_REFRESH_TOKEN

**Alternative option:** `homebridge-google-nest-sdm` (uses same SDM API we already have)

**Notes:**
- Google announced discontinuation of 1st/2nd gen Nest support on Oct 25, 2025
- Both plugins work with Google SDM API (which we already use in py_home)

### 2. Sensibo AC Controller
**Plugin name:** `homebridge-sensibo-ac`
**NPM:** https://www.npmjs.com/package/homebridge-sensibo-ac
**GitHub:** https://github.com/nitaybz/homebridge-sensibo-ac

**Configuration needed:**
- Sensibo API key: From config/.env SENSIBO_API_KEY
- Device auto-detection should find AC ID: 6WwepeGh

**Features:**
- HeaterCooler accessory with fan speed and swing control
- Occupancy sensor and Climate React support
- Filter cleaning indication
- Temperature/humidity history in Eve app

### 3. Roborock Vacuum
**Plugin choice:** NEED TO DETERMINE
- If using Mi Home app: `homebridge-xiaomi-roborock-vacuum`
- If using Roborock app: `homebridge-roborock-vacuum` or `homebridge-roborock-control`

**Configuration needed:**
- Check which app controls the vacuum (Mi Home vs Roborock)
- Username/password from that app account
- Note: config/.env shows ROBOROCK_USERNAME and ROBOROCK_PASSWORD are empty

**Action needed:**
- Verify which app is currently used
- Get credentials for that app
- Update config/.env with credentials

## Setup Steps

### 1. Initial Login
1. Open http://py5-home.local:8581
2. Login with admin/admin
3. Change password immediately
4. Update config/.env or password manager with new credentials

### 2. Install Plugins
From Homebridge UI > Plugins tab:
1. Search for "homebridge-nest"
2. Search for "homebridge-sensibo-ac"
3. Search for appropriate Roborock plugin (TBD based on app)
4. Install all three

### 3. Configure Nest Plugin
In Config tab, add:
```json
{
  "platform": "Nest",
  "access_token": "[from NEST_REFRESH_TOKEN]",
  "googleAuth": {
    "projectId": "b8e3fce2-20f4-471f-80e3-d08be2432b75",
    "clientId": "493001564141-vbibre8pa03t5mv3tsk6hiqg2ga2an49.apps.googleusercontent.com",
    "clientSecret": "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"
  }
}
```

### 4. Configure Sensibo Plugin
In Config tab, add:
```json
{
  "platform": "SensiboAC",
  "apiKey": "LqTrEXkgAJZEm4wfsWpdkIL5lXwx3s"
}
```

### 5. Configure Roborock Plugin
TBD - depends on which app/plugin we choose

### 6. Add to Home App
1. In Homebridge UI > Settings
2. Find HomeKit QR code
3. Open iPhone Home app
4. Add Accessory > Scan QR code
5. Enter Homebridge PIN

### 7. Test Siri Commands
- "Hey Siri, set temperature to 70 degrees"
- "Hey Siri, turn on the air conditioner"
- "Hey Siri, start vacuuming"

### 8. Remove Old Bridge
Once confirmed working:
1. Open Home app
2. Remove "Pantry Homebridge 964A CBF6"
3. Verify all devices moved to new bridge

## Open Questions
1. Which app controls the Roborock? (Mi Home vs Roborock app)
2. What are the Roborock app credentials?
3. Should we use homebridge-nest or homebridge-google-nest-sdm for Nest?

## References
- Homebridge: https://homebridge.io
- Homebridge Nest: https://github.com/chrisjshull/homebridge-nest
- Homebridge Sensibo: https://github.com/nitaybz/homebridge-sensibo-ac
- Sensibo API: https://home.sensibo.com/me/api

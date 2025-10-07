# Google Nest API Setup Guide

**Status**: Active (2025)
**Cost**: $5 one-time Device Access registration fee
**API**: Smart Device Management (SDM) API

---

## Overview

Google Nest thermostats (including 3rd gen) are controlled via the Smart Device Management API. This replaced the old "Works with Nest" API.

**What you can control**:
- Thermostat mode (HEAT, COOL, HEATCOOL, OFF, ECO)
- Temperature setpoints
- Fan mode
- Read current temperature, humidity

**Limitations**:
- Temperatures must be in Celsius (API requirement)
- Requires Device Access registration ($5 one-time)
- OAuth2 authentication (token refresh needed)

---

## Setup Steps

### 1. Register for Device Access

1. Go to https://console.nest.google.com/device-access/
2. Pay $5 one-time registration fee
3. Accept terms of service

### 2. Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create new project: "Home Automation" (or similar)
3. Note the **Project ID**

### 3. Enable Smart Device Management API

1. In Google Cloud Console, go to APIs & Services
2. Click "+ ENABLE APIS AND SERVICES"
3. Search for "Smart Device Management API"
4. Click Enable

### 4. Create OAuth2 Credentials

1. Go to APIs & Services → Credentials
2. Click "+ CREATE CREDENTIALS" → OAuth client ID
3. Application type: **Web application**
4. Name: "py_home"
5. Authorized redirect URIs: Add
   - `http://localhost:8080` (for local testing)
   - `https://www.google.com` (alternative)
6. Click Create
7. Download credentials JSON or copy:
   - **Client ID**
   - **Client Secret**

### 5. Create Device Access Project

1. Go back to https://console.nest.google.com/device-access/
2. Click "Create project"
3. Project name: "py_home"
4. OAuth client ID: Paste from step 4
5. Click "Enable events" (optional)
6. Click Next
7. Note the **Project ID** (format: `projects/PROJECT_ID`)

### 6. Link Nest Account

1. In Device Access console, click "Link account"
2. Sign in with Google account that owns Nest devices
3. Authorize access
4. Your devices should appear in the console

### 7. Get OAuth Tokens

**First-time authentication** requires browser flow:

```python
# Run this once to get tokens
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/sdm.service']

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=SCOPES
)

credentials = flow.run_local_server(port=8080)

print("Refresh token:", credentials.refresh_token)
print("Access token:", credentials.token)
```

Save the **refresh token** to `.env` - it doesn't expire!

---

## Configuration

Add to `config/.env`:

```bash
# Google Nest API
NEST_PROJECT_ID=projects/your-project-id-here
NEST_CLIENT_ID=your-client-id.apps.googleusercontent.com
NEST_CLIENT_SECRET=your-client-secret
NEST_REFRESH_TOKEN=your-refresh-token-from-step-7
```

Add to `config/config.yaml`:

```yaml
nest:
  project_id: "${NEST_PROJECT_ID}"
  client_id: "${NEST_CLIENT_ID}"
  client_secret: "${NEST_CLIENT_SECRET}"
  refresh_token: "${NEST_REFRESH_TOKEN}"

  # Device ID (find after linking account)
  device_id: "enterprises/PROJECT_ID/devices/DEVICE_ID"

  # Temperature presets (Fahrenheit for convenience)
  away_temp: 62
  sleep_temp: 68
  comfort_temp: 72
```

---

## Finding Your Device ID

Once devices are linked:

```python
import requests

access_token = "YOUR_ACCESS_TOKEN"
project_id = "projects/YOUR_PROJECT_ID"

resp = requests.get(
    f"https://smartdevicemanagement.googleapis.com/v1/{project_id}/devices",
    headers={"Authorization": f"Bearer {access_token}"}
)

devices = resp.json()
print(devices)

# Find your thermostat
for device in devices.get('devices', []):
    print(f"Name: {device['name']}")
    print(f"Type: {device['type']}")
```

Copy the full device `name` (e.g., `enterprises/.../devices/...`) to config.

---

## Python Library

**Recommended**: `python-google-nest`

```bash
pip install python-google-nest
```

**Alternative**: Use `requests` library directly (our approach for simplicity)

---

## API Reference

**Base URL**: `https://smartdevicemanagement.googleapis.com/v1`

### Get Device Info
```
GET /enterprises/{enterprise_id}/devices/{device_id}
```

### Set Temperature (Heat mode)
```
POST /enterprises/{enterprise_id}/devices/{device_id}:executeCommand
{
  "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat",
  "params": {
    "heatCelsius": 20.0
  }
}
```

### Set Temperature (Cool mode)
```
POST /enterprises/{enterprise_id}/devices/{device_id}:executeCommand
{
  "command": "sdm.devices.commands.ThermostatTemperatureSetpoint.SetCool",
  "params": {
    "coolCelsius": 22.0
  }
}
```

### Set Mode
```
POST /enterprises/{enterprise_id}/devices/{device_id}:executeCommand
{
  "command": "sdm.devices.commands.ThermostatMode.SetMode",
  "params": {
    "mode": "HEAT"  // or "COOL", "HEATCOOL", "OFF"
  }
}
```

---

## Temperature Conversion

API requires Celsius, but we work in Fahrenheit:

```python
def f_to_c(fahrenheit):
    return round((fahrenheit - 32) * 5 / 9, 1)

def c_to_f(celsius):
    return round(celsius * 9 / 5 + 32, 1)
```

---

## Common Issues

### "Invalid OAuth token"
- Access tokens expire after 1 hour
- Use refresh token to get new access token
- Our `nest_api.py` handles this automatically

### "Device not found"
- Check device_id in config matches actual device name
- Run device list command to verify

### "Permission denied"
- Ensure Device Access project is created
- Verify account linking is complete
- Check OAuth scopes include `sdm.service`

---

## Resources

- **Official Docs**: https://developers.google.com/nest/device-access/api
- **Device Access Console**: https://console.nest.google.com/device-access/
- **Google Cloud Console**: https://console.cloud.google.com/
- **Python Library**: https://pypi.org/project/python-google-nest/

---

## Next Steps

1. Complete setup steps 1-7
2. Add credentials to `.env`
3. Test with `utils/nest_api.py`
4. Use in automation scripts

---

**Last Updated**: 2025-10-06

# Tapo P125M Smart Plug - Complete Guide

## Quick Reference

### Your Plugs
1. **Heater** - 192.168.50.135
2. **Bedroom Right Lamp** - 192.168.50.143
3. **Livingroom Lamp** - 192.168.50.162
4. **Bedroom Bedroom Left Lamp** - 192.168.50.93

### Quick Commands

```python
from utils.tapo_api import turn_on, turn_off, get_status

# Control by name
turn_on("Heater")
turn_off("Livingroom Lamp")

# Check status
status = get_status("Bedroom Right Lamp")
print(f"Status: {'ON' if status['on'] else 'OFF'}")
```

---

## Discovery & Setup

### Find All Plugs on Network
```bash
cd /c/git/cyneta/siri_n8n/py_home
kasa --username matt@wheelers.us --password h4fsqSbNjfdm discover
```

### Name/Rename Plugs
```bash
# Name all plugs
python scripts/name_plugs.py

# Name specific plug(s)
python scripts/name_plugs.py 2          # Just plug #2
python scripts/name_plugs.py 2 4        # Plugs 2 and 4

# Controls while running:
# - ESC: pause/resume cycling
# - Type name (spaces OK) + ENTER: save name
# - ENTER alone: skip/keep current name
```

---

## Python API Usage

### Basic Control

```python
from utils.tapo_api import turn_on, turn_off, get_status

# Turn on/off by name
turn_on("Heater")
turn_off("Livingroom Lamp")

# Get detailed status
status = get_status("Bedroom Right Lamp")
print(f"On: {status['on']}")
print(f"Model: {status['device_info']['model']}")
print(f"Signal: {status['device_info']['rssi']} dBm")
print(f"MAC: {status['device_info']['mac']}")
```

### Control All Plugs

```python
from utils.tapo_api import turn_on_all, turn_off_all

# Turn all on/off
turn_on_all()
turn_off_all()
```

### Control by IP

```python
from utils.tapo_api import TapoAPI

tapo = TapoAPI()

# Direct IP control
tapo.turn_on(ip="192.168.50.135")
tapo.turn_off(ip="192.168.50.162")
status = tapo.get_status(ip="192.168.50.143")
```

### Get All Statuses

```python
from utils.tapo_api import TapoAPI

tapo = TapoAPI()
statuses = tapo.list_all_status()

for s in statuses:
    if 'error' not in s:
        print(f"{s['device_info']['alias']}: {'ON' if s['on'] else 'OFF'}")
```

---

## Configuration

### Add New Plug to Config

Edit `config/config.yaml`:

```yaml
tapo:
  username: "${TAPO_USERNAME}"
  password: "${TAPO_PASSWORD}"
  outlets:
    - name: "Heater"
      ip: "192.168.50.135"
    - name: "New Plug Name"
      ip: "192.168.50.XXX"  # Add discovered IP here
```

### Credentials

Stored in `config/.env` (gitignored):
```bash
TAPO_USERNAME=matt@wheelers.us
TAPO_PASSWORD=h4fsqSbNjfdm
```

---

## Demo Script

Run interactive demos:
```bash
python scripts/demo_tapo.py
```

Options:
1. Get status of all plugs
2. Control individual plug by name
3. Control all plugs at once
4. Control by IP address

---

## Technical Details

### Protocol
- **KLAP** (Kasa Local Access Protocol)
- **Port**: 80 (HTTP)
- **Local control**: Works without internet (after initial auth)
- **Encryption**: Device-specific, requires TP-Link credentials

### Library
- **python-kasa** v0.10.2
- Supports P100, P105, P110, P115, P125M

### Connection

```python
from kasa import Device, DeviceConfig, Credentials, DeviceConnectionParameters
from kasa import DeviceEncryptionType, DeviceFamily

config = DeviceConfig(
    host="192.168.50.135",
    credentials=Credentials("user@example.com", "password"),
    connection_type=DeviceConnectionParameters(
        device_family=DeviceFamily.SmartTapoPlug,
        encryption_type=DeviceEncryptionType.Klap
    )
)
device = await Device.connect(config=config)
await device.turn_on()
await device.protocol.close()  # Important: close session
```

### Setting Names Programmatically

```python
device = await Device.connect(config=config)
await device.set_alias("My New Name")
await device.protocol.close()
```

---

## Troubleshooting

### Plug Not Responding
1. Check if it's powered on
2. Ping the IP: `ping 192.168.50.XXX`
3. Verify credentials in `.env`
4. Check WiFi network (must be on same network)

### "Connection Refused" Error
- Wrong protocol - make sure using KLAP for P125M
- Wrong port - should be 80, not 9999

### Name Not Showing
- Names are stored locally in the plug
- Use `set_alias()` to set programmatically
- Or name via Tapo app

### Discovery Timeout
- Check firewall settings
- Ensure on same subnet (192.168.50.x)
- Try direct IP connection instead

---

## Use Cases

### Automation Examples

**Morning routine:**
```python
turn_on("Bedroom Right Lamp")
turn_on("Heater")
```

**Leaving home:**
```python
turn_off_all()
```

**Schedule-based:**
```python
import schedule
import time

schedule.every().day.at("07:00").do(lambda: turn_on("Bedroom Right Lamp"))
schedule.every().day.at("22:00").do(lambda: turn_off("Bedroom Right Lamp"))

while True:
    schedule.run_pending()
    time.sleep(60)
```

**Integrate with Flask webhook:**
```python
from flask import Flask, request
from utils.tapo_api import turn_on, turn_off

app = Flask(__name__)

@app.route('/plug/<name>/<action>')
def control_plug(name, action):
    if action == 'on':
        turn_on(name)
    elif action == 'off':
        turn_off(name)
    return f"OK: {name} {action}"
```

---

## Files

- **API**: `py_home/utils/tapo_api.py`
- **Config**: `py_home/config/config.yaml`
- **Credentials**: `py_home/config/.env`
- **Naming Tool**: `py_home/scripts/name_plugs.py`
- **Demo**: `py_home/scripts/demo_tapo.py`
- **Docs**:
  - `py_home/docs/TAPO_INTEGRATION.md` (technical details)
  - `py_home/docs/TAPO_GUIDE.md` (this file - user guide)

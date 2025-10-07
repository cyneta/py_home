# Tapo P125M Smart Plug Integration

## Overview

Controls TP-Link Tapo P125M smart plugs using the `python-kasa` library with KLAP protocol.

## Setup

### 1. Install Dependencies
```bash
pip install python-kasa>=0.8.0
```

### 2. Add Credentials to `.env`
```bash
TAPO_USERNAME=your-email@example.com
TAPO_PASSWORD=your-tapo-password
```

Use your TP-Link cloud account credentials (same as Tapo app login).

### 3. Configure Outlets in `config.yaml`
```yaml
tapo:
  username: "${TAPO_USERNAME}"
  password: "${TAPO_PASSWORD}"
  outlets:
    - name: "Kitchen plug"
      ip: "192.168.50.135"
```

## Discovery

Find Tapo devices on your network:
```bash
kasa --username user@example.com --password password discover
```

## Usage

```python
from utils.tapo_api import turn_on, turn_off, get_status

# Control by name
turn_on("Kitchen plug")
turn_off("Kitchen plug")

# Get status
status = get_status("Kitchen plug")
print(f"Status: {'ON' if status['on'] else 'OFF'}")
print(f"Model: {status['device_info']['model']}")
print(f"Signal: {status['device_info']['rssi']} dBm")
```

## Technical Details

### Protocol
- **KLAP Protocol** (Kasa Local Access Protocol)
- **Port**: 80 (HTTP)
- **Authentication**: TP-Link cloud credentials required
- **Encryption**: Device family SmartTapoPlug with Klap encryption

### Supported Models
- P125M (tested - Hardware 1.0 US / Firmware 1.2.5)
- P100, P105, P110, P110M, P115 (should work)

### Connection Method
```python
config = DeviceConfig(
    host=ip,
    credentials=Credentials(username, password),
    connection_type=DeviceConnectionParameters(
        device_family=DeviceFamily.SmartTapoPlug,
        encryption_type=DeviceEncryptionType.Klap
    )
)
device = await Device.connect(config=config)
```

## Notes

- **Third-Party Compatibility**: Not required for P125M plugs (only needed for cameras)
- **Session Management**: HTTP sessions are closed after each operation to prevent warnings
- **Network**: Devices must be on same local network
- **Matter Support**: P125M supports Matter protocol but python-kasa uses local HTTP API

## Tested Configuration
- **Device**: Tapo P125M (1.0 US)
- **Firmware**: 1.2.5 Build 240830 Rel.153927
- **Library**: python-kasa 0.10.2
- **Protocol**: KLAP over HTTP (port 80)
- **Network**: 192.168.50.x
- **SSID**: dapad

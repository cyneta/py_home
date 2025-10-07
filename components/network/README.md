# Network Presence Detection

Detect device presence on local network via WiFi.

**Purpose:** Backup/complement iOS location automations for home/away detection.

---

## Quick Start

### 1. Find Your iPhone's Network Info

**Get IP Address:**
```
iPhone Settings
→ WiFi
→ Tap (i) next to your network
→ IP Address: 192.168.1.50 (example)
```

**Get MAC Address:**
```
iPhone Settings
→ General
→ About
→ WiFi Address: AA:BB:CC:DD:EE:FF (example)
```

### 2. Test Detection

```bash
# Run interactive demo
cd components/network
python demo.py

# Option 1: Scan network to find iPhone
# Option 2: Test ping detection
# Option 3: Test ARP detection
```

### 3. Use in Code

```python
from components.network import is_device_home

# Check by IP (faster)
if is_device_home('192.168.1.50'):
    print("iPhone is home!")

# Check by MAC (more reliable)
if is_device_home('AA:BB:CC:DD:EE:FF', method='arp'):
    print("iPhone is home!")

# Auto-detect method
if is_device_home('192.168.1.50', method='auto'):
    print("iPhone is home!")
```

---

## Detection Methods

### Method 1: Ping (Fast)

**How it works:** Sends ICMP ping to IP address

**Pros:**
- ✅ Fast (< 2 seconds)
- ✅ Simple
- ✅ No special tools needed

**Cons:**
- ❌ Requires static IP
- ❌ Some devices ignore pings (battery saving)
- ❌ False negatives common

**Usage:**
```python
is_device_home('192.168.1.50', method='ping')
```

**Best for:** Quick checks, devices that respond to pings

---

### Method 2: ARP Scan (Reliable)

**How it works:** Scans network ARP table for MAC address

**Pros:**
- ✅ More reliable than ping
- ✅ Works even if device ignores pings
- ✅ Uses MAC address (no static IP needed)

**Cons:**
- ❌ Slower (5-10 seconds)
- ❌ May require `arp-scan` tool on Linux
- ❌ May need sudo permissions

**Usage:**
```python
is_device_home('AA:BB:CC:DD:EE:FF', method='arp')
```

**Best for:** Most reliable detection, production use

---

### Method 3: Auto (Recommended)

**How it works:** Tries ping first, falls back to ARP

**Pros:**
- ✅ Best of both worlds
- ✅ Fast when possible, reliable when needed

**Usage:**
```python
is_device_home('192.168.1.50', method='auto')
```

**Best for:** General use, automated monitoring

---

## Setup

### Linux (Raspberry Pi) - Recommended

```bash
# Install arp-scan for best reliability
sudo apt install arp-scan

# Test it
sudo arp-scan --localnet

# Grant sudo access for arp-scan (optional, for automation)
sudo visudo
# Add line:
# pi ALL=(ALL) NOPASSWD: /usr/sbin/arp-scan
```

### Windows

```bash
# No installation needed
# Uses built-in arp and ping commands

# Test network scan
arp -a
```

### Mac

```bash
# Install arp-scan (optional, for better scanning)
brew install arp-scan

# Test it
sudo arp-scan --localnet
```

---

## Configuration

Add to `config/config.yaml`:

```yaml
presence:
  devices:
    iphone:
      name: "Matt's iPhone"
      ip: "192.168.1.50"
      mac: "AA:BB:CC:DD:EE:FF"
      method: "auto"  # ping, arp, or auto

    # Add more devices if needed
    ipad:
      name: "Matt's iPad"
      ip: "192.168.1.51"
      mac: "BB:CC:DD:EE:FF:00"
      method: "auto"
```

---

## API Reference

### `is_device_home(identifier, method='ping')`

Check if device is on network.

**Parameters:**
- `identifier` (str): IP address or MAC address
- `method` (str): 'ping', 'arp', or 'auto'

**Returns:**
- `bool`: True if device is online

**Example:**
```python
from components.network import is_device_home

# By IP
if is_device_home('192.168.1.50'):
    print("Device is home")

# By MAC with ARP
if is_device_home('AA:BB:CC:DD:EE:FF', method='arp'):
    print("Device is home")
```

---

### `scan_network(subnet='192.168.1.0/24')`

Scan network for all active devices.

**Parameters:**
- `subnet` (str): Network subnet in CIDR notation

**Returns:**
- `list`: List of dicts with 'ip', 'mac', 'vendor' keys

**Example:**
```python
from components.network import scan_network

devices = scan_network()
for device in devices:
    print(f"{device['ip']} - {device['mac']} - {device['vendor']}")
```

---

### `get_device_info(identifier)`

Get detailed information about a device.

**Parameters:**
- `identifier` (str): IP address or MAC address

**Returns:**
- `dict`: Device info with 'ip', 'mac', 'vendor', 'online' keys

**Example:**
```python
from components.network import get_device_info

info = get_device_info('192.168.1.50')
print(f"Online: {info['online']}")
print(f"MAC: {info['mac']}")
```

---

## Use Cases

### 1. Automated Presence Monitoring

See `automations/presence_monitor.py` for complete example.

```python
from components.network import is_device_home
import time

previous_state = None

while True:
    current_state = is_device_home('192.168.1.50')

    # Detect arrival
    if current_state and not previous_state:
        print("ARRIVED HOME!")
        # Trigger im_home automation

    # Detect departure
    elif not current_state and previous_state:
        print("LEFT HOME!")
        # Trigger leaving_home automation

    previous_state = current_state
    time.sleep(300)  # Check every 5 minutes
```

### 2. Backup to iOS Location

```python
from components.network import is_device_home

def is_anyone_home():
    """Check both iOS and WiFi detection"""

    # Check iOS automation timestamp
    ios_home = check_last_ios_ping()  # Custom function

    # Check WiFi
    wifi_home = is_device_home('192.168.1.50')

    # Either method = home
    return ios_home or wifi_home
```

### 3. Multi-Person Detection

```python
from components.network import is_device_home

def get_home_status():
    """Check who's home"""

    matt_home = is_device_home('192.168.1.50')  # Matt's iPhone
    guest_home = is_device_home('192.168.1.60')  # Guest phone

    if matt_home and guest_home:
        return "both_home"
    elif matt_home:
        return "matt_home"
    elif guest_home:
        return "guest_home"
    else:
        return "nobody_home"
```

---

## Troubleshooting

### Ping not working

**Problem:** `is_device_home(ip)` always returns False

**Solutions:**
```bash
# Test ping manually
ping 192.168.1.50

# If it works manually but not in code:
# 1. Check IP is correct
# 2. Try ARP method instead
# 3. Check device is on WiFi (not cellular)
```

### ARP scan requires sudo

**Problem:** "Permission denied" when using ARP scan

**Solutions:**
```bash
# Option 1: Run script with sudo
sudo python automations/presence_monitor.py

# Option 2: Grant sudo access to arp-scan
sudo visudo
# Add: pi ALL=(ALL) NOPASSWD: /usr/sbin/arp-scan

# Option 3: Use ping method instead
is_device_home('192.168.1.50', method='ping')
```

### Device not found even when home

**Problem:** Device appears offline but is definitely connected

**Possible causes:**
1. **Wrong IP** - iPhone IP changed (use MAC instead)
2. **Private WiFi Address** - iOS randomizes MAC (turn off in WiFi settings)
3. **5GHz vs 2.4GHz** - Check on same WiFi band as server
4. **WiFi sleeping** - iPhone may disconnect WiFi when locked

**Solutions:**
```python
# Use MAC address instead of IP
is_device_home('AA:BB:CC:DD:EE:FF', method='arp')

# Disable iOS Private WiFi Address:
# Settings → WiFi → (i) → Private WiFi Address → OFF
```

### Network scan finds no devices

**Problem:** `scan_network()` returns empty list

**Solutions:**
```bash
# Install arp-scan
sudo apt install arp-scan

# Test manually
sudo arp-scan --localnet

# If still empty, check:
# 1. Server is on same WiFi network
# 2. Firewall not blocking
# 3. Using correct network interface
```

---

## Performance

**Ping method:**
- Speed: ~2 seconds
- CPU: Very low
- Battery: No impact on phone

**ARP method:**
- Speed: ~5-10 seconds (scan), ~1 second (arp -a)
- CPU: Low
- Battery: No impact on phone

**Recommended check interval:**
- Development: Every 1-2 minutes
- Production: Every 5 minutes
- Battery saver: Every 15 minutes

---

## Security Notes

- ✅ Read-only, no device control
- ✅ Local network only
- ✅ No internet access required
- ⚠️ arp-scan may need sudo (configure carefully)
- ⚠️ Shows all devices on network (privacy consideration)

---

## Next Steps

1. **Find your iPhone's IP/MAC** (see Quick Start)
2. **Test detection** with `python demo.py`
3. **Add to config.yaml** under `presence` section
4. **Set up automated monitoring** (see `automations/presence_monitor.py`)
5. **Combine with iOS location** for best results

---

## Related

- **iOS Location Automations** - Primary detection method
- **automations/presence_monitor.py** - Automated monitoring
- **server/README.md** - Flask webhook integration

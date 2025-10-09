# Raspberry Pi 5 Deployment Plan

**Hardware:** Raspberry Pi 5
**OS:** Raspberry Pi OS Lite
**Network:** WiFi (DHCP - no static IP)
**Date:** 2025-10-07

---

## Overview

Deploy py_home to Raspberry Pi 5 for 24/7 home automation. Flask server will be accessible via mDNS (raspberrypi.local) instead of static IP, making iOS shortcuts work without IP hardcoding.

---

## Pre-Deployment Checklist

### ✅ On Development Machine (Before Deploying)

- [ ] All 7 commits pushed to git
- [ ] Test suite passes: `python test_all.py --quick`
- [ ] Flask server works locally: `python server/app.py`
- [ ] At least one automation works: `python automations/leaving_home.py --dry-run`
- [ ] Have credentials ready:
  - [ ] Nest OAuth token/credentials
  - [ ] Sensibo API key
  - [ ] Tapo credentials
  - [ ] Pushover API keys (notifications)
  - [ ] GitHub token (if using)
  - [ ] Checkvist credentials (if using)

### ✅ Raspberry Pi 5 Setup (Fresh Install)

- [ ] Raspberry Pi OS Lite installed
- [ ] WiFi configured and connected
- [ ] SSH enabled
- [ ] Can connect via: `ssh pi@raspberrypi.local`
- [ ] System updated: `sudo apt update && sudo apt upgrade -y`

---

## Deployment Steps

### Step 1: Prepare Raspberry Pi 5

```bash
# Connect via SSH
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    avahi-daemon \
    curl

# Verify Python version (should be 3.11+ on Pi OS Lite)
python3 --version

# Enable and start Avahi (mDNS) for raspberrypi.local hostname
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

**Why Avahi?** Enables `raspberrypi.local` hostname so iOS shortcuts don't need hardcoded IP.

---

### Step 2: Clone Project to Pi

**Option A: Git Clone (if pushed to GitHub)**
```bash
# On Pi
cd ~
git clone https://github.com/YOUR_USERNAME/py_home.git
cd py_home
```

**Option B: Direct Copy via SCP (if not using GitHub)**
```bash
# From development machine
cd /c/git/cyneta
scp -r py_home/ pi@raspberrypi.local:~/

# Then on Pi
cd ~/py_home
```

**Option C: USB Transfer**
```bash
# Copy py_home to USB drive on dev machine
# Insert USB into Pi
# On Pi:
sudo mount /dev/sda1 /mnt
cp -r /mnt/py_home ~/
cd ~/py_home
```

---

### Step 3: Install Python Dependencies

```bash
cd ~/py_home

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask; print('Flask OK')"
python -c "from tapo import ApiClient; print('Tapo OK')"
```

---

### Step 4: Configure Credentials

```bash
cd ~/py_home/config

# Create .env file (DO NOT copy from dev machine if it has Windows paths)
nano .env
```

**Paste this template and fill in your values:**
```bash
# Nest
NEST_PROJECT_ID=your-project-id
NEST_CLIENT_ID=your-client-id
NEST_CLIENT_SECRET=your-client-secret
NEST_REFRESH_TOKEN=your-refresh-token

# Sensibo
SENSIBO_API_KEY=your-sensibo-key

# Tapo
TAPO_USERNAME=your-tapo-email
TAPO_PASSWORD=your-tapo-password

# Pushover (notifications)
PUSHOVER_USER_KEY=your-user-key
PUSHOVER_API_TOKEN=your-api-token

# OpenWeather (optional)
OPENWEATHER_API_KEY=your-openweather-key

# GitHub (optional)
GITHUB_TOKEN=your-github-token

# Checkvist (optional)
CHECKVIST_USERNAME=your-checkvist-username
CHECKVIST_API_KEY=your-checkvist-key
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

**Verify .env file:**
```bash
cat .env  # Should show your credentials
chmod 600 .env  # Secure permissions
```

---

### Step 5: Update Device IPs in config.yaml

```bash
cd ~/py_home/config
nano config.yaml
```

Update the device IPs to match your actual network:

```yaml
tapo:
  outlets:
    - name: "Heater"
      ip: "192.168.50.135"  # Update these!
    - name: "Bedroom Right Lamp"
      ip: "192.168.50.143"
    # ... etc
```

**To find device IPs:**
```bash
# Option 1: Use find_devices script
cd ~/py_home
source venv/bin/activate
python components/tapo/find_devices.py

# Option 2: Check your router's DHCP leases
# Option 3: Use network scanner (if installed)
sudo apt install arp-scan
sudo arp-scan --localnet
```

---

### Step 6: Test Installation

```bash
cd ~/py_home
source venv/bin/activate

# Test config loads
python -c "from lib.config import config; print('Config OK')"

# Test Tapo connection
python components/tapo/test.py

# Test Nest connection
python components/nest/test.py

# Test Sensibo connection
python components/sensibo/test.py

# Test automation in dry-run mode
python automations/leaving_home.py --dry-run

# Test Flask server (Ctrl+C to stop)
python server/app.py
```

**Expected output:**
```
 * Running on http://0.0.0.0:5000
```

**Test from another device:**
```bash
# From your phone or dev machine
curl http://raspberrypi.local:5000/status
```

Should return JSON with status: "running".

---

### Step 7: Install Flask as Systemd Service

```bash
cd ~/py_home

# Copy service file
sudo cp server/py_home.service /etc/systemd/system/

# Edit service to use correct paths
sudo nano /etc/systemd/system/py_home.service
```

**Update these lines if needed:**
```ini
[Unit]
Description=py_home Flask API Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/py_home
Environment="PATH=/home/pi/py_home/venv/bin"
ExecStart=/home/pi/py_home/venv/bin/python server/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable py_home

# Start service now
sudo systemctl start py_home

# Check status
sudo systemctl status py_home
```

**Should show:**
```
● py_home.service - py_home Flask API Server
   Loaded: loaded (/etc/systemd/system/py_home.service; enabled)
   Active: active (running)
```

**View logs:**
```bash
sudo journalctl -u py_home -f  # Follow logs
sudo journalctl -u py_home -n 50  # Last 50 lines
```

---

### Step 8: Setup Cron Jobs for Automations

```bash
# Edit crontab
crontab -e
```

**Add these lines:**
```bash
# Presence monitoring (check WiFi every 5 minutes)
*/5 * * * * cd /home/pi/py_home && /home/pi/py_home/venv/bin/python automations/presence_monitor.py >> /home/pi/py_home/logs/presence.log 2>&1

# Temperature coordination (every 15 minutes)
*/15 * * * * cd /home/pi/py_home && /home/pi/py_home/venv/bin/python automations/temp_coordination.py >> /home/pi/py_home/logs/temp.log 2>&1

# Traffic alert (weekday mornings at 7:30 AM)
30 7 * * 1-5 cd /home/pi/py_home && /home/pi/py_home/venv/bin/python automations/traffic_alert.py >> /home/pi/py_home/logs/traffic.log 2>&1
```

**Create log directory:**
```bash
mkdir -p ~/py_home/logs
```

**Test cron job manually:**
```bash
cd ~/py_home
source venv/bin/activate
python automations/presence_monitor.py
```

---

### Step 9: Test End-to-End

**From iOS Shortcuts app:**

1. Create shortcut "Leaving Home"
2. Add action: "Get contents of URL"
3. URL: `http://raspberrypi.local:5000/leaving-home`
4. Method: POST
5. Test shortcut

**Expected:**
- Nest sets to away temp
- Tapo outlets turn off
- Notification sent
- Returns JSON: `{"status": "success"}`

**Test other endpoints:**
- `http://raspberrypi.local:5000/goodnight`
- `http://raspberrypi.local:5000/im-home`
- `http://raspberrypi.local:5000/good-morning`

---

## WiFi DHCP Considerations (No Static IP)

### Problem: iOS shortcuts need consistent hostname

**Solution: Use mDNS (Avahi)**

Pi 5 advertises itself as `raspberrypi.local` via mDNS/Avahi. This works on:
- ✅ iOS devices on same WiFi network
- ✅ macOS/Linux devices
- ✅ Windows 10+ (with Bonjour/mDNS support)

**Advantages:**
- No router configuration needed
- Works even if Pi gets different DHCP IP
- iOS shortcuts use `raspberrypi.local` instead of IP

**Disadvantages:**
- Only works on local network (can't access remotely)
- Requires mDNS support on client devices

**Alternative if mDNS doesn't work:**

1. **Reserve DHCP IP in router:**
   - Find Pi's MAC address: `ip addr show wlan0 | grep ether`
   - Log into router
   - Reserve IP for Pi's MAC address
   - Use that IP in iOS shortcuts

2. **Set static IP on Pi:**
   ```bash
   sudo nmcli con mod "Wired connection 1" ipv4.addresses 192.168.1.100/24
   sudo nmcli con mod "Wired connection 1" ipv4.gateway 192.168.1.1
   sudo nmcli con mod "Wired connection 1" ipv4.dns "8.8.8.8 8.8.4.4"
   sudo nmcli con mod "Wired connection 1" ipv4.method manual
   sudo nmcli con up "Wired connection 1"
   ```

---

## Monitoring & Maintenance

### View Flask Server Logs
```bash
# Follow live logs
sudo journalctl -u py_home -f

# Last 100 lines
sudo journalctl -u py_home -n 100

# Logs since boot
sudo journalctl -u py_home -b
```

### View Automation Logs
```bash
# Presence monitoring
tail -f ~/py_home/logs/presence.log

# Temperature coordination
tail -f ~/py_home/logs/temp.log

# Traffic alerts
tail -f ~/py_home/logs/traffic.log
```

### Restart Services
```bash
# Restart Flask server
sudo systemctl restart py_home

# Check service status
sudo systemctl status py_home

# View recent errors
sudo journalctl -u py_home -p err
```

### Update Code
```bash
cd ~/py_home

# Pull latest changes (if using git)
git pull origin main

# Restart service to apply changes
sudo systemctl restart py_home
```

### Check System Resources
```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Network connectivity
ping 8.8.8.8

# Check WiFi signal
iwconfig wlan0
```

---

## Troubleshooting

### Flask server won't start

```bash
# Check service status
sudo systemctl status py_home

# View detailed logs
sudo journalctl -u py_home -n 100

# Test manually
cd ~/py_home
source venv/bin/activate
python server/app.py
# Look for error messages
```

**Common issues:**
- Missing dependencies: `pip install -r requirements.txt`
- Wrong Python path in service file
- Port 5000 already in use: `sudo lsof -i :5000`

### iOS shortcuts can't reach Pi

```bash
# Check if Pi is reachable
ping raspberrypi.local

# Check if Flask is listening
sudo netstat -tlnp | grep 5000

# Check firewall (should be disabled by default on Pi OS)
sudo ufw status

# Test from Pi itself
curl http://localhost:5000/status
```

**Common issues:**
- Avahi not running: `sudo systemctl start avahi-daemon`
- WiFi disconnected: `iwconfig wlan0`
- Flask bound to 127.0.0.1 instead of 0.0.0.0

### Automations not running

```bash
# Check crontab
crontab -l

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Test automation manually
cd ~/py_home
source venv/bin/activate
python automations/presence_monitor.py
```

**Common issues:**
- Wrong paths in crontab
- Virtual environment not activated in cron
- Permissions issues on log directory

### Devices not responding

```bash
# Test Tapo
cd ~/py_home
source venv/bin/activate
python components/tapo/test.py

# Test Nest
python components/nest/test.py

# Test Sensibo
python components/sensibo/test.py
```

**Common issues:**
- Device IPs changed (check router DHCP table)
- WiFi disconnected on devices
- API credentials expired (Nest token refresh)
- Network connectivity issues

---

## Security Considerations

### ✅ Implemented
- `.env` file with 600 permissions (not readable by other users)
- Flask server only accessible on local network (no internet exposure)
- No hardcoded credentials in code
- Virtual environment isolates dependencies

### ⚠️ Consider Adding
- **API authentication:** Add API key to Flask endpoints
  - Edit `server/routes.py` to require auth header
  - Update iOS shortcuts to send API key
- **HTTPS:** Use self-signed cert or Let's Encrypt
  - Only needed if exposing to internet (not recommended)
- **Firewall rules:** Limit Flask to local network only
  ```bash
  sudo ufw allow from 192.168.1.0/24 to any port 5000
  ```

---

## Performance Optimization

### Pi 5 Specifics
- **CPU:** 4-core ARM Cortex-A76 (plenty for Flask + cron jobs)
- **RAM:** 8GB (more than enough for this workload)
- **Expected CPU usage:** <5% average
- **Expected RAM usage:** ~200MB for Flask + cron jobs

### Optimize if needed
```bash
# Reduce logging verbosity
# Edit server/app.py
app.logger.setLevel(logging.WARNING)

# Reduce cron job frequency
# Edit crontab
*/10 * * * *  # Presence check every 10 min instead of 5
*/30 * * * *  # Temp coordination every 30 min instead of 15
```

---

## Backup Strategy

### What to Backup
- `config/.env` (credentials)
- `config/config.yaml` (device configuration)
- Automation logs (optional)

### Backup Script
```bash
#!/bin/bash
# ~/py_home/backup.sh

BACKUP_DIR=~/py_home_backups
mkdir -p $BACKUP_DIR

DATE=$(date +%Y%m%d_%H%M%S)

# Backup credentials and config
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    ~/py_home/config/.env \
    ~/py_home/config/config.yaml

# Keep only last 7 days of backups
find $BACKUP_DIR -name "config_*.tar.gz" -mtime +7 -delete

echo "Backup complete: $BACKUP_DIR/config_$DATE.tar.gz"
```

**Add to crontab:**
```bash
# Daily backup at 2 AM
0 2 * * * /home/pi/py_home/backup.sh >> /home/pi/py_home/logs/backup.log 2>&1
```

---

## Next Steps After Deployment

1. **Monitor for 24 hours**
   - Check logs hourly: `sudo journalctl -u py_home -f`
   - Test each iOS shortcut
   - Verify automations run on schedule

2. **Fine-tune automation schedules**
   - Adjust cron timings based on usage
   - Add/remove automations as needed

3. **Setup remote access (optional)**
   - VPN (WireGuard) for secure remote access
   - Tailscale for easy setup
   - **DO NOT** expose Flask directly to internet

4. **Add more automations**
   - Weather-based adjustments
   - Presence-based lighting
   - Energy monitoring

---

## Quick Reference

### Common Commands
```bash
# SSH to Pi
ssh pi@raspberrypi.local

# Activate venv
cd ~/py_home && source venv/bin/activate

# View Flask logs
sudo journalctl -u py_home -f

# Restart Flask
sudo systemctl restart py_home

# Test automation
python automations/leaving_home.py --dry-run

# Check system status
htop
```

### Important Paths
- Project: `/home/pi/py_home`
- Virtual env: `/home/pi/py_home/venv`
- Credentials: `/home/pi/py_home/config/.env`
- Service file: `/etc/systemd/system/py_home.service`
- Logs: `/home/pi/py_home/logs/`

### URLs for iOS Shortcuts
- Status: `http://raspberrypi.local:5000/status`
- Leaving home: `http://raspberrypi.local:5000/leaving-home`
- Goodnight: `http://raspberrypi.local:5000/goodnight`
- I'm home: `http://raspberrypi.local:5000/im-home`
- Good morning: `http://raspberrypi.local:5000/good-morning`

---

**End of Deployment Plan**

**Estimated Time:** 1-2 hours for fresh deployment
**Difficulty:** Intermediate (requires SSH and basic Linux knowledge)
**Success Rate:** High (Pi 5 with OS Lite is well-supported)

# py_home Deployment Guide

Complete guide for deploying py_home to production.

---

## Production Server Details

### Raspberry Pi Access

**On-Site (Local Network)**:
- Hostname: `raspberrypi` or `raspberrypi.local`
- IP Address: `192.168.50.189`
- Username: `matt.wheeler`
- SSH: `ssh matt.wheeler@192.168.50.189`
- Web UI: `http://192.168.50.189:5000`

**Off-Site (Tailscale VPN)**:
- Hostname: TBD (check `tailscale status` on Pi)
- Requires Tailscale connected on client device
- SSH: `ssh matt.wheeler@<tailscale-hostname>`
- Web UI: `http://<tailscale-hostname>:5000`

**Service Management**:
```bash
# Restart Flask server
ssh matt.wheeler@192.168.50.189 "sudo systemctl restart py_home"

# Check status
ssh matt.wheeler@192.168.50.189 "sudo systemctl status py_home"

# View logs
ssh matt.wheeler@192.168.50.189 "sudo journalctl -u py_home -n 50"
```

**File Deployment**:
```bash
# Deploy updated .env (credentials)
scp config/.env matt.wheeler@192.168.50.189:/home/matt.wheeler/py_home/config/

# Deploy code changes
scp -r automations/ matt.wheeler@192.168.50.189:/home/matt.wheeler/py_home/

# After deployment, restart service
ssh matt.wheeler@192.168.50.189 "sudo systemctl restart py_home"
```

---

## Deployment Options

### Option 1: Raspberry Pi (Recommended)
- ✅ Low power consumption (~$5/year electricity)
- ✅ Always-on, 24/7 availability
- ✅ Linux native (easier systemd setup)
- ❌ Requires hardware purchase (~$50-100)

### Option 2: Always-On Windows PC
- ✅ Use existing hardware
- ✅ No additional purchase needed
- ❌ Higher power consumption (~$50/year)
- ❌ Systemd not available (use NSSM or startup folder)

### Option 3: Cloud Server (VPS)
- ✅ Accessible from anywhere
- ✅ Professional uptime
- ❌ Monthly cost ($5-10/month)
- ❌ Security considerations (expose home automation to internet)

**Recommendation:** Raspberry Pi 4 (2GB) for best balance of cost, power, and reliability.

---

## Pre-Deployment Checklist

### ✅ Before You Deploy
- [ ] Flask server tested locally (`python server/app.py` works)
- [ ] All automations tested (`python automations/leaving_home.py` works)
- [ ] Credentials configured in `config/.env`
- [ ] Device IPs updated in `config/config.yaml`
- [ ] Test suite passing (`python test_all.py`)
- [ ] Server accessible on local network (test from phone)

### ✅ Server Requirements
- [ ] Python 3.9 or higher installed
- [ ] pip installed
- [ ] Git installed (for updates)
- [ ] Network connectivity (WiFi or Ethernet)
- [ ] Static IP address configured (recommended)

---

## Deployment: Raspberry Pi / Linux

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv git -y

# Verify versions
python3 --version  # Should be 3.9+
pip3 --version
```

### 2. Copy Project to Pi

**Option A: From development machine**
```bash
# From your development machine
cd /c/git/cyneta
scp -r py_home/ pi@raspberrypi.local:~/

# Or use specific IP
scp -r py_home/ pi@192.168.1.100:~/
```

**Option B: Clone from git** (if you've pushed to GitHub)
```bash
# On the Pi
cd ~
git clone https://github.com/your-username/py_home.git
cd py_home
```

**Option C: Manual USB transfer**
- Copy `py_home/` to USB drive
- Insert into Pi
- `cp -r /media/usb/py_home ~/`

### 3. Install Dependencies

```bash
cd ~/py_home

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installations
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import googlemaps; print('googlemaps OK')"
```

### 4. Configure Environment

```bash
# Ensure .env file is present
ls -la config/.env

# If missing, create it
cp config/.env.example config/.env
nano config/.env
# Add your credentials
```

### 5. Test Locally on Pi

```bash
# Test Flask server
python server/app.py

# In another SSH session or from your computer:
curl http://raspberrypi.local:5000/status

# Test automation
python automations/travel_time.py Milwaukee

# Run test suite
python test_all.py
```

### 6. Install systemd Service

```bash
# Edit service file with correct paths
nano server/py_home.service

# Update these lines to match your setup:
# WorkingDirectory=/home/pi/py_home
# ExecStart=/home/pi/py_home/venv/bin/python /home/pi/py_home/server/app.py
# EnvironmentFile=/home/pi/py_home/config/.env

# Copy service file
sudo cp server/py_home.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable py_home

# Start service
sudo systemctl start py_home

# Check status
sudo systemctl status py_home
```

### 7. Verify Service is Running

```bash
# Check service status
sudo systemctl status py_home
# Should show "Active: active (running)"

# Check logs
sudo journalctl -u py_home -f
# Press Ctrl+C to exit

# Test endpoint from another computer
curl http://raspberrypi.local:5000/status
```

### 8. Set Up Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines (copy/paste the entire block):
# ============================================
# py_home scheduled automations
# ============================================

# Scheduler: wake (05:00) and sleep (22:30) transitions
# Runs every minute, checks for exact time matches
* * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

# Temperature coordination: Nest + Sensibo HVAC sync (every 15 min)
*/15 * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/temp_coordination.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

# Temperature data logger: CSV logging for analysis (every 15 min)
*/15 * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/temp_data_logger.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

# TempStick monitoring: temp/humidity alerts (every 30 min)
*/30 * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/tempstick_monitor.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

# Air quality monitoring: PM2.5 alerts (every 30 min)
*/30 * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/air_quality_monitor.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

# Presence detection: WiFi-based home/away (every 5 min)
*/5 * * * * cd /home/matt.wheeler/py_home && /home/matt.wheeler/py_home/venv/bin/python automations/presence_monitor.py >> /home/matt.wheeler/py_home/data/logs/automations.log 2>&1

# Save and exit (Ctrl+O, Enter, Ctrl+X in nano)
```

**Verify cron jobs are installed:**
```bash
crontab -l
# Should show 6 py_home entries
```

### 9. Create Log Directory

```bash
# Create logs directory
mkdir -p ~/py_home/logs

# Test log rotation (optional)
sudo apt install logrotate
```

---

## Deployment: Windows PC

### 1. Prepare Windows Environment

```powershell
# Verify Python installation
python --version  # Should be 3.9+

# Install dependencies
cd C:\git\cyneta\py_home
pip install -r requirements.txt
```

### 2. Test Locally

```powershell
# Start server
python server\app.py

# Test in another terminal
curl http://localhost:5000/status
```

### 3. Run on Startup (Option A: Startup Folder)

```powershell
# Create startup batch file
# File: start_py_home.bat
@echo off
cd C:\git\cyneta\py_home
python server\app.py
pause

# Copy to startup folder
# Press Win+R, type: shell:startup
# Copy start_py_home.bat to the opened folder
```

### 4. Run as Windows Service (Option B: NSSM)

```powershell
# Download NSSM (Non-Sucking Service Manager)
# https://nssm.cc/download

# Install as service
nssm install py_home "C:\Python39\python.exe" "C:\git\cyneta\py_home\server\app.py"

# Set working directory
nssm set py_home AppDirectory C:\git\cyneta\py_home

# Start service
nssm start py_home

# Check status
nssm status py_home
```

### 5. Set Up Scheduled Tasks

```powershell
# Open Task Scheduler (taskschd.msc)

# Create task for scheduler (time-based transitions)
# Name: py_home Scheduler
# Trigger: Repeat every 1 minute
# Action: Start program
#   Program: C:\Python39\python.exe
#   Arguments: C:\git\cyneta\py_home\automations\scheduler.py
#   Start in: C:\git\cyneta\py_home
# Note: Scheduler checks for exact time matches (05:00 wake, 22:30 sleep)
#       Times configured in config/config.yaml
```

---

## Network Configuration

### Static IP Address (Recommended)

**Why:** Prevents server IP from changing, keeps iOS Shortcuts working.

**Raspberry Pi:**
```bash
# Edit dhcpcd.conf
sudo nano /etc/dhcpcd.conf

# Add these lines (adjust for your network)
interface wlan0  # or eth0 for Ethernet
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# Restart networking
sudo systemctl restart dhcpcd
```

**Windows:**
- Control Panel → Network → Change Adapter Settings
- Right-click WiFi/Ethernet → Properties
- Select IPv4 → Properties
- Set static IP (e.g., 192.168.1.100)

### Firewall Configuration

**Raspberry Pi:**
```bash
# Install UFW (Uncomplicated Firewall)
sudo apt install ufw

# Allow SSH (port 22)
sudo ufw allow 22

# Allow Flask server (port 5000)
sudo ufw allow 5000

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

**Windows:**
- Windows Firewall → Advanced Settings
- Inbound Rules → New Rule
- Port → TCP 5000 → Allow

### Port Forwarding (External Access - Optional)

**⚠️ Security Warning:** Only do this if you understand the risks. Better to use VPN.

1. Log into your router (usually 192.168.1.1)
2. Find Port Forwarding section
3. Forward external port 5000 → internal 192.168.1.100:5000
4. Enable authentication in Flask (`FLASK_REQUIRE_AUTH=true`)
5. Use HTTPS reverse proxy (nginx/Caddy)

---

## Security Best Practices

### 1. Enable Authentication

```bash
# Edit .env file
nano config/.env

# Add these lines
FLASK_REQUIRE_AUTH=true
FLASK_AUTH_USERNAME=admin
FLASK_AUTH_PASSWORD=your-secure-password-here
FLASK_SECRET_KEY=random-secret-key-generate-with-uuid

# Restart service
sudo systemctl restart py_home
```

### 2. Generate Secure Secret Key

```python
# Generate random secret key
python -c "import uuid; print(uuid.uuid4().hex)"
# Copy output to FLASK_SECRET_KEY in .env
```

### 3. Use HTTPS (Production)

**Install Nginx as reverse proxy:**
```bash
sudo apt install nginx certbot python3-certbot-nginx

# Configure nginx to proxy to Flask
sudo nano /etc/nginx/sites-available/py_home

# Add:
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/py_home /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 4. Keep System Updated

```bash
# Raspberry Pi - weekly updates
sudo apt update && sudo apt upgrade -y

# Update Python packages
cd ~/py_home
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## Monitoring & Maintenance

### Check Service Status

```bash
# systemd status
sudo systemctl status py_home

# Recent logs
sudo journalctl -u py_home -n 50

# Follow logs in real-time
sudo journalctl -u py_home -f

# Check if server is responding
curl http://localhost:5000/status
```

### Restart Service

```bash
# Restart Flask server
sudo systemctl restart py_home

# Stop service
sudo systemctl stop py_home

# Start service
sudo systemctl start py_home
```

### Update Code

```bash
# Pull latest changes (if using git)
cd ~/py_home
git pull

# Or copy updated files via scp
scp -r automations/ pi@raspberrypi:~/py_home/

# Restart service to apply changes
sudo systemctl restart py_home
```

### View Cron Job Logs

```bash
# View automations log (includes scheduler and all automations)
tail -f ~/py_home/data/logs/automations.log

# Or view with grep to filter
tail -f ~/py_home/data/logs/automations.log | grep automation=scheduler
tail -f ~/py_home/data/logs/automations.log | grep automation=goodnight
```

### Disk Space

```bash
# Check disk usage
df -h

# Check log file sizes
du -h ~/py_home/logs/
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status py_home

# View detailed logs
sudo journalctl -u py_home -n 100

# Common issues:
# 1. Wrong Python path in service file
# 2. Missing .env file
# 3. Port 5000 already in use
# 4. Missing dependencies

# Test manually
cd ~/py_home
source venv/bin/activate
python server/app.py
# Look for error messages
```

### Can't Connect from Phone

```bash
# Check if server is running
sudo systemctl status py_home

# Check firewall
sudo ufw status

# Check if port is listening
sudo netstat -tuln | grep 5000

# Test from Pi itself
curl http://localhost:5000/status

# Test from development machine
curl http://raspberrypi.local:5000/status

# Check Pi's IP address
hostname -I
```

### Cron Jobs Not Running

```bash
# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog

# Test cron job manually
cd /home/matt.wheeler/py_home
/home/matt.wheeler/py_home/venv/bin/python automations/scheduler.py --dry-run

# Common issues:
# 1. Wrong paths (use absolute paths)
# 2. Virtual environment not activated
# 3. Missing environment variables
```

### High CPU/Memory Usage

```bash
# Check resource usage
top
# Press 'q' to quit

# Check specific process
ps aux | grep python

# View system resources
free -h
```

### Pi Won't Boot After Power Loss

**Symptoms:**
- Pi responds to ping but SSH refused
- Flask server not responding
- Solid green LED (no blinking during boot)

**Root Cause:** SD card corruption from improper shutdown (unplugging power).

**Recovery Steps:**

1. **Reseat SD Card (Most Common Fix)**
   ```bash
   # Power off Pi completely
   # Remove and firmly reinsert SD card until it clicks
   # Power back on
   # Watch for blinking green LED during boot (30-60 seconds)
   # Solid green after boot = success
   ```

2. **Enable SSH via Boot Partition (If SSH Refused)**
   ```bash
   # Power off Pi, remove SD card
   # Insert SD card into your laptop
   # Windows will show "boot" drive (FAT32 partition)
   # Create empty file named "ssh" (no extension) in root of boot drive

   # In Git Bash or Command Prompt:
   echo. > E:\ssh  # Replace E: with your drive letter

   # Safely eject SD card
   # Reinsert into Pi and power on
   # SSH should now be enabled
   ```

3. **Physical Console Access (If Above Fails)**
   ```bash
   # Connect HDMI monitor + USB keyboard to Pi
   # Login at console
   # Username: matt.wheeler (or your Pi username)

   # Enable SSH service
   sudo systemctl enable ssh
   sudo systemctl start ssh
   sudo systemctl status ssh  # Should show "active (running)"

   # Check filesystem status
   mount | grep " / "  # Should show "rw" not "ro"

   # Check for errors
   sudo dmesg | grep -i error | tail -20

   # Start Flask manually if needed
   cd ~/py_home
   python3 server/__init__.py
   ```

4. **Set Static IP (Prevent IP Changes After Reboot)**
   ```bash
   # Edit network config
   sudo nano /etc/dhcpcd.conf

   # Add at end (adjust for your network):
   interface wlan0
   static ip_address=192.168.50.189/24
   static routers=192.168.50.1
   static domain_name_servers=192.168.50.1 8.8.8.8

   # Save: Ctrl+X, Y, Enter
   # Reboot to apply
   sudo reboot
   ```

5. **Test Recovery**
   ```bash
   # After reboot, test from your laptop:
   ping raspberrypi.local  # Should resolve to your static IP
   ssh matt.wheeler@raspberrypi.local  # Should connect
   curl http://raspberrypi.local:5000/status  # Should return JSON
   ```

**Prevention:**
- **ALWAYS use proper shutdown:** `sudo shutdown -h now`
- Wait for LED to stop blinking (30-60 seconds) before unplugging
- Never yank power while Pi is running
- Consider adding UPS (battery backup) for power protection

**Backup Strategy:**
- Keep SD card image backup: `sudo dd if=/dev/mmcblk0 of=~/pi_backup.img bs=4M`
- Or use tool like Win32DiskImager to image SD card from Windows
- Store backup somewhere safe - fastest recovery is restoring known-good image

---

## Backup Strategy

### What to Backup

**Essential:**
- `config/.env` - Credentials (most important!)
- `config/config.yaml` - Configuration

**Nice to have:**
- Entire `py_home/` directory
- Logs (if you want history)

### Backup Script

```bash
#!/bin/bash
# backup.sh - Create py_home backup

BACKUP_DIR="/home/pi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/py_home_$DATE.tar.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
tar -czf $BACKUP_FILE \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='logs' \
    ~/py_home

echo "Backup created: $BACKUP_FILE"

# Keep only last 7 backups
ls -t $BACKUP_DIR/py_home_*.tar.gz | tail -n +8 | xargs rm -f
```

### Automated Backups (Cron)

```bash
# Add to crontab
crontab -e

# Backup every Sunday at 2 AM
0 2 * * 0 /home/pi/backup.sh >> /home/pi/backup.log 2>&1
```

---

## Performance Optimization

### Reduce Memory Usage

```bash
# Use gunicorn instead of Flask dev server (production)
pip install gunicorn

# Start with gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 server.app:app

# Update systemd service to use gunicorn
# ExecStart=/home/pi/py_home/venv/bin/gunicorn -w 2 -b 0.0.0.0:5000 server.app:app
```

### Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/py_home

# Add:
/home/pi/py_home/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## Post-Deployment Checklist

### ✅ Verify Everything Works

- [ ] Service auto-starts on boot (test by rebooting Pi)
- [ ] Flask server accessible from phone on local network
- [ ] Can trigger automation via curl from phone
- [ ] Cron jobs running on schedule (check logs)
- [ ] Notifications being sent to phone
- [ ] All automations working (test each one)
- [ ] Static IP address configured
- [ ] Firewall configured correctly
- [ ] Backups configured and tested

### ✅ Next Steps After Deployment

- [ ] Create iOS Shortcuts pointing to server IP
- [ ] Test voice commands end-to-end
- [ ] Set up monitoring/alerts (optional)
- [ ] Document any custom changes
- [ ] Celebrate! 🎉

---

## Quick Reference

### Useful Commands

```bash
# Service management
sudo systemctl status py_home
sudo systemctl restart py_home
sudo journalctl -u py_home -f

# Testing
curl http://localhost:5000/status
python test_all.py

# Logs
tail -f ~/py_home/data/logs/automations.log
sudo journalctl -u py_home -n 50

# Updates
cd ~/py_home && git pull
sudo systemctl restart py_home

# Cron jobs
crontab -e
crontab -l
```

### Important Files

- `/etc/systemd/system/py_home.service` - systemd service file
- `/home/matt.wheeler/py_home/config/.env` - credentials
- `/home/matt.wheeler/py_home/config/config.yaml` - configuration
- `/home/matt.wheeler/py_home/data/logs/automations.log` - automation logs
- `/var/log/syslog` - system logs (includes cron)

---

## Support

**Issues?** Check the troubleshooting section above or:
1. Review logs: `sudo journalctl -u py_home -n 100`
2. Test manually: `python server/app.py`
3. Check network: `curl http://localhost:5000/status`
4. Review systemd service file paths

**Success?** Time to create iOS Shortcuts! See `server/README.md` for examples.

---

**Your py_home server is now production-ready! 🚀**

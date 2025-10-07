# py_home Deployment Guide

Complete guide for deploying py_home to production.

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

# Add scheduled automations
# Temperature coordination every 15 minutes
*/15 * * * * cd /home/pi/py_home && /home/pi/py_home/venv/bin/python automations/temp_coordination.py >> /home/pi/py_home/logs/temp_coordination.log 2>&1

# Good morning routine at 7 AM weekdays
0 7 * * 1-5 cd /home/pi/py_home && /home/pi/py_home/venv/bin/python automations/good_morning.py >> /home/pi/py_home/logs/good_morning.log 2>&1

# Save and exit (Ctrl+O, Enter, Ctrl+X in nano)
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

# Create task for temp_coordination
# Name: py_home Temperature Coordination
# Trigger: Repeat every 15 minutes
# Action: Start program
#   Program: C:\Python39\python.exe
#   Arguments: C:\git\cyneta\py_home\automations\temp_coordination.py
#   Start in: C:\git\cyneta\py_home

# Create task for good_morning
# Name: py_home Good Morning
# Trigger: Daily at 7:00 AM, weekdays only
# Action: Same as above but with good_morning.py
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
# View temperature coordination logs
tail -f ~/py_home/logs/temp_coordination.log

# View good morning logs
tail -f ~/py_home/logs/good_morning.log
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
cd /home/pi/py_home
/home/pi/py_home/venv/bin/python automations/temp_coordination.py

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
tail -f ~/py_home/logs/temp_coordination.log
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
- `/home/pi/py_home/config/.env` - credentials
- `/home/pi/py_home/config/config.yaml` - configuration
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

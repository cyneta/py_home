# Raspberry Pi Cleanup Plan

Removing n8n and other unused components before deploying py_home.

---

## Current Pi Status (Assumptions)

**Previous Setup (from siri_n8n project):**
- n8n workflow automation
- Node.js runtime
- npm packages
- Possibly PM2 or systemd services
- Old automation scripts
- Webhook endpoints

**What We're Keeping:**
- Python 3.11+
- System packages (curl, git, etc.)
- mDNS/Avahi (for raspberrypi.local)
- SSH access
- Basic OS utilities

**What We're Removing:**
- n8n (entire installation)
- Old siri_n8n repository
- Unused Node.js packages
- Old automation scripts
- Orphaned services

---

## Pre-Cleanup: Backup n8n Workflows

**IMPORTANT: Back up before deletion!**

```bash
# SSH to Pi
ssh pi@raspberrypi.local

# Create backup directory
mkdir -p ~/backups/n8n_$(date +%Y%m%d)

# Backup n8n data directory
if [ -d ~/.n8n ]; then
    cp -r ~/.n8n ~/backups/n8n_$(date +%Y%m%d)/
    echo "✓ n8n data backed up"
fi

# Backup workflows (if in different location)
if [ -d ~/n8n ]; then
    cp -r ~/n8n ~/backups/n8n_$(date +%Y%m%d)/
    echo "✓ n8n workflows backed up"
fi

# Backup siri_n8n repo
if [ -d ~/siri_n8n ]; then
    cp -r ~/siri_n8n ~/backups/n8n_$(date +%Y%m%d)/
    echo "✓ siri_n8n repo backed up"
fi

# Create archive for easy recovery
cd ~/backups
tar -czf n8n_backup_$(date +%Y%m%d).tar.gz n8n_$(date +%Y%m%d)/
echo "✓ Backup archive created: ~/backups/n8n_backup_$(date +%Y%m%d).tar.gz"

# List backup
ls -lh ~/backups/n8n_backup_*.tar.gz
```

---

## Cleanup Script

Create and run this automated cleanup script:

```bash
#!/bin/bash
# pi_cleanup.sh - Remove n8n and unused components

set -e  # Exit on error

echo "========================================="
echo "Raspberry Pi Cleanup for py_home"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running as pi user (not root)
if [ "$USER" != "pi" ]; then
    print_error "Please run as pi user, not root"
    exit 1
fi

echo "Step 1: Stopping n8n services"
echo "------------------------------"

# Stop n8n if running as systemd service
if systemctl list-units --full -all | grep -q n8n; then
    sudo systemctl stop n8n || print_warning "n8n service not running"
    sudo systemctl disable n8n || print_warning "n8n service not enabled"
    print_status "n8n systemd service stopped and disabled"
else
    print_warning "n8n systemd service not found"
fi

# Stop n8n if running with PM2
if command -v pm2 &> /dev/null; then
    pm2 stop n8n || print_warning "n8n not in PM2"
    pm2 delete n8n || print_warning "n8n not in PM2"
    pm2 save || true
    print_status "PM2 n8n process stopped"
else
    print_warning "PM2 not installed"
fi

# Kill any running n8n processes
pkill -f n8n || print_warning "No running n8n processes"

echo ""
echo "Step 2: Removing n8n installation"
echo "-----------------------------------"

# Remove global n8n
if command -v n8n &> /dev/null; then
    sudo npm uninstall -g n8n
    print_status "n8n uninstalled globally"
else
    print_warning "n8n not installed globally"
fi

# Remove n8n data directories
if [ -d ~/.n8n ]; then
    rm -rf ~/.n8n
    print_status "~/.n8n directory removed"
fi

if [ -d ~/n8n ]; then
    rm -rf ~/n8n
    print_status "~/n8n directory removed"
fi

echo ""
echo "Step 3: Removing old repositories"
echo "-----------------------------------"

# Remove siri_n8n repo
if [ -d ~/siri_n8n ]; then
    rm -rf ~/siri_n8n
    print_status "~/siri_n8n repository removed"
fi

# Remove any other old automation repos
if [ -d ~/home_automation ]; then
    rm -rf ~/home_automation
    print_status "~/home_automation removed"
fi

echo ""
echo "Step 4: Removing systemd service files"
echo "----------------------------------------"

# Remove n8n systemd service
if [ -f /etc/systemd/system/n8n.service ]; then
    sudo rm /etc/systemd/system/n8n.service
    sudo systemctl daemon-reload
    print_status "n8n.service file removed"
fi

echo ""
echo "Step 5: Cleaning Node.js/npm (optional)"
echo "-----------------------------------------"

read -p "Remove Node.js and npm? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Remove PM2 first
    if command -v pm2 &> /dev/null; then
        sudo npm uninstall -g pm2
        print_status "PM2 uninstalled"
    fi

    # Remove Node.js
    sudo apt-get remove --purge -y nodejs npm
    sudo apt-get autoremove -y

    # Clean npm cache
    rm -rf ~/.npm

    print_status "Node.js and npm removed"
else
    print_warning "Keeping Node.js/npm (may be needed for other projects)"
fi

echo ""
echo "Step 6: Cleaning package cache"
echo "--------------------------------"

sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y
print_status "Package cache cleaned"

echo ""
echo "Step 7: Disk space analysis"
echo "----------------------------"

echo "Disk usage before cleanup was saved to ~/disk_usage_before.txt"
echo "Current disk usage:"
df -h | grep -E 'Filesystem|/dev/root'

echo ""
echo "Largest directories in home:"
du -h ~ 2>/dev/null | sort -hr | head -10

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""
echo "Backup location: ~/backups/"
ls -lh ~/backups/n8n_backup_*.tar.gz 2>/dev/null || echo "(no backups found)"
echo ""
echo "Next steps:"
echo "1. Review backup: tar -tzf ~/backups/n8n_backup_*.tar.gz"
echo "2. Deploy py_home: Follow PI_DEPLOYMENT_PLAN.md"
echo "3. Test: curl http://localhost:5000/status"
echo ""

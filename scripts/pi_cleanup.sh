#!/bin/bash
# pi_cleanup.sh - Remove n8n and unused components from Raspberry Pi
# Run on Pi: bash pi_cleanup.sh

set -e  # Exit on error

echo "========================================="
echo "Raspberry Pi Cleanup for py_home"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Check user
if [ "$USER" != "pi" ]; then
    print_error "Please run as pi user, not root"
    exit 1
fi

# Save disk usage before cleanup
df -h > ~/disk_usage_before.txt

echo "Step 0: Backing up n8n data"
echo "----------------------------"

mkdir -p ~/backups/n8n_$(date +%Y%m%d)

if [ -d ~/.n8n ]; then
    cp -r ~/.n8n ~/backups/n8n_$(date +%Y%m%d)/
    print_status "n8n data backed up"
fi

if [ -d ~/n8n ]; then
    cp -r ~/n8n ~/backups/n8n_$(date +%Y%m%d)/
    print_status "n8n workflows backed up"
fi

if [ -d ~/siri_n8n ]; then
    cp -r ~/siri_n8n ~/backups/n8n_$(date +%Y%m%d)/
    print_status "siri_n8n repo backed up"
fi

cd ~/backups
tar -czf n8n_backup_$(date +%Y%m%d).tar.gz n8n_$(date +%Y%m%d)/ 2>/dev/null || true
print_status "Backup archive: ~/backups/n8n_backup_$(date +%Y%m%d).tar.gz"

echo ""
echo "Step 1: Stopping n8n services"
echo "------------------------------"

# Stop systemd service
if systemctl list-units --full -all | grep -q n8n; then
    sudo systemctl stop n8n || print_warning "n8n not running"
    sudo systemctl disable n8n || print_warning "n8n not enabled"
    print_status "systemd service stopped"
else
    print_warning "n8n systemd service not found"
fi

# Stop PM2
if command -v pm2 &> /dev/null; then
    pm2 stop n8n 2>/dev/null || print_warning "n8n not in PM2"
    pm2 delete n8n 2>/dev/null || true
    pm2 save || true
    print_status "PM2 stopped"
fi

# Kill processes
pkill -f n8n || print_warning "No n8n processes"

echo ""
echo "Step 2: Removing n8n"
echo "--------------------"

if command -v n8n &> /dev/null; then
    sudo npm uninstall -g n8n
    print_status "n8n uninstalled"
fi

[ -d ~/.n8n ] && rm -rf ~/.n8n && print_status "~/.n8n removed"
[ -d ~/n8n ] && rm -rf ~/n8n && print_status "~/n8n removed"

echo ""
echo "Step 3: Removing old repos"
echo "--------------------------"

[ -d ~/siri_n8n ] && rm -rf ~/siri_n8n && print_status "siri_n8n removed"
[ -d ~/home_automation ] && rm -rf ~/home_automation && print_status "home_automation removed"

echo ""
echo "Step 4: Removing systemd files"
echo "--------------------------------"

if [ -f /etc/systemd/system/n8n.service ]; then
    sudo rm /etc/systemd/system/n8n.service
    sudo systemctl daemon-reload
    print_status "n8n.service removed"
fi

echo ""
echo "Step 5: Node.js cleanup (optional)"
echo "-----------------------------------"

read -p "Remove Node.js and npm? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    command -v pm2 &> /dev/null && sudo npm uninstall -g pm2 && print_status "PM2 removed"
    sudo apt-get remove --purge -y nodejs npm
    sudo apt-get autoremove -y
    rm -rf ~/.npm
    print_status "Node.js/npm removed"
else
    print_warning "Keeping Node.js/npm"
fi

echo ""
echo "Step 6: Cleaning cache"
echo "----------------------"

sudo apt-get clean
sudo apt-get autoclean
sudo apt-get autoremove -y
print_status "Cache cleaned"

echo ""
echo "Step 7: Disk analysis"
echo "---------------------"

echo "Before cleanup:"
cat ~/disk_usage_before.txt | grep -E 'Filesystem|/dev/root'
echo ""
echo "After cleanup:"
df -h | grep -E 'Filesystem|/dev/root'

echo ""
echo "========================================="
echo "Cleanup Complete!"
echo "========================================="
echo ""
echo "Backup: ~/backups/n8n_backup_$(date +%Y%m%d).tar.gz"
echo ""
echo "Next: Deploy py_home (see PI_DEPLOYMENT_PLAN.md)"
echo ""

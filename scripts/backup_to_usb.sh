#!/bin/bash
# Daily backup to USB drive
# Backs up critical config and state files to /mnt/usb_backup/py_home_backups/

set -euo pipefail

BACKUP_DIR="/mnt/usb_backup/py_home_backups"
PY_HOME="/home/matt.wheeler/py_home"
DATE=$(date +%Y%m%d)
BACKUP_NAME="backup_${DATE}"
RETENTION_DAYS=7

# Check if USB is mounted
if ! mountpoint -q /mnt/usb_backup; then
    echo "ERROR: USB drive not mounted at /mnt/usb_backup"
    exit 1
fi

# Create dated backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

# Backup critical files
echo "Backing up to ${BACKUP_DIR}/${BACKUP_NAME}..."

# Config directory (includes .env and config.yaml)
rsync -av --delete \
    "${PY_HOME}/config/" \
    "${BACKUP_DIR}/${BACKUP_NAME}/config/"

# Data directory (location.json, logs)
rsync -av --delete \
    "${PY_HOME}/data/" \
    "${BACKUP_DIR}/${BACKUP_NAME}/data/"

# State files from home directory
cd "${PY_HOME}"
for state_file in .presence_state .presence_fail_count .night_mode .scheduler_state; do
    if [ -f "${state_file}" ]; then
        cp "${state_file}" "${BACKUP_DIR}/${BACKUP_NAME}/"
    fi
done

# Create metadata file
cat > "${BACKUP_DIR}/${BACKUP_NAME}/backup_info.txt" <<EOF
Backup Date: $(date)
Hostname: $(hostname)
Py_Home Git Commit: $(cd ${PY_HOME} && git rev-parse HEAD 2>/dev/null || echo "unknown")
Backup Contents:
$(du -sh ${BACKUP_DIR}/${BACKUP_NAME}/*)
EOF

echo "Backup completed: ${BACKUP_NAME}"

# Clean up old backups (keep last 7 days)
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -maxdepth 1 -type d -name "backup_*" -mtime +${RETENTION_DAYS} -exec rm -rf {} \;

# Show current backups
echo ""
echo "Current backups:"
ls -lh "${BACKUP_DIR}" | grep "^d" || echo "No backups found"

# Show disk usage
echo ""
df -h /mnt/usb_backup | grep -v Filesystem

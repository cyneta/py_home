# Backup System Documentation

**Date:** 2025-11-06
**Status:** Tier 1 Operational (USB Daily Backups)

---

## Overview

Three-tier backup strategy for py_home Raspberry Pi system:
- **Tier 1:** Local USB drive (IMPLEMENTED ✅)
- **Tier 2:** Git repository (PARTIAL - code only)
- **Tier 3:** Cloud/remote (PLANNED)

---

## Tier 1: Local USB Backup (OPERATIONAL)

### Configuration

**USB Drive:**
- Device: `/dev/sdb1`
- UUID: `8CA1-9D56`
- Size: 30 GB
- Mount: `/mnt/usb_backup` (persistent via /etc/fstab)
- Format: vfat (FAT32)

**Backup Location:** `/mnt/usb_backup/py_home_backups/`

**Schedule:** Daily at 2:00 AM (cron job)

**Retention:** Last 7 days (automatic cleanup)

### What Gets Backed Up

**Critical Files:**
- `config/.env` - API keys, credentials, tokens (1.5 KB)
- `config/config.yaml` - Device settings and automation config (4.9 KB)
- `config/home_location.kml` - Geofence coordinates (2.7 KB)

**State Files:**
- `data/location.json` - Current GPS location
- `.presence_state` - Home/away status
- `.night_mode` - Sleep mode flag
- `.presence_fail_count` - Presence detection retry counter
- `.scheduler_state` - Scheduler status

**Operational Data:**
- `data/logs/` - All automation log files (~21 MB total)

**Backup Size:** ~21 MB per backup

**Storage Used:** ~147 MB for 7 days of backups

### What's NOT Backed Up

**Code (already in git):**
- `automations/`
- `server/`
- `lib/`
- `components/`
- `services/`

**System files:**
- Python packages (reinstallable via requirements.txt)
- OS configuration (fresh install)

### Backup Script

**Location:** `/home/matt.wheeler/py_home/scripts/backup_to_usb.sh`

**What it does:**
1. Verifies USB drive is mounted
2. Creates dated backup folder (`backup_YYYYMMDD`)
3. Uses rsync to copy config and data directories
4. Copies state files from home directory
5. Generates metadata file with timestamp and git commit hash
6. Deletes backups older than 7 days
7. Shows disk usage summary

**Logs:** `/home/matt.wheeler/py_home/data/logs/backup.log`

### Cron Schedule

```bash
# Daily backup to USB at 2 AM
0 2 * * * /home/matt.wheeler/py_home/scripts/backup_to_usb.sh >> /home/matt.wheeler/py_home/data/logs/backup.log 2>&1
```

### Manual Backup

Run backup immediately:
```bash
/home/matt.wheeler/py_home/scripts/backup_to_usb.sh
```

### Recovery Procedure

**Scenario: SD card fails completely**

1. Flash fresh Raspberry Pi OS to new SD card
2. Set up basic system (user account, network, SSH)
3. Mount USB drive:
   ```bash
   sudo mount /dev/sdb1 /mnt/usb_backup
   ```

4. Find latest backup:
   ```bash
   ls -lh /mnt/usb_backup/py_home_backups/
   ```

5. Clone py_home repository:
   ```bash
   git clone https://github.com/[your-repo]/py_home.git ~/py_home
   cd ~/py_home
   ```

6. Restore config files:
   ```bash
   BACKUP_DIR="/mnt/usb_backup/py_home_backups/backup_YYYYMMDD"
   cp -r $BACKUP_DIR/config/* ~/py_home/config/
   cp -r $BACKUP_DIR/data/* ~/py_home/data/
   ```

7. Restore state files:
   ```bash
   cd ~/py_home
   cp $BACKUP_DIR/.presence_state .
   cp $BACKUP_DIR/.night_mode .
   cp $BACKUP_DIR/.presence_fail_count .
   cp $BACKUP_DIR/.scheduler_state .
   ```

8. Install dependencies and deploy:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   sudo cp server/py_home.service /etc/systemd/system/
   sudo systemctl enable py_home
   sudo systemctl start py_home
   ```

**Recovery Time:** ~30 minutes (vs 2-4 hours manual rebuild)

### Testing

**Last test:** 2025-11-06
- ✅ Backup created successfully
- ✅ All files present in backup
- ✅ Credentials (.env) backed up correctly
- ✅ Restore to /tmp/restore_test successful

**Test restore periodically:**
```bash
mkdir -p /tmp/restore_test
cp -r /mnt/usb_backup/py_home_backups/backup_$(date +%Y%m%d)/* /tmp/restore_test/
ls -lh /tmp/restore_test/
rm -rf /tmp/restore_test
```

### Monitoring

**Check backup health:**
```bash
# View recent backups
ls -lh /mnt/usb_backup/py_home_backups/

# Check last backup log
tail -50 /home/matt.wheeler/py_home/data/logs/backup.log

# Verify USB drive is mounted
df -h /mnt/usb_backup

# Check disk usage
du -sh /mnt/usb_backup/py_home_backups/*
```

**Alert on failure:**
- Cron output redirected to backup.log
- Check logs daily for errors
- TODO: Add automated health check with ntfy alerts

### Maintenance

**Monthly tasks:**
- Verify backups are being created (check backup.log)
- Test restore procedure
- Check USB drive health

**Yearly tasks:**
- Consider rotating USB drive (wear)
- Archive old data if needed

---

## Tier 2: Git Repository (PARTIAL)

### Current State

**Implemented:**
- Code synced to origin/main automatically
- Manual commits via /scommit slash command
- Full git history preserved

**Not Implemented:**
- Automatic config backup to git
- Encrypted credential storage in git
- Automated push on config changes

### Future Enhancement

Add git-based config backup:
```bash
# Encrypt .env before committing
git-crypt init
echo "config/.env" >> .gitattributes
git add .gitattributes
git-crypt add-gpg-user [your-key-id]
```

---

## Tier 3: Cloud/Remote Backup (PLANNED)

### Design

**Target:** Weekly encrypted backup to cloud storage or remote server

**Options:**
1. rsync to home laptop over Tailscale
2. AWS S3 (encrypted, lifecycle policy for cost)
3. Backblaze B2 (cheaper than S3)
4. Personal NAS/server

**Implementation:**
- Weekly cron job (Sunday 3 AM)
- Encrypt with gpg before upload
- Retain last 4 weeks (monthly rotation)
- Alert on failure

**Script location (future):** `scripts/backup_to_cloud.sh`

**Estimated cost:**
- S3: $0.50/month for 1 GB with Standard-IA
- Backblaze B2: $0.24/month for 1 GB
- Laptop/NAS: $0 (just electricity)

---

## Backup Status Summary

| Tier | Status | Frequency | Retention | Location | Size |
|------|--------|-----------|-----------|----------|------|
| **Tier 1: USB** | ✅ OPERATIONAL | Daily | 7 days | `/mnt/usb_backup` | 147 MB |
| **Tier 2: Git** | ⚠️ PARTIAL | On commit | Forever | origin/main | Code only |
| **Tier 3: Cloud** | ❌ PLANNED | Weekly | 4 weeks | TBD | ~21 MB |

---

## Recovery Scenarios

| Scenario | Recovery Method | Time | Data Loss |
|----------|----------------|------|-----------|
| Config file corruption | Restore from USB (Tier 1) | 2 min | <24 hours |
| SD card failure | Restore from USB (Tier 1) | 30 min | <24 hours |
| USB drive failure | Restore from git + manual .env | 1 hour | Logs lost |
| House fire/theft | Restore from cloud (Tier 3) | 1 hour | <7 days |
| Accidental deletion | Restore from USB (Tier 1) | 5 min | <24 hours |

---

## Implementation History

**2025-11-06: Tier 1 Implemented**
- USB drive cleaned (removed 9.9 GB old flight test data)
- Created `backup_to_usb.sh` script
- Added persistent USB mount to /etc/fstab
- Configured daily cron job (2 AM)
- Tested backup and restore procedures
- First backup: backup_20251106 (21 MB)

**Next Steps:**
1. Monitor backup.log for one week
2. Test recovery procedure after 7 days
3. Design Tier 3 cloud backup strategy
4. Add backup health check automation
5. Set up ntfy alerts for backup failures

---

## Troubleshooting

### USB drive not mounted after reboot

Check /etc/fstab entry:
```bash
cat /etc/fstab | grep usb_backup
```

Manually mount:
```bash
sudo mount -a
```

### Backup script fails

Check if USB is mounted:
```bash
mountpoint /mnt/usb_backup
```

Check permissions:
```bash
ls -ld /mnt/usb_backup/py_home_backups
```

### Out of space on USB

Remove old backups manually:
```bash
rm -rf /mnt/usb_backup/py_home_backups/backup_YYYYMMDD
```

### Cron job not running

Check cron status:
```bash
systemctl status cron
```

View crontab:
```bash
crontab -l
```

Check backup log:
```bash
tail -100 /home/matt.wheeler/py_home/data/logs/backup.log
```

---

## References

- SD Card Protection: `dev/setup/SD_CARD_PROTECTION.md`
- USB Storage Setup: `dev/setup/USB_STORAGE_SETUP.md`
- Deployment Guide: `dev/setup/DEPLOYMENT.md`
- Backup Script: `scripts/backup_to_usb.sh`

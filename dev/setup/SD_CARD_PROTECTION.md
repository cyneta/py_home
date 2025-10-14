# SD Card Protection Strategies

**Problem:** Raspberry Pi SD cards fail due to write wear and power loss corruption.

**Goal:** Maximize SD card lifespan and prevent data loss.

---

## Pi Non-Volatile Memory Options

Your Raspberry Pi 4 has these storage options:

| Storage Type | Capacity | Speed | Reliability | Boot? | Cost |
|--------------|----------|-------|-------------|-------|------|
| **MicroSD card** | 32GB+ | Slow | Poor (10k writes) | ✅ Yes | $10 |
| **USB Flash Drive** | 32GB+ | Fast | Good (100k writes) | ⚠️ Pi 4 only | $10 |
| **USB SSD** | 128GB+ | Very Fast | Excellent (1M+ writes) | ⚠️ Pi 4 only | $50 |
| **EEPROM** | 512KB | N/A | Excellent | Config only | Built-in |

**Answer:** No, Pi has no other built-in non-volatile memory besides:
- **SD card slot** (primary)
- **EEPROM** (bootloader config only, 512KB, not for data)

**Best Solution:** Use USB flash drive for frequently-written data (see `USB_STORAGE_SETUP.md`)

---

## Protection Strategies (Ranked by Effectiveness)

### Strategy 1: Move High-Write Data to USB ⭐⭐⭐⭐⭐

**Effectiveness:** 90% reduction in SD card writes

**Implementation:** See `USB_STORAGE_SETUP.md`

**What to move:**
- `data/logs/` - Log files (10+ writes/minute)
- `.presence_state` - Updated every 5 minutes
- `.presence_fail_count` - Updated every 5 minutes
- `.night_mode` - Created/deleted daily
- `data/location.json` - Updated on GPS changes

**Result:** SD card only used for:
- OS (rarely changes)
- Python code (only on `git pull`)
- Config files (manual edits only)

---

### Strategy 2: Enable Overlay Filesystem (Read-Only Root) ⭐⭐⭐⭐

**Effectiveness:** 95% reduction in SD card writes, but complex

**How it works:** Root filesystem is read-only, all writes go to RAM (lost on reboot)

**Setup:**
```bash
# Enable overlay filesystem
sudo raspi-config
# 4 Performance Options → P3 Overlay FS → Yes

# Reboot
sudo reboot

# Now root filesystem is read-only!
# To make temporary changes:
sudo raspi-config nonint do_overlayfs 1  # Disable overlay
# Make changes
sudo raspi-config nonint do_overlayfs 0  # Re-enable overlay
sudo reboot
```

**Pros:**
- SD card becomes nearly read-only
- Immune to power loss corruption
- SD card lasts years

**Cons:**
- Logs lost on reboot (unless stored on USB)
- Software updates require disabling overlay
- More complex to maintain

**Recommendation:** Only if you have frequent power issues

---

### Strategy 3: Use log2ram (RAM Disk for Logs) ⭐⭐⭐⭐

**Effectiveness:** 80% reduction in SD card writes

**How it works:** Logs written to RAM, synced to SD hourly

**Setup:**
```bash
# Install
sudo apt-get update
sudo apt-get install log2ram

# Configure
sudo nano /etc/log2ram.conf
# Set SIZE=100M (adjust for your log size)
# Set USE_RSYNC=true

# Restart
sudo systemctl restart log2ram

# Verify
df -h | grep log2ram
# Should show tmpfs mounted on /var/log
```

**Pros:**
- Transparent to applications
- Logs preserved across reboots (synced hourly)
- Easy to set up

**Cons:**
- Uses 100MB RAM
- 1 hour of logs lost if power fails
- Doesn't help with non-log writes

**Compatibility with py_home:**
- Your logs are in `data/logs/`, not `/var/log/`
- Need to either:
  - Move logs to `/var/log/` (log2ram covers them)
  - Or use USB drive (Strategy 1)

---

### Strategy 4: Disable Swap ⭐⭐⭐

**Effectiveness:** 30% reduction in SD card writes

**How it works:** Swap constantly writes to SD card

```bash
# Disable swap
sudo dphys-swapfile swapoff
sudo dphys-swapfile uninstall
sudo systemctl disable dphys-swapfile

# Verify
free -h
# Swap should show 0
```

**Pros:**
- One-line fix
- No downside if you have enough RAM (Pi 4 has 2-8GB)

**Cons:**
- If RAM fills up, system may crash (rare)

**Safe for your system:** Yes, Flask + automations use <500MB RAM

---

### Strategy 5: Mount with noatime ⭐⭐⭐

**Effectiveness:** 20% reduction in SD card writes

**How it works:** Prevents updating file access times

```bash
# Edit fstab
sudo nano /etc/fstab

# Change this line:
/dev/mmcblk0p2  /  ext4  defaults  0  1

# To this:
/dev/mmcblk0p2  /  ext4  defaults,noatime,nodiratime  0  1

# Reboot
sudo reboot

# Verify
mount | grep mmcblk0p2
# Should show "noatime" in options
```

**Pros:**
- Simple one-line change
- No downside (access times rarely needed)

**Cons:**
- Doesn't help with actual data writes (logs, state files)

---

### Strategy 6: Use High-Endurance SD Card ⭐⭐

**Effectiveness:** 3-5x longer lifespan vs regular SD cards

**Recommended cards:**
- **SanDisk High Endurance** (32GB, ~$15) - 10,000 hours recording
- **Samsung PRO Endurance** (32GB, ~$20) - 25,000 hours recording
- **Industrial-grade SD** (32GB, ~$50) - 100,000+ write cycles

**Regular SD cards:** ~10,000 write cycles
**High endurance:** ~100,000 write cycles
**Industrial:** ~1,000,000 write cycles

**Pros:**
- Drop-in replacement
- 3-5x longer life

**Cons:**
- Still fails eventually
- More expensive

---

### Strategy 7: Automated Backups ⭐⭐⭐⭐

**Effectiveness:** Doesn't prevent corruption, but makes recovery instant

**Implementation:**

#### Daily Git Backup (Code + Config)
```bash
# Already done! Your code is in git
cd ~/py_home
git status
```

#### Daily Logs Backup to Cloud
```bash
# Add to crontab
crontab -e

# Daily backup to ntfy (for critical logs)
0 3 * * * cd ~/py_home && tail -100 data/logs/automation.log | curl -d @- https://ntfy.sh/py_home_7h3k2m9x
```

#### Weekly Full System Image (Laptop)
```bash
# On Windows laptop (requires Win32DiskImager or similar)
# Backup SD card to .img file weekly
# Store on external drive

# Or use rsync over network:
rsync -avz --delete matt.wheeler@raspberrypi.local:~ ./pi_backup/
```

---

## Monitoring SD Card Health

### Check SD Card Wear
```bash
# Install smartmontools
sudo apt-get install smartmontools

# Check SD card SMART data (if supported)
sudo smartctl -a /dev/mmcblk0

# Check filesystem errors
sudo fsck -n /dev/mmcblk0p2
```

### Monitor Write Activity
```bash
# Install iostat
sudo apt-get install sysstat

# Watch real-time writes
iostat -x 2
# Look at mmcblk0 "w/s" (writes per second)

# Total writes since boot
cat /proc/diskstats | grep mmcblk0
```

### Set Up Alerts
```bash
# Add to cron (daily check)
crontab -e

# Daily SD card health check
0 4 * * * sudo smartctl -H /dev/mmcblk0 || curl -d "SD card health check failed!" https://ntfy.sh/py_home_7h3k2m9x
```

---

## Recovery Plan

### If SD Card Corrupts

**Symptom:** Pi won't boot, or files corrupted

**Recovery Steps:**

1. **Flash new SD card** (keep corrupted card as backup)
   ```bash
   # On Windows: Use Raspberry Pi Imager
   # Flash Raspberry Pi OS Lite
   ```

2. **Run deployment script**
   ```bash
   # Follow DEPLOYMENT.md
   git clone https://github.com/cyneta/py_home.git
   cd py_home
   ./scripts/deploy_pi.sh
   ```

3. **Restore .env credentials** (from 1Password backup)
   ```bash
   nano config/.env
   # Paste credentials
   ```

4. **Remount USB data drive** (if using USB strategy)
   ```bash
   sudo mount /dev/sda1 /mnt/usb_data
   # Data intact!
   ```

5. **Test system**
   ```bash
   curl http://localhost:5000/status
   ```

**Total recovery time:** ~30 minutes (if USB drive preserved data)

---

## Recommended Combination

**For maximum protection, combine these strategies:**

1. ✅ **USB drive for data** (Strategy 1) - Eliminates 90% of SD writes
2. ✅ **Disable swap** (Strategy 4) - Quick win
3. ✅ **Enable noatime** (Strategy 5) - No downside
4. ✅ **Use high-endurance SD card** (Strategy 6) - Buy once
5. ✅ **Daily git backups** (Strategy 7) - Safety net

**Result:**
- SD card writes reduced by ~95%
- Expected SD card lifespan: 5-10 years (vs 1-2 years)
- Recovery time if failure: <30 minutes

---

## Implementation Priority

**Immediate (Do Now):**
1. Order USB flash drive (~$10)
2. Disable swap (1 minute)
3. Enable noatime in fstab (2 minutes)

**This Week:**
1. Set up USB drive for data (30 minutes)
2. Move logs to USB (5 minutes)
3. Test for a week

**Optional (Later):**
1. Buy high-endurance SD card (~$15)
2. Set up log2ram (if not using USB)
3. Enable overlay filesystem (if power issues)

---

## Cost Summary

| Item | Cost | Benefit |
|------|------|---------|
| **USB Flash Drive** | $10 | 90% write reduction |
| **High-Endurance SD Card** | $15 | 5x longer lifespan |
| **USB SSD (overkill)** | $50 | 10x longer lifespan |
| **Free strategies** | $0 | 50% write reduction |

**Best bang for buck:** $10 USB drive + free strategies = 95% write reduction

---

## References

- [Raspberry Pi SD Card Wear Leveling](https://www.raspberrypi.com/documentation/computers/config_txt.html)
- [log2ram GitHub](https://github.com/azlux/log2ram)
- [USB Boot Pi 4](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#usb-boot)

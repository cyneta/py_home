# USB Storage Setup for Pi

**Goal:** Reduce SD card wear by storing frequently-written data on USB flash drive.

**Why:** USB flash drives are more robust than SD cards for frequent writes.

---

## Hardware

**Recommended USB Drive:**
- **SanDisk Ultra Fit 32GB+** (~$10) - low profile, USB 3.0
- **Samsung BAR Plus** - durable metal casing
- **Avoid:** Cheap no-name drives

**Alternative:** USB SSD (overkill but ultra-reliable)
- **Samsung T7 Portable SSD** (~$50 for 500GB)

---

## Setup: Mount USB Drive for Data

### Step 1: Insert USB Drive, Format It

```bash
# SSH to Pi
ssh matt.wheeler@raspberrypi.local

# Find the USB drive
lsblk
# Look for something like /dev/sda1 (8-32GB size)

# Format as ext4
sudo mkfs.ext4 /dev/sda1 -L py_home_data

# Create mount point
sudo mkdir -p /mnt/usb_data
```

### Step 2: Auto-Mount on Boot

```bash
# Get UUID
sudo blkid /dev/sda1
# Copy the UUID (e.g., 1234-5678-90AB)

# Add to /etc/fstab
sudo nano /etc/fstab

# Add this line (replace UUID with yours):
UUID=1234-5678-90AB  /mnt/usb_data  ext4  defaults,noatime  0  2

# Test mount
sudo mount -a
df -h  # Verify /mnt/usb_data shows up
```

### Step 3: Move py_home Data to USB

```bash
cd ~/py_home

# Stop Flask
sudo systemctl stop py_home

# Move data directory to USB
sudo rsync -av data/ /mnt/usb_data/py_home_data/
sudo mv data data.old  # Backup original
ln -s /mnt/usb_data/py_home_data data  # Create symlink

# Verify
ls -la data/  # Should show -> /mnt/usb_data/py_home_data

# Restart Flask
sudo systemctl start py_home

# Test
curl http://localhost:5000/status

# If everything works, delete backup
# rm -rf data.old
```

### Step 4: Move Logs to USB (High-Write Files)

```bash
# Move logs to USB
sudo rsync -av data/logs/ /mnt/usb_data/py_home_logs/
rm -rf data/logs
ln -s /mnt/usb_data/py_home_logs data/logs

# Restart services
sudo systemctl restart py_home
```

---

## What to Store on USB vs SD Card

### USB Drive (Frequent Writes)
✅ `data/logs/` - Log files (constant writes)
✅ `data/location.json` - GPS updates
✅ `.presence_state` - Presence updates every 5 min
✅ `.presence_fail_count` - Frequent updates
✅ `.night_mode` - Created/deleted daily

### SD Card (Rare Writes)
✅ Operating system (`/`)
✅ Python code (`~/py_home/`)
✅ Config files (`config/config.yaml`)
✅ `.env` credentials (read-only)

---

## Testing USB Drive Reliability

```bash
# Check USB drive health
sudo smartctl -a /dev/sda  # If supported

# Monitor I/O stats
iostat -x 5  # Watch sda vs mmcblk0

# Check filesystem
sudo fsck /dev/sda1
```

---

## Backup Strategy

### Auto-Backup USB to Git (Daily Cron)

```bash
# Add to crontab
crontab -e

# Daily backup of logs to git (if small enough)
0 2 * * * cd ~/py_home && tar -czf data/logs_backup_$(date +\%Y\%m\%d).tar.gz data/logs/ && git add data/logs_backup_*.tar.gz && git commit -m "Daily log backup" && git push
```

### Manual Backup to Cloud

```bash
# Backup to your laptop via rsync
rsync -avz matt.wheeler@raspberrypi.local:/mnt/usb_data/ ./pi_backup/
```

---

## Recovery Plan

**If USB drive fails:**
1. Insert new USB drive
2. Format and mount (Steps 1-2 above)
3. Restore from git/laptop backup
4. Restart services

**If SD card fails:**
1. Flash new SD card with OS
2. Re-run deployment script
3. USB data is intact! Just remount it

---

## Performance Comparison

| Operation | SD Card | USB 3.0 Drive | USB SSD |
|-----------|---------|---------------|---------|
| Random Write | ~10 MB/s | ~30 MB/s | ~400 MB/s |
| Seq Write | ~20 MB/s | ~100 MB/s | ~500 MB/s |
| Latency | ~10ms | ~5ms | ~1ms |
| Lifespan | 10k writes | 100k writes | 1M+ writes |
| Cost | Included | $10 | $50 |

---

## Troubleshooting

### USB drive not mounting on boot
```bash
# Check fstab syntax
sudo mount -a

# Check USB drive is detected
lsblk

# Check systemd mount logs
sudo journalctl -u mnt-usb_data.mount
```

### Flask can't write to USB
```bash
# Fix permissions
sudo chown -R matt.wheeler:matt.wheeler /mnt/usb_data/
chmod -R 755 /mnt/usb_data/
```

### USB drive disappeared
```bash
# Check if USB unplugged or failed
dmesg | tail -50

# Remount manually
sudo mount /dev/sda1 /mnt/usb_data
```

---

## Next Steps

1. Order USB flash drive (~$10)
2. Follow setup steps above
3. Monitor for a week to ensure stability
4. Delete old data from SD card
5. Set up automated backups

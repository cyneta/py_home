# Config Sync System

Automatic synchronization of `config.local.yaml` with schema changes from `config.yaml`.

---

## Overview

py_home uses a two-layer config system:
- **`config.yaml`** - Base configuration (committed to git)
- **`config.local.yaml`** - Local overrides (gitignored, machine-specific)

When `config.yaml` is updated in git (new features, new settings), your `config.local.yaml` needs to get those new keys. The **config sync system** automates this.

---

## Quick Start

### First-Time Setup (Per Machine)

```bash
# Install git hook for automatic notifications
bash scripts/install_git_hooks.sh
```

That's it! From now on, `git pull` will automatically detect config changes.

### After Git Pull

```bash
git pull
# ═══════════════════════════════════════════════════════════
#   ⚙️  config.yaml was updated in this merge
# ═══════════════════════════════════════════════════════════
#
# Found 3 new key(s) to add:
#   + temperatures.weather_aware.cold_target: 72
#   + temperatures.weather_aware.hot_target: 68
#   + device_timeouts.connect: 5
#
# To apply: python3 scripts/sync_local_config.py

# Apply the changes
python3 scripts/sync_local_config.py

# Review new values (customize if needed)
nano config/config.local.yaml

# Restart service
sudo systemctl restart py_home
```

---

## How It Works

### The Two-Layer Config System

```yaml
# config.yaml (base, in git)
temperatures:
  comfort: 70
  bedroom_sleep: 66

# config.local.yaml (your overrides, gitignored)
temperatures:
  comfort: 72  # ← Your custom value

# Runtime merged result:
temperatures:
  comfort: 72          # ← Your override wins
  bedroom_sleep: 66    # ← Default from base
```

### Schema Evolution Problem

**Scenario:** A new feature is added that requires new config keys.

```yaml
# config.yaml gets updated in git:
temperatures:
  comfort: 70
  bedroom_sleep: 66
  weather_aware:        # ← NEW!
    cold_target: 72
    hot_target: 68
```

**Problem:** Your `config.local.yaml` doesn't have `weather_aware`, so the new feature breaks.

**Old solution:** Manually figure out what changed and add it.

**New solution:** Config sync does it automatically.

### Automatic Sync Process

```
┌─────────────┐
│  git pull   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ post-merge hook triggers        │
│ (if config.yaml changed)        │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Compares config.yaml vs         │
│ config.local.yaml               │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Shows preview:                  │
│ • New keys to add               │
│ • Obsolete keys to remove       │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ You run sync script             │
│ (with confirmation)             │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ • Backup created                │
│ • New keys added (defaults)     │
│ • Obsolete keys removed         │
│ • Your overrides preserved      │
└─────────────────────────────────┘
```

---

## Safety Guarantees

### Your Settings Are Never Overwritten ✅

```python
# The merge algorithm:
if key exists in config.local.yaml:
    keep your value  # ← Never touched!
else:
    add from config.yaml with default value
```

**Example:**
```yaml
# You have:
temperatures:
  comfort: 72

# Base has:
temperatures:
  comfort: 70

# After sync:
temperatures:
  comfort: 72  # ← YOUR VALUE STAYS!
```

### Backups Are Always Created ✅

Before every modification:
```
config.local.backup_20251018_153204.yaml  # Timestamped
```

Easy rollback:
```bash
cp config/config.local.backup_20251018_153204.yaml config/config.local.yaml
```

### Dry-Run Preview Available ✅

Always preview before applying:
```bash
python3 scripts/sync_local_config.py --dry-run
```

---

## Usage Guide

### sync_local_config.py

**Preview mode (recommended first step):**
```bash
python3 scripts/sync_local_config.py --dry-run
```

Output:
```
Found 3 new key(s) to add:
  + temperatures.weather_aware.cold_target: 72
  + temperatures.weather_aware.hot_target: 68
  + device_timeouts.connect: 5

Found 1 obsolete key(s) to remove:
  - automations.night_mode: True

(Dry run mode - no files modified)
```

**Interactive mode (prompts for confirmation):**
```bash
python3 scripts/sync_local_config.py
```

Output:
```
This will update /path/to/config.local.yaml
A backup will be created before modifying the file.
  • 3 key(s) will be added
  • 1 obsolete key(s) will be removed

Continue? [y/N]: y

✓ Backup created: config.local.backup_20251018_153204.yaml
✓ Updated: config.local.yaml
  Added 3 new key(s) with default values
  Removed 1 obsolete key(s)
```

**Force mode (no prompts, for automation):**
```bash
python3 scripts/sync_local_config.py --force
```

### install_git_hooks.sh

**One-time setup:**
```bash
bash scripts/install_git_hooks.sh
```

Output:
```
Installing py_home git hooks...

✓ Git hooks installed successfully!

The post-merge hook will now:
  • Detect when config.yaml changes after git pull
  • Auto-run sync script in preview mode
  • Show you what keys would be added/removed
  • Prompt you to apply changes if needed
```

**Where to run:**
- Development machines
- Pi deployment
- Any environment that pulls git updates

---

## Common Workflows

### Development Machine Workflow

```bash
# 1. One-time setup
bash scripts/install_git_hooks.sh

# 2. Work on feature, update config.yaml
nano config/config.yaml
git add config/config.yaml
git commit -m "Add weather-aware temperature settings"
git push

# 3. Pull on another machine
git pull
# ← Hook notifies you of config changes

# 4. Sync config
python3 scripts/sync_local_config.py

# 5. Test
python server/app.py
```

### Pi Deployment Workflow

```bash
# 1. SSH to Pi (one-time setup)
ssh matt.wheeler@100.107.121.6
cd /home/matt.wheeler/py_home
bash scripts/install_git_hooks.sh

# 2. Future deployments
git pull
# ← Hook tells you if config changed

# If changes detected:
python3 scripts/sync_local_config.py
sudo systemctl restart py_home
```

### First Deployment (No config.local.yaml Yet)

```bash
# Script creates config.local.yaml from scratch
python3 scripts/sync_local_config.py --force

# Creates new file with ALL keys from base config
# Now customize for this machine:
nano config/config.local.yaml

# Common Pi customizations:
automations:
  dry_run: false  # Run for real on Pi

logging:
  level: INFO     # Less verbose on Pi

server:
  debug: false    # Production mode
```

---

## What Gets Synced

### New Keys (Added)

When `config.yaml` gets new keys:
```yaml
# Added to config.local.yaml with default values
device_timeouts:
  connect: 5
  status: 5
  control: 10
```

You can then customize:
```yaml
device_timeouts:
  connect: 10  # Slower network, need more time
  status: 5
  control: 10
```

### Obsolete Keys (Removed)

When keys are removed from `config.yaml`:
```yaml
# Removed from config.local.yaml (they do nothing anyway)
# Old deprecated keys are cleaned up automatically
```

### Preserved Keys (Never Touched)

Your existing overrides:
```yaml
temperatures:
  comfort: 72  # ← Your custom value, NEVER changed
```

---

## Troubleshooting

### Hook Not Running After git pull

**Check if hook is installed:**
```bash
ls -la .git/hooks/post-merge
# Should show: -rwxr-xr-x (executable)
```

**Reinstall if missing:**
```bash
bash scripts/install_git_hooks.sh
```

### Script Says "No Changes Needed"

Your config is already up to date! Nothing to do.

### Want to See What Would Change

Always safe to run:
```bash
python3 scripts/sync_local_config.py --dry-run
```

### Accidentally Applied Wrong Changes

Restore from backup:
```bash
# Find latest backup
ls -lt config/config.local.backup_*

# Restore it
cp config/config.local.backup_20251018_153204.yaml config/config.local.yaml
```

### Hook Shows Python Error

Make sure you're in the project directory:
```bash
cd /home/matt.wheeler/py_home
git pull
```

Hook runs `python3 scripts/sync_local_config.py` which needs project root.

---

## Advanced Usage

### Automated Deployment Script

```bash
#!/bin/bash
# scripts/deploy_to_pi.sh

set -e

echo "Deploying to Pi..."

# Push changes
git push

# SSH and update
ssh matt.wheeler@100.107.121.6 << 'EOF'
cd /home/matt.wheeler/py_home
git pull
python3 scripts/sync_local_config.py --force
sudo systemctl restart py_home
echo "Deployment complete!"
EOF
```

### Skip Hook for Specific Pull

```bash
# Temporarily disable hook
mv .git/hooks/post-merge .git/hooks/post-merge.disabled

git pull

# Re-enable
mv .git/hooks/post-merge.disabled .git/hooks/post-merge
```

### Batch Update Multiple Machines

```bash
# Update all deployments
for host in dev-machine pi-server backup-pi; do
    echo "Updating $host..."
    ssh $host "cd ~/py_home && git pull && python3 scripts/sync_local_config.py --force"
done
```

---

## Technical Details

### How merge_new_keys() Works

```python
# 1. Flatten both configs to dot-separated paths
base_keys = {'temperatures.comfort': 70, 'logging.level': 'INFO', ...}
local_keys = {'temperatures.comfort': 72, ...}

# 2. Find differences
new_keys = base_keys - local_keys  # Missing in local
obsolete_keys = local_keys - base_keys  # No longer in base

# 3. Add new keys
for key in new_keys:
    set_nested_value(local_config, key, base_keys[key])

# 4. Remove obsolete keys
for key in obsolete_keys:
    delete_nested_key(local_config, key)

# 5. Your existing values never touched (they're not in new_keys)
```

### Why Git Hooks Aren't Committed

Git hooks in `.git/hooks/` are local to each clone. They:
- Don't get committed to the repository
- Need to be installed per machine
- Can be customized per deployment

Solution: We commit the hook *template* to `scripts/git-hooks/` and provide an installer script.

---

## See Also

- `scripts/README.md` - Script usage examples
- `config/README.md` - Config system overview
- `lib/config.py` - Runtime config loading and merging
- `lib/config_validator.py` - Schema validation

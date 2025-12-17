# Git Sync Workflow (Local ↔ Pi)

**Problem:** Changes can be made on both local machine and Pi, need safe bidirectional sync.

## Current Setup

- **Local:** `C:\git\cyneta\py_home` (development machine)
- **Pi:** `/home/matt.wheeler/py_home` (live system at 100.107.121.6)
- **Remote:** `origin/main` (GitHub - source of truth)
- **Network share:** `\\100.107.121.6\py_home` (direct Pi file access)

## Recommended Workflow

### Option 1: Git-First (Safest, Most Control)

**For planned changes (development):**
1. Make changes locally
2. Test locally if possible
3. Commit: `/scommit` or `/mcommit`
4. Push: `git push`
5. Deploy to Pi:
   ```bash
   ssh matt.wheeler@100.107.121.6 \
     'cd /home/matt.wheeler/py_home && git pull && sudo systemctl restart py_home'
   ```

**For emergency fixes (live system):**
1. Edit directly on Pi (via SSH or network share)
2. Config watcher auto-reloads (no restart needed for config changes)
3. When stable, commit from Pi:
   ```bash
   ssh matt.wheeler@100.107.121.6 'cd /home/matt.wheeler/py_home && git add -A && git commit -m "Fix: description"'
   ```
4. Pull locally: `git pull`

**Pros:**
- Full history preserved
- Can review diffs before committing
- Can revert bad changes
- Clear separation of dev vs live

**Cons:**
- Requires SSH for Pi changes
- Extra steps for quick tweaks

---

### Option 2: Network Share + Periodic Commits (Convenient)

**For quick config tweaks:**
1. Edit directly via `\\100.107.121.6\py_home\config\config.yaml`
2. Config watcher auto-reloads (changes take effect immediately)
3. Test the change
4. If good, commit from Pi:
   ```bash
   ssh matt.wheeler@100.107.121.6 \
     'cd /home/matt.wheeler/py_home && git add config/config.yaml && git commit -m "Update config"'
   ```
5. Pull locally: `git pull`

**For code changes:**
- Always use Option 1 (Git-First)

**Pros:**
- Instant feedback for config changes
- No SSH needed for editing
- Can use Windows editors (VS Code, Notepad++)

**Cons:**
- Easy to forget to commit
- Risk of uncommitted changes piling up
- No pre-commit review

---

## Conflict Prevention Rules

1. **Never edit the same file on both machines without syncing**
2. **Always pull before making changes**
3. **Commit and push frequently**
4. **Check status before and after sync:**
   ```bash
   # Local
   git status

   # Pi
   ssh matt.wheeler@100.107.121.6 'cd /home/matt.wheeler/py_home && git status'
   ```

---

## Handling Conflicts

If both machines have uncommitted changes to the same file:

### Method 1: Stash and Reapply (Preferred)

```bash
# On machine with less important changes (usually local)
git stash push -m "Local changes before sync"
git pull
git stash pop
# Resolve conflicts if any
git add <resolved-files>
git commit -m "Merge local changes"
git push
```

### Method 2: Commit Both Sides (More History)

```bash
# On local machine
git add -A
git commit -m "Local changes before sync"
git pull  # Will create merge commit if conflicts
# Resolve conflicts if any
git add <resolved-files>
git commit -m "Merge Pi changes"
git push
```

---

## Safe Sync Script

Create `~/bin/sync-py-home.sh`:
```bash
#!/bin/bash
# Safe bidirectional sync for py_home

set -e

LOCAL_DIR="/c/git/cyneta/py_home"
PI_HOST="matt.wheeler@100.107.121.6"
PI_DIR="/home/matt.wheeler/py_home"

echo "=== Checking status ==="

# Check local status
echo "Local:"
cd "$LOCAL_DIR"
git status -s

# Check Pi status
echo ""
echo "Pi:"
ssh "$PI_HOST" "cd $PI_DIR && git status -s"

echo ""
echo "=== Options ==="
echo "1) Pull from origin (safe if both clean)"
echo "2) Commit local + push + pull on Pi"
echo "3) Commit Pi + push + pull local"
echo "4) Show detailed status"
echo "5) Cancel"
read -p "Choice: " choice

case $choice in
    1)
        echo "Pulling local..."
        git pull
        echo "Pulling Pi..."
        ssh "$PI_HOST" "cd $PI_DIR && git pull && sudo systemctl restart py_home"
        echo "✓ Both synced with origin"
        ;;
    2)
        read -p "Commit message: " msg
        git add -A
        git commit -m "$msg"
        git push
        ssh "$PI_HOST" "cd $PI_DIR && git pull && sudo systemctl restart py_home"
        echo "✓ Local → origin → Pi"
        ;;
    3)
        read -p "Commit message: " msg
        ssh "$PI_HOST" "cd $PI_DIR && git add -A && git commit -m '$msg' && git push"
        git pull
        echo "✓ Pi → origin → local"
        ;;
    4)
        echo "=== Local full status ==="
        git status
        echo ""
        echo "=== Pi full status ==="
        ssh "$PI_HOST" "cd $PI_DIR && git status"
        ;;
    *)
        echo "Cancelled"
        exit 1
        ;;
esac
```

---

## Current State

**Local has:**
- Modified: `.claude/settings.local.json`
- Untracked: `dev/tasks/`

**Pi has:**
- Modified: `config/config.yaml` (dry_run: false)
- Modified: `data/location.json`
- Untracked: backup files, logs, deprecated files

**To sync now:**
```bash
# Option A: Keep Pi's config.yaml, discard local change
cd /c/git/cyneta/py_home
git restore config/config.yaml  # Undo local edit
git pull  # Get Pi's version when it's committed

# Option B: Force local version to match Pi
ssh matt.wheeler@100.107.121.6 \
  'cd /home/matt.wheeler/py_home && git add config/config.yaml data/location.json && git commit -m "Update config: disable dry-run"'
git pull

# Option C: Cherry-pick changes (if both have valuable edits)
# Manually resolve by editing the file to combine both changes
```

---

## Gitignore Strategy

Files that should stay untracked on Pi:
- `data/logs/` (runtime logs)
- `*.backup` (config backups)
- `*.deprecated` (old code kept for reference)
- `*.local` (machine-specific scripts)

Update `.gitignore`:
```
data/logs/
*.backup
*.deprecated
scripts/*.local
```

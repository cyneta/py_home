## Raspberry Pi SSH Access

When syncing code to the Raspberry Pi, use credentials from `config/.env`:
- Username: `${PI_USERNAME}` (matt.wheeler)
- Host: `${PI_HOST}` (Tailscale IP: 100.107.121.6)

SSH command: `ssh ${PI_USERNAME}@${PI_HOST}`

Sync workflow:
1. Commit and push changes to origin/main
2. SSH to Pi: `ssh matt.wheeler@100.107.121.6`
3. Pull changes: `cd /home/matt.wheeler/py_home && git pull`
4. Restart service: `sudo systemctl restart py_home`

## Deprecated Code

When deprecating code files (scripts, modules, etc.):
1. Create `deprecated/` subfolder in the same directory as the deprecated file
2. Move file into `deprecated/` to keep it out of active listings
3. Add deprecation notice to file header with:
   - Deprecation date
   - Reason for deprecation
   - What replaced it
   - Why kept (historical reference, etc.)
4. Remove from cron/systemd if applicable
5. Update documentation references

Example: `automations/tempstick_monitor.py` → `automations/deprecated/tempstick_monitor.py`
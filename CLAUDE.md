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
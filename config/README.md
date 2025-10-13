# Configuration

## Overview

py_home uses a layered configuration system:

1. **config.yaml** - Base configuration (committed to git)
2. **config.local.yaml** - Optional local overrides (gitignored)
3. **.env** - Sensitive credentials (gitignored)

## Files

### config.yaml (Base Configuration)
- Committed to git
- Contains all default settings
- Safe to share (no secrets)
- Changes here propagate to all instances via git pull

### config.local.yaml (Local Overrides)
- **Optional** - only create if you need instance-specific settings
- Gitignored - never committed
- Only needs values you want to override
- Useful for testing or per-instance customization

Example `config.local.yaml`:
```yaml
# Override just the comfort temp on Pi for testing
nest:
  comfort_temp: 68

# Override automation settings
automation:
  temp_coordination:
    night_mode_temp_f: 64
```

### .env (Credentials)
- Gitignored - never committed
- Contains API keys, passwords, tokens
- Referenced in config files with `${VAR_NAME}` syntax
- Copy from `.env.example` and fill in real values

## How It Works

Configuration is loaded in this order:

1. Load `config.yaml` (base)
2. Deep merge `config.local.yaml` if it exists (overrides)
3. Resolve environment variables from `.env` (secrets)

**Deep merge** means nested values are merged, not replaced:

```yaml
# config.yaml
nest:
  comfort_temp: 70
  away_temp: 62

# config.local.yaml
nest:
  comfort_temp: 68  # Override just this

# Result:
nest:
  comfort_temp: 68  # From local
  away_temp: 62     # From base
```

## Workflow

### Normal Use (No Local Overrides)
1. Edit `config.yaml`
2. Commit and push
3. Pull on Pi
4. Changes take effect on next automation run

✅ Simple, changes propagate everywhere

### Pi-Specific Settings
1. Create `config/config.local.yaml` on Pi only
2. Add just the values you want different
3. Pull updates to `config.yaml` normally
4. Local overrides persist automatically

✅ No merge conflicts, changes still propagate

### Adding New Settings
1. Add to `config.yaml` with sensible defaults
2. Commit and push
3. Pull everywhere
4. Override in `config.local.yaml` if needed per instance

✅ New settings available immediately on all instances

## Example: Testing Temperature Settings

On your dev machine, you might want to test with different temps without affecting Pi:

```yaml
# config/config.local.yaml (dev machine only)
nest:
  comfort_temp: 65  # Testing lower temp

automation:
  temp_coordination:
    night_mode_temp_f: 62  # Testing colder night mode
```

The Pi continues using values from `config.yaml` (70°F and 66°F).

## When to Use Each File

| Setting Type | File | Example |
|-------------|------|---------|
| **Shared defaults** | config.yaml | Default temps, device IPs, thresholds |
| **Instance-specific** | config.local.yaml | Testing different values on Pi vs dev |
| **Sensitive credentials** | .env | API keys, passwords, tokens |

## State Files

Some settings are managed by state files (not config):
- `.night_mode` - Current night mode state (created by automations)
- `.presence_state` - Last known presence state
- `.alert_state/` - Alert cooldown tracking

These are runtime state, not configuration.

## Network Configuration (Raspberry Pi)

### Static IP Address
The Pi is configured with a static IP to prevent address changes after reboots:

**IP Address:** `192.168.50.189`
**Hostname:** `raspberrypi.local` (resolves to 192.168.50.189)
**Gateway:** `192.168.50.1`
**DNS:** `192.168.50.1`, `8.8.8.8`

**Configuration Method:** NetworkManager (not dhcpcd)
```bash
# View current config:
sudo nmcli connection show preconfigured

# Modify if needed:
sudo nmcli connection modify preconfigured ipv4.addresses 192.168.50.189/24
```

### Access Methods
- **SSH:** `ssh matt.wheeler@raspberrypi.local` or `ssh matt.wheeler@192.168.50.189`
- **Flask Server:** `http://raspberrypi.local:5000` or `http://192.168.50.189:5000`
- **Dashboard:** `http://raspberrypi.local:5000/dashboard`

### Why Static IP?
Static IP prevents:
- IP address changes after long power outages (DHCP lease expiration)
- iOS Shortcuts breaking when Pi gets new IP
- Need to hunt for new IP after reboots
- Hardcoded IP references becoming stale

**Note:** Always use `sudo shutdown -h now` before unplugging power to prevent SD card corruption.

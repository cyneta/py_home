# Scripts Directory

Utility scripts for py_home system maintenance and setup.

## Config Management

### sync_local_config.py

Sync `config.local.yaml` with schema changes from `config.yaml` after git updates.

```bash
# Preview changes
python3 scripts/sync_local_config.py --dry-run

# Apply changes
python3 scripts/sync_local_config.py
```

See [dev/CONFIG_SYNC_GUIDE.md](../dev/CONFIG_SYNC_GUIDE.md) for complete guide.

### install_git_hooks.sh

One-time setup for automatic config change notifications:

```bash
bash scripts/install_git_hooks.sh
```

After installation, `git pull` automatically detects and previews config changes.

## Nest Authentication

### get_nest_token.py
Generate OAuth token for Google Nest API integration.

### nest_reauth.py, nest_reauth_device_flow.py, nest_reauth_standard.py
Various methods for re-authenticating with Nest API.

### deploy_nest_token.sh
Deploy Nest token to remote Pi server.

### test_nest_auth.py
Test Nest API authentication.

## Logging & Debugging

### preview_log_format.py
Preview structured log output formatting.

### test_logging.py
Test logging configuration and output.

## Notifications

### test_ntfy.py
Test ntfy notification service integration.

## iOS Shortcuts

See `scripts/ios/` for iOS Shortcuts automation examples.

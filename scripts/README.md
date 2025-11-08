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

### get_nest_token.py ⭐ (PRIMARY METHOD)

**Use this one to fix Nest authentication.**

Generate OAuth token for Google Nest API integration. This is the proven working method that uses manual code copy/paste from the browser redirect URL.

```bash
python scripts/get_nest_token.py
```

Follow the on-screen instructions to:
1. Open the authorization URL in your browser
2. Sign in with matthew.g.wheeler@gmail.com
3. Copy the code from the redirect URL
4. Paste it to get your refresh token
5. Update `NEST_REFRESH_TOKEN` in config/.env

### Alternative OAuth Methods

**Only use these if the primary method doesn't work:**

- `nest_reauth.py` - Uses localhost:8080 redirect (requires Google Cloud Console setup)
- `nest_reauth_device_flow.py` - OAuth device flow (TV-style authentication)
- `nest_reauth_standard.py` - Standard Google OAuth endpoint (not Nest-specific)

### Other Nest Tools

- `deploy_nest_token.sh` - Deploy Nest token to remote Pi server
- `test_nest_auth.py` - Test Nest API authentication

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

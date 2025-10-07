# Flask Webhook Server

HTTP server for triggering py_home automations via iOS Shortcuts.

## Quick Start

```bash
# Start server (development mode)
python server/app.py

# Server will be available at:
# http://localhost:5000
```

## Endpoints

### Health Check
```bash
GET /
GET /status
```

### Automation Triggers
```bash
# Leaving home automation
POST /leaving-home

# Goodnight automation
POST /goodnight

# Welcome home automation
POST /im-home

# Good morning automation
POST /good-morning

# Travel time query (returns JSON)
GET /travel-time?destination=Milwaukee,%20WI
POST /travel-time
{
  "destination": "Milwaukee, WI"
}

# Add task (routes to GitHub/Checkvist)
POST /add-task
{
  "task": "Buy groceries"
}
```

## Configuration

Set environment variables or add to `.env`:

```bash
# Server settings
FLASK_HOST=0.0.0.0          # Listen on all interfaces
FLASK_PORT=5000             # Port number
FLASK_DEBUG=false           # Debug mode (dev only)

# Security
FLASK_SECRET_KEY=your-secret-key-here

# Optional: Require authentication
FLASK_REQUIRE_AUTH=true
FLASK_AUTH_USERNAME=admin
FLASK_AUTH_PASSWORD=your-password

# Logging
FLASK_LOG_LEVEL=INFO
FLASK_LOG_FILE=/var/log/py_home.log  # Optional
```

## iOS Shortcuts Integration

### Example: "I'm Leaving" Shortcut

1. Create new shortcut in iOS Shortcuts app
2. Add "Get Contents of URL" action
3. Configure:
   - URL: `http://your-server-ip:5000/leaving-home`
   - Method: POST
   - Headers: (if auth enabled)
     - Authorization: `Basic base64(username:password)`
4. Add "Show Notification" with result

### Example: "Travel Time" Shortcut

1. Create shortcut with "Ask for Input" (destination)
2. Add "Get Contents of URL":
   - URL: `http://your-server-ip:5000/travel-time?destination=[input]`
   - Method: GET
3. Add "Get Dictionary Value" for `duration_in_traffic_minutes`
4. Add "Speak Text": "Travel time is [value] minutes"

## Testing

```bash
# Start server in one terminal
python server/app.py

# Test in another terminal
python test_server.py

# Or test with curl
curl http://localhost:5000/status
curl -X POST http://localhost:5000/goodnight
curl "http://localhost:5000/travel-time?destination=Milwaukee"
```

## Production Deployment

### Option 1: Systemd Service (Linux/Raspberry Pi)

See `server/py_home.service` for systemd service file.

```bash
# Copy service file
sudo cp server/py_home.service /etc/systemd/system/

# Enable and start
sudo systemctl enable py_home
sudo systemctl start py_home

# Check status
sudo systemctl status py_home
```

### Option 2: Windows Service

Run with Python in startup folder or use NSSM (Non-Sucking Service Manager).

### Option 3: Production WSGI Server

```bash
# Install gunicorn (Linux)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server.app:app
```

## Security Notes

- **Development**: Run without auth for testing on local network
- **Production**:
  - Enable `FLASK_REQUIRE_AUTH=true`
  - Use HTTPS with reverse proxy (nginx, Caddy)
  - Set strong `FLASK_SECRET_KEY`
  - Consider VPN or firewall rules

## Troubleshooting

### Server won't start
- Check port 5000 isn't in use: `netstat -an | grep 5000`
- Check Python path in systemd service
- Check logs: `journalctl -u py_home -f`

### Endpoints return 404
- Verify routes are registered: Check startup logs
- Verify URL path is correct (case-sensitive)

### Automations don't run
- Check automation scripts have execute permission
- Check logs for script errors
- Test scripts manually: `python automations/leaving_home.py`

## Architecture

```
iOS Shortcut → HTTP POST → Flask Server → Automation Script → Components → Devices
                                ↓
                          Background Process
                                ↓
                          Notification Sent
```

The server runs automation scripts in the background and returns immediately, so iOS Shortcuts don't timeout.

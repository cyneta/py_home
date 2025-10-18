# Notification Setup Guide

py_home sends alerts to your phone for important events like pipe freeze risk, sensor offline, battery low, etc.

## Quick Start: ntfy (Free, Recommended to Start)

**1. Install ntfy app:**
- iOS: https://apps.apple.com/app/ntfy/id1625396347
- Android: https://play.google.com/store/apps/details?id=io.heckel.ntfy

**2. Subscribe to your topic:**
- Open the app
- Tap "+" to add a subscription
- Enter your topic name: `py_home_matt_wheeler` (or whatever you set in config.yaml)
- That's it!

**3. Test it:**
```bash
python -c "from lib.notifications import send_normal; send_normal('Test from py_home', 'Test Alert')"
```

You should get a notification on your phone within seconds.

**No signup, no API keys, no credit card needed.**

---

## Alternative: Pushover (Paid, More Features)

**Cost:** $5 one-time purchase (not subscription)

**Why upgrade to Pushover?**
- ✅ Emergency alerts repeat every 5 minutes until acknowledged
- ✅ High priority bypasses Do Not Disturb mode
- ✅ More reliable delivery
- ✅ Better iOS/Android integration
- ✅ Custom sounds and vibration patterns
- ✅ Delivery receipts

**Setup:**
1. Go to https://pushover.net/ and create account
2. Buy Pushover app ($5 one-time on iOS/Android)
3. Get your **User Key** from dashboard
4. Create a new **Application** to get an **API Token**
5. Add to `config/.env`:
   ```bash
   PUSHOVER_TOKEN=your_api_token_here
   PUSHOVER_USER=your_user_key_here
   ```
6. Change `config/config.yaml`:
   ```yaml
   notifications:
     service: "pushover"
   ```

---

## Priority Levels

Both services support different priority levels:

| Function | Priority | Use Case | Pushover | ntfy |
|----------|----------|----------|----------|------|
| `send_low()` | -1 | Daily summaries, info | No sound | Min priority |
| `send_normal()` | 0 | Warnings, status updates | Normal | Default |
| `send_high()` | 1 | Urgent alerts | Bypasses DND | High priority |
| `send_emergency()` | 2 | Critical failures | Repeats every 5min | Max priority (no repeat) |

**Examples:**
```python
from lib.notifications import send_normal, send_high, send_emergency

# Normal notification
send_normal("Sensor battery at 15%")

# High priority (bypasses quiet hours on Pushover)
send_high("🚨 Pipe freeze risk! Crawlspace: 48°F")

# Emergency (Pushover only - repeats until acknowledged)
send_emergency("CRITICAL: Water detected in basement!")
```

---

## Notification Philosophy

**py_home sends alerts for emergencies and errors only** - not for routine events.

**Quick summary:**
- ✅ **Send notifications for:** Emergency conditions (pipe freeze, high humidity), equipment failures (sensor offline, battery low), automation errors
- ❌ **Don't send for:** Routine arrivals/departures, scheduled tasks completing normally, status updates, debug info

**Why?** You already know when routine events happen. Notifications should signal exceptional conditions requiring attention.

For complete philosophy, implementation patterns, and code examples, see [design/principles/notifications.md](../design/principles/notifications.md)

---

## Switching Between Services

Just change `config.yaml`:
```yaml
notifications:
  service: "ntfy"  # or "pushover"
```

No code changes needed - everything automatically uses the configured service.

---

## Troubleshooting

### ntfy: Not receiving notifications
1. Check app is installed and subscription is active
2. Verify topic name matches config.yaml
3. Test with curl:
   ```bash
   curl -d "Test from command line" ntfy.sh/py_home_matt_wheeler
   ```

### Pushover: "Credentials not configured"
1. Check `.env` file has both PUSHOVER_TOKEN and PUSHOVER_USER
2. Make sure values are actual tokens, not placeholders
3. Verify config.yaml has `service: "pushover"`

### No notifications at all
1. Check logs for "notification sent" messages
2. Verify internet connection on server
3. Test with simple Python command:
   ```python
   from lib.notifications import send_normal
   result = send_normal("Test")
   print(f"Success: {result}")
   ```

---

## Privacy & Security

**ntfy:**
- Messages sent through ntfy.sh servers (open source)
- Anyone who knows your topic name can send you notifications
- Use a unique, hard-to-guess topic name
- No personal data stored (messages not logged)

**Pushover:**
- Messages sent through Pushover's servers (proprietary)
- Requires API token (secure)
- More private (only you can send to your account)

Both are fine for home automation alerts. If you're paranoid about privacy, you can self-host ntfy.

---

## Recommendation

**Start with ntfy (free)** - It's perfectly adequate for home automation alerts. You don't need repeating emergency notifications for things like "battery low" or even "pipe freeze risk" - if you check your phone within an hour, you'll be fine.

**Upgrade to Pushover later** if you want the extra features (emergency repeating, better DND bypass, etc.). The $5 is worth it if you find yourself missing critical alerts, but try ntfy first.

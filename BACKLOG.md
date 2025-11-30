# Backlog

## Ready to Deploy (User Action Required)

- [ ] **Pi: Install systemd service** - `sudo cp server/py_home.service /etc/systemd/system/`
- [ ] **Pi: Set up cron jobs** - See `dev/setup/DEPLOYMENT.md` for copy/paste block
- [ ] **iOS: Create manual shortcuts** - See `docs/IOS_SHORTCUTS_GUIDE.md`
- [ ] **iOS: Create geofencing automations** - See `docs/IOS_SHORTCUTS_GEOFENCING.md`

## Planned Features

- [ ] **Roborock vacuum integration** - Config placeholder exists, needs component implementation
- [ ] **Apple Music voice control** - Design complete in `dev/`, ready to implement

## Future Enhancements (Optional)

- [ ] Weekly battery report for TempStick sensor
- [ ] System health monitor (disk space, memory alerts)
- [ ] Quiet hours support (10pm-7am notification suppression)
- [ ] Notification aggregation (combine multiple issues into single alert)

## Known Issues

- [ ] `automations/tempstick_monitor.py:313` - Investigate exceptions when sensor is operational

## Voice Tasks

Tasks added via voice command appear below:

- [ ] Test task (added 2025-10-17 10:32)
- [ ] Test task (added 2025-10-17 10:43)

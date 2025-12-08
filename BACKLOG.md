Test Fixes
- fix set_temperature import error in components.nest - cannot import name 'set_temperature'
- fix network presence method signature - is_device_home() got unexpected keyword argument 'method'
- remove or fix presence_monitor automation reference - module not found
- refresh Nest API token - 400 Bad Request on token refresh

Next
- configure homebridge plugins (see dev/designs/homebridge-setup.md) - allows siri control of some devices

Light control
- look in new IKEA tech for light control

Temperature Control
- analyze temperature data after 1 week of logging
- re-enable weather-aware boost with optimized logic

Reliability
- review ntfy alert configuration

Future Integrations
- alen air purifier (test Tuya API, verify device IDs)
- checkvist shortcuts (API config exists)
- grow light automation (scheduler hook needed)
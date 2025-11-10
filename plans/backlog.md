Top of Mind
- implement temperature data logger (specs and plans complete in specs/, plans/, dev/designs/)
- review the boost for cold outdoor conditions

Reliability
- investigate TempStick API rate limiting (still hitting "too many requests" even at 15-min intervals)
- investigate TempStick monitor false alarm exceptions (sensor works, but monitor logs exceptions)
- review ntfy alerts

Deployment
- push commits to GitHub (git push blocked by permissions)
- pull latest changes on Pi to get config validation fix

Advanced Integrations
- checkvist (API config exists, needs shortcuts)
- alen air purifier integration (test Tuya API, verify device IDs)
- roborock vacuum integration (check availability, test API)
- grow light automation (config exists, needs scheduler hook)
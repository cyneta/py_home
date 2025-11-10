Deployment
- push commits to GitHub (2 commits waiting: config fix + data logger)

Temperature Control
- analyze temperature data after 1 week of logging
- re-enable weather-aware boost with optimized logic based on data analysis

Reliability
- investigate TempStick API rate limiting (hitting limits at 15-min intervals)
- investigate TempStick monitor exceptions (sensor works but logs errors)
- review ntfy alert configuration

Future Integrations
- alen air purifier (test Tuya API, verify device IDs, log air quality data)
- checkvist (API config exists, needs shortcuts)
- roborock vacuum (check availability, test API)
- grow light automation (config exists, needs scheduler hook)
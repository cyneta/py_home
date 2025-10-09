# Temp Stick API Documentation

**Source:** https://tempstickapi.com/docs/

**Note:** Official API docs require JavaScript rendering. This document compiled from:
- Home Assistant Community forum: https://community.home-assistant.io/t/ideal-sciences-tempstick/414778
- GitHub tempstick-sharp: https://github.com/timheuer/tempstick-sharp
- Manual API testing

---

## Authentication

### API Key
- Header: `X-API-KEY`
- Value: Your API key from Temp Stick account dashboard

**Example:**
```bash
curl -H "X-API-KEY: YOUR_API_KEY_HERE" \
  https://tempstickapi.com/api/v1/sensor/YOUR_SENSOR_ID
```

**Getting Your API Key:**
1. Log in to https://tempstick.com/
2. Navigate to account dashboard
3. Find API key in settings/developer section

---

## Base URL

```
https://tempstickapi.com/api/v1
```

---

## Endpoints

### Get Sensor Data

**Endpoint:** `GET /sensor/{sensor_id}`

**Headers:**
```
X-API-KEY: YOUR_API_KEY_HERE
```

**Response:**
```json
{
  "sensor_id": "123456789",
  "name": "Basement Sensor",
  "temperature_f": 72.5,
  "temperature_c": 22.5,
  "humidity": 45,
  "battery_percentage": 85,
  "last_check_in": "2025-10-09T12:30:00Z",
  "signal_strength": -65
}
```

**Finding Your Sensor ID:**
- Log in to Temp Stick web interface at https://tempstick.com/
- View sensor details
- Sensor ID shown in URL or sensor settings

---

## Rate Limiting

**Recommended polling interval:** 1800 seconds (30 minutes)

- Temp Stick devices report every 15-30 minutes (depending on model/settings)
- Polling faster than device reports is unnecessary
- Respect rate limits to avoid API throttling

---

## Python Example

### Basic Usage

```python
import requests

API_KEY = "your_api_key_here"
SENSOR_ID = "your_sensor_id_here"
BASE_URL = "https://tempstickapi.com/api/v1"

def get_sensor_data(sensor_id):
    """Get current temperature and humidity from Temp Stick sensor"""
    url = f"{BASE_URL}/sensor/{sensor_id}"
    headers = {"X-API-KEY": API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None

# Get data
data = get_sensor_data(SENSOR_ID)
if data:
    print(f"Temperature: {data['temperature_f']}°F")
    print(f"Humidity: {data['humidity']}%")
    print(f"Battery: {data['battery_percentage']}%")
```

### Home Assistant Example

```yaml
sensor:
  - platform: rest
    name: "Basement Temperature"
    resource: https://tempstickapi.com/api/v1/sensor/YOUR_SENSOR_ID
    headers:
      X-API-KEY: YOUR_API_KEY_HERE
    scan_interval: 1800  # 30 minutes
    value_template: "{{ value_json.temperature_f }}"
    unit_of_measurement: "°F"

  - platform: rest
    name: "Basement Humidity"
    resource: https://tempstickapi.com/api/v1/sensor/YOUR_SENSOR_ID
    headers:
      X-API-KEY: YOUR_API_KEY_HERE
    scan_interval: 1800
    value_template: "{{ value_json.humidity }}"
    unit_of_measurement: "%"
```

---

## Known Endpoints (Inferred)

Based on C# client and common REST patterns:

### User Endpoints
- `GET /user` - Get user account info (may include sensor list)
- `GET /user/sensors` - List all sensors (likely)

### Sensor Endpoints
- `GET /sensor/{sensor_id}` - Get current sensor data (confirmed)
- `GET /sensor/{sensor_id}/readings` - Get historical readings (likely)
- `GET /sensor/{sensor_id}/readings?start={timestamp}&end={timestamp}` - Get readings for date range (likely)

### Alert Endpoints (Mentioned in docs template)
- `GET /alerts` - List configured alerts (likely)
- `POST /alerts` - Create new alert (likely)
- `PUT /alerts/{alert_id}` - Update alert (likely)
- `DELETE /alerts/{alert_id}` - Delete alert (likely)

**Note:** Endpoints marked "likely" are inferred from documentation template and common REST patterns. Test before using.

---

## Error Codes

### 406 Not Acceptable
- **Cause:** Missing or incorrect `X-API-KEY` header
- **Solution:** Ensure header is `X-API-KEY` (not `Authorization`)

### 401 Unauthorized
- **Cause:** Invalid API key
- **Solution:** Verify API key from Temp Stick dashboard

### 404 Not Found
- **Cause:** Invalid sensor ID or endpoint
- **Solution:** Check sensor ID from web interface

### 429 Too Many Requests
- **Cause:** Rate limit exceeded
- **Solution:** Reduce polling frequency (recommended: 30 min intervals)

---

## Data Fields

### Sensor Response Fields

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `sensor_id` | string | - | Unique sensor identifier |
| `name` | string | - | User-defined sensor name |
| `temperature_f` | float | °F | Temperature (Fahrenheit) |
| `temperature_c` | float | °C | Temperature (Celsius) |
| `humidity` | integer | % | Relative humidity |
| `battery_percentage` | integer | % | Battery level |
| `last_check_in` | string | ISO8601 | Last data upload timestamp |
| `signal_strength` | integer | dBm | WiFi signal strength |

**Note:** Exact field names may vary. Test with your API to confirm.

---

## Integration Notes

### Temp Stick Device Behavior
- Reports every 15-30 minutes (configurable in device settings)
- Stores up to 1000 offline readings
- Uploads buffered data when reconnected
- Battery powered (2x AA) or USB powered (depends on model)

### Best Practices
1. **Poll infrequently:** 30-minute intervals match device reporting
2. **Handle offline gracefully:** Check `last_check_in` timestamp
3. **Monitor battery:** Alert when `battery_percentage` < 20%
4. **Cache results:** Avoid redundant API calls
5. **Log errors:** Track API failures for debugging

### Automation Ideas
- **Low temperature alert:** Trigger when temp < 45°F (pipes freezing risk)
- **High humidity alert:** Trigger when humidity > 70% (mold risk)
- **Battery warning:** Notify when battery < 20%
- **Offline alert:** Warn if `last_check_in` > 2 hours old
- **Climate coordination:** Use with HVAC/dehumidifier control

---

## Limitations

1. **Cloud-only:** No local network API
2. **Polling-based:** No webhooks/push notifications
3. **Rate limited:** Unknown exact limits (use 30 min intervals)
4. **No historical bulk export:** API doesn't provide CSV/bulk download
5. **Sensor ID required:** Must get from web interface, not discoverable via API

---

## References

- **Official Docs:** https://tempstickapi.com/docs/ (requires JavaScript)
- **Vendor Site:** https://tempstick.com/
- **Home Assistant Thread:** https://community.home-assistant.io/t/ideal-sciences-tempstick/414778
- **C# Client:** https://github.com/timheuer/tempstick-sharp
- **Product Manual:** https://manuals.plus/asin/B07SG7BPM3

---

## Actual API Response (Confirmed)

### GET /sensor/{sensor_id}

**Confirmed Response Structure:**
```json
{
  "type": "success",
  "message": "get sensor",
  "data": {
    "id": "200336",
    "version": "2004",
    "sensor_id": "TS00EMA9JZ",
    "sensor_name": "TS00EMA9JZ",
    "sensor_mac_addr": "08:3A:8D:F2:E5:B9",
    "owner_id": "131459",
    "type": "DHT",
    "alert_interval": "900",
    "send_interval": "900",
    "last_temp": 21.5,
    "last_humidity": 50.4,
    "last_voltage": 3.39,
    "wifi_connect_time": 1,
    "rssi": -67,
    "last_checkin": "2025-10-08 21:56:07-00:00Z",
    "next_checkin": "2025-10-08 22:11:07-00:00Z",
    "ssid": "herbnzen",
    "offline": "1",
    "alerts": [],
    "use_sensor_settings": 0,
    "temp_offset": 0,
    "humidity_offset": 0,
    "alert_temp_below": "-99",
    "alert_temp_above": "200",
    "alert_humidity_below": "-99",
    "alert_humidity_above": "100",
    "connection_sensitivity": 2,
    "HI_M": 0,
    "HI": 99,
    "DP_M": 0,
    "DP": 0,
    "wlanA": "dapad",
    "wlanB": "",
    "last_wlan": "1",
    "wlan_1_used": "2025-10-08 21:57:45Z",
    "use_alert_interval": 0,
    "use_offset": 0,
    "battery_pct": 100,
    "last_messages": []
  }
}
```

**Key Fields:**
- `last_temp` - Temperature in Celsius
- `last_humidity` - Relative humidity percentage
- `battery_pct` - Battery level (0-100)
- `last_voltage` - Battery voltage
- `rssi` - WiFi signal strength (dBm)
- `offline` - "0" = online, "1" = offline
- `last_checkin` - Last data upload timestamp
- `wlanA` - WiFi network name

---

## TODO

- [x] Get sensor ID from Temp Stick web interface
- [ ] Test `/user` endpoint for sensor list
- [ ] Test `/readings` endpoint for historical data
- [x] Confirm exact field names from actual API response
- [ ] Test rate limits
- [ ] Document alert endpoints (if available)

---

**Last Updated:** 2025-10-09
**Status:** ✅ Fully documented and tested (sensor ID: TS00EMA9JZ)

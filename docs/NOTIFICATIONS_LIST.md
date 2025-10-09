# All py_home Notifications

Complete list of all notifications sent by the system.

## Temperature/Humidity Monitoring (tempstick_monitor.py)

**Schedule:** Every 30 minutes via cron

| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔴 HIGH | Temp < 50°F | 🚨 PIPE FREEZE RISK!<br>Location: Crawlspace<br>Temperature: 48.0°F (< 50.0°F)<br>Action: Check immediately! | 🚨 Crawlspace: 48°F - FREEZE RISK |
| ⚠️ NORMAL | Temp < 55°F | ⚠️ Cold Temperature Warning<br>Location: Crawlspace<br>Temperature: 52.0°F<br>Not critical yet, but monitor closely. | ⚠️ Crawlspace: 52°F - Cold |
| 🔴 HIGH | Humidity > 70% | 🚨 VERY HIGH HUMIDITY!<br>Location: Crawlspace<br>Humidity: 75.0% (> 70.0%)<br>Possible leak or flood!<br>Check for water intrusion. | 🚨 Crawlspace: 75% humidity - LEAK RISK |
| ⚠️ NORMAL | Humidity > 65% | ⚠️ High Humidity Warning<br>Location: Crawlspace<br>Humidity: 68.0%<br>Mold risk if sustained.<br>Consider running dehumidifier. | ⚠️ Crawlspace: 68% humidity - High |
| ⚠️ NORMAL | Sensor offline | ⚠️ Temp Stick Sensor Issues<br>Location: Crawlspace<br>- Sensor offline (last seen: 2025-10-09 14:04:08+00:00) | ⚠️ Temp Stick offline (Crawlspace) |
| ⚠️ NORMAL | Battery < 20% | ⚠️ Temp Stick Sensor Issues<br>Location: Crawlspace<br>- Low battery: 15% | ⚠️ Temp Stick battery: 15% |
| ⚠️ NORMAL | Monitor error | ❌ Temp Stick Monitor Error<br>Failed to check sensor<br>Error: Connection timeout | ❌ Temp Stick error: Connection timeout |

---

## Home Automation Scenes

### Leaving Home (leaving_home.py)
| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔴 HIGH | With errors | House set to away mode (with 2 errors) | 🏠 Away mode (2 errors) |
| ⚠️ NORMAL | Success | House secured - Away mode activated | 🏠 Away mode activated |

### Goodnight (goodnight.py)
| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔴 HIGH | With errors | Sleep mode activated (with 1 errors) | 😴 Goodnight (1 error) |
| ⚠️ NORMAL | Success | Goodnight - Sleep mode activated | 😴 Goodnight |

### Welcome Home (im_home.py)
| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔵 LOW | With errors | Welcome home (with 1 errors) | 🏡 Welcome (1 error) |
| 🔵 LOW | Success | Welcome home! House is ready. | 🏡 Welcome home |

### Good Morning (good_morning.py)
| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| ⚠️ NORMAL | Daily 7am | Good morning! It's 45°F and cloudy. High: 62°F | ☀️ 45°F, cloudy. High: 62° |

---

## Presence Detection (presence_monitor.py)

**Schedule:** Every 5 minutes via cron (WiFi detection)

| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔵 LOW | Arrived (WiFi) | Welcome home! (detected via WiFi) | 🏡 Home (WiFi) |
| 🔵 LOW | Left (WiFi) | House set to away mode (detected via WiFi) | 🚗 Left (WiFi) |

---

## Air Quality Monitoring (air_quality_monitor.py)

**Schedule:** Every 30 minutes via cron

| Priority | Trigger | Message |
|----------|---------|---------|
| 🔴 HIGH | PM2.5 > 100 | 🔴 Air unhealthy: PM2.5 150 (Bedroom) |
| ⚠️ NORMAL | PM2.5 > 50 | ⚠️ Air moderate: PM2.5 55 (Living Room) |
| ⚠️ NORMAL | Device offline | ⚠️ Air purifier offline (Bedroom) |

---

## Traffic Alerts (traffic_alert.py)

**Schedule:** On-demand or scheduled before commute

| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔴 HIGH | Construction/Heavy | Construction on I-84 E. Add 25 minutes to your commute. | ⚠️ I-84: +25min (construction) |
| ⚠️ NORMAL | Moderate delays | Moderate traffic on I-84 E. Expect 10-15 minute delays. | 🟡 I-84: +10-15min |

---

## Task Management (task_router.py)

**Trigger:** Voice command via iOS Shortcut

| Priority | Trigger | Current Message | Concise Version |
|----------|---------|-----------------|-----------------|
| 🔵 LOW | Task added | Task added: Buy milk | ✓ Added: Buy milk |

---

## Priority Legend

| Symbol | Priority | Behavior | Use Case |
|--------|----------|----------|----------|
| 🔵 LOW | -1 | No sound/vibration | Info, arrivals, tasks |
| ⚠️ NORMAL | 0 | Normal notification | Warnings, status |
| 🔴 HIGH | 1 | Bypasses quiet hours (Pushover) | Urgent alerts |
| 🚨 EMERGENCY | 2 | Repeats every 5min (Pushover only) | Not currently used |

---

## Summary Statistics

**Total Notification Types:** 22 (was 21, removed 2 AC notifications, added 3 air quality)

**By Priority:**
- 🔵 LOW: 5 notifications (23%)
- ⚠️ NORMAL: 12 notifications (55%)
- 🔴 HIGH: 5 notifications (23%)
- 🚨 EMERGENCY: 0 notifications (0%)

**By Category:**
- Temperature/Humidity: 7 notifications
- Air Quality: 3 notifications (NEW)
- Home Automation: 8 notifications
- Presence Detection: 2 notifications
- Traffic: 2 notifications
- Tasks: 1 notification

**Most Common:** Home automation scenes (8 types), Temperature/humidity monitoring (7 types)

---

## Recommendations

### Make Messages Concise
All messages currently use multi-line format. Suggested concise alternatives shown in "Concise Version" column.

**Benefits:**
- Easier to read on phone
- Less screen space
- Quicker to understand at a glance
- Better for Apple Watch/notification center

**Trade-offs:**
- Less detail (but you can tap for more info)
- Less helpful for debugging

### Future Enhancements
1. **Rate limiting** - Don't send same alert multiple times per hour
2. **Daily summaries** - Email with all sensor readings
3. **Alert aggregation** - Combine multiple issues into one notification
4. **Quiet hours** - No non-urgent alerts 10pm-7am (Pushover supports this)

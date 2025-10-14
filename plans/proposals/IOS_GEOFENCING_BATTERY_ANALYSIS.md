# iOS Geofencing Battery Analysis

**Q: Does using "Get Current Location" in iOS Shortcuts suck battery?**

## Short Answer

**NO** - Your current setup is battery-efficient because:
1. iOS geofencing is event-driven (triggers only on boundary crossings)
2. "Get Current Location" only runs **when geofence is crossed** (2-3 times per trip)
3. Not continuous location tracking

**Estimated battery impact: 1-3% per day**

---

## Your Current Setup

### What you have:
```
Automation: "When I leave [Work]"
Trigger: Geographic region (geofence)
Action: Get Current Location → Send to Pi
```

### How it works:
1. **iOS monitors geofence passively** (very efficient, uses cell towers + WiFi)
2. **When boundary crossed** → iOS wakes up Shortcuts app
3. **GPS activates for ~2-5 seconds** → Gets precise location
4. **Sends HTTP POST to Pi** → Goes back to sleep

**Total GPS activations per day:**
- Leave work: 1x
- Near home (1km): 1x
- (Optional) Arriving home: 1x
- **Total: 2-3 GPS fixes per day** (not continuous!)

---

## Battery Impact Breakdown

### What DOES drain battery:
❌ **Continuous location tracking** (navigation apps, fitness trackers)
  - GPS on constantly
  - Drains 10-20% per hour

❌ **Background app refresh with location**
  - Apps polling location every N minutes
  - Drains 5-10% per day

### What DOES NOT drain much:
✅ **Geofencing** (what you're using)
  - Cell tower + WiFi triangulation (passive)
  - GPS only activates when crossing boundary
  - Drains 1-3% per day

✅ **"Get Current Location" in Shortcuts**
  - Only runs when automation triggers
  - Single GPS fix (2-5 seconds)
  - Negligible impact (<0.1% per fix)

---

## iOS Location Accuracy Modes

Your Shortcuts use **"Best" location accuracy**. Here's what that means:

### "Best" (Highest Accuracy)
- Uses: GPS + WiFi + Cell towers
- Accuracy: ±5-10 meters
- Battery: Moderate (only during fix)
- **Your usage:** 2-3 fixes/day = minimal impact

### "Hundred Meters" (Lower Accuracy)
- Uses: WiFi + Cell towers only (no GPS)
- Accuracy: ±100 meters
- Battery: Low
- **Trade-off:** Not accurate enough for geofencing decisions

### "Kilometer" (Lowest Accuracy)
- Uses: Cell towers only
- Accuracy: ±1000 meters
- Battery: Very low
- **Trade-off:** Too inaccurate, would cause false triggers

---

## Recommendation

**Keep using "Best" accuracy** because:

1. **Already efficient:** Only 2-3 GPS fixes per day
2. **Accurate decisions:** Knows if you're 5km vs 1km vs 200m from home
3. **Prevents false triggers:** If you use lower accuracy, system might think you're home when you're at neighbor's house

**If you want to reduce battery further:**
- Remove "arriving_home" geofence (redundant with WiFi detection)
- This saves 1 GPS fix per trip
- **Impact:** ~0.5% less battery drain per day

---

## Monitoring Battery Impact

### Check location battery usage:
1. **Settings** → **Battery**
2. Scroll down to app list
3. Look for **"Shortcuts"** app
4. Tap for breakdown (Onscreen vs Background)

**Normal:** 1-3% total usage per day
**High:** >5% per day (investigate)

### If battery drain is high:
1. Check for "stuck" GPS (iPhone gets warm)
2. Restart iPhone
3. Check for other location apps running continuously

---

## Comparison: Your Setup vs Continuous Tracking

| Method | GPS Active Time | Battery/Day | Use Case |
|--------|----------------|-------------|----------|
| **Your geofencing** | ~10 sec/day | 1-3% | Smart home triggers |
| Find My (passive) | <1 min/day | 1-2% | Device tracking |
| Navigation (active) | Hours | 20-30% | Driving directions |
| Fitness tracking | 30-60 min | 8-15% | Running/cycling |

**Conclusion:** Your setup is in the "very efficient" category.

---

## Summary

✅ **Your current setup is fine** - "Best" accuracy with geofencing is battery-efficient
✅ **2-3 GPS fixes per day** is negligible impact (~1-3% battery)
✅ **Do NOT change to lower accuracy** - would cause false triggers
❌ **Avoid continuous location tracking** - that's what drains battery

**Answer to Q5: NO, it does NOT suck battery** - you're using geofencing correctly!

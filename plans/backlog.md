# Backlog

Quick-scan task list for py_home. Pick what to work on next based on impact, effort, and current priorities.

---

## 🎯 Ready to Work

Quick wins and high-value tasks ready to start.

| Task | Impact | Effort | Notes |
|------|--------|--------|-------|
| **Fix 71 Pytest Warnings** | Low | 1-2h | Replace `return True` with `assert True` in tests |
| **Grow Light Automation** | Medium | 1-2h | Config exists, needs time-based scheduler hook |
| **Make Bedroom Heater Settable** | Low | 1h | Currently only on/off, add temp control if possible |

---

## 🔨 Needs Planning

Larger tasks that need design/research before implementation.

| Task | Complexity | Blocker | Next Step |
|------|------------|---------|-----------|
| **HomePod Environment Sensors** | Medium | No direct API | Create webhook endpoint, HomeKit automation setup |
| **Alen Air Purifier Integration** | Medium | Partial config exists | Test Tuya API, verify device IDs work |
| **Roborock Vacuum Integration** | Medium | Hardware needed? | Check if vacuum is available, test API |
| **Backup System for Pi** | Medium | Need strategy | Design: rsync? git backup? cloud? |
| **Audit Dry-Run Test System** | Medium | None | Review test patterns, verify isolation |

---

## 💡 Feature Ideas

Nice-to-have features, low priority.

| Task | Value | Complexity | Notes |
|------|-------|------------|-------|
| **YouTube Music Integration** | Low | Medium | iOS shortcuts for playlists/control |
| **Checkvist Integration** | Low | Low | Already has API config, needs shortcuts |
| **HomePod Siri Shortcuts** | Low | Medium | Voice control for HomePod speakers |
| **Extract Design Principles** | Medium | Low | Document patterns (already doing organically) |

---

---

## ✅ Recently Completed

Last 5 completed items for context.

- **Config Schema Auto-Sync System** (2025-10-18)
  - Auto-detects config.yaml changes after git pull
  - Merges new keys, removes obsolete, preserves overrides
  - Git hook + installer + comprehensive docs

- **Notification Philosophy Cleanup** (2025-10-18)
  - Established "emergency-only" notification principle
  - Removed duplicate docs, single source in design/principles/

- **Weather-Aware Temperature Settings** (Recent)
  - Configurable cold/hot thresholds and targets
  - Morning temperature adjusts based on outdoor weather

- **Component Timeout Pattern** (Recent)
  - 4.6x dashboard speedup (5sec vs 20-25sec)
  - Parallel Tapo queries, configurable timeouts

- **100% Test Pass Rate** (Recent)
  - 225 tests passing, 0 skipped
  - Fixed isolation issues

---

## 📊 View by Category

### Hardware/Devices
- Review Tapo Outlet Config (ready)
- HomePod Environment Sensors (needs planning)
- Alen Air Purifier Integration (needs planning)
- Roborock Vacuum Integration (needs planning)
- Grow Light Automation (ready)
- Make Bedroom Heater Settable (ready)

### Code Quality
- Fix 71 Pytest Warnings (ready)
- Audit Dry-Run Test System (needs planning)
- Extract Design Principles (feature idea)

### System/Ops
- Backup System for Pi (needs planning)

### Integrations
- YouTube Music (feature idea)
- Checkvist (feature idea)
- HomePod Shortcuts (feature idea)

---

## 🎲 Picking What to Do Next

**Quick win (< 2 hours)?**
→ Fix pytest warnings, review Tapo config, or grow light automation

**Want to add new hardware?**
→ Check if Alen/Roborock are accessible, then plan integration

**Improve system reliability?**
→ Design Pi backup system or audit dry-run tests

**Low energy, easy task?**
→ Extract design principles (document existing patterns)

**Want to learn something new?**
→ Checkvist or YouTube Music API integration

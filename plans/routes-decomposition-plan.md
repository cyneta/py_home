# Server Routes Decomposition Plan

**Goal**: Decompose server/routes.py (2,041 lines) into maintainable modules

**Problem**: 66% of the file is embedded HTML (1,340 lines), making maintenance difficult

## Phase 1: Extract HTML to Templates (~1,340 lines removed)

### Tasks:
1. Create server/templates/ directory
2. Extract dashboard HTML to templates/dashboard.html (lines 490-1334, ~844 lines)
3. Extract logs UI HTML to templates/logs.html (lines 1630-1920, ~490 lines)
4. Update routes.py to use render_template() for dashboard
5. Update routes.py to use render_template() for logs
6. Test /dashboard and /logs URLs work correctly

**Expected reduction**: 2,041 → ~700 lines

---

## Phase 2: Extract Helper Functions (~50 lines)

### Tasks:
1. Create server/routes/ directory and __init__.py
2. Create helpers.py with:
   - `require_auth()` decorator
   - `run_automation_script()` function
3. Update routes.py imports to use helpers
4. Test that auth and automation scripts still work

**Expected reduction**: ~700 → ~650 lines

---

## Phase 3: Create Flask Blueprints (~600 lines → 7 modules)

### 3a. Device Status APIs Blueprint (server/routes/api_device.py)
- `/nest-status` (GET)
- `/sensibo-status` (GET)
- `/tapo-status` (GET)
- `/tempstick-status` (GET)

**Tasks**:
1. Create api_device.py blueprint with 4 device status endpoints
2. Register blueprint in routes.py
3. Test all 4 device status endpoints

---

### 3b. iOS Shortcut Webhooks Blueprint (server/routes/webhooks.py)
- `/pre-arrival` (POST)
- `/leaving-home` (POST)
- `/bedtime` (POST)
- `/wakeup` (POST)
- `/away` (POST)
- `/home` (POST)

**Tasks**:
1. Create webhooks.py blueprint with 6 iOS Shortcut endpoints
2. Register blueprint in routes.py
3. Test webhook endpoints work

---

### 3c. Location/Presence Blueprint (server/routes/location.py)
- `/ios-location` (POST)
- `/location-test` (GET)
- `/presence` (GET)

**Tasks**:
1. Create location.py blueprint with 3 location endpoints
2. Register blueprint in routes.py
3. Test location endpoints work

---

### 3d. Logs UI Blueprint (server/routes/logs.py)
- `/logs` (GET) - Log viewer UI
- `/logs/data` (GET) - Log data API
- `/logs/tail` (GET) - Log tail stream

**Tasks**:
1. Create logs.py blueprint with 3 log viewing endpoints
2. Register blueprint in routes.py
3. Test logs UI still works

---

### 3e. System Status APIs Blueprint (server/routes/api_system.py)
- `/status` (GET) - Full system status
- `/devices/status` (GET) - Device status summary
- `/location` (GET) - Current location
- `/weather` (GET) - Weather data

**Tasks**:
1. Create api_system.py blueprint with 4 system status endpoints
2. Register blueprint in routes.py
3. Test system status endpoints

---

### 3f. Admin APIs Blueprint (server/routes/api_admin.py)
- `/restart` (POST)
- `/deploy` (POST)
- `/logs/clear` (POST)

**Tasks**:
1. Create api_admin.py blueprint with 3 admin endpoints
2. Register blueprint in routes.py
3. Test admin endpoints exist

---

### 3g. AI Command Blueprint (server/routes/ai.py)
- `/ai/command` (POST) - AI-driven automation

**Tasks**:
1. Create ai.py blueprint with AI command endpoint
2. Register blueprint in routes.py
3. Test AI command endpoint

---

## Phase 4: Final Cleanup

### Tasks:
1. Verify main routes.py is now ~150 lines with clean structure
2. Update any documentation references to old structure
3. Run full test suite to ensure nothing broke

---

## Expected Final Structure

```
server/
├── __init__.py              # Flask app factory
├── routes.py                # Main routing (~150 lines)
├── templates/
│   ├── dashboard.html       # Dashboard UI
│   └── logs.html            # Logs UI
└── routes/
    ├── __init__.py
    ├── helpers.py           # Auth & utilities
    ├── api_device.py        # Device status APIs
    ├── api_system.py        # System status APIs
    ├── api_admin.py         # Admin APIs
    ├── webhooks.py          # iOS Shortcut hooks
    ├── location.py          # Location/presence
    ├── logs.py              # Logs UI & APIs
    └── ai.py                # AI commands
```

**Total Reduction**: 2,041 lines → ~150 lines (main routes) + organized modules

---

## Testing Strategy

After each phase:
1. Run pytest suite: `pytest tests/ -v`
2. Test key endpoints manually
3. Verify no regression in automation behavior

**Critical test cases**:
- Dashboard loads correctly
- iOS shortcuts trigger automations
- Location updates work
- Device status APIs respond
- Logs UI displays correctly

# Tesla API Status

**Date**: 2025-10-06
**Status**: Deferred / Research Needed

---

## Problem

Tesla has deprecated their unofficial API and is transitioning to a new Fleet API system that requires:
- Official registration as a developer
- Command signing for security
- More complex authentication flow
- May not support all older vehicles

**Old unofficial API** (used by TeslaPy, etc.):
- Being phased out
- Won't work on 2021+ vehicles with new command protocol
- Uncertain how long it will continue working

---

## Options

### 1. Tesla Fleet API (Official)
**Pros**: Official, future-proof
**Cons**: Complex setup, requires developer registration, command signing
**Status**: Need to research registration process

**Resources**:
- https://www.tesla.com/developer-docs
- https://github.com/fabianhu/tesla_api (2024 implementation)

### 2. Third-Party Proxy Services
**Teslemetry** (https://teslemetry.com):
- Paid service that handles Fleet API complexity
- Simple REST API for developers
- Pricing: TBD

**Tessie** (https://tessie.com):
- Similar proxy service
- Handles authentication and command signing

**Pros**: Easier integration
**Cons**: Ongoing cost, dependency on third party

### 3. TeslaPy (Old API)
**Library**: https://github.com/tdorssers/TeslaPy
**Pros**: Simple, well-documented
**Cons**: May stop working, doesn't support newer vehicles

---

## Decision

**For py_home Phase 0-2**: Skip Tesla integration entirely

**Focus instead on**:
- Nest thermostat
- Tapo smart outlets
- Sensibo AC
- Roborock vacuum
- Alen air purifiers
- Google Maps (travel time)
- Weather API

**Revisit Tesla in Phase 3+** after:
1. Testing core automations with other devices
2. Researching Fleet API registration
3. Evaluating Teslemetry/Tessie pricing
4. Determining if benefit justifies complexity/cost

---

## Affected Workflows

These planned workflows are deferred:

### High Priority (originally)
- ❌ "Warm up my car" voice command
- ❌ Smart workday pre-heat (weather-aware)
- ❌ Tesla presence detection (arrive/depart)
- ❌ Tesla charging automation

### Medium Priority
- ❌ Low battery alerts
- ❌ Sentry mode automation
- ❌ "Road trip mode" scene

### Lower Priority
- ❌ Calendar-aware pre-heat
- ❌ Solar-optimized charging
- ❌ Share ETA features

---

## Alternative Approaches

Without Tesla integration:

**"Leaving Home" scene**: Still works
- Set Nest to away
- Turn off outlets
- Start vacuum
- ~~Stop Tesla charging~~ (removed)
- ~~Enable sentry mode~~ (removed)

**Presence detection**: Use iPhone location instead
- iOS Shortcuts can trigger on location
- "When arriving home" → run webhook
- "When leaving home" → run webhook

**Travel time queries**: Still works via Google Maps
- No dependency on Tesla

---

## Next Steps (Phase 3+)

If/when Tesla integration is added:

1. **Research**:
   - [ ] Review Tesla Fleet API docs
   - [ ] Test registration process
   - [ ] Evaluate Teslemetry pricing
   - [ ] Check if TeslaPy still works

2. **Decide**:
   - Official Fleet API vs third-party service
   - Cost/benefit analysis
   - Required effort vs value

3. **Implement** (if approved):
   - [ ] `utils/tesla_api.py`
   - [ ] `scripts/tesla_preheat.py`
   - [ ] `scripts/tesla_presence.py`
   - [ ] Update webhook server endpoints

---

## Conclusion

Tesla integration is **nice to have** but not critical for core home automation.

The system will be valuable without it:
- Climate control (Nest + Sensibo)
- Lighting/outlets (Tapo)
- Cleaning (Roborock)
- Air quality (Alen)
- Travel planning (Google Maps)
- Task management

Tesla can be added later if the API situation improves.

# Documentation Organization Guide

Where to place new markdown files in py_home.

## Directory Structure

```
py_home/
├── *.md                    # Root-level docs (project overview only)
├── docs/                   # Technical documentation & user guides
├── plans/                  # Implementation plans & roadmaps
├── status/                 # Historical session summaries & milestones
├── reviews/                # Audits & analysis documents
├── dev/                    # Current session context only
├── components/*/           # Component-specific docs
└── server/                 # Server documentation
```

---

## Root Level (*.md)

**Purpose:** High-level project documentation visible on GitHub

**Place here:**
- ✓ README.md - Main project overview (always root)
- ✓ MIGRATION_PLAN.md - Overall migration roadmap
- ✓ MIGRATION_LOG.md - Migration progress tracking
- ✓ CLAUDE.md - Instructions for Claude Code
- ✓ REPOSITORY-INDEX.md - Multi-repo overview (if multi-project repo)

**Don't place here:**
- ✗ Session summaries (go in status/)
- ✗ Implementation plans (go in plans/)
- ✗ Audits/reviews (go in reviews/)
- ✗ Technical guides (go in docs/)
- ✗ Session context (go in dev/)

**Why root?**
- First thing people see on GitHub
- Quick project overview
- Installation/getting started
- High-level architecture

---

## docs/ (Technical Documentation)

**Purpose:** User-facing guides, references, and how-tos

**Place here:**
- ✓ Setup guides (NOTIFICATIONS.md, TAPO_GUIDE.md)
- ✓ API references (TEMPSTICK_API.md)
- ✓ Testing guides (CURL_TESTING_GUIDE.md)
- ✓ System documentation (LOGGING.md)
- ✓ Feature lists (NOTIFICATIONS_LIST.md)
- ✓ Analysis/decisions (NOTIFICATION_ANALYSIS.md)
- ✓ Status documents (TESLA_STATUS.md)

**Examples:**
```
docs/
├── NOTIFICATIONS.md          # How to set up notifications
├── NOTIFICATIONS_LIST.md     # All notification types
├── NOTIFICATION_ANALYSIS.md  # Coverage analysis
├── TEMPSTICK_API.md         # API reference
├── LOGGING.md               # Logging system guide
└── CURL_TESTING_GUIDE.md    # Testing with curl
```

**Naming Convention:**
- UPPERCASE_WITH_UNDERSCORES.md
- Descriptive names (not CODE_NAMES.md)
- Use full words (not abbreviations)

**When to use docs/:**
- User needs to reference it to USE the system
- Technical how-to or setup guide
- API reference or specification
- System-wide feature documentation

---

## plans/ (Implementation Plans)

**Purpose:** Planning documents for features, implementations, and roadmaps

**Place here:**
- ✓ Feature implementation plans (*_PLAN.md, *_IMPLEMENTATION.md)
- ✓ System design documents
- ✓ Architecture decisions
- ✓ Deployment plans
- ✓ Testing plans

**Examples:**
```
plans/
├── APPLE_MUSIC_PLAN.md           # Future feature plan
├── TUYA_IMPLEMENTATION_PLAN.md   # Implementation design
├── LOGGING_IMPLEMENTATION.md     # System design
├── PI_DEPLOYMENT_PLAN.md         # Deployment roadmap
└── TESTING_PLAN.md               # Testing strategy
```

**Naming Convention:**
- *_PLAN.md - Future feature plans
- *_IMPLEMENTATION.md - Design documents
- *_DEPLOYMENT.md - Deployment plans

**When to use plans/:**
- Planning future features (not yet implemented)
- Design decisions and architecture
- Deployment strategies
- Testing strategies
- "How we will build it"

---

## status/ (Historical Status & Sessions)

**Purpose:** Historical session summaries, milestones, and status snapshots

**Place here:**
- ✓ Session summaries (*_SUMMARY.md)
- ✓ Milestone markers (*_COMPLETE.md)
- ✓ Historical status reports
- ✓ Continuation prompts (for resuming sessions)
- ✓ Phase completion documents

**Examples:**
```
status/
├── SESSION_SUMMARY.md                 # Latest session work
├── FINAL_SESSION_SUMMARY.md           # Historical summary
├── PHASE1_COMPLETE.md                 # Milestone marker
├── STATUS_REPORT.md                   # Historical status
└── CONTINUATION_PROMPT.md             # Session resume context
```

**Naming Convention:**
- *_SUMMARY.md - Session summaries
- *_COMPLETE.md - Milestone completions
- *_STATUS.md or *_REPORT.md - Status snapshots
- CONTINUATION_PROMPT.md - Session context

**When to use status/:**
- Documenting what was accomplished in a session
- Marking project milestones
- Historical status snapshots
- Context for resuming work after a break
- "What we did" not "what we will do"

---

## reviews/ (Audits & Analysis)

**Purpose:** Audit documents, gap analyses, and review reports

**Place here:**
- ✓ Audit reports (*_AUDIT.md)
- ✓ Gap analyses (*_GAP_ANALYSIS.md)
- ✓ Code reviews
- ✓ System reviews
- ✓ Coverage analyses

**Examples:**
```
reviews/
├── TESTING_AUDIT.md              # Testing coverage audit
├── TESTING_GAP_ANALYSIS.md       # Testing gaps identified
├── PROJECT_CLEANUP_AUDIT.md      # Cleanup review
└── DEVICE_CONTROL_AUDIT.md       # Device control review
```

**Naming Convention:**
- *_AUDIT.md - Audit reports
- *_GAP_ANALYSIS.md - Gap analyses
- *_REVIEW.md - Review documents

**When to use reviews/:**
- Auditing test coverage
- Analyzing gaps/issues
- Reviewing code/architecture
- Identifying improvements needed
- "What we found" not "what we'll fix"

---

## dev/ (Current Session Context)

**Purpose:** Active development context for current session only

**Place here:**
- ✓ context.md - Current session working context
- ✓ Temporary test scripts (*.py)
- ✓ Work-in-progress notes

**Examples:**
```
dev/
├── context.md                    # Current session context
└── temp_test.py                  # Temporary script (delete when done)
```

**Naming Convention:**
- context.md - Session context (lowercase, special)
- temp_*.py - Temporary scripts (will be deleted)

**When to use dev/:**
- Current session working context
- Temporary/throwaway files that will be deleted
- Active work-in-progress notes

**Important:**
- DO NOT use for historical summaries (use status/)
- DO NOT use for plans (use plans/)
- DO NOT use for completed audits (use reviews/)
- Clean up temporary files when session ends

**Git Status:**
- Usually .gitignored
- Or committed if needed for collaboration
- Clean up before commits

---

## components/*/ (Component-Specific Docs)

**Purpose:** Documentation for individual device/service components

**Structure per component:**
```
components/tapo/
├── README.md    # Quick start (required)
├── GUIDE.md     # User guide (optional)
├── API.md       # API reference (optional)
├── client.py    # Implementation
├── demo.py      # Demo script
└── test.py      # Tests
```

**Place here:**
- ✓ Component quick start (README.md)
- ✓ Component user guide (GUIDE.md)
- ✓ Component API reference (API.md)
- ✓ Component-specific setup

**Examples:**
```
components/
├── tapo/
│   ├── README.md         # "How to use Tapo plugs"
│   ├── GUIDE.md          # "Complete Tapo guide"
│   └── API.md            # "TapoAPI class reference"
├── nest/
│   ├── README.md         # "How to use Nest"
│   └── GUIDE.md          # "Nest setup guide"
└── tempstick/
    └── README.md         # (if we make it a package)
```

**Naming Convention:**
- README.md - Always the entry point
- GUIDE.md - User guide
- API.md - API/class reference
- UPPERCASE for markdown docs

**When to use components/:**
- Documentation specific to ONE component
- Not system-wide features
- Users need to understand this specific device/service

---

## server/ (Server Documentation)

**Purpose:** Flask webhook server documentation

**Place here:**
- ✓ Server setup (README.md)
- ✓ Deployment guides
- ✓ Endpoint documentation
- ✓ Systemd service setup

**Examples:**
```
server/
├── README.md           # Server documentation
├── app.py              # Flask app
├── routes.py           # Endpoints
└── py_home.service     # Systemd service
```

**When to use server/:**
- Flask server setup
- Deployment instructions
- Endpoint documentation
- Only if it's server-specific (not general docs)

---

## Decision Tree: Where Should This File Go?

### Is it about the whole project overview?
- **Yes** → Root level (README.md, MIGRATION_PLAN.md, MIGRATION_LOG.md)
- **No** → Continue...

### Is it a session summary or milestone?
- **Yes** → status/ (*_SUMMARY.md, *_COMPLETE.md, STATUS_REPORT.md)
- **No** → Continue...

### Is it an audit or analysis?
- **Yes** → reviews/ (*_AUDIT.md, *_GAP_ANALYSIS.md, *_REVIEW.md)
- **No** → Continue...

### Is it a plan for future implementation?
- **Yes** → plans/ (*_PLAN.md, *_IMPLEMENTATION.md, *_DEPLOYMENT.md)
- **No** → Continue...

### Is it specific to ONE component/device?
- **Yes** → components/componentname/ (README.md, GUIDE.md, API.md)
- **No** → Continue...

### Is it about the Flask server?
- **Yes** → server/ (README.md)
- **No** → Continue...

### Is it user-facing documentation?
- **Yes** → docs/ (setup guides, API refs, system docs)
- **No** → Continue...

### Is it current session working context?
- **Yes** → dev/ (context.md only)
- **No** → Probably docs/

---

## Examples by Type

### Setup Guides → docs/
```
docs/NOTIFICATIONS.md        # How to set up notifications
docs/TAPO_GUIDE.md          # How to set up Tapo
docs/DEPLOYMENT_GUIDE.md     # How to deploy to Raspberry Pi
```

### API References → docs/ or components/*/
```
docs/TEMPSTICK_API.md       # System-wide service API
components/tapo/API.md      # Component-specific API
```

### Feature Lists → docs/
```
docs/NOTIFICATIONS_LIST.md  # All notification types
docs/AUTOMATIONS_LIST.md    # All automation scripts
```

### Planning Documents → plans/
```
plans/APPLE_MUSIC_PLAN.md            # Future feature
plans/TUYA_IMPLEMENTATION_PLAN.md    # Design doc
plans/PI_DEPLOYMENT_PLAN.md          # Deployment plan
```

### Session Summaries → status/
```
status/SESSION_SUMMARY.md            # Latest work
status/PHASE1_COMPLETE.md            # Milestone
status/STATUS_REPORT.md              # Historical status
```

### Audits & Reviews → reviews/
```
reviews/TESTING_AUDIT.md             # Test coverage audit
reviews/TESTING_GAP_ANALYSIS.md      # Gap analysis
reviews/PROJECT_CLEANUP_AUDIT.md     # Cleanup review
```

### Analysis Documents → docs/
```
docs/NOTIFICATION_ANALYSIS.md  # Feature analysis (user-facing)
docs/SYSTEM_DESIGN.md          # System documentation
```

### Component Docs → components/*/
```
components/tapo/README.md      # Quick start
components/tapo/GUIDE.md       # User guide
components/tapo/API.md         # API reference
```

### Migration/Progress → Root & status/
```
MIGRATION_PLAN.md              # Overall roadmap (root)
MIGRATION_LOG.md               # Progress tracking (root)
status/SESSION_SUMMARY.md      # Latest work (status/)
```

---

## Naming Conventions

### Markdown Files
- **Root & docs/**: UPPERCASE_WITH_UNDERSCORES.md
  - ✓ NOTIFICATIONS.md
  - ✓ TAPO_GUIDE.md
  - ✓ CURL_TESTING_GUIDE.md
  - ✗ notifications.md
  - ✗ NotificationsGuide.md

- **Special cases** (lowercase):
  - context.md (dev/ session context)

- **Component docs**: UPPERCASE
  - README.md (always)
  - GUIDE.md
  - API.md

### Suffixes
- *_GUIDE.md - Setup/user guides
- *_API.md - API references
- *_PLAN.md - Implementation plans
- *_IMPLEMENTATION.md - Design documents
- *_LIST.md - Lists/catalogs
- *_ANALYSIS.md - Analysis/decisions
- *_STATUS.md - Status/progress

---

## Migration Checklist

When you create a new markdown file, ask:

1. **Who is it for?**
   - Users → docs/
   - Developers → dev/
   - Component users → components/*/

2. **What is it about?**
   - Whole project → Root
   - One component → components/*/
   - System feature → docs/
   - Future plans → dev/

3. **When will it be used?**
   - During setup → docs/
   - During development → dev/
   - During daily use → Root or components/*/

4. **Is it temporary?**
   - Yes → dev/ (and .gitignore it)
   - No → Proper location above

---

## Common Mistakes

### ❌ Don't Do This:
```
py_home/
├── notification_setup.md       # Should be docs/NOTIFICATIONS.md
├── temp-stick-api.md          # Should be docs/TEMPSTICK_API.md
├── TODO.md                    # Should be dev/ or root MIGRATION_PLAN.md
└── docs/
    └── apple_music_plan.md    # Should be dev/APPLE_MUSIC_PLAN.md
```

### ✅ Do This Instead:
```
py_home/
├── README.md                   # Root overview
├── MIGRATION_PLAN.md          # Project roadmap
├── docs/
│   ├── NOTIFICATIONS.md       # Setup guide
│   └── TEMPSTICK_API.md       # API reference
└── dev/
    └── APPLE_MUSIC_PLAN.md    # Future feature plan
```

---

## Quick Reference

| Type | Location | Example |
|------|----------|---------|
| Project overview | Root | README.md |
| Migration tracking | Root | MIGRATION_PLAN.md |
| Setup guide | docs/ | NOTIFICATIONS.md |
| API reference | docs/ | TEMPSTICK_API.md |
| Feature list | docs/ | NOTIFICATIONS_LIST.md |
| Feature analysis | docs/ | NOTIFICATION_ANALYSIS.md |
| Implementation plans | plans/ | APPLE_MUSIC_PLAN.md |
| Design docs | plans/ | TUYA_IMPLEMENTATION.md |
| Deployment plans | plans/ | PI_DEPLOYMENT_PLAN.md |
| Session summaries | status/ | SESSION_SUMMARY.md |
| Milestones | status/ | PHASE1_COMPLETE.md |
| Audits | reviews/ | TESTING_AUDIT.md |
| Gap analyses | reviews/ | TESTING_GAP_ANALYSIS.md |
| Current session context | dev/ | context.md |
| Component guide | components/*/ | tapo/README.md |
| Server setup | server/ | README.md |

---

## When in Doubt

**Default locations:**
- User documentation → docs/
- Planning/design → plans/
- Historical summaries → status/
- Audits/reviews → reviews/
- Current session → dev/
- Component-specific → components/*/
- Project-wide overview → Root

**Ask yourself:**
- "Would a NEW user need this to get started?" → docs/
- "Is this planning for FUTURE work?" → plans/
- "Is this documenting PAST work?" → status/
- "Is this an audit or analysis?" → reviews/
- "Is this about ONE component only?" → components/*/
- "Is this the FIRST thing people should read?" → Root README.md
- "Is this temporary working context?" → dev/

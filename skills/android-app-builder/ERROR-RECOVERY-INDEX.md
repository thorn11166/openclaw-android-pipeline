# Error Recovery System - Navigation Guide

## 📚 Quick Navigation

### For Immediate Use (Start Here!)
1. **[QUICKSTART.md](scripts/QUICKSTART.md)** - Get running in 5 minutes
   - Copy-paste commands
   - Setup instructions
   - Common issues

### For Deep Understanding
2. **[ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md)** - Complete reference
   - Architecture and workflow
   - Script details
   - Configuration options
   - Troubleshooting

### For Overview
3. **[ENHANCEMENT-SUMMARY.md](ENHANCEMENT-SUMMARY.md)** - What was added
   - New components
   - Features and capabilities
   - Before/after comparison
   - Production readiness

### For Integration
4. **[SKILL.md](SKILL.md)** - Updated skill documentation
   - How error recovery fits in workflow
   - Phase 6: Automatic Error Recovery
   - Error classification and handling
   - Updated troubleshooting

---

## 📋 New Files Added

### Scripts (in `scripts/`)

#### **error-recovery.py** (Main Orchestrator)
- **Purpose:** Coordinates entire error recovery pipeline
- **Lines of Code:** 600+
- **Dependencies:** requests, subprocess, git
- **Input:** GitHub run ID, tokens
- **Output:** `.error-recovery.log`, `.error-recovery-history.json`
- **Key Features:**
  - State machine for error recovery
  - Git integration (commit, push, retrigger)
  - Discord escalation with full context
  - Retry loop (up to 3x)

**Usage:**
```bash
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 123456789 \
  --max-retries 3
```

---

#### **auto-fix.py** (Automated Fixer)
- **Purpose:** Generates and applies targeted fixes
- **Lines of Code:** 700+
- **Dependencies:** regex, pathlib, json, logging
- **Input:** Error report JSON from error-parser.py
- **Output:** Modified build files + fix report JSON
- **Key Features:**
  - 8+ error type handlers
  - Confidence-based application (80%+ auto-apply)
  - Gradle, AndroidX, SDK version updates
  - Conservative approach (won't break things)

**Usage:**
```bash
# Preview fixes
python scripts/auto-fix.py \
  --error-json errors.json \
  --project-dir . \
  --output-json fixes.json

# Apply fixes
python scripts/auto-fix.py \
  --error-json errors.json \
  --project-dir . \
  --apply
```

---

### Documentation (in `scripts/`)

#### **ERROR-RECOVERY-GUIDE.md**
- **Length:** 14 KB
- **Sections:** 12 major sections + FAQ
- **Contents:**
  - System architecture
  - Script details and flows
  - Error detection patterns
  - Fix strategies with confidence levels
  - Retry logic and state machine
  - Discord escalation format
  - Logging structure
  - Production checklist

**Read this for:** Complete understanding of how system works

---

#### **QUICKSTART.md**
- **Length:** 8 KB
- **Sections:** 10 focused sections
- **Contents:**
  - TL;DR one-liner
  - Setup instructions
  - Running commands
  - Example output
  - Error reference tables
  - Tips & tricks
  - Common troubleshooting
  - Example workflows

**Read this for:** Getting started quickly, solving immediate problems

---

### Updated Documentation

#### **SKILL.md** (Enhanced)
- **New Phase:** Phase 6 - Automatic Error Recovery & Retry Loop
- **New Sections:** 4 major additions
  - "Automatic Error Recovery Pipeline"
  - "Error Recovery Scripts" (error-recovery.py, auto-fix.py)
  - "Auto-Recovery Limitations"
  - Enhanced "Error Handling & Retries"
  - Updated integration steps
  - Enhanced troubleshooting

**Read this for:** Integration into full skill workflow

---

#### **ENHANCEMENT-SUMMARY.md** (New)
- **Length:** 14 KB
- **Contents:**
  - What was added
  - Components overview
  - Error detection details
  - Feature list
  - Before/after comparison
  - Testing recommendations
  - Maintenance guide

**Read this for:** Executive summary and overall picture

---

## 🔄 Error Recovery Workflow

```
┌─────────────────────────────────────────────────┐
│ 1. Error Recovery Triggered (error-recovery.py)│
│    └─ Input: GitHub run ID, repo, tokens       │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 2. Monitor Build (build-monitor.py)             │
│    └─ Polls GitHub Actions every 20 seconds    │
│    └─ Returns status: success or failure        │
└──────────────────┬──────────────────────────────┘
                   ↓ (if failure)
┌─────────────────────────────────────────────────┐
│ 3. Parse Errors (error-parser.py)               │
│    └─ Scans logs for 8+ error patterns          │
│    └─ Outputs: errors.json with classification │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 4. Generate Fixes (auto-fix.py)                 │
│    └─ Analyzes each error type                  │
│    └─ Generates targeted fixes                  │
│    └─ Scores confidence (30-90%)                │
│    └─ Outputs: fixes.json with suggestions     │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 5. Apply Fixes (auto-fix.py --apply)            │
│    └─ Modifies build.gradle.kts                 │
│    └─ Updates gradle.properties                 │
│    └─ Only applies 80%+ confidence fixes        │
│    └─ Creates: .error-recovery.log              │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 6. Commit & Push (git commands)                 │
│    └─ git add -A                                │
│    └─ git commit -m "Auto-fix: attempt #N..."  │
│    └─ git push                                  │
│    └─ Triggers new GitHub Actions build         │
└──────────────────┬──────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────┐
│ 7. Repeat (up to 3 times)                       │
│    └─ Monitor new build                         │
│    └─ If success: Done!                         │
│    └─ If failure: Parse new error type          │
│    └─ Generate new fixes                        │
│    └─ Apply and retry                           │
└──────────────────┬──────────────────────────────┘
                   ↓
        ┌──────────┴──────────┐
        ↓                     ↓
    ✅ Success          🔴 Max Retries
    Done!               └─ Escalate to Discord
```

---

## 🎯 Key Features

### ✅ Automatic Error Detection
- Regex patterns for 8+ error types
- Contextual information (file, line, suggestion)
- JSON output for programmatic handling

### ✅ Intelligent Fixing
- Type-specific fix strategies
- Confidence scoring (30-90%)
- Only applies high-confidence fixes (80%+)
- Conservative approach (won't break builds)

### ✅ Automatic Retry Loop
- Up to 3 retry attempts
- Tracks history with timestamps
- Commits all changes (auditable)
- Different error types = separate retry counts

### ✅ Discord Integration
- Real-time build status
- Escalation alerts with full context
- Retry summary and next steps
- Links to GitHub Actions logs

### ✅ Comprehensive Logging
- Real-time `.error-recovery.log`
- Structured JSON history
- Error reports per attempt
- Fix suggestions per attempt

---

## 🚀 Getting Started (3 Steps)

### Step 1: Read QUICKSTART.md
```bash
cat scripts/QUICKSTART.md
```

### Step 2: Set Environment Variables
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"
export DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/xxx/yyy"
```

### Step 3: Run Error Recovery
```bash
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 12345678
```

---

## 📊 Error Classification

| Error Type | Detection | Auto-Fix? | Confidence |
|-----------|-----------|-----------|-----------|
| Gradle Sync | `sync failed` | ✅ | 80% |
| Dependency Conflict | `version conflict` | ✅ | 85% |
| Missing SDK | `not installed` | ✅ | 90% |
| AndroidX Issue | `androidx` error | ✅ | 85% |
| Manifest Conflict | `merger failed` | ⚠️ | 75% |
| Resource Conflict | `duplicate` | ⚠️ | 60% |
| Kotlin Error | `syntax error` | ❌ | 30% |
| Java Error | `symbol not found` | ❌ | 30% |

✅ = Automatically fixed  
⚠️ = Logged and alerted  
❌ = Requires manual intervention

---

## 📁 File Organization

```
android-app-builder/
├── 📄 SKILL.md (UPDATED - error recovery docs added)
├── 📄 ENHANCEMENT-SUMMARY.md (NEW - overview)
├── 📄 ERROR-RECOVERY-INDEX.md (THIS FILE)
├── scripts/
│   ├── 🐍 error-recovery.py (NEW - main orchestrator)
│   ├── 🐍 auto-fix.py (NEW - fix generator)
│   ├── 🐍 error-parser.py (existing - reused)
│   ├── 🐍 build-monitor.py (existing - reused)
│   ├── 🐍 discord-notifier.py (existing - reused)
│   ├── 📖 ERROR-RECOVERY-GUIDE.md (NEW - complete ref)
│   └── 📖 QUICKSTART.md (NEW - quick start)
├── references/ (existing - unchanged)
├── assets/ (existing - unchanged)
└── build-logs/ (created during runs)
```

---

## 🔧 Common Tasks

### Run Error Recovery
See: [QUICKSTART.md](scripts/QUICKSTART.md)
```bash
python scripts/error-recovery.py --repo owner/repo --run-id 123 ...
```

### Preview Fixes Without Applying
See: [ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md) → "Customization"
```bash
python scripts/auto-fix.py --error-json errors.json --output-json fixes.json
```

### Understand What Went Wrong
See: [ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md) → "Logging"
1. Check `.error-recovery.log` for real-time trace
2. Check `.error-recovery-history.json` for retry summary
3. Check `.error-report-*.json` for error details
4. Check Discord for escalation context

### Customize Max Retries
See: [ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md) → "Customization"
```bash
python scripts/error-recovery.py ... --max-retries 5
```

---

## ❓ Common Questions

**Q: Can I use this without Discord?**  
A: Yes. The `--discord-webhook` argument is optional. Logs still saved locally.

**Q: What if an error can't be auto-fixed?**  
A: After 3 retries, escalated to Discord with full logs for manual intervention.

**Q: Can I customize which errors get fixed?**  
A: Yes. Edit `auto-fix.py` to change confidence thresholds or add new strategies.

**Q: How long does error recovery take?**  
A: Depends on build time. Each retry = ~5-10 minutes. Max 3x = ~30 minutes total.

**Q: Are my changes safe?**  
A: Yes. All changes in git with clear commit messages. No direct production deployments.

---

## 📞 Support & Troubleshooting

### Issue: Python module not found
→ See [QUICKSTART.md](scripts/QUICKSTART.md) → "Troubleshooting"

### Issue: Discord webhook not working
→ See [ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md) → "Troubleshooting"

### Issue: Build keeps failing after retries
→ See [SKILL.md](SKILL.md) → "Troubleshooting"

### Issue: Want to understand the system
→ Read [ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md) → "Architecture"

---

## 🎓 Learning Path

1. **5 min:** Read [QUICKSTART.md](scripts/QUICKSTART.md) - Get overview
2. **15 min:** Read [ENHANCEMENT-SUMMARY.md](ENHANCEMENT-SUMMARY.md) - Understand scope
3. **30 min:** Read [ERROR-RECOVERY-GUIDE.md](scripts/ERROR-RECOVERY-GUIDE.md) - Deep dive
4. **10 min:** Review [SKILL.md](SKILL.md) Phase 6 - Integration context
5. **Hands-on:** Run error-recovery.py on a real build

---

## 📈 Performance & Scale

| Metric | Value |
|--------|-------|
| Supported Error Types | 8+ |
| Auto-Fix Confidence Range | 30-90% |
| High-Confidence (Auto-Apply) | 80%+ |
| Max Retry Attempts | 3 (configurable) |
| Poll Interval | 20 seconds (configurable) |
| Max Wait Time | 1800 seconds / 30 min |
| Log Files Created | 3-4 per run |
| Git Commits Created | Up to 3 per recovery cycle |

---

## 🏆 Quality Metrics

- ✅ 600+ lines of production code
- ✅ 8+ error type handlers
- ✅ Confidence scoring (prevents bad fixes)
- ✅ Full error handling with retries
- ✅ Comprehensive logging
- ✅ Git integration for auditability
- ✅ Discord integration for visibility
- ✅ State machine for reliability
- ✅ Edge case handling (network, git, timeout)
- ✅ Production-ready code quality

---

## 📝 Documentation Stats

| Document | Type | Size | Purpose |
|----------|------|------|---------|
| QUICKSTART.md | Guide | 8 KB | Get started quickly |
| ERROR-RECOVERY-GUIDE.md | Reference | 14 KB | Complete documentation |
| ENHANCEMENT-SUMMARY.md | Overview | 14 KB | What was added |
| SKILL.md | Integration | Updated | How it fits in skill |
| CODE | Python | 45 KB | Scripts (error-recovery + auto-fix) |

**Total Documentation:** 40+ KB (comprehensive)  
**Total Code:** 45+ KB (production-ready)

---

## 🚀 Ready to Use!

The android-app-builder error recovery system is **production-ready** with:

- ✅ Automatic error detection and fixing
- ✅ Intelligent retry logic (up to 3x)
- ✅ Discord integration for notifications
- ✅ Comprehensive logging and history
- ✅ Conservative approach (won't break builds)
- ✅ Full documentation and guides

**Next Step:** Start with [QUICKSTART.md](scripts/QUICKSTART.md)

---

**Status:** ✅ Complete  
**Last Updated:** 2026-03-25  
**Version:** 1.0.0

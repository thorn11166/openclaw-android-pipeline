# Error Recovery System - Complete Guide

## Overview

The Android App Builder now includes **automatic error detection, recovery, and retry logic**. When a build fails, the system:

1. 🔍 **Analyzes** the error logs
2. 🔧 **Generates** targeted fixes
3. ✅ **Applies** high-confidence fixes automatically
4. 🔄 **Retries** the build up to 3 times
5. 📢 **Escalates** to Discord if recovery fails

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  error-recovery.py (Main Orchestrator)                  │
│  ├─ Monitors: build-monitor.py                          │
│  ├─ Parses: error-parser.py                             │
│  ├─ Fixes: auto-fix.py                                  │
│  └─ Notifies: Discord webhook                           │
└─────────────────────────────────────────────────────────┘
        ↓
    GitHub Actions
        ↓
    Build Log
        ↓
   error-parser.py (JSON errors)
        ↓
   auto-fix.py (JSON fix suggestions)
        ↓
    Apply fixes → Commit → Push → Retrigger
```

## Scripts Overview

### 1. error-recovery.py (Orchestrator)
**Purpose:** Coordinates the entire error recovery pipeline.

**Main Flow:**
```python
run_full_recovery_cycle(run_id) {
    for each retry (max 3):
        1. Monitor build with build-monitor.py
        2. If success: Done! Return True
        3. If failure:
           - Parse errors with error-parser.py
           - Generate fixes with auto-fix.py
           - Apply fixes (git add, commit, push)
           - Trigger new build
           - Sleep 5 seconds
           - Repeat monitoring with new run_id
        4. If all retries exhausted: Escalate to Discord
}
```

**Key Classes:**
- `ErrorRecoveryOrchestrator` - Manages state and retry logic
- `RecoveryState` - Enum tracking current phase
- `RetryAttempt` - Records each retry with details

**Output Files:**
- `.error-recovery.log` - Real-time log (append-only)
- `.error-recovery-history.json` - Structured retry history
- `.error-report-*.json` - Parsed errors from each attempt
- `.fixes-report-*.json` - Fix suggestions from each attempt

### 2. error-parser.py (Error Detection)
**Purpose:** Classifies and categorizes errors in build logs.

**Supported Error Types:**
1. `gradle_sync` - Gradle dependency resolution failures
2. `missing_sdk` - Missing Android SDK components
3. `kotlin_compilation` - Kotlin syntax/type errors
4. `java_compilation` - Java compilation errors
5. `resource_conflict` - Duplicate resource definitions
6. `manifest_merge` - AndroidManifest.xml conflicts
7. `dependency_resolution` - Version conflicts
8. `build_timeout` - Build exceeded time limit

**Pattern Matching:**
- Uses regex to identify error patterns
- Extracts file paths and line numbers
- Provides contextual lines (2 before/after)

**Output (JSON):**
```json
{
  "total_errors": 2,
  "errors_by_type": {
    "gradle_sync": 1,
    "missing_sdk": 1
  },
  "first_error": {
    "error_type": "gradle_sync",
    "line_number": 45,
    "file_path": "build.gradle.kts",
    "error_message": "Failed to resolve dependency",
    "suggestion": "Check build.gradle.kts versions...",
    "raw_context": "..."
  },
  "all_errors": [...]
}
```

### 3. auto-fix.py (Automated Fixer)
**Purpose:** Generates and applies targeted fixes based on error type.

**Fix Strategies:**
1. **UPDATE_DEPENDENCY** (85% confidence)
   - Updates library versions in build.gradle.kts
   - Targets AndroidX and Jetpack libs

2. **UPDATE_SDK_VERSION** (80% confidence)
   - Updates compileSdk and targetSdk
   - Ensures consistency

3. **UPDATE_GRADLE_VERSION** (70% confidence)
   - Updates Gradle wrapper version if needed

4. **ENABLE_ANDROIDX** (90% confidence)
   - Sets `android.useAndroidX=true`
   - Sets `android.enableJetifier=true`

5. **FIX_MANIFEST_MERGE** (75% confidence)
   - Detects conflicts
   - Suggests tools:replace usage
   - Requires manual review

6. **ADD_MISSING_RESOURCE** (60% confidence)
   - Identifies missing resources
   - Points to specific files

7. **FIX_KOTLIN_SYNTAX** (30% confidence)
   - Low confidence; mostly just logs issues
   - Suggests manual review

**Key Methods:**
- `generate_fixes(error_report)` - Analyzes errors and generates suggestions
- `apply_fixes(fixes)` - Applies high-confidence fixes to files
- `_apply_dependency_update()` - Updates build.gradle.kts
- `_apply_sdk_version_update()` - Updates SDK versions
- `_apply_androidx_enablement()` - Configures gradle.properties
- `_deduplicate_fixes()` - Removes duplicate suggestions

**Output (JSON):**
```json
{
  "total_suggestions": 3,
  "timestamp": "2026-03-25T19:12:00",
  "suggestions": [
    {
      "strategy": "update_dependency",
      "file": "build.gradle.kts",
      "description": "Update androidx.appcompat:appcompat",
      "confidence": 0.85,
      "changes": {
        "artifact": "androidx.appcompat:appcompat",
        "new_version": "1.6.1"
      }
    }
  ]
}
```

## Usage Examples

### Basic Error Recovery
```bash
cd /path/to/android-project
python scripts/error-recovery.py \
  --repo myuser/myapp \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 123456789 \
  --max-retries 3
```

### Without Discord Notifications
```bash
python scripts/error-recovery.py \
  --repo myuser/myapp \
  --github-token $GITHUB_TOKEN \
  --run-id 123456789
```

### With Custom Project Directory
```bash
python scripts/error-recovery.py \
  --repo myuser/myapp \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --project-dir /path/to/project \
  --run-id 123456789
```

### Preview Fixes Without Applying
```bash
python scripts/error-parser.py \
  --log-file build-logs/run-123456789.log \
  --output-format json > errors.json

python scripts/auto-fix.py \
  --error-json errors.json \
  --project-dir . \
  --output-json fixes.json
# (Don't use --apply flag)
```

## Error Recovery States

```
MONITORING
    ↓ [build completes]
[SUCCESS] → COMPLETE_SUCCESS (end)
    ↓ [failure]
ERROR_DETECTED
    ↓
PARSING_ERRORS
    ↓
GENERATING_FIXES
    ↓
APPLYING_FIXES
    ↓
COMMITTING
    ↓ [failure] → ESCALATING
PUSHING
    ↓ [failure] → ESCALATING
RETRIGGERING_BUILD
    ↓
MONITORING (new run_id)
    ↓
[repeat up to max_retries]
    ↓ [max retries exceeded]
ESCALATING → COMPLETE_FAILURE
```

## Confidence Levels

| Level | Range | Action | Examples |
|-------|-------|--------|----------|
| **Very High** | 85-90% | Auto-apply | Dependency updates, AndroidX enabling, SDK version sync |
| **High** | 75-84% | Auto-apply + log | Gradle sync fixes, manifest alerts |
| **Medium** | 60-74% | Log + alert | Resource conflict detection |
| **Low** | <60% | Manual only | Kotlin/Java syntax errors, complex logic issues |

## Retry Logic

### Single Attempt Example
```
Run #1: Gradle sync error
  └─ Parse: gradle_sync type
  └─ Fix: Update appcompat to 1.6.1
  └─ Commit: "Auto-fix: Error recovery attempt #1 [skip ci]"
  └─ Push: Changes go to GitHub
  └─ Trigger: New run #2
  └─ Monitor: Run #2 → Different error

Run #2: Missing SDK error
  └─ Parse: missing_sdk type
  └─ Fix: Update compileSdk to 34
  └─ Commit: "Auto-fix: Error recovery attempt #2 [skip ci]"
  └─ Push: Changes go to GitHub
  └─ Trigger: New run #3
  └─ Monitor: Run #3 → Kotlin syntax error (can't fix)

Run #3: Kotlin compilation error
  └─ Parse: kotlin_compilation type
  └─ Fix: Log only (confidence too low)
  └─ No changes made
  └─ Max retries exceeded
  └─ Escalate to Discord with logs
```

### Retry History
Each retry is recorded:
```json
{
  "final_state": "complete_failure",
  "total_attempts": 3,
  "max_retries": 3,
  "success": false,
  "timestamp": "2026-03-25T19:12:00",
  "attempts": [
    {
      "attempt_number": 1,
      "error_type": "gradle_sync",
      "error_count": 1,
      "fixes_applied": 1,
      "success": false,
      "timestamp": "2026-03-25T19:05:00",
      "run_id": 123456789,
      "error_summary": "1 errors of 1 types"
    },
    {
      "attempt_number": 2,
      "error_type": "missing_sdk",
      "error_count": 1,
      "fixes_applied": 1,
      "success": false,
      "timestamp": "2026-03-25T19:08:00",
      "run_id": 123456790,
      "error_summary": "1 errors of 1 types"
    },
    {
      "attempt_number": 3,
      "error_type": "kotlin_compilation",
      "error_count": 1,
      "fixes_applied": 0,
      "success": false,
      "timestamp": "2026-03-25T19:11:00",
      "run_id": 123456791,
      "error_summary": "1 errors of 1 types"
    }
  ]
}
```

## Discord Escalation Format

When all retries fail, Discord receives:

```
🔴 Build Recovery Failed - Escalation

Run #123456789 in [myuser/myapp](https://github.com/myuser/myapp/actions/runs/123456789)

Recovery Summary:
  ❌ Attempt 1: gradle_sync (1 errors, 1 fixes)
  ❌ Attempt 2: missing_sdk (1 errors, 1 fixes)
  ❌ Attempt 3: kotlin_compilation (1 errors, 0 fixes)

Final Error Log:
```
[Last 1000 chars of build log]
```

Next Steps:
1. Review logs above
2. Debug locally
3. Commit and push fixes
4. Re-run build
```

## Logging

### Real-Time Log
`.error-recovery.log` (append-only):
```
[2026-03-25 19:05:00] INFO 🚀 Starting error recovery cycle for run #123456789
[2026-03-25 19:05:00] INFO 📊 Phase 1: Monitoring build...
[2026-03-25 19:05:20] INFO Status: queued
[2026-03-25 19:05:40] INFO Status: in_progress
[2026-03-25 19:08:00] INFO ✅ Logs saved: build-logs/run-123456789.log
[2026-03-25 19:08:00] INFO ❌ BUILD FAILED (conclusion: failure)
[2026-03-25 19:08:00] INFO ❌ Build failed, starting error recovery loop...
```

### Error Reports
`.error-report-1711382700.json`:
```json
{
  "total_errors": 2,
  "errors_by_type": {
    "gradle_sync": 1,
    "missing_sdk": 1
  },
  "first_error": {...},
  "all_errors": [...]
}
```

### Fix Reports
`.fixes-report-1711382700.json`:
```json
{
  "total_suggestions": 2,
  "timestamp": "2026-03-25T19:08:00",
  "suggestions": [
    {...},
    {...}
  ]
}
```

## Edge Cases & Handling

### Network Error During Monitoring
- Retry monitoring after 20 second delay
- Log each retry attempt
- Continue up to max_wait (1800s default)

### Git Push Fails
- Logged as warning, stops retry cycle
- Escalated to Discord
- User must fix git conflict manually

### Build Retrigger Fails
- Logged and escalated
- May indicate GitHub token permissions issue
- User must verify token and retry

### Multiple Error Types Across Retries
- Tracked separately in retry history
- Each type subject to same 3-retry limit
- Different errors in sequence = separate retry attempts

### Manifest Conflicts
- Detected with medium confidence (75%)
- NOT auto-applied (requires domain knowledge)
- Logged and user alerted
- Escalated after retries

## Customization

### Change Max Retries
```bash
python scripts/error-recovery.py \
  --repo myuser/myapp \
  --github-token $GITHUB_TOKEN \
  --max-retries 5  # Default is 3
```

### Increase Poll Interval
Edit `error-recovery.py`, change in `_run_build_monitor()`:
```python
subprocess.run([
    ...
    "--poll-interval",
    "30",  # Was 20, now 30 seconds
    ...
])
```

### Skip Discord Notifications
```bash
python scripts/error-recovery.py \
  --repo myuser/myapp \
  --github-token $GITHUB_TOKEN \
  --run-id 123456789
  # (omit --discord-webhook)
```

## Production Readiness Checklist

- ✅ Error parsing with 8+ error types
- ✅ Confidence-based fix application (80%+ auto-apply)
- ✅ Automatic retry loop (up to 3 times)
- ✅ Git integration (commit, push, retrigger)
- ✅ Discord escalation with full context
- ✅ Comprehensive logging (file + JSON)
- ✅ Graceful degradation (no fixes > escalate)
- ✅ State tracking and recovery history
- ✅ Error handling for network/git issues
- ✅ Timeout handling (build monitor max_wait)

## Troubleshooting

### "Auto-fix didn't apply any fixes"
1. Check `.fixes-report-*.json` confidence levels
2. If <80%, that's by design (safety first)
3. Manually apply fix and push to retrigger

### "Build kept failing even after retries"
1. Review `.error-recovery-history.json` for what was tried
2. Check `.error-report-*.json` for error classification
3. Some errors (syntax, logic) can't be auto-fixed
4. Discord escalation provides full logs for manual debugging

### "Webhook failed but no Discord message"
1. Check Discord webhook URL is correct
2. Verify Discord channel still exists
3. Check webhook hasn't been revoked
4. Error logs still saved to `.error-recovery.log`

### "Git push failed during retry"
1. Check network connectivity
2. Verify GitHub token has correct permissions
3. Check for merge conflicts in repo
4. Manually resolve and retry

## FAQ

**Q: Can I customize which error types get auto-fixed?**
A: Edit `auto-fix.py` in `_fix_*` methods. Lower confidence threshold or add new strategies. Remember to test thoroughly.

**Q: What if an error occurs that isn't in the list?**
A: Classified as `unknown`. Logged but not fixed. Escalated to Discord after max retries.

**Q: Can I increase max retries beyond 3?**
A: Yes, use `--max-retries N`. Be aware: 3 retries = ~15 minutes of build time. Higher = longer waits.

**Q: Do auto-applied fixes get reviewed?**
A: All changes are in git commits with clear messages. Review in GitHub before merging to main branch.

**Q: What's the difference between confidence levels?**
A: High (85%+) = auto-apply. Medium (60-84%) = log + alert. Low (<60%) = manual only. Prevents breaking changes.

**Q: Can the system fix logic errors?**
A: No. It handles config/dependency/build issues. Logic errors need human review and fix.

---

**Last Updated:** 2026-03-25  
**Status:** Production-Ready

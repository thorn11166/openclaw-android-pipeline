# Error Recovery Quick Start

## TL;DR

```bash
# In your Android project root:
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 12345 \
  --max-retries 3
```

That's it! The system will:
- Monitor the build
- If it fails, automatically detect errors
- Generate and apply targeted fixes
- Retry up to 3 times
- Escalate to Discord if recovery fails

## Setup (One-Time)

### 1. Get GitHub Token
```bash
# Go to: https://github.com/settings/tokens
# Create Fine-grained token with:
#   - Repository access: All repositories
#   - Permissions: Contents (R/W), Actions (R), Workflows (R/W)

export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"
```

### 2. Get Discord Webhook
```bash
# In Discord: Channel → Integrations → Webhooks → New Webhook
# Copy URL

export DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/xxx/yyy"
```

### 3. Install Python Dependencies
```bash
pip install requests
```

## Running Error Recovery

### After a Build Failure
```bash
# Get the run ID from GitHub Actions URL:
# https://github.com/owner/repo/actions/runs/12345678
#                                             ^^^^^^^^

python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 12345678
```

### Without Discord (Console Only)
```bash
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --run-id 12345678
```

### Custom Project Directory
```bash
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --project-dir /path/to/project \
  --run-id 12345678
```

### More Retries
```bash
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 12345678 \
  --max-retries 5  # Default is 3
```

## What Happens

### Console Output
```
[19:05:00] INFO 🚀 Starting error recovery cycle for run #123456789
[19:05:00] INFO 📊 Phase 1: Monitoring build...
[19:05:20] INFO Status: queued
[19:05:40] INFO Status: in_progress
[19:08:00] INFO ✅ Logs saved: build-logs/run-123456789.log
[19:08:00] INFO ❌ BUILD FAILED
[19:08:00] INFO ❌ Build failed, starting error recovery loop...
[19:08:00] INFO ============================================================
[19:08:00] INFO RECOVERY ATTEMPT 1/3
[19:08:00] INFO ============================================================
[19:08:00] INFO 🔍 Found 2 errors:
[19:08:00] INFO    • gradle_sync: 1
[19:08:00] INFO    • missing_sdk: 1
[19:08:00] INFO 💡 Generated 2 fix suggestions
[19:08:00] INFO 🔧 Applied 2 fix(es)
[19:08:00] INFO ✅ Committed: 'Auto-fix: Error recovery attempt #1 [skip ci]'
[19:08:01] INFO ✅ Changes pushed to GitHub
[19:08:01] INFO 🔄 New build triggered: run #123456790
[19:08:06] INFO 📊 Phase 1: Monitoring build...
[19:08:26] INFO Status: queued
[19:08:46] INFO Status: in_progress
[19:11:00] INFO ✅ Logs saved: build-logs/run-123456790.log
[19:11:00] INFO ✅ BUILD SUCCEEDED after 1 attempt(s)!
[19:11:00] INFO ✅ Recovery history saved: .error-recovery-history.json
```

### Discord Notifications

**Success:**
```
✅ Android Build SUCCESS

Repository: owner/repo
Build #: 123456790
Duration: 2.8m
Retry #: 1

View details: [GitHub Actions]
```

**Escalation (Max Retries):**
```
🔴 Build Recovery Failed - Escalation

Run #123456791 in owner/repo

Recovery Summary:
  ❌ Attempt 1: gradle_sync (1 errors, 1 fixes)
  ❌ Attempt 2: missing_sdk (1 errors, 1 fixes)
  ❌ Attempt 3: kotlin_compilation (1 errors, 0 fixes)

Final Error Log:
[error context]

Next Steps:
1. Review logs above
2. Debug locally
3. Commit and push fixes
4. Re-run build
```

## Output Files

After running, check:

```
.error-recovery.log
├─ Real-time log of entire process
├─ Timestamps for each phase
└─ Perfect for debugging

.error-recovery-history.json
├─ Structured retry history
├─ JSON format for parsing
└─ Shows what was tried and why it failed

build-logs/run-*.log
├─ Full GitHub Actions logs
├─ One per build attempt
└─ Source of truth for errors

.error-report-*.json
├─ Parsed errors from each attempt
├─ Error classification and suggestions
└─ Input to auto-fix.py

.fixes-report-*.json
├─ Fix suggestions from each attempt
├─ Confidence scores
└─ What was/wasn't applied
```

## Common Error Types (Auto-Fixed ✅)

| Error | Fix | Confidence |
|-------|-----|-----------|
| Gradle dependency conflict | Update version in build.gradle.kts | 85% |
| Missing SDK version | Update compileSdk | 90% |
| AndroidX error | Enable in gradle.properties | 85% |
| Gradle sync failure | Update SDK + enable AndroidX | 80% |

## Common Error Types (Escalated ⚠️)

| Error | Reason | Action |
|-------|--------|--------|
| Kotlin syntax error | Logic error, not config | Debug locally |
| Manifest conflict | Requires domain knowledge | Manual review |
| Resource duplication | Which copy to remove? | Manual review |
| Build timeout | Resource intensive | Check runner or increase timeout |

## Exit Codes

- `0` = Success (build passed)
- `1` = Max retries exceeded (escalated)
- `2` = Interrupted by user (Ctrl+C)

## Tips & Tricks

### Dry-Run Error Parsing
```bash
python scripts/error-parser.py \
  --log-file build-logs/run-12345.log \
  --output-format json \
  --summary-only
```

### Preview Fixes Without Applying
```bash
# Parse errors
python scripts/error-parser.py \
  --log-file build-logs/run-12345.log \
  --output-format json > errors.json

# Preview fixes
python scripts/auto-fix.py \
  --error-json errors.json \
  --project-dir . \
  --output-json fixes.json
# (no --apply flag)

# Review fixes.json before applying manually
```

### Enable Verbose Logging
Edit `error-recovery.py`, change:
```python
logging.basicConfig(level=logging.DEBUG)  # Was INFO
```

### Increase Build Timeout
Default is 30 minutes. To increase:
```bash
# Edit scripts/error-recovery.py, find _run_build_monitor call:
result = subprocess.run([
    ...
    "--max-wait",
    "3600",  # 60 minutes instead of 1800 (30 min)
    ...
])
```

## Troubleshooting

### "Python: command not found"
```bash
# Use python3 instead
python3 scripts/error-recovery.py ...
```

### "requests library not found"
```bash
pip install requests
# or
pip3 install requests
```

### "GITHUB_TOKEN not found"
```bash
# Set it explicitly or via env:
export GITHUB_TOKEN="ghp_xxxxx"
python scripts/error-recovery.py --github-token $GITHUB_TOKEN ...
```

### "Discord webhook returned 401"
- Check webhook URL is correct
- Verify Discord channel still exists
- Create new webhook if needed

### "Build still fails after retries"
1. Check `.error-recovery-history.json` for what was tried
2. Review Discord escalation for error context
3. Debug locally and commit fixes manually
4. Re-run error-recovery with new run ID

## Example Workflow

```bash
# 1. Push code to trigger build
git push

# 2. Wait for failure (or check Actions page)
# 3. Get run ID from: https://github.com/owner/repo/actions/runs/123456

# 4. Start error recovery
cd /path/to/project
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 123456789

# 5. Watch console + Discord
# System will auto-retry up to 3 times

# 6a. If success: Done! 🎉
# Check Discord for "✅ BUILD SUCCESS" notification

# 6b. If max retries exceeded:
# Review Discord "🔴 Build Recovery Failed" message
# Debug locally, fix issue, push, and retry:
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --run-id 123456790  # New run ID
```

---

**Need help?** See ERROR-RECOVERY-GUIDE.md for detailed documentation.

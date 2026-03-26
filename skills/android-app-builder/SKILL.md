# Android App Builder Skill

**Orchestrates the complete Android development lifecycle** — from idea clarification through GitHub integration, CI/CD setup, automated builds, error detection, and Discord-tracked feedback loops.

## When to Use

Use this skill when:
- Building a new Android app from scratch
- Automating the dev-to-deploy workflow
- Integrating GitHub + GitHub Actions + Discord for transparent build tracking
- Need intelligent error parsing and retry logic
- Want a hands-off build pipeline that reports to Discord in real-time

**NOT for:**
- Publishing to Google Play Store (out of scope)
- Mobile game development with complex graphics engines
- Cross-platform frameworks (Flutter, React Native) — this is native Android only

---

## Model Selection

This skill supports flexible model switching between:
- **Primary**: openrouter/deepseek/deepseek-chat ($0.14/M input tokens)
- **Fallback**: anthropic/claude-haiku-4-5-20251001 ($0.80/M input tokens)

### Switching Methods:
1. **Session Override**: `/model anthropic/claude-opus-4-6`
2. **Config Primary**: Edit `openclaw.json` + restart
3. **Fallback Chain**: Add `"fallbacks": ["anthropic/claude-opus-4-6"]`
4. **Sub-agent Spawn**: `sessions_spawn(model="anthropic/claude-opus-4-6")`

### Cost Comparison (per 20 builds):
- DeepSeek V3: ~$0.02
- Opus 4.6: ~$2.00
- Hybrid (80/20): ~$0.42

### Recommendations:
- Use DeepSeek for routine builds
- Escalate to Opus for complex error resolution
- Test model changes in `anime-calc` before production

## Requirements

Before starting, ensure you have:

### 1. **GitHub Personal Access Token**
- Go to: `https://github.com/settings/tokens`
- Create a **Fine-grained token** with:
  - Repository access: `All repositories` (or specify repos)
  - Permissions:
    - `Contents` (read/write)
    - `Actions` (read)
    - `Workflows` (read/write)
- Store securely in env var: `GITHUB_TOKEN`

### 2. **Discord Webhook URL (per project)**
- Open your Discord server → target channel → Integrations → Webhooks
- Create a webhook, copy the URL
- Provide when asked or set `DISCORD_WEBHOOK_URL`

### 3. **GitHub Actions Environment**
- Repos must have GitHub Actions enabled
- Android SDK and build tools installed via action (provided in template)

### 4. **Phase 2.5 Code Review — no extra setup required**
- Uses `sessions_spawn(model="anthropic/claude-sonnet-4-6")` — OpenClaw native
- Runs on your existing subscription, no separate API key needed
- Switch to Opus for deeper review: `sessions_spawn(model="anthropic/claude-opus-4-6")`

### 5. **Optional: Local Android SDK**
- For testing locally before pushing to GitHub
- Set `ANDROID_HOME` env var
- Not required if relying on GitHub Actions

---

## Workflow

### Phase 1: Idea Clarification
1. Agent asks 7-8 targeted questions about the app
2. Captures: name, purpose, target SDK, key features, UI requirements
3. Generates a brief spec document

### Phase 2: Code Generation
1. Creates Kotlin/Java boilerplate from template
2. Customizes `AndroidManifest.xml` based on app needs
3. Generates `build.gradle.kts` with correct dependencies
4. Scaffolds basic UI layout files
5. Bundles into a clean project structure

### Phase 2.5: Claude Code Review *(always runs — uses your existing subscription)*

This phase uses a higher-capability Claude model to review the code DeepSeek just
generated, catching build-blocking issues before they ever hit CI/CD. The review
runs via `sessions_spawn()` — OpenClaw's native sub-agent mechanism — so it uses
your existing subscription with no separate API key or credentials.

**Flow (Zoidberg orchestrates all steps):**

```
Step 1 — Collect files & build prompt:
  python scripts/code-reviewer.py \
    --project-dir . \
    --output-prompt .review-prompt.txt

Step 2 — Spawn Claude sub-agent for review:
  sessions_spawn(model="anthropic/claude-sonnet-4-6", prompt_file=".review-prompt.txt")
  → save response to .review-response.txt

Step 3 — Parse response into structured report:
  python scripts/code-reviewer.py \
    --response-file .review-response.txt \
    --output-json .code-review-report.json \
    --discord-webhook $DISCORD_WEBHOOK_URL
  → exits 0 (passed) or 1 (critical issues / score < 60)

Step 4 — If exit 1:
  Read prompt_for_model from .code-review-report.json
  Send it to DeepSeek as its next instruction
  DeepSeek revises the affected files
  Repeat from Step 1 (max 2 revision rounds)

Step 5 — If exit 0 (or after 2 revision rounds):
  Proceed to Phase 3 (GitHub push)
```

**Model options (switch at Step 2):**
- `anthropic/claude-sonnet-4-6` — default, fast, catches most issues
- `anthropic/claude-opus-4-6` — deeper review for complex architectures

**What Claude reviews:**
- **critical** — will prevent the project from building
- **high** — likely runtime crash or serious architecture violation
- **medium** — best-practice violations
- **low** — style and minor improvements
- Security, missing resources, deprecated Gradle APIs

**The `prompt_for_model` field** is a complete, copy-pasteable instruction for
DeepSeek — no reformatting needed:
> "In MainActivity.kt line 21, the theme Theme.MaterialComponents.Light includes
> a built-in ActionBar which conflicts with setSupportActionBar(). Change the
> parent in themes.xml to Theme.MaterialComponents.Light.NoActionBar."

---

### Phase 3: GitHub Integration
1. Creates a new repository on GitHub
2. Initializes git locally with `.gitignore`
3. Pushes initial commit with full project structure
4. Returns repo URL

### Phase 4: GitHub Actions Setup
1. Creates `.github/workflows/build.yml` from template
2. Customizes SDK versions, build variants, signing (if needed)
3. Commits workflow file
4. Pushes to trigger first build

### Phase 5: Build Monitoring Loop
1. **build-monitor.py** polls GitHub Actions API
2. Tracks build status every 15–30 seconds
3. Captures build logs on completion
4. Extracts errors using **error-parser.py**
5. Posts updates to Discord via webhook

### Phase 6: Automatic Error Recovery & Retry Loop
1. **Continuous Monitoring:**
   - `build-monitor.py` polls GitHub Actions for build status
   - On completion, analyzes conclusion (success/failure/timeout)
   - Saves full logs to `build-logs/run-{id}.log`

2. **Error Detection & Analysis:**
   - `error-parser.py` scans logs for 8+ error types
   - Categorizes: Gradle, Kotlin, manifest, dependencies, resources, AndroidX, etc.
   - Produces structured JSON with line numbers, file paths, and fix suggestions

3. **Automated Fixing:**
   - `auto-fix.py` generates targeted fixes based on error type
   - **Dependency errors**: Updates `build.gradle.kts` versions
   - **AndroidX errors**: Enables flags in `gradle.properties`
   - **Manifest errors**: Detects and logs conflicts for review
   - **Resource conflicts**: Identifies duplicates and suggests deduplication
   - **SDK version mismatches**: Updates `compileSdk` and `targetSdk`
   - Applies fixes with high confidence (85%+)
   - Logs all changes for auditability

4. **Automatic Retry Cycle:**
   - `error-recovery.py` orchestrates full pipeline:
     1. Monitor build → detect errors
     2. Parse errors → generate fixes
     3. Apply fixes → commit changes
     4. Push to GitHub → trigger new build
     5. Repeat monitoring with new run ID
   - **Up to 3 retries per error type** (configurable)
   - Tracks retry history with timestamps and outcomes
   - **Escalates to Discord** if all retries fail:
     - Full error logs
     - Retry summary (what was tried, why it failed)
     - Actionable next steps for manual intervention

5. **Graceful Degradation:**
   - Low-confidence fixes (e.g., Kotlin syntax errors) logged but not auto-applied
   - Manifest merge conflicts escalated for manual review
   - Build timeouts escalated immediately
   - Network errors trigger automatic retry with backoff

### Phase 7: Discord Feedback & Loop
1. Success/failure posted to project channel
2. Discord channel becomes source of truth for build history
3. User can reply with feedback → agent fetches messages
4. Changes triggered from Discord → rebuild cycle repeats

---

## File Reference

### Code Review Script

#### **code-reviewer.py** — Claude Code Review (Phase 2.5)
Two-mode helper script that brackets a `sessions_spawn()` call. No model
credentials required — the actual review runs through OpenClaw's native
sub-agent mechanism using your existing subscription.

**Mode 1 — Build prompt** (`--output-prompt`):
Collect all `.kt`/`.java`/`.xml`/`.kts` files and write a structured review
prompt to a file. Zoidberg then passes that file to `sessions_spawn()`.

**Mode 2 — Parse response** (`--response-file`):
Read the raw JSON from the sub-agent, produce a normalised report, print a
formatted summary, and exit 0 (passed) or 1 (issues found / low score).

**Step 1 — Build prompt:**
```bash
python scripts/code-reviewer.py \
  --project-dir /path/to/project \
  --output-prompt .review-prompt.txt
```

**Step 2 — Zoidberg spawns sub-agent (no script needed):**
```
sessions_spawn(model="anthropic/claude-sonnet-4-6", prompt_file=".review-prompt.txt")
# or for deeper review:
sessions_spawn(model="anthropic/claude-opus-4-6", prompt_file=".review-prompt.txt")
```

**Step 3 — Parse response:**
```bash
python scripts/code-reviewer.py \
  --response-file .review-response.txt \
  --output-json .code-review-report.json \
  --model-used anthropic/claude-sonnet-4-6 \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --pass-threshold 60
```

**Key arguments:**
| Flag | Mode | Default | Description |
|---|---|---|---|
| `--project-dir` | 1 | `.` | Root of Android project |
| `--output-prompt` | 1 | — | Write review prompt to this file |
| `--response-file` | 2 | — | Raw JSON response from sub-agent |
| `--model-used` | 2 | `anthropic/claude-sonnet-4-6` | Recorded in report |
| `--output-json` | 2 | — | Save parsed report to this file |
| `--pass-threshold` | 2 | `60` | Min quality score to exit 0 |
| `--discord-webhook` | 2 | — | Post summary to Discord |
| `--quiet` | 2 | off | Suppress console report |

**Output JSON (from Mode 2):**
```json
{
  "timestamp": "2026-03-26T12:00:00",
  "model_used": "anthropic/claude-sonnet-4-6",
  "overall_quality": "fair",
  "quality_score": 62,
  "summary": "Code has one build-blocking issue and two high-severity problems.",
  "issues": [
    {
      "severity": "critical",
      "category": "build",
      "file": "activity_main.xml",
      "line": 11,
      "issue": "Unknown class com.google.android.material.appbarwith.MaterialToolbar",
      "suggestion": "Change `appbarwith` to `appbar` in the fully qualified class name."
    }
  ],
  "issue_counts": { "critical": 1, "high": 2, "medium": 0, "low": 1 },
  "prompt_for_model": "Please fix the following issues in the generated code: ...",
  "passed": false
}
```

**How `prompt_for_model` is used:**
```
Zoidberg reads .code-review-report.json
  └─ if not passed:
       send prompt_for_model to DeepSeek as next instruction
       DeepSeek revises files
       repeat from Step 1 (max 2 rounds)
  └─ if passed:
       continue to Phase 3 (GitHub push)
```

---

### Error Recovery Scripts

#### **error-recovery.py** (NEW - Main Orchestrator)
Coordinates the complete error recovery pipeline: monitoring → detection → fixing → retry.

**Features:**
- Full error detection loop with GitHub Actions API integration
- Automatic error parsing and fix generation
- Intelligent retry logic with exponential backoff
- Discord escalation with full context
- Comprehensive logging and history tracking

**Usage:**
```bash
python scripts/error-recovery.py \
  --repo OWNER/REPO \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --project-dir . \
  --run-id 12345678 \
  --max-retries 3
```

**Workflow:**
1. Monitors build with `build-monitor.py`
2. On failure, parses errors with `error-parser.py`
3. Generates fixes with `auto-fix.py`
4. Applies fixes and commits/pushes changes
5. Retrigggers new build and monitors again
6. Repeats up to `--max-retries` times
7. On final failure, sends escalation to Discord with full logs

**Output:**
- `.error-recovery.log` - Real-time recovery log
- `.error-recovery-history.json` - Structured retry history
- `.error-report-*.json` - Parsed errors from each attempt
- `.fixes-report-*.json` - Fix suggestions from each attempt

**Exit Codes:**
- `0` = Success (build passed)
- `1` = Max retries exceeded (escalated to Discord)

---

#### **auto-fix.py** (NEW - Automated Fix Generator)
Takes error reports and generates + applies targeted fixes.

**Features:**
- 8+ error type handlers with specific fix strategies
- Gradle dependency version updates
- AndroidX/Jetpack flag configuration
- SDK version synchronization
- Manifest merge conflict detection
- Resource duplication warnings
- Confidence scoring (0.0-1.0) for each fix

**Supported Error Types:**
1. **Dependency Resolution** (confidence: 85%)
   - Detects version conflicts
   - Updates `build.gradle.kts` with compatible versions
   - Enables AndroidX if needed

2. **Gradle Sync** (confidence: 80%)
   - Updates `compileSdk` and `targetSdk`
   - Enables AndroidX for Jetpack compatibility

3. **Missing SDK** (confidence: 90%)
   - Extracts required SDK version from error
   - Updates build configuration

4. **Manifest Merge** (confidence: 75%)
   - Detects conflicting attributes
   - Suggests `tools:replace` usage
   - Requires manual review for application

5. **Resource Conflicts** (confidence: 60%)
   - Identifies duplicate resource definitions
   - Points to specific files
   - Suggests deduplication approach

6. **Kotlin Compilation** (confidence: 30%)
   - Logs unresolved references
   - Suggests import checks
   - Requires manual review

7. **Java Compilation** (confidence: 30%)
   - Similar to Kotlin
   - Suggests symbol and import verification

**Usage:**
```bash
# Preview fixes (no changes)
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

---

### Scripts

#### **build-monitor.py**
Monitors GitHub Actions workflow runs. Polls every 15–30 seconds until complete.

**Usage:**
```bash
python scripts/build-monitor.py \
  --repo OWNER/REPO \
  --workflow build.yml \
  --run-id 12345678 \
  --github-token $GITHUB_TOKEN \
  --poll-interval 20
```

**Output:**
- Prints live status (queued → in_progress → completed)
- Returns exit code 0 on success, 1 on failure
- Writes logs to `build-logs/run-{id}.log`

#### **error-parser.py**
Extracts meaningful errors from Android build logs.

**Usage:**
```bash
python scripts/error-parser.py \
  --log-file build-logs/run-12345.log \
  --output-format json
```

**Detects:**
- Gradle sync failures
- Missing SDK components
- Kotlin/Java compilation errors
- Resource conflicts
- Manifest merge issues
- Dependency resolution problems

**Output:** Structured JSON with error type, line number, suggestion

#### **discord-notifier.py**
Posts build status updates to Discord webhook.

**Usage:**
```bash
python scripts/discord-notifier.py \
  --webhook-url $DISCORD_WEBHOOK_URL \
  --status success|failure \
  --repo OWNER/REPO \
  --run-id 12345 \
  --error-summary "Optional error details"
```

**Output:** Formatted embed posted to Discord with:
- Project name & repo link
- Build status (✅ or ❌)
- Elapsed time
- Error summary (if failed)
- Retry count
- Link to GitHub Actions run

---

### References

#### **github-actions-template.yaml**
Complete CI/CD workflow for building Android APK with GitHub Actions.

**Includes:**
- Android SDK setup
- Gradle caching
- Build variant selection
- APK artifact upload
- Failure notifications

#### **android-manifest-guide.md**
Standard AndroidManifest.xml patterns and customization rules.

**Covers:**
- Permissions (camera, location, contacts, etc.)
- Activities and launch modes
- Services and broadcast receivers
- Intent filters
- App metadata (version, SDK targets)

#### **gradle-config.md**
Gradle build configuration for Android projects.

**Covers:**
- Kotlin/Java setup
- Dependency management
- Build variants (debug/release)
- ProGuard/R8 configuration
- Build feature flags

#### **clarification-questions.md**
7-8 targeted questions to ask when starting a new app project.

**Topics:**
- App name and purpose
- Target Android versions
- Key features
- Data persistence (database, preferences)
- Network requirements
- UI complexity
- Authentication needs

---

### Assets

#### **basic-android-app/**
Complete Kotlin starter template with:
- Modern Gradle Kotlin DSL (build.gradle.kts)
- Single Activity with ViewModel
- Basic layout XML
- Resource strings
- Unit & instrumentation test stubs
- .gitignore configured

**Ready to customize and push.**

---

## Complete Workflow Example

### Step 1: Prepare Environment
```bash
export GITHUB_TOKEN="ghp_xxxxx"
export DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/xxx/yyy"
cd /path/to/android/project
```

### Step 2: Answer Clarification Questions
Agent asks about app name, features, target SDK, UI complexity, etc.

### Step 3: Generate & Push Code
Agent creates project → commits to GitHub → pushes → Actions triggers first build

### Step 4: Automatic Build Monitoring with Error Recovery
```
# Agent invokes:
python scripts/error-recovery.py \
  --repo owner/repo \
  --github-token $GITHUB_TOKEN \
  --discord-webhook $DISCORD_WEBHOOK_URL \
  --project-dir . \
  --run-id 12345 \
  --max-retries 3
```

### Step 5: Real-Time Status
- **Console:** Live build status, error parsing, fix generation
- **Discord:** Milestones, build results, escalations
- **Files:** Recovery logs, error reports, fix suggestions

### Step 6: Handle Outcomes

**If Build Succeeds (Attempt 1-3):**
- ✅ Discord notification with elapsed time
- ✅ APK artifact ready
- Done!

**If Auto-Recovery Fails After 3 Retries:**
- 🔴 Discord escalation with full context
- 📋 Retry history showing what was tried
- 🔗 Links to GitHub Actions logs
- Next steps for manual debugging

---

## Automatic Error Recovery Pipeline

The skill now includes a **complete error recovery loop** that runs automatically:

### Error Detection (Automatic)
- Monitors GitHub Actions for build completion
- Captures full logs on failure
- Parses logs to identify error type and root cause

### Error Classification
| Error Type | Detection | Auto-Fix? | Confidence |
|-----------|-----------|-----------|-----------|
| **Gradle Sync** | `Failed to resolve`, `sync failed` | ✅ Yes | 80% |
| **Dependency Conflicts** | `version conflict`, `No solution` | ✅ Yes | 85% |
| **Missing SDK** | `compileSdkVersion not installed` | ✅ Yes | 90% |
| **AndroidX Issues** | `androidx` version errors | ✅ Yes | 85% |
| **Manifest Merge** | `Manifest merger failed` | ⚠️ Alert | 75% |
| **Resource Conflicts** | `Duplicate resources` | ⚠️ Alert | 60% |
| **Kotlin Syntax** | `unresolved reference`, `Type mismatch` | ❌ Manual | 30% |
| **Java Syntax** | `cannot find symbol`, `package not found` | ❌ Manual | 30% |

### Automatic Fixes Applied
✅ **High Confidence (Auto-applied)**
- Update Gradle dependency versions
- Enable AndroidX and Jetifier
- Synchronize SDK versions (compileSdk, targetSdk)
- Refresh Gradle dependencies

⚠️ **Medium Confidence (Logged, Requires Review)**
- Manifest merge conflict detection
- Resource duplication warnings
- Permission conflicts

❌ **Low Confidence (Manual Only)**
- Kotlin/Java syntax and logic errors
- Custom business logic issues

### Retry Logic
```
Build Attempt 1: Monitor → Fails
↓
Error Detection: Parse logs → Identify 2 Gradle errors
↓
Auto-Fix Phase 1: Update deps, enable AndroidX → Commit
↓
Build Attempt 2: Monitor → Still fails, different error
↓
Error Detection: Parse logs → Identify 1 SDK version error
↓
Auto-Fix Phase 2: Update compileSdk → Commit
↓
Build Attempt 3: Monitor → Success!
↓
✅ Build Succeeded (after 2 auto-retries)
```

**If all 3 retries fail:**
- Full error logs sent to Discord
- Retry history (what was tried, outcomes)
- Actionable next steps for manual debugging
- Build halts, awaiting human intervention

### Escalation to Discord
When auto-recovery exhausts retries:

```
🔴 Build Recovery Failed - Escalation

Run #12345678 in owner/repo

Recovery Summary:
  ❌ Attempt 1: gradle_sync (2 errors, 1 fix applied)
  ❌ Attempt 2: missing_sdk (1 error, 1 fix applied)
  ❌ Attempt 3: kotlin_compilation (1 error, 0 fixes - manual required)

Final Error Log:
[Error context from build log]

Next Steps:
1. Review logs above
2. Debug locally
3. Commit and push fixes
4. Re-run build
```

---

## Output & Deliverables

When complete, you get:
1. ✅ GitHub repo with full Android project
2. ✅ GitHub Actions workflow (auto-triggers on push)
3. ✅ Discord channel with build history & links
4. ✅ APK artifact (downloadable from Actions)
5. ✅ Build logs & error summaries (archived)
6. ✅ Ready-to-extend codebase (Kotlin, modern patterns)

---

## Examples

### Example: "Build a todo list app"
1. Agent asks: target SDK, features (due dates? repeating?), data storage (SQLite? Cloud?), UI complexity
2. User answers → agent generates TodoListApp with SQLite, Room persistence, Material Design
3. Repo created: `github.com/user/TodoListApp`
4. Actions runs, builds successful APK
5. Discord logs milestone: "✅ Build #1 successful"
6. User tests, requests dark mode → feedback from Discord
7. Agent modifies theme, commits, builds again
8. Discord logs: "✅ Build #2 successful - dark mode added"

---

## Auto-Recovery Limitations

The error recovery system is powerful but has important limitations:

### ✅ What It CAN Fix
- Dependency version conflicts and outdated libraries
- AndroidX/Jetpack compatibility issues
- SDK version mismatches (compileSdk, targetSdk, buildTools)
- Build property flags (enable AndroidX, Jetifier, etc.)
- Missing Android SDK components
- Gradle sync failures caused by configuration issues

### ❌ What It CANNOT Fix (Requires Manual Intervention)
- **Logic errors** in Kotlin/Java code (syntax, type mismatches, algorithm issues)
- **Custom business logic** problems
- **Complex manifest conflicts** requiring domain knowledge
- **Resource deduplication** (which duplicate to remove)
- **Build tool version conflicts** beyond standard patterns
- **Native code (C/C++)** compilation issues
- **Custom Gradle tasks** with errors

### Design Philosophy
The system is **conservative by design**:
- Only applies fixes with **80%+ confidence**
- Medium-confidence fixes (60-80%) are logged and alerted, not auto-applied
- Low-confidence fixes (<60%) are escalated to Discord immediately
- All changes are committed with traceable messages
- Full logs preserved for debugging

### Retry Limits
- **Max 3 retries** per build (configurable)
- **Same error type** doesn't retry more than 3x
- **Different error types** in sequence count separately
- **Timeout** (>30 min per build) escalates immediately

## General Limitations

- **Native Android only** — no cross-platform frameworks
- **No Play Store publishing** — builds APK, doesn't submit to Google Play
- **Requires GitHub** — relies on GitHub Actions for CI/CD
- **No obfuscation by default** — ProGuard/R8 must be configured manually for release builds
- **Kotlin preferred** — Java support available but templates use Kotlin

---

## Troubleshooting

### Build hangs for >30 minutes
- Build monitor will timeout and escalate
- Check GitHub Actions runner status
- Review logs for stuck tasks (Gradle cache, SDK downloads)
- Increase `--max-wait` in build-monitor.py if needed

### Auto-recovery doesn't apply fixes
- Check confidence level in `.fixes-report-*.json`
- If <80%, manual review required
- Review `.error-report-*.json` for error classification
- Some errors (syntax, logic) cannot be auto-fixed

### Discord escalation appears but shouldn't
- Review retry history in `.error-recovery-history.json`
- Check if all 3 retries were actually attempted
- Verify error-parser correctly identified errors
- Confirm auto-fix.py had applicable strategies

### Fix was applied but build still fails
- Same error: Already retried 3x, needs manual investigation
- Different error: Error-recovery retries automatically (up to 3 max-retries total)
- Review logs to understand new error type
- Consider if fix is incompatible with project structure

### "Gradle sync failed" keeps repeating
- Usually indicates dependency version mismatch
- error-parser identifies specific artifact
- auto-fix.py updates to recommended version
- If still fails, may need manual gradle.properties tweaks

### Manifest merge conflicts not auto-fixed
- Design decision: Manifest conflicts require domain knowledge
- Logged and alerted, escalated after retries
- Check `.error-report-*.json` for conflicting attribute
- Apply tools:replace or tools:ignore manually
- Commit and push to retrigger build

### Discord webhook returns 401/403
- Verify webhook URL is correct and not expired
- Create new webhook from Discord server
- Re-export `DISCORD_WEBHOOK_URL`
- Check Discord channel still exists and webhook not revoked

### APK artifact missing
- Check GitHub Actions run tab → workflow logs
- Verify build.gradle.kts has `assembleDebug` task
- Confirm build succeeded (green checkmark)
- Artifact stored in `app/build/outputs/apk/debug/`

---

## Next Steps

1. **Read the skill SKILL.md** (you're here!)
2. **Run the clarification questions** from `references/clarification-questions.md`
3. **Review the template files** to understand customization
4. **Provide tokens** for GitHub and Discord
5. **Start building** — let the agent orchestrate the rest!

---

**Status:** Production-ready | Last updated: 2026-03-25 | Compatible with: Android 14+ (API 34+)

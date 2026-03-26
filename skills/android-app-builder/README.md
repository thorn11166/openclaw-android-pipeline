# Android App Builder Skill

A comprehensive OpenClaw skill for orchestrating the complete Android development lifecycle — from idea clarification through GitHub integration, CI/CD automation, build monitoring, error detection, and Discord-tracked feedback loops.

## Overview

This skill automates:

1. **Idea Clarification** — Ask targeted questions to understand app requirements
2. **Code Generation** — Generate full Android project boilerplate with Kotlin, Gradle, manifests
3. **GitHub Integration** — Create repo, push code, initialize Git workflow
4. **CI/CD Pipeline** — Set up GitHub Actions for automatic APK building
5. **Build Monitoring** — Poll GitHub Actions API, track progress in real-time
6. **Error Detection & Parsing** — Extract meaningful errors from build logs
7. **Discord Tracking** — Create project channel, post milestones and status updates
8. **Feedback Loop** — Accept Discord messages, make changes, rebuild automatically

## Directory Structure

```
android-app-builder/
├── SKILL.md                              # This skill's documentation
├── README.md                             # Overview and quick start
├── scripts/
│   ├── build-monitor.py                  # Poll GitHub Actions for build status
│   ├── error-parser.py                   # Extract & categorize build errors
│   └── discord-notifier.py               # Post updates to Discord
├── references/
│   ├── github-actions-template.yaml      # CI/CD workflow for Android builds
│   ├── android-manifest-guide.md         # AndroidManifest.xml patterns
│   ├── gradle-config.md                  # Gradle configuration reference
│   └── clarification-questions.md        # 7-8 app requirement questions
└── assets/
    └── basic-android-app/                # Kotlin starter template
        ├── build.gradle.kts
        ├── AndroidManifest.xml
        ├── MainActivity.kt
        ├── activity_main.xml
        ├── strings.xml
        ├── colors.xml
        ├── themes.xml
        ├── .gitignore
        ├── settings.gradle.kts
        └── README.md
```

## Quick Start

### 1. Prerequisites

Before using this skill, ensure you have:

- **GitHub Personal Access Token** (Settings → Tokens)
  - Required permissions: `repo`, `workflow`, `gist`
  - Store as: `$GITHUB_TOKEN` environment variable

- **Discord Webhook URL** (per project)
  - Server → Channel → Integrations → Webhooks
  - Store as: `$DISCORD_WEBHOOK_URL`

- **Python 3.8+** (for scripts)
  - Required packages: `requests`
  - Install: `pip install requests`

### 2. Invoke the Skill

When you ask the agent to build an Android app:

```
"Build me a todo list app for Android"
```

The agent will:
1. Ask clarification questions (name, features, target SDK, etc.)
2. Generate project structure
3. Create GitHub repo
4. Set up GitHub Actions workflow
5. Trigger initial build
6. Create Discord channel
7. Monitor build progress
8. Report results to Discord

### 3. Watch Progress

Once started, the skill:
- Polls GitHub Actions every 15-30 seconds
- Posts status updates to Discord
- Detects and categorizes build errors
- Suggests fixes for common issues
- Retries up to 3 times on failure

### 4. Provide Feedback

React to Discord messages with:
- 👍 to approve and rebuild
- 💬 to add comments
- The agent fetches reactions and rebuilds

## File Descriptions

### SKILL.md

Complete skill documentation with:
- When to use this skill
- Integration requirements
- Full workflow breakdown
- File reference guide
- Error handling & retries
- Troubleshooting guide

### Scripts

#### build-monitor.py

**Monitors GitHub Actions builds in real-time**

```bash
python scripts/build-monitor.py \
  --repo owner/repo \
  --workflow build.yml \
  --run-id 12345 \
  --github-token $GITHUB_TOKEN \
  --poll-interval 20
```

**Features:**
- Polls every 15-30 seconds
- Captures full build logs
- Outputs exit code (0 = success, 1 = failure)
- Saves logs to `build-logs/run-{id}.log`

#### error-parser.py

**Extracts meaningful errors from Android build logs**

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

**Output:** Structured JSON with error type, file, line number, and suggestion

#### discord-notifier.py

**Posts build status updates to Discord**

```bash
python scripts/discord-notifier.py \
  --webhook-url $DISCORD_WEBHOOK_URL \
  --status success \
  --repo owner/repo \
  --run-id 12345 \
  --elapsed-minutes 5.5
```

**Sends:**
- ✅ Success embeds with build time
- ❌ Failure embeds with error summary
- 🚀 Milestone notifications
- ⚠️ Escalation alerts on max retries

### References

#### github-actions-template.yaml

Complete GitHub Actions workflow for Android builds:
- Android SDK setup
- Gradle caching (faster builds)
- Debug & release APK builds
- Unit test execution
- Lint checks
- Artifact uploads
- Customization guide

#### android-manifest-guide.md

Complete AndroidManifest.xml reference:
- Basic structure
- All common permissions
- Activities, services, receivers, providers
- Intent filters & deep linking
- API 31+ export requirements
- Manifest merging strategies
- Validation checklist

#### gradle-config.md

Complete Gradle configuration reference:
- Root & app-level build.gradle.kts
- Kotlin DSL syntax
- Dependency management
- Build variants & flavors
- Signing configuration
- ProGuard/R8 setup
- Testing configuration
- Performance tips

#### clarification-questions.md

7-8 targeted questions for app requirements:
1. App name & purpose
2. Target Android versions
3. Key features (MVP)
4. Data persistence method
5. Network & API needs
6. UI complexity
7. Authentication & permissions
8. Third-party integrations

Includes decision trees, scoring, and example conversations.

### Assets

#### basic-android-app/

Production-ready Kotlin template with:

- **build.gradle.kts** — Modern Kotlin DSL, all common dependencies
- **AndroidManifest.xml** — Material 3, proper permissions
- **MainActivity.kt** — Lifecycle-aware, view binding
- **activity_main.xml** — Material design layout
- **strings.xml** — Localization-ready
- **colors.xml** — Material 3 light & dark themes
- **themes.xml** — Complete theme configuration
- **.gitignore** — Gradle, Android, IDE, OS files
- **settings.gradle.kts** — Project configuration
- **README.md** — Complete customization guide

Ready to customize and push to GitHub.

## Integration Points

### GitHub

1. **Authentication:** Requires `GITHUB_TOKEN` with repo permissions
2. **Actions:** Reads run status from GitHub Actions API
3. **Artifacts:** Downloads APK files from build artifacts
4. **Logs:** Fetches build logs for error parsing

### Discord

1. **Webhooks:** Posts to Discord webhook URL
2. **Channels:** Create per-project channel (optional)
3. **Embeds:** Formatted status messages with links
4. **Reactions:** (Optional) Monitor reactions for feedback

### Environment Variables

```bash
export GITHUB_TOKEN="ghp_xxxxx"
export DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/xxx/yyy"
export ANDROID_SDK_VERSION="34"          # Optional
export BUILD_TOOLS_VERSION="34.0.0"      # Optional
```

## Workflow Example

### Scenario: Build a Todo List App

**Step 1: User Request**
```
"Build an Android todo list app"
```

**Step 2: Clarification**
Agent asks:
- Name: "TodoList"
- Target SDK: API 24+
- Features: Create, edit, delete, due dates
- Storage: SQLite locally
- UI: List + detail screens
- Auth: None
- Integrations: None

**Step 3: Code Generation**
Agent creates:
- Project skeleton with Kotlin
- SQLite Room persistence setup
- Two-screen navigation
- Material 3 UI
- GitHub-ready structure

**Step 4: GitHub Integration**
- Create repo: `github.com/user/TodoList`
- Push initial code
- Init `.github/workflows/build.yml`

**Step 5: GitHub Actions**
Workflow runs:
1. Checkout code
2. Set up Android SDK
3. Run Gradle build
4. Compile Kotlin to APK
5. Upload artifact

**Step 6: Monitoring**
Agent:
- Polls Actions API every 20s
- Fetches logs on completion
- Parses for errors
- Posts to Discord: "✅ Build #1 successful"

**Step 7: User Feedback (Discord)**
User: "Add dark mode support"

Agent:
- Fetches message from Discord
- Modifies theme configuration
- Commits and pushes
- Build #2 triggers automatically
- Posts: "✅ Build #2 successful - dark mode added"

**Step 8: Download & Test**
APK available from GitHub Actions artifacts.

## Error Handling

| Scenario | Response |
|----------|----------|
| Build timeout (>30 min) | Capture logs, post to Discord, pause |
| Gradle sync fails | Identify missing deps, suggest fix, retry |
| Compilation error | Pinpoint file/line, suggest fix, retry |
| Max retries exceeded (3) | Post full logs to Discord, escalate |
| Network error during monitor | Wait 30s, retry |
| Invalid webhook | Report error, pause Discord updates |

## Performance

- **Build monitoring:** 15-30 second polling interval
- **Error parsing:** <1s per 1000 lines of logs
- **Discord webhooks:** <500ms per message
- **GitHub API:** Rate limited to 60 req/min (unauthenticated) or 5000/hr (token-based)

## Limitations

- **Native Android only** — no cross-platform frameworks (Flutter, React Native)
- **No Play Store publishing** — builds APK, doesn't submit to Google Play
- **Requires GitHub** — relies on GitHub Actions for CI/CD
- **Local modifications only** — can't modify remote repos (only push)
- **Kotlin preferred** — templates use Kotlin, Java support available

## Troubleshooting

### Build Monitor Hangs

Check GitHub Actions runner:
```bash
# View workflow runs
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/runs
```

### Error Parser Misses Errors

Check log format is standard Gradle output. Add custom patterns if needed:

```python
# Modify error-parser.py PATTERNS dict
PATTERNS = {
    ErrorType.CUSTOM: [
        r"my custom error pattern",
    ]
}
```

### Discord Webhook Rejected

Verify webhook URL is correct:
```bash
curl -X POST $DISCORD_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"content":"Test"}'
```

### GitHub Token Expired

Create new token:
```bash
# GitHub Settings → Developer settings → Personal access tokens
# Re-export: export GITHUB_TOKEN="ghp_xxxxx"
```

## Future Enhancements

- [ ] Firebase Cloud Build integration (no local GitHub Actions needed)
- [ ] Play Store automated submission
- [ ] Sonarqube integration for code quality metrics
- [ ] Slack support (in addition to Discord)
- [ ] Dependency update automation (Dependabot wrapper)
- [ ] APK size analysis & recommendations
- [ ] Performance profiling integration
- [ ] Multi-variant builds (different architectures)

## Contributing

To improve this skill:

1. Test scripts locally with real Android projects
2. Add new error patterns to `error-parser.py`
3. Extend clarification questions for new use cases
4. Update references with new techniques
5. Expand template assets with additional examples

## License

MIT

## Support

For issues, questions, or feature requests:
1. Check SKILL.md troubleshooting section
2. Review reference docs for your specific question
3. Test scripts independently to isolate issues
4. File issue with detailed logs and steps to reproduce

---

**Status:** Production-ready | Last updated: 2026-03-25 | Tested with Android 14+ (API 34+), GitHub Actions, Python 3.8+

# Android App Builder Skill - Implementation Checklist

Use this checklist when implementing the android-app-builder skill in an agent.

---

## Pre-Implementation Setup

### Environment & Tokens

- [ ] **GitHub Token Ready**
  - [ ] Navigate to https://github.com/settings/tokens
  - [ ] Create Fine-grained Personal Access Token
  - [ ] Grant: Contents (r/w), Actions (r), Workflows (r/w)
  - [ ] Copy token → `export GITHUB_TOKEN="ghp_xxxxx"`
  - [ ] Test token: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`

- [ ] **Discord Webhook Ready**
  - [ ] Join Discord server with admin access
  - [ ] Create dedicated channel (e.g., #builds-todolist)
  - [ ] Server Settings → Integrations → Webhooks
  - [ ] Create webhook, copy URL
  - [ ] `export DISCORD_WEBHOOK_URL="https://discordapp.com/api/webhooks/..."`
  - [ ] Test webhook: `curl -X POST $DISCORD_WEBHOOK_URL -H "Content-Type: application/json" -d '{"content":"Test"}'`

- [ ] **Python Dependencies**
  - [ ] Python 3.8+ installed
  - [ ] `pip install requests`
  - [ ] Test: `python3 -c "import requests; print(requests.__version__)"`

- [ ] **Android SDK (Optional for local testing)**
  - [ ] Android SDK 34 installed
  - [ ] Build Tools 34.0.0 installed
  - [ ] `export ANDROID_HOME="/path/to/android-sdk"`

---

## Phase 1: Idea Clarification

When user requests an Android app:

- [ ] **Ask 7-8 Clarification Questions**
  - [ ] App name & purpose
  - [ ] Target Android versions (min SDK)
  - [ ] Key features (top 3-5)
  - [ ] Data persistence (none/SQLite/Firebase/REST API)
  - [ ] Network requirements (offline/API/real-time)
  - [ ] UI complexity (simple/medium/complex)
  - [ ] Auth & permissions needed
  - [ ] Third-party integrations (Firebase/Analytics/Maps/etc.)

- [ ] **Generate Spec Document**
  - [ ] Summarize answers
  - [ ] Show back to user for confirmation
  - [ ] Example format:
    ```
    App: TodoList
    SDK: API 24-34
    Features: Create, edit, delete, due dates
    Storage: SQLite (Room)
    Network: None
    UI: 2 screens
    Auth: None
    Integrations: None
    ```

---

## Phase 2: Code Generation

### Generate Project Structure

- [ ] **Customize AndroidManifest.xml**
  - [ ] Set package name to app ID
  - [ ] Add required permissions
  - [ ] Set target SDK version
  - [ ] Configure app metadata

- [ ] **Customize build.gradle.kts**
  - [ ] Set namespace & applicationId
  - [ ] Configure SDK versions
  - [ ] Add required dependencies based on features
  - [ ] SQLite? Add Room dependencies
  - [ ] REST API? Add Retrofit + OkHttp
  - [ ] Firebase? Add Firebase BOM

- [ ] **Generate Activity Files**
  - [ ] Create MainActivity.kt
  - [ ] If multi-screen: Create additional Activity files
  - [ ] If REST API: Create data models & API service interface
  - [ ] If SQLite: Create Room entities & DAOs

- [ ] **Generate Layout Files**
  - [ ] activity_main.xml with MaterialToolbar
  - [ ] Additional screen layouts if needed
  - [ ] Fragment layouts if using Navigation Component

- [ ] **Generate Resource Files**
  - [ ] strings.xml with app strings
  - [ ] colors.xml with Material 3 palette
  - [ ] themes.xml (light + dark)

- [ ] **Bundle Template Assets**
  - [ ] Copy from `assets/basic-android-app/`
  - [ ] Customize package names
  - [ ] Ensure .gitignore is present

---

## Phase 3: GitHub Integration

### Create & Populate Repository

- [ ] **Create Remote Repository**
  ```bash
  curl -X POST https://api.github.com/user/repos \
    -H "Authorization: token $GITHUB_TOKEN" \
    -d '{"name":"AppName","private":false,"auto_init":true}'
  ```
  - [ ] Verify repo created at github.com/user/AppName

- [ ] **Initialize Local Git**
  - [ ] `cd /path/to/project`
  - [ ] `git init`
  - [ ] `git add .`
  - [ ] `git config user.name "Your Name"`
  - [ ] `git config user.email "your@email.com"`
  - [ ] `git commit -m "Initial commit: Android project scaffold"`

- [ ] **Add Remote & Push**
  - [ ] `git remote add origin https://github.com/user/AppName.git`
  - [ ] `git branch -M main`
  - [ ] `git push -u origin main`
  - [ ] Verify files on GitHub

---

## Phase 4: GitHub Actions Setup

### Create CI/CD Workflow

- [ ] **Create Workflow Directory**
  - [ ] `mkdir -p .github/workflows`

- [ ] **Copy & Customize Workflow**
  - [ ] Copy from `references/github-actions-template.yaml`
  - [ ] Rename to `.github/workflows/build.yml`
  - [ ] Customize SDK versions to match project
  - [ ] Set correct API levels
  - [ ] Enable signing if needed (optional)

- [ ] **Commit & Push Workflow**
  - [ ] `git add .github/workflows/build.yml`
  - [ ] `git commit -m "Add GitHub Actions CI/CD pipeline"`
  - [ ] `git push origin main`
  - [ ] Check GitHub → Actions → Workflows tab
  - [ ] Verify workflow is visible and enabled

---

## Phase 5: Build Monitoring Loop

### Monitor GitHub Actions

- [ ] **Trigger First Build**
  - [ ] Workflow auto-triggers on push
  - [ ] Check GitHub Actions for run ID
  - [ ] Example run URL: `github.com/user/AppName/actions/runs/123456789`

- [ ] **Start Build Monitor Script**
  ```bash
  python scripts/build-monitor.py \
    --repo user/AppName \
    --run-id 123456789 \
    --github-token $GITHUB_TOKEN \
    --poll-interval 20
  ```
  - [ ] Monitor outputs status updates
  - [ ] Saves logs to `build-logs/run-123456789.log`

- [ ] **Monitor Output Handling**
  - [ ] Script exits with 0 on success
  - [ ] Script exits with 1 on failure
  - [ ] Check `build-logs/` for full logs

---

## Phase 6: Error Detection & Parsing

### Parse Build Errors (if build failed)

- [ ] **Run Error Parser**
  ```bash
  python scripts/error-parser.py \
    --log-file build-logs/run-123456789.log \
    --output-format json
  ```
  - [ ] Identifies error type (Gradle, Kotlin, manifest, etc.)
  - [ ] Suggests fix
  - [ ] Outputs JSON with structured errors

- [ ] **Analyze Results**
  - [ ] Error type identified? → Suggest fix
  - [ ] File & line number? → Show code location
  - [ ] Unknown error? → Post raw logs to Discord

- [ ] **Apply Fixes**
  - [ ] Make changes to code based on error
  - [ ] Commit: `git commit -am "Fix: [error description]"`
  - [ ] Push: `git push origin main`
  - [ ] Rebuild auto-triggers from push

---

## Phase 7: Discord Tracking

### Create Channel & Post Updates

- [ ] **Create Discord Channel** (optional but recommended)
  - [ ] Server → Create Channel → #builds-appname
  - [ ] Set topic: "Build pipeline for AppName"
  - [ ] Copy channel ID (right-click channel)

- [ ] **Post Initial Milestone**
  ```bash
  python scripts/discord-notifier.py \
    --webhook-url $DISCORD_WEBHOOK_URL \
    --milestone "Repository Created" \
    --milestone-description "github.com/user/AppName"
  ```
  - [ ] Message appears in Discord channel

- [ ] **Post Build Status on Completion**
  ```bash
  # On success
  python scripts/discord-notifier.py \
    --webhook-url $DISCORD_WEBHOOK_URL \
    --status success \
    --repo user/AppName \
    --run-id 123456789 \
    --elapsed-minutes 5.5 \
    --run-url https://github.com/user/AppName/actions/runs/123456789
  ```
  - [ ] ✅ Success embed posted with build time

- [ ] **Post Build Status on Failure**
  ```bash
  python scripts/discord-notifier.py \
    --webhook-url $DISCORD_WEBHOOK_URL \
    --status failure \
    --repo user/AppName \
    --run-id 123456789 \
    --error-summary "Gradle sync failed: missing dependency com.example:lib:1.0" \
    --retry-count 1
  ```
  - [ ] ❌ Failure embed posted with error summary

---

## Phase 8: Feedback Loop (Optional)

### Accept Discord Feedback & Rebuild

- [ ] **Monitor Discord Channel**
  - [ ] Watch for user reactions (👍 approve, 💬 comment)
  - [ ] Check for text messages with change requests

- [ ] **On User Feedback**
  - [ ] Fetch message from Discord
  - [ ] Parse requested changes
  - [ ] Modify code accordingly
  - [ ] Commit & push (auto-triggers build)

- [ ] **Report Progress**
  - [ ] Post update: "Implementing dark mode..."
  - [ ] Post when build starts
  - [ ] Post when complete with success/failure status

---

## Post-Build Validation

### Verify Deliverables

- [ ] **GitHub Repository**
  - [ ] Repo exists and is public/private as intended
  - [ ] Code structure matches app requirements
  - [ ] All files present (manifest, gradle, sources, resources)
  - [ ] .gitignore configured correctly

- [ ] **GitHub Actions Workflow**
  - [ ] Workflow file exists in `.github/workflows/build.yml`
  - [ ] Workflow is enabled
  - [ ] Workflow runs on push to main/develop
  - [ ] Build tasks execute in correct order

- [ ] **APK Artifact**
  - [ ] APK file generated in build outputs
  - [ ] Artifact downloadable from GitHub Actions
  - [ ] APK is debuggable (if debug build)
  - [ ] APK is not debuggable (if release build)

- [ ] **Discord Channel**
  - [ ] Channel created for project
  - [ ] Build milestones logged
  - [ ] Success/failure messages posted
  - [ ] Links to GitHub Actions runs provided

- [ ] **Error Logs**
  - [ ] Logs saved to `build-logs/` directory
  - [ ] Errors properly categorized
  - [ ] Suggestions accurate and actionable

---

## Troubleshooting Checklist

### Build Fails on First Run

- [ ] Check AndroidManifest.xml is valid XML
- [ ] Check build.gradle.kts syntax (Kotlin DSL)
- [ ] Verify all dependencies have valid versions
- [ ] Check SDK versions match what's installed
- [ ] Review full logs in `build-logs/`

### Monitor Script Times Out

- [ ] Check GitHub Actions runner status (github.com/status)
- [ ] Verify GITHUB_TOKEN is valid (not expired)
- [ ] Check if Actions are enabled on repository
- [ ] Increase `--max-wait` parameter (default 30 min)

### Discord Webhook Fails

- [ ] Verify webhook URL is correct (copy-paste again)
- [ ] Check webhook hasn't been deleted
- [ ] Verify bot has permissions in channel
- [ ] Test webhook manually with curl

### Error Parser Doesn't Identify Error

- [ ] Check log file exists at specified path
- [ ] Review raw log file for error patterns
- [ ] Consider adding custom error pattern
- [ ] Check error format is standard Gradle output

### GitHub Token Rejected

- [ ] Verify token is not expired (GitHub settings)
- [ ] Check token has required permissions (repo, workflow)
- [ ] Try creating new token and re-exporting
- [ ] Test with: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`

---

## Success Criteria

By the end, you should have:

- ✅ GitHub repo with full Android project code
- ✅ GitHub Actions workflow building APK on every push
- ✅ Discord channel tracking build progress
- ✅ Build monitor polling and logging status
- ✅ Error parser identifying issues automatically
- ✅ First successful build documented
- ✅ APK artifact downloadable from Actions
- ✅ Ready for user feedback & iterations

---

## Next Steps for User

Once skill completes:

1. **Download APK** from GitHub Actions
2. **Install on device/emulator** and test
3. **Request changes** via Discord (skill rebuilds automatically)
4. **Iterate** until feature-complete
5. **Prepare for Play Store** (signing, obfuscation, testing)

---

**Checklist Status:** ✅ Complete | **Last Updated:** 2026-03-25

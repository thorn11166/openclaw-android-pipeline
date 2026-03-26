# Quick Start: Android App Builder

## What You Have

A fully automated Android app development pipeline:
1. **Code generation** (DeepSeek V3)
2. **GitHub automation** (repo creation, push, CI/CD)
3. **Build monitoring** (GitHub Actions + Discord notifications)
4. **Error recovery** (auto-fix.py for common issues)

## How to Use

### Step 1: Trigger the Skill

In Discord or CLI:
```
@zoidberg Build an Android app called MyApp
- Purpose: A task management app
- Key features: Create, edit, delete tasks; local SQLite storage; offline-capable
- UI complexity: Simple (2-3 screens)
- Permissions needed: None
```

### Step 2: Answer Clarification Questions

The skill will ask ~7-8 targeted questions:
- Target SDK version
- Data storage strategy
- Network requirements
- UI framework (Material Design 3)
- etc.

### Step 3: Watch It Build

1. Code auto-generated in Kotlin
2. GitHub repo created at `github.com/[username]/MyApp`
3. GitHub Actions builds automatically
4. Status posted to Discord `#bot-logs` channel
5. APK artifact available if successful

## Configuration

**Model (Primary):** DeepSeek V3  
**Model (Fallback):** Claude Haiku  
**GitHub Token:** Stored in `openclaw.json`  
**Discord Webhook:** Stored as GitHub secret  

To verify:
```bash
gh secret list --repo [your-repo]
```

## What to Expect

### Success (✅)
- Build completes in ~2-3 minutes
- APK ready for testing
- Discord notification with download link

### Failure (❌)
- Build fails with error message
- Error parsed automatically
- Discord notified with error type
- You can:
  - Manually fix code + push (triggers rebuild)
  - Invoke auto-fix.py script
  - Ask for simplified version

## Common Issues & Fixes

### Gradle Errors
**Cause:** Missing or mismatched dependencies  
**Fix:** Run auto-fix.py (detects + fixes automatically)

### AndroidX Errors
**Cause:** `android.useAndroidX` flag missing or wrong  
**Fix:** Check `gradle.properties` has both:
```properties
android.useAndroidX=true
android.enableJetifier=true
```

### Manifest Errors
**Cause:** Missing permissions or activities  
**Fix:** auto-fix.py validates + fixes AndroidManifest.xml

### Resource Errors
**Cause:** Missing strings, colors, or layouts  
**Fix:** auto-fix.py checks all res/ directories

## Tips for Success

1. **Keep it simple** — Fewer dependencies = faster builds
2. **Avoid Jetpack Compose** — Use XML layouts (fewer conflicts)
3. **Minimal APIs** — Reduces dependency resolution issues
4. **Watch Discord** — Real-time build status + errors
5. **Use local storage** — SQLite (Room) works great, Firebase adds complexity

## Example: Simple Todo App

```
@zoidberg Build an Android app called TodoList
- Purpose: Simple task manager
- Target SDK: Android 8+ (API 26+)
- Features: Add/edit/delete tasks, local SQLite, dark mode
- UI: 2 screens (list + detail)
- Permissions: None
- Storage: Room + SQLite
- No external APIs
```

**Expected:** ✅ Builds successfully in 2-3 min

## Example: Complex App

```
@zoidberg Build an Android app called TradeTracker
- Purpose: Stock trading app
- Features: Real-time quotes, portfolio tracking, news feed, push notifications
- Storage: Firebase Realtime DB + local cache
- APIs: Alpha Vantage (stocks), Firebase (auth + messaging)
- UI: 4+ screens (complex)
- Auth: Google OAuth
```

**Expected:** ❌ May fail (dependency complexity)  
**Solution:** Simplify or use auto-fix.py

## Troubleshooting

### No Discord notification?
- Check webhook is valid: `curl -X POST [webhook-url] -d '{"content":"test"}'`
- Verify `#bot-logs` channel exists
- Check GitHub secret is set correctly

### Builds keep failing?
- Check `#bot-logs` Discord for error type
- Run error-parser.py on build logs
- Invoke auto-fix.py with error report
- If still stuck, simplify project scope

### Want to retry?
```bash
git commit --allow-empty -m "Retry build"
git push
```

## Files to Know

- `android-app-builder/SKILL.md` — Full documentation
- `android-app-builder/scripts/error-parser.py` — Understand errors
- `android-app-builder/scripts/auto-fix.py` — Automatic fixes
- `torbox-downloader/` — Reference implementation (has build issues, but shows structure)

## Next Steps

1. **Try a simple app** first (Calculator, Notes, Todo)
2. **Watch it build** on Discord
3. **Study error patterns** if it fails
4. **Gradually increase complexity** as you learn

---

**Ready?** Trigger the skill and let it build! 🚀

# Session Changes — 2026-03-26

All changes were committed to branch: `claude/review-and-fix-repo-2G2gH`

---

## Commit 1 — Fix bugs in build pipeline scripts
**Files:** `skills/android-app-builder/scripts/`

### error-recovery.py
- **Line 308:** Fixed error parser failure check: `if result.returncode != 0 and not result.stdout` → `if result.returncode != 0`
  — the original swallowed errors silently when the parser produced any stdout output
- **Line 243:** Fixed retry count not appearing in Discord notifications: positional `attempt` → keyword `retry=attempt`
  — `_notify_discord` reads `retry` from `**kwargs`, so passing it positionally meant it was always 0
- **Lines 591–598:** Added try/except in `_log()` around the file write
  — an unwritable log path would previously crash the entire orchestrator

### auto-fix.py
- **Line 191:** Fixed inverted AndroidX detection: `if "androidx" not in message.lower()` → `if "androidx" in message.lower()`
  — was suggesting enabling AndroidX for errors that had nothing to do with AndroidX
- **Line 348:** Fixed fragile artifact matching in `_get_androidx_updates`: `key.startswith(...)` → `key == artifact`
  — startswith could return wrong library version for similarly-named packages (e.g. `androidx.appcompat` matching `androidx.appcompat-extras`)
- **Lines 421–427:** Added `logger.warning(...)` when dependency pattern not found in `_apply_dependency_update`
  — previously returned `False` silently, hiding bugs in pattern matching

### build-monitor.py
- **Lines 62–85:** Fixed `get_run_logs()` to handle GitHub's binary ZIP response
  — was calling `response.text` on a binary ZIP file, producing garbled output; replaced with `zipfile.ZipFile` extraction

### discord-notifier.py
- **Lines 253–287:** Added `--project-name` CLI argument (default `"Project"`)
  — `send_milestone()` was receiving the milestone text as both `project_name` and `milestone` arguments

---

## Commit 2 — Add .gitignore
**File:** `.gitignore` (new)

- Repository had no `.gitignore`, leaving `__pycache__/`, build outputs, logs, and IDE files untracked
- Added patterns for: Python bytecode, virtual environments, runtime log/report files, Android build outputs, IDE configs, OS files

---

## Commit 3 — Fix build-blocking errors in basic-android-app template
**Files:** `skills/android-app-builder/assets/basic-android-app/`

### activity_main.xml
- **Line 11:** Fixed typo in MaterialToolbar class path: `appbarwith` → `appbar`
  — `com.google.android.material.appbarwith.MaterialToolbar` does not exist; AAPT2 would reject the layout on every generated app

### themes.xml
- **Line 4:** Changed theme parent from `Theme.MaterialComponents.Light` → `Theme.MaterialComponents.Light.NoActionBar`
  — calling `setSupportActionBar()` with a non-NoActionBar theme throws `IllegalStateException` at runtime

### build.gradle.kts
- **Line 54:** Replaced deprecated `packagingOptions { }` with `packaging { }`
  — `packagingOptions` was deprecated in AGP 7.0 and will become an error in future AGP versions

### gradle.properties (new)
- Created missing file with: AndroidX/Jetifier flags, JVM heap allocation, parallel build and caching settings, Kotlin incremental compilation

### gradle/wrapper/gradle-wrapper.properties (new)
- Created missing file pinning Gradle 8.4
  — without this, `./gradlew` cannot bootstrap and the build cannot run

### proguard-rules.pro (new)
- Created missing file referenced in `build.gradle.kts` release build configuration
  — release builds would fail with "file not found" without it

### Launcher icon resources (all new)
- `res/drawable/ic_launcher_background.xml` — solid primary-color rectangle
- `res/drawable/ic_launcher_foreground.xml` — white circle vector (placeholder)
- `res/mipmap-anydpi-v26/ic_launcher.xml` — adaptive icon for API 26+ (uses above drawables)
- `res/mipmap-anydpi-v26/ic_launcher_round.xml` — adaptive round icon for API 26+
- `res/mipmap-anydpi/ic_launcher.xml` — shape drawable fallback for API 24–25
- `res/mipmap-anydpi/ic_launcher_round.xml` — oval shape fallback for API 24–25
  — `AndroidManifest.xml` references `@mipmap/ic_launcher` and `@mipmap/ic_launcher_round`; without these files the AAPT2 resource pass fails with "resource not found"

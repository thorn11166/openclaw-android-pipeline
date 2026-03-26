# Example Android App Projects

This directory contains **two complete Android app projects** generated during the OpenClaw Android Pipeline development. Both serve as reference implementations and learning examples.

## Projects Overview

### 1. TorBox Downloader (Complex Example)

**Directory:** `torbox-downloader/`  
**Builds Attempted:** 15  
**Final Status:** Builds fail (dependency/resource issues)  
**Learning Level:** High (shows real-world complexity)

**What It Is:**
- Magnet/torrent link interceptor for Android
- Sends links to TorBox cloud service for downloading
- Real-time status monitoring
- Auto-download to device when ready
- Full MVVM architecture with Room database

**Technology Stack:**
- Kotlin + MVVM + Room ORM
- Retrofit + OkHttp for networking
- WorkManager for background tasks
- Jetpack Compose (refactored to XML)
- Material Design 3

**Why It's Useful:**
- **Shows complexity:** Real feature-rich app with multiple concerns
- **Demonstrates refactoring:** Compose → XML simplification
- **Real dependencies:** Uses external APIs (TorBox)
- **Actual errors:** 15 builds show real problems

**Key Files:**
```
torbox-downloader/
├── .github/workflows/build.yml          [CI/CD configuration]
├── app/src/main/
│   ├── java/com/torbox/downloader/
│   │   ├── MainActivity.kt
│   │   ├── viewmodel/DownloadViewModel.kt
│   │   ├── data/TorBoxRepository.kt
│   │   ├── data/RoomEntities.kt
│   │   └── work/DownloadStatusWorker.kt
│   ├── res/layout/                      [5+ XML layouts]
│   ├── res/drawable/                    [11 vector drawables]
│   └── AndroidManifest.xml
├── build.gradle.kts                     [App config]
└── gradle/
    └── libs.versions.toml                [Dependency versions]
```

**Build Failures Breakdown:**
| Build | Issue | Root Cause |
|-------|-------|-----------|
| 1-7 | Gradle wrapper | Missing wrapper + gradle.properties |
| 8-11 | Retrofit dependency | converter-kotlinx-serialization 2.9.0 |
| 12-13 | Resource conflict | Launcher icon duplicates |
| 14 | AndroidX metadata | Missing gradle.properties flags |
| 15 | Complexity | Jetpack Compose overhead |

**What We Learned:**
- Complex generated apps need simplification
- Jetpack Compose adds 50+ transitive dependencies
- gradle.properties critical for AndroidX
- Real APIs increase dependency complexity

### 2. AnimeCalc (Simple Example)

**Directory:** `anime-calc/`  
**Builds Attempted:** 5  
**Final Status:** Builds fail (resource/config issues)  
**Learning Level:** Medium (shows config fundamentals)

**What It Is:**
- Simple calculator with anime aesthetic
- Calculation history (last 10 results)
- Dark mode support
- Settings screen (theme toggle, history clear)
- Anime-themed UI (vibrant colors, mascot character)

**Technology Stack:**
- Kotlin + MVVM + ViewModel
- XML layouts (no Compose)
- SharedPreferences (no database)
- Material Design 3 (anime-styled)
- Minimal dependencies (only AndroidX + Material)

**Why It's Useful:**
- **Shows simplicity:** Minimal feature set
- **Config focus:** Demonstrates gradle.properties importance
- **Resource management:** Shows resource file requirements
- **Quick iteration:** 5 builds identified key issues fast

**Key Files:**
```
anime-calc/
├── .github/workflows/build.yml          [CI/CD configuration]
├── app/src/main/
│   ├── java/com/animecalc/app/
│   │   ├── MainActivity.kt
│   │   ├── viewmodel/CalculatorViewModel.kt
│   │   ├── ui/CalculatorFragment.kt
│   │   ├── ui/HistoryFragment.kt
│   │   ├── ui/SettingsFragment.kt
│   │   └── utils/CalculatorEngine.kt
│   ├── res/layout/                      [5 XML layouts]
│   ├── res/drawable/                    [11 vector drawables]
│   ├── res/values/colors.xml
│   ├── res/values/strings.xml
│   └── AndroidManifest.xml
├── build.gradle.kts                     [App config]
├── gradle.properties                    [Gradle settings]
└── gradle/wrapper/
    ├── gradle-wrapper.jar
    └── gradle-wrapper.properties
```

**Build Failures Breakdown:**
| Build | Issue | Root Cause |
|-------|-------|-----------|
| 16 | Deprecation | GitHub Actions v3 → v4 |
| 17 | Wrapper | Missing gradle-wrapper.jar |
| 18 | Plugin | AGP 8.2 application failed |
| 19 | Resources | Missing layouts, drawables, colors |
| 20 | Config | gradle.properties AGP/JDK compat |

**What We Learned:**
- gradle.properties is CRITICAL for AGP compatibility
- All resource files must exist (layouts, drawables, colors)
- GitHub Actions need regular updates
- Simple apps still need complete resource setup

## Comparison Matrix

| Aspect | TorBox | AnimeCalc |
|--------|--------|-----------|
| **Complexity** | High (MVVM+Room+Retrofit) | Low (MVVM only) |
| **Dependencies** | 30+ libraries | 8 core libraries |
| **Features** | Real API integration | Basic calculator |
| **Builds** | 15 attempts | 5 attempts |
| **UI Framework** | Compose → XML | XML only |
| **Database** | Room SQLite | SharedPreferences |
| **Networking** | Retrofit + OkHttp | None |
| **Background** | WorkManager | None |

## How to Use These Examples

### For Learning
1. **Study TorBox** to understand MVVM + Room + Retrofit patterns
2. **Study AnimeCalc** to understand minimal viable setup
3. **Compare failures** to see how complexity creates issues
4. **Review fixes** to understand Android configuration

### For Testing
1. Clone either project locally
2. Run `./gradlew build` to reproduce errors
3. Apply fixes from `docs/BUILD_ANALYSIS.md`
4. Monitor build logs for error patterns

### For Improvement
1. These projects serve as **test cases** for pre-build validators
2. Use them to **validate** new skills before deployment
3. Reference them when **documenting** error patterns
4. Build **automated fixes** that handle these specific errors

## What's Included

### TorBox Downloader
✅ Complete Kotlin source code (10 files)  
✅ Room database entities + DAO  
✅ Retrofit API service interface  
✅ MVVM ViewModels  
✅ XML layouts + drawables  
✅ AndroidManifest.xml  
✅ Gradle configuration  
✅ GitHub Actions workflow  
✅ 15 build attempts documented  

### AnimeCalc
✅ Complete Kotlin source code (10 files)  
✅ MVVM architecture  
✅ Fragment-based UI  
✅ Calculator engine  
✅ Anime-themed UI resources  
✅ XML layouts + drawables  
✅ AndroidManifest.xml  
✅ Gradle configuration  
✅ GitHub Actions workflow  
✅ 5 build attempts documented  

## Build Logs Reference

Both projects have GitHub Actions workflows configured. Build logs for all 20 attempts are documented in:
- `docs/BUILD_ANALYSIS.md` — Detailed error breakdown
- Each project's `.github/workflows/build.yml` — CI/CD configuration
- GitHub Actions runs: See respective repos for full logs

## Next Steps

### For This Session
1. Use these projects as **reference implementations**
2. Document error patterns for **skill development**
3. Validate fixes by **rebuilding with corrections**

### For Next Session
1. Build **pre-build validators** using these as test cases
2. Create **resource auto-generators** from templates
3. Test validators on **both projects** before rebuild
4. Achieve **>85% success rate** on rebuild attempts

## Key Takeaways

### From TorBox (Complex)
- Real-world apps have many dependencies
- Jetpack Compose significantly increases complexity
- External API integration requires careful dependency management
- MVVM + Room patterns are production-grade

### From AnimeCalc (Simple)
- Even simple apps need complete resource setup
- gradle.properties is critical for build success
- Minimal dependencies reduce build complexity
- Resource file consistency is essential

## Files & Structure

```
projects/
├── README.md                    [This file]
├── torbox-downloader/           [Complex app example]
│   ├── app/
│   ├── build.gradle.kts
│   ├── gradle.properties
│   ├── .github/workflows/
│   └── [40+ files]
└── anime-calc/                  [Simple app example]
    ├── app/
    ├── build.gradle.kts
    ├── gradle.properties
    ├── .github/workflows/
    └── [55+ files]
```

---

**Use these projects to:**
- Learn Android architecture patterns
- Understand real build issues
- Validate new skills
- Develop error fixes
- Benchmark against improvements

**See:** `docs/BUILD_ANALYSIS.md` for detailed error breakdowns of all 20 builds.

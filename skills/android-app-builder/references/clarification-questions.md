# Clarification Questions for Android App Ideas

Use these 7-8 targeted questions to gather requirements before generating an Android app skeleton.

---

## Question Set

### 1. **App Name & Purpose**

**What is your app called, and what is its primary purpose?**

Example answers:
- "TodoList - helps users manage daily tasks"
- "WeatherNow - shows real-time weather for your location"
- "FitTrack - tracks workouts and calories burned"

*This defines the app identity and core feature set.*

---

### 2. **Target Android Versions & Device Types**

**What Android versions should this app support, and what devices?**

Options:
- **Min SDK:** Android 7.0 (API 24) → max backwards compat
- **Min SDK:** Android 8.0 (API 26) → medium reach
- **Min SDK:** Android 10+ (API 29+) → latest features only
- **Devices:** Phones only, tablets, both?
- **Screen sizes:** Compact, medium, large?

*This affects library choices, UI design, and feature availability.*

---

### 3. **Key Features (MVP)**

**What are the top 3-5 features for the first release?**

Examples:
- "Create, edit, delete tasks; persist locally"
- "Fetch weather API; show current + 5-day forecast"
- "Record workout sessions; chart progress over time"
- "Browse product catalog; add to favorites; checkout"

*This defines scope and drives code generation (activities, services, databases).*

---

### 4. **Data Persistence**

**How should the app store data?**

Options:
- **No persistence:** Stateless, data only in memory
- **Local (SQLite):** Use Room library for local database
- **Local (SharedPreferences):** Simple key-value storage
- **Cloud (Firebase/REST API):** Backend server required
- **Hybrid:** Local cache + cloud sync

*This determines database schema and networking code.*

---

### 5. **Network & API Requirements**

**Does the app need to fetch data from the internet?**

- **No network:** Fully offline app
- **REST API:** Calls backend endpoints (Retrofit + OkHttp)
- **Real-time:** WebSocket or Firebase Realtime Database
- **Social/Auth:** OAuth login (Google, Facebook, custom)

*This adds networking, authentication, and error handling.*

---

### 6. **UI Complexity & Design**

**How complex should the user interface be?**

Options:
- **Simple:** 1-2 screens, basic layouts
- **Medium:** 3-5 screens, navigation drawer, bottom nav
- **Complex:** 5+ screens, custom views, animations
- **Very Complex:** Multi-tab, nested navigation, Jetpack Compose

*This affects layout generation, fragments, and navigation structure.*

---

### 7. **User Authentication & Permissions**

**Does the app need to authenticate users or request special permissions?**

Authentication:
- None
- Local PIN/password
- Google/Firebase authentication
- Custom backend login

Permissions:
- Camera (photo/video)
- Location (GPS, background location)
- Contacts
- Files/Storage
- Microphone
- Sensors (accelerometer, etc.)

*This affects AndroidManifest.xml, permission handling, and Gradle dependencies.*

---

### 8. **Third-Party Integrations (Optional)**

**Does the app use external services or libraries?**

Common integrations:
- **Firebase:** Analytics, Crashlytics, Cloud Messaging
- **Analytics:** Google Analytics, Amplitude
- **Ads:** Google AdMob
- **Maps:** Google Maps API
- **Payment:** Stripe, Google Play Billing
- **Social:** Firebase Social Auth, Twitter API
- **Cloud Storage:** Firebase Storage, AWS S3

*This determines which SDKs/libraries to include in Gradle.*

---

## Template Response Form

Copy and fill this when collecting answers:

```
## [App Name] - Requirements

1. **Purpose:**
   [1-2 sentence description]

2. **Target Versions & Devices:**
   - Min SDK: API 24 (Android 7.0) / 26 / 29+
   - Target SDK: API 34 (latest)
   - Devices: Phones / Tablets / Both
   - Screen focus: Compact / Medium / Large

3. **Key Features (MVP):**
   - Feature 1
   - Feature 2
   - Feature 3
   - [Optional: 4-5]

4. **Data Storage:**
   - Offline / SQLite (Room) / SharedPrefs / Firebase / REST API

5. **Network Needs:**
   - Offline / REST API / Real-time / OAuth

6. **UI Complexity:**
   - Simple (1-2 screens) / Medium (3-5) / Complex (5+) / Very Complex

7. **Auth & Permissions:**
   - Auth: None / PIN / Google / Custom
   - Permissions: [List needed permissions]

8. **Integrations:**
   - [Firebase, Analytics, Maps, etc. or "None"]
```

---

## Decision Trees

### Data Storage Decision Tree

```
Will the app store data?
├─ NO → No persistence needed
└─ YES → How is it accessed?
    ├─ Only locally (offline)
    │   ├─ Complex queries? 
    │   │   ├─ YES → SQLite (Room)
    │   │   └─ NO → SharedPreferences
    │   
    └─ Needs sync to server
        ├─ Real-time updates?
        │   ├─ YES → Firebase Realtime DB / Firestore
        │   └─ NO → REST API + local SQLite cache
```

### UI Navigation Decision Tree

```
How many screens?
├─ 1-2 → Single Activity, Fragments optional
├─ 3-5 → Single Activity + Navigation Component
├─ 5+ → Multi-Activity + Navigation Component
│   ├─ Needs tabs? → BottomNavigationView
│   ├─ Needs drawer? → NavigationDrawer
│   └─ Needs both? → Composite layout
└─ 10+ → Consider modularization
```

### API & Networking Decision Tree

```
Does app fetch remote data?
├─ NO → No networking
└─ YES → What type?
    ├─ REST JSON API
    │   ├─ Auth needed? → Retrofit + OkHttp + interceptors
    │   └─ Simple queries? → Retrofit + Gson converter
    ├─ Real-time → Firebase Realtime DB / Firestore
    ├─ GraphQL → Apollo GraphQL client
    └─ WebSocket → OkHttp + WebSocket adapter
```

---

## Scoring & Complexity

Use this to estimate scope:

| Feature | Impact | Complexity |
|---------|--------|-----------|
| SQLite (Room) | +data persistence | **Medium** |
| REST API | +network I/O | **Medium** |
| Firebase | +auth + real-time | **High** |
| Location tracking | +background service | **High** |
| File upload | +networking + storage | **High** |
| Compose UI | +modern toolkit | **Medium** |
| Animations | +UX polish | **Low-Medium** |
| Notifications | +Firebase Cloud Messaging | **Medium** |
| Dark mode | +theme variants | **Low** |
| Multi-language | +localization | **Low** |

---

## Example Conversation

**User:** "I want to build a simple todo app"

**Agent:** "Great! Let me ask a few clarifying questions:

1. **Name & Purpose:** What's it called? A basic task list, or with categories/priorities?
2. **Android versions:** Support back to Android 7+, or newer only?
3. **Key features:** Create, edit, delete tasks—anything else? Reminders? Due dates?
4. **Data storage:** Tasks stored locally on the phone, or sync to cloud?
5. **UI:** Just a simple list, or with multiple screens (details, settings)?
6. **Permissions:** Camera, location, or just basic access?
7. **Integrations:** Plain app, or Firebase notifications for reminders?

Once you answer, I'll generate the full project with Gradle, manifest, layouts, and sample code!"

**User:** "Basic list, API 24+, just CRUD operations, local SQLite, simple 2-screen UI (list + detail), no special permissions, no integrations"

**Agent:** Generates project ✅

---

## Notes for Agent Implementation

When asking these questions:
1. **Be conversational** — don't dump all 8 at once
2. **Group related questions** — ask auth + permissions together
3. **Provide defaults** — suggest common options for each
4. **Show examples** — help user understand what's possible
5. **Confirm before proceeding** — "Got it, so local SQLite + 3-screen app. Ready?"

Based on answers, generate:
- ✅ `AndroidManifest.xml` with correct permissions
- ✅ `build.gradle.kts` with needed dependencies
- ✅ Activity/Fragment skeleton files
- ✅ Database models (Room entities) if using SQLite
- ✅ API service interfaces if using REST
- ✅ Navigation graph XML if multi-screen
- ✅ Resource files (strings, colors, dimensions)

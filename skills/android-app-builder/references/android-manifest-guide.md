# AndroidManifest.xml Guide

Complete reference for customizing AndroidManifest.xml for Android applications.

## Basic Structure

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    package="com.example.myapp">

    <!-- Permissions -->
    <uses-permission android:name="android.permission.INTERNET" />

    <!-- Features -->
    <uses-feature
        android:name="android.hardware.camera"
        android:required="false" />

    <!-- App configuration -->
    <application
        android:allowBackup="true"
        android:debuggable="false"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.MyApp"
        android:usesCleartextTraffic="false">

        <!-- Activities -->
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <!-- Services, receivers, providers... -->

    </application>

</manifest>
```

---

## Permissions

### Common Permissions

```xml
<!-- Internet & Network -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.CHANGE_NETWORK_STATE" />

<!-- Location (API 31+: background location requires separate permission) -->
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION" />

<!-- Camera & Sensors -->
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />

<!-- Contacts & Calendar -->
<uses-permission android:name="android.permission.READ_CONTACTS" />
<uses-permission android:name="android.permission.WRITE_CONTACTS" />
<uses-permission android:name="android.permission.READ_CALENDAR" />
<uses-permission android:name="android.permission.WRITE_CALENDAR" />

<!-- File Access (API 30+: scoped storage is preferred) -->
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.MANAGE_EXTERNAL_STORAGE" />

<!-- Phone -->
<uses-permission android:name="android.permission.READ_PHONE_STATE" />
<uses-permission android:name="android.permission.CALL_PHONE" />
<uses-permission android:name="android.permission.READ_SMS" />

<!-- Device Info -->
<uses-permission android:name="android.permission.READ_DEVICE_CONFIG" />
<uses-permission android:name="android.permission.READ_PRIVILEGED_PHONE_STATE" />
```

### Permission Groups (API 23+)

Dangerous permissions require runtime requests:

```kotlin
// In your Activity
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
    requestPermissions(
        arrayOf(Manifest.permission.CAMERA),
        PERMISSION_REQUEST_CODE
    )
}
```

---

## Activities

### Main Activity (Launcher)

```xml
<activity
    android:name=".MainActivity"
    android:exported="true"
    android:launchMode="singleTop"
    android:theme="@style/Theme.MyApp">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>
```

### Additional Activities

```xml
<activity
    android:name=".DetailActivity"
    android:exported="false"
    android:parentActivityName=".MainActivity" />

<activity
    android:name=".SettingsActivity"
    android:exported="false"
    android:label="@string/title_activity_settings" />
```

### Launch Modes

```xml
<!-- Default: New instance each time -->
android:launchMode="standard"

<!-- Reuse existing instance if available -->
android:launchMode="singleTop"

<!-- Single instance, cleared when navigated away -->
android:launchMode="singleTask"

<!-- Truly single instance, app-wide -->
android:launchMode="singleInstance"
```

### Intent Filters (Deep Linking)

```xml
<activity
    android:name=".DetailActivity"
    android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="https"
            android:host="example.com"
            android:pathPrefix="/details" />
    </intent-filter>
</activity>
```

---

## Services

### Background Service

```xml
<service
    android:name=".SyncService"
    android:exported="false" />
```

### Foreground Service (API 31+: specify type)

```xml
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />

<service
    android:name=".LocationService"
    android:exported="false"
    android:foregroundServiceType="location" />
```

Foreground service types:
- `location`, `camera`, `microphone`
- `body_sensors`, `nearby_wifi_devices`
- `mediaPlayback`, `dataSync`, `phoneCall`

---

## Broadcast Receivers

### Exported Receiver (API 31+)

```xml
<receiver
    android:name=".NotificationReceiver"
    android:exported="true">
    <intent-filter>
        <action android:name="com.example.CUSTOM_ACTION" />
    </intent-filter>
</receiver>
```

### Non-exported Receiver (Recommended)

```xml
<receiver
    android:name=".BootReceiver"
    android:exported="false">
    <intent-filter>
        <action android:name="android.intent.action.BOOT_COMPLETED" />
    </intent-filter>
</receiver>
```

---

## Content Providers

### Exported Provider

```xml
<provider
    android:name=".DataProvider"
    android:authorities="com.example.myapp.provider"
    android:exported="true"
    android:grantUriPermissions="true">
    <path-permission
        android:path="/public/*"
        android:readPermission="android.permission.READ_EXTERNAL_STORAGE" />
</provider>
```

---

## Application-Level Configuration

### Debug vs Release

```xml
<application
    android:debuggable="false"
    android:usesCleartextTraffic="false"
    android:label="@string/app_name"
    android:icon="@mipmap/ic_launcher">
    <!-- ... -->
</application>
```

Set `android:debuggable="true"` only for debug builds:

```gradle
// build.gradle.kts
buildTypes {
    debug {
        debuggable = true
    }
    release {
        debuggable = false
    }
}
```

### Data Safety

```xml
android:usesCleartextTraffic="false"
```

This enforces HTTPS for all network traffic.

### Backup Configuration

```xml
<application android:allowBackup="true">
    <meta-data
        android:name="com.google.android.backup.api_key"
        android:value="..." />
</application>
```

Or use backup agent:

```xml
<application android:backupAgent=".BackupAgent">
    <!-- ... -->
</application>
```

---

## Target & Min SDK Versions

Set in `build.gradle.kts`:

```gradle
android {
    compileSdk = 34  // Target latest Android version
    
    defaultConfig {
        minSdk = 24    // Support Android 7.0+
        targetSdk = 34
    }
}
```

Do NOT set in `AndroidManifest.xml` (deprecated).

---

## Manifest Merging

When using libraries, their manifests auto-merge. Resolve conflicts with `tools:` attributes:

```xml
<activity
    android:name=".MainActivity"
    tools:node="replace"
    android:exported="true">
    <!-- Replaces library's MainActivity if present -->
</activity>

<uses-permission
    android:name="android.permission.CAMERA"
    tools:node="remove" />
    <!-- Removes camera permission from merged manifest -->

<service
    android:name=".MyService"
    tools:replace="android:exported"
    android:exported="false" />
    <!-- Replaces only exported attribute -->
```

---

## API 31+ Export Requirements

All components must explicitly set `android:exported`:

```xml
<!-- Explicitly exported (can be accessed by other apps/system) -->
<activity android:name=".MainActivity" android:exported="true" />

<!-- Explicitly not exported (internal only) -->
<service android:name=".MyService" android:exported="false" />
```

Failure to set causes build failure on API 31+.

---

## Common Patterns

### Dark Mode Support (API 29+)

```xml
<application
    android:theme="@style/Theme.MyApp"
    tools:targetApi="29">
    <!-- Uses light theme by default, auto-switches on dark mode -->
</application>
```

### Notification Icons (API 33+)

```xml
<meta-data
    android:name="com.google.android.gms.version"
    android:value="@integer/google_play_services_version" />
```

### Firebase Integration

```xml
<meta-data
    android:name="com.google.firebase.messaging.default_notification_icon"
    android:resource="@drawable/ic_notification" />

<meta-data
    android:name="com.google.firebase.messaging.default_notification_color"
    android:resource="@color/colorAccent" />
```

---

## Validation Checklist

Before submitting to Play Store:

- ✅ `android:exported` set on all components with intent filters
- ✅ `android:debuggable="false"` in release builds
- ✅ `android:usesCleartextTraffic="false"` for production
- ✅ All permissions documented and justified
- ✅ Target SDK = latest Android version
- ✅ Min SDK aligns with user base
- ✅ Manifest merging conflicts resolved
- ✅ No deprecated attributes

---

## Tools

### Validate Manifest

```bash
./gradlew lint
```

### Generate Manifest

Android Gradle plugin auto-merges manifests from:
- `src/main/AndroidManifest.xml`
- Library manifests
- Build variant overlays

View merged manifest:
```bash
./gradlew mergeDebugManifest
# Output: app/build/intermediates/manifest/debug/AndroidManifest.xml
```

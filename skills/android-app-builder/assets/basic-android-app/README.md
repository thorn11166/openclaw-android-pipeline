# Basic Android App Template

This is a minimal, production-ready Android application template with Kotlin, Material Design 3, View Binding, and modern Android architecture.

## Features

- **Kotlin** — Modern, concise syntax
- **View Binding** — Type-safe view access
- **Material Design 3** — Modern UI components
- **Lifecycle-aware** — Proper lifecycle management
- **Min SDK 24** — Supports Android 7.0+
- **Modern Gradle** — Kotlin DSL configuration

## Project Structure

```
app/
├── src/
│   ├── main/
│   │   ├── kotlin/com/example/basicapp/
│   │   │   └── MainActivity.kt
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   └── activity_main.xml
│   │   │   ├── values/
│   │   │   │   ├── strings.xml
│   │   │   │   ├── colors.xml
│   │   │   │   └── themes.xml
│   │   │   └── drawable/
│   │   │       └── (app icons, assets)
│   │   └── AndroidManifest.xml
│   ├── test/
│   │   └── kotlin/com/example/basicapp/
│   │       └── ExampleUnitTest.kt
│   └── androidTest/
│       └── kotlin/com/example/basicapp/
│           └── ExampleInstrumentedTest.kt
└── build.gradle.kts
```

## Building

### Prerequisites

- Android SDK 34 (installed via Android Studio or sdkmanager)
- Java 17 or higher
- Gradle 8.0+

### Build Commands

```bash
# Debug build
./gradlew assembleDebug

# Release build (requires signing config)
./gradlew assembleRelease

# Run tests
./gradlew test
./gradlew connectedAndroidTest

# Clean
./gradlew clean

# Check for issues
./gradlew lint
```

### Running on Device/Emulator

```bash
# Install and run
./gradlew installDebug

# Or via Android Studio: Run → Run 'app'
```

## Customization

### Change App Name & Package

1. In `AndroidManifest.xml`:
   ```xml
   <manifest package="com.yourcompany.yourapp">
   ```

2. In `build.gradle.kts`:
   ```kotlin
   android {
       namespace = "com.yourcompany.yourapp"
       defaultConfig {
           applicationId = "com.yourcompany.yourapp"
       }
   }
   ```

3. Refactor package in source code (right-click in Android Studio: Refactor → Rename)

### Add Dependencies

Edit `build.gradle.kts`:

```kotlin
dependencies {
    // Example: Add Retrofit for networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
}
```

### Add Permissions

Edit `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

Then request at runtime (API 23+) in your Activity.

### Change App Icon

Place icon files in `res/mipmap-*/`:

```
res/
├── mipmap-hdpi/ic_launcher.png
├── mipmap-mdpi/ic_launcher.png
├── mipmap-xhdpi/ic_launcher.png
├── mipmap-xxhdpi/ic_launcher.png
└── mipmap-xxxhdpi/ic_launcher.png
```

Or use Android Studio: New → Image Asset

### Add New Activities

```bash
# In Android Studio: File → New → Activity → Empty Activity
# Or manually:
```

1. Create `MyNewActivity.kt`:
   ```kotlin
   class MyNewActivity : AppCompatActivity() {
       override fun onCreate(savedInstanceState: Bundle?) {
           super.onCreate(savedInstanceState)
           val binding = ActivityMyNewBinding.inflate(layoutInflater)
           setContentView(binding.root)
       }
   }
   ```

2. Create layout `res/layout/activity_my_new.xml`

3. Register in `AndroidManifest.xml`:
   ```xml
   <activity
       android:name=".MyNewActivity"
       android:exported="false" />
   ```

## Testing

### Unit Tests

Edit `src/test/kotlin/com/example/basicapp/ExampleUnitTest.kt`:

```kotlin
@Test
fun testExample() {
    assertEquals(4, 2 + 2)
}
```

Run: `./gradlew test`

### Instrumented Tests (on device/emulator)

Edit `src/androidTest/kotlin/com/example/basicapp/ExampleInstrumentedTest.kt`:

```kotlin
@RunWith(AndroidJUnit4::class)
class ExampleInstrumentedTest {
    @get:Rule
    val activityRule = ActivityScenarioRule(MainActivity::class.java)

    @Test
    fun textViewIsDisplayed() {
        onView(withId(R.id.welcome_text))
            .check(matches(isDisplayed()))
    }
}
```

Run: `./gradlew connectedAndroidTest`

## Release Build

For production:

1. Create keystore:
   ```bash
   keytool -genkey -v -keystore release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my_key
   ```

2. Add signing config to `build.gradle.kts`:
   ```kotlin
   signingConfigs {
       release {
           storeFile = file("release.jks")
           storePassword = "your_password"
           keyAlias = "my_key"
           keyPassword = "your_password"
       }
   }
   
   buildTypes {
       release {
           signingConfig = signingConfigs.getByName("release")
       }
   }
   ```

3. Build: `./gradlew assembleRelease`

4. Find APK: `app/build/outputs/apk/release/app-release.apk`

## Resources

- [Android Documentation](https://developer.android.com/docs)
- [Kotlin Docs](https://kotlinlang.org/docs/home.html)
- [Material Design](https://material.io/design/)
- [Gradle for Android](https://gradle.org/android/)
- [AndroidX Libraries](https://developer.android.com/jetpack/androidx)

## License

MIT

## Support

For issues or questions, open a GitHub issue or contact the maintainers.

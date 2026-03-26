# Gradle Configuration Guide for Android

Complete reference for customizing `build.gradle.kts` for Android projects.

## Basic Project Structure

```
MyApp/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── kotlin/ (or java/)
│   │   │   ├── res/
│   │   │   └── AndroidManifest.xml
│   │   ├── debug/
│   │   ├── release/
│   │   └── test/
│   │       └── kotlin/
│   └── build.gradle.kts
├── settings.gradle.kts
└── build.gradle.kts (root)
```

---

## Root build.gradle.kts

```kotlin
plugins {
    id("com.android.application") version "8.2.0" apply false
    id("com.android.library") version "8.2.0" apply false
    kotlin("android") version "1.9.20" apply false
}

buildscript {
    repositories {
        google()
        mavenCentral()
    }
    
    dependencies {
        classpath("com.android.tools.build:gradle:8.2.0")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.20")
        classpath("com.google.dagger:hilt-android-gradle-plugin:2.47")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
}
```

---

## App-Level build.gradle.kts

### Full Example

```kotlin
plugins {
    id("com.android.application")
    kotlin("android")
    kotlin("kapt")
    id("kotlin-parcelize")
    id("dagger.hilt.android.plugin")
}

android {
    namespace = "com.example.myapp"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.example.myapp"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
        
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        
        vectorDrawables {
            useSupportLibrary = true
        }
    }

    // Build types (Debug/Release)
    buildTypes {
        debug {
            debuggable = true
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            isMinifyEnabled = false
        }
        
        release {
            debuggable = false
            isMinifyEnabled = true
            isShrinkResources = true
            
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            
            signingConfig = signingConfigs.getByName("release")
        }
    }

    // Build variants
    flavorDimensions.add("version")
    productFlavors {
        create("free") {
            dimension = "version"
            applicationIdSuffix = ".free"
        }
        
        create("pro") {
            dimension = "version"
            applicationIdSuffix = ".pro"
        }
    }

    // Compilation options
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    // View binding
    buildFeatures {
        viewBinding = true
        dataBinding = true
        compose = false
    }

    // Resource configuration
    packagingOptions {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Core Android
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("androidx.activity:activity-ktx:1.8.0")
    implementation("androidx.fragment:fragment-ktx:1.6.1")

    // UI & Material
    implementation("com.google.android.material:material:1.10.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")

    // Lifecycle
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.6.2")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.6.2")
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.6.2")

    // Navigation
    implementation("androidx.navigation:navigation-fragment-ktx:2.7.5")
    implementation("androidx.navigation:navigation-ui-ktx:2.7.5")

    // Database
    implementation("androidx.room:room-runtime:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")

    // Network
    implementation("com.squareup.okhttp3:okhttp:4.11.0")
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")

    // JSON
    implementation("com.google.code.gson:gson:2.10.1")

    // Dependency Injection (Hilt)
    implementation("com.google.dagger:hilt-android:2.47")
    kapt("com.google.dagger:hilt-compiler:2.47")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")

    // Logging
    implementation("com.jakewharton.timber:timber:5.0.1")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito:mockito-core:5.5.1")
    testImplementation("io.mockk:mockk:1.13.8")
    
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
```

---

## Common Configurations

### Kotlin DSL vs Groovy

Modern Android uses **Kotlin DSL** (`.kts`):

```kotlin
// Kotlin DSL (preferred)
implementation("com.example:library:1.0.0")
```

vs old Groovy:

```groovy
// Groovy (deprecated)
implementation 'com.example:library:1.0.0'
```

### Version Catalog (Recommended)

**gradle/libs.versions.toml:**

```toml
[versions]
kotlin = "1.9.20"
android-gradle = "8.2.0"
androidx-core = "1.12.0"
androidx-appcompat = "1.6.1"
androidx-lifecycle = "2.6.2"

[libraries]
kotlin-stdlib = { group = "org.jetbrains.kotlin", name = "kotlin-stdlib", version.ref = "kotlin" }
androidx-core = { group = "androidx.core", name = "core-ktx", version.ref = "androidx-core" }
androidx-appcompat = { group = "androidx.appcompat", name = "appcompat", version.ref = "androidx-appcompat" }
androidx-lifecycle-runtime = { group = "androidx.lifecycle", name = "lifecycle-runtime-ktx", version.ref = "androidx-lifecycle" }

[plugins]
android-app = { id = "com.android.application", version.ref = "android-gradle" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
```

**build.gradle.kts:**

```kotlin
plugins {
    alias(libs.plugins.android.app)
    alias(libs.plugins.kotlin.android)
}

dependencies {
    implementation(libs.androidx.core)
    implementation(libs.androidx.appcompat)
}
```

### Dependency Management

```kotlin
// Simple dependency
implementation("com.example:library:1.0.0")

// With transitive exclusions
implementation("com.example:library:1.0.0") {
    exclude(group = "com.google.guava", module = "guava")
}

// BOM (Bill of Materials) - align multiple versions
implementation(platform("com.google.firebase:firebase-bom:32.6.0"))
implementation("com.google.firebase:firebase-analytics-ktx")
implementation("com.google.firebase:firebase-auth-ktx")

// Force a specific version
constraints {
    implementation("com.example:library") {
        version { require("1.0.0") }
    }
}
```

### Build Variants & Flavors

```kotlin
flavorDimensions.addAll(listOf("store", "version"))

productFlavors {
    create("google") {
        dimension = "store"
        applicationIdSuffix = ".google"
    }
    
    create("samsung") {
        dimension = "store"
        applicationIdSuffix = ".samsung"
    }
    
    create("free") {
        dimension = "version"
    }
    
    create("pro") {
        dimension = "version"
        versionNameSuffix = "-pro"
    }
}

// Variant-specific dependencies
dependencies {
    freeImplementation("com.google.android.gms:play-services-ads:22.6.0")
}

// Variant-specific resources
sourceSets {
    getByName("free") {
        res.srcDirs("src/free/res")
    }
}
```

### Signing Configuration

```kotlin
signingConfigs {
    create("release") {
        storeFile = file("keystore.jks")
        storePassword = System.getenv("KEYSTORE_PASSWORD") ?: ""
        keyAlias = System.getenv("KEY_ALIAS") ?: ""
        keyPassword = System.getenv("KEY_PASSWORD") ?: ""
    }
}

buildTypes {
    release {
        signingConfig = signingConfigs.getByName("release")
    }
}
```

### ProGuard/R8 Configuration

**proguard-rules.pro:**

```pro
# Preserve all public classes and methods
-keep public class * {
    public <methods>;
}

# Keep View constructors
-keep public class * extends android.view.View {
    public <init>(android.content.Context);
    public <init>(android.content.Context, android.util.AttributeSet);
    public <init>(android.content.Context, android.util.AttributeSet, int);
    public void set*(***);
    *** get*();
}

# Keep Parcelable implementations
-keep class * implements android.os.Parcelable {
    static android.os.Parcelable$Creator CREATOR;
}

# Keep enums
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}

# Keep custom exceptions
-keep public class * extends java.lang.Exception

# Keep native methods
-keepclasseswithmembernames class * {
    native <methods>;
}

# Keep callback methods
-keep class * implements android.os.Handler
```

### Lint Configuration

```kotlin
android {
    lint {
        abortOnError = true
        disable += listOf(
            "MissingTranslation",
            "ExtraTranslation",
            "ContentDescription"
        )
        checkOnly += listOf(
            "NewApi",
            "InlinedApi"
        )
        warningLevel = "Default"
    }
}
```

### Compose Support

```kotlin
buildFeatures {
    compose = true
}

composeOptions {
    kotlinCompilerExtensionVersion = "1.5.9"
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2023.10.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")
    debugImplementation("androidx.compose.ui:ui-tooling")
}
```

### Data Binding & View Binding

```kotlin
buildFeatures {
    viewBinding = true    // Modern approach
    dataBinding = true    // XML-based binding
}

dependencies {
    implementation("androidx.databinding:databinding-runtime:8.2.0")
}
```

---

## Testing Configuration

```kotlin
dependencies {
    // Unit tests
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.mockito:mockito-core:5.5.1")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("org.robolectric:robolectric:4.11.1")

    // Instrumented tests
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test:runner:1.5.2")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("androidx.test.espresso:espresso-intents:3.5.1")
}

android {
    testOptions {
        unitTests {
            isIncludeAndroidResources = true
        }
        execution = "ANDROIDX_TEST_ORCHESTRATOR"
    }
}
```

---

## Performance Tips

### Enable Build Cache

```kotlin
android {
    buildCache {
        isEnabled = true
    }
}
```

### Parallel Compilation

```gradle.properties
org.gradle.parallel=true
org.gradle.workers.max=8
```

### Incremental Compilation

```gradle.properties
kotlin.incremental=true
kotlin.incremental.js=true
```

### Shrink Resources

```kotlin
buildTypes {
    release {
        isShrinkResources = true
        isMinifyEnabled = true
    }
}
```

---

## Troubleshooting

### Gradle Sync Fails

```bash
./gradlew clean
./gradlew --refresh-dependencies
```

### Duplicate Class Error

```kotlin
dependencies {
    implementation("lib-a:1.0.0") {
        exclude(group = "com.google.guava")
    }
}
```

### Out of Memory

**gradle.properties:**

```properties
org.gradle.jvmargs=-Xmx4096m
```

### Plugin Version Conflicts

Use BOM or explicit version constraints:

```kotlin
dependencies {
    constraints {
        implementation("com.google.firebase:firebase-analytics") {
            version { require("21.2.0") }
        }
    }
}
```

---

## Validation

```bash
# Lint checks
./gradlew lint

# Dependency tree
./gradlew app:dependencies

# Task graph
./gradlew app:tasks
```

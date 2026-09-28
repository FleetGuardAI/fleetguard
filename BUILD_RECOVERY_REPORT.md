# DRIVER APP + OWNER APP BUILD FORENSIC AUDIT

## 1. Executive Summary
This forensic audit analyzed the build configurations, toolchains, dependencies, and native code integration for both the **Driver App** and **Owner App** in the Fleetguard repository. The applications are currently in a fragile state with cascading dependency issues stemming from Flutter/Dart version bumps, breaking API changes in notification plugins, and aggressive Kotlin/AGP upgrades.

* **Current Build Status:** Both applications are currently unbuildable due to newly introduced compilation errors and configuration gaps.
* **Driver App Status:** Fails at compilation phase (Dart code errors in `notification_service.dart`).
* **Owner App Status:** Vulnerable to missing local configuration and potential environment inconsistencies, though stable at the code level.
* **Blockers:** 1 (Code compilation error)
* **High-Severity Issues:** 2 (AGP/Kotlin versions)
* **Medium Issues:** 2 (Hardcoded compileSdk, Missing files)
* **Low Issues:** 2 (Desugaring, Manifest placeholders)

---

## 2. Toolchain Matrix

| Component | Driver | Owner | Expected | Status |
| --------- | ------ | ----- | -------- | ------ |
| **Flutter** | 3.42.0 (CI) | 3.42.0 (CI) | 3.42.0 (Stable) | Compatible |
| **Dart** | 3.10/3.11 | 3.10/3.11 | >=3.10.0 <4.0.0 | Compatible |
| **Java/JDK** | 17 | 17 | 17 | Compatible |
| **Gradle** | 9.1.0 | 9.1.0 | 8.9+ / 9.x | High Risk |
| **AGP** | 9.0.1 | 9.0.1 | 8.x / 9.0 | High Risk |
| **Kotlin** | 2.3.20 | 2.3.20 | 1.9.2x or 2.x | High Risk |
| **compileSdk** | 36 (Hardcoded) | `flutter.compileSdkVersion` | 34 / 35 | Mismatch |
| **targetSdk** | `flutter.targetSdkVersion` | `flutter.targetSdkVersion` | 34 / 35 | Compatible |
| **minSdk** | 26 (Hardcoded) | `flutter.minSdkVersion` | >= 24 | Mismatch |

---

## 3. Dependency Matrix

| Package | Driver Version | Owner Version | Compatibility | Problem |
| ------- | -------------- | ------------- | ------------- | ------- |
| `flutter_local_notifications` | 17.2.4 | N/A | Breaking API | `show()` and `initialize()` method signatures changed in 17.x, but core arguments remain positional. Recent attempts to use named arguments caused compile blockers. |
| `google_maps_flutter` | 2.18.0 | 2.18.0 | Requires Dart 3.10 | Compatible now that CI is set to Flutter 3.42.0. |
| `activity_recognition_flutter` | 6.1.0 | N/A | Requires Dart 3.9.2 | Compatible with Flutter 3.42.0. |
| `riverpod_generator` | 2.4.3 | 2.4.3 | Breaks on Dart 3.13 | Bypassed successfully by pinning Flutter < 3.47.5. |
| `build_runner` | 2.5.4 | 2.5.4 | Needs Dart < 3.13 | Bypassed successfully. |

---

## 4. BLOCKERS

| ID | App | Category | Root Cause | Build Impact | File |
| -- | --- | -------- | ---------- | ------------ | ---- |
| FG-DRIVER-001 | Driver | Compilation | Incorrect API usage for `flutter_local_notifications` v17.2.4. The `show()` method requires `id`, `title`, `body`, and `notificationDetails` as positional arguments, NOT named. | Prevents `flutter build apk`. `build_runner` might pass, but compilation will fail. | `driver_app/lib/core/services/notification_service.dart` |

---

## 5. HIGH-SEVERITY ISSUES

| ID | App | Category | Root Cause | Build Impact | File |
| -- | --- | -------- | ---------- | ------------ | ---- |
| FG-SHARED-002 | Both | Android Config | Extremely aggressive AGP (9.0.1) and Kotlin (2.3.20) versions inside `settings.gradle.kts`. AGP 9.0 is bleeding-edge and breaks many standard Flutter plugins that rely on older build hooks. | High risk of native Android compilation failures or manifest merger issues during `assembleRelease`. | `android/settings.gradle.kts` |
| FG-OWNER-003 | Owner | Configuration | Missing `local.properties` file in the repository (while Driver app has one). The Gradle script explicitly requires it to locate the Flutter SDK. | Blocks local builds completely if the dev environment isn't perfectly configured. (CI injects this automatically via flutter-action, so it passes there). | `owner_app/android/local.properties` |

---

## 6. MEDIUM-SEVERITY ISSUES

| ID | App | Category | Root Cause | Build Impact | File |
| -- | --- | -------- | ---------- | ------------ | ---- |
| FG-DRIVER-004 | Driver | Android Config | `compileSdk` is forcibly hardcoded to `36` via a reflection hack in `build.gradle.kts`. | Hardcoding against API 36 (VanillaIceCream) can cause build failures if the local Android SDK or CI environment doesn't have it installed. | `driver_app/android/build.gradle.kts` |
| FG-DRIVER-005 | Driver | Android Config | `minSdk = 26` is hardcoded instead of using `flutter.minSdkVersion`. | Prevents centralized management and might clash with specific plugins requiring different minimums. | `driver_app/android/app/build.gradle.kts` |

---

## 7. LOW-SEVERITY ISSUES

| ID | App | Category | Root Cause | Build Impact | File |
| -- | --- | -------- | ---------- | ------------ | ---- |
| FG-DRIVER-006 | Driver | Build | `isCoreLibraryDesugaringEnabled = true` is used. | Slows down build times and increases APK size; necessary for older APIs, but with minSdk 26, it might be obsolete. | `driver_app/android/app/build.gradle.kts` |
| FG-SHARED-007 | Both | Configuration | Firebase config files (`google-services.json`, `GoogleService-Info.plist`) are absent. | Assuming they are injected via CI/CD secrets, but if missing locally, Firebase initialization will crash at runtime. | Project Root |

---

## 8. ROOT-CAUSE TREE

```text
Flutter SDK Version (3.47.5 introduced Dart 3.13)
     ↓
Analyzer Parser Crash (visitDotShorthandPropertyAccess)
     ↓
build_runner Failure (Riverpod Code Gen)
     ↓
[RESOLVED BY DOWNGRADING FLUTTER TO 3.42.0]

flutter_local_notifications Upgrade to 17.x
     ↓
API Breaking Change (Callbacks and NotificationDetails)
     ↓
Incorrect attempt to convert ALL arguments to named parameters
     ↓
Dart Compilation Failure (Too many named arguments in show())
     ↓
[CURRENT BLOCKER: APK BUILD FAILURE]
```

---

## 9. DRIVER APP BUILD FAILURE CHAIN

1. `flutter_local_notifications` was upgraded to 17.2.4.
2. The `show()` method signature changed.
3. The previous "fix" mistakenly converted `id`, `title`, `body`, and `notificationDetails` to named parameters (`id: ...`).
4. **Current Status:** Dart compilation fails because `show()` strictly requires those 4 arguments to be positional.

---

## 10. OWNER APP BUILD FAILURE CHAIN

1. `owner_app/android/local.properties` is missing.
2. `settings.gradle.kts` explicitly reads `flutter.sdk` from it.
3. **Current Status:** Fails to build locally. CI passes only because the GitHub Action generates this file dynamically.
4. **Secondary Risk:** AGP 9.0.1 + Kotlin 2.3.20 is highly unstable with older Flutter packages.

---

## 11. SHARED PROBLEMS

* **AGP 9.0.1 & Kotlin 2.3.20:** Both apps are configured with bleeding-edge Android build tools in `settings.gradle.kts`. This is highly irregular for standard Flutter apps and very prone to breaking third-party plugins.
* **Gradle 9.1.0:** The wrapper is set to a pre-release/bleeding-edge Gradle version.

---

## 12. APP-SPECIFIC PROBLEMS

**Driver App:**
* `notification_service.dart` has severe compilation errors.
* `build.gradle.kts` contains highly unusual reflection code (`android.javaClass.getMethod...`) forcing `compileSdk` to 36.

**Owner App:**
* Clean code state, but missing `local.properties`.

---

## 13. VERSION STANDARDIZATION RECOMMENDATION

```text
Flutter: 3.42.0 (Stable, avoids Dart 3.13 bugs)
Dart: 3.10.x (Bundled with Flutter)
Java: 17
Gradle: 8.7 (Downgrade from 9.1.0 for plugin stability)
AGP: 8.3.2 (Downgrade from 9.0.1 for plugin stability)
Kotlin: 1.9.23 (Downgrade from 2.3.20 for plugin stability)
compileSdk: flutter.compileSdkVersion (Remove hardcoded 36)
targetSdk: flutter.targetSdkVersion
minSdk: flutter.minSdkVersion (Remove hardcoded 26)
NDK: flutter.ndkVersion
```
**Why:** AGP 8.3 + Gradle 8.7 is the standard stable stack for Flutter 3.40+. AGP 9.x and Kotlin 2.x are too new and frequently break native Android plugins.

---

## 14. FIX ORDER

1. **Dart Compilation Errors:** Fix `notification_service.dart` in the Driver app (revert named parameters to positional for `id`, `title`, `body`, and `notificationDetails`).
2. **Android Configuration:** Remove the reflection hack forcing `compileSdk = 36` in the Driver app's `build.gradle.kts`.
3. **Gradle/AGP/Kotlin Downgrade:** Standardize both apps on AGP 8.3.2, Gradle 8.7, and Kotlin 1.9.23.
4. **Local Config:** Generate a template `local.properties` for the Owner app to prevent local build failures.

---

# 15. FINAL "BUILD BLOCKERS ONLY" CHECKLIST

[ ] Driver App — Blocker 1: Fix `notification_service.dart` positional arguments in `_plugin.show()`.
[ ] Driver App — Blocker 2: Fix `notification_service.dart` positional arguments in `_plugin.initialize()`.
[ ] Shared — Risk 1: Monitor AGP 9.0.1 / Gradle 9.1.0 for plugin compatibility failures during `assembleRelease`.

---
*Audit Complete. DO NOT attempt builds until Blocker 1 is addressed in source code.*

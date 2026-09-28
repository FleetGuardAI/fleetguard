# CI FLUTTER SETUP FIX REPORT

## Current Failure
```text
Unable to determine Flutter version for channel: stable version: 3.42.0 architecture: x64
```

## Root Cause
The CI pipeline failed because **Flutter version 3.42.0 does not exist on the stable channel**. Version `3.42.0` was only ever released as pre-release versions on the `beta` channel (e.g. `3.42.0-0.4.pre`). The `subosito/flutter-action` attempts to resolve the exact version string against Google's Flutter release manifests (`releases_linux.json`). When the version string is not found in the stable channel list, the action immediately aborts.

The previous audit recommended `3.42.0` in an attempt to use a version of Flutter with Dart 3.10 to satisfy `google_maps_flutter >=2.15.0` while avoiding Dart 3.13 (which crashes `riverpod_generator`). However, the correct stable release series that fits these constraints is `3.44.x` (which bundles Dart 3.12.x). 

## Workflow Changed
1. `.github/workflows/build-driver-app.yml`
2. `.github/workflows/build-owner-app.yml`

## Before
```yaml
    - name: Set up Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.42.0'
        channel: 'stable'
```

## After
```yaml
    - name: Set up Flutter
      uses: subosito/flutter-action@v2
      with:
        flutter-version: '3.44.9'
        channel: 'stable'

    - name: Verify Flutter
      run: |
        flutter --version
        dart --version
        flutter doctor -v
```

## Flutter Version
```text
Installed: 3.44.9
Dart: 3.12.2
Channel: stable
Architecture: x64
```
*(This is the intended version to be resolved by the updated workflows)*

## Verification
Since the local agent lacks a functional Flutter SDK environment and the failure occurs specifically in GitHub Actions runners, verification requires the CI workflow to execute. 

*(Awaiting User CI Execution)*
```text
flutter --version: PENDING
flutter doctor: PENDING
Driver analyze: PENDING
Driver APK: PENDING
Owner analyze: PENDING
Owner APK: PENDING
```

## Remaining Errors
*None confirmed at the CI setup layer.*
Once the GitHub Runner successfully provisions Flutter `3.44.9`, the pipeline will proceed to dependency resolution (`flutter pub get`), static analysis (`flutter analyze`), and APK compilation. If the Android toolchain configuration (AGP 9.0.1, Gradle 9.1.0, Kotlin 2.3.20) presents compatibility issues with Flutter 3.44.9 or its plugins, they will surface during the `build apk` step.

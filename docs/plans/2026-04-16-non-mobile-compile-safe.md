# Non-Mobile Compile-Safe Fallback Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `flutter_performance_tier` compile safely in Web and desktop hosts without changing the Android/iOS public API.

**Architecture:** Keep the current `MethodChannelDeviceSignalCollector` as the default collector, but remove its `dart:io` dependency and switch to Flutter platform detection. Only Android/iOS should invoke the method channel; Web and desktop should return a lightweight fallback `DeviceSignals` snapshot so the service can still initialize and produce a decision.

**Tech Stack:** Flutter, Dart, `flutter_test`, existing `MethodChannel` collector and `DefaultPerformanceTierService`.

---

### Task 1: Add Failing Tests For Non-Mobile Fallback Behavior

**Files:**
- Modify: `test/performance_tier/service/platform_field_integrity_test.dart`
- Create or modify: `test/performance_tier/service/method_channel_device_signal_collector_test.dart`

**Step 1: Write the failing test**

Add tests that verify:

- on Web, `MethodChannelDeviceSignalCollector.collect()` returns fallback signals and never touches the channel
- on desktop target platforms, `MethodChannelDeviceSignalCollector.collect()` returns fallback signals and never touches the channel
- on Android/iOS target platforms, the collector still uses the existing channel contract

**Step 2: Run test to verify it fails**

Run:

```bash
flutter test test/performance_tier/service/method_channel_device_signal_collector_test.dart
```

Expected: FAIL because the collector currently imports `dart:io` and has no injectable platform detection seam.

**Step 3: Write minimal implementation**

Add the smallest platform-detection seam needed for tests and future non-mobile compilation support.

**Step 4: Run test to verify it passes**

Run:

```bash
flutter test test/performance_tier/service/method_channel_device_signal_collector_test.dart
```

Expected: PASS

### Task 2: Make The Default Collector Compile-Safe Outside Android/iOS

**Files:**
- Modify: `lib/performance_tier/service/method_channel_device_signal_collector.dart`
- Check: `lib/performance_tier/service/default_performance_tier_service.dart`

**Step 1: Write the failing test**

Use the Task 1 tests as the red phase for this behavior.

**Step 2: Run test to verify it fails**

Run:

```bash
flutter test test/performance_tier/service/method_channel_device_signal_collector_test.dart
```

Expected: FAIL before implementation.

**Step 3: Write minimal implementation**

- remove `dart:io`
- use `kIsWeb` and `defaultTargetPlatform`
- keep `performance_tier/device_signals` + `collectDeviceSignals` unchanged for Android/iOS
- return fallback `DeviceSignals` for Web and desktop with an explicit platform name

**Step 4: Run test to verify it passes**

Run:

```bash
flutter test test/performance_tier/service/method_channel_device_signal_collector_test.dart
```

Expected: PASS

### Task 3: Update README Platform Boundary

**Files:**
- Modify: `README.md`

**Step 1: Update documentation**

Clarify that:

- this package is intended for the current workspace/private integration flow
- Android/iOS use plugin-backed native signal collection by default
- Web and desktop are compile-safe but use fallback/default signals unless the host injects a custom `DeviceSignalCollector`
- minimum supported mobile platforms are Android `minSdk 24` and iOS `13.0`

**Step 2: Verify documentation matches the implementation**

Cross-check the README wording against:

- `android/build.gradle.kts`
- `ios/flutter_performance_tier.podspec`
- `lib/performance_tier/service/method_channel_device_signal_collector.dart`

### Task 4: Run Package Validation

**Files:**
- No code changes

**Step 1: Run targeted tests**

```bash
flutter test test/performance_tier/service/method_channel_device_signal_collector_test.dart
```

**Step 2: Run package test suite**

```bash
flutter test test/performance_tier
```

Expected: PASS

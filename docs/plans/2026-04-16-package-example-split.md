# Package + Example Split Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert `flutter_performance_tier` into a standard Flutter package/plugin with an `example/` app, while keeping signals in the same package and moving demo/internal tools out of the root package.

**Architecture:** First move all demo/internal-tools code and tests into `example/` so the root package only contains reusable code. Then migrate Android/iOS signal collection from host-app files into standard plugin implementation files and shrink root dependencies to package-only requirements.

**Tech Stack:** Flutter, Dart, `flutter_test`, Android Kotlin, iOS Swift, existing `MethodChannel` collector stack.

---

### Task 1: Add A Stable Public Package Entry Point

**Files:**
- Create: `lib/flutter_performance_tier.dart`
- Check: `lib/performance_tier/performance_tier.dart`
- Check: `test/performance_tier/`

**Step 1: Write the failing test**

Add a simple import smoke test under `test/performance_tier/` that imports:

```dart
import 'package:flutter_performance_tier/flutter_performance_tier.dart';
```

and references one exported type such as:

```dart
final RuntimeTierController controller = RuntimeTierController();
expect(controller.config.enableFrameDropSignal, isFalse);
```

**Step 2: Run test to verify it fails**

Run: `flutter test test/performance_tier/<new_import_smoke_test>.dart`
Expected: FAIL because `lib/flutter_performance_tier.dart` does not exist yet.

**Step 3: Write minimal implementation**

Create `lib/flutter_performance_tier.dart` and export:

- `performance_tier/performance_tier.dart`

Do not remove the existing nested barrel file yet.

**Step 4: Run test to verify it passes**

Run: `flutter test test/performance_tier/<new_import_smoke_test>.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add lib/flutter_performance_tier.dart test/performance_tier/<new_import_smoke_test>.dart
git commit -m "refactor: add public package barrel"
```

### Task 2: Move Demo Entrypoints Into `example/lib`

**Files:**
- Create: `example/lib/main.dart`
- Create: `example/lib/internal_upload_probe_main.dart`
- Move/Create: `example/lib/demo/`
- Move/Create: `example/lib/internal_upload_probe/`
- Modify: `README.md`
- Delete or repurpose: `lib/main.dart`
- Delete or repurpose: `lib/internal_upload_probe_main.dart`

**Step 1: Write the failing test**

Create an example-side smoke test that imports:

```dart
import 'package:flutter_performance_tier_example/main.dart';
```

and pumps the app:

```dart
await tester.pumpWidget(const PerformanceTierDemoApp());
expect(find.text('Performance Tier Diagnostics'), findsOneWidget);
```

**Step 2: Run test to verify it fails**

Run: `flutter test example/test/<new_widget_smoke_test>.dart`
Expected: FAIL because `example/` app structure and imports are not in place.

**Step 3: Write minimal implementation**

Move or recreate the current demo entrypoints and demo support files under `example/lib/`:

- `lib/demo/*` -> `example/lib/demo/*`
- `lib/internal_upload_probe/*` -> `example/lib/internal_upload_probe/*`
- `lib/internal_upload_probe_main.dart` -> `example/lib/internal_upload_probe_main.dart`
- `lib/main.dart` functionality -> `example/lib/main.dart`

Update imports so example files depend on:

```dart
import 'package:flutter_performance_tier/flutter_performance_tier.dart';
```

Keep the UI behavior unchanged.

**Step 4: Run test to verify it passes**

Run: `flutter test example/test/<new_widget_smoke_test>.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add example/lib README.md
git rm lib/main.dart lib/internal_upload_probe_main.dart
git commit -m "refactor: move demo entrypoints into example"
```

### Task 3: Move Demo And Widget Tests Into `example/test`

**Files:**
- Move/Create: `example/test/widget_test.dart`
- Move/Create: `example/test/demo/example_app_factory_test.dart`
- Move/Create: `example/test/demo/internal_tools_controller_test.dart`
- Move/Create: `example/test/demo/public_example_mode_test.dart`
- Move/Create: `example/test/demo/demo_runtime_signal_support_test.dart`
- Modify: moved test imports
- Keep: `test/performance_tier/`

**Step 1: Write the failing test**

Pick one moved test first, such as the widget test, and update it to import the example app package path.

Example import target:

```dart
import 'package:flutter_performance_tier_example/main.dart';
```

**Step 2: Run test to verify it fails**

Run: `flutter test example/test/widget_test.dart`
Expected: FAIL until the example package metadata and imports are wired correctly.

**Step 3: Write minimal implementation**

Move the current demo-facing tests from root `test/` into `example/test/` and update imports so:

- demo tests import from `example/lib/...` package namespace
- core tests continue importing from `package:flutter_performance_tier/...`

Do not move `test/performance_tier/*`.

**Step 4: Run test to verify it passes**

Run: `flutter test example/test`
Expected: PASS

**Step 5: Commit**

```bash
git add example/test
git rm test/widget_test.dart test/demo/*.dart
git commit -m "test: move demo tests into example"
```

### Task 4: Create `example/pubspec.yaml` And Move Demo-Only Dependencies

**Files:**
- Create: `example/pubspec.yaml`
- Modify: `pubspec.yaml`
- Check: `lib/demo/performance_tier_upload_probe_controller.dart` moved under `example/lib/`
- Check: `example/lib/internal_upload_probe/`

**Step 1: Write the failing test**

Run dependency resolution after drafting `example/pubspec.yaml`.

**Step 2: Run command to verify it fails before completion**

Run: `flutter pub get`
Expected: FAIL or remain incomplete until root/example dependencies are correctly split.

**Step 3: Write minimal implementation**

Set up `example/pubspec.yaml` with:

- SDK and Flutter metadata
- path dependency on `..`
- demo-only dependencies such as `common` and `dio`

Then remove demo-only dependencies from root `pubspec.yaml`:

- `common`
- `dio`
- any demo-only generator or env dependency that is no longer needed by root package

Keep only dependencies required by the reusable package.

**Step 4: Run command to verify it passes**

Run:

```bash
flutter pub get
cd example && flutter pub get
```

Expected: PASS in both locations

**Step 5: Commit**

```bash
git add pubspec.yaml example/pubspec.yaml pubspec.lock
git commit -m "build: split root and example dependencies"
```

### Task 5: Convert Android Signal Collection Into Package Plugin Code

**Files:**
- Create/Move: `android/src/main/kotlin/...`
- Modify: `android/build.gradle.kts`
- Modify: `android/settings.gradle.kts` if needed
- Modify: `pubspec.yaml`
- Delete or stop using: `android/app/src/main/kotlin/com/example/flutter_performance_tier/MainActivity.kt`
- Delete or stop using: `android/app/src/main/kotlin/com/example/flutter_performance_tier/DeviceSignalChannelHandler.kt`
- Test: `test/performance_tier/service/platform_field_integrity_test.dart`

**Step 1: Write the failing test**

Update `platform_field_integrity_test.dart` to point at the future Android plugin source path and keep the same channel/key assertions.

**Step 2: Run test to verify it fails**

Run: `flutter test test/performance_tier/service/platform_field_integrity_test.dart`
Expected: FAIL because the new plugin file does not exist yet.

**Step 3: Write minimal implementation**

Move Android channel registration and signal collection into standard plugin files under `android/src/main/...`.

Keep these constants unchanged:

- channel name: `performance_tier/device_signals`
- method: `collectDeviceSignals`

Wire package registration through standard Flutter plugin mechanisms instead of `MainActivity`.

**Step 4: Run test to verify it passes**

Run: `flutter test test/performance_tier/service/platform_field_integrity_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add android pubspec.yaml test/performance_tier/service/platform_field_integrity_test.dart
git commit -m "refactor: move android signal collection into plugin"
```

### Task 6: Convert iOS Signal Collection Into Package Plugin Code

**Files:**
- Create/Move: `ios/Classes/`
- Modify: `ios/flutter_performance_tier.podspec` or equivalent plugin metadata
- Modify: `pubspec.yaml`
- Delete or stop using: `ios/Runner/AppDelegate.swift` signal collection logic
- Test: `test/performance_tier/service/platform_field_integrity_test.dart`

**Step 1: Write the failing test**

Update `platform_field_integrity_test.dart` to point at the future iOS plugin implementation path and keep the same channel/key assertions.

**Step 2: Run test to verify it fails**

Run: `flutter test test/performance_tier/service/platform_field_integrity_test.dart`
Expected: FAIL because the new iOS plugin file path does not exist yet.

**Step 3: Write minimal implementation**

Move the signal channel setup and collection logic into standard iOS plugin files under `ios/Classes/`.

Preserve:

- channel name
- method name
- field names emitted to Dart

Do not change the Dart collector contract.

**Step 4: Run test to verify it passes**

Run: `flutter test test/performance_tier/service/platform_field_integrity_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add ios pubspec.yaml test/performance_tier/service/platform_field_integrity_test.dart
git commit -m "refactor: move ios signal collection into plugin"
```

### Task 7: Remove Root App Scaffolding And Normalize README Commands

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `AGENTS.md`
- Delete or shrink: root app-specific references

**Step 1: Write the failing doc expectation**

Search for outdated commands and paths such as:

- `flutter run`
- `flutter run -t lib/internal_upload_probe_main.dart`
- `lib/demo/`

and note every reference that should become an `example/` path.

**Step 2: Run search to verify stale references exist**

Run:

```bash
rg -n "lib/demo|lib/internal_upload_probe_main.dart|flutter run(?! .*example)" README.md docs AGENTS.md
```

Expected: matches found

**Step 3: Write minimal implementation**

Update docs so commands become example-oriented, for example:

- `flutter run -t example/lib/main.dart`
- `flutter run -t example/lib/internal_upload_probe_main.dart`

Update structural descriptions from:

- root `lib/demo/`

to:

- `example/lib/demo/`

**Step 4: Run search to verify it passes**

Run the same `rg` command again.
Expected: no stale matches for migrated paths

**Step 5: Commit**

```bash
git add README.md docs AGENTS.md
git commit -m "docs: update package and example workflow"
```

### Task 8: Run Full Validation For Root Package And Example

**Files:**
- Check: `test/performance_tier/`
- Check: `example/test/`

**Step 1: Run root package tests**

Run: `flutter test test/performance_tier`
Expected: PASS

**Step 2: Run example tests**

Run: `cd example && flutter test`
Expected: PASS

**Step 3: Run formatter**

Run: `dart format lib test example/lib example/test`
Expected: PASS with formatted files only

**Step 4: Manual smoke validation**

Run:

```bash
flutter run -t example/lib/main.dart
flutter run -t example/lib/internal_upload_probe_main.dart
```

Expected:

- public example starts
- internal upload probe entrypoint starts
- signal collection still returns device fields

**Step 5: Commit**

```bash
git add .
git commit -m "refactor: split package from example app"
```

# Example / Demo Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor the repository into a pure `performance_tier` core plus a lightweight public example and a clearly separated internal tools area.

**Architecture:** Keep `lib/performance_tier/` pure, move example-specific assembly out of the current all-in-one demo controller, and split the example UI into a default public path plus a collapsible internal tools section. Treat runtime preset injection as an example-only collector decorator and keep upload probe as an example-side internal tool.

**Tech Stack:** Flutter, Dart, `flutter_test`, existing `performance_tier` service stack, existing `common` + `dio` upload probe code.

---

### Task 1: Lock In The Refactor With Widget Expectations

**Files:**
- Modify: `test/widget_test.dart`
- Check: `lib/demo/performance_tier_demo_app.dart`

**Step 1: Write the failing test**

Add assertions for the new default UI contract:

- default screen still renders the decision demo
- `Run /upload probe` is not visible on first load
- runtime preset chips are not visible on first load
- an `Internal Tools` entry point is visible

**Step 2: Run test to verify it fails**

Run: `flutter test test/widget_test.dart`
Expected: FAIL because the current page still renders upload probe and runtime preset controls by default.

**Step 3: Write minimal implementation**

Adjust the example page so the default state renders a lightweight public view and defers internal controls behind a collapsed section.

**Step 4: Run test to verify it passes**

Run: `flutter test test/widget_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add test/widget_test.dart lib/demo/performance_tier_demo_app.dart
git commit -m "refactor: hide internal tools from default example"
```

### Task 2: Extract Example Assembly From The Current Demo Controller

**Files:**
- Create: `lib/demo/example_app_factory.dart`
- Modify: `lib/demo/performance_tier_demo_controller.dart`
- Check: `lib/demo/demo_runtime_signal_support.dart`

**Step 1: Write the failing test**

Add a focused unit test covering the assembly rule:

- default example service assembly uses real `MethodChannelDeviceSignalCollector`
- runtime preset override is only applied when the internal tools path requests it

Prefer a dedicated new test file such as `test/demo/example_app_factory_test.dart`.

**Step 2: Run test to verify it fails**

Run: `flutter test test/demo/example_app_factory_test.dart`
Expected: FAIL because no dedicated assembly boundary exists yet.

**Step 3: Write minimal implementation**

Create `example_app_factory.dart` to own:

- logger assembly
- base collector assembly
- optional preset decorator assembly
- default `DefaultPerformanceTierService` construction

Then slim `PerformanceTierDemoController` so it no longer builds the whole service internally.

**Step 4: Run test to verify it passes**

Run: `flutter test test/demo/example_app_factory_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add lib/demo/example_app_factory.dart lib/demo/performance_tier_demo_controller.dart test/demo/example_app_factory_test.dart
git commit -m "refactor: extract example service assembly"
```

### Task 3: Split Public Page State From Internal Tools State

**Files:**
- Create: `lib/demo/internal_tools_controller.dart`
- Modify: `lib/demo/performance_tier_demo_controller.dart`
- Modify: `lib/demo/performance_tier_demo_app.dart`
- Modify: `lib/demo/performance_tier_upload_probe_controller.dart`

**Step 1: Write the failing test**

Add tests covering state separation:

- public page controller can initialize and refresh without starting upload probe
- internal tools controller owns runtime preset state, structured logs, and upload probe state

Prefer a dedicated new test file such as `test/demo/internal_tools_controller_test.dart`.

**Step 2: Run test to verify it fails**

Run: `flutter test test/demo/internal_tools_controller_test.dart`
Expected: FAIL because the current demo controller still owns both public and internal state.

**Step 3: Write minimal implementation**

Move these responsibilities into `internal_tools_controller.dart`:

- runtime preset selection
- structured log caching / copy helpers
- upload probe bootstrap and action handling

Leave `PerformanceTierDemoController` responsible for:

- service lifecycle
- decision subscription
- headline / public report data
- refresh state

**Step 4: Run test to verify it passes**

Run: `flutter test test/demo/internal_tools_controller_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add lib/demo/internal_tools_controller.dart lib/demo/performance_tier_demo_controller.dart lib/demo/performance_tier_demo_app.dart lib/demo/performance_tier_upload_probe_controller.dart test/demo/internal_tools_controller_test.dart
git commit -m "refactor: separate internal tools controller"
```

### Task 4: Convert Runtime Preset Support Into An Explicit Example-Only Decorator

**Files:**
- Modify: `lib/demo/demo_runtime_signal_support.dart`
- Modify: `lib/demo/example_app_factory.dart`
- Test: `test/demo/demo_runtime_signal_support_test.dart`

**Step 1: Write the failing test**

Expand `test/demo/demo_runtime_signal_support_test.dart` to assert:

- the base collector result is unchanged in live mode
- memory / thermal presets only override the intended runtime fields
- naming and API make the decorator role explicit

**Step 2: Run test to verify it fails**

Run: `flutter test test/demo/demo_runtime_signal_support_test.dart`
Expected: FAIL after renaming or API tightening is introduced in the test.

**Step 3: Write minimal implementation**

Refine the runtime support type so its role is unmistakably example-only, for example by:

- renaming it to a decorator-oriented name
- keeping the override surface limited to runtime diagnostic fields
- wiring it only through `example_app_factory.dart`

**Step 4: Run test to verify it passes**

Run: `flutter test test/demo/demo_runtime_signal_support_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add lib/demo/demo_runtime_signal_support.dart lib/demo/example_app_factory.dart test/demo/demo_runtime_signal_support_test.dart
git commit -m "refactor: clarify runtime preset decorator semantics"
```

### Task 5: Rebuild The Example UI Around Public View + Internal Tools

**Files:**
- Modify: `lib/demo/performance_tier_demo_app.dart`
- Check: `lib/demo/performance_tier_diagnostics_scaffold.dart`
- Test: `test/widget_test.dart`

**Step 1: Write the failing test**

Extend the widget test to cover:

- public summary block is visible
- policy / signal information is still visible
- `Internal Tools` is collapsed by default
- expanding it reveals preset controls, structured log actions, and upload probe actions

**Step 2: Run test to verify it fails**

Run: `flutter test test/widget_test.dart`
Expected: FAIL until the UI is reorganized.

**Step 3: Write minimal implementation**

Restructure the page so:

- public summary appears first
- internal tools live inside a clearly marked collapsed section
- upload probe and preset controls are removed from the default first impression

**Step 4: Run test to verify it passes**

Run: `flutter test test/widget_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add lib/demo/performance_tier_demo_app.dart test/widget_test.dart
git commit -m "refactor: separate public example view from internal tools"
```

### Task 6: Prove Internal Tools Do Not Affect The Default Decision Path

**Files:**
- Create: `test/demo/public_example_mode_test.dart`
- Check: `lib/demo/example_app_factory.dart`
- Check: `lib/demo/internal_tools_controller.dart`

**Step 1: Write the failing test**

Create a new test that proves:

- default example startup does not require upload probe bootstrap
- default example startup does not require preset injection
- decision generation still succeeds when internal tools remain untouched

**Step 2: Run test to verify it fails**

Run: `flutter test test/demo/public_example_mode_test.dart`
Expected: FAIL if implicit coupling remains.

**Step 3: Write minimal implementation**

Remove any remaining hidden dependencies between the public example path and internal tools startup.

**Step 4: Run test to verify it passes**

Run: `flutter test test/demo/public_example_mode_test.dart`
Expected: PASS

**Step 5: Commit**

```bash
git add test/demo/public_example_mode_test.dart lib/demo/example_app_factory.dart lib/demo/internal_tools_controller.dart
git commit -m "test: verify public example is independent from internal tools"
```

### Task 7: Update Documentation To Match The New Boundary

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Check: `docs/plan/development_plan.md`
- Check: `docs/plan/real_device_acceptance_checklist.md`

**Step 1: Write the failing test**

For docs work, use a checklist-based validation step instead of a unit test. Write down the required wording changes:

- describe the repo as core library + lightweight example + internal tools area
- explain that upload probe is an internal test tool inside the example
- clarify the distinction between real device signals and preset-injected signals

**Step 2: Run validation to verify current docs are stale**

Run: `rg -n "Run /upload probe|Runtime signal preset|Structured diagnostics demo" README.md docs`
Expected: output shows old wording that still treats internal tooling as part of the main demo story.

**Step 3: Write minimal implementation**

Update docs to match the new public-vs-internal boundary without rewriting unrelated sections.

**Step 4: Run validation to verify docs are aligned**

Run: `rg -n "internal tools|lightweight example|preset" README.md docs`
Expected: output reflects the new wording.

**Step 5: Commit**

```bash
git add README.md docs/README.md
git commit -m "docs: align example and internal tools positioning"
```

### Task 8: Run The Full Verification Pass

**Files:**
- No code changes expected

**Step 1: Run focused demo and library tests**

Run:

```bash
flutter test test/widget_test.dart
flutter test test/demo
flutter test test/performance_tier
flutter test test/internal_upload_probe
```

Expected: PASS

**Step 2: Run full project test suite**

Run: `flutter test`
Expected: PASS

**Step 3: Format touched files**

Run: `dart format lib test docs`
Expected: formatter completes with no errors

**Step 4: Re-run critical tests after formatting**

Run:

```bash
flutter test test/widget_test.dart
flutter test
```

Expected: PASS

**Step 5: Commit**

```bash
git add lib test README.md docs
git commit -m "refactor: converge example and internal tools boundaries"
```

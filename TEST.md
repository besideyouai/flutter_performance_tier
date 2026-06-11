# Flutter Performance Tier TEST

Date: 2026-06-11
Status: current test and validation fact source
Scope: `packages/flutter_performance_tier/`

Use this document with `SPEC.md` when deciding what validation is meaningful for
the Android-first performance monitoring refactor.

## Automated Test Scope

Prefer automated tests for:

1. Dart report models, schema versioning, parsing, serialization, and migration.
2. Tiering, policy, runtime-controller, and report assembly logic that can run
   without a device.
3. MethodChannel contract tests that verify field names, missing-field fallback,
   error handling, and platform boundary behavior.
4. Android-side pure JVM/Kotlin logic that does not require launching an app,
   installing an APK, or connecting a device.
5. Offline analysis scripts and sample reports, including parse failures and
   malformed report handling.

Avoid tests whose only value is:

1. Proving Flutter or Gradle can build in this environment.
2. Repeating private implementation details without checking observable
   behavior.
3. Pretending emulator/device-only signal behavior is validated by mocks.

## Manual Validation

Manual validation is required for the Android report loop.

The expected evidence for a real-device validation pass is:

1. Device model, Android version, app variant, branch, and commit.
2. Report generation trigger used inside the example or host app.
3. On-device report directory and report filename.
4. Host-side retrieval path used:
   - direct `adb` command, or
   - `@test-android-apps` assisted collection.
5. Pulled report file path on the developer machine.
6. A short parse result or analyzer result proving the report is valid JSON and
   matches the current schema.
7. Any redacted runtime logs needed to explain failures.

Before the new report storage contract is implemented, exact commands may stay
as placeholders in implementation plans. Precursor changes such as report schema
models, parsers, storage design docs, report API skeletons, and non-device tests
can be accepted with automated evidence plus explicit deferred manual validation
when the change does not claim real-device readiness.

Once a change claims the Android report loop is ready, publishable, stable for
package consumers, or changes the concrete report storage path after V1 readiness,
update this file and `LOCAL.md` with concrete commands and include manual pull
evidence.

Current Android V1 report storage path:

- App-private directory: `files/performance_tier_reports/`
- Native directory source: Android `Context.filesDir/performance_tier_reports`
- File naming shape:
  `performance_tier_v<schemaVersion>_<utcTimestamp>_<reportId>.json`
- Default service report ids include a service session id and per-service report
  sequence. Android native write handling must avoid overwriting an existing
  file if the same file name is requested again.

Manual retrieval commands for a debug/development app:

```bash
adb shell run-as <applicationId> ls files/performance_tier_reports
adb exec-out run-as <applicationId> cat files/performance_tier_reports/<fileName> > <host-report-file>
```

For the bundled example app, `<applicationId>` is usually
`com.example.flutter_performance_tier_example`.

In the bundled example, expand `Internal Tools` and use `Generate report` to
write a report before pulling it. `List reports` refreshes the on-device file
list through the same package API, and `Copy adb command` copies the direct
retrieval command shape for the latest listed or written report.

The old OSS upload probe is no longer the primary acceptance path. It may remain
as an internal comparison tool. A change that declares the Android report loop
ready, publishable, or consumable is not accepted unless a device-side report can
be pulled to the host machine.

## Agent Boundary

Codex may:

1. Read and edit source, tests, and docs.
2. Run search, formatting, static Dart diagnostics, and non-device unit tests
   when they are useful and allowed by `AGENTS.md`.
3. Prepare exact manual validation commands for the user.

Codex must not:

1. Run `flutter run`, `flutter build`, `./gradlew build`, app install commands,
   emulator commands, simulator commands, or device execution commands.
2. Run `adb` against a real device.
3. Use `@test-android-apps` to launch, install, drive, or collect from a device
   under the current package policy.

If device evidence is needed, record the exact deferred command or plugin
workflow for the user to run.

## Bug Reports

Android performance-monitoring bug reports should include:

1. Package branch and commit.
2. App variant, application id, and whether the example app or a host app was
   used.
3. Device model, Android version, RAM class if known, thermal/power state if
   relevant, and whether developer options or battery restrictions were changed.
4. Report schema version, report filename, and host-side pulled file path.
5. Retrieval method: `adb` command or `@test-android-apps` workflow.
6. Expected behavior, actual behavior, and whether the failure is report
   generation, storage, retrieval, parsing, or analysis.
7. Redacted report sample or minimal reproduction fixture when possible.

## Related Fact Sources

- `SPEC.md`: project posture and breaking-change stance.
- `LOCAL.md`: local setup, human-only commands, adb handoff notes, secrets.
- `PACKAGING.md`: package identity, application ids, artifact boundaries.
- `GENERATION.md`: generated-file ownership and generator command boundary.
- `AGENTS.md`: execution rules and read-before-editing path.

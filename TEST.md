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
   malformed report handling. The analyzer gate has focused Python tests in
   `tool/analyze_diagnostics_test.py`, and the filled evidence markdown
   validator has focused tests in `tool/validate_android_report_evidence_test.py`.

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

Preferred host-side acceptance command after reports have been pulled:

```bash
python3 tool/analyze_diagnostics.py <pulled-report-file-or-directory> --output build/diagnostics_analysis_android_report_gate --android-report-gate
```

The command must exit `0` for a report-loop acceptance pass. It writes
`android_report_gate.md` in the output directory with PASS / FAIL details and
six evidence sections: a copyable Gate Summary, the Checks list, a
performance-report / decision summary, an Android signal snapshot covering
device, OS version, SDK, RAM, low-RAM, low-power, memory pressure, and thermal
fields, a Report Field Check, and an Identity And Gate Checklist.
Analyzer Markdown / CLI output, evidence draft builder checks, and evidence
validator checks share the gate Markdown file name, stable gate section headings,
Gate Summary keys, top status block labels and order, PASS / FAIL status values, the required single `text`
fenced Gate Summary key-value block with exact field order, table columns/order,
Report Field Check labels/order, no-issues text, checklist labels/order, and schema name from
`tool/android_report_gate_contract.py`; update that contract module before
changing the gate Markdown file name, section order, Gate Summary keys/order/fence, top status block
labels/order, summary table columns/order, Report Field Check labels/order, Checks list, Identity
Checklist labels/order, Issues empty-state text, status values, or current
performance-report schema name. The static evidence template is also covered by the evidence validator
regression tests so its gate section order, Gate Summary keys, table headers,
top status block labels/order, Gate Summary `text` fence, Report Field Check labels/order,
Checks, and Identity Checklist sections/order cannot silently drift from the shared
contract.
Evidence validator status markers, evidence draft markers, `## Run Context`,
`## App-Side Trigger`, `## Host Outputs`, `## Result`, `## Host Commands Run`,
required host-command snippets, script paths, gate-status check command, host-command stage order,
safe report filename pattern, and `App used` allowed values are centralized in
`tool/android_report_evidence_contract.py`; update that contract before changing
`android_report_evidence_status`, `android_report_evidence_draft`,
`Pass / fail`, failure category labels, host-command handoff shape, safe report
filename rules, `App used` choices, required `--application-id`, `--branch`,
`--commit`, `--output`, `--analysis-output-dir`, or `--android-report-gate`
host-command options, or the static evidence template section headings.
Use
`goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_evidence_template.md`
to record the human-run context, host commands, gate result, and field check
before claiming readiness. Readiness evidence is scoped to one selected safe
`.json` report file, matching `Copy host commands` and the evidence draft
builder. The evidence draft builder expects that file to contain one top-level
current V1 report JSON object; directory inputs, batch files, JSON arrays,
non-current schema objects, and unreadable `android_report_gate.md` files are
not valid readiness-evidence draft inputs. The pulled report file name must also
be a native-style safe `.json` report file name. The report JSON must also
include non-empty `source`, `generatedAt`, `metadata.serviceSessionId`, positive
integer `metadata.reportSequence`, a matching `reportId`, and non-empty
`decision.decidedAt`, plus tier, confidence, runtime status, and the current
Android gate-required device, OS, RAM, SDK, low-RAM, low-power, memory pressure,
and thermal signals. `generatedAt` must be a parseable UTC ISO-8601 timestamp,
`decision.decidedAt` must be a parseable ISO-8601 date-time timestamp, and
`generatedAt` must not be earlier than `decision.decidedAt` when both timestamps
carry timezone information. The `android_report_gate.md`
must also be a PASS gate for that same selected report and must describe exactly
one performance report row; its top status block must match Gate Summary, and
its Performance Reports table Source must match the pulled report path and
selected report file name. The Performance Reports table source tag, service
session, sequence, tier, confidence, runtime, generated timestamp, and decision
timestamp must also match the selected report JSON. The Android Signals table
report id, platform, device, OS version, SDK, RAM, low-RAM, low-power, memory
pressure, and thermal fields must also match the selected report JSON. The
Report Field Check schema, identity, decision, Android signal, and runtime
fields must also match the selected report JSON. Every Identity And Gate
Checklist item must be `yes`, and the `## Issues` section must only contain
`- None.`. The `## Checks` section must retain the analyzer gate checklist
unchanged. The preferred path is to
generate a draft from the pulled report and gate output, then review it.
`build_android_report_evidence.py` requires the application id to be passed
explicitly with the same value recorded in the run context. It reads branch and
commit from git; when that is unavailable, pass `--branch <branch>` and
`--commit <commit>` explicitly. Prefer keeping explicit branch / commit in the
reviewed evidence command when the values are known:

```bash
python3 tool/build_android_report_evidence.py <pulled-report-file> \
  --analysis-output-dir build/diagnostics_analysis_android_report_gate \
  --branch <branch> \
  --commit <commit> \
  --output goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md \
  --application-id <applicationId>
```

After filling or reviewing the evidence file, run
`python3 tool/validate_android_report_evidence.py <filled-evidence.md>`; it must
return `android_report_evidence_status=PASS` before the evidence can be used to
close or mark the Android report loop ready. The validator also checks that the
`## Run Context` section includes the app variant, the `## App-Side Trigger`
fields still record `Internal Tools` -> `Generate report`,
`Internal Tools` -> `List reports`, `Internal Tools` -> `Copy host commands`,
and `files/performance_tier_reports/`, the `## Host Outputs` section records the
pulled report path, analyzer output directory, analyzer exit code, and gate
status, the recorded host command block includes the
fail-fast start, report-directory listing, host-directory preparation, pull,
non-empty pulled-file check, analyzer gate failure capture, analyzer gate, gate
status capture, fail-fast resume, gate Markdown print, gate status check,
evidence draft builder, and evidence validator commands in the expected order,
the copied command block is a single `bash` fenced code block, contains no
unexpected commands and no placeholder
tokens such as `<fileName>` or `<applicationId>`, the command block still
parses as valid shell tokens, and references the same application id,
report file name, pulled report path, and
analyzer output directory recorded in the evidence, the adb list command has the
exact `adb shell run-as <applicationId> ls files/performance_tier_reports`
shape, the adb pull command has the exact
`adb exec-out run-as <applicationId> cat files/performance_tier_reports/<fileName> > <pulled-report-path>`
shape, analyzer / evidence builder / evidence validator commands use their exact
expected argv shape without extra arguments, the evidence builder command passes
the same `--application-id`, `--branch`, and `--commit` recorded in the run
context, builder `--branch` / `--commit` values are present together, builder
`--output` is present, the pulled report path
basename matches the recorded report file name, the evidence validator command targets the same evidence file produced by
the draft builder, the Android Report Gate status block matches Gate Summary,
the status block fields stay directly under `# Android Report Gate` with the
shared field order and no extra labels, the
Gate Summary section remains a single `text` fenced key-value block with the
shared field order and no extra keys, the
`## Checks` section is present and unchanged, the `## Issues` section contains
only `- None.`, the Gate Summary row counts and summary tables describe
exactly one selected report, both summary table columns still match the shared
order with no extra, duplicate, or reordered columns, the Performance Reports table Source still matches
the pulled report path and the same selected report file name, the Performance
Reports table still matches the Report Field Check report identity, service
session, decision, runtime, and timestamp fields, the Android Signals table
still matches the Report Field Check report id, platform, device, OS version,
SDK, RAM, low-RAM, low-power, memory pressure, and thermal fields, the Report
Field Check has exactly one `### <reportId>` heading matching the current
selected report, the Report Field Check field labels stay inside
`## Report Field Check`, match the shared field order with no extra, duplicate,
or reordered labels, the Report Field Check still reports current V1 schema,
Android platform, and the same device model, Android version, and SDK recorded
in the run context, the Identity And Gate Checklist labels stay inside
`## Identity And Gate Checklist`, match the shared checklist order with no
extra, duplicate, or reordered labels, and the `## Result` section itself records `Pass` with failure
category `none`; matching Run Context, App-Side Trigger, Host Outputs, or Result
labels outside their named sections do not count, so stale,
incomplete, inconsistent,
non-executable, out-of-order, mismatched-source, or multi-report evidence cannot
close the loop.
When passing a directory, keep it dedicated to pulled V1 performance reports;
the gate rejects legacy AI diagnostics, decision-only sessions, structured-log
sessions, and other non-performance-report rows in the same input.

Before the new report storage contract is implemented, exact commands may stay
as placeholders in implementation plans. Precursor changes such as report schema
models, parsers, storage design docs, report API skeletons, and non-device tests
can be accepted with automated evidence plus explicit deferred manual validation
when the change does not claim real-device readiness.

Once a change claims the Android report loop is ready, publishable, stable for
package consumers, or changes the concrete report storage path after V1 readiness,
update this file and `LOCAL.md` with concrete commands, a pulled real-device
report, Android report gate PASS evidence, and filled goal evidence that
validates with `android_report_evidence_status=PASS`.

Current Android V1 report storage path:

- App-private directory: `files/performance_tier_reports/`
- Native directory source: Android `Context.filesDir/performance_tier_reports`
- File naming shape:
  `performance_tier_v<schemaVersion>_<utcTimestamp>_<reportId>.json`
- Default service report ids include a service session id and per-service report
  sequence. Android native write handling must avoid overwriting an existing
  file if the same file name is requested again.
- Native write results must either omit `reportId` or echo the requested report
  id. `MethodChannelPerformanceReportStore` rejects mismatched non-empty
  `reportId` values so a platform implementation cannot silently swap report
  identity after Dart has assembled the V1 payload.
- Android native write handling rejects MethodChannel calls whose
  `schemaVersion` is not the current V1 integer or whose `reportId` is blank,
  so malformed direct channel calls cannot land files that the host gate will
  later reject as non-V1 or unidentifiable reports.
- Native write and list metadata must return non-blank `fileName` /
  `relativePath` strings and a positive integer `bytes` value. Stringified
  numbers, zero-byte metadata, and blank path fields are treated as malformed
  platform results, because they are not safe host-pull targets.
- `listPerformanceReports` results are normalized in Dart by `modifiedAt`
  descending, with missing timestamps last, so callers see a stable newest-first
  list even if a platform implementation returns unordered metadata.
- `listPerformanceReports` results must be a list of map-like file metadata
  items with string keys. `MethodChannelPerformanceReportStore` rejects
  malformed non-map list items, non-string metadata keys, and incomplete
  metadata instead of silently dropping platform bugs.
- Android native `listPerformanceReports` reuses the same safe `.json` file-name
  predicate as `writePerformanceReport`, so manually introduced or legacy
  unsafe JSON names in the app-private directory are not exposed as host-pull
  candidates.
- Retention policy: V1 does not enforce automatic cleanup. Reports remain in the
  app-private directory until app data is cleared, the app is uninstalled, or a
  human explicitly deletes report files during validation. A future automatic
  retention policy must update this file, `LOCAL.md`, platform contract tests,
  and the goal document before it is treated as part of readiness.

Manual retrieval commands for a debug/development app:

```bash
adb shell run-as '<applicationId>' ls 'files/performance_tier_reports'
adb exec-out run-as '<applicationId>' cat 'files/performance_tier_reports/<fileName>' > '<host-report-file>'
```

Manual cleanup command shape for local validation only:

```bash
adb shell run-as '<applicationId>' rm 'files/performance_tier_reports/<fileName>'
```

For the bundled example app, `<applicationId>` is usually
`com.example.flutter_performance_tier_example`.

In the bundled example, expand `Internal Tools` and use `Generate report` to
write a report before pulling it. `List reports` refreshes the on-device file
list through the same package API, and `Copy host commands` copies the host
handoff commands for the latest listed or written report. The freshly written
safe report wins; otherwise the latest safe listed `.json` report by
`modifiedAt` is used. The commands create the local output directory, pull the
JSON with adb, verify the pulled file is non-empty, then run the analyzer
`--android-report-gate`, and print `android_report_gate.md` so the PASS / FAIL
status, summary tables, field check, and identity checklist are visible in the
terminal. Copied host commands start with `set -e` for retrieval and file checks, temporarily preserve the
analyzer exit code so FAIL reports are still printed, then fail the command block
when the saved analyzer status is non-zero. They also quote shell path arguments
so report paths and output directories remain stable when a human customizes
them.
After a PASS gate, the copied command block runs
`tool/build_android_report_evidence.py` and
`tool/validate_android_report_evidence.py` so a reviewed evidence draft is
created under the goal evidence folder and immediately checked. The host
commands must keep the full evidence-contract order: start fail-fast, list the
report directory, prepare the host report directory, pull report, verify
non-empty output, allow analyzer gate failure capture, run the analyzer gate,
capture gate status, resume fail-fast, print the gate Markdown, check the gate
status, build the evidence draft, then validate the evidence. The copied builder
command resolves the host checkout branch and commit with
`$(git branch --show-current)` and `$(git rev-parse --short HEAD)`, then passes
those values through `--branch` / `--commit` for validator review. The builder uses
`decision.deviceSignals.osVersion` as the Android version by default; if a
legacy report lacks that field, the evidence validator keeps the draft from
being used as readiness evidence until the context is corrected. The example
only generates host commands for native-style safe `.json` report file names;
unexpected names from custom service implementations must be treated as invalid
handoff targets.

After pulling the JSON, run `tool/analyze_diagnostics.py` with
`--android-report-gate`. The gate requires at least one V1 Android performance
report, no parse issues, no non-performance-report session rows in the gate
input, non-fallback Android signal data, and required report / decision /
runtime fields with expected wire values. `schemaVersion` must be JSON integer
`1`, not a string or floating-point value. Top-level `generatedAt` must be a
JSON string containing a parseable ISO-8601 UTC timestamp, while
`decision.decidedAt` must be a JSON string containing a parseable ISO-8601
date-time timestamp rather than a date-only string. When both timestamps include
timezone information, `generatedAt` must be at or after `decision.decidedAt`.
`reportId`, `source`, `metadata.serviceSessionId`, and `deviceModel` must be
JSON strings that remain non-empty after trimming whitespace.
`metadata.reportSequence` must be a positive JSON integer, and `reportId` must
match `<metadata.serviceSessionId>-report-<metadata.reportSequence>`.
Across a gate input file set, `reportId` values and
`metadata.serviceSessionId` / `metadata.reportSequence` pairs must be unique.
Tier, confidence, runtime status, platform, memory pressure state, and SDK 29+
thermal state must be non-empty JSON strings in the package-defined wire ranges.
Current required Android signal fields include device model, OS version, RAM,
low-RAM classification, SDK, low-power mode, and memory pressure. RAM and SDK
must be JSON integers greater than zero; low-RAM and low-power mode must be JSON
booleans; memory pressure level must be a JSON integer.
Thermal state and thermal state level are required by the gate when
`sdkInt >= 29`; thermal state level must be a JSON integer in the expected
Android report range. Thermal fields may be absent on older Android versions.
`mediaPerformanceClass` is collected when Android reports it, but may be absent
or zero on devices that do not declare a class, so the gate does not require it.

`PerformanceReport` construction is intentionally stricter than older report
helpers: only the current V1 `schemaName` and `schemaVersion` are accepted, and
blank `reportId` or `source` values are rejected before a report can be written. If
`metadata.serviceSessionId` or `metadata.reportSequence` is present, both fields
must be present and `reportId` must match
`<metadata.serviceSessionId>-report-<metadata.reportSequence>`. `generatedAt`
must be at or after `decision.decidedAt`, matching the Android report gate
timestamp rule before a report can be written. Custom report assemblers should
use `PerformanceReport.buildServiceReportId()` or provide the same service id /
sequence identity shape with trusted timestamps covered by tests.

The old OSS upload probe is no longer the primary acceptance path. It may remain
as an internal comparison tool. A change that declares the Android report loop
ready, publishable, or consumable is not accepted unless a device-side report can
be pulled to the host machine, accepted by the Android report gate, and recorded
in filled goal evidence that validates with
`android_report_evidence_status=PASS`.

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

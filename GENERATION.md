# Flutter Performance Tier GENERATION

Date: 2026-06-11
Status: current generated-file fact source
Scope: `packages/flutter_performance_tier/`

This document owns generated-file rules for `flutter_performance_tier`.

## Current Generated Content

The main committed source tree should be source-first. Generated outputs are
usually ignored and should not be edited by hand.

Known generated or generator-owned content:

- `example/lib/internal_upload_probe/internal_upload_probe_env.g.dart` is generated
  from `example/lib/internal_upload_probe/internal_upload_probe_env.dart`.
- `tool/testdata/sample_ai_report.json` is a curated legacy fixture, not live
  device output.
- `tool/testdata/sample_performance_report.json` is a curated V1 performance
  report fixture, not live device output.

Before regenerating upload-probe env code, note that
`tool/internal_upload_probe_secure_env.json` still references the pre-split path
`lib/internal_upload_probe/internal_upload_probe_env.dart`. Reconcile that config
with the current `example/lib/internal_upload_probe/` path as a dedicated
generation task before running any generator.

## Ignored Generated Content

Ignored generated or machine-local outputs include:

- `.dart_tool/`
- `build/`
- `example/.dart_tool/`
- `example/build/`
- Android `.gradle/`, `captures/`, `.cxx/`, and `local.properties`
- iOS `Pods/`, `Flutter/Generated.xcconfig`, `.symlinks/`, and DerivedData-style
  outputs
- `.env.internal_upload_probe`
- `encryption_key.json`
- Android keystores and key property files

## Generators

### Internal Upload Probe Secure Env

1. Source files:
   - `example/lib/internal_upload_probe/internal_upload_probe_env.dart`
   - `.env.internal_upload_probe` when present locally
   - generator configuration under `tool/internal_upload_probe_secure_env.json`
2. Generated output:
   - `example/lib/internal_upload_probe/internal_upload_probe_env.g.dart`
3. Command:
   - The exact generator command is not currently documented in this package.
     Do not infer it from old paths.
4. Codex may run it:
   - No, not until the command and paths are made explicit.
5. Commit policy:
   - Commit the generated Dart file only when the generator source/config change
     intentionally changes the runtime env surface.
6. Required validation:
   - Unit tests covering upload-probe runtime config and auth setup.

### Offline Diagnostics Analysis

1. Source files:
   - `tool/analyze_diagnostics.py`
   - redacted fixtures under `tool/testdata/`
2. Generated output:
   - `build/diagnostics_analysis/` by default, or a caller-provided output path.
3. Command:

```bash
python3 tool/analyze_diagnostics.py tool/testdata/sample_ai_report.json --output build/diagnostics_analysis_sample
```

Android report gate smoke:

```bash
python3 tool/analyze_diagnostics.py tool/testdata/sample_performance_report.json --output build/diagnostics_analysis_gate_sample --android-report-gate
```

Analyzer unit tests:

```bash
python3 tool/analyze_diagnostics_test.py
```

Evidence validator unit tests:

```bash
python3 tool/validate_android_report_evidence_test.py
```

The evidence validator rejects drafts that violate the current evidence
contract. The recorded host command block must be one `bash` fenced block with
no placeholders or unexpected commands, must preserve the copied order from the
example app, and must include start fail-fast, report directory listing, host
directory preparation, report pull, non-empty file check, analyzer gate failure
capture, analyzer gate, gate status capture, fail-fast resume, gate Markdown
print, gate status check, evidence draft builder, and evidence validator stages.
The gate Markdown file name and required host-command snippets are owned by
`tool/android_report_evidence_contract.py` and include the analyzer
`--android-report-gate` option plus the builder `--analysis-output-dir`,
`--application-id`, `--branch`, `--commit`, and `--output` options.

The validator also requires host commands to reference the same application id,
report file name, pulled report path, analyzer output directory, and evidence
file recorded in the evidence. Android Report Gate content must keep the shared
section order, top status block labels/order, single `text` fenced Gate Summary,
summary table columns/order, Report Field Check labels/order, Identity Checklist
labels/order, complete `## Checks`, and an empty PASS `## Issues` section of
`- None.`. The evidence must remain scoped to one selected safe `.json` report,
using the filename pattern owned by `tool/android_report_evidence_contract.py`.
`App used` must choose one of the same contract-owned values. Performance
Reports, Android Signals, Report Field Check, run context, app-side trigger,
host outputs, and Result values must agree with each other. The reviewed Result
section must record `Pass` with failure category `none`.

Evidence draft builder. The application id must be passed explicitly with
`--application-id`; the builder no longer supplies an implicit example app id.
Branch and commit are read from git by default; if unavailable, pass
`--branch <branch>` and `--commit <commit>`. Generated evidence records
explicit branch / commit in the copied builder command for reproducibility:

```bash
python3 tool/build_android_report_evidence.py tool/testdata/sample_performance_report.json \
  --analysis-output-dir build/diagnostics_analysis_gate_sample \
  --branch codex/android-report-loop \
  --commit abc1234 \
  --output build/android_report_loop_evidence_sample.md \
  --application-id com.example.flutter_performance_tier_example
```

Evidence draft builder unit tests:

```bash
python3 tool/build_android_report_evidence_test.py
```

4. Codex may run it:
   - Yes, if Python is available and no real device, network, build, install, or
     secret-bearing input is involved.
5. Commit policy:
   - Do not commit generated analysis output unless a task explicitly asks for a
     small, redacted expected-output fixture.
   - Do not commit generated evidence drafts unless they are the intended
     redacted real-device goal evidence and are linked from `goal.html`.
6. Required validation:
   - Parser/analyzer output should match the current report schema expectations
     documented in `TEST.md`.
   - Generated evidence drafts must pass
     `tool/validate_android_report_evidence.py` before they are treated as
     readiness evidence.

## Command Boundary

Generator or analysis commands must not be used as a back door to run Flutter
builds, app execution, Gradle builds, installs, emulators, simulators, `adb`, or
device collection. Those remain human-only under `AGENTS.md`, `TEST.md`, and
`LOCAL.md`.

## Change Rules

1. Edit generator source/config first, then regenerate outputs.
2. Do not hand-edit `.g.dart` generated files except for emergency inspection
   notes in a throwaway branch.
3. Do not commit machine-local outputs or pulled real-device reports.
4. When adding a new report generator or device-side exporter, document its
   source, output path, command, commit policy, and validation here before
   relying on it in tests or release notes.

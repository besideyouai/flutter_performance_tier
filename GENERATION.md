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
python tool/analyze_diagnostics.py tool/testdata/sample_ai_report.json --output build/diagnostics_analysis_sample
```

4. Codex may run it:
   - Yes, if Python is available and no real device, network, build, install, or
     secret-bearing input is involved.
5. Commit policy:
   - Do not commit generated analysis output unless a task explicitly asks for a
     small, redacted expected-output fixture.
6. Required validation:
   - Parser/analyzer output should match the current report schema expectations
     documented in `TEST.md`.

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

# Flutter Performance Tier LOCAL

Date: 2026-06-11
Status: current local setup and run fact source
Scope: `packages/flutter_performance_tier/`

This document owns local setup, debug entries, machine-local files, and command
handoff notes for `flutter_performance_tier`.

## Local Setup

- Work from the repo-root Dart workspace when resolving dependencies:

```bash
cd <repo-root>
flutter pub get
```

- The package itself lives at:

```bash
cd <repo-root>/packages/flutter_performance_tier
```

- The example app remains an internal demo and validation surface, not a
  standalone public template.

## Human-Only Commands

These commands are valid local workflows for a human, but Codex must not run
them under the current project policy:

```bash
flutter run -t example/lib/main.dart
flutter run -t example/lib/internal_upload_probe_main.dart
flutter build apk --release
```

Future Android report retrieval and cleanup commands are also human-only until
the package policy changes:

```bash
adb shell run-as '<applicationId>' ls 'files/performance_tier_reports'
adb exec-out run-as '<applicationId>' cat 'files/performance_tier_reports/<fileName>' > '<host-report-file>'
adb shell run-as '<applicationId>' rm 'files/performance_tier_reports/<fileName>'
```

For the bundled example app, `<applicationId>` is usually
`com.example.flutter_performance_tier_example`.

`@test-android-apps` may be used by a human-directed validation workflow to
collect reports from a connected Android target, but the resulting artifact must
be equivalent to the direct `adb` retrieval path described in `TEST.md`.
Record the run with
`goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_evidence_template.md`
before using the result as readiness evidence.

## Codex Boundary

Codex may run local file inspection, formatting, static diagnostics, and
non-device tests when useful and allowed by `AGENTS.md`.

Codex must not run build, app execution, install, emulator, simulator, `adb`, or
device collection commands in this package. When those commands are needed,
Codex should write the exact command and mark validation as deferred to the user.

## Debug Configuration

- Public example entry: `example/lib/main.dart`.
- Internal upload-probe entry: `example/lib/internal_upload_probe_main.dart`.
- Android report loop trigger: in the public example, expand `Internal Tools`
  and use `Generate report`, `List reports`, and `Copy host commands`.
  Copied host commands shell-quote the application id, device report path, host
  report path, analyzer output directory, gate Markdown path, and evidence
  output path. They start with `set -e`, list the app-private report directory,
  create the host pull directory, verify the pulled report file is non-empty
  before the analyzer gate, temporarily capture the analyzer gate status, print
  `android_report_gate.md` even when the analyzer gate fails, then restore
  fail-fast and fail the command block with the saved analyzer exit status.
  After a PASS gate, the command block builds and validates the goal evidence
  draft. The builder command resolves the current host checkout with
  `$(git branch --show-current)` and `$(git rev-parse --short HEAD)` and passes
  the resulting `--branch` / `--commit` explicitly. Keep the copied order intact: start fail-fast, list the report
  directory, prepare the host directory, pull report, verify non-empty output,
  allow analyzer gate failure capture, run analyzer gate, capture gate status,
  resume fail-fast, print the gate Markdown, check gate status, build evidence,
  then validate evidence. If the evidence builder cannot resolve git branch or
  commit from the host checkout, rerun the builder command with explicit
  `--branch <branch>` and `--commit <commit>` before validating the evidence.
  They are only generated for native-style safe `.json` report file names. The
  freshly written safe report is preferred; otherwise the latest safe listed
  report by `modifiedAt` is used.
- Upload-probe configuration may come from `--dart-define` values or the
  internal secure env source in `example/lib/internal_upload_probe/`.
- `.env.internal_upload_probe` and `encryption_key.json` are machine-local secret
  files and must not be committed.
- Android V1 performance reports are written to the app-private
  `files/performance_tier_reports/` directory. V1 intentionally does not enforce
  automatic retention cleanup: files remain until app data is cleared, the app
  is uninstalled, or a human removes specific reports during validation.

## Secrets and Local Files

Ignored local files include:

- `.env.internal_upload_probe`
- `encryption_key.json`
- `.dart_tool/`
- `build/`
- Android `local.properties`
- Android keystores and key property files

Do not put auth tokens, passwords, signing keys, device-private data, or pulled
production reports into committed fixtures. Redact or synthesize samples before
adding them under `tool/testdata/`.

## Related Fact Sources

- `SPEC.md`: current project direction and compatibility stance.
- `TEST.md`: validation scope and report gate / evidence requirements.
- `GENERATION.md`: generated-file and secure-env generator rules.
- `PACKAGING.md`: package identity and artifact boundaries.

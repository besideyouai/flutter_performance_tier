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

Future Android report retrieval commands are also human-only until the package
policy changes:

```bash
adb shell run-as <applicationId> ls files/performance_tier_reports
adb exec-out run-as <applicationId> cat files/performance_tier_reports/<fileName> > <host-report-file>
```

For the bundled example app, `<applicationId>` is usually
`com.example.flutter_performance_tier_example`.

`@test-android-apps` may be used by a human-directed validation workflow to
collect reports from a connected Android target, but the resulting artifact must
be equivalent to the direct `adb` retrieval path described in `TEST.md`.

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
  and use `Generate report`, `List reports`, and `Copy adb command`.
- Upload-probe configuration may come from `--dart-define` values or the
  internal secure env source in `example/lib/internal_upload_probe/`.
- `.env.internal_upload_probe` and `encryption_key.json` are machine-local secret
  files and must not be committed.
- Android V1 performance reports are written to the app-private
  `files/performance_tier_reports/` directory. The current implementation lists
  and writes files but does not enforce retention cleanup yet.

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
- `TEST.md`: validation scope and report-pull evidence requirements.
- `GENERATION.md`: generated-file and secure-env generator rules.
- `PACKAGING.md`: package identity and artifact boundaries.

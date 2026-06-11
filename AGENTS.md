# Repository Guidelines

## Scope
- This file covers `packages/flutter_performance_tier/` only.
- Read this file first when working in this package subtree.
- Workspace-level coordination rules live in `../../AGENTS.md`.
- Read `../../AGENTS.md` as needed when workspace-level coordination, ownership, or validation policy matters.
- This package is a member of the repo-root Dart workspace; keep `resolution: workspace` aligned with the root `pubspec.yaml`.

## Read Before Editing
- Read `SPEC.md` before interpreting project stage, compatibility posture, Android monitoring direction, or breaking-change tolerance.
- Read `TEST.md` before adding tests, judging validation scope, investigating runtime bugs, or discussing adb / `@test-android-apps` report collection.
- Read `LOCAL.md` before changing local setup, debug entries, run instructions, adb handoff notes, secrets, or machine-local files.
- Read `PACKAGING.md` before changing package identity, Android/iOS identifiers, signing, versioning, artifact naming, install/update behavior, or deployment docs.
- Read `GENERATION.md` before adding, editing, deleting, or validating generated files, generated report outputs, secure-env generation, or generation commands.
- Use `docs/README.md` for historical plans, design notes, progress logs, and archived discussion.

## Reverse Discovery
- If you start in `example/`, read `example/AGENTS.md` first, then come back here.
- Use this file for package-local rules.
- Use `../../AGENTS.md` for workspace-wide coordination, ownership, and validation policy when relevant to the task.

## Project Structure & Module Organization
- `lib/performance_tier/` contains the core package, split into `config/`, `engine/`, `model/`, `policy/`, and `service/`.
- `lib/flutter_performance_tier.dart` is the package-level barrel export for public consumption.
- `android/src/main/kotlin/com/example/flutter_performance_tier/` and `ios/Classes/` hold the plugin-side native signal collection implementation.
- `example/lib/` is the example app, including public demo UI and internal validation tools.
- `test/performance_tier/` covers tiering logic and platform contract integrity; example-facing widget/demo tests live under `example/test/`.
- Treat `.dart_tool/` and `build/` as generated output.

## Build, Test, and Development Commands
- Current project posture and validation authority live in `SPEC.md` and `TEST.md`.
- Run dependency resolution from the workspace root when working in this workspace: `cd ../.. && flutter pub get`.
- Do not run `flutter analyze` by default; if static analysis is relevant, provide the exact command for the user to run.
- `dart format lib test example/lib example/test` - format source and test files before commit.
- `flutter test test/performance_tier` - run core package tests.
- `cd example && flutter test` - run example widget/demo/internal-tools tests.
- Human-only: `flutter run -t example/lib/main.dart` launches the public example app locally.
- Human-only: `flutter run -t example/lib/internal_upload_probe_main.dart` launches the isolated internal upload probe entrypoint.
- Human-only: `flutter build apk --release` builds a release APK for packaging checks.
- Human-only: adb report-pull commands and `@test-android-apps` device collection workflows for Android performance reports.
- Agents must not run the human-only build, run, install, simulator, emulator, adb, or device commands; hand them off when manual validation is needed.

## Coding Style & Naming Conventions
- Follow `analysis_options.yaml` (`package:flutter_lints/flutter.yaml`).
- Use 2-space indentation in Dart; prefer trailing commas to keep formatter-friendly diffs.
- Naming: files in `snake_case.dart`, types in `PascalCase`, members in `camelCase`.
- Keep model and tier decision objects immutable and explicit; avoid hidden side effects in engine logic.

## Testing Guidelines
- Use `flutter_test` with behavior-focused test names (example: `returns low tier when low-ram device is reported`).
- Mirror `lib/` structure under `test/` when adding coverage.
- Add deterministic tests for new rules in engine, policy resolver, and service orchestration.
- No enforced coverage threshold yet; increase coverage with each feature or bug fix.

## Commit & Pull Request Guidelines
- Prefer Conventional Commit prefixes, as seen in history (for example, `feat: scaffold performance tier...`).
- Keep commit messages concise and imperative; split unrelated changes into separate commits.
- PRs should include purpose, key changes, and validation steps run (`flutter test`, plus any manually deferred `flutter analyze` command if relevant).
- Link related issues or tasks, and include screenshots or recordings for UI-visible changes.

## Security & Configuration Tips
- Never commit secrets, keystores, or signing credentials.
- Keep MethodChannel contracts synchronized across Dart and platform code (`performance_tier/device_signals`).

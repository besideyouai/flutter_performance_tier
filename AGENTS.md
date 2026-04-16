# Repository Guidelines

## Scope
- This file covers `flutter_performance_tier/` only.
- Workspace-level coordination rules live in `../AGENTS.md`.

## Project Structure & Module Organization
- `lib/performance_tier/` contains the core package, split into `config/`, `engine/`, `model/`, `policy/`, and `service/`.
- `lib/flutter_performance_tier.dart` is the package-level barrel export for public consumption.
- `android/src/main/kotlin/com/example/flutter_performance_tier/` and `ios/Classes/` hold the plugin-side native signal collection implementation.
- `example/lib/` is the example app, including public demo UI and internal validation tools.
- `test/performance_tier/` covers tiering logic and platform contract integrity; example-facing widget/demo tests live under `example/test/`.
- Treat `.dart_tool/` and `build/` as generated output.

## Build, Test, and Development Commands
- `flutter pub get` - install or update dependencies from `pubspec.yaml`.
- Do not run `flutter analyze` by default; if static analysis is relevant, provide the exact command for the user to run.
- `dart format lib test example/lib example/test` - format source and test files before commit.
- `flutter test test/performance_tier` - run core package tests.
- `cd example && flutter test` - run example widget/demo/internal-tools tests.
- `flutter run -t example/lib/main.dart` - launch the public example app locally.
- `flutter run -t example/lib/internal_upload_probe_main.dart` - launch the isolated internal upload probe entrypoint.
- `flutter build apk --release` - build a release APK for packaging checks.

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

# Flutter Performance Tier SPEC

Date: 2026-06-11
Status: current project fact source
Scope: `packages/flutter_performance_tier/`

This document owns the current project posture for `flutter_performance_tier`.
It explains what the package is optimizing for now, what may break, and which
assumptions should guide implementation decisions.

It is not the execution rulebook, a detailed architecture document, a build
manual, or a backend API contract.

## Current Stage

`flutter_performance_tier` is entering an Android-first performance monitoring
refactor stage.

The previous direction centered on reusable tier decisions, structured logs,
example diagnostics JSON, and optional upload probe validation. That work remains
useful as reference material, but it is no longer the main delivery shape.

The next primary outcome is an Android device-side performance monitoring loop:
the Flutter package and Android plugin should be able to produce structured
performance reports on device, and those reports must be retrievable to a
developer machine through either direct `adb` commands or an assisted
`@test-android-apps` workflow.

**BREAKING CHANGE POSTURE:** breaking changes are explicitly allowed. Do not keep
unclear compatibility layers only to preserve old APIs, old example flows, old
MethodChannel payloads, or old upload-probe behavior. Prefer clean boundaries and
clear migration notes.

## Project Goal

1. Provide Android-native performance signal collection suitable for real-device
   investigation, including device capability, memory pressure, thermal state,
   runtime health, frame stability, and report-generation metadata.
2. Produce versioned structured reports that can be stored on the Android device
   and pulled to the host machine deterministically.
3. Make the host-side retrieval path first-class: direct `adb` usage and
   `@test-android-apps` assisted collection should produce equivalent report
   artifacts.
4. Keep the Dart API focused on orchestration, report metadata, tier/policy
   consumption, and testable transformations.
5. Preserve enough offline analysis support that pulled reports can be inspected
   by scripts such as `tool/analyze_diagnostics.py` or its successor.

## Non-Goals

1. Preserving the old public API surface when it blocks the Android report
   pipeline.
2. Treating OSS upload or the example upload probe as the primary acceptance
   path.
3. Requiring iOS parity before the Android monitoring and report retrieval loop
   is stable.
4. Building a cloud dashboard, fleet analytics platform, or ML-based tier model
   in this package.
5. Supporting web, desktop, or Fuchsia performance monitoring beyond safe
   fallback behavior.

## Decision Principles

1. Android report retrieval is the current north star. If a design improves
   in-app display but weakens report capture, choose the report loop.
2. Reports need explicit schema versions, deterministic naming, and documented
   storage/retrieval paths.
3. Native Android collection should own Android-only signals. Dart should avoid
   pretending platform facts are portable when they are not.
4. Runtime logs are useful evidence, but logs alone are not the report contract.
5. Privacy and debugging value must be balanced up front. Reports may include
   device model, Android version, memory, thermal, frame, and tiering data; they
   must not include account tokens, passwords, signing material, or unrelated
   personal data by default.
6. Migration cost is acceptable during this phase when it buys simpler APIs,
   clearer storage, or better report integrity.

## Required Considerations

- Current Android package/plugin identity is documented in `PACKAGING.md`.
- Current Android minimum SDK is `24`; changing it is allowed only with an
  explicit breaking-change note and updated validation docs.
- The current MethodChannel name, `performance_tier/device_signals`, is not a
  permanent contract during this refactor. If it changes, update Dart tests,
  Android implementation, package docs, and migration notes together.
- Every report storage design must document:
  - the on-device directory,
  - the file naming pattern,
  - whether the file is app-private or externally readable,
  - the exact host-side retrieval command or `@test-android-apps` collection
    procedure,
  - the cleanup/retention policy.
- iOS should remain compiling when practical, but Android monitoring quality has
  priority over cross-platform symmetry in this stage.

## Documentation Authority

- `SPEC.md` owns project posture, compatibility stance, current goals, and
  non-goals.
- `TEST.md` owns validation scope, manual device evidence, report pull
  requirements, and agent command boundaries.
- `LOCAL.md` owns local setup, debug entries, adb handoff notes, and secrets.
- `PACKAGING.md` owns package identity, versioning, signing, and artifact rules.
- `GENERATION.md` owns generated-file policy.
- `README.md` stays focused on package consumers and should not duplicate
  volatile project status.
- `docs/plan/` and `docs/plans/` are historical or execution-plan material unless
  a file explicitly says otherwise.

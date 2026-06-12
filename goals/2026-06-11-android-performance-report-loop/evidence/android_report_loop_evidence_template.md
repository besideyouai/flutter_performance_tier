# Android Report Loop Evidence Template

Use this template after a human runs the example app on a real Android device,
generates a report, pulls the JSON to the host machine, and runs the analyzer
gate. Do not paste secrets, auth tokens, signing material, account identifiers,
or unredacted production reports.

Readiness evidence is scoped to one selected safe `.json` report file. Directory
inputs can be useful for analyzer triage, but the final reviewed evidence must
bind to the single report file pulled by the copied host commands.
Keep the copied host commands in order: start fail-fast, list the report
directory, prepare the host report directory, pull the report, verify the pulled
file is non-empty, allow analyzer gate failure capture, run analyzer gate,
capture gate status, resume fail-fast, print gate Markdown, check gate status,
build the evidence draft, then validate the evidence.
Required host command order: start fail-fast -> list report directory -> prepare host report directory -> pull report -> nonempty report check -> allow analyzer gate failure capture -> analyzer gate -> capture gate status -> resume fail-fast -> gate markdown print -> gate status check -> evidence builder -> evidence validator.

## Run Context

- Date:
- Branch:
- Commit:
- App used: example app / host app
- App variant:
- Application id:
- Device model:
- Android version:
- SDK int:
- RAM class / total RAM if known:
- Thermal / power state if relevant:

## App-Side Trigger

- Trigger path: `Internal Tools` -> `Generate report`
- Report list refreshed with: `Internal Tools` -> `List reports`
- Copy source: `Internal Tools` -> `Copy host commands`
- On-device directory: `files/performance_tier_reports/`
- Report file name:
- Copied commands were available for a safe `.json` report file name: yes / no

## Host Commands Run

```bash
set -e
adb shell run-as '<applicationId>' ls 'files/performance_tier_reports'
mkdir -p 'build/pulled_performance_reports'
adb exec-out run-as '<applicationId>' cat 'files/performance_tier_reports/<fileName>' > 'build/pulled_performance_reports/<fileName>'
test -s 'build/pulled_performance_reports/<fileName>'
set +e
python3 tool/analyze_diagnostics.py 'build/pulled_performance_reports/<fileName>' --output 'build/diagnostics_analysis_android_report_gate' --android-report-gate
gate_status=$?
set -e
cat 'build/diagnostics_analysis_android_report_gate/android_report_gate.md'
test "$gate_status" -eq 0
python3 tool/build_android_report_evidence.py 'build/pulled_performance_reports/<fileName>' --analysis-output-dir 'build/diagnostics_analysis_android_report_gate' --branch '<branch>' --commit '<commit>' --output 'goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md' --application-id '<applicationId>'
python3 tool/validate_android_report_evidence.py 'goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md'
```

## Host Outputs

- Pulled report path:
- Analyzer output directory:
- Analyzer exit code:
- `android_report_gate.md` status: PASS / FAIL

Paste the status block, summary tables, report field check, and identity
checklist from `android_report_gate.md`. Keep exactly one `### <reportId>`
heading under `Report Field Check`, and replace `<reportId>` with the selected
report id. Keep the summary table columns, Report Field Check field labels,
and Identity Checklist labels and order exactly as shown; do not add, duplicate,
remove, or reorder table columns, field lines, or checklist lines:

# Android Report Gate

- Status:
- Files scanned:
- Performance report rows:
- Session rows:
- Parse issues:

## Gate Summary

```text
status=
issueCount=
filesScanned=
performanceReportRows=
sessionRows=
parseIssues=
```

## Checks

- At least one V1 `flutter_performance_tier.performance_report` row.
- No parse issues.
- No non-performance-report session rows in the gate input.
- `schemaVersion` is JSON integer `1`.
- Report identity, service session, device model, OS version, `generatedAt`, and `decision.decidedAt` are non-empty JSON strings.
- `metadata.reportSequence` is a positive JSON integer.
- Report id matches `<serviceSessionId>-report-<reportSequence>`.
- Report id and service session/report sequence pairs are unique within the gate input.
- Top-level `generatedAt` is an ISO-8601 UTC timestamp and `decision.decidedAt` is an ISO-8601 timestamp.
- Required report, session, tier, runtime, and Android signal fields are present.
- Tier, confidence, runtime status, platform, memory pressure, and thermal wire values are JSON strings in expected ranges.
- RAM, SDK, memory pressure level, and SDK 29+ thermal level are JSON integers in expected ranges.
- Low-RAM and low-power Android signals are JSON booleans.
- Android SDK 29+ reports include thermal state and thermal state level.
- Report platform is `android` and the decision is not a fallback.

## Performance Reports

| Source | Report ID | Source Tag | Session | Sequence | Tier | Confidence | Runtime | Generated At | Decided At |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ... |

## Android Signals

| Report ID | Platform | Device | OS Version | SDK | RAM bytes | Low RAM | Low Power | Memory Pressure | Memory Level | Thermal | Thermal Level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ... |

## Report Field Check

### <reportId>

- `schemaName`:
- `schemaVersion`:
- `reportId`:
- `generatedAt`:
- `source`:
- `metadata.serviceSessionId`:
- `metadata.reportSequence`:
- `decision.tier`:
- `decision.confidence`:
- `decision.decidedAt`:
- `decision.deviceSignals.platform`:
- `decision.deviceSignals.deviceModel`:
- `decision.deviceSignals.osVersion`:
- `decision.deviceSignals.totalRamBytes`:
- `decision.deviceSignals.isLowRamDevice`:
- `decision.deviceSignals.sdkInt`:
- `decision.deviceSignals.thermalState`:
- `decision.deviceSignals.thermalStateLevel`:
- `decision.deviceSignals.isLowPowerModeEnabled`:
- `decision.deviceSignals.memoryPressureState`:
- `decision.deviceSignals.memoryPressureLevel`:
- `decision.runtimeObservation.status`:

## Identity And Gate Checklist

- `schemaVersion` is JSON integer `1`: yes / no
- `generatedAt` is UTC ISO-8601 timestamp: yes / no
- `decision.decidedAt` is ISO-8601 timestamp: yes / no
- `generatedAt` is at or after `decision.decidedAt`: yes / no
- `metadata.serviceSessionId` is a non-empty JSON string: yes / no
- `metadata.reportSequence` is a positive JSON integer: yes / no
- `reportId` equals `<metadata.serviceSessionId>-report-<metadata.reportSequence>`: yes / no
- Gate input contains no duplicate `reportId`: yes / no
- Gate input contains no duplicate `serviceSessionId + reportSequence`: yes / no
- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes / no

## Issues

- None. / paste gate issues

## Result

- Pass / fail:
- If failed, failure category: none / generation / storage / retrieval / parsing / gate
- Notes:

Use `none` when `Pass / fail` is `Pass`; readiness evidence must validate with
`android_report_evidence_status=PASS`.

## Evidence Validator

Instead of filling this file by hand, prefer generating a reviewed draft after
`android_report_gate.md` exists. The builder reads branch and commit from git
when they are not passed, but reviewed evidence should keep the copied builder
command explicit when the values are known:

```bash
python3 tool/build_android_report_evidence.py build/pulled_performance_reports/<fileName> \
  --analysis-output-dir build/diagnostics_analysis_android_report_gate \
  --branch <branch> \
  --commit <commit> \
  --output goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md \
  --application-id <applicationId>
```

After the generated or manually filled file is reviewed, run:

```bash
python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md
```

Expected output for readiness evidence:

```text
android_report_evidence_status=PASS
```

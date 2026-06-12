#!/usr/bin/env python3

from __future__ import annotations

import unittest
from pathlib import Path

from android_report_evidence_contract import (
    ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
    ANDROID_REPORT_EVIDENCE_APP_SIDE_TRIGGER_HEADING,
    ANDROID_REPORT_EVIDENCE_APP_TRIGGER_LABELS,
    ANDROID_REPORT_EVIDENCE_APP_USED_PLACEHOLDER,
    ANDROID_REPORT_EVIDENCE_APP_USED_LABEL,
    ANDROID_REPORT_EVIDENCE_APP_USED_OPTION,
    ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION,
    ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION,
    ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
    ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
    ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY,
    ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
    ANDROID_REPORT_EVIDENCE_HOST_APP_USED,
    ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
    ANDROID_REPORT_EVIDENCE_HOST_OUTPUTS_HEADING,
    ANDROID_REPORT_EVIDENCE_HOST_OUTPUT_LABELS,
    ANDROID_REPORT_EVIDENCE_OPTIONAL_RUN_CONTEXT_LABELS,
    ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
    ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
    ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
    ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
    ANDROID_REPORT_EVIDENCE_RESULT_LABELS,
    ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_HEADING,
    ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_LABELS,
    ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN,
    host_path_basename,
)
from android_report_gate_contract import (
    ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
    ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS,
    ANDROID_REPORT_GATE_CHECK_LINES,
    ANDROID_REPORT_GATE_CHECKS_HEADING,
    ANDROID_REPORT_GATE_FIELD_CHECK_LABELS,
    ANDROID_REPORT_GATE_HEADER_FIELDS,
    ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
    ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
    ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
    ANDROID_REPORT_GATE_SECTION_HEADINGS,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START,
    ANDROID_REPORT_GATE_SUMMARY_FIELDS,
    ANDROID_REPORT_GATE_SUMMARY_HEADING,
    IDENTITY_CHECKLIST_LABELS,
)
import validate_android_report_evidence


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_TEMPLATE = (
    ROOT
    / "goals"
    / "2026-06-11-android-performance-report-loop"
    / "evidence"
    / "android_report_loop_evidence_template.md"
)

PASSING_EVIDENCE = f"""# Android Report Loop Evidence Template

## Run Context

- Date: 2026-06-11
- Branch: codex/android-report-loop
- Commit: abc1234
- {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL}: {ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED}
- App variant: debug
- Application id: com.example.flutter_performance_tier_example
- Device model: Pixel 8 Pro
- Android version: 15
- SDK int: 35
- RAM class / total RAM if known: 8589934592
- Thermal / power state if relevant: normal / low-power false

## App-Side Trigger

- Trigger path: `Internal Tools` -> `Generate report`
- Report list refreshed with: `Internal Tools` -> `List reports`
- Copy source: `Internal Tools` -> `Copy host commands`
- On-device directory: `files/performance_tier_reports/`
- Report file name: performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json
- Copied commands were available for a safe `.json` report file name: yes

## Host Commands Run

```bash
set -e
adb shell run-as com.example.flutter_performance_tier_example ls 'files/performance_tier_reports'
mkdir -p build/pulled_performance_reports
adb exec-out run-as com.example.flutter_performance_tier_example cat files/performance_tier_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json > build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json
test -s build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json
set +e
python3 tool/analyze_diagnostics.py build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json --output build/diagnostics_analysis_android_report_gate --android-report-gate
gate_status=$?
set -e
cat build/diagnostics_analysis_android_report_gate/android_report_gate.md
test "$gate_status" -eq 0
python3 tool/build_android_report_evidence.py build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json --analysis-output-dir build/diagnostics_analysis_android_report_gate --branch codex/android-report-loop --commit abc1234 --output goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md --application-id com.example.flutter_performance_tier_example
python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md
```

## Host Outputs

- Pulled report path: build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json
- Analyzer output directory: build/diagnostics_analysis_android_report_gate
- Analyzer exit code: 0
- `android_report_gate.md` status: PASS

# Android Report Gate

- Status: PASS
- Files scanned: 1
- Performance report rows: 1
- Session rows: 1
- Parse issues: 0

## Gate Summary

```text
status=PASS
issueCount=0
filesScanned=1
performanceReportRows=1
sessionRows=1
parseIssues=0
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
| build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json | perf-tier-1781111111000000-report-1 | example-internal-tools | perf-tier-1781111111000000 | 1 | t2High | high | inactive | 2026-06-11T08:01:58.000Z | 2026-06-11T08:01:57.000Z |

## Android Signals

| Report ID | Platform | Device | OS Version | SDK | RAM bytes | Low RAM | Low Power | Memory Pressure | Memory Level | Thermal | Thermal Level |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| perf-tier-1781111111000000-report-1 | android | Pixel 8 Pro | 15 | 35 | 8589934592 | false | false | normal | 0 | normal | 0 |

## Report Field Check

### perf-tier-1781111111000000-report-1

- `schemaName`: flutter_performance_tier.performance_report
- `schemaVersion`: 1
- `reportId`: perf-tier-1781111111000000-report-1
- `generatedAt`: 2026-06-11T08:01:58.000Z
- `source`: example-internal-tools
- `metadata.serviceSessionId`: perf-tier-1781111111000000
- `metadata.reportSequence`: 1
- `decision.tier`: t2High
- `decision.confidence`: high
- `decision.decidedAt`: 2026-06-11T08:01:57.000Z
- `decision.deviceSignals.platform`: android
- `decision.deviceSignals.deviceModel`: Pixel 8 Pro
- `decision.deviceSignals.osVersion`: 15
- `decision.deviceSignals.totalRamBytes`: 8589934592
- `decision.deviceSignals.isLowRamDevice`: false
- `decision.deviceSignals.sdkInt`: 35
- `decision.deviceSignals.thermalState`: normal
- `decision.deviceSignals.thermalStateLevel`: 0
- `decision.deviceSignals.isLowPowerModeEnabled`: false
- `decision.deviceSignals.memoryPressureState`: normal
- `decision.deviceSignals.memoryPressureLevel`: 0
- `decision.runtimeObservation.status`: inactive

## Identity And Gate Checklist

- `schemaVersion` is JSON integer `1`: yes
- `generatedAt` is UTC ISO-8601 timestamp: yes
- `decision.decidedAt` is ISO-8601 timestamp: yes
- `generatedAt` is at or after `decision.decidedAt`: yes
- `metadata.serviceSessionId` is a non-empty JSON string: yes
- `metadata.reportSequence` is a positive JSON integer: yes
- `reportId` equals `<metadata.serviceSessionId>-report-<metadata.reportSequence>`: yes
- Gate input contains no duplicate `reportId`: yes
- Gate input contains no duplicate `serviceSessionId + reportSequence`: yes
- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes

## Issues

- None.

## Result

- Pass / fail: Pass
- If failed, failure category: none
- Notes: reviewed
"""


class AndroidReportEvidenceValidationTest(unittest.TestCase):
    def test_accepts_filled_passing_evidence(self) -> None:
        result = validate_android_report_evidence.validate_evidence_text(
            PASSING_EVIDENCE,
        )

        self.assertEqual([], result.issues)
        self.assertTrue(result.ok)

    def test_host_path_basename_contract_handles_host_path_separators(self) -> None:
        report_file_name = (
            "performance_tier_v1_20260611T080158Z_"
            "perf-tier-1781111111000000-report-1.json"
        )

        self.assertEqual(
            report_file_name,
            host_path_basename(
                f" build/pulled_performance_reports/{report_file_name} ",
            ),
        )
        self.assertEqual(
            report_file_name,
            host_path_basename(
                f"build\\pulled_performance_reports\\{report_file_name}",
            ),
        )

    def test_accepts_builder_command_with_matching_branch_and_commit(self) -> None:
        evidence = _with_builder_git_context(
            PASSING_EVIDENCE,
            f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} codex/android-report-loop "
            f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} abc1234 ",
        )

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertEqual([], result.issues)
        self.assertTrue(result.ok)

    def test_rejects_builder_command_without_explicit_git_context(self) -> None:
        evidence = _with_builder_git_context(PASSING_EVIDENCE, "")

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_git_context_missing" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_with_partial_git_context(self) -> None:
        evidence = _with_builder_git_context(
            PASSING_EVIDENCE,
            f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} codex/android-report-loop ",
        )

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_git_context_partial" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_with_mismatched_branch(self) -> None:
        evidence = _with_builder_git_context(
            PASSING_EVIDENCE,
            f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} other-branch "
            f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} abc1234 ",
        )

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_branch_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_with_mismatched_commit(self) -> None:
        evidence = _with_builder_git_context(
            PASSING_EVIDENCE,
            f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} codex/android-report-loop "
            f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} def5678 ",
        )

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_commit_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_template_gate_contract_sections_match_shared_contract(self) -> None:
        template = EVIDENCE_TEMPLATE.read_text(encoding="utf-8")
        headings = _section_headings(template)
        start = headings.index(ANDROID_REPORT_GATE_SUMMARY_HEADING)
        end = headings.index(ANDROID_REPORT_EVIDENCE_RESULT_HEADING)

        for heading in [
            ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_HEADING,
            ANDROID_REPORT_EVIDENCE_APP_SIDE_TRIGGER_HEADING,
            ANDROID_REPORT_EVIDENCE_HOST_OUTPUTS_HEADING,
            ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
        ]:
            self.assertIn(heading, headings)
        self.assertEqual(
            [
                *ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_LABELS,
                *ANDROID_REPORT_EVIDENCE_OPTIONAL_RUN_CONTEXT_LABELS,
            ],
            _section_field_labels(template, ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_HEADING),
        )
        self.assertIn(
            f"- {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL}: "
            f"{ANDROID_REPORT_EVIDENCE_APP_USED_PLACEHOLDER}",
            template,
        )
        self.assertEqual(
            ANDROID_REPORT_EVIDENCE_APP_TRIGGER_LABELS,
            _section_field_labels(
                template,
                ANDROID_REPORT_EVIDENCE_APP_SIDE_TRIGGER_HEADING,
            ),
        )
        self.assertEqual(
            ANDROID_REPORT_EVIDENCE_HOST_OUTPUT_LABELS,
            _section_field_labels(template, ANDROID_REPORT_EVIDENCE_HOST_OUTPUTS_HEADING),
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_SECTION_HEADINGS,
            headings[start:end],
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_SUMMARY_FIELDS,
            _section_key_value_fields(template, ANDROID_REPORT_GATE_SUMMARY_HEADING),
        )
        gate_summary_lines = _section_non_empty_lines(
            template,
            ANDROID_REPORT_GATE_SUMMARY_HEADING,
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START,
            gate_summary_lines[0],
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END,
            gate_summary_lines[-1],
        )
        self.assertEqual(
            [
                label
                for label, _summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
            ],
            _top_status_block_labels(template),
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_CHECK_LINES,
            _section_non_empty_lines(template, ANDROID_REPORT_GATE_CHECKS_HEADING),
        )
        self.assertEqual(
            [
                _markdown_table_header(
                    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
                ),
                _markdown_table_divider(
                    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
                ),
            ],
            _section_non_empty_lines(
                template,
                ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
            )[:2],
        )
        self.assertEqual(
            [
                _markdown_table_header(ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS),
                _markdown_table_divider(ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS),
            ],
            _section_non_empty_lines(
                template,
                ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
            )[:2],
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_FIELD_CHECK_LABELS,
            _section_field_labels(
                template,
                ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
            ),
        )
        self.assertEqual(
            [f"- {label}: yes / no" for label in IDENTITY_CHECKLIST_LABELS],
            _section_non_empty_lines(template, ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING),
        )
        self.assertEqual(
            ANDROID_REPORT_EVIDENCE_RESULT_LABELS,
            _section_field_labels(template, ANDROID_REPORT_EVIDENCE_RESULT_HEADING),
        )

    def test_template_host_command_contract_matches_shared_contract(self) -> None:
        template = EVIDENCE_TEMPLATE.read_text(encoding="utf-8")
        command_text = "\n".join(
            _section_non_empty_lines(
                template,
                ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
            ),
        )

        self.assertIn(
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
            _section_headings(template),
        )
        self.assertIn(
            f"`{ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY}/`",
            template,
        )
        self.assertIn(
            f"ls '{ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY}'",
            command_text,
        )
        self.assertEqual(
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START,
            _section_non_empty_lines(
                template,
                ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
            )[0],
        )
        self.assertEqual(
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END,
            _section_non_empty_lines(
                template,
                ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
            )[-1],
        )
        self.assertIn(ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT, template)
        for snippet in ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS:
            self.assertIn(snippet, command_text)
        self.assertIn(ANDROID_REPORT_EVIDENCE_BRANCH_OPTION, command_text)
        self.assertIn(ANDROID_REPORT_EVIDENCE_COMMIT_OPTION, command_text)

    def test_required_host_command_snippets_include_context_options(self) -> None:
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )
        self.assertIn(
            ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME,
            ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
        )

    def test_rejects_unfilled_template_values(self) -> None:
        result = validate_android_report_evidence.validate_evidence_text(
            "- Date:\n"
            f"- {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL}: "
            f"{ANDROID_REPORT_EVIDENCE_APP_USED_PLACEHOLDER}\n"
            "- Report file name: <fileName>\n"
            "- Copied commands were available for a safe `.json` report file name: yes / no\n"
            "## Gate Summary\n"
            "```text\n"
            "status=\n"
            "```\n",
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_or_placeholder: Date" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("host_commands_unavailable" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_unfenced_gate_summary_values(self) -> None:
        fenced_summary = (
            "```text\n"
            "status=PASS\n"
            "issueCount=0\n"
            "filesScanned=1\n"
            "performanceReportRows=1\n"
            "sessionRows=1\n"
            "parseIssues=0\n"
            "```"
        )
        unfenced_summary = (
            "status=PASS\n"
            "issueCount=0\n"
            "filesScanned=1\n"
            "performanceReportRows=1\n"
            "sessionRows=1\n"
            "parseIssues=0"
        )
        evidence = PASSING_EVIDENCE.replace(fenced_summary, unfenced_summary)

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("gate_summary_fence_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_unknown_app_used_value(self) -> None:
        evidence = PASSING_EVIDENCE.replace(
            f"- {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL}: "
            f"{ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED}",
            "- App used: staging app",
        )

        result = validate_android_report_evidence.validate_evidence_text(evidence)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("invalid_app_used" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_app_side_trigger_that_does_not_match_internal_tools(
        self,
    ) -> None:
        wrong_trigger = PASSING_EVIDENCE.replace(
            "- Trigger path: `Internal Tools` -> `Generate report`",
            "- Trigger path: `Internal Tools` -> `Upload diagnostics`",
        ).replace(
            "- Copy source: `Internal Tools` -> `Copy host commands`",
            "- Copy source: `Internal Tools` -> `Copy adb command`",
        ).replace(
            "- On-device directory: `files/performance_tier_reports/`",
            "- On-device directory: `cache/performance_tier_reports/`",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            wrong_trigger,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("app_trigger_mismatch: trigger_path" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("app_trigger_mismatch: copy_source" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "app_trigger_mismatch: on_device_directory" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_app_side_trigger_fields_outside_trigger_section(self) -> None:
        misplaced_lines = [
            "- Trigger path: `Internal Tools` -> `Generate report`",
            "- Report list refreshed with: `Internal Tools` -> `List reports`",
            "- Copy source: `Internal Tools` -> `Copy host commands`",
            "- On-device directory: `files/performance_tier_reports/`",
            "- Copied commands were available for a safe `.json` report file name: yes",
        ]
        misplaced_trigger = PASSING_EVIDENCE
        for line in misplaced_lines:
            misplaced_trigger = misplaced_trigger.replace(f"{line}\n", "")
        misplaced_trigger = misplaced_trigger.replace(
            "- `android_report_gate.md` status: PASS\n",
            "- `android_report_gate.md` status: PASS\n"
            + "\n".join(misplaced_lines)
            + "\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            misplaced_trigger,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_app_trigger_field: Trigger path" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_app_trigger_field: Report list refreshed with" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any("host_commands_unavailable" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_host_output_fields_outside_host_outputs_section(self) -> None:
        misplaced_lines = [
            "- Pulled report path: build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "- Analyzer output directory: build/diagnostics_analysis_android_report_gate",
            "- Analyzer exit code: 0",
            "- `android_report_gate.md` status: PASS",
        ]
        misplaced_outputs = PASSING_EVIDENCE
        for line in misplaced_lines:
            misplaced_outputs = misplaced_outputs.replace(f"{line}\n", "")
        misplaced_outputs = misplaced_outputs.replace(
            "- Copied commands were available for a safe `.json` report file name: yes\n",
            "- Copied commands were available for a safe `.json` report file name: yes\n"
            + "\n".join(misplaced_lines)
            + "\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            misplaced_outputs,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "missing_or_placeholder: Pulled report path" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any("analyzer_exit_code" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("gate_status" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_incomplete_host_command_chain(self) -> None:
        incomplete = PASSING_EVIDENCE.replace(
            "python3 tool/build_android_report_evidence.py build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json --analysis-output-dir build/diagnostics_analysis_android_report_gate --branch codex/android-report-loop --commit abc1234 --output goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md --application-id com.example.flutter_performance_tier_example\n",
            "",
        )

        result = validate_android_report_evidence.validate_evidence_text(incomplete)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "missing_host_command: tool/build_android_report_evidence.py" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_host_commands_that_run_out_of_order(self) -> None:
        analyzer_command = (
            "python3 tool/analyze_diagnostics.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--output build/diagnostics_analysis_android_report_gate --android-report-gate"
        )
        builder_command = (
            "python3 tool/build_android_report_evidence.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--analysis-output-dir build/diagnostics_analysis_android_report_gate "
            "--branch codex/android-report-loop --commit abc1234 "
            "--output goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md "
            "--application-id com.example.flutter_performance_tier_example"
        )
        out_of_order = PASSING_EVIDENCE.replace(
            f"{builder_command}\n",
            "",
        ).replace(
            analyzer_command,
            f"{builder_command}\n{analyzer_command}",
        )

        result = validate_android_report_evidence.validate_evidence_text(out_of_order)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_command_order_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_host_commands_missing_execution_semantics(self) -> None:
        missing_execution_semantics = PASSING_EVIDENCE.replace(
            "mkdir -p build/pulled_performance_reports\n",
            "",
        ).replace(
            "gate_status=$?\n",
            "",
        ).replace(
            "gate_status=$?",
            "",
        ).replace(
            "set -e\n"
            "cat build/diagnostics_analysis_android_report_gate/android_report_gate.md\n",
            "cat build/diagnostics_analysis_android_report_gate/android_report_gate.md\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            missing_execution_semantics,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_host_command: mkdir -p" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_host_command: gate_status=$?" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_host_command_stage: prepare host report directory" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_host_command_stage: capture gate status" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_host_command_stage: resume fail-fast" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_unexpected_host_command_lines(self) -> None:
        unexpected_command = PASSING_EVIDENCE.replace(
            "test -s build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json\n",
            "test -s build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json\n"
            "echo inspected\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            unexpected_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "unexpected_host_command: echo inspected" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_unfenced_host_command_block(self) -> None:
        unfenced_command_block = PASSING_EVIDENCE.replace(
            "```bash\n",
            "",
            1,
        ).replace(
            "\n```\n\n## Host Outputs",
            "\n\n## Host Outputs",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            unfenced_command_block,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_commands_fence_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_malformed_host_command_shell_syntax(self) -> None:
        malformed_command = PASSING_EVIDENCE.replace(
            "adb shell run-as com.example.flutter_performance_tier_example ls 'files/performance_tier_reports'",
            "adb shell run-as com.example.flutter_performance_tier_example ls 'files/performance_tier_reports",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            malformed_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("malformed_host_command" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_placeholder_host_commands(self) -> None:
        with_placeholder_command = PASSING_EVIDENCE.replace(
            "files/performance_tier_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "files/performance_tier_reports/<fileName>",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            with_placeholder_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_commands_placeholder" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_host_commands_that_do_not_match_context(self) -> None:
        mismatched_application_id = PASSING_EVIDENCE.replace(
            "adb shell run-as com.example.flutter_performance_tier_example",
            "adb shell run-as com.example.other_app",
        ).replace(
            "adb exec-out run-as com.example.flutter_performance_tier_example",
            "adb exec-out run-as com.example.other_app",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_application_id,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_adb_app_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_host_command_context_prefix_matches(self) -> None:
        prefix_context = PASSING_EVIDENCE.replace(
            "- Application id: com.example.flutter_performance_tier_example",
            "- Application id: com.example.flutter_performance_tier",
        ).replace(
            "- Analyzer output directory: build/diagnostics_analysis_android_report_gate",
            "- Analyzer output directory: build/diagnostics_analysis_android_report",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            prefix_context,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_context_mismatch: application_id" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "host_command_context_mismatch: analyzer_output_directory" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_pull_command_with_wrong_adb_context(self) -> None:
        wrong_pull_command = PASSING_EVIDENCE.replace(
            "adb exec-out run-as com.example.flutter_performance_tier_example cat "
            "files/performance_tier_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "adb exec-out run-as com.example.other_app cat "
            "files/performance_tier_reports/other_report.json",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            wrong_pull_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_command_adb_app_mismatch: pull" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("host_command_device_report_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_list_command_with_extra_adb_arguments(self) -> None:
        extra_list_argument = PASSING_EVIDENCE.replace(
            "adb shell run-as com.example.flutter_performance_tier_example ls 'files/performance_tier_reports'",
            "adb shell run-as com.example.flutter_performance_tier_example ls 'files/performance_tier_reports' /sdcard",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_list_argument,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_adb_list_structure_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_pull_command_without_exact_stdout_redirection(self) -> None:
        pipe_pull_command = PASSING_EVIDENCE.replace(
            "adb exec-out run-as com.example.flutter_performance_tier_example cat "
            "files/performance_tier_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json > "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "adb exec-out run-as com.example.flutter_performance_tier_example cat "
            "files/performance_tier_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json | "
            "tee build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            pipe_pull_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_adb_pull_structure_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_analyzer_command_that_uses_different_paths(self) -> None:
        wrong_analyzer_command = PASSING_EVIDENCE.replace(
            "python3 tool/analyze_diagnostics.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--output build/diagnostics_analysis_android_report_gate --android-report-gate",
            "python3 tool/analyze_diagnostics.py "
            "build/pulled_performance_reports/other_report.json "
            "--output build/other_analysis --android-report-gate",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            wrong_analyzer_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_command_analyzer_input_mismatch" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("host_command_analyzer_output_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_analyzer_command_with_extra_arguments(self) -> None:
        extra_analyzer_arg = PASSING_EVIDENCE.replace(
            "python3 tool/analyze_diagnostics.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--output build/diagnostics_analysis_android_report_gate --android-report-gate",
            "python3 tool/analyze_diagnostics.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--output build/diagnostics_analysis_android_report_gate --android-report-gate "
            "build/pulled_performance_reports/other_report.json",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_analyzer_arg,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_analyzer_structure_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_that_uses_different_inputs(self) -> None:
        wrong_builder_command = PASSING_EVIDENCE.replace(
            "python3 tool/build_android_report_evidence.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--analysis-output-dir build/diagnostics_analysis_android_report_gate",
            "python3 tool/build_android_report_evidence.py "
            "build/pulled_performance_reports/other_report.json "
            "--analysis-output-dir build/other_analysis",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            wrong_builder_command,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_command_builder_input_mismatch" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "host_command_builder_analysis_output_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_with_different_application_id(self) -> None:
        wrong_application_id = PASSING_EVIDENCE.replace(
            "--application-id com.example.flutter_performance_tier_example",
            "--application-id com.example.other_app",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            wrong_application_id,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_application_id_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_without_application_id_option(self) -> None:
        missing_application_id = PASSING_EVIDENCE.replace(
            " --application-id com.example.flutter_performance_tier_example",
            "",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            missing_application_id,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                f"missing_host_command: {ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION}"
                in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "host_command_builder_application_id_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_without_output_option(self) -> None:
        missing_output = PASSING_EVIDENCE.replace(
            " --output goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md",
            "",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            missing_output,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_output_missing" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_builder_command_with_extra_arguments(self) -> None:
        extra_builder_arg = PASSING_EVIDENCE.replace(
            "python3 tool/build_android_report_evidence.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--analysis-output-dir build/diagnostics_analysis_android_report_gate "
            "--branch codex/android-report-loop --commit abc1234 "
            "--output goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md "
            "--application-id com.example.flutter_performance_tier_example",
            "python3 tool/build_android_report_evidence.py "
            "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
            "--analysis-output-dir build/diagnostics_analysis_android_report_gate "
            "--branch codex/android-report-loop --commit abc1234 "
            "--output goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md "
            "--application-id com.example.flutter_performance_tier_example "
            f"{ANDROID_REPORT_EVIDENCE_APP_USED_OPTION} "
            f"{ANDROID_REPORT_EVIDENCE_HOST_APP_USED}",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_builder_arg,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_builder_structure_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_wrong_file_check_and_gate_markdown_print_paths(self) -> None:
        wrong_file_checks = PASSING_EVIDENCE.replace(
            "test -s build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "test -s build/pulled_performance_reports/other_report.json",
        ).replace(
            "cat build/diagnostics_analysis_android_report_gate/android_report_gate.md",
            "cat build/other_analysis/android_report_gate.md",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            wrong_file_checks,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_command_nonempty_check_mismatch" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "host_command_gate_markdown_path_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_host_commands_that_validate_a_different_evidence_file(
        self,
    ) -> None:
        mismatched_evidence_path = PASSING_EVIDENCE.replace(
            "python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md",
            "python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/other_evidence.md",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_evidence_path,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("host_command_evidence_path_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_validator_command_with_extra_arguments(self) -> None:
        extra_validator_arg = PASSING_EVIDENCE.replace(
            "python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md",
            "python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.md --verbose",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_validator_arg,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "host_command_validator_structure_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_pulled_report_path_that_does_not_match_file_name(self) -> None:
        mismatched_path = PASSING_EVIDENCE.replace(
            "- Pulled report path: build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "- Pulled report path: build/pulled_performance_reports/other_report.json",
        ).replace(
            "> build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "> build/pulled_performance_reports/other_report.json",
        ).replace(
            "test -s build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "test -s build/pulled_performance_reports/other_report.json",
        ).replace(
            "python3 tool/analyze_diagnostics.py build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "python3 tool/analyze_diagnostics.py build/pulled_performance_reports/other_report.json",
        ).replace(
            "python3 tool/build_android_report_evidence.py build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "python3 tool/build_android_report_evidence.py build/pulled_performance_reports/other_report.json",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_path,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("report_file_path_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_report_field_check_that_does_not_match_context(self) -> None:
        mismatched_device_model = PASSING_EVIDENCE.replace(
            "- `decision.deviceSignals.deviceModel`: Pixel 8 Pro",
            "- `decision.deviceSignals.deviceModel`: Pixel 7",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_device_model,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "report_field_context_mismatch: device_model" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_report_field_check_extra_label(self) -> None:
        extra_label = PASSING_EVIDENCE.replace(
            "- `decision.runtimeObservation.status`: inactive\n",
            "- `decision.runtimeObservation.status`: inactive\n"
            "- `unexpected`: value\n",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(extra_label)

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "report_field_check_labels_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_report_field_check_without_current_report_heading(self) -> None:
        missing_heading = PASSING_EVIDENCE.replace(
            "\n### perf-tier-1781111111000000-report-1\n\n",
            "\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            missing_heading,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_report_field_check_heading" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_report_field_check_fields_outside_expected_section(self) -> None:
        report_field_lines = [
            "- `schemaName`: flutter_performance_tier.performance_report",
            "- `schemaVersion`: 1",
            "- `reportId`: perf-tier-1781111111000000-report-1",
            "- `generatedAt`: 2026-06-11T08:01:58.000Z",
            "- `source`: example-internal-tools",
            "- `metadata.serviceSessionId`: perf-tier-1781111111000000",
            "- `metadata.reportSequence`: 1",
            "- `decision.tier`: t2High",
            "- `decision.confidence`: high",
            "- `decision.decidedAt`: 2026-06-11T08:01:57.000Z",
            "- `decision.deviceSignals.platform`: android",
            "- `decision.deviceSignals.deviceModel`: Pixel 8 Pro",
            "- `decision.deviceSignals.osVersion`: 15",
            "- `decision.deviceSignals.totalRamBytes`: 8589934592",
            "- `decision.deviceSignals.isLowRamDevice`: false",
            "- `decision.deviceSignals.sdkInt`: 35",
            "- `decision.deviceSignals.thermalState`: normal",
            "- `decision.deviceSignals.thermalStateLevel`: 0",
            "- `decision.deviceSignals.isLowPowerModeEnabled`: false",
            "- `decision.deviceSignals.memoryPressureState`: normal",
            "- `decision.deviceSignals.memoryPressureLevel`: 0",
            "- `decision.runtimeObservation.status`: inactive",
        ]
        misplaced_fields = PASSING_EVIDENCE
        for line in report_field_lines:
            misplaced_fields = misplaced_fields.replace(f"{line}\n", "")
        misplaced_fields = misplaced_fields.replace(
            "- `android_report_gate.md` status: PASS\n",
            "- `android_report_gate.md` status: PASS\n"
            + "\n".join(report_field_lines)
            + "\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            misplaced_fields,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "missing_report_field_check: `schemaName`" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_report_field_check: `reportId`" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_report_field_check: `decision.deviceSignals.osVersion`"
                in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_report_field_check_with_multiple_report_headings(self) -> None:
        multiple_headings = PASSING_EVIDENCE.replace(
            ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
            "### perf-tier-1781111111000000-report-2\n\n"
            + ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            multiple_headings,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("report_field_check_scope_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_identity_checklist_outside_expected_section(self) -> None:
        misplaced_checklist = PASSING_EVIDENCE.replace(
            ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
            "## Identity Checklist",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            misplaced_checklist,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("identity_check_not_yes" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_identity_checklist_extra_label(self) -> None:
        extra_label = PASSING_EVIDENCE.replace(
            "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes\n",
            "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes\n"
            "- Unexpected checklist label: yes\n",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_label,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "identity_checklist_labels_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_performance_report_table_that_does_not_match_fields(
        self,
    ) -> None:
        mismatched_report_table = PASSING_EVIDENCE.replace(
            "| build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json | perf-tier-1781111111000000-report-1 | example-internal-tools | perf-tier-1781111111000000 | 1 | t2High | high | inactive | 2026-06-11T08:01:58.000Z | 2026-06-11T08:01:57.000Z |",
            "| build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json | perf-tier-1781111111000000-report-99 | example-internal-tools | perf-tier-1781111111000000 | 1 | t2High | high | inactive | 2026-06-11T08:01:58.000Z | 2026-06-11T08:01:57.000Z |",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_report_table,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "performance_report_table_context_mismatch: report_id" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_performance_report_table_extra_column(self) -> None:
        extra_column = PASSING_EVIDENCE.replace(
            "| Source | Report ID | Source Tag | Session | Sequence | Tier | Confidence | Runtime | Generated At | Decided At |",
            "| Source | Report ID | Source Tag | Session | Sequence | Tier | Confidence | Runtime | Generated At | Decided At | Unexpected |",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_column,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "performance_report_table_columns_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_performance_report_table_source_that_does_not_match_pull(
        self,
    ) -> None:
        mismatched_source = PASSING_EVIDENCE.replace(
            "| build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json | perf-tier-1781111111000000-report-1 |",
            "| build/pulled_performance_reports/other_report.json | perf-tier-1781111111000000-report-1 |",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_source,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "performance_report_table_source_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_android_signal_table_that_does_not_match_context(self) -> None:
        mismatched_signal_table = PASSING_EVIDENCE.replace(
            "| perf-tier-1781111111000000-report-1 | android | Pixel 8 Pro | 15 | 35 | 8589934592 | false | false | normal | 0 | normal | 0 |",
            "| perf-tier-1781111111000000-report-1 | android | Pixel 7 | 15 | 35 | 8589934592 | false | false | normal | 0 | normal | 0 |",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_signal_table,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "android_signal_table_context_mismatch: device_model" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_android_signal_table_that_does_not_match_fields(self) -> None:
        mismatched_signal_table = PASSING_EVIDENCE.replace(
            "| perf-tier-1781111111000000-report-1 | android | Pixel 8 Pro | 15 | 35 | 8589934592 | false | false | normal | 0 | normal | 0 |",
            "| perf-tier-1781111111000000-report-1 | android | Pixel 8 Pro | 15 | 35 | 1024 | false | false | normal | 0 | normal | 0 |",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_signal_table,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "android_signal_table_context_mismatch: total_ram_bytes" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_android_signal_table_extra_column(self) -> None:
        extra_column = PASSING_EVIDENCE.replace(
            "| Report ID | Platform | Device | OS Version | SDK | RAM bytes | Low RAM | Low Power | Memory Pressure | Memory Level | Thermal | Thermal Level |",
            "| Report ID | Platform | Device | OS Version | SDK | RAM bytes | Low RAM | Low Power | Memory Pressure | Memory Level | Thermal | Thermal Level | Unexpected |",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            extra_column,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "android_signal_table_columns_mismatch" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_missing_result_section(self) -> None:
        without_result = PASSING_EVIDENCE.replace(
            "\n## Result\n\n"
            "- Pass / fail: Pass\n"
            "- If failed, failure category: none\n"
            "- Notes: reviewed\n",
            "\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            without_result,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_result: Pass / fail" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_result: If failed, failure category" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_result_fields_outside_result_section(self) -> None:
        misplaced_result_fields = PASSING_EVIDENCE.replace(
            "\n## Result\n\n"
            "- Pass / fail: Pass\n"
            "- If failed, failure category: none\n"
            "- Notes: reviewed\n",
            "\n## Result\n\n- Notes: reviewed\n",
        ).replace(
            "- Analyzer exit code: 0\n"
            "- `android_report_gate.md` status: PASS\n",
            "- Analyzer exit code: 0\n"
            "- `android_report_gate.md` status: PASS\n"
            "- Pass / fail: Pass\n"
            "- If failed, failure category: none\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            misplaced_result_fields,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_result: Pass / fail" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_result: If failed, failure category" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_missing_gate_issues_section(self) -> None:
        missing_issues = PASSING_EVIDENCE.replace(
            "\n## Issues\n\n"
            "- None.\n",
            "",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            missing_issues,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_gate_issues" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_non_empty_gate_issues_section(self) -> None:
        non_empty_issues = PASSING_EVIDENCE.replace(
            "- None.",
            "- Missing Android thermal state.",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            non_empty_issues,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("gate_issues_not_none" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_missing_gate_checks_section(self) -> None:
        missing_checks = PASSING_EVIDENCE.replace(
            "\n## Checks\n\n"
            "- At least one V1 `flutter_performance_tier.performance_report` row.\n"
            "- No parse issues.\n"
            "- No non-performance-report session rows in the gate input.\n"
            "- `schemaVersion` is JSON integer `1`.\n"
            "- Report identity, service session, device model, OS version, `generatedAt`, and `decision.decidedAt` are non-empty JSON strings.\n"
            "- `metadata.reportSequence` is a positive JSON integer.\n"
            "- Report id matches `<serviceSessionId>-report-<reportSequence>`.\n"
            "- Report id and service session/report sequence pairs are unique within the gate input.\n"
            "- Top-level `generatedAt` is an ISO-8601 UTC timestamp and `decision.decidedAt` is an ISO-8601 timestamp.\n"
            "- Required report, session, tier, runtime, and Android signal fields are present.\n"
            "- Tier, confidence, runtime status, platform, memory pressure, and thermal wire values are JSON strings in expected ranges.\n"
            "- RAM, SDK, memory pressure level, and SDK 29+ thermal level are JSON integers in expected ranges.\n"
            "- Low-RAM and low-power Android signals are JSON booleans.\n"
            "- Android SDK 29+ reports include thermal state and thermal state level.\n"
            "- Report platform is `android` and the decision is not a fallback.\n",
            "",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            missing_checks,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_gate_checks" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_gate_checks_that_do_not_match_analyzer_output(self) -> None:
        mismatched_checks = PASSING_EVIDENCE.replace(
            "- No parse issues.",
            "- Parse issues were not reviewed.",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_checks,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("gate_checks_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_fail_gate_summary(self) -> None:
        failing = PASSING_EVIDENCE.replace(
            "- Analyzer exit code: 0",
            "- Analyzer exit code: 2",
        ).replace(
            "- `android_report_gate.md` status: PASS",
            "- `android_report_gate.md` status: FAIL",
        ).replace(
            "status=PASS",
            "status=FAIL",
        ).replace(
            "issueCount=0",
            "issueCount=1",
        )

        result = validate_android_report_evidence.validate_evidence_text(failing)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("analyzer_exit_code" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("gate_summary_status" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any("gate_summary_issueCount" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_gate_summary_that_does_not_match_table_counts(self) -> None:
        mismatched_summary = PASSING_EVIDENCE.replace(
            "performanceReportRows=1",
            "performanceReportRows=2",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_summary,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "gate_summary_table_count_mismatch: performanceReportRows" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any("gate_summary_session_count_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_unexpected_gate_summary_field(self) -> None:
        unexpected_summary_field = PASSING_EVIDENCE.replace(
            "parseIssues=0\n```",
            "parseIssues=0\nunexpected=1\n```",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            unexpected_summary_field,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("gate_summary_fields_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_gate_header_that_does_not_match_summary(self) -> None:
        mismatched_header = PASSING_EVIDENCE.replace(
            "- Status: PASS",
            "- Status: FAIL",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            mismatched_header,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("gate_header_summary_mismatch: status" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_unexpected_gate_header_field(self) -> None:
        unexpected_header_field = PASSING_EVIDENCE.replace(
            "- Parse issues: 0\n\n## Gate Summary",
            "- Parse issues: 0\n- Unexpected: yes\n\n## Gate Summary",
            1,
        )

        result = validate_android_report_evidence.validate_evidence_text(
            unexpected_header_field,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("gate_header_fields_mismatch" in issue for issue in result.issues),
            result.issues,
        )

    def test_rejects_gate_header_fields_outside_gate_header(self) -> None:
        gate_header_lines = [
            "- Status: PASS",
            "- Files scanned: 1",
            "- Performance report rows: 1",
            "- Session rows: 1",
            "- Parse issues: 0",
        ]
        misplaced_header = PASSING_EVIDENCE
        for line in gate_header_lines:
            misplaced_header = misplaced_header.replace(f"{line}\n", "", 1)
        misplaced_header = misplaced_header.replace(
            "- `android_report_gate.md` status: PASS\n",
            "- `android_report_gate.md` status: PASS\n"
            + "\n".join(gate_header_lines)
            + "\n",
        )

        result = validate_android_report_evidence.validate_evidence_text(
            misplaced_header,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any("missing_gate_header: Status" in issue for issue in result.issues),
            result.issues,
        )
        self.assertTrue(
            any(
                "missing_gate_header: Performance report rows" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_multiple_report_evidence_scope(self) -> None:
        performance_row = (
            "| build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json | perf-tier-1781111111000000-report-1 | "
            "example-internal-tools | perf-tier-1781111111000000 | 1 | "
            "t2High | high | inactive | 2026-06-11T08:01:58.000Z | "
            "2026-06-11T08:01:57.000Z |"
        )
        second_performance_row = (
            "| sample-2.json | perf-tier-1781111111000000-report-2 | "
            "example-internal-tools | perf-tier-1781111111000000 | 2 | "
            "t2High | high | inactive | 2026-06-11T08:02:58.000Z | "
            "2026-06-11T08:02:57.000Z |"
        )
        signal_row = (
            "| perf-tier-1781111111000000-report-1 | android | Pixel 8 Pro | "
            "15 | 35 | 8589934592 | false | false | normal | 0 | normal | 0 |"
        )
        second_signal_row = (
            "| perf-tier-1781111111000000-report-2 | android | Pixel 8 Pro | "
            "15 | 35 | 8589934592 | false | false | normal | 0 | normal | 0 |"
        )
        multiple_report_evidence = (
            PASSING_EVIDENCE.replace("- Files scanned: 1", "- Files scanned: 2")
            .replace("- Performance report rows: 1", "- Performance report rows: 2")
            .replace("- Session rows: 1", "- Session rows: 2")
            .replace("filesScanned=1", "filesScanned=2")
            .replace("performanceReportRows=1", "performanceReportRows=2")
            .replace("sessionRows=1", "sessionRows=2")
            .replace(performance_row, f"{performance_row}\n{second_performance_row}")
            .replace(signal_row, f"{signal_row}\n{second_signal_row}")
        )

        result = validate_android_report_evidence.validate_evidence_text(
            multiple_report_evidence,
        )

        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "single_report_scope_mismatch: performance_report_rows" in issue
                for issue in result.issues
            ),
            result.issues,
        )
        self.assertTrue(
            any(
                "single_report_scope_mismatch: performance_report_table_rows" in issue
                for issue in result.issues
            ),
            result.issues,
        )

    def test_rejects_unsafe_report_file_name(self) -> None:
        unsafe = PASSING_EVIDENCE.replace(
            "- Report file name: performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json",
            "- Report file name: ../unsafe.json",
        )

        result = validate_android_report_evidence.validate_evidence_text(unsafe)

        self.assertFalse(result.ok)
        self.assertTrue(
            any("unsafe_report_file_name" in issue for issue in result.issues),
            result.issues,
        )


def _section_non_empty_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = lines.index(heading) + 1
    except ValueError:
        return []

    heading_level = _heading_level(heading)
    section: list[str] = []
    for line in lines[start:]:
        next_heading_level = _heading_level(line)
        if next_heading_level and next_heading_level <= heading_level:
            break
        stripped = line.strip()
        if stripped:
            section.append(stripped)
    return section


def _heading_level(line: str) -> int:
    stripped = line.strip()
    if not stripped.startswith("#"):
        return 0
    marker, _sep, _text = stripped.partition(" ")
    if not marker or any(char != "#" for char in marker):
        return 0
    return len(marker)


def _with_builder_git_context(text: str, git_args: str) -> str:
    builder_prefix = (
        "python3 tool/build_android_report_evidence.py "
        "build/pulled_performance_reports/performance_tier_v1_20260611T080158Z_perf-tier-1781111111000000-report-1.json "
        "--analysis-output-dir build/diagnostics_analysis_android_report_gate "
    )
    current_git_args = (
        f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} codex/android-report-loop "
        f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} abc1234 "
    )
    return text.replace(
        builder_prefix + current_git_args + "--output ",
        builder_prefix + git_args + "--output ",
        1,
    )


def _section_headings(text: str) -> list[str]:
    return [
        line.strip()
        for line in text.splitlines()
        if line.startswith("## ")
    ]


def _section_field_labels(text: str, heading: str) -> list[str]:
    labels: list[str] = []
    for line in _section_non_empty_lines(text, heading):
        if not line.startswith("- ") or ":" not in line:
            continue
        label, _ = line[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _section_key_value_fields(text: str, heading: str) -> list[str]:
    fields: list[str] = []
    for line in _section_non_empty_lines(text, heading):
        if line.startswith("```") or "=" not in line:
            continue
        field, _ = line.split("=", 1)
        fields.append(field.strip())
    return fields


def _top_status_block_labels(text: str) -> list[str]:
    labels: list[str] = []
    in_gate_block = False
    for line in text.splitlines():
        if line.strip() == "# Android Report Gate":
            in_gate_block = True
            continue
        if not in_gate_block:
            continue
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        label, _ = stripped[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _markdown_table_header(columns: list[str]) -> str:
    return "| " + " | ".join(columns) + " |"


def _markdown_table_divider(columns: list[str]) -> str:
    return "| " + " | ".join("---" for _ in columns) + " |"


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import analyze_diagnostics
from android_report_gate_contract import (
    ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS,
    ANDROID_REPORT_GATE_FAIL_STATUS,
    ANDROID_REPORT_GATE_HEADER_FIELDS,
    ANDROID_REPORT_GATE_PASS_STATUS,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
    ANDROID_REPORT_GATE_SINGLE_REPORT_HEADER_VALUES,
)

ROOT = Path(__file__).resolve().parents[1]
TESTDATA = ROOT / "tool" / "testdata"


class AndroidReportGateTest(unittest.TestCase):
    def test_v1_android_performance_report_passes_gate(self) -> None:
        analyzer = self._analyze(TESTDATA / "sample_performance_report.json")

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertEqual([], issues)

    def test_legacy_ai_report_is_not_android_report_gate_evidence(self) -> None:
        analyzer = self._analyze(TESTDATA / "sample_ai_report.json")

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertIn(
            "no_performance_report: no performance-report session rows found.",
            issues,
        )
        self.assertTrue(
            any("unexpected session source_type=ai-report" in issue for issue in issues),
            issues,
        )

    def test_mixed_legacy_and_v1_reports_fail_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "sample_performance_report.json").write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            (tmp_path / "sample_ai_report.json").write_text(
                (TESTDATA / "sample_ai_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analyzer = self._analyze_many(
                [
                    tmp_path / "sample_performance_report.json",
                    tmp_path / "sample_ai_report.json",
                ]
            )

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("unexpected session source_type=ai-report" in issue for issue in issues),
            issues,
        )

    def test_missing_required_android_signal_fails_gate(self) -> None:
        report = json.loads(
            (TESTDATA / "sample_performance_report.json").read_text(
                encoding="utf-8",
            )
        )
        del report["decision"]["deviceSignals"]["deviceModel"]
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "missing_device_model.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            analyzer = self._analyze(report_path)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("missing required field device_model" in issue for issue in issues),
            issues,
        )

    def test_missing_low_ram_signal_fails_gate(self) -> None:
        report = self._sample_performance_report()
        del report["decision"]["deviceSignals"]["isLowRamDevice"]
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("missing required field is_low_ram_device" in issue for issue in issues),
            issues,
        )

    def test_missing_media_performance_class_still_passes_gate(self) -> None:
        report = self._sample_performance_report()
        del report["decision"]["deviceSignals"]["mediaPerformanceClass"]
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertEqual([], issues)

    def test_non_string_identity_fields_fail_gate(self) -> None:
        report = self._sample_performance_report()
        report["reportId"] = 123
        report["source"] = 456
        report["metadata"]["serviceSessionId"] = 789
        report["decision"]["deviceSignals"]["deviceModel"] = 101112
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        expected_fragments = [
            "expected report_id to be a non-empty JSON string, got 123 (int)",
            "expected report_source to be a non-empty JSON string, got 456 (int)",
            "expected session_id to be a non-empty JSON string, got 789 (int)",
            "expected device_model to be a non-empty JSON string, got 101112 (int)",
        ]
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in issue for issue in issues), issues)

    def test_blank_identity_fields_fail_gate(self) -> None:
        report = self._sample_performance_report()
        report["reportId"] = "   "
        report["source"] = "\t"
        report["metadata"]["serviceSessionId"] = "\n"
        report["decision"]["deviceSignals"]["deviceModel"] = "   "
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        expected_fragments = [
            "expected report_id to be a non-empty JSON string",
            "expected report_source to be a non-empty JSON string",
            "expected session_id to be a non-empty JSON string",
            "expected device_model to be a non-empty JSON string",
        ]
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in issue for issue in issues), issues)

    def test_missing_report_sequence_fails_gate(self) -> None:
        report = self._sample_performance_report()
        del report["metadata"]["reportSequence"]
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("missing required field report_sequence" in issue for issue in issues),
            issues,
        )

    def test_string_report_sequence_fails_gate(self) -> None:
        report = self._sample_performance_report()
        report["metadata"]["reportSequence"] = "1"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected report_sequence to be a JSON integer, got '1' (str)"
                in issue
                for issue in issues
            ),
            issues,
        )

    def test_report_identity_must_match_session_and_sequence(self) -> None:
        report = self._sample_performance_report()
        report["reportId"] = "other-session-report-1"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected report_id=perf-tier-1781111111000000-report-1 "
                "from service session and report_sequence" in issue
                for issue in issues
            ),
            issues,
        )

    def test_report_sequence_must_match_report_id_suffix(self) -> None:
        report = self._sample_performance_report()
        report["metadata"]["reportSequence"] = 2
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected report_id=perf-tier-1781111111000000-report-2 "
                "from service session and report_sequence" in issue
                for issue in issues
            ),
            issues,
        )

    def test_duplicate_report_identity_fails_gate(self) -> None:
        report = self._sample_performance_report()
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_path = tmp_path / "first_report.json"
            second_path = tmp_path / "second_report.json"
            first_path.write_text(json.dumps(report), encoding="utf-8")
            second_path.write_text(json.dumps(report), encoding="utf-8")
            analyzer = self._analyze_many([first_path, second_path])

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("duplicate_report_id" in issue for issue in issues),
            issues,
        )
        self.assertTrue(
            any("duplicate_report_sequence" in issue for issue in issues),
            issues,
        )

    def test_non_integer_schema_version_fails_gate(self) -> None:
        report = self._sample_performance_report()
        report["schemaVersion"] = 1.9
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("expected schema_version=1" in issue for issue in issues),
            issues,
        )

    def test_string_schema_version_fails_gate(self) -> None:
        report = self._sample_performance_report()
        report["schemaVersion"] = "1"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected schema_version=1, got '1' (str)" in issue
                for issue in issues
            ),
            issues,
        )

    def test_invalid_report_timestamps_fail_gate(self) -> None:
        report = self._sample_performance_report()
        report["generatedAt"] = "2026-06-11"
        report["decision"]["decidedAt"] = "also-not-a-timestamp"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected generated_at to be an ISO-8601 timestamp" in issue
                for issue in issues
            ),
            issues,
        )
        self.assertTrue(
            any(
                "expected decided_at to be an ISO-8601 timestamp" in issue
                for issue in issues
            ),
            issues,
        )

    def test_generated_at_requires_utc_timestamp(self) -> None:
        report = self._sample_performance_report()
        report["generatedAt"] = "2026-06-11T08:02:03.004"
        report["decision"]["decidedAt"] = "2026-06-11T08:01:58.000"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected generated_at to be an ISO-8601 UTC timestamp" in issue
                for issue in issues
            ),
            issues,
        )
        self.assertFalse(
            any("expected decided_at" in issue for issue in issues),
            issues,
        )

    def test_non_string_report_timestamps_fail_gate(self) -> None:
        report = self._sample_performance_report()
        report["generatedAt"] = 123
        report["decision"]["decidedAt"] = 456
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected generated_at to be a non-empty JSON string, got 123 (int)"
                in issue
                for issue in issues
            ),
            issues,
        )
        self.assertTrue(
            any(
                "expected decided_at to be a non-empty JSON string, got 456 (int)"
                in issue
                for issue in issues
            ),
            issues,
        )

    def test_report_generated_at_cannot_precede_decision_time(self) -> None:
        report = self._sample_performance_report()
        report["generatedAt"] = "2026-06-11T08:01:57.000Z"
        report["decision"]["decidedAt"] = "2026-06-11T08:01:58.000Z"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(
                "expected generated_at to be at or after decided_at" in issue
                for issue in issues
            ),
            issues,
        )

    def test_android_sdk_29_plus_requires_thermal_fields(self) -> None:
        report = self._sample_performance_report()
        signals = report["decision"]["deviceSignals"]
        signals["sdkInt"] = 35
        del signals["thermalState"]
        del signals["thermalStateLevel"]
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("missing required field thermal_state" in issue for issue in issues),
            issues,
        )
        self.assertTrue(
            any(
                "missing required field thermal_state_level" in issue
                for issue in issues
            ),
            issues,
        )

    def test_android_below_sdk_29_allows_missing_thermal_fields(self) -> None:
        report = self._sample_performance_report()
        signals = report["decision"]["deviceSignals"]
        signals["sdkInt"] = 28
        signals.pop("thermalState", None)
        signals.pop("thermalStateLevel", None)
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertEqual([], issues)

    def test_non_android_report_fails_gate(self) -> None:
        report = self._sample_performance_report()
        signals = report["decision"]["deviceSignals"]
        signals["platform"] = "ios"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("expected platform=android" in issue for issue in issues),
            issues,
        )

    def test_unexpected_gate_values_fail_gate(self) -> None:
        report = self._sample_performance_report()
        decision = report["decision"]
        signals = decision["deviceSignals"]
        decision["tier"] = "t9Impossible"
        decision["confidence"] = "certain"
        decision["runtimeObservation"]["status"] = "wedged"
        signals["totalRamBytes"] = 0
        signals["sdkInt"] = 0
        signals["memoryPressureState"] = "unknown"
        signals["memoryPressureLevel"] = 9
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        expected_fragments = [
            "unexpected tier=t9Impossible",
            "unexpected confidence=certain",
            "unexpected runtime_status=wedged",
            "expected total_ram_bytes to be greater than 0",
            "expected sdk_int to be greater than 0",
            "unexpected memory_pressure_state=unknown",
            "unexpected memory_pressure_level=9",
        ]
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in issue for issue in issues), issues)

    def test_non_string_wire_fields_fail_gate(self) -> None:
        report = self._sample_performance_report()
        decision = report["decision"]
        signals = decision["deviceSignals"]
        decision["tier"] = 1
        decision["confidence"] = 2
        decision["runtimeObservation"]["status"] = 3
        signals["platform"] = 4
        signals["memoryPressureState"] = 5
        signals["thermalState"] = 6
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        expected_fragments = [
            "expected tier to be a non-empty JSON string, got 1 (int)",
            "expected confidence to be a non-empty JSON string, got 2 (int)",
            "expected runtime_status to be a non-empty JSON string, got 3 (int)",
            "expected platform to be a non-empty JSON string, got 4 (int)",
            "expected memory_pressure_state to be a non-empty JSON string, got 5 (int)",
            "expected thermal_state to be a non-empty JSON string, got 6 (int)",
        ]
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in issue for issue in issues), issues)

    def test_string_android_numeric_signals_fail_gate(self) -> None:
        report = self._sample_performance_report()
        signals = report["decision"]["deviceSignals"]
        signals["totalRamBytes"] = "8589934592"
        signals["sdkInt"] = "35"
        signals["memoryPressureLevel"] = "1"
        signals["thermalStateLevel"] = "1"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        expected_fragments = [
            "expected total_ram_bytes to be a JSON integer, got '8589934592' (str)",
            "expected sdk_int to be a JSON integer, got '35' (str)",
            "expected memory_pressure_level to be a JSON integer, got '1' (str)",
            "expected thermal_state_level to be a JSON integer, got '1' (str)",
        ]
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in issue for issue in issues), issues)

    def test_string_android_boolean_signals_fail_gate(self) -> None:
        report = self._sample_performance_report()
        signals = report["decision"]["deviceSignals"]
        signals["isLowRamDevice"] = "false"
        signals["isLowPowerModeEnabled"] = "false"
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        expected_fragments = [
            "expected is_low_ram_device to be a JSON boolean, got 'false' (str)",
            "expected is_low_power_mode_enabled to be a JSON boolean, got 'false' (str)",
        ]
        for fragment in expected_fragments:
            self.assertTrue(any(fragment in issue for issue in issues), issues)

    def test_unexpected_thermal_values_fail_gate_on_sdk_29_plus(self) -> None:
        report = self._sample_performance_report()
        signals = report["decision"]["deviceSignals"]
        signals["sdkInt"] = 35
        signals["thermalState"] = "melting"
        signals["thermalStateLevel"] = 99
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("unexpected thermal_state=melting" in issue for issue in issues),
            issues,
        )
        self.assertTrue(
            any("unexpected thermal_state_level=99" in issue for issue in issues),
            issues,
        )

    def test_fallback_decision_fails_gate(self) -> None:
        report = self._sample_performance_report()
        report["decision"]["reasons"].append(
            "Failed to collect platform signals; using fallback.",
        )
        analyzer = self._analyze_report_payload(report)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any("fallback decision observed" in issue for issue in issues),
            issues,
        )

    def test_parse_issues_fail_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "broken.json"
            report_path.write_text("{", encoding="utf-8")
            analyzer = self._analyze(report_path)

        issues = analyze_diagnostics.android_report_gate_issues(analyzer)

        self.assertTrue(
            any(issue.startswith("parse_issues:") for issue in issues),
            issues,
        )

    def test_gate_markdown_reports_pass_and_fail(self) -> None:
        passing = self._analyze(TESTDATA / "sample_performance_report.json")
        failing = self._analyze(TESTDATA / "sample_ai_report.json")
        self.assertEqual(
            ANDROID_REPORT_GATE_PASS_STATUS,
            analyze_diagnostics.android_report_gate_status([]),
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_FAIL_STATUS,
            analyze_diagnostics.android_report_gate_status(["issue"]),
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            analyze_diagnostics.write_android_report_gate(
                output_dir,
                passing,
                analyze_diagnostics.android_report_gate_issues(passing),
            )
            pass_markdown = (output_dir / "android_report_gate.md").read_text(
                encoding="utf-8",
            )
            analyze_diagnostics.write_android_report_gate(
                output_dir,
                failing,
                analyze_diagnostics.android_report_gate_issues(failing),
            )
            fail_markdown = (output_dir / "android_report_gate.md").read_text(
                encoding="utf-8",
            )

        self.assertIn("- Status: PASS", pass_markdown)
        self.assertEqual(
            [
                label
                for label, _summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
            ],
            _top_status_block_labels(pass_markdown),
        )
        self.assertEqual(
            ANDROID_REPORT_GATE_SINGLE_REPORT_HEADER_VALUES,
            _top_status_block_values(pass_markdown),
        )
        self.assertIn("## Gate Summary", pass_markdown)
        self.assertIn("status=PASS", pass_markdown)
        self.assertIn("issueCount=0", pass_markdown)
        self.assertIn("performanceReportRows=1", pass_markdown)
        self.assertIn("## Performance Reports", pass_markdown)
        self.assertIn(
            _markdown_table_header(
                ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
            ),
            pass_markdown,
        )
        self.assertIn("perf-tier-1781111111000000-report-1", pass_markdown)
        self.assertIn("2026-06-11T08:01:58.000Z", pass_markdown)
        self.assertIn("## Android Signals", pass_markdown)
        self.assertIn(
            _markdown_table_header(ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS),
            pass_markdown,
        )
        self.assertIn("Pixel 8 Pro", pass_markdown)
        self.assertIn("15", pass_markdown)
        self.assertIn("8589934592", pass_markdown)
        self.assertIn("normal", pass_markdown)
        self.assertIn("## Report Field Check", pass_markdown)
        self.assertIn(
            "### perf-tier-1781111111000000-report-1",
            pass_markdown,
        )
        self.assertEqual(
            1,
            pass_markdown.count("### perf-tier-1781111111000000-report-1"),
        )
        self.assertIn(
            "- `metadata.serviceSessionId`: perf-tier-1781111111000000",
            pass_markdown,
        )
        self.assertIn("- `decision.deviceSignals.osVersion`: 15", pass_markdown)
        self.assertIn("- `metadata.reportSequence`: 1", pass_markdown)
        self.assertIn(
            "- `decision.deviceSignals.isLowPowerModeEnabled`: false",
            pass_markdown,
        )
        self.assertIn("## Identity And Gate Checklist", pass_markdown)
        self.assertIn("- `schemaVersion` is JSON integer `1`: yes", pass_markdown)
        self.assertIn(
            "- `reportId` equals `<metadata.serviceSessionId>-report-<metadata.reportSequence>`: yes",
            pass_markdown,
        )
        self.assertIn(
            "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes",
            pass_markdown,
        )
        self.assertIn(
            "OS version, `generatedAt`, and `decision.decidedAt` are non-empty JSON strings",
            pass_markdown,
        )
        self.assertIn("- Status: FAIL", fail_markdown)
        self.assertEqual(
            [
                label
                for label, _summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
            ],
            _top_status_block_labels(fail_markdown),
        )
        self.assertIn("status=FAIL", fail_markdown)
        self.assertIn("issueCount=2", fail_markdown)
        self.assertIn("- No performance report rows.", fail_markdown)
        self.assertIn("- `schemaVersion` is JSON integer `1`: no", fail_markdown)
        self.assertIn("no_performance_report", fail_markdown)

    def test_discover_input_files_excludes_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            input_dir = root / "pulled_reports"
            output_dir = input_dir / "diagnostics_analysis"
            output_dir.mkdir(parents=True)
            report_path = input_dir / "device_report.json"
            generated_output_path = output_dir / "session_summary.json"
            report_path.write_text("{}", encoding="utf-8")
            generated_output_path.write_text("{}", encoding="utf-8")

            files = analyze_diagnostics.discover_input_files(
                [input_dir],
                output_dir,
            )

        self.assertEqual([report_path.resolve()], files)

    def _analyze(self, path: Path) -> analyze_diagnostics.DiagnosticsAnalyzer:
        return self._analyze_many([path])

    def _analyze_many(
        self,
        paths: list[Path],
    ) -> analyze_diagnostics.DiagnosticsAnalyzer:
        analyzer = analyze_diagnostics.DiagnosticsAnalyzer(
            prefix="PERF_TIER_LOG",
            top_n=10,
        )
        analyzer.ingest_files(paths)
        return analyzer

    def _analyze_report_payload(
        self,
        report: dict[str, object],
    ) -> analyze_diagnostics.DiagnosticsAnalyzer:
        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = Path(tmp_dir) / "report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            return self._analyze(report_path)

    def _sample_performance_report(self) -> dict[str, object]:
        return json.loads(
            (TESTDATA / "sample_performance_report.json").read_text(
                encoding="utf-8",
            )
        )


def _markdown_table_header(columns: list[str]) -> str:
    return "| " + " | ".join(columns) + " |"


def _top_status_block_labels(markdown: str) -> list[str]:
    return list(_top_status_block_values(markdown).keys())


def _top_status_block_values(markdown: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in markdown.splitlines():
        if line.startswith("## "):
            break
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        values[key.strip()] = value.strip()
    return values


if __name__ == "__main__":
    unittest.main()

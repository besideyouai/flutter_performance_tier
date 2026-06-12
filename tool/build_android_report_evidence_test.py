#!/usr/bin/env python3

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

import analyze_diagnostics
import build_android_report_evidence
import validate_android_report_evidence
from android_report_evidence_contract import (
    ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
    ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
    ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
    ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
    ANDROID_REPORT_EVIDENCE_GIT_BRANCH_COMMAND,
    ANDROID_REPORT_EVIDENCE_GIT_COMMIT_COMMAND,
    ANDROID_REPORT_EVIDENCE_HOST_APP_USED,
    ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
    ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
    ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
)


ROOT = Path(__file__).resolve().parents[1]
TESTDATA = ROOT / "tool" / "testdata"


class AndroidReportEvidenceBuilderTest(unittest.TestCase):
    def test_builds_validator_passing_evidence_from_gate_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            output_path = root / "evidence.md"
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=analysis_output_dir,
                gate_markdown_path=analysis_output_dir / "android_report_gate.md",
                output_path=output_path,
                run_date="2026-06-11",
                branch="codex/android-report-loop",
                commit="abc1234",
                app_used=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
                app_variant="debug",
                application_id="com.example.flutter_performance_tier_example",
                android_version=None,
            )

            build_android_report_evidence.write_evidence_draft(config)
            evidence = output_path.read_text(encoding="utf-8")
            validation = validate_android_report_evidence.validate_evidence_text(
                evidence,
            )

        self.assertEqual([], validation.issues)
        self.assertIn("android_report_gate.md", evidence)
        self.assertIn(ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING, evidence)
        self.assertIn(ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT, evidence)
        for snippet in ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS:
            self.assertIn(snippet, evidence)
        self.assertIn("tool/build_android_report_evidence.py", evidence)
        self.assertIn("tool/validate_android_report_evidence.py", evidence)
        self.assertIn(
            "the validator only accepts a single safe `.json` report",
            evidence,
        )
        self.assertIn(
            "Keep exactly one\n`### <reportId>` heading under `Report Field Check`",
            evidence,
        )
        self.assertIn("- Device model: Pixel 8 Pro", evidence)
        self.assertIn("- Android version: 15", evidence)
        self.assertIn("## Report Field Check", evidence)
        self.assertIn("### perf-tier-1781111111000000-report-1", evidence)
        self.assertIn("## Identity And Gate Checklist", evidence)

    def test_uses_configured_application_id_in_context_and_host_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            output_path = root / "evidence.md"
            application_id = "com.example.host_app"
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=analysis_output_dir,
                gate_markdown_path=analysis_output_dir / "android_report_gate.md",
                output_path=output_path,
                run_date="2026-06-11",
                branch="codex/android-report-loop",
                commit="abc1234",
                app_used=ANDROID_REPORT_EVIDENCE_HOST_APP_USED,
                app_variant="release",
                application_id=application_id,
                android_version=None,
            )

            evidence = build_android_report_evidence.build_evidence_markdown(config)
            validation = validate_android_report_evidence.validate_evidence_text(
                evidence,
            )

        self.assertEqual([], validation.issues)
        self.assertIn(f"- Application id: {application_id}", evidence)
        self.assertIn(f"adb shell run-as {application_id} ls", evidence)
        self.assertIn(f"adb exec-out run-as {application_id} cat", evidence)
        self.assertIn(
            f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} codex/android-report-loop",
            evidence,
        )
        self.assertIn(f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} abc1234", evidence)
        self.assertIn(
            f"{ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION} {application_id}",
            evidence,
        )

    def test_cli_requires_explicit_application_id(self) -> None:
        with patch("sys.stderr", new=io.StringIO()):
            with self.assertRaises(SystemExit) as exit_context:
                build_android_report_evidence.parse_args(
                    [
                        "build/pulled_report.json",
                        ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
                        "build/evidence.md",
                    ],
                )

        self.assertNotEqual(0, exit_context.exception.code)

    def test_cli_accepts_explicit_application_id(self) -> None:
        args = build_android_report_evidence.parse_args(
            [
                "build/pulled_report.json",
                ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
                "build/evidence.md",
                ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
                "com.example.host_app",
            ],
        )

        self.assertEqual("com.example.host_app", args.application_id)

    def test_cli_resolves_missing_git_context_with_shared_contract_commands(
        self,
    ) -> None:
        args = build_android_report_evidence.parse_args(
            [
                "build/pulled_report.json",
                ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
                "build/evidence.md",
                ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
                "com.example.host_app",
            ],
        )

        def git_value(command: Sequence[str]) -> str:
            if command == ANDROID_REPORT_EVIDENCE_GIT_BRANCH_COMMAND:
                return "codex/android-report-loop"
            if command == ANDROID_REPORT_EVIDENCE_GIT_COMMIT_COMMAND:
                return "abc1234"
            raise AssertionError(f"unexpected git command: {command!r}")

        with patch.object(build_android_report_evidence, "_git_value", git_value):
            config = build_android_report_evidence.config_from_args(args)

        self.assertEqual("codex/android-report-loop", config.branch)
        self.assertEqual("abc1234", config.commit)

    def test_rejects_blank_application_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=analysis_output_dir,
                gate_markdown_path=analysis_output_dir / "android_report_gate.md",
                output_path=root / "evidence.md",
                run_date="2026-06-11",
                branch="codex/android-report-loop",
                commit="abc1234",
                app_used=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
                app_variant="debug",
                application_id=" ",
                android_version=None,
            )

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "non-empty Application id",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_placeholder_branch_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=analysis_output_dir,
                gate_markdown_path=analysis_output_dir / "android_report_gate.md",
                output_path=root / "evidence.md",
                run_date="2026-06-11",
                branch="<branch>",
                commit="abc1234",
                app_used=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
                app_variant="debug",
                application_id="com.example.flutter_performance_tier_example",
                android_version=None,
            )

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Branch without placeholders",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_unknown_app_used_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=analysis_output_dir,
                gate_markdown_path=analysis_output_dir / "android_report_gate.md",
                output_path=root / "evidence.md",
                run_date="2026-06-11",
                branch="codex/android-report-loop",
                commit="abc1234",
                app_used="staging app",
                app_variant="debug",
                application_id="com.example.flutter_performance_tier_example",
                android_version=None,
            )

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "App used",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_cli_requires_branch_when_git_branch_is_unavailable(self) -> None:
        args = build_android_report_evidence.parse_args(
            [
                "build/pulled_report.json",
                ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
                "build/evidence.md",
                ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
                "com.example.host_app",
            ],
        )

        with patch.object(build_android_report_evidence, "_git_value", return_value=""):
            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                f"pass {ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} explicitly",
            ):
                build_android_report_evidence.config_from_args(args)

    def test_cli_requires_commit_when_git_commit_is_unavailable(self) -> None:
        args = build_android_report_evidence.parse_args(
            [
                "build/pulled_report.json",
                ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
                "build/evidence.md",
                ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
                "com.example.host_app",
                ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
                "codex/android-report-loop",
            ],
        )

        with patch.object(build_android_report_evidence, "_git_value", return_value=""):
            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                f"pass {ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} explicitly",
            ):
                build_android_report_evidence.config_from_args(args)

    def test_rejects_unsafe_report_file_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "unsafe report.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=analysis_output_dir,
                gate_markdown_path=analysis_output_dir / "android_report_gate.md",
                output_path=root / "evidence.md",
                run_date="2026-06-11",
                branch="codex/android-report-loop",
                commit="abc1234",
                app_used=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
                app_variant="debug",
                application_id="com.example.flutter_performance_tier_example",
                android_version=None,
            )

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "safe .json file name",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_gate_markdown_for_another_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "perf-tier-1781111111000000-report-1",
                    "other-session-report-1",
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Report Field Check heading",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_multi_report_gate_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "performanceReportRows=1",
                    "performanceReportRows=2",
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "performanceReportRows=1",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_unfenced_gate_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8")
                .replace("```text\n", "")
                .replace("```\n\n## Checks", "\n## Checks"),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Gate Summary fields",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_unexpected_gate_summary_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "parseIssues=0\n```",
                    "parseIssues=0\nunexpected=1\n```",
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Gate Summary fields",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_mismatched_gate_header_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- Status: PASS",
                    "- Status: FAIL",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "header Status=PASS",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_mismatched_gate_header_row_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- Performance report rows: 1",
                    "- Performance report rows: 2",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "header Performance report rows=1",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_unexpected_gate_header_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- Parse issues: 0\n\n## Gate Summary",
                    "- Parse issues: 0\n- Unexpected: yes\n\n## Gate Summary",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "header fields",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_gate_markdown_missing_checks_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "## Checks",
                    "## Checks Removed",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Checks section",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_gate_markdown_with_mismatched_checks_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- No parse issues.",
                    "- Parse issues were not reviewed.",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Checks section",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_gate_source_for_another_report_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    str(report_path),
                    str(root / "other_report.json"),
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Performance Reports Source",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_performance_report_table_value_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    " | t2High | high | inactive | ",
                    " | t0Low | high | inactive | ",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Performance Reports Tier",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_performance_report_table_extra_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "| Source | Report ID | Source Tag | Session | Sequence | Tier | Confidence | Runtime | Generated At | Decided At |",
                    "| Source | Report ID | Source Tag | Session | Sequence | Tier | Confidence | Runtime | Generated At | Decided At | Unexpected |",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Performance Reports columns",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_android_signal_table_value_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    " | false | false | normal | 0 | normal | 0 |",
                    " | false | true | normal | 0 | normal | 0 |",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Android Signals Low Power",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_android_signal_table_extra_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "| Report ID | Platform | Device | OS Version | SDK | RAM bytes | Low RAM | Low Power | Memory Pressure | Memory Level | Thermal | Thermal Level |",
                    "| Report ID | Platform | Device | OS Version | SDK | RAM bytes | Low RAM | Low Power | Memory Pressure | Memory Level | Thermal | Thermal Level | Unexpected |",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Android Signals columns",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_field_check_value_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- `decision.deviceSignals.osVersion`: 15",
                    "- `decision.deviceSignals.osVersion`: 14",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Report Field Check `decision.deviceSignals.osVersion`",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_field_check_extra_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- `decision.runtimeObservation.status`: inactive\n",
                    "- `decision.runtimeObservation.status`: inactive\n"
                    "- `unexpected`: value\n",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Report Field Check labels",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_identity_checklist_not_yes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes",
                    "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: no",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Identity And Gate Checklist",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_identity_checklist_extra_label(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes\n",
                    "- Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs: yes\n"
                    "- Unexpected checklist label: yes\n",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Identity And Gate Checklist labels",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_non_empty_gate_issues_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            analysis_output_dir = root / "analysis"
            analyzer = self._analyze(report_path)
            analyzer.write_outputs(analysis_output_dir)
            analyze_diagnostics.write_android_report_gate(
                analysis_output_dir,
                analyzer,
                analyze_diagnostics.android_report_gate_issues(analyzer),
            )
            gate_path = analysis_output_dir / "android_report_gate.md"
            gate_path.write_text(
                gate_path.read_text(encoding="utf-8").replace(
                    "- None.",
                    "- stale gate issue.",
                    1,
                ),
                encoding="utf-8",
            )
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "Issues section",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_json_array_report_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_batch.json"
            report_path.write_text(
                "["
                + (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                )
                + "]",
                encoding="utf-8",
            )
            gate_path = root / "android_report_gate.md"
            gate_path.write_text(
                "# Android Report Gate\n\n"
                "- Status: PASS\n\n"
                "## Gate Summary\n\n"
                "status=PASS\n",
                encoding="utf-8",
            )
            config = build_android_report_evidence.EvidenceDraftConfig(
                report_path=report_path,
                analysis_output_dir=root,
                gate_markdown_path=gate_path,
                output_path=root / "evidence.md",
                run_date="2026-06-11",
                branch="codex/android-report-loop",
                commit="abc1234",
                app_used=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
                app_variant="debug",
                application_id="com.example.flutter_performance_tier_example",
                android_version=None,
            )

            with self.assertRaises(build_android_report_evidence.EvidenceDraftError):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_non_v1_report_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["schemaName"] = "legacy.ai_diagnostics"
            report_path = root / "legacy_report.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "expected schemaName",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_with_blank_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["source"] = " "
            report_path = root / "performance_tier_v1_blank_source.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "non-empty string source",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_with_non_utc_generated_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["generatedAt"] = "2026-06-11T08:02:03.004"
            report_path = root / "performance_tier_v1_non_utc_generated_at.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "generatedAt to be UTC ISO-8601",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_with_date_only_decided_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["decision"]["decidedAt"] = "2026-06-11"
            report_path = root / "performance_tier_v1_date_only_decided_at.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "decision.decidedAt to be ISO-8601",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_generated_before_decision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["generatedAt"] = "2026-06-11T08:01:57.999Z"
            report_path = root / "performance_tier_v1_timestamp_order.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "generatedAt to be at or after decision.decidedAt",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_id_that_does_not_match_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["reportId"] = "wrong-report-id"
            report_path = root / "performance_tier_v1_wrong_identity.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "expected reportId to match",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_missing_android_device_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            del report["decision"]["deviceSignals"]["deviceModel"]
            report_path = root / "performance_tier_v1_missing_device_model.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "decision.deviceSignals.deviceModel",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_rejects_report_with_string_android_boolean_signal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = json.loads(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
            )
            report["decision"]["deviceSignals"]["isLowPowerModeEnabled"] = "false"
            report_path = root / "performance_tier_v1_string_boolean.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            gate_path = root / "android_report_gate.md"
            gate_path.write_text("# Android Report Gate\n", encoding="utf-8")
            config = self._config(root, report_path, gate_path)

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "boolean decision.deviceSignals.isLowPowerModeEnabled",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def test_wraps_missing_gate_markdown_as_draft_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report_path = root / "performance_tier_v1_sample.json"
            report_path.write_text(
                (TESTDATA / "sample_performance_report.json").read_text(
                    encoding="utf-8",
                ),
                encoding="utf-8",
            )
            config = self._config(
                root,
                report_path,
                root / "missing_android_report_gate.md",
            )

            with self.assertRaisesRegex(
                build_android_report_evidence.EvidenceDraftError,
                "unable to read android_report_gate.md",
            ):
                build_android_report_evidence.build_evidence_markdown(config)

    def _config(
        self,
        root: Path,
        report_path: Path,
        gate_path: Path,
    ) -> build_android_report_evidence.EvidenceDraftConfig:
        return build_android_report_evidence.EvidenceDraftConfig(
            report_path=report_path,
            analysis_output_dir=root,
            gate_markdown_path=gate_path,
            output_path=root / "evidence.md",
            run_date="2026-06-11",
            branch="codex/android-report-loop",
            commit="abc1234",
            app_used=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
            app_variant="debug",
            application_id="com.example.flutter_performance_tier_example",
            android_version=None,
        )

    def _analyze(self, path: Path) -> analyze_diagnostics.DiagnosticsAnalyzer:
        analyzer = analyze_diagnostics.DiagnosticsAnalyzer(
            prefix="PERF_TIER_LOG",
            top_n=10,
        )
        analyzer.ingest_files([path])
        return analyzer


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from android_report_evidence_contract import (
    ANDROID_REPORT_EVIDENCE_ANALYZER_SCRIPT,
    ANDROID_REPORT_EVIDENCE_ANALYZER_EXIT_CODE_LABEL,
    ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION,
    ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL,
    ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION,
    ANDROID_REPORT_EVIDENCE_ADB_LIST_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_ADB_LIST_COMMAND,
    ANDROID_REPORT_EVIDENCE_ADB_PULL_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_ADB_PULL_COMMAND,
    ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_OPTION,
    ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_LABEL,
    ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
    ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL,
    ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES,
    ANDROID_REPORT_EVIDENCE_APP_SIDE_TRIGGER_HEADING,
    ANDROID_REPORT_EVIDENCE_APP_USED_OPTION,
    ANDROID_REPORT_EVIDENCE_APP_USED_LABEL,
    ANDROID_REPORT_EVIDENCE_APP_VARIANT_OPTION,
    ANDROID_REPORT_EVIDENCE_APP_VARIANT_LABEL,
    ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
    ANDROID_REPORT_EVIDENCE_BRANCH_LABEL,
    ANDROID_REPORT_EVIDENCE_COMMIT_LABEL,
    ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
    ANDROID_REPORT_EVIDENCE_COPIED_COMMANDS_AVAILABLE_LABEL,
    ANDROID_REPORT_EVIDENCE_COPY_SOURCE_LABEL,
    ANDROID_REPORT_EVIDENCE_COPY_SOURCE_VALUE,
    ANDROID_REPORT_EVIDENCE_DATE_LABEL,
    ANDROID_REPORT_EVIDENCE_DATE_OPTION,
    ANDROID_REPORT_EVIDENCE_DEFAULT_APP_VARIANT,
    ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY,
    ANDROID_REPORT_EVIDENCE_DEVICE_MODEL_LABEL,
    ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT,
    ANDROID_REPORT_EVIDENCE_ALLOW_GATE_FAIL_COMMAND,
    ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
    ANDROID_REPORT_EVIDENCE_FAIL_RESULT,
    ANDROID_REPORT_EVIDENCE_FAIL_STATUS,
    ANDROID_REPORT_EVIDENCE_FAIL_FAST_START_COMMAND,
    ANDROID_REPORT_EVIDENCE_FAILURE_CATEGORY_LABEL,
    ANDROID_REPORT_EVIDENCE_GATE_FAILURE_CATEGORY,
    ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_OPTION,
    ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_PRINT_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_GATE_STATUS_CAPTURE_COMMAND,
    ANDROID_REPORT_EVIDENCE_GATE_STATUS_LABEL,
    ANDROID_REPORT_EVIDENCE_GATE_STATUS_CHECK_COMMAND,
    ANDROID_REPORT_EVIDENCE_GIT_BRANCH_COMMAND,
    ANDROID_REPORT_EVIDENCE_GIT_COMMIT_COMMAND,
    ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT,
    ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_LABEL,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
    ANDROID_REPORT_EVIDENCE_HOST_OUTPUTS_HEADING,
    ANDROID_REPORT_EVIDENCE_HOST_DIR_PREPARE_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_NONEMPTY_REPORT_CHECK_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_ON_DEVICE_DIRECTORY_LABEL,
    ANDROID_REPORT_EVIDENCE_ON_DEVICE_DIRECTORY_VALUE,
    ANDROID_REPORT_EVIDENCE_NO_FAILURE_CATEGORY,
    ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
    ANDROID_REPORT_EVIDENCE_PASS_FAIL_LABEL,
    ANDROID_REPORT_EVIDENCE_PASS_RESULT,
    ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
    ANDROID_REPORT_EVIDENCE_RAM_LABEL,
    ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL,
    ANDROID_REPORT_EVIDENCE_REPORT_LIST_REFRESHED_LABEL,
    ANDROID_REPORT_EVIDENCE_REPORT_LIST_REFRESHED_VALUE,
    ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
    ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_HEADING,
    ANDROID_REPORT_EVIDENCE_SDK_INT_LABEL,
    ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN,
    ANDROID_REPORT_EVIDENCE_THERMAL_POWER_LABEL,
    ANDROID_REPORT_EVIDENCE_TRIGGER_PATH_LABEL,
    ANDROID_REPORT_EVIDENCE_TRIGGER_PATH_VALUE,
    ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT,
    android_report_device_path,
    evidence_draft_line,
    host_command_argv_text,
    host_path_basename,
    is_safe_report_file_name,
)
from android_report_gate_contract import (
    ANDROID_REPORT_GATE_CHECK_LINES,
    ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
    ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS,
    ANDROID_REPORT_GATE_CHECKS_HEADING,
    ANDROID_REPORT_GATE_FIELD_CHECK_LABELS,
    ANDROID_REPORT_GATE_HEADER_FIELDS,
    ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
    ANDROID_REPORT_GATE_ISSUES_HEADING,
    ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME,
    ANDROID_REPORT_GATE_NO_ISSUES_LINE,
    ANDROID_REPORT_GATE_PASS_STATUS,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
    ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
    ANDROID_REPORT_GATE_SINGLE_REPORT_HEADER_VALUES,
    ANDROID_REPORT_GATE_SINGLE_REPORT_SUMMARY_VALUES,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START,
    ANDROID_REPORT_GATE_SUMMARY_FIELDS,
    ANDROID_REPORT_GATE_SUMMARY_HEADING,
    ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD,
    IDENTITY_CHECKLIST_LABELS,
    PERFORMANCE_REPORT_SCHEMA_NAME,
)

DEFAULT_ANALYSIS_OUTPUT_DIR = Path("build/diagnostics_analysis_android_report_gate")


class EvidenceDraftError(ValueError):
    pass


@dataclass(frozen=True)
class EvidenceDraftConfig:
    report_path: Path
    analysis_output_dir: Path
    gate_markdown_path: Path
    output_path: Path
    run_date: str
    branch: str
    commit: str
    app_used: str
    app_variant: str
    application_id: str
    android_version: str | None


def build_evidence_markdown(config: EvidenceDraftConfig) -> str:
    _validate_run_context(config)
    report = _load_report(config.report_path)
    report_file_name = config.report_path.name
    if not is_safe_report_file_name(report_file_name):
        raise EvidenceDraftError(
            "expected pulled report file name to be a safe .json file name, "
            f"got {report_file_name!r}."
        )
    device_signals = _dict_at(report, "decision", "deviceSignals")
    gate_markdown = _read_text_file(
        config.gate_markdown_path,
        ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME,
    ).strip()
    _validate_gate_markdown_matches_report(gate_markdown, report, config.report_path)
    gate_status = _gate_status(gate_markdown)
    gate_passed = gate_status == ANDROID_REPORT_GATE_PASS_STATUS
    analyzer_exit_code = "0" if gate_passed else "2"
    pulled_report_path = str(config.report_path)
    analysis_output_dir = str(config.analysis_output_dir)
    android_version = config.android_version or _text(device_signals.get("osVersion"))
    ram_text = _ram_text(device_signals.get("totalRamBytes"))
    thermal_power_text = _thermal_power_text(device_signals)

    return "\n".join(
        [
            "# Android Report Loop Evidence",
            "",
            "Generated from a pulled report and "
            f"`{ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME}`. Review the",
            "run context before using this as readiness evidence.",
            "Readiness evidence must stay scoped to this selected report file;",
            "the validator only accepts a single safe `.json` report, not a directory",
            "or multi-report batch.",
            "",
            ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_HEADING,
            "",
            f"- {ANDROID_REPORT_EVIDENCE_DATE_LABEL}: {config.run_date}",
            f"- {ANDROID_REPORT_EVIDENCE_BRANCH_LABEL}: {config.branch}",
            f"- {ANDROID_REPORT_EVIDENCE_COMMIT_LABEL}: {config.commit}",
            f"- {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL}: {config.app_used}",
            f"- {ANDROID_REPORT_EVIDENCE_APP_VARIANT_LABEL}: {config.app_variant}",
            f"- {ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL}: {config.application_id}",
            f"- {ANDROID_REPORT_EVIDENCE_DEVICE_MODEL_LABEL}: {_text(device_signals.get('deviceModel'))}",
            f"- {ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_LABEL}: {android_version}",
            f"- {ANDROID_REPORT_EVIDENCE_SDK_INT_LABEL}: {_text(device_signals.get('sdkInt'))}",
            f"- {ANDROID_REPORT_EVIDENCE_RAM_LABEL}: {ram_text}",
            f"- {ANDROID_REPORT_EVIDENCE_THERMAL_POWER_LABEL}: {thermal_power_text}",
            "",
            ANDROID_REPORT_EVIDENCE_APP_SIDE_TRIGGER_HEADING,
            "",
            f"- {ANDROID_REPORT_EVIDENCE_TRIGGER_PATH_LABEL}: {ANDROID_REPORT_EVIDENCE_TRIGGER_PATH_VALUE}",
            f"- {ANDROID_REPORT_EVIDENCE_REPORT_LIST_REFRESHED_LABEL}: {ANDROID_REPORT_EVIDENCE_REPORT_LIST_REFRESHED_VALUE}",
            f"- {ANDROID_REPORT_EVIDENCE_COPY_SOURCE_LABEL}: {ANDROID_REPORT_EVIDENCE_COPY_SOURCE_VALUE}",
            f"- {ANDROID_REPORT_EVIDENCE_ON_DEVICE_DIRECTORY_LABEL}: {ANDROID_REPORT_EVIDENCE_ON_DEVICE_DIRECTORY_VALUE}",
            f"- {ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL}: {report_file_name}",
            f"- {ANDROID_REPORT_EVIDENCE_COPIED_COMMANDS_AVAILABLE_LABEL}: yes",
            f"- {ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_LABEL}: {ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT}",
            "",
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
            "",
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START,
            *_host_command_lines(
                config.application_id,
                config.branch,
                config.commit,
                report_file_name,
                pulled_report_path,
                analysis_output_dir,
                str(config.output_path),
            ),
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END,
            "",
            ANDROID_REPORT_EVIDENCE_HOST_OUTPUTS_HEADING,
            "",
            f"- {ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL}: {pulled_report_path}",
            f"- {ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL}: {analysis_output_dir}",
            f"- {ANDROID_REPORT_EVIDENCE_ANALYZER_EXIT_CODE_LABEL}: {analyzer_exit_code}",
            f"- {ANDROID_REPORT_EVIDENCE_GATE_STATUS_LABEL}: {gate_status or 'UNKNOWN'}",
            "",
            "Paste the status block, summary tables, report field check, and identity",
            f"checklist from `{ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME}`. "
            "Keep exactly one",
            "`### <reportId>` heading under `Report Field Check`, matching this",
            "selected report:",
            "",
            gate_markdown,
            "",
            ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
            "",
            f"- {ANDROID_REPORT_EVIDENCE_PASS_FAIL_LABEL}: "
            f"{ANDROID_REPORT_EVIDENCE_PASS_RESULT if gate_passed else ANDROID_REPORT_EVIDENCE_FAIL_RESULT}",
            f"- {ANDROID_REPORT_EVIDENCE_FAILURE_CATEGORY_LABEL}: "
            f"{ANDROID_REPORT_EVIDENCE_NO_FAILURE_CATEGORY if gate_passed else ANDROID_REPORT_EVIDENCE_GATE_FAILURE_CATEGORY}",
            "- Notes: Draft generated by `tool/build_android_report_evidence.py`; "
            "review real-device context before closing the goal.",
            "",
            "## Evidence Validator",
            "",
            "After this file is reviewed, run:",
            "",
            "```bash",
            f"{ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND} "
            f"{ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT} "
            f"{shlex.quote(str(config.output_path))}",
            "```",
            "",
        ]
    )


def write_evidence_draft(config: EvidenceDraftConfig) -> None:
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(build_evidence_markdown(config), encoding="utf-8")


def _validate_run_context(config: EvidenceDraftConfig) -> None:
    _validate_context_value(ANDROID_REPORT_EVIDENCE_DATE_LABEL, config.run_date)
    _validate_context_value(ANDROID_REPORT_EVIDENCE_BRANCH_LABEL, config.branch)
    _validate_context_value(ANDROID_REPORT_EVIDENCE_COMMIT_LABEL, config.commit)
    _validate_context_value(
        ANDROID_REPORT_EVIDENCE_APP_VARIANT_LABEL,
        config.app_variant,
    )
    _validate_context_value(
        ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL,
        config.application_id,
    )
    if config.app_used not in ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES:
        raise EvidenceDraftError(
            f"expected {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL} to be "
            f"{' or '.join(ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES)}."
        )


def _validate_context_value(label: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise EvidenceDraftError(f"expected non-empty {label}.")
    if _contains_placeholder_text(value):
        raise EvidenceDraftError(f"expected {label} without placeholders.")


def _contains_placeholder_text(value: str) -> bool:
    return "..." in value or "<" in value or ">" in value


def _load_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text_file(path, "report"))
    except json.JSONDecodeError as error:
        raise EvidenceDraftError(f"invalid report JSON: {error}") from error

    if isinstance(payload, list):
        raise EvidenceDraftError(
            "expected a single V1 report JSON object, got a JSON array."
        )
    if not isinstance(payload, dict):
        raise EvidenceDraftError(
            "expected a single V1 report JSON object."
        )
    _validate_report_payload(payload)
    return payload


def _read_text_file(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise EvidenceDraftError(f"unable to read {label}: {path}") from error


def _validate_report_payload(report: dict[str, Any]) -> None:
    schema_name = report.get("schemaName")
    schema_version = report.get("schemaVersion")
    report_id = report.get("reportId")
    source = report.get("source")
    generated_at = report.get("generatedAt")
    metadata = report.get("metadata")
    decision = report.get("decision")
    if schema_name != PERFORMANCE_REPORT_SCHEMA_NAME:
        raise EvidenceDraftError(
            "expected schemaName "
            f"{PERFORMANCE_REPORT_SCHEMA_NAME!r}, got {schema_name!r}."
        )
    if type(schema_version) is not int or schema_version != 1:
        raise EvidenceDraftError(
            "expected integer schemaVersion 1, got "
            f"{schema_version!r}."
        )
    if not isinstance(report_id, str) or not report_id.strip():
        raise EvidenceDraftError("expected non-empty string reportId.")
    if not isinstance(source, str) or not source.strip():
        raise EvidenceDraftError("expected non-empty string source.")
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise EvidenceDraftError("expected non-empty string generatedAt.")
    generated_at_timestamp = _parse_iso_datetime(generated_at)
    if (
        generated_at_timestamp is None
        or generated_at_timestamp.tzinfo is None
        or generated_at_timestamp.utcoffset()
        != timezone.utc.utcoffset(generated_at_timestamp)
    ):
        raise EvidenceDraftError(
            "expected generatedAt to be UTC ISO-8601 timestamp."
        )
    if not isinstance(metadata, dict):
        raise EvidenceDraftError("expected metadata object.")
    service_session_id = metadata.get("serviceSessionId")
    report_sequence = metadata.get("reportSequence")
    if not isinstance(service_session_id, str) or not service_session_id.strip():
        raise EvidenceDraftError(
            "expected non-empty string metadata.serviceSessionId."
        )
    if type(report_sequence) is not int or report_sequence <= 0:
        raise EvidenceDraftError(
            "expected positive integer metadata.reportSequence, got "
            f"{report_sequence!r}."
        )
    expected_report_id = f"{service_session_id}-report-{report_sequence}"
    if report_id != expected_report_id:
        raise EvidenceDraftError(
            "expected reportId to match metadata.serviceSessionId and "
            f"metadata.reportSequence: {expected_report_id!r}, got {report_id!r}."
        )
    if not isinstance(decision, dict):
        raise EvidenceDraftError("expected decision object.")
    decided_at = decision.get("decidedAt")
    if not isinstance(decided_at, str) or not decided_at.strip():
        raise EvidenceDraftError("expected non-empty string decision.decidedAt.")
    decided_at_timestamp = _parse_iso_datetime(decided_at)
    if decided_at_timestamp is None:
        raise EvidenceDraftError(
            "expected decision.decidedAt to be ISO-8601 timestamp."
        )
    if (
        decided_at_timestamp.tzinfo is not None
        and decided_at_timestamp.utcoffset() is not None
        and generated_at_timestamp < decided_at_timestamp
    ):
        raise EvidenceDraftError(
            "expected generatedAt to be at or after decision.decidedAt."
        )
    if not isinstance(decision.get("tier"), str) or not decision.get("tier", "").strip():
        raise EvidenceDraftError("expected non-empty string decision.tier.")
    if (
        not isinstance(decision.get("confidence"), str)
        or not decision.get("confidence", "").strip()
    ):
        raise EvidenceDraftError("expected non-empty string decision.confidence.")
    runtime = decision.get("runtimeObservation")
    if not isinstance(runtime, dict):
        raise EvidenceDraftError("expected decision.runtimeObservation object.")
    if not isinstance(runtime.get("status"), str) or not runtime.get("status", "").strip():
        raise EvidenceDraftError(
            "expected non-empty string decision.runtimeObservation.status."
        )
    device_signals = decision.get("deviceSignals")
    if not isinstance(device_signals, dict):
        raise EvidenceDraftError("expected decision.deviceSignals object.")
    _validate_android_device_signals(device_signals)


def _parse_iso_datetime(value: str) -> datetime | None:
    text = value.strip()
    if not text or "T" not in text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _validate_android_device_signals(device_signals: dict[str, Any]) -> None:
    for label in [
        "platform",
        "deviceModel",
        "osVersion",
        "memoryPressureState",
    ]:
        value = device_signals.get(label)
        if not isinstance(value, str) or not value.strip():
            raise EvidenceDraftError(
                f"expected non-empty string decision.deviceSignals.{label}."
            )
    platform = device_signals.get("platform")
    if platform != "android":
        raise EvidenceDraftError(
            "expected decision.deviceSignals.platform to be 'android', "
            f"got {platform!r}."
        )
    for label in ["totalRamBytes", "sdkInt", "memoryPressureLevel"]:
        value = device_signals.get(label)
        if type(value) is not int:
            raise EvidenceDraftError(
                f"expected integer decision.deviceSignals.{label}, got {value!r}."
            )
    if device_signals["totalRamBytes"] <= 0:
        raise EvidenceDraftError(
            "expected decision.deviceSignals.totalRamBytes to be greater than 0."
        )
    if device_signals["sdkInt"] <= 0:
        raise EvidenceDraftError(
            "expected decision.deviceSignals.sdkInt to be greater than 0."
        )
    for label in ["isLowRamDevice", "isLowPowerModeEnabled"]:
        value = device_signals.get(label)
        if type(value) is not bool:
            raise EvidenceDraftError(
                f"expected boolean decision.deviceSignals.{label}, got {value!r}."
            )
    sdk_int = device_signals["sdkInt"]
    if sdk_int >= 29:
        thermal_state = device_signals.get("thermalState")
        thermal_state_level = device_signals.get("thermalStateLevel")
        if not isinstance(thermal_state, str) or not thermal_state.strip():
            raise EvidenceDraftError(
                "expected non-empty string decision.deviceSignals.thermalState "
                f"for Android SDK {sdk_int}."
            )
        if type(thermal_state_level) is not int:
            raise EvidenceDraftError(
                "expected integer decision.deviceSignals.thermalStateLevel "
                f"for Android SDK {sdk_int}, got {thermal_state_level!r}."
            )


def _validate_gate_markdown_matches_report(
    gate_markdown: str,
    report: dict[str, Any],
    report_path: Path,
) -> None:
    report_id = str(report["reportId"]).strip()
    gate_summary_fields = _gate_summary_field_names(gate_markdown)
    if gate_summary_fields != ANDROID_REPORT_GATE_SUMMARY_FIELDS:
        raise EvidenceDraftError(
            "expected android_report_gate.md Gate Summary fields to match "
            f"{ANDROID_REPORT_GATE_SUMMARY_FIELDS!r}, got {gate_summary_fields!r}."
        )

    gate_summary = _gate_summary_values(gate_markdown)
    for key, expected in ANDROID_REPORT_GATE_SINGLE_REPORT_SUMMARY_VALUES.items():
        actual = gate_summary.get(key)
        if actual != expected:
            raise EvidenceDraftError(
                "expected android_report_gate.md Gate Summary "
                f"{key}={expected}, got {actual!r}."
            )

    expected_header_labels = [
        label for label, _summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
    ]
    header_labels = _gate_header_labels(gate_markdown)
    if header_labels != expected_header_labels:
        raise EvidenceDraftError(
            "expected android_report_gate.md header fields to match "
            f"{expected_header_labels!r}, got {header_labels!r}."
        )

    header_values = _gate_header_values(gate_markdown)
    for label, expected in ANDROID_REPORT_GATE_SINGLE_REPORT_HEADER_VALUES.items():
        actual = header_values.get(label)
        if actual != expected:
            raise EvidenceDraftError(
                "expected android_report_gate.md header "
                f"{label}={expected}, got {actual!r}."
            )
    check_lines = [
        line.strip()
        for line in _section_lines(gate_markdown, ANDROID_REPORT_GATE_CHECKS_HEADING)
        if line.strip()
    ]
    if not check_lines:
        raise EvidenceDraftError(
            "expected android_report_gate.md Checks section."
        )
    if check_lines != ANDROID_REPORT_GATE_CHECK_LINES:
        raise EvidenceDraftError(
            "expected android_report_gate.md Checks section to match analyzer "
            "gate checklist."
        )
    issue_lines = [
        line.strip()
        for line in _section_lines(gate_markdown, ANDROID_REPORT_GATE_ISSUES_HEADING)
        if line.strip()
    ]
    if issue_lines != [ANDROID_REPORT_GATE_NO_ISSUES_LINE]:
        raise EvidenceDraftError(
            "expected android_report_gate.md Issues section to be '- None.', "
            f"got {issue_lines!r}."
        )

    headings = _section_subheadings(gate_markdown, ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING)
    if headings != [report_id]:
        raise EvidenceDraftError(
            "expected android_report_gate.md Report Field Check heading "
            f"for {report_id!r}, got {headings!r}."
        )
    field_check_labels = _section_field_labels(
        gate_markdown,
        ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
    )
    if field_check_labels != ANDROID_REPORT_GATE_FIELD_CHECK_LABELS:
        raise EvidenceDraftError(
            "expected android_report_gate.md Report Field Check labels to match "
            f"{ANDROID_REPORT_GATE_FIELD_CHECK_LABELS!r}, got "
            f"{field_check_labels!r}."
        )
    field_report_id = _section_line_value(
        gate_markdown,
        ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
        "`reportId`",
    )
    if field_report_id != report_id:
        raise EvidenceDraftError(
            "expected android_report_gate.md Report Field Check reportId "
            f"{report_id!r}, got {field_report_id!r}."
        )
    expected_field_values = dict(
        zip(
            ANDROID_REPORT_GATE_FIELD_CHECK_LABELS,
            [
                _value_at(report, "schemaName"),
                _gate_text(_raw_value_at(report, "schemaVersion")),
                report_id,
                _value_at(report, "generatedAt"),
                _value_at(report, "source"),
                _value_at(report, "metadata", "serviceSessionId"),
                _gate_text(_raw_value_at(report, "metadata", "reportSequence")),
                _value_at(report, "decision", "tier"),
                _value_at(report, "decision", "confidence"),
                _value_at(report, "decision", "decidedAt"),
                _value_at(report, "decision", "deviceSignals", "platform"),
                _value_at(report, "decision", "deviceSignals", "deviceModel"),
                _value_at(report, "decision", "deviceSignals", "osVersion"),
                _gate_text(
                    _raw_value_at(report, "decision", "deviceSignals", "totalRamBytes"),
                ),
                _gate_text(
                    _raw_value_at(report, "decision", "deviceSignals", "isLowRamDevice"),
                ),
                _gate_text(_raw_value_at(report, "decision", "deviceSignals", "sdkInt")),
                _gate_text(
                    _raw_value_at(report, "decision", "deviceSignals", "thermalState"),
                ),
                _gate_text(
                    _raw_value_at(
                        report,
                        "decision",
                        "deviceSignals",
                        "thermalStateLevel",
                    ),
                ),
                _gate_text(
                    _raw_value_at(
                        report,
                        "decision",
                        "deviceSignals",
                        "isLowPowerModeEnabled",
                    ),
                ),
                _value_at(report, "decision", "deviceSignals", "memoryPressureState"),
                _gate_text(
                    _raw_value_at(
                        report,
                        "decision",
                        "deviceSignals",
                        "memoryPressureLevel",
                    ),
                ),
                _value_at(report, "decision", "runtimeObservation", "status"),
            ],
        ),
    )
    for label, expected in expected_field_values.items():
        actual = _section_line_value(
            gate_markdown,
            ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
            label,
        )
        if actual is None:
            raise EvidenceDraftError(
                "expected android_report_gate.md Report Field Check "
                f"{label} line."
            )
        if actual != expected:
            raise EvidenceDraftError(
                "expected android_report_gate.md Report Field Check "
                f"{label} {expected!r}, got {actual!r}."
            )
    performance_columns = ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS
    performance_headers = _table_headers(
        gate_markdown,
        ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    )
    if performance_headers != performance_columns:
        raise EvidenceDraftError(
            "expected android_report_gate.md Performance Reports columns to "
            f"match {performance_columns!r}, got {performance_headers!r}."
        )
    performance_records = _table_records(gate_markdown, ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING)
    if len(performance_records) != 1:
        raise EvidenceDraftError(
            "expected android_report_gate.md Performance Reports table to have "
            f"exactly one data row, got {len(performance_records)}."
        )
    performance_record = performance_records[0]
    table_report_id = performance_record.get(performance_columns[1])
    if table_report_id != report_id:
        raise EvidenceDraftError(
            "expected android_report_gate.md Performance Reports Report ID "
            f"{report_id!r}, got {table_report_id!r}."
        )
    source = performance_record.get(performance_columns[0])
    if source is None:
        raise EvidenceDraftError(
            "expected android_report_gate.md Performance Reports Source column."
        )
    if not _source_matches_pulled_report(
        source,
        str(report_path),
        report_path.name,
    ):
        raise EvidenceDraftError(
            "expected android_report_gate.md Performance Reports Source to match "
            f"{str(report_path)!r}, got {source!r}."
        )
    expected_performance_values = {
        performance_columns[2]: _value_at(report, "source"),
        performance_columns[3]: _value_at(report, "metadata", "serviceSessionId"),
        performance_columns[4]: _value_at(report, "metadata", "reportSequence"),
        performance_columns[5]: _value_at(report, "decision", "tier"),
        performance_columns[6]: _value_at(report, "decision", "confidence"),
        performance_columns[7]: _value_at(
            report,
            "decision",
            "runtimeObservation",
            "status",
        ),
        performance_columns[8]: _value_at(report, "generatedAt"),
        performance_columns[9]: _value_at(report, "decision", "decidedAt"),
    }
    for column, expected in expected_performance_values.items():
        actual = performance_record.get(column)
        if actual is None:
            raise EvidenceDraftError(
                "expected android_report_gate.md Performance Reports "
                f"{column} column."
            )
        if actual != expected:
            raise EvidenceDraftError(
                "expected android_report_gate.md Performance Reports "
                f"{column} {expected!r}, got {actual!r}."
            )
    signal_columns = ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS
    signal_headers = _table_headers(
        gate_markdown,
        ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
    )
    if signal_headers != signal_columns:
        raise EvidenceDraftError(
            "expected android_report_gate.md Android Signals columns to match "
            f"{signal_columns!r}, got {signal_headers!r}."
        )
    signal_records = _table_records(gate_markdown, ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING)
    if len(signal_records) != 1:
        raise EvidenceDraftError(
            "expected android_report_gate.md Android Signals table to have "
            f"exactly one data row, got {len(signal_records)}."
        )
    signal_record = signal_records[0]
    expected_signal_values = {
        signal_columns[0]: report_id,
        signal_columns[1]: _gate_text(
            _value_at(report, "decision", "deviceSignals", "platform"),
        ),
        signal_columns[2]: _gate_text(
            _value_at(report, "decision", "deviceSignals", "deviceModel"),
        ),
        signal_columns[3]: _gate_text(
            _value_at(report, "decision", "deviceSignals", "osVersion"),
        ),
        signal_columns[4]: _gate_text(
            _raw_value_at(report, "decision", "deviceSignals", "sdkInt"),
        ),
        signal_columns[5]: _gate_text(
            _raw_value_at(report, "decision", "deviceSignals", "totalRamBytes"),
        ),
        signal_columns[6]: _gate_text(
            _raw_value_at(report, "decision", "deviceSignals", "isLowRamDevice"),
        ),
        signal_columns[7]: _gate_text(
            _raw_value_at(
                report,
                "decision",
                "deviceSignals",
                "isLowPowerModeEnabled",
            ),
        ),
        signal_columns[8]: _gate_text(
            _value_at(report, "decision", "deviceSignals", "memoryPressureState"),
        ),
        signal_columns[9]: _gate_text(
            _raw_value_at(report, "decision", "deviceSignals", "memoryPressureLevel"),
        ),
        signal_columns[10]: _gate_text(
            _value_at(report, "decision", "deviceSignals", "thermalState"),
        ),
        signal_columns[11]: _gate_text(
            _raw_value_at(report, "decision", "deviceSignals", "thermalStateLevel"),
        ),
    }
    for column, expected in expected_signal_values.items():
        actual = signal_record.get(column)
        if actual is None:
            raise EvidenceDraftError(
                "expected android_report_gate.md Android Signals "
                f"{column} column."
            )
        if actual != expected:
            raise EvidenceDraftError(
                "expected android_report_gate.md Android Signals "
                f"{column} {expected!r}, got {actual!r}."
            )
    identity_labels = _section_field_labels(
        gate_markdown,
        ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
    )
    if identity_labels != IDENTITY_CHECKLIST_LABELS:
        raise EvidenceDraftError(
            "expected android_report_gate.md Identity And Gate Checklist labels "
            f"to match {IDENTITY_CHECKLIST_LABELS!r}, got {identity_labels!r}."
        )
    for label in IDENTITY_CHECKLIST_LABELS:
        actual = _section_line_value(
            gate_markdown,
            ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
            label,
        )
        if actual != "yes":
            raise EvidenceDraftError(
                "expected android_report_gate.md Identity And Gate Checklist "
                f"{label!r} to be yes, got {actual!r}."
            )


def _gate_summary_values(markdown: str) -> dict[str, str]:
    lines = _gate_summary_key_value_lines(markdown)
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _gate_summary_field_names(markdown: str) -> list[str]:
    fields: list[str] = []
    for line in _gate_summary_key_value_lines(markdown):
        stripped = line.strip()
        if "=" not in stripped:
            fields.append(stripped)
            continue
        field, _value = stripped.split("=", 1)
        fields.append(field.strip())
    return fields


def _gate_summary_key_value_lines(markdown: str) -> list[str]:
    lines = [
        line.strip()
        for line in _section_lines(markdown, ANDROID_REPORT_GATE_SUMMARY_HEADING)
        if line.strip()
    ]
    if len(lines) < 2:
        return []
    if lines[0] != ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START:
        return []
    if lines[-1] != ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END:
        return []
    if any(line.startswith("```") for line in lines[1:-1]):
        return []
    return lines[1:-1]


def _gate_header_values(markdown: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        values[key.strip()] = value.strip()
    return values


def _gate_header_labels(markdown: str) -> list[str]:
    labels: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        label, _value = stripped[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _section_line_value(markdown: str, heading: str, label: str) -> str | None:
    prefix = f"- {label}:"
    for line in _section_lines(markdown, heading):
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _section_field_labels(markdown: str, heading: str) -> list[str]:
    labels: list[str] = []
    for line in _section_lines(markdown, heading):
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        label, _value = stripped[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _table_headers(markdown: str, heading: str) -> list[str]:
    lines = _section_lines(markdown, heading)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            return _split_table_row(stripped)
    return []


def _table_records(markdown: str, heading: str) -> list[dict[str, str]]:
    lines = _section_lines(markdown, heading)
    table_lines = [line.strip() for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = _split_table_row(table_lines[0])
    records: list[dict[str, str]] = []
    for line in table_lines[2:]:
        if "..." in line:
            continue
        cells = _split_table_row(line)
        if not cells:
            continue
        records.append(
            {
                header: cells[index] if index < len(cells) else ""
                for index, header in enumerate(headers)
            },
        )
    return records


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _source_matches_pulled_report(
    source: str,
    pulled_report_path: str,
    report_file_name: str,
) -> bool:
    if host_path_basename(source) != report_file_name:
        return False
    normalized_source = _normalized_path_for_match(source)
    normalized_pulled = _normalized_path_for_match(pulled_report_path)
    return (
        normalized_source == normalized_pulled
        or normalized_source.endswith(f"/{normalized_pulled}")
    )


def _normalized_path_for_match(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _section_subheadings(markdown: str, heading: str) -> list[str]:
    headings: list[str] = []
    for line in _section_lines(markdown, heading):
        stripped = line.strip()
        if stripped.startswith("### "):
            headings.append(stripped[4:].strip())
    return headings


def _section_lines(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return []
    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        section.append(line)
    return section


def _dict_at(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def _value_at(payload: dict[str, Any], *keys: str) -> str:
    return _text(_raw_value_at(payload, *keys))


def _raw_value_at(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _gate_text(value: Any) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _gate_status(markdown: str) -> str:
    status_header_label = next(
        label
        for label, summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
        if summary_key == ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD
    )
    header_prefix = f"- {status_header_label}:"
    summary_prefix = f"{ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD}="
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith(header_prefix):
            return stripped[len(header_prefix):].strip()
        if stripped.startswith(summary_prefix):
            return stripped[len(summary_prefix):].strip()
    return ""


def _host_command_lines(
    application_id: str,
    branch: str,
    commit: str,
    report_file_name: str,
    pulled_report_path: str,
    analysis_output_dir: str,
    evidence_output_path: str,
) -> list[str]:
    gate_markdown_path = str(
        Path(analysis_output_dir) / ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME
    )
    report_dir = str(Path(pulled_report_path).parent)
    device_report_path = android_report_device_path(report_file_name)
    adb_list_prefix = host_command_argv_text(
        ANDROID_REPORT_EVIDENCE_ADB_LIST_ARGV_PREFIX,
    )
    adb_pull_prefix = host_command_argv_text(
        ANDROID_REPORT_EVIDENCE_ADB_PULL_ARGV_PREFIX,
    )
    gate_markdown_print_prefix = host_command_argv_text(
        ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_PRINT_ARGV_PREFIX,
    )
    host_dir_prepare_prefix = host_command_argv_text(
        ANDROID_REPORT_EVIDENCE_HOST_DIR_PREPARE_ARGV_PREFIX,
    )
    nonempty_report_check_prefix = host_command_argv_text(
        ANDROID_REPORT_EVIDENCE_NONEMPTY_REPORT_CHECK_ARGV_PREFIX,
    )
    return [
        ANDROID_REPORT_EVIDENCE_FAIL_FAST_START_COMMAND,
        f"{adb_list_prefix} {shlex.quote(application_id)} "
        f"{ANDROID_REPORT_EVIDENCE_ADB_LIST_COMMAND} "
        f"{shlex.quote(ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY)}",
        f"{host_dir_prepare_prefix} {shlex.quote(report_dir)}",
        f"{adb_pull_prefix} {shlex.quote(application_id)} "
        f"{ANDROID_REPORT_EVIDENCE_ADB_PULL_COMMAND} "
        f"{shlex.quote(device_report_path)} "
        f"{ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN} "
        f"{shlex.quote(pulled_report_path)}",
        f"{nonempty_report_check_prefix} {shlex.quote(pulled_report_path)}",
        ANDROID_REPORT_EVIDENCE_ALLOW_GATE_FAIL_COMMAND,
        f"{ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND} "
        f"{ANDROID_REPORT_EVIDENCE_ANALYZER_SCRIPT} "
        f"{shlex.quote(pulled_report_path)} "
        f"{ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION} "
        f"{shlex.quote(analysis_output_dir)} "
        f"{ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION}",
        ANDROID_REPORT_EVIDENCE_GATE_STATUS_CAPTURE_COMMAND,
        ANDROID_REPORT_EVIDENCE_FAIL_FAST_START_COMMAND,
        f"{gate_markdown_print_prefix} {shlex.quote(gate_markdown_path)}",
        ANDROID_REPORT_EVIDENCE_GATE_STATUS_CHECK_COMMAND,
        f"{ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND} "
        f"{ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT} "
        f"{shlex.quote(pulled_report_path)} "
        f"{ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION} "
        f"{shlex.quote(analysis_output_dir)} "
        f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} {shlex.quote(branch)} "
        f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} {shlex.quote(commit)} "
        f"{ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION} {shlex.quote(evidence_output_path)} "
        f"{ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION} {shlex.quote(application_id)}",
        f"{ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND} "
        f"{ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT} "
        f"{shlex.quote(evidence_output_path)}",
    ]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _ram_text(total_ram_bytes: Any) -> str:
    if total_ram_bytes is None:
        return ""
    return str(total_ram_bytes)


def _thermal_power_text(device_signals: dict[str, Any]) -> str:
    thermal = _text(device_signals.get("thermalState")) or "unknown thermal"
    low_power = _text(device_signals.get("isLowPowerModeEnabled")) or "unknown power"
    return f"{thermal} / low-power {low_power}"


def _git_value(command: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ""
    return result.stdout.strip()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a filled Android report-loop evidence draft from a pulled "
            f"report JSON and {ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME}."
        ),
    )
    parser.add_argument("report", type=Path, help="Pulled V1 Android report JSON.")
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION,
        type=Path,
        default=DEFAULT_ANALYSIS_OUTPUT_DIR,
        help=(
            "Analyzer output directory containing "
            f"{ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME}."
        ),
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_OPTION,
        type=Path,
        help=(
            f"Explicit {ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME} path. "
            "Defaults to <analysis-output-dir>/"
            f"{ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME}."
        ),
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
        type=Path,
        required=True,
        help="Evidence draft path.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_DATE_OPTION,
        default=date.today().isoformat(),
        help="Run date.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
        help="Git branch. Defaults to current branch.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
        help="Git commit. Defaults to current short commit.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_APP_USED_OPTION,
        default=ANDROID_REPORT_EVIDENCE_EXAMPLE_APP_USED,
        choices=ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES,
        help="App used during real-device validation.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_APP_VARIANT_OPTION,
        default=ANDROID_REPORT_EVIDENCE_DEFAULT_APP_VARIANT,
        help="App build variant.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
        required=True,
        help="Android application id.",
    )
    parser.add_argument(
        ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_OPTION,
        help="Human-observed Android version, for example 15. Defaults to deviceSignals.osVersion.",
    )
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> EvidenceDraftConfig:
    analysis_output_dir = args.analysis_output_dir
    gate_markdown_path = (
        args.gate_markdown
        or analysis_output_dir / ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME
    )
    branch = args.branch or _git_value(ANDROID_REPORT_EVIDENCE_GIT_BRANCH_COMMAND)
    commit = args.commit or _git_value(ANDROID_REPORT_EVIDENCE_GIT_COMMIT_COMMAND)
    if not branch:
        raise EvidenceDraftError(
            "unable to resolve git branch; pass "
            f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} explicitly."
        )
    if not commit:
        raise EvidenceDraftError(
            "unable to resolve git commit; pass "
            f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} explicitly."
        )
    return EvidenceDraftConfig(
        report_path=args.report,
        analysis_output_dir=analysis_output_dir,
        gate_markdown_path=gate_markdown_path,
        output_path=args.output,
        run_date=args.date,
        branch=branch,
        commit=commit,
        app_used=args.app_used,
        app_variant=args.app_variant,
        application_id=args.application_id,
        android_version=args.android_version,
    )


def main() -> int:
    try:
        config = config_from_args(parse_args())
        write_evidence_draft(config)
    except EvidenceDraftError as error:
        print(evidence_draft_line(ANDROID_REPORT_EVIDENCE_FAIL_STATUS))
        print(f"error: {error}")
        return 2
    print(evidence_draft_line(str(config.output_path)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

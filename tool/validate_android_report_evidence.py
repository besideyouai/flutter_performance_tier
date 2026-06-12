#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

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
    ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_LABEL,
    ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
    ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL,
    ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES,
    ANDROID_REPORT_EVIDENCE_APP_USED_PLACEHOLDER,
    ANDROID_REPORT_EVIDENCE_APP_SIDE_TRIGGER_HEADING,
    ANDROID_REPORT_EVIDENCE_APP_USED_LABEL,
    ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
    ANDROID_REPORT_EVIDENCE_BRANCH_LABEL,
    ANDROID_REPORT_EVIDENCE_COMMIT_LABEL,
    ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
    ANDROID_REPORT_EVIDENCE_COPIED_COMMANDS_AVAILABLE_LABEL,
    ANDROID_REPORT_EVIDENCE_CORE_CONTEXT_LABELS,
    ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT,
    ANDROID_REPORT_EVIDENCE_ALLOW_GATE_FAIL_COMMAND,
    ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY,
    ANDROID_REPORT_EVIDENCE_DEVICE_MODEL_LABEL,
    ANDROID_REPORT_EVIDENCE_FIELD_SECTIONS,
    ANDROID_REPORT_EVIDENCE_FAIL_STATUS,
    ANDROID_REPORT_EVIDENCE_FAIL_FAST_START_COMMAND,
    ANDROID_REPORT_EVIDENCE_FAILURE_CATEGORY_LABEL,
    ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_PRINT_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_GATE_STATUS_LABEL,
    ANDROID_REPORT_EVIDENCE_GATE_STATUS_CAPTURE_COMMAND,
    ANDROID_REPORT_EVIDENCE_GATE_STATUS_CHECK_ARGV,
    ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT,
    ANDROID_REPORT_EVIDENCE_HOST_COMMAND_STAGE_ORDER,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START,
    ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING,
    ANDROID_REPORT_EVIDENCE_HOST_OUTPUTS_HEADING,
    ANDROID_REPORT_EVIDENCE_HOST_DIR_PREPARE_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_NONEMPTY_REPORT_CHECK_ARGV_PREFIX,
    ANDROID_REPORT_EVIDENCE_NO_FAILURE_CATEGORY,
    ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
    ANDROID_REPORT_EVIDENCE_PASS_FAIL_LABEL,
    ANDROID_REPORT_EVIDENCE_PASS_RESULT,
    ANDROID_REPORT_EVIDENCE_PASS_STATUS,
    ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
    ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL,
    ANDROID_REPORT_EVIDENCE_REQUIRED_APP_TRIGGER_VALUES,
    ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS,
    ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
    ANDROID_REPORT_EVIDENCE_RUN_CONTEXT_HEADING,
    ANDROID_REPORT_EVIDENCE_SDK_INT_LABEL,
    ANDROID_REPORT_EVIDENCE_STAGE_ALLOW_GATE_FAIL,
    ANDROID_REPORT_EVIDENCE_STAGE_ANALYZER,
    ANDROID_REPORT_EVIDENCE_STAGE_BUILDER,
    ANDROID_REPORT_EVIDENCE_STAGE_FAIL_FAST_RESUME,
    ANDROID_REPORT_EVIDENCE_STAGE_FAIL_FAST_START,
    ANDROID_REPORT_EVIDENCE_STAGE_GATE_MARKDOWN_PRINT,
    ANDROID_REPORT_EVIDENCE_STAGE_GATE_STATUS_CAPTURE,
    ANDROID_REPORT_EVIDENCE_STAGE_GATE_STATUS_CHECK,
    ANDROID_REPORT_EVIDENCE_STAGE_LIST_REPORTS,
    ANDROID_REPORT_EVIDENCE_STAGE_NONEMPTY_CHECK,
    ANDROID_REPORT_EVIDENCE_STAGE_PREPARE_HOST_DIR,
    ANDROID_REPORT_EVIDENCE_STAGE_PULL,
    ANDROID_REPORT_EVIDENCE_STAGE_VALIDATOR,
    ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN,
    ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT,
    android_report_device_path,
    evidence_status_line,
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
    ANDROID_REPORT_GATE_PRESENT_FIELD_LABELS,
    ANDROID_REPORT_GATE_POSITIVE_SUMMARY_FIELDS,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START,
    ANDROID_REPORT_GATE_SUMMARY_FIELDS,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
    ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
    ANDROID_REPORT_GATE_PASS_SUMMARY_VALUES,
    ANDROID_REPORT_GATE_REQUIRED_FIELD_LABELS,
    ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_HEADING,
    IDENTITY_CHECKLIST_LABELS,
    PERFORMANCE_REPORT_SCHEMA_NAME,
)


@dataclass(frozen=True)
class EvidenceValidationResult:
    issues: list[str]

    @property
    def ok(self) -> bool:
        return not self.issues


def validate_evidence_path(path: Path) -> EvidenceValidationResult:
    return validate_evidence_text(path.read_text(encoding="utf-8"))


def validate_evidence_text(text: str) -> EvidenceValidationResult:
    issues: list[str] = []

    _validate_core_context(text, issues)
    _validate_report_file_path_context(text, issues)
    _validate_app_trigger(text, issues)
    _validate_host_commands(text, issues)
    _validate_host_outputs(text, issues)
    _validate_result(text, issues)
    _validate_gate_summary(text, issues)
    _validate_gate_header_summary_values(text, issues)
    _validate_gate_checks(text, issues)
    _validate_gate_issues(text, issues)
    _validate_summary_table_columns(text, issues)
    _validate_summary_tables(text, issues)
    _validate_single_report_scope(text, issues)
    _validate_gate_summary_table_counts(text, issues)
    _validate_performance_report_table_field_values(text, issues)
    _validate_performance_report_table_source(text, issues)
    _validate_android_signal_table_context_values(text, issues)
    _validate_report_fields(text, issues)
    _validate_report_field_check_scope(text, issues)
    _validate_report_field_check_labels(text, issues)
    _validate_report_field_contract_values(text, issues)
    _validate_identity_checklist(text, issues)

    return EvidenceValidationResult(issues)


def _validate_core_context(text: str, issues: list[str]) -> None:
    for label in ANDROID_REPORT_EVIDENCE_CORE_CONTEXT_LABELS:
        value = _evidence_line_value(text, label)
        if not _is_filled_value(value):
            issues.append(f"missing_or_placeholder: {label}")

    app_used = _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_APP_USED_LABEL)
    if app_used and " / " in app_used:
        issues.append(
            f"placeholder_choice: {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL} "
            f"must choose {' or '.join(ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES)}."
        )
    elif app_used and app_used not in ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES:
        issues.append(
            f"invalid_app_used: {ANDROID_REPORT_EVIDENCE_APP_USED_LABEL} "
            f"must be {' or '.join(ANDROID_REPORT_EVIDENCE_ALLOWED_APP_USED_VALUES)}."
        )

    report_file_name = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL,
    )
    if report_file_name and not is_safe_report_file_name(report_file_name.strip()):
        issues.append(
            "unsafe_report_file_name: Report file name must be a safe .json file name."
        )


def _validate_app_trigger(text: str, issues: list[str]) -> None:
    for label, expected in ANDROID_REPORT_EVIDENCE_REQUIRED_APP_TRIGGER_VALUES.items():
        actual = _evidence_line_value(text, label)
        if not _is_filled_app_trigger_value(actual):
            issues.append(f"missing_app_trigger_field: {label}")
        elif actual != expected:
            issue_key = _issue_key(label)
            issues.append(
                f"app_trigger_mismatch: {issue_key} expected {expected!r}, got {actual!r}."
            )

    copied_commands = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_COPIED_COMMANDS_AVAILABLE_LABEL,
    )
    if _normalized_yes_no(copied_commands) != "yes":
        issues.append(
            "host_commands_unavailable: copied commands must be available for a safe report."
        )


def _validate_report_file_path_context(text: str, issues: list[str]) -> None:
    report_file_name = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL,
    )
    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    if not _is_filled_value(report_file_name) or not _is_filled_value(pulled_report_path):
        return

    pulled_basename = host_path_basename(pulled_report_path)
    if pulled_basename != report_file_name:
        issues.append(
            "report_file_path_mismatch: expected Pulled report path basename "
            f"to be {report_file_name!r}, got {pulled_basename!r}."
        )


def _validate_host_commands(text: str, issues: list[str]) -> None:
    command_text = "\n".join(
        _section_lines(text, ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING),
    )
    if not command_text.strip():
        issues.append(
            f"missing_host_commands: {ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_HEADING} section is required."
        )
        return

    if _contains_placeholder(command_text):
        issues.append(
            "host_commands_placeholder: Host commands must not contain placeholders."
        )

    _validate_host_command_code_fence(command_text, issues)
    _validate_host_command_shell_syntax(command_text, issues)

    for snippet in ANDROID_REPORT_EVIDENCE_REQUIRED_HOST_COMMAND_SNIPPETS:
        if snippet not in command_text:
            issues.append(f"missing_host_command: {snippet}")

    _validate_host_command_context_values(text, command_text, issues)
    _validate_evidence_command_output_path(command_text, issues)
    _validate_host_command_allowed_lines(text, command_text, issues)
    _validate_host_command_order(text, command_text, issues)


def _validate_host_outputs(text: str, issues: list[str]) -> None:
    exit_code = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_ANALYZER_EXIT_CODE_LABEL,
    )
    if exit_code != "0":
        issues.append("analyzer_exit_code: expected Analyzer exit code to be 0.")

    gate_status = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_GATE_STATUS_LABEL,
    )
    if gate_status != ANDROID_REPORT_GATE_PASS_STATUS:
        issues.append(
            "gate_status: expected `android_report_gate.md` status to be "
            f"{ANDROID_REPORT_GATE_PASS_STATUS}."
        )


def _validate_host_command_context_values(
    text: str,
    command_text: str,
    issues: list[str],
) -> None:
    context_fields = [
        (ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL, "application_id", False),
        (ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL, "report_file_name", True),
        (ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL, "pulled_report_path", False),
        (
            ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL,
            "analyzer_output_directory",
            False,
        ),
    ]
    for label, issue_key, allow_path_basename in context_fields:
        value = _evidence_line_value(text, label)
        if not _is_filled_value(value):
            continue
        if not _command_contains_value(
            command_text,
            value,
            allow_path_basename=allow_path_basename,
        ):
            issues.append(f"host_command_context_mismatch: {issue_key}")

    _validate_adb_report_commands(text, command_text, issues)
    _validate_analysis_evidence_commands(text, command_text, issues)
    _validate_file_check_commands(text, command_text, issues)


def _validate_file_check_commands(
    text: str,
    command_text: str,
    issues: list[str],
) -> None:
    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    analysis_output_dir = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL,
    )
    application_id = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL,
    )
    branch = _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_BRANCH_LABEL)
    commit = _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_COMMIT_LABEL)
    if not _is_filled_value(pulled_report_path) or not _is_filled_value(
        analysis_output_dir,
    ):
        return

    gate_markdown_path = str(
        Path(analysis_output_dir) / ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME
    )
    host_report_dir = str(Path(pulled_report_path).parent)
    has_nonempty_check = False
    has_gate_markdown_print = False
    has_host_dir_prepare = False
    for argv in _host_command_argvs(command_text):
        if argv == [
            *ANDROID_REPORT_EVIDENCE_HOST_DIR_PREPARE_ARGV_PREFIX,
            host_report_dir,
        ]:
            has_host_dir_prepare = True
        if argv == [
            *ANDROID_REPORT_EVIDENCE_NONEMPTY_REPORT_CHECK_ARGV_PREFIX,
            pulled_report_path,
        ]:
            has_nonempty_check = True
        if argv == [
            *ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_PRINT_ARGV_PREFIX,
            gate_markdown_path,
        ]:
            has_gate_markdown_print = True

    expected_host_dir_prepare = host_command_argv_text(
        [*ANDROID_REPORT_EVIDENCE_HOST_DIR_PREPARE_ARGV_PREFIX, host_report_dir],
    )
    expected_nonempty_report_check = host_command_argv_text(
        [
            *ANDROID_REPORT_EVIDENCE_NONEMPTY_REPORT_CHECK_ARGV_PREFIX,
            pulled_report_path,
        ],
    )
    if not has_host_dir_prepare:
        issues.append(
            "host_command_prepare_dir_mismatch: expected "
            f"{expected_host_dir_prepare}."
        )
    if not has_nonempty_check:
        issues.append(
            "host_command_nonempty_check_mismatch: expected "
            f"{expected_nonempty_report_check}."
        )
    if not has_gate_markdown_print:
        issues.append(
            "host_command_gate_markdown_path_mismatch: expected "
            f"cat {gate_markdown_path!r}."
        )


def _validate_host_command_order(
    text: str,
    command_text: str,
    issues: list[str],
) -> None:
    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    analysis_output_dir = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL,
    )
    if not _is_filled_value(pulled_report_path) or not _is_filled_value(
        analysis_output_dir,
    ):
        return

    gate_markdown_path = str(
        Path(analysis_output_dir) / ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME
    )
    host_report_dir = str(Path(pulled_report_path).parent)
    stage_positions: dict[str, int] = {}
    for index, argv in enumerate(_host_command_argvs(command_text)):
        stage = _host_command_stage(
            argv,
            pulled_report_path=pulled_report_path,
            gate_markdown_path=gate_markdown_path,
            host_report_dir=host_report_dir,
            seen_stages=stage_positions,
        )
        if stage and stage not in stage_positions:
            stage_positions[stage] = index

    expected_order = ANDROID_REPORT_EVIDENCE_HOST_COMMAND_STAGE_ORDER
    missing_stages = [
        label for stage, label in expected_order if stage not in stage_positions
    ]
    if missing_stages:
        for label in missing_stages:
            issues.append(f"missing_host_command_stage: {label}")
        return

    first_stage, previous_label = expected_order[0]
    previous_position = stage_positions[first_stage]
    for stage, label in expected_order[1:]:
        position = stage_positions[stage]
        if previous_position >= position:
            issues.append(
                "host_command_order_mismatch: expected "
                f"{ANDROID_REPORT_EVIDENCE_HOST_COMMAND_ORDER_TEXT}; "
                f"got {label} before {previous_label}."
            )
            return
        previous_label = label
        previous_position = position


def _validate_host_command_allowed_lines(
    text: str,
    command_text: str,
    issues: list[str],
) -> None:
    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    analysis_output_dir = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL,
    )
    if not _is_filled_value(pulled_report_path) or not _is_filled_value(
        analysis_output_dir,
    ):
        return

    gate_markdown_path = str(
        Path(analysis_output_dir) / ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME
    )
    host_report_dir = str(Path(pulled_report_path).parent)
    seen_stages: dict[str, int] = {}
    for index, argv in enumerate(_host_command_argvs(command_text)):
        stage = _host_command_stage(
            argv,
            pulled_report_path=pulled_report_path,
            gate_markdown_path=gate_markdown_path,
            host_report_dir=host_report_dir,
            seen_stages=seen_stages,
        )
        command = " ".join(argv)
        if stage is None:
            issues.append(f"unexpected_host_command: {command}")
            continue
        if stage in seen_stages:
            issues.append(f"duplicate_host_command_stage: {stage}")
            continue
        seen_stages[stage] = index


def _validate_host_command_shell_syntax(
    command_text: str,
    issues: list[str],
) -> None:
    for line in command_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue
        try:
            shlex.split(stripped)
        except ValueError as error:
            issues.append(f"malformed_host_command: {stripped} ({error})")


def _validate_host_command_code_fence(
    command_text: str,
    issues: list[str],
) -> None:
    lines = [line.strip() for line in command_text.splitlines() if line.strip()]
    fence_lines = [line for line in lines if line.startswith("```")]
    if (
        not lines
        or lines[0] != ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START
        or lines[-1] != ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END
        or fence_lines
        != [
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_START,
            ANDROID_REPORT_EVIDENCE_HOST_COMMANDS_CODE_FENCE_END,
        ]
    ):
        issues.append(
            "host_commands_fence_mismatch: expected ## Host Commands Run "
            "to contain exactly one bash fenced command block."
        )


def _host_command_stage(
    argv: list[str],
    *,
    pulled_report_path: str,
    gate_markdown_path: str,
    host_report_dir: str,
    seen_stages: dict[str, int],
) -> str | None:
    if argv == shlex.split(ANDROID_REPORT_EVIDENCE_FAIL_FAST_START_COMMAND):
        if ANDROID_REPORT_EVIDENCE_STAGE_FAIL_FAST_START not in seen_stages:
            return ANDROID_REPORT_EVIDENCE_STAGE_FAIL_FAST_START
        if (
            ANDROID_REPORT_EVIDENCE_STAGE_GATE_STATUS_CAPTURE in seen_stages
            and ANDROID_REPORT_EVIDENCE_STAGE_FAIL_FAST_RESUME not in seen_stages
        ):
            return ANDROID_REPORT_EVIDENCE_STAGE_FAIL_FAST_RESUME
        return None
    if argv == shlex.split(ANDROID_REPORT_EVIDENCE_ALLOW_GATE_FAIL_COMMAND):
        return ANDROID_REPORT_EVIDENCE_STAGE_ALLOW_GATE_FAIL
    if argv == [ANDROID_REPORT_EVIDENCE_GATE_STATUS_CAPTURE_COMMAND]:
        return ANDROID_REPORT_EVIDENCE_STAGE_GATE_STATUS_CAPTURE
    if _is_adb_report_list_command(argv):
        return ANDROID_REPORT_EVIDENCE_STAGE_LIST_REPORTS
    if argv == [
        *ANDROID_REPORT_EVIDENCE_HOST_DIR_PREPARE_ARGV_PREFIX,
        host_report_dir,
    ]:
        return ANDROID_REPORT_EVIDENCE_STAGE_PREPARE_HOST_DIR
    if _is_adb_report_pull_command(argv):
        return ANDROID_REPORT_EVIDENCE_STAGE_PULL
    if argv == [
        *ANDROID_REPORT_EVIDENCE_NONEMPTY_REPORT_CHECK_ARGV_PREFIX,
        pulled_report_path,
    ]:
        return ANDROID_REPORT_EVIDENCE_STAGE_NONEMPTY_CHECK
    if _is_python_script_argv(argv, ANDROID_REPORT_EVIDENCE_ANALYZER_SCRIPT):
        return ANDROID_REPORT_EVIDENCE_STAGE_ANALYZER
    if argv == [
        *ANDROID_REPORT_EVIDENCE_GATE_MARKDOWN_PRINT_ARGV_PREFIX,
        gate_markdown_path,
    ]:
        return ANDROID_REPORT_EVIDENCE_STAGE_GATE_MARKDOWN_PRINT
    if argv == ANDROID_REPORT_EVIDENCE_GATE_STATUS_CHECK_ARGV:
        return ANDROID_REPORT_EVIDENCE_STAGE_GATE_STATUS_CHECK
    if _is_python_script_argv(argv, ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT):
        return ANDROID_REPORT_EVIDENCE_STAGE_BUILDER
    if _is_python_script_argv(argv, ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT):
        return ANDROID_REPORT_EVIDENCE_STAGE_VALIDATOR
    return None


def _validate_analysis_evidence_commands(
    text: str,
    command_text: str,
    issues: list[str],
) -> None:
    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    analysis_output_dir = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_ANALYZER_OUTPUT_DIRECTORY_LABEL,
    )
    application_id = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL,
    )
    branch = _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_BRANCH_LABEL)
    commit = _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_COMMIT_LABEL)
    if not _is_filled_value(pulled_report_path) or not _is_filled_value(
        analysis_output_dir,
    ):
        return

    analyzer = _python_script_argv(
        command_text,
        ANDROID_REPORT_EVIDENCE_ANALYZER_SCRIPT,
    )
    if analyzer is None:
        issues.append(
            f"missing_host_command: {ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND} "
            f"{ANDROID_REPORT_EVIDENCE_ANALYZER_SCRIPT}"
        )
    else:
        analyzer_input = _positional_after_script_arg(analyzer)
        if analyzer_input != pulled_report_path:
            issues.append(
                "host_command_analyzer_input_mismatch: expected "
                f"{pulled_report_path!r}, got {analyzer_input!r}."
            )
        analyzer_output = _argv_option_value(
            analyzer,
            ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
        )
        if analyzer_output != analysis_output_dir:
            issues.append(
                "host_command_analyzer_output_mismatch: expected "
                f"{analysis_output_dir!r}, got {analyzer_output!r}."
            )
        if ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION not in analyzer:
            issues.append(
                "host_command_analyzer_gate_missing: expected "
                f"{ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION}."
            )
        expected_analyzer = _expected_analyzer_argv(
            pulled_report_path,
            analysis_output_dir,
        )
        if analyzer != expected_analyzer:
            issues.append(
                "host_command_analyzer_structure_mismatch: expected "
                f"{host_command_argv_text(expected_analyzer)}."
            )

    builder = _python_script_argv(
        command_text,
        ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT,
    )
    if builder is None:
        issues.append(
            f"missing_host_command: {ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND} "
            f"{ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT}"
        )
    else:
        builder_input = _positional_after_script_arg(builder)
        if builder_input != pulled_report_path:
            issues.append(
                "host_command_builder_input_mismatch: expected "
                f"{pulled_report_path!r}, got {builder_input!r}."
            )
        builder_analysis_output = _argv_option_value(
            builder,
            ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION,
        )
        if builder_analysis_output != analysis_output_dir:
            issues.append(
                "host_command_builder_analysis_output_mismatch: expected "
                f"{analysis_output_dir!r}, got {builder_analysis_output!r}."
            )
        builder_application_id = _argv_option_value(
            builder,
            ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
        )
        if (
            _is_filled_value(application_id)
            and builder_application_id != application_id
        ):
            issues.append(
                "host_command_builder_application_id_mismatch: expected "
                f"{application_id!r}, got {builder_application_id!r}."
            )
        builder_branch = _argv_option_value(
            builder,
            ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
        )
        builder_commit = _argv_option_value(
            builder,
            ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
        )
        has_explicit_branch = builder_branch is not None
        has_explicit_commit = builder_commit is not None
        context_has_git = _is_filled_value(branch) and _is_filled_value(commit)
        if has_explicit_branch != has_explicit_commit:
            issues.append(
                "host_command_builder_git_context_partial: expected "
                f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} and "
                f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} to be provided together."
            )
        elif context_has_git and not has_explicit_branch:
            issues.append(
                "host_command_builder_git_context_missing: expected "
                f"{ANDROID_REPORT_EVIDENCE_BRANCH_OPTION} and "
                f"{ANDROID_REPORT_EVIDENCE_COMMIT_OPTION} to match Run Context."
            )
        if has_explicit_branch and has_explicit_commit:
            if _is_filled_value(branch) and builder_branch != branch:
                issues.append(
                    "host_command_builder_branch_mismatch: expected "
                    f"{branch!r}, got {builder_branch!r}."
                )
            if _is_filled_value(commit) and builder_commit != commit:
                issues.append(
                    "host_command_builder_commit_mismatch: expected "
                    f"{commit!r}, got {builder_commit!r}."
                )
        builder_output = _argv_option_value(
            builder,
            ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
        )
        if not _is_filled_value(builder_output):
            issues.append(
                "host_command_builder_output_missing: expected "
                f"{ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION}."
            )
        elif _is_filled_value(application_id):
            expected_builder = _expected_builder_argv(
                pulled_report_path,
                analysis_output_dir,
                builder_output,
                application_id,
                branch if has_explicit_branch and has_explicit_commit else None,
                commit if has_explicit_branch and has_explicit_commit else None,
            )
            if builder != expected_builder:
                issues.append(
                    "host_command_builder_structure_mismatch: expected "
                    f"{host_command_argv_text(expected_builder)}."
                )


def _expected_analyzer_argv(
    pulled_report_path: str,
    analysis_output_dir: str,
) -> list[str]:
    return [
        ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
        ANDROID_REPORT_EVIDENCE_ANALYZER_SCRIPT,
        pulled_report_path,
        ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
        analysis_output_dir,
        ANDROID_REPORT_EVIDENCE_ANALYZER_GATE_OPTION,
    ]


def _expected_builder_argv(
    pulled_report_path: str,
    analysis_output_dir: str,
    evidence_output_path: str,
    application_id: str,
    branch: str | None = None,
    commit: str | None = None,
) -> list[str]:
    argv = [
        ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
        ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT,
        pulled_report_path,
        ANDROID_REPORT_EVIDENCE_ANALYSIS_OUTPUT_DIR_OPTION,
        analysis_output_dir,
    ]
    if branch is not None and commit is not None:
        argv.extend(
            [
                ANDROID_REPORT_EVIDENCE_BRANCH_OPTION,
                branch,
                ANDROID_REPORT_EVIDENCE_COMMIT_OPTION,
                commit,
            ],
        )
    argv.extend(
        [
            ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
            evidence_output_path,
            ANDROID_REPORT_EVIDENCE_APPLICATION_ID_OPTION,
            application_id,
        ],
    )
    return argv


def _expected_validator_argv(evidence_path: str) -> list[str]:
    return [
        ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND,
        ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT,
        evidence_path,
    ]


def _validate_adb_report_commands(
    text: str,
    command_text: str,
    issues: list[str],
) -> None:
    application_id = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_APPLICATION_ID_LABEL,
    )
    report_file_name = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL,
    )
    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    if (
        not _is_filled_value(application_id)
        or not _is_filled_value(report_file_name)
        or not _is_filled_value(pulled_report_path)
    ):
        return

    expected_device_report_path = android_report_device_path(report_file_name)
    for argv in _host_command_argvs(command_text):
        if _is_adb_report_list_command(argv):
            _validate_adb_run_as_application_id(
                argv,
                application_id,
                "list",
                issues,
            )
            expected_list_argv = _expected_adb_report_list_argv(application_id)
            if argv != expected_list_argv:
                issues.append(
                    "host_command_adb_list_structure_mismatch: expected "
                    f"{host_command_argv_text(expected_list_argv)}."
                )
        if _is_adb_report_pull_command(argv):
            _validate_adb_run_as_application_id(
                argv,
                application_id,
                "pull",
                issues,
            )
            device_path = _token_after(argv, ANDROID_REPORT_EVIDENCE_ADB_PULL_COMMAND)
            if device_path != expected_device_report_path:
                issues.append(
                    "host_command_device_report_mismatch: expected "
                    f"{expected_device_report_path!r}, got {device_path!r}."
                )
            redirected_path = _token_after(
                argv,
                ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN,
            )
            if redirected_path != pulled_report_path:
                issues.append(
                    "host_command_pulled_report_mismatch: expected "
                    f"{pulled_report_path!r}, got {redirected_path!r}."
                )
            expected_pull_argv = _expected_adb_report_pull_argv(
                application_id,
                expected_device_report_path,
                pulled_report_path,
            )
            if argv != expected_pull_argv:
                issues.append(
                    "host_command_adb_pull_structure_mismatch: expected "
                    f"{host_command_argv_text(expected_pull_argv)}."
                )


def _expected_adb_report_list_argv(application_id: str) -> list[str]:
    return [
        *ANDROID_REPORT_EVIDENCE_ADB_LIST_ARGV_PREFIX,
        application_id,
        ANDROID_REPORT_EVIDENCE_ADB_LIST_COMMAND,
        ANDROID_REPORT_EVIDENCE_DEVICE_REPORT_DIRECTORY,
    ]


def _expected_adb_report_pull_argv(
    application_id: str,
    device_report_path: str,
    pulled_report_path: str,
) -> list[str]:
    return [
        *ANDROID_REPORT_EVIDENCE_ADB_PULL_ARGV_PREFIX,
        application_id,
        ANDROID_REPORT_EVIDENCE_ADB_PULL_COMMAND,
        device_report_path,
        ANDROID_REPORT_EVIDENCE_STDOUT_REDIRECT_TOKEN,
        pulled_report_path,
    ]


def _is_adb_report_list_command(argv: list[str]) -> bool:
    return (
        len(argv) >= 6
        and argv[:3] == ANDROID_REPORT_EVIDENCE_ADB_LIST_ARGV_PREFIX
        and ANDROID_REPORT_EVIDENCE_ADB_LIST_COMMAND in argv
    )


def _is_adb_report_pull_command(argv: list[str]) -> bool:
    return (
        len(argv) >= 6
        and argv[:3] == ANDROID_REPORT_EVIDENCE_ADB_PULL_ARGV_PREFIX
        and ANDROID_REPORT_EVIDENCE_ADB_PULL_COMMAND in argv
    )


def _validate_adb_run_as_application_id(
    argv: list[str],
    expected_application_id: str,
    command_kind: str,
    issues: list[str],
) -> None:
    actual_application_id = argv[3] if len(argv) > 3 else ""
    if actual_application_id != expected_application_id:
        issues.append(
            f"host_command_adb_app_mismatch: {command_kind} expected "
            f"{expected_application_id!r}, got {actual_application_id!r}."
        )


def _token_after(argv: list[str], token: str) -> str | None:
    try:
        index = argv.index(token)
    except ValueError:
        return None
    next_index = index + 1
    return argv[next_index] if next_index < len(argv) else None


def _python_script_argv(command_text: str, script: str) -> list[str] | None:
    for argv in _host_command_argvs(command_text):
        if _is_python_script_argv(argv, script):
            return argv
    return None


def _is_python_script_argv(argv: list[str], script: str) -> bool:
    return (
        len(argv) >= 2
        and argv[0] == ANDROID_REPORT_EVIDENCE_PYTHON_COMMAND
        and argv[1] == script
    )


def _positional_after_script_arg(argv: list[str]) -> str | None:
    return argv[2] if len(argv) > 2 else None


def _argv_option_value(argv: list[str], option: str) -> str | None:
    try:
        option_index = argv.index(option)
    except ValueError:
        return None
    value_index = option_index + 1
    return argv[value_index] if value_index < len(argv) else None


def _validate_evidence_command_output_path(
    command_text: str,
    issues: list[str],
) -> None:
    builder_output = _command_option_value(
        command_text,
        ANDROID_REPORT_EVIDENCE_DRAFT_BUILDER_SCRIPT,
        ANDROID_REPORT_EVIDENCE_OUTPUT_OPTION,
    )
    validator_input = _command_positional_after_script(
        command_text,
        ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT,
    )
    if not _is_filled_value(builder_output) or not _is_filled_value(validator_input):
        return
    if builder_output != validator_input:
        issues.append(
            "host_command_evidence_path_mismatch: expected validator input "
            f"to be {builder_output!r}, got {validator_input!r}."
        )
        return

    validator = _python_script_argv(
        command_text,
        ANDROID_REPORT_EVIDENCE_VALIDATOR_SCRIPT,
    )
    if validator is None:
        return
    expected_validator = _expected_validator_argv(builder_output)
    if validator != expected_validator:
        issues.append(
            "host_command_validator_structure_mismatch: expected "
            f"{host_command_argv_text(expected_validator)}."
        )


def _validate_result(text: str, issues: list[str]) -> None:
    result = _section_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
        ANDROID_REPORT_EVIDENCE_PASS_FAIL_LABEL,
    )
    if result is None:
        issues.append(f"missing_result: {ANDROID_REPORT_EVIDENCE_PASS_FAIL_LABEL}")
    elif result.strip() != ANDROID_REPORT_EVIDENCE_PASS_RESULT:
        issues.append(
            "result_status: expected "
            f"{ANDROID_REPORT_EVIDENCE_PASS_FAIL_LABEL} to be "
            f"{ANDROID_REPORT_EVIDENCE_PASS_RESULT}."
        )

    failure_category = _section_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_RESULT_HEADING,
        ANDROID_REPORT_EVIDENCE_FAILURE_CATEGORY_LABEL,
    )
    if failure_category is None:
        issues.append(
            f"missing_result: {ANDROID_REPORT_EVIDENCE_FAILURE_CATEGORY_LABEL}"
        )
    elif failure_category.strip() != ANDROID_REPORT_EVIDENCE_NO_FAILURE_CATEGORY:
        issues.append(
            "result_failure_category: expected failure category to be "
            f"{ANDROID_REPORT_EVIDENCE_NO_FAILURE_CATEGORY}."
        )


def _validate_gate_summary(text: str, issues: list[str]) -> None:
    if any(
        line.strip()
        for line in _section_lines(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
    ):
        if not _has_valid_gate_summary_fence(text):
            issues.append(
                "gate_summary_fence_mismatch: expected ## Gate Summary to contain exactly one text fenced key-value block."
            )
            return

    summary_fields = _gate_summary_field_names(text)
    if summary_fields and summary_fields != ANDROID_REPORT_GATE_SUMMARY_FIELDS:
        issues.append(
            "gate_summary_fields_mismatch: expected Gate Summary fields "
            f"{ANDROID_REPORT_GATE_SUMMARY_FIELDS!r}, got {summary_fields!r}."
        )

    summary = _key_value_block(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
    if not summary:
        issues.append("missing_gate_summary: ## Gate Summary block is required.")
        return

    for key, expected in ANDROID_REPORT_GATE_PASS_SUMMARY_VALUES.items():
        actual = summary.get(key)
        if actual != expected:
            issues.append(
                f"gate_summary_{key}: expected {key}={expected}, got {actual!r}."
            )

    for key in ANDROID_REPORT_GATE_POSITIVE_SUMMARY_FIELDS:
        actual = summary.get(key)
        if not _is_positive_int(actual):
            issues.append(
                f"gate_summary_{key}: expected positive integer {key}, got {actual!r}."
            )


def _validate_gate_header_summary_values(text: str, issues: list[str]) -> None:
    summary = _key_value_block(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
    if not summary:
        return

    expected_header_labels = [
        label for label, _summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
    ]
    header_labels = _gate_header_labels(text)
    if header_labels != expected_header_labels:
        issues.append(
            "gate_header_fields_mismatch: expected Android Report Gate header fields "
            f"{expected_header_labels!r}, got {header_labels!r}."
        )

    for header_label, summary_key, issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS:
        header_value = _gate_header_line_value(text, header_label)
        summary_value = summary.get(summary_key)
        if not _is_filled_value(summary_value):
            continue
        if not _is_filled_value(header_value):
            issues.append(f"missing_gate_header: {header_label}")
            continue
        if header_value != summary_value:
            issues.append(
                f"gate_header_summary_mismatch: {issue_key} expected {summary_value!r}, got {header_value!r}."
            )


def _validate_summary_tables(text: str, issues: list[str]) -> None:
    performance_rows = _table_rows(text, ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING)
    if not performance_rows:
        issues.append(
            "missing_performance_report_rows: Performance Reports table needs a data row."
        )

    android_signal_rows = _table_rows(text, ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING)
    if not android_signal_rows:
        issues.append("missing_android_signal_rows: Android Signals table needs a data row.")


def _validate_summary_table_columns(text: str, issues: list[str]) -> None:
    performance_headers = _table_headers(
        text,
        ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    )
    if performance_headers != ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS:
        issues.append(
            "performance_report_table_columns_mismatch: expected "
            f"{ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS!r}, got "
            f"{performance_headers!r}."
        )

    signal_headers = _table_headers(text, ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING)
    if signal_headers != ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS:
        issues.append(
            "android_signal_table_columns_mismatch: expected "
            f"{ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS!r}, got "
            f"{signal_headers!r}."
        )


def _validate_gate_checks(text: str, issues: list[str]) -> None:
    check_lines = [
        line.strip()
        for line in _section_lines(text, ANDROID_REPORT_GATE_CHECKS_HEADING)
        if line.strip()
    ]
    if not check_lines:
        issues.append("missing_gate_checks: ## Checks section is required.")
        return
    if check_lines != ANDROID_REPORT_GATE_CHECK_LINES:
        issues.append(
            "gate_checks_mismatch: expected ## Checks to match analyzer gate checklist."
        )


def _validate_gate_issues(text: str, issues: list[str]) -> None:
    issue_lines = [
        line.strip()
        for line in _section_lines(text, ANDROID_REPORT_GATE_ISSUES_HEADING)
        if line.strip()
    ]
    if not issue_lines:
        issues.append("missing_gate_issues: ## Issues section is required.")
        return
    if issue_lines != [ANDROID_REPORT_GATE_NO_ISSUES_LINE]:
        issues.append(
            "gate_issues_not_none: expected ## Issues to contain exactly '- None.'."
        )


def _validate_single_report_scope(text: str, issues: list[str]) -> None:
    summary = _key_value_block(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
    expected_single_count_fields = [
        (summary_key, issue_key)
        for _header_label, summary_key, issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
        if summary_key in ANDROID_REPORT_GATE_POSITIVE_SUMMARY_FIELDS
    ]
    for summary_key, issue_key in expected_single_count_fields:
        actual = _int_value(summary.get(summary_key))
        if actual is not None and actual != 1:
            issues.append(
                f"single_report_scope_mismatch: {issue_key} expected 1, got {actual}."
            )

    table_counts = [
        (
            "performance_report_table_rows",
            len(_table_records(text, ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING)),
        ),
        ("android_signal_table_rows", len(_table_records(text, ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING))),
    ]
    for issue_key, actual in table_counts:
        if actual > 0 and actual != 1:
            issues.append(
                f"single_report_scope_mismatch: {issue_key} expected 1, got {actual}."
            )


def _validate_gate_summary_table_counts(text: str, issues: list[str]) -> None:
    summary = _key_value_block(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
    if not summary:
        return

    performance_count = _int_value(
        summary.get(ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD),
    )
    session_count = _int_value(
        summary.get(ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD),
    )
    performance_records = _table_records(text, ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING)
    android_signal_records = _table_records(text, ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING)

    if performance_count is not None:
        if performance_records and performance_count != len(performance_records):
            issues.append(
                "gate_summary_table_count_mismatch: "
                f"{ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD} "
                f"expected {len(performance_records)}, got {performance_count}."
            )
        if android_signal_records and performance_count != len(android_signal_records):
            issues.append(
                "gate_summary_table_count_mismatch: androidSignals "
                f"expected {performance_count}, got {len(android_signal_records)}."
            )

    if (
        performance_count is not None
        and session_count is not None
        and performance_count != session_count
    ):
        issues.append(
            "gate_summary_session_count_mismatch: expected "
            f"{ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD} to equal "
            f"{ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD}, got "
            f"{ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD}={session_count}, "
            f"{ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD}={performance_count}."
        )


def _validate_android_signal_table_context_values(
    text: str,
    issues: list[str],
) -> None:
    records = _table_records(text, ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING)
    if not records:
        return

    row = records[0]
    signal_columns = ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS
    expected_values = [
        (signal_columns[0], _report_field_value(text, "`reportId`"), "report_id"),
        (signal_columns[1], _report_field_value(text, "`decision.deviceSignals.platform`"), "platform"),
        (
            signal_columns[2],
            _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_DEVICE_MODEL_LABEL),
            "device_model",
        ),
        (
            signal_columns[3],
            _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_LABEL),
            "android_version",
        ),
        (
            signal_columns[4],
            _evidence_line_value(text, ANDROID_REPORT_EVIDENCE_SDK_INT_LABEL),
            "sdk_int",
        ),
        (signal_columns[5], _report_field_value(text, "`decision.deviceSignals.totalRamBytes`"), "total_ram_bytes"),
        (signal_columns[6], _report_field_value(text, "`decision.deviceSignals.isLowRamDevice`"), "is_low_ram_device"),
        (signal_columns[7], _report_field_value(text, "`decision.deviceSignals.isLowPowerModeEnabled`"), "is_low_power_mode_enabled"),
        (signal_columns[8], _report_field_value(text, "`decision.deviceSignals.memoryPressureState`"), "memory_pressure_state"),
        (signal_columns[9], _report_field_value(text, "`decision.deviceSignals.memoryPressureLevel`"), "memory_pressure_level"),
        (signal_columns[10], _report_field_value(text, "`decision.deviceSignals.thermalState`"), "thermal_state"),
        (signal_columns[11], _report_field_value(text, "`decision.deviceSignals.thermalStateLevel`"), "thermal_state_level"),
    ]
    for column, expected, issue_key in expected_values:
        actual = row.get(column)
        if actual is None:
            issues.append(f"android_signal_table_missing_column: {column}")
            continue
        if not _is_filled_value(expected):
            continue
        if not _is_filled_value(actual):
            issues.append(f"android_signal_table_missing_value: {issue_key}")
            continue
        if actual != expected:
            issues.append(
                f"android_signal_table_context_mismatch: {issue_key} expected {expected!r}, got {actual!r}."
            )


def _validate_performance_report_table_field_values(
    text: str,
    issues: list[str],
) -> None:
    records = _table_records(text, ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING)
    if not records:
        return

    row = records[0]
    performance_columns = ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS
    expected_values = [
        (performance_columns[1], _report_field_value(text, "`reportId`"), "report_id"),
        (performance_columns[2], _report_field_value(text, "`source`"), "source"),
        (performance_columns[3], _report_field_value(text, "`metadata.serviceSessionId`"), "service_session_id"),
        (performance_columns[4], _report_field_value(text, "`metadata.reportSequence`"), "report_sequence"),
        (performance_columns[5], _report_field_value(text, "`decision.tier`"), "tier"),
        (performance_columns[6], _report_field_value(text, "`decision.confidence`"), "confidence"),
        (performance_columns[7], _report_field_value(text, "`decision.runtimeObservation.status`"), "runtime"),
        (performance_columns[8], _report_field_value(text, "`generatedAt`"), "generated_at"),
        (performance_columns[9], _report_field_value(text, "`decision.decidedAt`"), "decided_at"),
    ]
    for column, expected, issue_key in expected_values:
        actual = row.get(column)
        if actual is None:
            issues.append(f"performance_report_table_missing_column: {column}")
            continue
        if not _is_filled_value(actual):
            issues.append(f"performance_report_table_missing_value: {issue_key}")
            continue
        if _is_filled_value(expected) and actual != expected:
            issues.append(
                f"performance_report_table_context_mismatch: {issue_key} expected {expected!r}, got {actual!r}."
            )


def _validate_performance_report_table_source(
    text: str,
    issues: list[str],
) -> None:
    records = _table_records(text, ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING)
    if not records:
        return

    row = records[0]
    source_column = ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS[0]
    source = row.get(source_column)
    if source is None:
        issues.append(f"performance_report_table_missing_column: {source_column}")
        return

    pulled_report_path = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_PULLED_REPORT_PATH_LABEL,
    )
    report_file_name = _evidence_line_value(
        text,
        ANDROID_REPORT_EVIDENCE_REPORT_FILE_NAME_LABEL,
    )
    if not _is_filled_value(pulled_report_path) or not _is_filled_value(
        report_file_name,
    ):
        return

    if not _source_matches_pulled_report(
        source,
        pulled_report_path,
        report_file_name,
    ):
        issues.append(
            "performance_report_table_source_mismatch: expected Source to match "
            f"Pulled report path {pulled_report_path!r}, got {source!r}."
        )


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


def _validate_report_fields(text: str, issues: list[str]) -> None:
    for label in ANDROID_REPORT_GATE_REQUIRED_FIELD_LABELS:
        value = _report_field_value(text, label)
        if not _is_filled_value(value):
            issues.append(f"missing_report_field_check: {label}")
    for label in ANDROID_REPORT_GATE_PRESENT_FIELD_LABELS:
        if _report_field_value(text, label) is None:
            issues.append(f"missing_report_field_check: {label}")


def _validate_report_field_check_scope(text: str, issues: list[str]) -> None:
    report_id = _report_field_value(text, "`reportId`")
    if not _is_filled_value(report_id):
        return

    headings = _section_subheadings(text, ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING)
    if not headings:
        issues.append(
            f"missing_report_field_check_heading: expected ### {report_id}."
        )
        return
    if len(headings) != 1:
        issues.append(
            "report_field_check_scope_mismatch: expected exactly one "
            f"Report Field Check heading for {report_id!r}, got {len(headings)}."
        )
        return
    if headings[0] != report_id:
        issues.append(
            "report_field_check_heading_mismatch: expected "
            f"{report_id!r}, got {headings[0]!r}."
        )


def _validate_report_field_check_labels(text: str, issues: list[str]) -> None:
    labels = _report_field_check_labels(text)
    if labels != ANDROID_REPORT_GATE_FIELD_CHECK_LABELS:
        issues.append(
            "report_field_check_labels_mismatch: expected Report Field Check "
            f"labels {ANDROID_REPORT_GATE_FIELD_CHECK_LABELS!r}, got "
            f"{labels!r}."
        )


def _validate_report_field_contract_values(text: str, issues: list[str]) -> None:
    expected_values = [
        ("`schemaName`", PERFORMANCE_REPORT_SCHEMA_NAME, "schema_name"),
        ("`schemaVersion`", "1", "schema_version"),
        ("`decision.deviceSignals.platform`", "android", "platform"),
    ]
    for label, expected, issue_key in expected_values:
        actual = _report_field_value(text, label)
        if _is_filled_value(actual) and actual != expected:
            issues.append(
                f"report_field_contract_mismatch: {issue_key} expected {expected!r}, got {actual!r}."
            )

    context_pairs = [
        (
            ANDROID_REPORT_EVIDENCE_DEVICE_MODEL_LABEL,
            "`decision.deviceSignals.deviceModel`",
            "device_model",
        ),
        (
            ANDROID_REPORT_EVIDENCE_ANDROID_VERSION_LABEL,
            "`decision.deviceSignals.osVersion`",
            "android_version",
        ),
        (
            ANDROID_REPORT_EVIDENCE_SDK_INT_LABEL,
            "`decision.deviceSignals.sdkInt`",
            "sdk_int",
        ),
    ]
    for context_label, field_label, issue_key in context_pairs:
        context_value = _evidence_line_value(text, context_label)
        field_value = _report_field_value(text, field_label)
        if not _is_filled_value(context_value) or not _is_filled_value(field_value):
            continue
        if context_value != field_value:
            issues.append(
                f"report_field_context_mismatch: {issue_key} expected {context_value!r}, got {field_value!r}."
            )


def _validate_identity_checklist(text: str, issues: list[str]) -> None:
    labels = _section_field_labels(
        text,
        ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
    )
    if labels != IDENTITY_CHECKLIST_LABELS:
        issues.append(
            "identity_checklist_labels_mismatch: expected "
            f"{IDENTITY_CHECKLIST_LABELS!r}, got {labels!r}."
        )
    for label in IDENTITY_CHECKLIST_LABELS:
        value = _section_line_value(
            text,
            ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
            label,
        )
        if _normalized_yes_no(value) != "yes":
            issues.append(f"identity_check_not_yes: {label}")


def _evidence_line_value(text: str, label: str) -> str | None:
    heading = ANDROID_REPORT_EVIDENCE_FIELD_SECTIONS.get(label)
    if heading is None:
        return _line_value(text, label)
    return _section_line_value(text, heading, label)


def _report_field_value(text: str, label: str) -> str | None:
    prefix = f"- {label}:"
    for line in _report_field_check_lines(text):
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _report_field_check_labels(text: str) -> list[str]:
    labels: list[str] = []
    for line in _report_field_check_lines(text):
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        label, _value = stripped[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _report_field_check_lines(text: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING:
            start = index + 1
            break
    if start is None:
        return []

    section: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        section.append(line)
    return section


def _gate_header_line_value(text: str, label: str) -> str | None:
    prefix = f"- {label}:"
    for line in _gate_header_lines(text):
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _gate_header_labels(text: str) -> list[str]:
    labels: list[str] = []
    for line in _gate_header_lines(text):
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        label, _value = stripped[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _gate_header_lines(text: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == "# Android Report Gate":
            start = index + 1
            break
    if start is None:
        return []

    header: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        header.append(line)
    return header


def _line_value(text: str, label: str) -> str | None:
    pattern = re.compile(
        rf"^[ \t]*-[ \t]*{re.escape(label)}:[ \t]*(.*?)[ \t]*$",
        re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def _section_line_value(text: str, heading: str, label: str) -> str | None:
    prefix = f"- {label}:"
    for line in _section_lines(text, heading):
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _section_field_labels(text: str, heading: str) -> list[str]:
    labels: list[str] = []
    for line in _section_lines(text, heading):
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        label, _value = stripped[2:].split(":", 1)
        labels.append(label.strip())
    return labels


def _is_filled_value(value: str | None) -> bool:
    if value is None:
        return False
    stripped = value.strip()
    if not stripped:
        return False
    if stripped in {
        "...",
        "PASS / FAIL",
        "yes / no",
        ANDROID_REPORT_EVIDENCE_APP_USED_PLACEHOLDER,
    }:
        return False
    if "<" in stripped or ">" in stripped:
        return False
    return True


def _contains_placeholder(text: str) -> bool:
    return re.search(r"<[^>\n]+>", text) is not None or "..." in text


def _is_filled_app_trigger_value(value: str | None) -> bool:
    if value is None:
        return False
    stripped = value.strip()
    if not stripped:
        return False
    return not _contains_placeholder(stripped)


def _command_contains_value(
    command_text: str,
    value: str,
    *,
    allow_path_basename: bool,
) -> bool:
    for argv in _host_command_argvs(command_text):
        for token in argv:
            if token == value:
                return True
            if allow_path_basename and host_path_basename(token) == value:
                return True
    return False


def _command_option_value(command_text: str, script: str, option: str) -> str | None:
    for argv in _host_command_argvs(command_text):
        if script not in argv:
            continue
        try:
            option_index = argv.index(option)
        except ValueError:
            return None
        value_index = option_index + 1
        return argv[value_index] if value_index < len(argv) else None
    return None


def _command_positional_after_script(command_text: str, script: str) -> str | None:
    for argv in _host_command_argvs(command_text):
        if script not in argv:
            continue
        script_index = argv.index(script)
        value_index = script_index + 1
        return argv[value_index] if value_index < len(argv) else None
    return None


def _host_command_argvs(command_text: str) -> Iterable[list[str]]:
    for line in command_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("```"):
            continue
        try:
            argv = shlex.split(stripped)
        except ValueError:
            continue
        if argv:
            yield argv


def _normalized_yes_no(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower()


def _key_value_block(text: str, heading: str) -> dict[str, str]:
    if heading == ANDROID_REPORT_GATE_SUMMARY_HEADING:
        lines = _gate_summary_key_value_lines(text)
    else:
        lines = _section_lines(text, heading)
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _gate_summary_key_value_lines(text: str) -> list[str]:
    lines = [
        line.strip()
        for line in _section_lines(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
        if line.strip()
    ]
    if not _is_valid_gate_summary_fence(lines):
        return []
    return lines[1:-1]


def _gate_summary_field_names(text: str) -> list[str]:
    fields: list[str] = []
    for line in _gate_summary_key_value_lines(text):
        stripped = line.strip()
        if "=" not in stripped:
            fields.append(stripped)
            continue
        field, _value = stripped.split("=", 1)
        fields.append(field.strip())
    return fields


def _has_valid_gate_summary_fence(text: str) -> bool:
    lines = [
        line.strip()
        for line in _section_lines(text, ANDROID_REPORT_GATE_SUMMARY_HEADING)
        if line.strip()
    ]
    return _is_valid_gate_summary_fence(lines)


def _is_valid_gate_summary_fence(lines: list[str]) -> bool:
    if len(lines) < 2:
        return False
    if lines[0] != ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START:
        return False
    if lines[-1] != ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END:
        return False
    return not any(line.startswith("```") for line in lines[1:-1])


def _table_rows(text: str, heading: str) -> list[str]:
    lines = _section_lines(text, heading)
    table_lines = [line.strip() for line in lines if line.strip().startswith("|")]
    data_rows: list[str] = []
    for line in table_lines[2:]:
        if "..." in line:
            continue
        if line.count("|") < 3:
            continue
        data_rows.append(line)
    return data_rows


def _table_headers(text: str, heading: str) -> list[str]:
    lines = _section_lines(text, heading)
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|"):
            return _split_table_row(stripped)
    return []


def _table_records(text: str, heading: str) -> list[dict[str, str]]:
    lines = _section_lines(text, heading)
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


def _section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return []

    section: list[str] = []
    for line in lines[start:]:
        if line.startswith("#") and line.strip() != heading:
            break
        section.append(line)
    return section


def _section_subheadings(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return []

    subheadings: list[str] = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("## ") and stripped != heading:
            break
        if stripped.startswith("### "):
            subheadings.append(stripped[4:].strip())
    return subheadings


def _is_positive_int(value: str | None) -> bool:
    if value is None:
        return False
    try:
        parsed = int(value)
    except ValueError:
        return False
    return parsed > 0


def _int_value(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _normalized_path_for_match(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _issue_key(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value.strip().lower())
    return normalized.strip("_")


def _format_issues(issues: Iterable[str]) -> str:
    return "\n".join(f"- {issue}" for issue in issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a filled Android report-loop evidence markdown file before "
            "using it as readiness evidence."
        ),
    )
    parser.add_argument("evidence", type=Path, help="Filled evidence markdown file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_evidence_path(args.evidence)
    if result.ok:
        print(evidence_status_line(ANDROID_REPORT_EVIDENCE_PASS_STATUS))
        return 0

    print(evidence_status_line(ANDROID_REPORT_EVIDENCE_FAIL_STATUS))
    print(_format_issues(result.issues))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

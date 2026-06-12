#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from android_report_gate_contract import (
    ANDROID_REPORT_GATE_CHECK_LINES,
    ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
    ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS,
    ANDROID_REPORT_GATE_CHECKS_HEADING,
    ANDROID_REPORT_GATE_FIELD_CHECK_LABELS,
    ANDROID_REPORT_GATE_FAIL_STATUS,
    ANDROID_REPORT_GATE_HEADER_FIELDS,
    ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
    ANDROID_REPORT_GATE_ISSUES_HEADING,
    ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME,
    ANDROID_REPORT_GATE_NO_ISSUES_LINE,
    ANDROID_REPORT_GATE_PASS_STATUS,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
    ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END,
    ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START,
    ANDROID_REPORT_GATE_SUMMARY_FIELDS,
    ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_HEADING,
    ANDROID_REPORT_GATE_SUMMARY_ISSUE_COUNT_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_PARSE_ISSUES_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD,
    IDENTITY_CHECKLIST_LABELS,
    PERFORMANCE_REPORT_SCHEMA_NAME,
)

SUPPORTED_SUFFIXES = {".json", ".jsonl", ".ndjson", ".log", ".txt"}
ACTIVE_RUNTIME_STATUSES = {"pending", "active", "cooldown", "recovery-pending"}
ANDROID_REPORT_GATE_TIERS = {"t0Low", "t1Mid", "t2High", "t3Ultra"}
ANDROID_REPORT_GATE_CONFIDENCES = {"low", "medium", "high"}
ANDROID_REPORT_GATE_RUNTIME_STATUSES = {
    "inactive",
    "pending",
    "active",
    "cooldown",
    "recovery-pending",
    "recovered",
}
ANDROID_REPORT_GATE_MEMORY_PRESSURE_STATES = {"normal", "moderate", "critical"}
ANDROID_REPORT_GATE_MEMORY_PRESSURE_LEVELS = {0, 1, 2}
ANDROID_REPORT_GATE_THERMAL_STATES = {"normal", "fair", "serious", "critical"}
ANDROID_REPORT_GATE_THERMAL_LEVELS = {0, 1, 2, 3}
SESSION_HEADERS = [
    "source_file",
    "source_ref",
    "source_type",
    "schema_name",
    "schema_version",
    "report_id",
    "report_source",
    "report_status",
    "generated_at",
    "session_id",
    "report_sequence",
    "initializing",
    "tier",
    "confidence",
    "decided_at",
    "runtime_status",
    "runtime_trigger_reason",
    "status_duration_ms",
    "downgrade_trigger_count",
    "recovery_trigger_count",
    "platform",
    "device_model",
    "os_version",
    "total_ram_bytes",
    "total_ram_gb",
    "is_low_ram_device",
    "media_performance_class",
    "sdk_int",
    "thermal_state",
    "thermal_state_level",
    "is_low_power_mode_enabled",
    "memory_pressure_state",
    "memory_pressure_level",
    "frame_drop_state",
    "frame_drop_level",
    "frame_drop_rate",
    "frame_dropped_count",
    "frame_sampled_count",
    "reason_count",
    "reasons_json",
    "applied_policies_json",
    "recent_structured_log_count",
    "upload_client",
    "upload_running",
    "upload_result",
    "upload_error",
    "top_level_error",
    "is_fallback",
]
EVENT_HEADERS = [
    "source_file",
    "source_ref",
    "origin",
    "session_id",
    "event",
    "timestamp",
    "trigger",
    "transition_type",
    "tier_changed",
    "runtime_status_changed",
    "from_tier",
    "to_tier",
    "from_runtime_status",
    "to_runtime_status",
    "decision_tier",
    "decision_confidence",
    "decision_runtime_status",
    "payload_json",
]
DEVICE_HEADERS = [
    "platform",
    "device_model",
    "sample_count",
    "tier_distribution",
    "runtime_status_distribution",
    "unique_tier_count",
    "active_runtime_rate",
    "avg_downgrade_trigger_count",
    "avg_recovery_trigger_count",
    "avg_frame_drop_rate",
    "avg_total_ram_gb",
    "fallback_count",
    "missing_total_ram_count",
]
FLAGGED_HEADERS = [
    "source_ref",
    "session_id",
    "platform",
    "device_model",
    "tier",
    "runtime_status",
    "downgrade_trigger_count",
    "frame_drop_rate",
    "flags",
    "reason_excerpt",
]
ISSUE_HEADERS = ["source_ref", "issue", "detail"]
ANDROID_REPORT_GATE_REQUIRED_FIELDS = [
    "report_id",
    "report_source",
    "generated_at",
    "session_id",
    "report_sequence",
    "tier",
    "confidence",
    "decided_at",
    "runtime_status",
    "platform",
    "device_model",
    "os_version",
    "total_ram_bytes",
    "is_low_ram_device",
    "is_low_power_mode_enabled",
    "sdk_int",
    "memory_pressure_state",
    "memory_pressure_level",
]


@dataclass
class ParseIssue:
    source_ref: str
    issue: str
    detail: str


def json_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def looks_like_report(value: Any) -> bool:
    return isinstance(value, dict) and (
        "decision" in value or "recentStructuredLogs" in value or "uploadProbe" in value
    )


def looks_like_decision(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and "tier" in value
        and "deviceSignals" in value
        and "runtimeObservation" in value
    )


def looks_like_log_record(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("event"), str)
        and isinstance(value.get("timestamp"), str)
        and isinstance(value.get("payload"), dict)
    )


def normalize_bool(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return ""


def safe_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            try:
                parsed = float(stripped)
            except ValueError:
                return None
            return int(parsed) if parsed.is_integer() else None
    return None


def safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def is_integerish(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return value.is_integer()
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return False
        return stripped.isdigit() or (
            stripped.startswith("-") and stripped[1:].isdigit()
        )
    return False


def is_json_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def is_json_bool(value: Any) -> bool:
    return isinstance(value, bool)


def is_non_empty_json_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse_iso_datetime(value: Any) -> datetime | None:
    text = safe_str(value).strip()
    if not text or "T" not in text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def is_iso_datetime(value: Any) -> bool:
    return parse_iso_datetime(value) is not None


def is_utc_iso_datetime(value: Any) -> bool:
    parsed = parse_iso_datetime(value)
    if parsed is None:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def report_source_type(report: dict[str, Any]) -> str:
    if safe_str(report.get("schemaName")) == PERFORMANCE_REPORT_SCHEMA_NAME:
        return "performance-report"
    if "schemaVersion" in report and "reportId" in report and "decision" in report:
        return "performance-report"
    return "ai-report"


def average(values: Iterable[float]) -> float | None:
    items = [value for value in values if value is not None]
    if not items:
        return None
    return sum(items) / len(items)


def format_percent(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"


def format_float(value: float | None, digits: int = 3) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def counter_to_text(counter: Counter[str]) -> str:
    if not counter:
        return ""
    parts = [f"{key}:{counter[key]}" for key in sorted(counter)]
    return ", ".join(parts)


def gate_value_text(value: Any) -> str:
    if value is None:
        return "<missing>"
    if isinstance(value, str):
        return f"{value!r} ({type(value).__name__})"
    return f"{safe_str(value)} ({type(value).__name__})"


def markdown_cell(value: Any) -> str:
    text = safe_str(value) or "-"
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_inline(value: Any) -> str:
    return safe_str(value).replace("\n", " ").strip()


def trim_reason_excerpt(reasons_json: str, max_length: int = 180) -> str:
    if not reasons_json:
        return ""
    try:
        reasons = json.loads(reasons_json)
        if isinstance(reasons, list):
            text = " | ".join(safe_str(item) for item in reasons[:3])
        else:
            text = safe_str(reasons)
    except json.JSONDecodeError:
        text = reasons_json
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."


class DiagnosticsAnalyzer:
    def __init__(self, prefix: str, top_n: int) -> None:
        self.prefix = prefix
        self.top_n = top_n
        self.session_rows: list[dict[str, Any]] = []
        self.event_rows: list[dict[str, Any]] = []
        self.device_rows: list[dict[str, Any]] = []
        self.flagged_rows: list[dict[str, Any]] = []
        self.issues: list[ParseIssue] = []
        self.files_scanned = 0
        self._report_session_keys: set[tuple[str, str]] = set()

    def ingest_files(self, paths: Iterable[Path]) -> None:
        for path in sorted(paths):
            self.files_scanned += 1
            if path.suffix.lower() == ".json":
                self._ingest_json_file(path)
            else:
                self._ingest_line_file(path)
        self._derive_sessions_from_events()
        self._build_device_rows()
        self._build_flagged_rows()

    def write_outputs(self, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        self._write_csv(output_dir / "session_summary.csv", SESSION_HEADERS, self.session_rows)
        self._write_csv(output_dir / "event_timeline.csv", EVENT_HEADERS, self.event_rows)
        self._write_csv(output_dir / "device_model_summary.csv", DEVICE_HEADERS, self.device_rows)
        self._write_csv(output_dir / "flagged_sessions.csv", FLAGGED_HEADERS, self.flagged_rows)
        self._write_csv(
            output_dir / "parse_issues.csv",
            ISSUE_HEADERS,
            [issue.__dict__ for issue in self.issues],
        )
        (output_dir / "summary.md").write_text(self._build_summary_markdown(), encoding="utf-8")

    def _ingest_json_file(self, path: Path) -> None:
        source_ref = str(path)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            self.issues.append(ParseIssue(source_ref, "empty_file", "File contains no JSON."))
            return
        try:
            data = json.loads(text)
        except json.JSONDecodeError as error:
            self.issues.append(ParseIssue(source_ref, "json_decode_error", str(error)))
            return
        self._ingest_value(data, path, source_ref)

    def _ingest_line_file(self, path: Path) -> None:
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except UnicodeDecodeError:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()
            if not line:
                continue
            json_text = self._extract_json_text_from_line(line)
            if json_text is None:
                continue
            source_ref = f"{path}:{index}"
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as error:
                self.issues.append(ParseIssue(source_ref, "json_decode_error", str(error)))
                continue
            self._ingest_value(data, path, source_ref)

    def _extract_json_text_from_line(self, line: str) -> str | None:
        if line.startswith(f"{self.prefix} "):
            return line[len(self.prefix) + 1 :].strip()
        if line.startswith("{") or line.startswith("["):
            return line
        return None

    def _ingest_value(self, value: Any, source_file: Path, source_ref: str) -> None:
        if isinstance(value, list):
            for index, item in enumerate(value, start=1):
                self._ingest_value(item, source_file, f"{source_ref}#{index}")
            return
        if looks_like_report(value):
            self._add_report_row(
                source_file,
                source_ref,
                value,
                report_source_type(value),
            )
            return
        if looks_like_decision(value):
            self._add_decision_row(source_file, source_ref, value, "decision-only")
            return
        if looks_like_log_record(value):
            event_row = self._build_event_row(source_file, source_ref, value, "log-record")
            self.event_rows.append(event_row)
            return
        self.issues.append(
            ParseIssue(source_ref, "unsupported_shape", f"Unsupported JSON shape: {type(value).__name__}")
        )

    def _add_report_row(
        self,
        source_file: Path,
        source_ref: str,
        report: dict[str, Any],
        source_type: str,
    ) -> None:
        logs = report.get("recentStructuredLogs")
        metadata = report.get("metadata")
        metadata_map = metadata if isinstance(metadata, dict) else {}
        recent_structured_log_count = len(logs) if isinstance(logs, list) else 0
        embedded_events = self._parse_embedded_logs(source_file, source_ref, logs)
        session_id = self._pick_session_id(embedded_events) or safe_str(
            metadata_map.get("serviceSessionId")
        )
        row = self._build_session_row(
            source_file=source_file,
            source_ref=source_ref,
            source_type=source_type,
            schema_name=safe_str(report.get("schemaName")),
            schema_version=safe_int(report.get("schemaVersion")),
            schema_version_raw=report.get("schemaVersion"),
            report_id=safe_str(report.get("reportId")),
            report_id_raw=report.get("reportId"),
            report_source=safe_str(report.get("source")),
            report_source_raw=report.get("source"),
            report_status=safe_str(report.get("status")) or "ok",
            generated_at=safe_str(report.get("generatedAt")),
            generated_at_raw=report.get("generatedAt"),
            initializing=normalize_bool(report.get("initializing")),
            decision=report.get("decision"),
            top_level_error=safe_str(report.get("error")),
            recent_structured_log_count=recent_structured_log_count,
            upload_probe=report.get("uploadProbe"),
            session_id=session_id,
            service_session_id_raw=metadata_map.get("serviceSessionId"),
            report_sequence_raw=metadata_map.get("reportSequence"),
        )
        self.session_rows.append(row)
        if session_id:
            self._report_session_keys.add((row["source_file"], session_id))

    def _add_decision_row(
        self,
        source_file: Path,
        source_ref: str,
        decision: dict[str, Any],
        source_type: str,
    ) -> None:
        row = self._build_session_row(
            source_file=source_file,
            source_ref=source_ref,
            source_type=source_type,
            schema_name="",
            schema_version=None,
            schema_version_raw=None,
            report_id="",
            report_id_raw=None,
            report_source="",
            report_source_raw=None,
            report_status="ok",
            generated_at=safe_str(decision.get("decidedAt")),
            generated_at_raw=decision.get("decidedAt"),
            initializing="false",
            decision=decision,
            top_level_error="",
            recent_structured_log_count=0,
            upload_probe=None,
            session_id="",
            service_session_id_raw=None,
            report_sequence_raw=None,
        )
        self.session_rows.append(row)

    def _parse_embedded_logs(
        self,
        source_file: Path,
        source_ref: str,
        log_lines: Any,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if not isinstance(log_lines, list):
            return events
        for index, item in enumerate(log_lines, start=1):
            item_ref = f"{source_ref}::recentStructuredLogs[{index}]"
            if isinstance(item, str):
                json_text = self._extract_json_text_from_line(item.strip())
                if json_text is None:
                    self.issues.append(
                        ParseIssue(item_ref, "unsupported_log_line", "Embedded log line does not contain JSON.")
                    )
                    continue
                try:
                    payload = json.loads(json_text)
                except json.JSONDecodeError as error:
                    self.issues.append(ParseIssue(item_ref, "json_decode_error", str(error)))
                    continue
            elif isinstance(item, dict):
                payload = item
            else:
                self.issues.append(
                    ParseIssue(item_ref, "unsupported_log_item", f"Unsupported item: {type(item).__name__}")
                )
                continue
            if not looks_like_log_record(payload):
                self.issues.append(
                    ParseIssue(item_ref, "unsupported_log_record", "Embedded item is not a log record.")
                )
                continue
            event_row = self._build_event_row(source_file, item_ref, payload, "embedded-log")
            self.event_rows.append(event_row)
            events.append(event_row)
        return events

    def _build_session_row(
        self,
        *,
        source_file: Path,
        source_ref: str,
        source_type: str,
        schema_name: str,
        schema_version: int | None,
        schema_version_raw: Any,
        report_id: str,
        report_id_raw: Any,
        report_source: str,
        report_source_raw: Any,
        report_status: str,
        generated_at: str,
        generated_at_raw: Any,
        initializing: str,
        decision: Any,
        top_level_error: str,
        recent_structured_log_count: int,
        upload_probe: Any,
        session_id: str,
        service_session_id_raw: Any,
        report_sequence_raw: Any,
    ) -> dict[str, Any]:
        decision_map = decision if isinstance(decision, dict) else {}
        device_signals = decision_map.get("deviceSignals")
        runtime = decision_map.get("runtimeObservation")
        reasons = decision_map.get("reasons")
        applied_policies = decision_map.get("appliedPolicies")
        upload_map = upload_probe if isinstance(upload_probe, dict) else {}

        reason_list = reasons if isinstance(reasons, list) else []
        fallback = any("Failed to collect platform signals" in safe_str(item) for item in reason_list)
        tier_raw = decision_map.get("tier")
        confidence_raw = decision_map.get("confidence")
        runtime_status_raw = _maybe_dict_value(runtime, "status")
        platform_raw = _maybe_dict_value(device_signals, "platform")
        total_ram_bytes_raw = _maybe_dict_value(device_signals, "totalRamBytes")
        device_model_raw = _maybe_dict_value(device_signals, "deviceModel")
        os_version_raw = _maybe_dict_value(device_signals, "osVersion")
        is_low_ram_device_raw = _maybe_dict_value(device_signals, "isLowRamDevice")
        sdk_int_raw = _maybe_dict_value(device_signals, "sdkInt")
        thermal_state_raw = _maybe_dict_value(device_signals, "thermalState")
        thermal_state_level_raw = _maybe_dict_value(device_signals, "thermalStateLevel")
        is_low_power_mode_enabled_raw = _maybe_dict_value(
            device_signals,
            "isLowPowerModeEnabled",
        )
        memory_pressure_state_raw = _maybe_dict_value(device_signals, "memoryPressureState")
        memory_pressure_level_raw = _maybe_dict_value(device_signals, "memoryPressureLevel")
        total_ram_bytes = safe_int(total_ram_bytes_raw)
        total_ram_gb = total_ram_bytes / (1024 ** 3) if total_ram_bytes is not None else None

        return {
            "source_file": str(source_file),
            "source_ref": source_ref,
            "source_type": source_type,
            "schema_name": schema_name,
            "schema_version": schema_version,
            "_schema_version_raw": schema_version_raw,
            "report_id": report_id,
            "_report_id_raw": report_id_raw,
            "report_source": report_source,
            "_report_source_raw": report_source_raw,
            "report_status": report_status,
            "generated_at": generated_at,
            "_generated_at_raw": generated_at_raw,
            "session_id": session_id,
            "_service_session_id_raw": service_session_id_raw,
            "report_sequence": safe_int(report_sequence_raw),
            "_report_sequence_raw": report_sequence_raw,
            "initializing": initializing,
            "tier": safe_str(tier_raw),
            "_tier_raw": tier_raw,
            "confidence": safe_str(confidence_raw),
            "_confidence_raw": confidence_raw,
            "decided_at": safe_str(decision_map.get("decidedAt")),
            "_decided_at_raw": decision_map.get("decidedAt"),
            "runtime_status": safe_str(runtime_status_raw),
            "_runtime_status_raw": runtime_status_raw,
            "runtime_trigger_reason": safe_str(_maybe_dict_value(runtime, "triggerReason")),
            "status_duration_ms": safe_int(_maybe_dict_value(runtime, "statusDurationMs")),
            "downgrade_trigger_count": safe_int(_maybe_dict_value(runtime, "downgradeTriggerCount")),
            "recovery_trigger_count": safe_int(_maybe_dict_value(runtime, "recoveryTriggerCount")),
            "platform": safe_str(platform_raw),
            "_platform_raw": platform_raw,
            "device_model": safe_str(device_model_raw),
            "_device_model_raw": device_model_raw,
            "os_version": safe_str(os_version_raw),
            "_os_version_raw": os_version_raw,
            "total_ram_bytes": total_ram_bytes,
            "_total_ram_bytes_raw": total_ram_bytes_raw,
            "total_ram_gb": format_float(total_ram_gb, 2),
            "is_low_ram_device": normalize_bool(is_low_ram_device_raw),
            "_is_low_ram_device_raw": is_low_ram_device_raw,
            "media_performance_class": safe_int(_maybe_dict_value(device_signals, "mediaPerformanceClass")),
            "sdk_int": safe_int(sdk_int_raw),
            "_sdk_int_raw": sdk_int_raw,
            "thermal_state": safe_str(thermal_state_raw),
            "_thermal_state_raw": thermal_state_raw,
            "thermal_state_level": safe_int(thermal_state_level_raw),
            "_thermal_state_level_raw": thermal_state_level_raw,
            "is_low_power_mode_enabled": normalize_bool(is_low_power_mode_enabled_raw),
            "_is_low_power_mode_enabled_raw": is_low_power_mode_enabled_raw,
            "memory_pressure_state": safe_str(memory_pressure_state_raw),
            "_memory_pressure_state_raw": memory_pressure_state_raw,
            "memory_pressure_level": safe_int(memory_pressure_level_raw),
            "_memory_pressure_level_raw": memory_pressure_level_raw,
            "frame_drop_state": safe_str(_maybe_dict_value(device_signals, "frameDropState")),
            "frame_drop_level": safe_int(_maybe_dict_value(device_signals, "frameDropLevel")),
            "frame_drop_rate": safe_float(_maybe_dict_value(device_signals, "frameDropRate")),
            "frame_dropped_count": safe_int(_maybe_dict_value(device_signals, "frameDroppedCount")),
            "frame_sampled_count": safe_int(_maybe_dict_value(device_signals, "frameSampledCount")),
            "reason_count": len(reason_list),
            "reasons_json": json_compact(reason_list),
            "applied_policies_json": json_compact(applied_policies if isinstance(applied_policies, dict) else {}),
            "recent_structured_log_count": recent_structured_log_count,
            "upload_client": safe_str(upload_map.get("client")),
            "upload_running": normalize_bool(upload_map.get("running")),
            "upload_result": safe_str(upload_map.get("result")),
            "upload_error": safe_str(upload_map.get("error")),
            "top_level_error": top_level_error,
            "is_fallback": "true" if fallback else "false",
        }

    def _build_event_row(
        self,
        source_file: Path,
        source_ref: str,
        record: dict[str, Any],
        origin: str,
    ) -> dict[str, Any]:
        payload = record.get("payload")
        payload_map = payload if isinstance(payload, dict) else {}
        transition = payload_map.get("transition")
        transition_map = transition if isinstance(transition, dict) else {}
        decision = payload_map.get("decision")
        decision_map = decision if isinstance(decision, dict) else {}
        runtime = decision_map.get("runtimeObservation")
        runtime_map = runtime if isinstance(runtime, dict) else {}

        return {
            "source_file": str(source_file),
            "source_ref": source_ref,
            "origin": origin,
            "session_id": safe_str(record.get("sessionId")),
            "event": safe_str(record.get("event")),
            "timestamp": safe_str(record.get("timestamp")),
            "trigger": safe_str(payload_map.get("trigger")),
            "transition_type": safe_str(transition_map.get("type")),
            "tier_changed": normalize_bool(transition_map.get("tierChanged")),
            "runtime_status_changed": normalize_bool(transition_map.get("runtimeStatusChanged")),
            "from_tier": safe_str(transition_map.get("fromTier")),
            "to_tier": safe_str(transition_map.get("toTier")),
            "from_runtime_status": safe_str(transition_map.get("fromRuntimeStatus")),
            "to_runtime_status": safe_str(transition_map.get("toRuntimeStatus")),
            "decision_tier": safe_str(decision_map.get("tier")),
            "decision_confidence": safe_str(decision_map.get("confidence")),
            "decision_runtime_status": safe_str(runtime_map.get("status")),
            "payload_json": json_compact(payload_map),
            "_decision": decision_map,
        }

    def _pick_session_id(self, event_rows: Iterable[dict[str, Any]]) -> str:
        counter = Counter(
            row["session_id"]
            for row in event_rows
            if isinstance(row.get("session_id"), str) and row["session_id"]
        )
        if not counter:
            return ""
        return counter.most_common(1)[0][0]

    def _derive_sessions_from_events(self) -> None:
        groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for event_row in self.event_rows:
            session_id = safe_str(event_row.get("session_id"))
            groups[(safe_str(event_row.get("source_file")), session_id)].append(event_row)

        derived_rows: list[dict[str, Any]] = []
        for (source_file, session_id), rows in groups.items():
            if session_id and (source_file, session_id) in self._report_session_keys:
                continue
            decision_rows = [row for row in rows if isinstance(row.get("_decision"), dict) and row["_decision"]]
            if not decision_rows:
                continue
            latest = sorted(
                decision_rows,
                key=lambda row: (safe_str(row.get("timestamp")), safe_str(row.get("source_ref"))),
            )[-1]
            derived_rows.append(
                self._build_session_row(
                    source_file=Path(source_file),
                    source_ref=safe_str(latest.get("source_ref")),
                    source_type="log-session",
                    schema_name="",
                    schema_version=None,
                    schema_version_raw=None,
                    report_id="",
                    report_id_raw=None,
                    report_source="",
                    report_source_raw=None,
                    report_status="ok",
                    generated_at=safe_str(latest.get("timestamp")),
                    generated_at_raw=latest.get("timestamp"),
                    initializing="false",
                    decision=latest.get("_decision"),
                    top_level_error="",
                    recent_structured_log_count=0,
                    upload_probe=None,
                    session_id=session_id,
                    service_session_id_raw=None,
                    report_sequence_raw=None,
                )
            )
        self.session_rows.extend(derived_rows)

    def _build_device_rows(self) -> None:
        groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in self.session_rows:
            key = (
                row.get("platform") or "unknown",
                row.get("device_model") or "unknown",
            )
            groups[key].append(row)

        device_rows: list[dict[str, Any]] = []
        for (platform, device_model), rows in groups.items():
            tier_counter = Counter(safe_str(row.get("tier")) or "missing" for row in rows)
            runtime_counter = Counter(safe_str(row.get("runtime_status")) or "missing" for row in rows)
            active_count = sum(
                1 for row in rows if safe_str(row.get("runtime_status")) in ACTIVE_RUNTIME_STATUSES
            )
            fallback_count = sum(1 for row in rows if row.get("is_fallback") == "true")
            missing_total_ram_count = sum(1 for row in rows if row.get("total_ram_bytes") is None)
            device_rows.append(
                {
                    "platform": platform,
                    "device_model": device_model,
                    "sample_count": len(rows),
                    "tier_distribution": counter_to_text(tier_counter),
                    "runtime_status_distribution": counter_to_text(runtime_counter),
                    "unique_tier_count": len({key for key in tier_counter if key and key != "missing"}),
                    "active_runtime_rate": format_percent(active_count, len(rows)),
                    "avg_downgrade_trigger_count": format_float(
                        average(
                            safe_float(row.get("downgrade_trigger_count"))
                            for row in rows
                            if row.get("downgrade_trigger_count") is not None
                        ),
                        2,
                    ),
                    "avg_recovery_trigger_count": format_float(
                        average(
                            safe_float(row.get("recovery_trigger_count"))
                            for row in rows
                            if row.get("recovery_trigger_count") is not None
                        ),
                        2,
                    ),
                    "avg_frame_drop_rate": format_float(
                        average(
                            safe_float(row.get("frame_drop_rate"))
                            for row in rows
                            if row.get("frame_drop_rate") is not None
                        ),
                        3,
                    ),
                    "avg_total_ram_gb": format_float(
                        average(
                            safe_float(row.get("total_ram_gb"))
                            for row in rows
                            if row.get("total_ram_gb")
                        ),
                        2,
                    ),
                    "fallback_count": fallback_count,
                    "missing_total_ram_count": missing_total_ram_count,
                }
            )
        self.device_rows = sorted(
            device_rows,
            key=lambda row: (
                -safe_int(row.get("sample_count")) if row.get("sample_count") is not None else 0,
                row.get("platform") or "",
                row.get("device_model") or "",
            ),
        )

    def _build_flagged_rows(self) -> None:
        volatile_device_keys = {
            (row["platform"], row["device_model"])
            for row in self.device_rows
            if safe_int(row.get("sample_count")) is not None
            and safe_int(row.get("sample_count")) >= 2
            and safe_int(row.get("unique_tier_count")) is not None
            and safe_int(row.get("unique_tier_count")) >= 2
        }

        flagged_rows: list[dict[str, Any]] = []
        for row in self.session_rows:
            flags: list[str] = []
            if row.get("is_fallback") == "true":
                flags.append("fallback_decision")
            if not row.get("device_model"):
                flags.append("missing_device_model")
            if row.get("total_ram_bytes") is None:
                flags.append("missing_total_ram")
            if not row.get("runtime_status"):
                flags.append("missing_runtime_status")
            downgrade_count = safe_int(row.get("downgrade_trigger_count"))
            if downgrade_count is not None and downgrade_count >= 3:
                flags.append("frequent_runtime_downgrade")
            frame_drop_rate = safe_float(row.get("frame_drop_rate"))
            if frame_drop_rate is not None and frame_drop_rate >= 0.20:
                flags.append("high_frame_drop_rate")
            if safe_str(row.get("runtime_status")) in {"active", "cooldown"}:
                flags.append("runtime_pressure_observed")
            device_key = (
                row.get("platform") or "unknown",
                row.get("device_model") or "unknown",
            )
            if device_key in volatile_device_keys:
                flags.append("tier_variation_same_model")
            if not flags:
                continue
            flagged_rows.append(
                {
                    "source_ref": row.get("source_ref"),
                    "session_id": row.get("session_id"),
                    "platform": row.get("platform"),
                    "device_model": row.get("device_model"),
                    "tier": row.get("tier"),
                    "runtime_status": row.get("runtime_status"),
                    "downgrade_trigger_count": row.get("downgrade_trigger_count"),
                    "frame_drop_rate": row.get("frame_drop_rate"),
                    "flags": ", ".join(flags),
                    "reason_excerpt": trim_reason_excerpt(safe_str(row.get("reasons_json"))),
                }
            )
        self.flagged_rows = flagged_rows

    def _write_csv(
        self,
        path: Path,
        headers: list[str],
        rows: list[dict[str, Any]],
    ) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def _build_summary_markdown(self) -> str:
        session_count = len(self.session_rows)
        event_count = len(self.event_rows)
        issue_count = len(self.issues)
        fallback_count = sum(1 for row in self.session_rows if row.get("is_fallback") == "true")

        device_model_complete = sum(1 for row in self.session_rows if row.get("device_model"))
        ram_complete = sum(1 for row in self.session_rows if row.get("total_ram_bytes") is not None)
        runtime_complete = sum(1 for row in self.session_rows if row.get("runtime_status"))

        tier_counter = Counter(safe_str(row.get("tier")) or "missing" for row in self.session_rows)
        runtime_counter = Counter(
            safe_str(row.get("runtime_status")) or "missing" for row in self.session_rows
        )
        trigger_counter = Counter(
            safe_str(row.get("runtime_trigger_reason"))
            for row in self.session_rows
            if row.get("runtime_trigger_reason")
        )

        top_devices = self.device_rows[: self.top_n]
        top_flags = self.flagged_rows[: self.top_n]

        lines = [
            "# Diagnostics Summary",
            "",
            f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
            f"- Files scanned: {self.files_scanned}",
            f"- Session rows: {session_count}",
            f"- Structured log events: {event_count}",
            f"- Parse issues: {issue_count}",
            "",
            "## Data quality",
            "",
            f"- `deviceModel` completeness: {device_model_complete}/{session_count} ({format_percent(device_model_complete, session_count)})",
            f"- `totalRamBytes` completeness: {ram_complete}/{session_count} ({format_percent(ram_complete, session_count)})",
            f"- `runtimeObservation.status` completeness: {runtime_complete}/{session_count} ({format_percent(runtime_complete, session_count)})",
            f"- Fallback decisions: {fallback_count}",
            "",
            "## Tier distribution",
            "",
        ]

        if tier_counter:
            for key, value in tier_counter.most_common():
                lines.append(f"- `{key}`: {value}")
        else:
            lines.append("- No tier data found.")

        lines.extend(["", "## Runtime status distribution", ""])
        if runtime_counter:
            for key, value in runtime_counter.most_common():
                lines.append(f"- `{key}`: {value}")
        else:
            lines.append("- No runtime status data found.")

        lines.extend(["", "## Top runtime trigger reasons", ""])
        if trigger_counter:
            for key, value in trigger_counter.most_common(self.top_n):
                lines.append(f"- `{key}`: {value}")
        else:
            lines.append("- No runtime trigger reasons found.")

        lines.extend(["", "## Top device models", ""])
        if top_devices:
            for row in top_devices:
                lines.append(
                    "- "
                    f"`{row['platform']}` / `{row['device_model']}`: "
                    f"samples={row['sample_count']}, "
                    f"tiers={row['tier_distribution']}, "
                    f"runtime={row['runtime_status_distribution']}, "
                    f"activeRate={row['active_runtime_rate']}"
                )
        else:
            lines.append("- No device aggregates available.")

        lines.extend(["", "## Flagged sessions", ""])
        if top_flags:
            for row in top_flags:
                lines.append(
                    "- "
                    f"`{row['source_ref']}`: "
                    f"flags={row['flags']}, "
                    f"tier={row['tier']}, "
                    f"runtime={row['runtime_status']}, "
                    f"device={row['platform']}/{row['device_model']}"
                )
        else:
            lines.append("- No flagged sessions.")

        lines.extend(["", "## Recommended reading order", ""])
        lines.append("- `session_summary.csv`: inspect data quality, tier, and runtime status at the sample level.")
        lines.append("- `device_model_summary.csv`: inspect model-level concentration and stability.")
        lines.append("- `event_timeline.csv`: inspect trigger, transition, and session timing.")
        lines.append("- `flagged_sessions.csv`: inspect fallback samples, missing fields, and heavy downgrade cases.")
        lines.append("- `parse_issues.csv`: inspect malformed files or unsupported payloads.")
        return "\n".join(lines) + "\n"


def _maybe_dict_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return None


def discover_input_files(input_paths: Iterable[Path], output_dir: Path) -> list[Path]:
    files: list[Path] = []
    resolved_output = output_dir.resolve()
    for input_path in input_paths:
        resolved_input = input_path.resolve()
        if resolved_input.is_file():
            if resolved_input.suffix.lower() in SUPPORTED_SUFFIXES and not _is_within(
                resolved_input, resolved_output
            ):
                files.append(resolved_input)
            continue
        if not resolved_input.exists():
            continue
        for candidate in resolved_input.rglob("*"):
            if not candidate.is_file():
                continue
            if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue
            if _is_within(candidate.resolve(), resolved_output):
                continue
            files.append(candidate.resolve())
    return files


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def android_report_gate_issues(analyzer: DiagnosticsAnalyzer) -> list[str]:
    issues: list[str] = []
    if analyzer.issues:
        issues.append(f"parse_issues: {len(analyzer.issues)} parse issue(s) found.")

    non_performance_rows = [
        row
        for row in analyzer.session_rows
        if row.get("source_type") != "performance-report"
    ]
    for row in non_performance_rows:
        source_ref = safe_str(row.get("source_ref")) or "<unknown>"
        source_type = safe_str(row.get("source_type")) or "<missing>"
        issues.append(
            f"{source_ref}: unexpected session source_type={source_type}; "
            "android-report-gate inputs must be V1 performance reports only."
        )

    performance_rows = [
        row for row in analyzer.session_rows if row.get("source_type") == "performance-report"
    ]
    if not performance_rows:
        issues.append("no_performance_report: no performance-report session rows found.")
        return issues

    report_id_sources: dict[str, list[str]] = {}
    session_sequence_sources: dict[tuple[str, int], list[str]] = {}
    for row in performance_rows:
        source_ref = safe_str(row.get("source_ref")) or "<unknown>"
        report_id = safe_str(row.get("report_id"))
        if report_id:
            report_id_sources.setdefault(report_id, []).append(source_ref)
        session_id = safe_str(row.get("session_id"))
        report_sequence = safe_int(row.get("report_sequence"))
        if session_id and report_sequence is not None:
            session_sequence_sources.setdefault(
                (session_id, report_sequence),
                [],
            ).append(source_ref)
    for report_id, source_refs in report_id_sources.items():
        if len(source_refs) > 1:
            issues.append(
                f"duplicate_report_id: report_id={report_id} appears in "
                f"{len(source_refs)} performance reports: {', '.join(source_refs)}."
            )
    for (session_id, report_sequence), source_refs in session_sequence_sources.items():
        if len(source_refs) > 1:
            issues.append(
                "duplicate_report_sequence: "
                f"service_session_id={session_id} report_sequence={report_sequence} "
                f"appears in {len(source_refs)} performance reports: "
                f"{', '.join(source_refs)}."
            )

    for row in performance_rows:
        source_ref = safe_str(row.get("source_ref")) or "<unknown>"
        if row.get("schema_name") != PERFORMANCE_REPORT_SCHEMA_NAME:
            issues.append(
                f"{source_ref}: expected schema_name={PERFORMANCE_REPORT_SCHEMA_NAME}, "
                f"got {safe_str(row.get('schema_name')) or '<missing>'}."
            )
        schema_version_raw = row.get("_schema_version_raw")
        if (
            isinstance(schema_version_raw, bool)
            or not isinstance(schema_version_raw, int)
            or schema_version_raw != 1
        ):
            issues.append(
                f"{source_ref}: expected schema_version=1, "
                f"got {gate_value_text(schema_version_raw)}."
            )
        if row.get("report_status") != "ok":
            issues.append(
                f"{source_ref}: expected report_status=ok, "
                f"got {safe_str(row.get('report_status')) or '<missing>'}."
            )
        for field in ANDROID_REPORT_GATE_REQUIRED_FIELDS:
            if row.get(field) in (None, ""):
                issues.append(f"{source_ref}: missing required field {field}.")
        for field, row_key, raw_key in (
            ("report_id", "report_id", "_report_id_raw"),
            ("report_source", "report_source", "_report_source_raw"),
            ("session_id", "session_id", "_service_session_id_raw"),
            ("device_model", "device_model", "_device_model_raw"),
            ("os_version", "os_version", "_os_version_raw"),
        ):
            raw_value = row.get(raw_key)
            if row.get(row_key) not in (None, "") and not is_non_empty_json_string(
                raw_value
            ):
                issues.append(
                    f"{source_ref}: expected {field} to be a non-empty JSON string, "
                    f"got {gate_value_text(raw_value)}."
                )
        for field, raw_key in (
            ("generated_at", "_generated_at_raw"),
            ("decided_at", "_decided_at_raw"),
        ):
            raw_value = row.get(raw_key)
            if row.get(field) not in (None, "") and not is_non_empty_json_string(
                raw_value
            ):
                issues.append(
                    f"{source_ref}: expected {field} to be a non-empty JSON string, "
                    f"got {gate_value_text(raw_value)}."
                )
        for field in ("generated_at", "decided_at"):
            if row.get(field) not in (None, "") and not is_iso_datetime(row.get(field)):
                issues.append(
                    f"{source_ref}: expected {field} to be an ISO-8601 timestamp, "
                    f"got {safe_str(row.get(field))}."
                )
        if row.get("generated_at") not in (None, "") and not is_utc_iso_datetime(
            row.get("generated_at")
        ):
            issues.append(
                f"{source_ref}: expected generated_at to be an ISO-8601 UTC timestamp, "
                f"got {safe_str(row.get('generated_at'))}."
            )
        generated_at = parse_iso_datetime(row.get("generated_at"))
        decided_at = parse_iso_datetime(row.get("decided_at"))
        if (
            generated_at is not None
            and decided_at is not None
            and generated_at.tzinfo is not None
            and decided_at.tzinfo is not None
            and generated_at < decided_at
        ):
            issues.append(
                f"{source_ref}: expected generated_at to be at or after decided_at, "
                f"got generated_at={safe_str(row.get('generated_at'))} "
                f"decided_at={safe_str(row.get('decided_at'))}."
            )
        for field, row_key, raw_key in (
            ("tier", "tier", "_tier_raw"),
            ("confidence", "confidence", "_confidence_raw"),
            ("runtime_status", "runtime_status", "_runtime_status_raw"),
            ("platform", "platform", "_platform_raw"),
            (
                "memory_pressure_state",
                "memory_pressure_state",
                "_memory_pressure_state_raw",
            ),
        ):
            raw_value = row.get(raw_key)
            if row.get(row_key) not in (None, "") and not is_non_empty_json_string(
                raw_value
            ):
                issues.append(
                    f"{source_ref}: expected {field} to be a non-empty JSON string, "
                    f"got {gate_value_text(raw_value)}."
                )
        if row.get("tier") and row.get("tier") not in ANDROID_REPORT_GATE_TIERS:
            issues.append(
                f"{source_ref}: unexpected tier={safe_str(row.get('tier'))}."
            )
        if (
            row.get("confidence")
            and row.get("confidence") not in ANDROID_REPORT_GATE_CONFIDENCES
        ):
            issues.append(
                f"{source_ref}: unexpected confidence={safe_str(row.get('confidence'))}."
            )
        if (
            row.get("runtime_status")
            and row.get("runtime_status") not in ANDROID_REPORT_GATE_RUNTIME_STATUSES
        ):
            issues.append(
                f"{source_ref}: unexpected runtime_status={safe_str(row.get('runtime_status'))}."
            )
        for field, raw_key in (
            ("report_sequence", "_report_sequence_raw"),
            ("total_ram_bytes", "_total_ram_bytes_raw"),
            ("sdk_int", "_sdk_int_raw"),
            ("memory_pressure_level", "_memory_pressure_level_raw"),
        ):
            raw_value = row.get(raw_key)
            if raw_value is not None and not is_json_int(raw_value):
                issues.append(
                    f"{source_ref}: expected {field} to be a JSON integer, "
                    f"got {gate_value_text(raw_value)}."
                )
        for field, raw_key in (
            ("is_low_ram_device", "_is_low_ram_device_raw"),
            ("is_low_power_mode_enabled", "_is_low_power_mode_enabled_raw"),
        ):
            raw_value = row.get(raw_key)
            if raw_value is not None and not is_json_bool(raw_value):
                issues.append(
                    f"{source_ref}: expected {field} to be a JSON boolean, "
                    f"got {gate_value_text(raw_value)}."
                )
        total_ram_bytes = safe_int(row.get("total_ram_bytes"))
        report_sequence = safe_int(row.get("report_sequence"))
        if report_sequence is not None and report_sequence <= 0:
            issues.append(
                f"{source_ref}: expected report_sequence to be greater than 0, got {report_sequence}."
            )
        report_id = safe_str(row.get("report_id"))
        session_id = safe_str(row.get("session_id"))
        if report_id and session_id and report_sequence is not None:
            expected_report_id = f"{session_id}-report-{report_sequence}"
            if report_id != expected_report_id:
                issues.append(
                    f"{source_ref}: expected report_id={expected_report_id} "
                    f"from service session and report_sequence, got {report_id}."
                )
        if total_ram_bytes is not None and total_ram_bytes <= 0:
            issues.append(
                f"{source_ref}: expected total_ram_bytes to be greater than 0, got {total_ram_bytes}."
            )
        if row.get("platform") and row.get("platform") != "android":
            issues.append(
                f"{source_ref}: expected platform=android, got {safe_str(row.get('platform'))}."
            )
        sdk_int = safe_int(row.get("sdk_int"))
        if sdk_int is not None and sdk_int <= 0:
            issues.append(f"{source_ref}: expected sdk_int to be greater than 0, got {sdk_int}.")
        memory_pressure_state = safe_str(row.get("memory_pressure_state"))
        if (
            memory_pressure_state
            and memory_pressure_state not in ANDROID_REPORT_GATE_MEMORY_PRESSURE_STATES
        ):
            issues.append(
                f"{source_ref}: unexpected memory_pressure_state={memory_pressure_state}."
            )
        memory_pressure_level = safe_int(row.get("memory_pressure_level"))
        if (
            memory_pressure_level is not None
            and memory_pressure_level not in ANDROID_REPORT_GATE_MEMORY_PRESSURE_LEVELS
        ):
            issues.append(
                f"{source_ref}: unexpected memory_pressure_level={memory_pressure_level}."
            )
        if sdk_int is not None and sdk_int >= 29:
            for field in ("thermal_state", "thermal_state_level"):
                if row.get(field) in (None, ""):
                    issues.append(
                        f"{source_ref}: missing required field {field} for Android SDK {sdk_int}."
                    )
            thermal_state = safe_str(row.get("thermal_state"))
            thermal_state_raw = row.get("_thermal_state_raw")
            if thermal_state and not is_non_empty_json_string(thermal_state_raw):
                issues.append(
                    f"{source_ref}: expected thermal_state to be a non-empty JSON string, "
                    f"got {gate_value_text(thermal_state_raw)}."
                )
            if thermal_state and thermal_state not in ANDROID_REPORT_GATE_THERMAL_STATES:
                issues.append(f"{source_ref}: unexpected thermal_state={thermal_state}.")
            thermal_state_level_raw = row.get("_thermal_state_level_raw")
            if (
                thermal_state_level_raw is not None
                and not is_json_int(thermal_state_level_raw)
            ):
                issues.append(
                    f"{source_ref}: expected thermal_state_level to be a JSON integer, "
                    f"got {gate_value_text(thermal_state_level_raw)}."
                )
            thermal_state_level = safe_int(row.get("thermal_state_level"))
            if (
                thermal_state_level is not None
                and thermal_state_level not in ANDROID_REPORT_GATE_THERMAL_LEVELS
            ):
                issues.append(
                    f"{source_ref}: unexpected thermal_state_level={thermal_state_level}."
                )
        if row.get("is_fallback") == "true":
            issues.append(f"{source_ref}: fallback decision observed.")

    return issues


def android_report_gate_status(issues: list[str]) -> str:
    return ANDROID_REPORT_GATE_PASS_STATUS if not issues else ANDROID_REPORT_GATE_FAIL_STATUS


def write_android_report_gate(
    output_dir: Path,
    analyzer: DiagnosticsAnalyzer,
    issues: list[str],
) -> None:
    performance_rows = [
        row for row in analyzer.session_rows if row.get("source_type") == "performance-report"
    ]
    performance_count = len(performance_rows)
    status = android_report_gate_status(issues)
    summary_values = {
        ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD: status,
        ANDROID_REPORT_GATE_SUMMARY_ISSUE_COUNT_FIELD: str(len(issues)),
        ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD: str(analyzer.files_scanned),
        ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD: str(performance_count),
        ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD: str(len(analyzer.session_rows)),
        ANDROID_REPORT_GATE_SUMMARY_PARSE_ISSUES_FIELD: str(len(analyzer.issues)),
    }
    lines = [
        "# Android Report Gate",
        "",
        *[
            f"- {label}: {summary_values[summary_key]}"
            for label, summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
        ],
        "",
        ANDROID_REPORT_GATE_SUMMARY_HEADING,
        "",
        ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START,
        *[
            f"{field}={summary_values[field]}"
            for field in ANDROID_REPORT_GATE_SUMMARY_FIELDS
        ],
        ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END,
        "",
        ANDROID_REPORT_GATE_CHECKS_HEADING,
        "",
        *ANDROID_REPORT_GATE_CHECK_LINES,
        "",
        ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
        "",
    ]
    if performance_rows:
        lines.extend(
            [
                _markdown_table_header(
                    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
                ),
                _markdown_table_divider(
                    ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS,
                ),
            ]
        )
        for row in performance_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(row.get("source_ref")),
                        markdown_cell(row.get("report_id")),
                        markdown_cell(row.get("report_source")),
                        markdown_cell(row.get("session_id")),
                        markdown_cell(row.get("report_sequence")),
                        markdown_cell(row.get("tier")),
                        markdown_cell(row.get("confidence")),
                        markdown_cell(row.get("runtime_status")),
                        markdown_cell(row.get("generated_at")),
                        markdown_cell(row.get("decided_at")),
                    ]
                )
                + " |"
            )
        lines.extend(
            [
                "",
                ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
                "",
                _markdown_table_header(
                    ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS,
                ),
                _markdown_table_divider(
                    ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS,
                ),
            ]
        )
        for row in performance_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(row.get("report_id")),
                        markdown_cell(row.get("platform")),
                        markdown_cell(row.get("device_model")),
                        markdown_cell(row.get("os_version")),
                        markdown_cell(row.get("sdk_int")),
                        markdown_cell(row.get("total_ram_bytes")),
                        markdown_cell(row.get("is_low_ram_device")),
                        markdown_cell(row.get("is_low_power_mode_enabled")),
                        markdown_cell(row.get("memory_pressure_state")),
                        markdown_cell(row.get("memory_pressure_level")),
                        markdown_cell(row.get("thermal_state")),
                        markdown_cell(row.get("thermal_state_level")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("- No performance report rows.")
    lines.extend(
        [
            "",
            ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
            "",
        ]
    )
    if performance_rows:
        for row in performance_rows:
            lines.extend(_android_report_field_check_lines(row))
    else:
        lines.append("- No performance report rows.")
    lines.extend(
        [
            "",
            ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
            "",
        ]
    )
    lines.extend(_android_report_identity_checklist_lines(analyzer, performance_rows))
    lines.extend(
        [
            "",
            ANDROID_REPORT_GATE_ISSUES_HEADING,
            "",
        ]
    )
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append(ANDROID_REPORT_GATE_NO_ISSUES_LINE)
    (output_dir / ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME).write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _android_report_field_check_lines(row: dict[str, Any]) -> list[str]:
    values = [
        row.get("schema_name"),
        row.get("schema_version"),
        row.get("report_id"),
        row.get("generated_at"),
        row.get("report_source"),
        row.get("session_id"),
        row.get("report_sequence"),
        row.get("tier"),
        row.get("confidence"),
        row.get("decided_at"),
        row.get("platform"),
        row.get("device_model"),
        row.get("os_version"),
        row.get("total_ram_bytes"),
        row.get("is_low_ram_device"),
        row.get("sdk_int"),
        row.get("thermal_state"),
        row.get("thermal_state_level"),
        row.get("is_low_power_mode_enabled"),
        row.get("memory_pressure_state"),
        row.get("memory_pressure_level"),
        row.get("runtime_status"),
    ]
    return [
        f"### {markdown_inline(row.get('report_id')) or 'Report'}",
        "",
        *[
            f"- {label}: {markdown_inline(value)}"
            for label, value in zip(ANDROID_REPORT_GATE_FIELD_CHECK_LABELS, values)
        ],
        "",
    ]


def _markdown_table_header(columns: list[str]) -> str:
    return "| " + " | ".join(columns) + " |"


def _markdown_table_divider(columns: list[str]) -> str:
    return "| " + " | ".join("---" for _ in columns) + " |"


def _android_report_identity_checklist_lines(
    analyzer: DiagnosticsAnalyzer,
    performance_rows: list[dict[str, Any]],
) -> list[str]:
    def yes_no(value: bool) -> str:
        return "yes" if value else "no"

    def all_performance_rows(predicate: Any) -> bool:
        return bool(performance_rows) and all(predicate(row) for row in performance_rows)

    schema_version_ok = all_performance_rows(
        lambda row: row.get("_schema_version_raw") == 1,
    )
    generated_at_ok = all_performance_rows(
        lambda row: is_utc_iso_datetime(row.get("_generated_at_raw")),
    )
    decided_at_ok = all_performance_rows(
        lambda row: is_iso_datetime(row.get("_decided_at_raw")),
    )
    timestamp_order_ok = all_performance_rows(_generated_at_not_before_decided_at)
    service_session_ok = all_performance_rows(
        lambda row: is_non_empty_json_string(row.get("_service_session_id_raw")),
    )
    report_sequence_ok = all_performance_rows(
        lambda row: is_json_int(row.get("_report_sequence_raw"))
        and row.get("_report_sequence_raw") > 0,
    )
    report_id_match_ok = all_performance_rows(_report_id_matches_session_sequence)
    report_ids = [
        row.get("report_id")
        for row in performance_rows
        if is_non_empty_json_string(row.get("_report_id_raw"))
    ]
    service_sequences = [
        (row.get("session_id"), row.get("report_sequence"))
        for row in performance_rows
        if row.get("session_id") and row.get("report_sequence") is not None
    ]
    unique_report_ids_ok = bool(performance_rows) and len(report_ids) == len(set(report_ids))
    unique_service_sequence_ok = bool(performance_rows) and len(service_sequences) == len(
        set(service_sequences)
    )
    pure_gate_input_ok = (
        bool(performance_rows)
        and not analyzer.issues
        and all(
            row.get("source_type") == "performance-report"
            for row in analyzer.session_rows
        )
    )

    checks = [
        schema_version_ok,
        generated_at_ok,
        decided_at_ok,
        timestamp_order_ok,
        service_session_ok,
        report_sequence_ok,
        report_id_match_ok,
        unique_report_ids_ok,
        unique_service_sequence_ok,
        pure_gate_input_ok,
    ]
    return [
        f"- {label}: {yes_no(check)}"
        for label, check in zip(IDENTITY_CHECKLIST_LABELS, checks)
    ]


def _generated_at_not_before_decided_at(row: dict[str, Any]) -> bool:
    generated_at = parse_iso_datetime(row.get("_generated_at_raw"))
    decided_at = parse_iso_datetime(row.get("_decided_at_raw"))
    if generated_at is None or decided_at is None:
        return False
    if generated_at.tzinfo is None or decided_at.tzinfo is None:
        return True
    return generated_at >= decided_at


def _report_id_matches_session_sequence(row: dict[str, Any]) -> bool:
    report_id = row.get("report_id")
    session_id = row.get("session_id")
    report_sequence = row.get("report_sequence")
    if not report_id or not session_id or report_sequence is None:
        return False
    return report_id == f"{session_id}-report-{report_sequence}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Flutter performance tier diagnostics JSON and structured logs."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input file or directory. Supports .json/.jsonl/.ndjson/.log/.txt",
    )
    parser.add_argument(
        "--output",
        default="build/diagnostics_analysis",
        help="Output directory for CSV and Markdown files.",
    )
    parser.add_argument(
        "--prefix",
        default="PERF_TIER_LOG",
        help="Structured log prefix used in text logs.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Top-N rows to include in the Markdown summary sections.",
    )
    parser.add_argument(
        "--android-report-gate",
        action="store_true",
        help=(
            "Return non-zero unless inputs contain at least one valid V1 Android "
            "PerformanceReport with required report, decision, runtime, and "
            "device signal fields."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output).resolve()
    files = discover_input_files((Path(item) for item in args.inputs), output_dir)
    if not files:
        print("No supported input files found.")
        return 1

    analyzer = DiagnosticsAnalyzer(prefix=args.prefix, top_n=max(args.top, 1))
    analyzer.ingest_files(files)
    analyzer.write_outputs(output_dir)
    gate_issues: list[str] = []
    if args.android_report_gate:
        gate_issues = android_report_gate_issues(analyzer)
        write_android_report_gate(output_dir, analyzer, gate_issues)
        gate_status = android_report_gate_status(gate_issues)

    print(f"Analyzed {analyzer.files_scanned} files.")
    print(f"Session rows: {len(analyzer.session_rows)}")
    print(f"Structured log events: {len(analyzer.event_rows)}")
    print(f"Parse issues: {len(analyzer.issues)}")
    if args.android_report_gate:
        print(
            "Android report gate: "
            f"{gate_status}"
            f" ({len(gate_issues)} issue(s))"
        )
    print(f"Output directory: {output_dir}")
    if gate_issues:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

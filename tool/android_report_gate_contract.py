"""Shared Android report gate contract text.

Keep analyzer output, evidence builder checks, and evidence validator checks
bound to the same literals so readiness evidence cannot drift by copy/paste.
"""

from __future__ import annotations


PERFORMANCE_REPORT_SCHEMA_NAME = "flutter_performance_tier.performance_report"

ANDROID_REPORT_GATE_MARKDOWN_FILE_NAME = "android_report_gate.md"
ANDROID_REPORT_GATE_SUMMARY_HEADING = "## Gate Summary"
ANDROID_REPORT_GATE_CHECKS_HEADING = "## Checks"
ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING = "## Performance Reports"
ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING = "## Android Signals"
ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING = "## Report Field Check"
ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING = "## Identity And Gate Checklist"
ANDROID_REPORT_GATE_ISSUES_HEADING = "## Issues"
ANDROID_REPORT_GATE_NO_ISSUES_LINE = "- None."
ANDROID_REPORT_GATE_PASS_STATUS = "PASS"
ANDROID_REPORT_GATE_FAIL_STATUS = "FAIL"
ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD = "status"
ANDROID_REPORT_GATE_SUMMARY_ISSUE_COUNT_FIELD = "issueCount"
ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD = "filesScanned"
ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD = "performanceReportRows"
ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD = "sessionRows"
ANDROID_REPORT_GATE_SUMMARY_PARSE_ISSUES_FIELD = "parseIssues"
ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_START = "```text"
ANDROID_REPORT_GATE_SUMMARY_CODE_FENCE_END = "```"

ANDROID_REPORT_GATE_SUMMARY_FIELDS = [
    ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_ISSUE_COUNT_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_PARSE_ISSUES_FIELD,
]

ANDROID_REPORT_GATE_PASS_SUMMARY_VALUES = {
    ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD: ANDROID_REPORT_GATE_PASS_STATUS,
    ANDROID_REPORT_GATE_SUMMARY_ISSUE_COUNT_FIELD: "0",
    ANDROID_REPORT_GATE_SUMMARY_PARSE_ISSUES_FIELD: "0",
}

ANDROID_REPORT_GATE_POSITIVE_SUMMARY_FIELDS = [
    ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD,
    ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD,
]

ANDROID_REPORT_GATE_SINGLE_REPORT_SUMMARY_VALUES = {
    **ANDROID_REPORT_GATE_PASS_SUMMARY_VALUES,
    ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD: "1",
    ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD: "1",
    ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD: "1",
}

ANDROID_REPORT_GATE_HEADER_FIELDS = [
    ("Status", ANDROID_REPORT_GATE_SUMMARY_STATUS_FIELD, "status"),
    ("Files scanned", ANDROID_REPORT_GATE_SUMMARY_FILES_SCANNED_FIELD, "files_scanned"),
    (
        "Performance report rows",
        ANDROID_REPORT_GATE_SUMMARY_PERFORMANCE_ROWS_FIELD,
        "performance_report_rows",
    ),
    ("Session rows", ANDROID_REPORT_GATE_SUMMARY_SESSION_ROWS_FIELD, "session_rows"),
    ("Parse issues", ANDROID_REPORT_GATE_SUMMARY_PARSE_ISSUES_FIELD, "parse_issues"),
]

ANDROID_REPORT_GATE_SINGLE_REPORT_HEADER_VALUES = {
    label: ANDROID_REPORT_GATE_SINGLE_REPORT_SUMMARY_VALUES[summary_key]
    for label, summary_key, _issue_key in ANDROID_REPORT_GATE_HEADER_FIELDS
}

ANDROID_REPORT_GATE_SECTION_HEADINGS = [
    ANDROID_REPORT_GATE_SUMMARY_HEADING,
    ANDROID_REPORT_GATE_CHECKS_HEADING,
    ANDROID_REPORT_GATE_PERFORMANCE_REPORTS_HEADING,
    ANDROID_REPORT_GATE_ANDROID_SIGNALS_HEADING,
    ANDROID_REPORT_GATE_REPORT_FIELD_CHECK_HEADING,
    ANDROID_REPORT_GATE_IDENTITY_CHECKLIST_HEADING,
    ANDROID_REPORT_GATE_ISSUES_HEADING,
]

ANDROID_REPORT_GATE_PERFORMANCE_REPORT_COLUMNS = [
    "Source",
    "Report ID",
    "Source Tag",
    "Session",
    "Sequence",
    "Tier",
    "Confidence",
    "Runtime",
    "Generated At",
    "Decided At",
]

ANDROID_REPORT_GATE_ANDROID_SIGNAL_COLUMNS = [
    "Report ID",
    "Platform",
    "Device",
    "OS Version",
    "SDK",
    "RAM bytes",
    "Low RAM",
    "Low Power",
    "Memory Pressure",
    "Memory Level",
    "Thermal",
    "Thermal Level",
]

ANDROID_REPORT_GATE_REQUIRED_FIELD_LABELS = [
    "`schemaName`",
    "`schemaVersion`",
    "`reportId`",
    "`generatedAt`",
    "`source`",
    "`metadata.serviceSessionId`",
    "`metadata.reportSequence`",
    "`decision.tier`",
    "`decision.confidence`",
    "`decision.decidedAt`",
    "`decision.deviceSignals.platform`",
    "`decision.deviceSignals.deviceModel`",
    "`decision.deviceSignals.osVersion`",
    "`decision.deviceSignals.totalRamBytes`",
    "`decision.deviceSignals.isLowRamDevice`",
    "`decision.deviceSignals.sdkInt`",
    "`decision.deviceSignals.isLowPowerModeEnabled`",
    "`decision.deviceSignals.memoryPressureState`",
    "`decision.deviceSignals.memoryPressureLevel`",
    "`decision.runtimeObservation.status`",
]

ANDROID_REPORT_GATE_PRESENT_FIELD_LABELS = [
    "`decision.deviceSignals.thermalState`",
    "`decision.deviceSignals.thermalStateLevel`",
]

ANDROID_REPORT_GATE_FIELD_CHECK_LABELS = [
    *ANDROID_REPORT_GATE_REQUIRED_FIELD_LABELS[:16],
    *ANDROID_REPORT_GATE_PRESENT_FIELD_LABELS,
    *ANDROID_REPORT_GATE_REQUIRED_FIELD_LABELS[16:],
]

IDENTITY_CHECKLIST_LABELS = [
    "`schemaVersion` is JSON integer `1`",
    "`generatedAt` is UTC ISO-8601 timestamp",
    "`decision.decidedAt` is ISO-8601 timestamp",
    "`generatedAt` is at or after `decision.decidedAt`",
    "`metadata.serviceSessionId` is a non-empty JSON string",
    "`metadata.reportSequence` is a positive JSON integer",
    "`reportId` equals `<metadata.serviceSessionId>-report-<metadata.reportSequence>`",
    "Gate input contains no duplicate `reportId`",
    "Gate input contains no duplicate `serviceSessionId + reportSequence`",
    "Gate input contains only V1 performance reports, not legacy AI diagnostics or structured logs",
]

ANDROID_REPORT_GATE_CHECK_LINES = [
    f"- At least one V1 `{PERFORMANCE_REPORT_SCHEMA_NAME}` row.",
    "- No parse issues.",
    "- No non-performance-report session rows in the gate input.",
    "- `schemaVersion` is JSON integer `1`.",
    "- Report identity, service session, device model, OS version, `generatedAt`, and `decision.decidedAt` are non-empty JSON strings.",
    "- `metadata.reportSequence` is a positive JSON integer.",
    "- Report id matches `<serviceSessionId>-report-<reportSequence>`.",
    "- Report id and service session/report sequence pairs are unique within the gate input.",
    "- Top-level `generatedAt` is an ISO-8601 UTC timestamp and `decision.decidedAt` is an ISO-8601 timestamp.",
    "- Required report, session, tier, runtime, and Android signal fields are present.",
    "- Tier, confidence, runtime status, platform, memory pressure, and thermal wire values are JSON strings in expected ranges.",
    "- RAM, SDK, memory pressure level, and SDK 29+ thermal level are JSON integers in expected ranges.",
    "- Low-RAM and low-power Android signals are JSON booleans.",
    "- Android SDK 29+ reports include thermal state and thermal state level.",
    "- Report platform is `android` and the decision is not a fallback.",
]

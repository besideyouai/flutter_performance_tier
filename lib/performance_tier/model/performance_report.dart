import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'tier_decision.dart';

@immutable
class PerformanceReport {
  PerformanceReport({
    required this.reportId,
    required this.generatedAt,
    required this.source,
    required this.decision,
    Map<String, Object?> metadata = const <String, Object?>{},
    this.schemaName = schemaNameV1,
    this.schemaVersion = currentSchemaVersion,
  }) : metadata = Map<String, Object?>.unmodifiable(metadata);

  factory PerformanceReport.fromDecision({
    required TierDecision decision,
    DateTime? generatedAt,
    String source = defaultSource,
    Map<String, Object?> metadata = const <String, Object?>{},
    String? reportId,
  }) {
    final resolvedGeneratedAt = (generatedAt ?? DateTime.now()).toUtc();
    return PerformanceReport(
      reportId: reportId ?? _buildReportId(resolvedGeneratedAt),
      generatedAt: resolvedGeneratedAt,
      source: source,
      decision: decision,
      metadata: metadata,
    );
  }

  static const String schemaNameV1 =
      'flutter_performance_tier.performance_report';
  static const int currentSchemaVersion = 1;
  static const String defaultSource = 'DefaultPerformanceTierService';

  final String schemaName;
  final int schemaVersion;
  final String reportId;
  final DateTime generatedAt;
  final String source;
  final TierDecision decision;
  final Map<String, Object?> metadata;

  String get defaultFileName {
    final timestamp = _compactUtcTimestamp(generatedAt);
    final safeReportId = _safeFileToken(reportId);
    return 'performance_tier_v$schemaVersion'
        '_${timestamp}_$safeReportId.json';
  }

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'schemaName': schemaName,
      'schemaVersion': schemaVersion,
      'reportId': reportId,
      'generatedAt': generatedAt.toUtc().toIso8601String(),
      'source': source,
      'decision': decision.toMap(),
      'metadata': metadata,
    };
  }

  String toJson() {
    return jsonEncode(toMap());
  }

  static String _buildReportId(DateTime generatedAt) {
    return 'report-${generatedAt.toUtc().microsecondsSinceEpoch}';
  }

  static String _compactUtcTimestamp(DateTime value) {
    final utc = value.toUtc();
    return '${_fourDigits(utc.year)}'
        '${_twoDigits(utc.month)}'
        '${_twoDigits(utc.day)}T'
        '${_twoDigits(utc.hour)}'
        '${_twoDigits(utc.minute)}'
        '${_twoDigits(utc.second)}'
        '${_threeDigits(utc.millisecond)}Z';
  }

  static String _safeFileToken(String value) {
    final buffer = StringBuffer();
    for (final codeUnit in value.codeUnits) {
      final char = String.fromCharCode(codeUnit);
      final isLower = codeUnit >= 97 && codeUnit <= 122;
      final isUpper = codeUnit >= 65 && codeUnit <= 90;
      final isDigit = codeUnit >= 48 && codeUnit <= 57;
      if (isLower || isUpper || isDigit || char == '-' || char == '_') {
        buffer.write(char);
      } else {
        buffer.write('-');
      }
    }
    final token = buffer.toString().replaceAll(RegExp('-+'), '-');
    return token.isEmpty ? 'report' : token;
  }

  static String _fourDigits(int value) => value.toString().padLeft(4, '0');

  static String _twoDigits(int value) => value.toString().padLeft(2, '0');

  static String _threeDigits(int value) => value.toString().padLeft(3, '0');
}

@immutable
class PerformanceReportWriteResult {
  const PerformanceReportWriteResult({
    required this.reportId,
    required this.fileName,
    required this.relativePath,
    required this.bytes,
    this.absolutePath,
    this.writtenAt,
  });

  factory PerformanceReportWriteResult.fromMap(
    Map<String, dynamic> map, {
    required String reportId,
  }) {
    return PerformanceReportWriteResult(
      reportId: _asString(map['reportId']) ?? reportId,
      fileName: _requiredString(map, 'fileName'),
      relativePath: _requiredString(map, 'relativePath'),
      absolutePath: _asString(map['absolutePath']),
      bytes: _requiredInt(map, 'bytes'),
      writtenAt:
          _asEpochMillisDateTime(map['writtenAtEpochMs']) ??
          _asIsoDateTime(map['writtenAt']),
    );
  }

  final String reportId;
  final String fileName;
  final String relativePath;
  final String? absolutePath;
  final int bytes;
  final DateTime? writtenAt;

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'reportId': reportId,
      'fileName': fileName,
      'relativePath': relativePath,
      'absolutePath': absolutePath,
      'bytes': bytes,
      'writtenAt': writtenAt?.toIso8601String(),
      'writtenAtEpochMs': writtenAt?.millisecondsSinceEpoch,
    };
  }
}

@immutable
class PerformanceReportFile {
  const PerformanceReportFile({
    required this.fileName,
    required this.relativePath,
    required this.bytes,
    this.absolutePath,
    this.modifiedAt,
  });

  factory PerformanceReportFile.fromMap(Map<String, dynamic> map) {
    return PerformanceReportFile(
      fileName: _requiredString(map, 'fileName'),
      relativePath: _requiredString(map, 'relativePath'),
      absolutePath: _asString(map['absolutePath']),
      bytes: _requiredInt(map, 'bytes'),
      modifiedAt:
          _asEpochMillisDateTime(map['modifiedAtEpochMs']) ??
          _asIsoDateTime(map['modifiedAt']),
    );
  }

  final String fileName;
  final String relativePath;
  final String? absolutePath;
  final int bytes;
  final DateTime? modifiedAt;

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'fileName': fileName,
      'relativePath': relativePath,
      'absolutePath': absolutePath,
      'bytes': bytes,
      'modifiedAt': modifiedAt?.toIso8601String(),
      'modifiedAtEpochMs': modifiedAt?.millisecondsSinceEpoch,
    };
  }
}

String _requiredString(Map<String, dynamic> map, String key) {
  final value = _asString(map[key]);
  if (value != null) {
    return value;
  }
  throw FormatException('Performance report native result missing "$key".');
}

int _requiredInt(Map<String, dynamic> map, String key) {
  final value = _asInt(map[key]);
  if (value != null) {
    return value;
  }
  throw FormatException('Performance report native result missing "$key".');
}

String? _asString(Object? value) {
  if (value is String && value.isNotEmpty) {
    return value;
  }
  return null;
}

int? _asInt(Object? value) {
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.toInt();
  }
  if (value is String) {
    return int.tryParse(value);
  }
  return null;
}

DateTime? _asEpochMillisDateTime(Object? value) {
  final epochMillis = _asInt(value);
  if (epochMillis == null) {
    return null;
  }
  return DateTime.fromMillisecondsSinceEpoch(epochMillis, isUtc: true);
}

DateTime? _asIsoDateTime(Object? value) {
  final text = _asString(value);
  if (text == null) {
    return null;
  }
  return DateTime.tryParse(text)?.toUtc();
}

import 'dart:convert';

import 'package:flutter/foundation.dart';

import 'tier_decision.dart';

/// Versioned report payload used by the Android device-to-host report loop.
@immutable
class PerformanceReport {
  PerformanceReport({
    required String reportId,
    required DateTime generatedAt,
    required String source,
    required this.decision,
    Map<String, Object?> metadata = const <String, Object?>{},
    String schemaName = schemaNameV1,
    int schemaVersion = currentSchemaVersion,
  }) : schemaName = _requiredSchemaName(schemaName),
       schemaVersion = _requiredSchemaVersion(schemaVersion),
       reportId = _requiredNonBlankString(reportId, 'reportId'),
       generatedAt = _validatedGeneratedAt(generatedAt, decision),
       source = _requiredNonBlankString(source, 'source'),
       metadata = Map<String, Object?>.unmodifiable(
         _validatedMetadata(metadata, reportId),
       );

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

  /// Builds the default service-owned report id for a session and sequence.
  ///
  /// This is the identity shape expected by the default service, report model
  /// metadata validation, and Android report gate.
  static String buildServiceReportId({
    required String serviceSessionId,
    required int reportSequence,
  }) {
    final sessionId = _requiredNonBlankString(
      serviceSessionId,
      'serviceSessionId',
    );
    final sequence = _requiredPositiveReportSequence(reportSequence);
    return '$sessionId-report-$sequence';
  }

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

/// Native or backing-store metadata returned after a report write.
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
      bytes: _requiredPositiveInt(map, 'bytes'),
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

/// Metadata for a report file that can be pulled from the backing store.
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
      bytes: _requiredPositiveInt(map, 'bytes'),
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

int _requiredPositiveInt(Map<String, dynamic> map, String key) {
  final value = _asInt(map[key]);
  if (value != null && value > 0) {
    return value;
  }
  throw FormatException(
    'Performance report native result missing positive integer "$key".',
  );
}

String _requiredNonBlankString(String value, String fieldName) {
  if (value.trim().isNotEmpty) {
    return value;
  }
  throw ArgumentError.value(value, fieldName, 'Must be a non-empty string.');
}

String _requiredSchemaName(String value) {
  if (value == PerformanceReport.schemaNameV1) {
    return value;
  }
  throw ArgumentError.value(
    value,
    'schemaName',
    'Must be ${PerformanceReport.schemaNameV1}.',
  );
}

int _requiredSchemaVersion(int value) {
  if (value == PerformanceReport.currentSchemaVersion) {
    return value;
  }
  throw ArgumentError.value(
    value,
    'schemaVersion',
    'Must be ${PerformanceReport.currentSchemaVersion}.',
  );
}

DateTime _validatedGeneratedAt(DateTime generatedAt, TierDecision decision) {
  final utcGeneratedAt = generatedAt.toUtc();
  final utcDecidedAt = decision.decidedAt.toUtc();
  if (utcGeneratedAt.isBefore(utcDecidedAt)) {
    throw ArgumentError.value(
      generatedAt,
      'generatedAt',
      'Must be at or after decision.decidedAt.',
    );
  }
  return utcGeneratedAt;
}

Map<String, Object?> _validatedMetadata(
  Map<String, Object?> metadata,
  String reportId,
) {
  final hasServiceSessionId = metadata.containsKey('serviceSessionId');
  final hasReportSequence = metadata.containsKey('reportSequence');
  if (!hasServiceSessionId && !hasReportSequence) {
    return metadata;
  }
  final serviceSessionId = metadata['serviceSessionId'];
  if (serviceSessionId is! String || serviceSessionId.trim().isEmpty) {
    throw ArgumentError.value(
      serviceSessionId,
      'metadata.serviceSessionId',
      'Must be a non-empty string when report identity metadata is present.',
    );
  }
  final reportSequence = metadata['reportSequence'];
  if (reportSequence is! int || reportSequence <= 0) {
    throw ArgumentError.value(
      reportSequence,
      'metadata.reportSequence',
      'Must be a positive integer when report identity metadata is present.',
    );
  }
  final expectedReportId = PerformanceReport.buildServiceReportId(
    serviceSessionId: serviceSessionId,
    reportSequence: reportSequence,
  );
  if (reportId != expectedReportId) {
    throw ArgumentError.value(
      reportId,
      'reportId',
      'Must match metadata identity: $expectedReportId.',
    );
  }
  return metadata;
}

int _requiredPositiveReportSequence(int value) {
  if (value > 0) {
    return value;
  }
  throw ArgumentError.value(
    value,
    'reportSequence',
    'Must be greater than zero.',
  );
}

String? _asString(Object? value) {
  if (value is String && value.trim().isNotEmpty) {
    return value;
  }
  return null;
}

int? _asInt(Object? value) {
  if (value is int) {
    return value;
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

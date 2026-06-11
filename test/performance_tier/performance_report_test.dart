import 'dart:convert';

import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PerformanceReport', () {
    test('serializes a versioned report around the current decision', () {
      final decision = TierDecision(
        tier: TierLevel.t2High,
        confidence: TierConfidence.high,
        deviceSignals: DeviceSignals(
          platform: 'android',
          deviceModel: 'Pixel 8 Pro',
          totalRamBytes: 8 * 1024 * 1024 * 1024,
          collectedAt: DateTime.utc(2026, 6, 11, 8),
        ),
        reasons: const <String>['test decision'],
        appliedPolicies: const <String, Object?>{'animationLevel': 2},
        decidedAt: DateTime.utc(2026, 6, 11, 8, 1),
      );

      final report = PerformanceReport.fromDecision(
        decision: decision,
        generatedAt: DateTime.utc(2026, 6, 11, 8, 2, 3, 4),
        source: 'unit-test',
        reportId: 'report/unit:test',
        metadata: const <String, Object?>{'serviceSessionId': 'session-1'},
      );
      final map = jsonDecode(report.toJson()) as Map<String, dynamic>;

      expect(map['schemaName'], PerformanceReport.schemaNameV1);
      expect(map['schemaVersion'], PerformanceReport.currentSchemaVersion);
      expect(map['reportId'], 'report/unit:test');
      expect(map['generatedAt'], '2026-06-11T08:02:03.004Z');
      expect(map['source'], 'unit-test');
      expect(map['metadata'], containsPair('serviceSessionId', 'session-1'));
      expect(map['decision'], isA<Map<String, Object?>>());
      expect(
        report.defaultFileName,
        'performance_tier_v1_20260611T080203004Z_report-unit-test.json',
      );
    });

    test('parses native write and file metadata maps', () {
      final writeResult =
          PerformanceReportWriteResult.fromMap(<String, dynamic>{
            'reportId': 'native-report',
            'fileName': 'report.json',
            'relativePath': 'files/performance_tier_reports/report.json',
            'absolutePath': '/data/user/0/app/files/report.json',
            'bytes': 42,
            'writtenAtEpochMs': 1781111111000,
          }, reportId: 'fallback-report');
      final file = PerformanceReportFile.fromMap(<String, dynamic>{
        'fileName': 'report.json',
        'relativePath': 'files/performance_tier_reports/report.json',
        'bytes': '42',
        'modifiedAtEpochMs': 1781111111000,
      });

      expect(writeResult.reportId, 'native-report');
      expect(writeResult.bytes, 42);
      expect(writeResult.writtenAt, DateTime.utc(2026, 6, 10, 17, 5, 11));
      expect(file.bytes, 42);
      expect(file.modifiedAt, DateTime.utc(2026, 6, 10, 17, 5, 11));
      expect(
        writeResult.toMap(),
        containsPair('writtenAtEpochMs', 1781111111000),
      );
      expect(file.toMap(), containsPair('modifiedAtEpochMs', 1781111111000));
      expect(
        PerformanceReportWriteResult.fromMap(
          writeResult.toMap(),
          reportId: 'fallback-report',
        ).writtenAt,
        writeResult.writtenAt,
      );
      expect(
        PerformanceReportFile.fromMap(file.toMap()).modifiedAt,
        file.modifiedAt,
      );
    });

    test('rejects incomplete native metadata maps', () {
      expect(
        () => PerformanceReportWriteResult.fromMap(<String, dynamic>{
          'relativePath': 'files/performance_tier_reports/report.json',
          'bytes': 42,
        }, reportId: 'fallback-report'),
        throwsA(isA<FormatException>()),
      );
      expect(
        () => PerformanceReportFile.fromMap(<String, dynamic>{
          'fileName': 'report.json',
          'relativePath': 'files/performance_tier_reports/report.json',
        }),
        throwsA(isA<FormatException>()),
      );
    });
  });
}

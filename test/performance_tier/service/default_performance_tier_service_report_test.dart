import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/default_performance_tier_service_test_support.dart';

void main() {
  group('DefaultPerformanceTierService reports', () {
    test('writes current report and initializes first when needed', () async {
      final reportStore = RecordingPerformanceReportStore();
      final service = DefaultPerformanceTierService(
        signalCollector: SequenceSignalCollector(<DeviceSignals>[
          androidSignals(
            ramBytes: 8 * bytesPerGb,
            mediaPerformanceClass: 13,
            sdkInt: 35,
          ),
        ]),
        configProvider: const DefaultConfigProvider(),
        engine: const RuleBasedTierEngine(),
        policyResolver: const DefaultPolicyResolver(),
        runtimeSignalRefreshInterval: Duration.zero,
        performanceReportStore: reportStore,
      );
      addTearDown(service.dispose);

      final firstResult = await service.writeCurrentReport(source: 'unit-test');
      final secondResult = await service.writeCurrentReport(
        source: 'unit-test',
      );

      expect(reportStore.reports, hasLength(2));
      expect(reportStore.reports.first.source, 'unit-test');
      expect(reportStore.reports.first.decision.tier, TierLevel.t3Ultra);
      expect(reportStore.reports.first.metadata, contains('serviceSessionId'));
      final serviceSessionId =
          reportStore.reports.first.metadata['serviceSessionId'] as String;
      expect(serviceSessionId, isNotEmpty);
      expect(
        reportStore.reports.last.metadata['serviceSessionId'],
        serviceSessionId,
      );
      expect(
        reportStore.reports.first.metadata,
        containsPair('reportSequence', 1),
      );
      expect(
        reportStore.reports.last.metadata,
        containsPair('reportSequence', 2),
      );
      expect(reportStore.reports.first.reportId, '$serviceSessionId-report-1');
      expect(reportStore.reports.last.reportId, '$serviceSessionId-report-2');
      expect(
        reportStore.reports.first.reportId,
        isNot(reportStore.reports.last.reportId),
      );
      expect(firstResult.fileName, reportStore.reports.first.defaultFileName);
      expect(secondResult.fileName, reportStore.reports.last.defaultFileName);
      expect(firstResult.fileName, isNot(secondResult.fileName));
      expect(
        firstResult.relativePath,
        startsWith('files/performance_tier_reports/'),
      );
    });

    test('lists reports through the configured report store', () async {
      final reportStore = RecordingPerformanceReportStore(
        files: const <PerformanceReportFile>[
          PerformanceReportFile(
            fileName: 'report.json',
            relativePath: 'files/performance_tier_reports/report.json',
            bytes: 12,
          ),
        ],
      );
      final service = DefaultPerformanceTierService(
        signalCollector: SequenceSignalCollector(<DeviceSignals>[
          androidSignals(
            ramBytes: 8 * bytesPerGb,
            mediaPerformanceClass: 13,
            sdkInt: 35,
          ),
        ]),
        configProvider: const DefaultConfigProvider(),
        engine: const RuleBasedTierEngine(),
        policyResolver: const DefaultPolicyResolver(),
        runtimeSignalRefreshInterval: Duration.zero,
        performanceReportStore: reportStore,
      );
      addTearDown(service.dispose);

      final reports = await service.listPerformanceReports();

      expect(reportStore.listCallCount, 1);
      expect(reports.single.fileName, 'report.json');
    });
  });
}

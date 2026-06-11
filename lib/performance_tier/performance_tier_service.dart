import 'model/performance_report.dart';
import 'model/tier_decision.dart';

abstract interface class PerformanceTierService {
  Future<void> initialize();

  Future<TierDecision> getCurrentDecision();

  Stream<TierDecision> watchDecision();

  Future<void> refresh();

  Future<PerformanceReportWriteResult> writeCurrentReport({
    String source = PerformanceReport.defaultSource,
  });

  Future<List<PerformanceReportFile>> listPerformanceReports();

  Future<void> dispose();
}

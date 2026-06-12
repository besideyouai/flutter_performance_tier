import 'model/performance_report.dart';
import 'model/tier_decision.dart';

/// Coordinates signal collection, tier decisions, and report-loop handoff.
abstract interface class PerformanceTierService {
  /// Prepares the service and computes the initial decision when needed.
  Future<void> initialize();

  /// Returns the most recent tier decision, initializing the service if needed.
  Future<TierDecision> getCurrentDecision();

  /// Emits the current decision and future refreshed decisions.
  Stream<TierDecision> watchDecision();

  /// Recomputes the current decision from the latest available signals.
  Future<void> refresh();

  /// Writes a V1 performance report for the current decision.
  ///
  /// Custom implementations must keep report identity, schema, timestamp, and
  /// storage metadata compatible with the Android report gate.
  Future<PerformanceReportWriteResult> writeCurrentReport({
    String source = PerformanceReport.defaultSource,
  });

  /// Lists reports written through the current report store.
  ///
  /// Implementations should return stable metadata for host-pull handoff.
  Future<List<PerformanceReportFile>> listPerformanceReports();

  /// Releases timers, streams, and native resources owned by the service.
  Future<void> dispose();
}

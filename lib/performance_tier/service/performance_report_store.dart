import '../model/performance_report.dart';

/// Persists V1 performance reports and exposes file metadata for host handoff.
abstract interface class PerformanceReportStore {
  /// Writes [report] and returns the native or backing-store file metadata.
  Future<PerformanceReportWriteResult> write(PerformanceReport report);

  /// Lists report files available from the backing store.
  Future<List<PerformanceReportFile>> list();
}

import '../model/performance_report.dart';

abstract interface class PerformanceReportStore {
  Future<PerformanceReportWriteResult> write(PerformanceReport report);

  Future<List<PerformanceReportFile>> list();
}

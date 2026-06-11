import 'package:flutter_performance_tier/flutter_performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('exports runtime tier controller from package barrel', () {
    final controller = RuntimeTierController();

    expect(controller.config.enableFrameDropSignal, isFalse);
  });

  test('exports performance report model from package barrel', () {
    final report = PerformanceReport.fromDecision(
      decision: TierDecision(
        tier: TierLevel.t1Mid,
        confidence: TierConfidence.low,
        deviceSignals: DeviceSignals(
          platform: 'android',
          collectedAt: DateTime(2026),
        ),
      ),
      generatedAt: DateTime.utc(2026, 6, 11),
      reportId: 'barrel-test',
    );

    expect(report.schemaVersion, PerformanceReport.currentSchemaVersion);
    expect(report.defaultFileName, contains('barrel-test'));
  });
}

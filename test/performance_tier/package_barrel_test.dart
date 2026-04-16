import 'package:flutter_performance_tier/flutter_performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('exports runtime tier controller from package barrel', () {
    final controller = RuntimeTierController();

    expect(controller.config.enableFrameDropSignal, isFalse);
  });
}

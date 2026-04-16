import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_performance_tier_example/demo/demo_runtime_signal_support.dart';
import 'package:flutter_performance_tier_example/demo/example_app_factory.dart';
import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';

void main() {
  test('default base collector uses method channel device signals', () {
    final factory = ExampleAppFactory();

    expect(
      factory.buildBaseCollector(),
      isA<MethodChannelDeviceSignalCollector>(),
    );
  });

  test(
    'runtime preset override is only applied when internal tools request it',
    () async {
      final baseCollector = _FakeDeviceSignalCollector(_baseSignals());
      final factory = ExampleAppFactory(
        baseCollectorBuilder: () => baseCollector,
      );

      final liveCollector = factory.buildSignalCollector();
      final presetCollector = factory.buildSignalCollector(
        presetProvider: () => DemoRuntimeSignalPreset.memoryCritical,
      );

      expect(identical(liveCollector, baseCollector), isTrue);

      final liveSignals = await liveCollector.collect();
      expect(liveSignals.memoryPressureState, 'normal');
      expect(liveSignals.memoryPressureLevel, 0);

      final presetSignals = await presetCollector.collect();
      expect(presetSignals.memoryPressureState, 'critical');
      expect(presetSignals.memoryPressureLevel, 2);
    },
  );
}

class _FakeDeviceSignalCollector implements DeviceSignalCollector {
  _FakeDeviceSignalCollector(this._signals);

  final DeviceSignals _signals;

  @override
  Future<DeviceSignals> collect() async => _signals;
}

DeviceSignals _baseSignals() {
  return DeviceSignals(
    platform: 'android',
    collectedAt: DateTime.utc(2026, 3, 11, 8),
    memoryPressureState: 'normal',
    memoryPressureLevel: 0,
  );
}

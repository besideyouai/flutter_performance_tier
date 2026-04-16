import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_performance_tier/demo/demo_runtime_signal_support.dart';
import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';

void main() {
  test('live device preset keeps base signals unchanged', () async {
    final collector = ExampleRuntimeSignalDecorator(
      baseCollector: _FakeDeviceSignalCollector(_baseSignals()),
      presetProvider: () => DemoRuntimeSignalPreset.liveDevice,
    );

    final signals = await collector.collect();

    expect(signals.memoryPressureState, 'normal');
    expect(signals.memoryPressureLevel, 0);
    expect(signals.thermalState, isNull);
    expect(signals.thermalStateLevel, isNull);
    expect(signals.platform, 'android');
    expect(signals.collectedAt, DateTime.utc(2026, 3, 11, 8));
  });

  test(
    'memory critical preset only overrides runtime memory signals',
    () async {
      final collector = ExampleRuntimeSignalDecorator(
        baseCollector: _FakeDeviceSignalCollector(_baseSignals()),
        presetProvider: () => DemoRuntimeSignalPreset.memoryCritical,
      );

      final signals = await collector.collect();

      expect(signals.memoryPressureState, 'critical');
      expect(signals.memoryPressureLevel, 2);
      expect(signals.thermalState, isNull);
      expect(signals.thermalStateLevel, isNull);
      expect(signals.platform, 'android');
    },
  );

  test('thermal serious preset only overrides thermal signals', () async {
    final collector = ExampleRuntimeSignalDecorator(
      baseCollector: _FakeDeviceSignalCollector(_baseSignals()),
      presetProvider: () => DemoRuntimeSignalPreset.thermalSerious,
    );

    final signals = await collector.collect();

    expect(signals.thermalState, 'serious');
    expect(signals.thermalStateLevel, 2);
    expect(signals.memoryPressureState, 'normal');
    expect(signals.memoryPressureLevel, 0);
    expect(signals.platform, 'android');
  });
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

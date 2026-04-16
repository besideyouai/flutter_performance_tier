import '../performance_tier/performance_tier.dart';

enum DemoRuntimeSignalPreset {
  liveDevice,
  memoryCritical,
  thermalSerious;

  String get label {
    return switch (this) {
      DemoRuntimeSignalPreset.liveDevice => 'Live device',
      DemoRuntimeSignalPreset.memoryCritical => 'Memory critical',
      DemoRuntimeSignalPreset.thermalSerious => 'Thermal serious',
    };
  }

  String get summary {
    return switch (this) {
      DemoRuntimeSignalPreset.liveDevice =>
        'Use current device signals without manual overrides.',
      DemoRuntimeSignalPreset.memoryCritical =>
        'Inject memoryPressure=critical(level=2) to force runtime downgrade.',
      DemoRuntimeSignalPreset.thermalSerious =>
        'Inject thermalState=serious(level=2) to force runtime downgrade.',
    };
  }

  Map<String, Object?> toMap() {
    return <String, Object?>{'id': name, 'label': label, 'summary': summary};
  }

  DeviceSignals apply(DeviceSignals baseSignals) {
    return switch (this) {
      DemoRuntimeSignalPreset.liveDevice => baseSignals,
      DemoRuntimeSignalPreset.memoryCritical => baseSignals.copyWith(
        memoryPressureState: 'critical',
        memoryPressureLevel: 2,
      ),
      DemoRuntimeSignalPreset.thermalSerious => baseSignals.copyWith(
        thermalState: 'serious',
        thermalStateLevel: 2,
      ),
    };
  }
}

class ExampleRuntimeSignalDecorator implements DeviceSignalCollector {
  ExampleRuntimeSignalDecorator({
    required DeviceSignalCollector baseCollector,
    required DemoRuntimeSignalPreset Function() presetProvider,
  }) : _baseCollector = baseCollector,
       _presetProvider = presetProvider;

  final DeviceSignalCollector _baseCollector;
  final DemoRuntimeSignalPreset Function() _presetProvider;

  @override
  Future<DeviceSignals> collect() async {
    final baseSignals = await _baseCollector.collect();
    return _presetProvider().apply(baseSignals);
  }
}

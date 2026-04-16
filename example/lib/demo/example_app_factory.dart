import 'demo_runtime_signal_support.dart';
import 'package:flutter_performance_tier/flutter_performance_tier.dart';

typedef ExampleBaseCollectorBuilder = DeviceSignalCollector Function();
typedef ExampleServiceBuilder =
    PerformanceTierService Function({
      required PerformanceTierLogger logger,
      required DeviceSignalCollector signalCollector,
      required Duration runtimeSignalRefreshInterval,
      required RuntimeTierController runtimeTierController,
    });

typedef ExampleRuntimeTierControllerBuilder = RuntimeTierController Function();

DeviceSignalCollector _defaultBaseCollectorBuilder() {
  return MethodChannelDeviceSignalCollector();
}

RuntimeTierController _defaultRuntimeTierControllerBuilder() {
  return RuntimeTierController(
    config: const RuntimeTierControllerConfig(
      downgradeDebounce: Duration(seconds: 1),
      recoveryCooldown: Duration(seconds: 3),
      upgradeDebounce: Duration(seconds: 1),
    ),
  );
}

PerformanceTierService _defaultServiceBuilder({
  required PerformanceTierLogger logger,
  required DeviceSignalCollector signalCollector,
  required Duration runtimeSignalRefreshInterval,
  required RuntimeTierController runtimeTierController,
}) {
  return DefaultPerformanceTierService(
    logger: logger,
    signalCollector: signalCollector,
    runtimeSignalRefreshInterval: runtimeSignalRefreshInterval,
    runtimeTierController: runtimeTierController,
  );
}

class ExampleAppFactory {
  ExampleAppFactory({
    this.baseCollectorBuilder = _defaultBaseCollectorBuilder,
    this.runtimeTierControllerBuilder = _defaultRuntimeTierControllerBuilder,
    this.serviceBuilder = _defaultServiceBuilder,
  });

  final ExampleBaseCollectorBuilder baseCollectorBuilder;
  final ExampleRuntimeTierControllerBuilder runtimeTierControllerBuilder;
  final ExampleServiceBuilder serviceBuilder;

  JsonLinePerformanceTierLogger buildLogger(PerformanceTierLogEmitter emitter) {
    return JsonLinePerformanceTierLogger(
      prefix: 'PERF_TIER_LOG',
      emitter: emitter,
    );
  }

  DeviceSignalCollector buildBaseCollector() {
    return baseCollectorBuilder();
  }

  RuntimeTierController buildRuntimeTierController() {
    return runtimeTierControllerBuilder();
  }

  DeviceSignalCollector buildSignalCollector({
    DemoRuntimeSignalPreset Function()? presetProvider,
  }) {
    final baseCollector = buildBaseCollector();
    if (presetProvider == null) {
      return baseCollector;
    }
    return ExampleRuntimeSignalDecorator(
      baseCollector: baseCollector,
      presetProvider: presetProvider,
    );
  }

  PerformanceTierService buildService({
    required PerformanceTierLogEmitter logEmitter,
    DemoRuntimeSignalPreset Function()? presetProvider,
    RuntimeTierController? runtimeTierController,
  }) {
    return serviceBuilder(
      logger: buildLogger(logEmitter),
      signalCollector: buildSignalCollector(presetProvider: presetProvider),
      runtimeSignalRefreshInterval: const Duration(seconds: 1),
      runtimeTierController:
          runtimeTierController ?? buildRuntimeTierController(),
    );
  }
}

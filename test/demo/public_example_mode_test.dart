import 'dart:async';

import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_performance_tier/demo/demo_runtime_signal_support.dart';
import 'package:flutter_performance_tier/demo/example_app_factory.dart';
import 'package:flutter_performance_tier/demo/internal_tools_controller.dart';
import 'package:flutter_performance_tier/demo/performance_tier_demo_app.dart';
import 'package:flutter_performance_tier/demo/performance_tier_demo_controller.dart';
import 'package:flutter_performance_tier/demo/performance_tier_upload_probe_controller.dart';
import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';

void main() {
  test('public demo app keeps upload probe lazy by default', () {
    const app = PerformanceTierDemoApp();

    expect(app.eagerBootstrapUploadProbe, isFalse);
  });

  test(
    'default example startup remains independent from internal tools',
    () async {
      final builtCollectors = <DeviceSignalCollector>[];
      final uploadProbeController = _SpyUploadProbeController();
      final internalToolsController = InternalToolsController(
        uploadProbeController: uploadProbeController,
      );
      final factory = ExampleAppFactory(
        baseCollectorBuilder: () => _FakeDeviceSignalCollector(_signals()),
        serviceBuilder:
            ({
              required PerformanceTierLogger logger,
              required DeviceSignalCollector signalCollector,
              required Duration runtimeSignalRefreshInterval,
              required RuntimeTierController runtimeTierController,
            }) {
              builtCollectors.add(signalCollector);
              return _FakePerformanceTierService(
                decision: _decision(TierLevel.t1Mid),
              );
            },
      );
      final controller = PerformanceTierDemoController(
        internalToolsController: internalToolsController,
        exampleAppFactory: factory,
      );
      addTearDown(controller.close);
      addTearDown(internalToolsController.close);

      await controller.start();
      await Future<void>.delayed(Duration.zero);

      expect(uploadProbeController.startCallCount, 0);
      expect(internalToolsController.hasActiveRuntimeSignalPreset, isFalse);
      expect(builtCollectors, hasLength(1));
      expect(
        builtCollectors.single,
        isNot(isA<ExampleRuntimeSignalDecorator>()),
      );
      expect(controller.decision?.tier, TierLevel.t1Mid);
      expect(controller.error, isNull);
    },
  );

  test(
    'switching back to live device preserves runtime cooldown state',
    () async {
      final builtRuntimeControllers = <RuntimeTierController>[];
      final baseCollector = _MutableDeviceSignalCollector(_signals());
      final internalToolsController = InternalToolsController(
        uploadProbeController: _SpyUploadProbeController(),
      );
      final factory = ExampleAppFactory(
        baseCollectorBuilder: () => baseCollector,
        serviceBuilder:
            ({
              required PerformanceTierLogger logger,
              required DeviceSignalCollector signalCollector,
              required Duration runtimeSignalRefreshInterval,
              required RuntimeTierController runtimeTierController,
            }) {
              builtRuntimeControllers.add(runtimeTierController);
              return _RuntimeAwareFakePerformanceTierService(
                signalCollector: signalCollector,
                runtimeTierController: runtimeTierController,
              );
            },
      );
      final controller = PerformanceTierDemoController(
        internalToolsController: internalToolsController,
        exampleAppFactory: factory,
      );
      addTearDown(controller.close);
      addTearDown(internalToolsController.close);

      await controller.start();
      await Future<void>.delayed(Duration.zero);
      expect(
        controller.decision?.runtimeObservation.status,
        RuntimeTierStatus.inactive,
      );

      await internalToolsController.selectRuntimeSignalPreset(
        DemoRuntimeSignalPreset.memoryCritical,
      );
      await controller.syncWithInternalToolsState();
      await Future<void>.delayed(const Duration(milliseconds: 1100));
      await controller.refreshDecision();
      await Future<void>.delayed(Duration.zero);

      expect(
        controller.decision?.runtimeObservation.status,
        RuntimeTierStatus.active,
      );
      expect(controller.decision?.tier, TierLevel.t1Mid);

      await internalToolsController.selectRuntimeSignalPreset(
        DemoRuntimeSignalPreset.liveDevice,
      );
      await controller.syncWithInternalToolsState();
      await controller.refreshDecision();
      await Future<void>.delayed(Duration.zero);

      expect(
        controller.decision?.runtimeObservation.status,
        RuntimeTierStatus.cooldown,
      );
      expect(controller.decision?.tier, TierLevel.t1Mid);
      expect(builtRuntimeControllers, hasLength(3));
    },
  );
}

class _FakePerformanceTierService implements PerformanceTierService {
  _FakePerformanceTierService({required this.decision});

  final TierDecision decision;
  final StreamController<TierDecision> _controller =
      StreamController<TierDecision>.broadcast();

  @override
  Future<TierDecision> getCurrentDecision() async => decision;

  @override
  Future<void> initialize() async {
    _controller.add(decision);
  }

  @override
  Future<void> refresh() async {
    _controller.add(decision);
  }

  @override
  Future<void> dispose() async {
    await _controller.close();
  }

  @override
  Stream<TierDecision> watchDecision() => _controller.stream;
}

class _FakeDeviceSignalCollector implements DeviceSignalCollector {
  _FakeDeviceSignalCollector(this._deviceSignals);

  final DeviceSignals _deviceSignals;

  @override
  Future<DeviceSignals> collect() async => _deviceSignals;
}

class _MutableDeviceSignalCollector implements DeviceSignalCollector {
  _MutableDeviceSignalCollector(this.currentSignals);

  DeviceSignals currentSignals;

  @override
  Future<DeviceSignals> collect() async => currentSignals;
}

class _SpyUploadProbeController extends PerformanceTierUploadProbeController {
  _SpyUploadProbeController() : super(logger: _noopLogger);

  int startCallCount = 0;

  @override
  Future<void> start() async {
    startCallCount += 1;
    notifyListeners();
  }
}

class _RuntimeAwareFakePerformanceTierService
    implements PerformanceTierService {
  _RuntimeAwareFakePerformanceTierService({
    required DeviceSignalCollector signalCollector,
    required RuntimeTierController runtimeTierController,
  }) : _signalCollector = signalCollector,
       _runtimeTierController = runtimeTierController;

  final DeviceSignalCollector _signalCollector;
  final RuntimeTierController _runtimeTierController;
  final StreamController<TierDecision> _controller =
      StreamController<TierDecision>.broadcast();

  TierDecision? _currentDecision;

  @override
  Future<TierDecision> getCurrentDecision() async {
    return _currentDecision ?? await _recompute();
  }

  @override
  Future<void> initialize() async {
    _currentDecision = await _recompute();
    _controller.add(_currentDecision!);
  }

  @override
  Future<void> refresh() async {
    _currentDecision = await _recompute();
    _controller.add(_currentDecision!);
  }

  @override
  Future<void> dispose() async {
    await _controller.close();
  }

  @override
  Stream<TierDecision> watchDecision() => _controller.stream;

  Future<TierDecision> _recompute() async {
    final signals = await _signalCollector.collect();
    final adjustment = _runtimeTierController.adjust(
      baseTier: TierLevel.t3Ultra,
      signals: signals,
    );
    return TierDecision(
      tier: adjustment.tier,
      confidence: TierConfidence.medium,
      deviceSignals: signals,
      runtimeObservation: adjustment.observation,
      reasons: adjustment.reasons,
    );
  }
}

TierDecision _decision(TierLevel tier) {
  return TierDecision(
    tier: tier,
    confidence: TierConfidence.medium,
    deviceSignals: _signals(),
  );
}

DeviceSignals _signals() {
  return DeviceSignals(
    platform: 'android',
    collectedAt: DateTime.utc(2026, 4, 16, 3),
    memoryPressureState: 'normal',
    memoryPressureLevel: 0,
  );
}

void _noopLogger(String line) {}

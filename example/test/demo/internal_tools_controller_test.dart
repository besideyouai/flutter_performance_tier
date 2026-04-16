import 'dart:async';

import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_performance_tier_example/demo/demo_runtime_signal_support.dart';
import 'package:flutter_performance_tier_example/demo/internal_tools_controller.dart';
import 'package:flutter_performance_tier_example/demo/performance_tier_demo_controller.dart';
import 'package:flutter_performance_tier_example/demo/performance_tier_upload_probe_controller.dart';
import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';

void main() {
  test(
    'public page controller can initialize and refresh without starting upload probe',
    () async {
      final uploadProbeController = _SpyUploadProbeController();
      final internalToolsController = InternalToolsController(
        uploadProbeController: uploadProbeController,
      );
      final service = _FakePerformanceTierService(
        initialDecision: _decision(TierLevel.t1Mid),
        refreshedDecision: _decision(TierLevel.t2High),
      );
      final controller = PerformanceTierDemoController(
        service: service,
        internalToolsController: internalToolsController,
      );
      addTearDown(controller.close);
      addTearDown(internalToolsController.close);

      await controller.start();
      await Future<void>.delayed(Duration.zero);
      await controller.refreshDecision();
      await Future<void>.delayed(Duration.zero);

      expect(service.initializeCallCount, 1);
      expect(service.refreshCallCount, 1);
      expect(uploadProbeController.startCallCount, 0);
      expect(controller.decision?.tier, TierLevel.t2High);
    },
  );

  test(
    'internal tools controller owns runtime preset state, structured logs, and upload probe actions',
    () async {
      final uploadProbeController = _SpyUploadProbeController(
        reportSections: <String, Object?>{
          'uploadProbe': <String, Object?>{'initialized': false},
        },
      );
      final controller = InternalToolsController(
        uploadProbeController: uploadProbeController,
      );
      addTearDown(controller.close);

      controller.recordStructuredLog('log-line-1');
      controller.recordStructuredLog('log-line-2');
      await controller.selectRuntimeSignalPreset(
        DemoRuntimeSignalPreset.memoryCritical,
      );

      final reportSections = controller.buildReportSections();

      expect(
        controller.runtimeSignalPreset,
        DemoRuntimeSignalPreset.memoryCritical,
      );
      expect(controller.structuredLogs, <String>['log-line-2', 'log-line-1']);
      expect(reportSections['recentStructuredLogs'], <String>[
        'log-line-2',
        'log-line-1',
      ]);
      expect(
        (reportSections['demoRuntimeSignalPreset']
            as Map<String, Object?>)['id'],
        'memoryCritical',
      );
      expect(reportSections['uploadProbe'], <String, Object?>{
        'initialized': false,
      });

      await controller.start();
      await controller.runUploadProbe(reportBuilder: () => '{"ok":true}');
      await controller.clearAuthSession();

      expect(uploadProbeController.startCallCount, 1);
      expect(uploadProbeController.runUploadProbeCallCount, 1);
      expect(uploadProbeController.clearAuthSessionCallCount, 1);
      expect(uploadProbeController.lastReportContent, '{"ok":true}');
    },
  );
}

class _FakePerformanceTierService implements PerformanceTierService {
  _FakePerformanceTierService({
    required TierDecision initialDecision,
    required TierDecision refreshedDecision,
  }) : _initialDecision = initialDecision,
       _refreshedDecision = refreshedDecision;

  final TierDecision _initialDecision;
  final TierDecision _refreshedDecision;
  final StreamController<TierDecision> _controller =
      StreamController<TierDecision>.broadcast();

  int initializeCallCount = 0;
  int refreshCallCount = 0;
  int disposeCallCount = 0;
  TierDecision? _currentDecision;

  @override
  Future<TierDecision> getCurrentDecision() async {
    return _currentDecision ?? _initialDecision;
  }

  @override
  Future<void> initialize() async {
    initializeCallCount += 1;
    _currentDecision = _initialDecision;
    _controller.add(_initialDecision);
  }

  @override
  Future<void> refresh() async {
    refreshCallCount += 1;
    _currentDecision = _refreshedDecision;
    _controller.add(_refreshedDecision);
  }

  @override
  Future<void> dispose() async {
    disposeCallCount += 1;
    await _controller.close();
  }

  @override
  Stream<TierDecision> watchDecision() {
    return _controller.stream;
  }
}

class _SpyUploadProbeController extends PerformanceTierUploadProbeController {
  _SpyUploadProbeController({
    this.reportSections = const <String, Object?>{
      'uploadProbe': <String, Object?>{'initialized': false},
    },
  }) : super(logger: _noopLogger);

  final Map<String, Object?> reportSections;

  int startCallCount = 0;
  int runUploadProbeCallCount = 0;
  int clearAuthSessionCallCount = 0;
  bool _started = false;
  String? lastReportContent;

  @override
  bool get started => _started;

  @override
  Future<void> start() async {
    startCallCount += 1;
    _started = true;
    notifyListeners();
  }

  @override
  Future<void> runUploadProbe({
    required String Function() reportBuilder,
  }) async {
    runUploadProbeCallCount += 1;
    lastReportContent = reportBuilder();
  }

  @override
  Future<void> clearAuthSession() async {
    clearAuthSessionCallCount += 1;
  }

  @override
  Map<String, Object?> buildReportSections() => reportSections;
}

TierDecision _decision(TierLevel tier) {
  return TierDecision(
    tier: tier,
    confidence: TierConfidence.medium,
    deviceSignals: DeviceSignals(
      platform: 'android',
      collectedAt: DateTime.utc(2026, 4, 16, 3),
      memoryPressureState: 'normal',
      memoryPressureLevel: 0,
    ),
  );
}

void _noopLogger(String line) {}

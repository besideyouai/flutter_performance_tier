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

  test('demo controller writes and lists Android reports through service', () async {
    final internalToolsController = InternalToolsController(
      uploadProbeController: _SpyUploadProbeController(),
    );
    final service = _FakePerformanceTierService(
      initialDecision: _decision(TierLevel.t1Mid),
      refreshedDecision: _decision(TierLevel.t2High),
      reportWriteResult: const PerformanceReportWriteResult(
        reportId: 'report-1',
        fileName: 'performance_tier_v1_report-1.json',
        relativePath:
            'files/performance_tier_reports/performance_tier_v1_report-1.json',
        bytes: 42,
      ),
      reportFiles: const <PerformanceReportFile>[
        PerformanceReportFile(
          fileName: 'performance_tier_v1_report-1.json',
          relativePath:
              'files/performance_tier_reports/performance_tier_v1_report-1.json',
          bytes: 42,
        ),
      ],
    );
    final controller = PerformanceTierDemoController(
      service: service,
      internalToolsController: internalToolsController,
    );
    addTearDown(controller.close);
    addTearDown(internalToolsController.close);

    await controller.start();
    await Future<void>.delayed(Duration.zero);

    expect(controller.canCopyAndroidReportHostCommands, isFalse);
    expect(
      controller.buildAndroidReportHostCommands(),
      'Generate or list a safe report before copying host commands.',
    );
    expect(controller.buildAndroidReportHostCommands(), isNot(contains('<')));

    await controller.writeAndroidReport();

    expect(service.writeReportCallCount, 1);
    expect(service.lastReportSource, 'example-internal-tools');
    expect(service.listReportsCallCount, 1);
    expect(controller.canCopyAndroidReportHostCommands, isTrue);
    expect(
      controller.lastReportWriteResult?.fileName,
      'performance_tier_v1_report-1.json',
    );
    expect(controller.androidReportFiles, hasLength(1));
    expect(controller.androidReportError, isNull);
    final hostCommands = controller.buildAndroidReportHostCommands();
    final hostCommandLines = hostCommands.split('\n');

    expect(hostCommands, startsWith('set -e\n'));
    expect(
      hostCommands,
      contains(
        "cat 'files/performance_tier_reports/performance_tier_v1_report-1.json'",
      ),
    );
    expect(
      hostCommands,
      contains(
        "'build/pulled_performance_reports/performance_tier_v1_report-1.json'",
      ),
    );
    expect(hostCommands, contains('--android-report-gate'));
    expect(hostCommands, contains(r'--branch "$(git branch --show-current)"'));
    expect(hostCommands, contains(r'--commit "$(git rev-parse --short HEAD)"'));
    expect(
      hostCommands,
      contains(
        "test -s 'build/pulled_performance_reports/performance_tier_v1_report-1.json'",
      ),
    );
    expect(
      hostCommands,
      contains(
        "'build/diagnostics_analysis_android_report_gate/android_report_gate.md'",
      ),
    );
    expect(hostCommands, contains('tool/build_android_report_evidence.py'));
    expect(hostCommands, contains('tool/validate_android_report_evidence.py'));
    expect(
      hostCommands,
      contains(
        "'goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_report-1.md'",
      ),
    );
    expect(
      hostCommandLines,
      containsAllInOrder(<String>[
        'set -e',
        "adb shell run-as 'com.example.flutter_performance_tier_example' ls 'files/performance_tier_reports'",
        "mkdir -p 'build/pulled_performance_reports'",
        "adb exec-out run-as 'com.example.flutter_performance_tier_example' cat 'files/performance_tier_reports/performance_tier_v1_report-1.json' > 'build/pulled_performance_reports/performance_tier_v1_report-1.json'",
        "test -s 'build/pulled_performance_reports/performance_tier_v1_report-1.json'",
        'set +e',
        "python3 tool/analyze_diagnostics.py 'build/pulled_performance_reports/performance_tier_v1_report-1.json' --output 'build/diagnostics_analysis_android_report_gate' --android-report-gate",
        r'gate_status=$?',
        'set -e',
        "cat 'build/diagnostics_analysis_android_report_gate/android_report_gate.md'",
        r'test "$gate_status" -eq 0',
        "python3 tool/build_android_report_evidence.py 'build/pulled_performance_reports/performance_tier_v1_report-1.json' --analysis-output-dir 'build/diagnostics_analysis_android_report_gate' --branch \"\$(git branch --show-current)\" --commit \"\$(git rev-parse --short HEAD)\" --output 'goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_report-1.md' --application-id 'com.example.flutter_performance_tier_example'",
        "python3 tool/validate_android_report_evidence.py 'goals/2026-06-11-android-performance-report-loop/evidence/android_report_loop_performance_tier_v1_report-1.md'",
      ]),
    );
    final currentDirectoryHostCommands = controller
        .buildAndroidReportHostCommands(
          hostReportFile: 'performance_tier_v1_report-1.json',
          evidenceOutputFile:
              'android_report_loop_performance_tier_v1_report-1.md',
        );
    expect(currentDirectoryHostCommands, contains("mkdir -p ."));
    final customHostCommands = controller.buildAndroidReportHostCommands(
      applicationId: 'com.example.flutter_performance_tier_example',
      hostReportFile: "build/pulled reports/report's copy.json",
      analysisOutputDir: 'build/diagnostics analysis',
      evidenceOutputFile: "goals/evidence/report's evidence.md",
    );
    expect(
      customHostCommands,
      contains(
        "adb shell run-as 'com.example.flutter_performance_tier_example'",
      ),
    );
    expect(customHostCommands, contains("mkdir -p 'build/pulled reports'"));
    expect(
      customHostCommands,
      contains(r"> 'build/pulled reports/report'\''s copy.json'"),
    );
    expect(
      customHostCommands,
      contains(r"test -s 'build/pulled reports/report'\''s copy.json'"),
    );
    expect(
      customHostCommands,
      contains(
        r"tool/analyze_diagnostics.py 'build/pulled reports/report'\''s copy.json'",
      ),
    );
    expect(customHostCommands, contains(r'gate_status=$?'));
    expect(customHostCommands, contains(r'test "$gate_status" -eq 0'));
    expect(
      customHostCommands,
      contains("--output 'build/diagnostics analysis'"),
    );
    expect(
      customHostCommands,
      contains("cat 'build/diagnostics analysis/android_report_gate.md'"),
    );
    expect(
      customHostCommands,
      contains(
        "tool/build_android_report_evidence.py 'build/pulled reports/report'\\''s copy.json' --analysis-output-dir 'build/diagnostics analysis' --branch \"\$(git branch --show-current)\" --commit \"\$(git rev-parse --short HEAD)\" --output 'goals/evidence/report'\\''s evidence.md' --application-id 'com.example.flutter_performance_tier_example'",
      ),
    );
    expect(
      customHostCommands,
      contains(
        r"tool/validate_android_report_evidence.py 'goals/evidence/report'\''s evidence.md'",
      ),
    );

    final reportSections =
        controller.buildAndroidReportSections()['androidReportLoop']
            as Map<String, Object?>;

    expect(reportSections['lastWriteResult'], isA<Map<String, Object?>>());
    expect(reportSections['files'], isA<List<Object?>>());
    expect(reportSections['hostCommands'], contains('adb shell run-as'));
    expect(reportSections['hostCommands'], contains('--android-report-gate'));
    expect(reportSections['hostCommands'], contains('android_report_gate.md'));
    expect(
      reportSections['hostCommands'],
      contains('tool/build_android_report_evidence.py'),
    );
    expect(
      reportSections['hostCommands'],
      contains('tool/validate_android_report_evidence.py'),
    );
    expect(reportSections['adbCommands'], contains('adb shell run-as'));
    expect(reportSections['adbCommands'], contains('--android-report-gate'));
    expect(reportSections['adbCommands'], contains('android_report_gate.md'));
  });

  test('demo controller refuses unsafe Android report file names', () async {
    final internalToolsController = InternalToolsController(
      uploadProbeController: _SpyUploadProbeController(),
    );
    final service = _FakePerformanceTierService(
      initialDecision: _decision(TierLevel.t1Mid),
      refreshedDecision: _decision(TierLevel.t2High),
      reportWriteResult: const PerformanceReportWriteResult(
        reportId: 'unsafe-report',
        fileName: '../unsafe report.json',
        relativePath: 'files/performance_tier_reports/../unsafe report.json',
        bytes: 42,
      ),
      reportFiles: const <PerformanceReportFile>[
        PerformanceReportFile(
          fileName: "../unsafe report's copy.json",
          relativePath:
              "files/performance_tier_reports/../unsafe report's copy.json",
          bytes: 42,
        ),
      ],
    );
    final controller = PerformanceTierDemoController(
      service: service,
      internalToolsController: internalToolsController,
    );
    addTearDown(controller.close);
    addTearDown(internalToolsController.close);

    await controller.start();
    await Future<void>.delayed(Duration.zero);
    await controller.writeAndroidReport();

    expect(controller.canCopyAndroidReportHostCommands, isFalse);
    expect(
      controller.buildAndroidReportHostCommands(),
      'Generate or list a safe report before copying host commands.',
    );
    expect(controller.buildAndroidReportHostCommands(), isNot(contains('..')));
    expect(controller.buildAndroidReportHostCommands(), isNot(contains("'")));
  });

  test(
    'demo controller skips unsafe listed reports for host commands',
    () async {
      final internalToolsController = InternalToolsController(
        uploadProbeController: _SpyUploadProbeController(),
      );
      final service = _FakePerformanceTierService(
        initialDecision: _decision(TierLevel.t1Mid),
        refreshedDecision: _decision(TierLevel.t2High),
        reportFiles: const <PerformanceReportFile>[
          PerformanceReportFile(
            fileName: '../unsafe.json',
            relativePath: 'files/performance_tier_reports/../unsafe.json',
            bytes: 1,
          ),
          PerformanceReportFile(
            fileName: 'performance_tier_v1_safe.json',
            relativePath:
                'files/performance_tier_reports/performance_tier_v1_safe.json',
            bytes: 42,
          ),
        ],
      );
      final controller = PerformanceTierDemoController(
        service: service,
        internalToolsController: internalToolsController,
      );
      addTearDown(controller.close);
      addTearDown(internalToolsController.close);

      await controller.start();
      await Future<void>.delayed(Duration.zero);
      await controller.listAndroidReports();

      expect(controller.canCopyAndroidReportHostCommands, isTrue);
      expect(
        controller.buildAndroidReportHostCommands(),
        contains(
          "'files/performance_tier_reports/performance_tier_v1_safe.json'",
        ),
      );
      expect(
        controller.buildAndroidReportHostCommands(),
        isNot(contains('..')),
      );
    },
  );

  test(
    'demo controller chooses latest safe listed report for host commands',
    () async {
      final internalToolsController = InternalToolsController(
        uploadProbeController: _SpyUploadProbeController(),
      );
      final service = _FakePerformanceTierService(
        initialDecision: _decision(TierLevel.t1Mid),
        refreshedDecision: _decision(TierLevel.t2High),
        reportFiles: <PerformanceReportFile>[
          PerformanceReportFile(
            fileName: 'performance_tier_v1_old.json',
            relativePath:
                'files/performance_tier_reports/performance_tier_v1_old.json',
            bytes: 24,
            modifiedAt: DateTime.utc(2026, 6, 11, 8),
          ),
          PerformanceReportFile(
            fileName: 'performance_tier_v1_new.json',
            relativePath:
                'files/performance_tier_reports/performance_tier_v1_new.json',
            bytes: 42,
            modifiedAt: DateTime.utc(2026, 6, 11, 9),
          ),
        ],
      );
      final controller = PerformanceTierDemoController(
        service: service,
        internalToolsController: internalToolsController,
      );
      addTearDown(controller.close);
      addTearDown(internalToolsController.close);

      await controller.start();
      await Future<void>.delayed(Duration.zero);
      await controller.listAndroidReports();

      expect(controller.canCopyAndroidReportHostCommands, isTrue);
      expect(
        controller.buildAndroidReportHostCommands(),
        contains(
          "'files/performance_tier_reports/performance_tier_v1_new.json'",
        ),
      );
      expect(
        controller.buildAndroidReportHostCommands(),
        isNot(
          contains(
            "'files/performance_tier_reports/performance_tier_v1_old.json'",
          ),
        ),
      );
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
    required this._initialDecision,
    required this._refreshedDecision,
    this.reportWriteResult,
    this.reportFiles = const <PerformanceReportFile>[],
  });

  final TierDecision _initialDecision;
  final TierDecision _refreshedDecision;
  final PerformanceReportWriteResult? reportWriteResult;
  final List<PerformanceReportFile> reportFiles;
  final StreamController<TierDecision> _controller =
      StreamController<TierDecision>.broadcast();

  int initializeCallCount = 0;
  int refreshCallCount = 0;
  int disposeCallCount = 0;
  int writeReportCallCount = 0;
  int listReportsCallCount = 0;
  String? lastReportSource;
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

  @override
  Future<PerformanceReportWriteResult> writeCurrentReport({
    String source = PerformanceReport.defaultSource,
  }) async {
    writeReportCallCount += 1;
    lastReportSource = source;
    return reportWriteResult ??
        const PerformanceReportWriteResult(
          reportId: 'report-1',
          fileName: 'report-1.json',
          relativePath: 'files/performance_tier_reports/report-1.json',
          bytes: 1,
        );
  }

  @override
  Future<List<PerformanceReportFile>> listPerformanceReports() async {
    listReportsCallCount += 1;
    return reportFiles;
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

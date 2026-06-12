import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'example_app_factory.dart';
import 'internal_tools_controller.dart';
import 'package:flutter_performance_tier/flutter_performance_tier.dart';

class PerformanceTierDemoController extends ChangeNotifier {
  PerformanceTierDemoController({
    PerformanceTierService? service,
    required this._internalToolsController,
    ExampleAppFactory? exampleAppFactory,
  }) : _providedService = service,
       _exampleAppFactory = exampleAppFactory ?? ExampleAppFactory();

  final PerformanceTierService? _providedService;
  final InternalToolsController _internalToolsController;
  final ExampleAppFactory _exampleAppFactory;

  PerformanceTierService? _ownedService;
  RuntimeTierController? _ownedRuntimeTierController;
  bool? _usesPresetDecorator;

  StreamSubscription<TierDecision>? _subscription;
  Future<void>? _startInFlight;
  bool _started = false;
  bool _disposed = false;

  TierDecision? _decision;
  String? _error;
  bool _initializing = true;
  bool _refreshing = false;
  bool _writingAndroidReport = false;
  bool _listingAndroidReports = false;
  PerformanceReportWriteResult? _lastReportWriteResult;
  List<PerformanceReportFile> _androidReportFiles =
      const <PerformanceReportFile>[];
  String? _androidReportError;

  TierDecision? get decision => _decision;
  String? get error => _error;
  bool get initializing => _initializing;
  bool get refreshing => _refreshing;
  bool get supportsRuntimeSignalPresets => _providedService == null;
  bool get writingAndroidReport => _writingAndroidReport;
  bool get listingAndroidReports => _listingAndroidReports;
  PerformanceReportWriteResult? get lastReportWriteResult =>
      _lastReportWriteResult;
  List<PerformanceReportFile> get androidReportFiles => _androidReportFiles;
  String? get androidReportError => _androidReportError;
  bool get canCopyAndroidReportHostCommands =>
      _androidReportCommandFileName != null;

  Future<void> start() {
    if (_disposed || _started) {
      return Future<void>.value();
    }

    final inFlight = _startInFlight;
    if (inFlight != null) {
      return inFlight;
    }

    final next = _startSafely().whenComplete(() {
      _startInFlight = null;
    });
    _startInFlight = next;
    return next;
  }

  Future<void> refreshDecision() async {
    if (_disposed || _refreshing) {
      return;
    }

    _refreshing = true;
    _notifySafely();
    try {
      await _currentService.refresh();
    } catch (error) {
      _error = 'Refresh failed: $error';
    } finally {
      _refreshing = false;
      _notifySafely();
    }
  }

  Future<void> syncWithInternalToolsState() async {
    if (_disposed || !supportsRuntimeSignalPresets) {
      return;
    }

    final shouldUsePresetDecorator =
        _internalToolsController.hasActiveRuntimeSignalPreset;
    if (_ownedService == null ||
        _usesPresetDecorator == shouldUsePresetDecorator) {
      return;
    }

    await _restartOwnedService(usePresetDecorator: shouldUsePresetDecorator);
  }

  Future<void> copyAiReport(
    BuildContext context, {
    Map<String, Object?> extraSections = const <String, Object?>{},
  }) async {
    await _copyToClipboard(
      context,
      buildAiReport(extraSections: extraSections),
      successMessage: 'AI report copied.',
    );
  }

  Future<void> writeAndroidReport() async {
    if (_disposed || _writingAndroidReport) {
      return;
    }

    _writingAndroidReport = true;
    _androidReportError = null;
    _notifySafely();
    try {
      final writeResult = await _currentService.writeCurrentReport(
        source: 'example-internal-tools',
      );
      _lastReportWriteResult = writeResult;
      try {
        _androidReportFiles = await _currentService.listPerformanceReports();
      } catch (error) {
        _androidReportError = 'Report written, but list failed: $error';
      }
    } catch (error) {
      _androidReportError = 'Report write failed: $error';
    } finally {
      _writingAndroidReport = false;
      _notifySafely();
    }
  }

  Future<void> listAndroidReports() async {
    if (_disposed || _listingAndroidReports) {
      return;
    }

    _listingAndroidReports = true;
    _androidReportError = null;
    _notifySafely();
    try {
      _androidReportFiles = await _currentService.listPerformanceReports();
    } catch (error) {
      _androidReportError = 'Report list failed: $error';
    } finally {
      _listingAndroidReports = false;
      _notifySafely();
    }
  }

  Future<void> copyAndroidReportHostCommands(BuildContext context) async {
    if (!canCopyAndroidReportHostCommands) {
      return;
    }
    await _copyToClipboard(
      context,
      buildAndroidReportHostCommands(),
      successMessage: 'Android report host commands copied.',
    );
  }

  String buildAndroidReportHostCommands({
    String applicationId = _exampleAndroidApplicationId,
    String? hostReportFile,
    String analysisOutputDir = 'build/diagnostics_analysis_android_report_gate',
    String? evidenceOutputFile,
  }) {
    final fileName = _androidReportCommandFileName;
    if (fileName == null) {
      return 'Generate or list a safe report before copying host commands.';
    }
    const reportDirectory = 'files/performance_tier_reports';
    final reportPath = '$reportDirectory/$fileName';
    final resolvedHostReportFile =
        hostReportFile ?? 'build/pulled_performance_reports/$fileName';
    final hostReportDirectory = _hostDirectoryFor(resolvedHostReportFile);
    final gateReportFile = '$analysisOutputDir/android_report_gate.md';
    final resolvedEvidenceOutputFile =
        evidenceOutputFile ??
        'goals/2026-06-11-android-performance-report-loop/evidence/'
            'android_report_loop_${_withoutJsonExtension(fileName)}.md';
    final commands = <String>[
      'set -e',
      'adb shell run-as ${_shellQuote(applicationId)} '
          'ls ${_shellQuote(reportDirectory)}',
      'mkdir -p ${_shellQuote(hostReportDirectory)}',
      'adb exec-out run-as ${_shellQuote(applicationId)} '
          'cat ${_shellQuote(reportPath)} > '
          '${_shellQuote(resolvedHostReportFile)}',
      'test -s ${_shellQuote(resolvedHostReportFile)}',
      'set +e',
      'python3 tool/analyze_diagnostics.py '
          '${_shellQuote(resolvedHostReportFile)} '
          '--output ${_shellQuote(analysisOutputDir)} --android-report-gate',
      r'gate_status=$?',
      'set -e',
      'cat ${_shellQuote(gateReportFile)}',
      r'test "$gate_status" -eq 0',
      'python3 tool/build_android_report_evidence.py '
          '${_shellQuote(resolvedHostReportFile)} '
          '--analysis-output-dir ${_shellQuote(analysisOutputDir)} '
          '--branch $_gitBranchShellValue '
          '--commit $_gitCommitShellValue '
          '--output ${_shellQuote(resolvedEvidenceOutputFile)} '
          '--application-id ${_shellQuote(applicationId)}',
      'python3 tool/validate_android_report_evidence.py '
          '${_shellQuote(resolvedEvidenceOutputFile)}',
    ];
    return commands.join('\n');
  }

  Map<String, Object?> buildAndroidReportSections() {
    final hostCommands = buildAndroidReportHostCommands();
    return <String, Object?>{
      'androidReportLoop': <String, Object?>{
        'lastWriteResult': _lastReportWriteResult?.toMap(),
        'files': _androidReportFiles
            .map((PerformanceReportFile file) => file.toMap())
            .toList(growable: false),
        'error': _androidReportError,
        'hostCommands': hostCommands,
        'adbCommands': hostCommands,
      },
    };
  }

  String? get _androidReportCommandFileName {
    final writtenFileName = _lastReportWriteResult?.fileName;
    if (_isSafeAndroidReportFileName(writtenFileName)) {
      return writtenFileName;
    }

    PerformanceReportFile? selectedFile;
    for (final file in _androidReportFiles) {
      if (!_isSafeAndroidReportFileName(file.fileName)) {
        continue;
      }
      final selectedModifiedAt = selectedFile?.modifiedAt;
      final fileModifiedAt = file.modifiedAt;
      final isNewer =
          fileModifiedAt != null &&
          (selectedModifiedAt == null ||
              fileModifiedAt.isAfter(selectedModifiedAt));
      if (selectedFile == null || isNewer) {
        selectedFile = file;
      }
    }
    return selectedFile?.fileName;
  }

  static bool _isSafeAndroidReportFileName(String? fileName) {
    if (fileName == null || fileName.isEmpty || !fileName.endsWith('.json')) {
      return false;
    }
    for (final codeUnit in fileName.codeUnits) {
      final isLower = codeUnit >= 97 && codeUnit <= 122;
      final isUpper = codeUnit >= 65 && codeUnit <= 90;
      final isDigit = codeUnit >= 48 && codeUnit <= 57;
      final isSymbol = codeUnit == 45 || codeUnit == 46 || codeUnit == 95;
      if (!isLower && !isUpper && !isDigit && !isSymbol) {
        return false;
      }
    }
    return true;
  }

  static String _withoutJsonExtension(String fileName) {
    if (fileName.endsWith('.json')) {
      return fileName.substring(0, fileName.length - '.json'.length);
    }
    return fileName;
  }

  static String _hostDirectoryFor(String filePath) {
    final slashIndex = filePath.lastIndexOf('/');
    if (slashIndex < 0) {
      return '.';
    }
    if (slashIndex == 0) {
      return '/';
    }
    return filePath.substring(0, slashIndex);
  }

  static String _shellQuote(String value) {
    if (value == '.') {
      return '.';
    }
    return "'${value.replaceAll("'", r"'\''")}'";
  }

  String buildAiReport({
    Map<String, Object?> extraSections = const <String, Object?>{},
  }) {
    final report = <String, Object?>{
      'status': _error == null ? 'ok' : 'error',
      'generatedAt': DateTime.now().toIso8601String(),
      'initializing': _initializing,
      if (_decision != null) 'decision': _decision!.toMap(),
      if (_error != null) 'error': _error,
    };
    report.addAll(extraSections);
    return const JsonEncoder.withIndent('  ').convert(report);
  }

  String buildHeadline() {
    if (_initializing && _decision == null) {
      return 'Initializing service and waiting for first decision...';
    }
    if (_decision == null) {
      return _error ?? 'No decision yet.';
    }

    final currentDecision = _decision!;
    return 'tier=${currentDecision.tier.name}, '
        'confidence=${currentDecision.confidence.name}, '
        'runtime=${currentDecision.runtimeObservation.status.wireName}';
  }

  Future<void> close() async {
    if (_disposed) {
      return;
    }

    _disposed = true;
    final subscription = _subscription;
    _subscription = null;
    final disposeFuture = _providedService != null
        ? _providedService.dispose()
        : _ownedService?.dispose();
    await subscription?.cancel();
    await disposeFuture;
    super.dispose();
  }

  Future<void> _startSafely() async {
    _started = true;
    _subscription = _currentService.watchDecision().listen(
      _onDecision,
      onError: (Object error, StackTrace stackTrace) {
        if (_disposed) {
          return;
        }
        _initializing = false;
        _error = 'watchDecision failed: $error';
        _notifySafely();
      },
    );

    try {
      await _currentService.initialize();
      if (_disposed || _decision != null) {
        return;
      }
      _initializing = false;
      _notifySafely();
    } catch (error) {
      if (_disposed) {
        return;
      }
      _initializing = false;
      _error = 'Initialization failed: $error';
      _notifySafely();
    }
  }

  Future<void> _copyToClipboard(
    BuildContext context,
    String text, {
    required String successMessage,
  }) async {
    final messenger = ScaffoldMessenger.maybeOf(context);
    await Clipboard.setData(ClipboardData(text: text));
    if (_disposed || messenger == null) {
      return;
    }
    messenger.showSnackBar(SnackBar(content: Text(successMessage)));
  }

  void _onDecision(TierDecision decision) {
    if (_disposed) {
      return;
    }
    _decision = decision;
    _error = null;
    _initializing = false;
    _notifySafely();
  }

  void _notifySafely() {
    if (_disposed) {
      return;
    }
    notifyListeners();
  }

  PerformanceTierService get _currentService {
    return _providedService ??
        (_ownedService ??= _buildOwnedService(
          usePresetDecorator:
              _internalToolsController.hasActiveRuntimeSignalPreset,
        ));
  }

  PerformanceTierService _buildOwnedService({
    required bool usePresetDecorator,
  }) {
    _usesPresetDecorator = usePresetDecorator;
    return _exampleAppFactory.buildService(
      logEmitter: _internalToolsController.recordStructuredLog,
      presetProvider: usePresetDecorator
          ? () => _internalToolsController.runtimeSignalPreset
          : null,
      runtimeTierController: _ownedRuntimeTierController ??= _exampleAppFactory
          .buildRuntimeTierController(),
    );
  }

  Future<void> _restartOwnedService({required bool usePresetDecorator}) async {
    final previousSubscription = _subscription;
    final previousService = _ownedService;
    _subscription = null;
    _ownedService = _buildOwnedService(usePresetDecorator: usePresetDecorator);
    _started = true;
    _initializing = true;
    _error = null;
    _notifySafely();

    await previousSubscription?.cancel();
    await previousService?.dispose();

    _subscription = _currentService.watchDecision().listen(
      _onDecision,
      onError: (Object error, StackTrace stackTrace) {
        if (_disposed) {
          return;
        }
        _initializing = false;
        _error = 'watchDecision failed: $error';
        _notifySafely();
      },
    );

    try {
      await _currentService.initialize();
      if (_disposed || _decision != null) {
        return;
      }
      _initializing = false;
      _notifySafely();
    } catch (error) {
      if (_disposed) {
        return;
      }
      _initializing = false;
      _error = 'Initialization failed: $error';
      _notifySafely();
    }
  }
}

const String _exampleAndroidApplicationId =
    'com.example.flutter_performance_tier_example';
const String _gitBranchShellValue = r'"$(git branch --show-current)"';
const String _gitCommitShellValue = r'"$(git rev-parse --short HEAD)"';

import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'demo_runtime_signal_support.dart';
import 'performance_tier_upload_probe_controller.dart';

class InternalToolsController extends ChangeNotifier {
  InternalToolsController({
    PerformanceTierUploadProbeController? uploadProbeController,
  }) {
    _uploadProbeController =
        uploadProbeController ??
        PerformanceTierUploadProbeController(logger: recordStructuredLog);
    _uploadProbeController.addListener(_handleUploadProbeChanged);
  }

  late final PerformanceTierUploadProbeController _uploadProbeController;
  final List<String> _structuredLogs = <String>[];

  DemoRuntimeSignalPreset _runtimeSignalPreset =
      DemoRuntimeSignalPreset.liveDevice;
  bool _disposed = false;

  DemoRuntimeSignalPreset get runtimeSignalPreset => _runtimeSignalPreset;
  bool get hasActiveRuntimeSignalPreset =>
      _runtimeSignalPreset != DemoRuntimeSignalPreset.liveDevice;
  List<String> get structuredLogs => List<String>.unmodifiable(_structuredLogs);
  PerformanceTierUploadProbeController get uploadProbeController =>
      _uploadProbeController;

  Future<void> start() {
    return _uploadProbeController.start();
  }

  Future<void> selectRuntimeSignalPreset(DemoRuntimeSignalPreset preset) async {
    if (_disposed || _runtimeSignalPreset == preset) {
      return;
    }
    _runtimeSignalPreset = preset;
    notifyListeners();
  }

  Future<void> runUploadProbe({required String Function() reportBuilder}) {
    return _uploadProbeController.runUploadProbe(reportBuilder: reportBuilder);
  }

  Future<void> clearAuthSession() {
    return _uploadProbeController.clearAuthSession();
  }

  Future<void> copyLatestLogLine(BuildContext context) async {
    final latest = _structuredLogs.isEmpty ? '' : _structuredLogs.first;
    final messenger = ScaffoldMessenger.maybeOf(context);
    await Clipboard.setData(ClipboardData(text: latest));
    if (_disposed || messenger == null) {
      return;
    }
    messenger.showSnackBar(
      const SnackBar(content: Text('Latest log line copied.')),
    );
  }

  void recordStructuredLog(String line) {
    debugPrint(line);
    _structuredLogs.insert(0, line);
    if (_structuredLogs.length > 200) {
      _structuredLogs.removeRange(200, _structuredLogs.length);
    }
    if (_disposed) {
      return;
    }
    notifyListeners();
  }

  Map<String, Object?> buildReportSections() {
    return <String, Object?>{
      'recentStructuredLogs': _structuredLogs.take(40).toList(),
      'demoRuntimeSignalPreset': _runtimeSignalPreset.toMap(),
      ..._uploadProbeController.buildReportSections(),
    };
  }

  String buildStructuredLogsJson() {
    return const JsonEncoder.withIndent('  ').convert(<String, Object?>{
      'recentStructuredLogs': _structuredLogs.take(40).toList(),
    });
  }

  Future<void> close() async {
    if (_disposed) {
      return;
    }
    _disposed = true;
    _uploadProbeController.removeListener(_handleUploadProbeChanged);
    await _uploadProbeController.dispose();
    super.dispose();
  }

  void _handleUploadProbeChanged() {
    if (_disposed) {
      return;
    }
    notifyListeners();
  }
}

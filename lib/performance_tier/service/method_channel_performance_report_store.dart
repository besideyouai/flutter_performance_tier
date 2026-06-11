import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../model/performance_report.dart';
import 'host_platform_resolver.dart';
import 'performance_report_store.dart';

class MethodChannelPerformanceReportStore implements PerformanceReportStore {
  MethodChannelPerformanceReportStore({
    this.methodChannel = const MethodChannel(_channelName),
    this.isWeb = kIsWeb,
    this.targetPlatform,
  });

  static const String _channelName = 'performance_tier/device_signals';
  static const String _writeMethod = 'writePerformanceReport';
  static const String _listMethod = 'listPerformanceReports';

  final MethodChannel methodChannel;
  final bool isWeb;
  final TargetPlatform? targetPlatform;

  @override
  Future<PerformanceReportWriteResult> write(PerformanceReport report) async {
    _ensureAndroidHost();
    final result = await methodChannel
        .invokeMapMethod<String, dynamic>(_writeMethod, <String, Object?>{
          'reportId': report.reportId,
          'schemaVersion': report.schemaVersion,
          'fileName': report.defaultFileName,
          'content': report.toJson(),
        });
    if (result == null) {
      throw StateError('Android performance report write returned no result.');
    }
    return PerformanceReportWriteResult.fromMap(
      result,
      reportId: report.reportId,
    );
  }

  @override
  Future<List<PerformanceReportFile>> list() async {
    _ensureAndroidHost();
    final result = await methodChannel.invokeListMethod<Object?>(_listMethod);
    if (result == null) {
      return const <PerformanceReportFile>[];
    }
    return result
        .whereType<Map<Object?, Object?>>()
        .map(_stringKeyedMap)
        .map(PerformanceReportFile.fromMap)
        .toList(growable: false);
  }

  void _ensureAndroidHost() {
    final operatingSystem = resolveHostOperatingSystem(
      isWeb: isWeb,
      targetPlatform: targetPlatform,
    );
    if (operatingSystem != 'android') {
      throw UnsupportedError(
        'Android performance report storage is only available on Android hosts. '
        'Current host: $operatingSystem.',
      );
    }
  }

  static Map<String, dynamic> _stringKeyedMap(Map<Object?, Object?> map) {
    return <String, dynamic>{
      for (final entry in map.entries)
        if (entry.key is String) entry.key! as String: entry.value,
    };
  }
}

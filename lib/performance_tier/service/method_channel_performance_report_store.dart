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
    final writeResult = PerformanceReportWriteResult.fromMap(
      result,
      reportId: report.reportId,
    );
    if (writeResult.reportId != report.reportId) {
      throw FormatException(
        'Android performance report write returned mismatched reportId: '
        '${writeResult.reportId}.',
      );
    }
    return writeResult;
  }

  @override
  Future<List<PerformanceReportFile>> list() async {
    _ensureAndroidHost();
    final result = await methodChannel.invokeListMethod<Object?>(_listMethod);
    if (result == null) {
      return const <PerformanceReportFile>[];
    }
    final reports = <PerformanceReportFile>[];
    for (var index = 0; index < result.length; index += 1) {
      final item = result[index];
      if (item is! Map<Object?, Object?>) {
        throw FormatException(
          'Android performance report list returned a non-map item '
          'at index $index.',
        );
      }
      reports.add(
        PerformanceReportFile.fromMap(
          _stringKeyedMap(item, context: 'report list item $index'),
        ),
      );
    }
    reports.sort(_compareReportFiles);
    return reports;
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

  static Map<String, dynamic> _stringKeyedMap(
    Map<Object?, Object?> map, {
    required String context,
  }) {
    final result = <String, dynamic>{};
    for (final entry in map.entries) {
      final key = entry.key;
      if (key is! String) {
        throw FormatException(
          'Android performance report $context returned a non-string key.',
        );
      }
      result[key] = entry.value;
    }
    return result;
  }

  static int _compareReportFiles(
    PerformanceReportFile left,
    PerformanceReportFile right,
  ) {
    final leftModifiedAt = left.modifiedAt;
    final rightModifiedAt = right.modifiedAt;
    if (leftModifiedAt != null && rightModifiedAt != null) {
      final modifiedComparison = rightModifiedAt.compareTo(leftModifiedAt);
      if (modifiedComparison != 0) {
        return modifiedComparison;
      }
    } else if (leftModifiedAt != null) {
      return -1;
    } else if (rightModifiedAt != null) {
      return 1;
    }
    return right.fileName.compareTo(left.fileName);
  }
}

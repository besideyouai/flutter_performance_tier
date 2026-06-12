import 'dart:io';

import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Platform field integrity', () {
    test(
      'android native handler keeps method-channel contract and keys',
      () async {
        final source = await File(_androidHandlerPath).readAsString();

        expect(source, contains(_channelName));
        expect(source, contains(_collectMethod));
        expect(source, contains(_writeReportMethod));
        expect(source, contains(_listReportsMethod));
        expect(source, contains(_reportsDirectoryName));
        for (final key in _androidExpectedKeys) {
          expect(source, contains('"$key"'));
        }
      },
    );

    test(
      'android native report writer keeps private safe-file boundary',
      () async {
        final source = await File(_androidHandlerPath).readAsString();

        expect(source, contains('currentPerformanceReportSchemaVersion'));
        expect(source, contains('call.argument<Int>("schemaVersion")'));
        expect(source, contains('invalid_report_schema_version'));
        expect(source, contains('reportId.isNullOrBlank()'));
        expect(source, contains('invalid_report_id'));
        expect(source, contains('invalid_report_content'));
        expect(source, contains('invalid_report_file_name'));
        expect(source, contains('isSafeReportFileName'));
        expect(
          source,
          contains('file.isFile && isSafeReportFileName(file.name)'),
        );
        expect(source, contains('fileName.endsWith(".json")'));
        expect(
          source,
          contains(
            "char.isLetterOrDigit() || char == '-' || char == '_' || char == '.'",
          ),
        );
        expect(source, contains('nextAvailableReportFile'));
        expect(source, contains('writeText(content, Charsets.UTF_8)'));
      },
    );

    test('ios native handler keeps method-channel contract and keys', () async {
      final source = await File(_iosAppDelegatePath).readAsString();

      expect(source, contains(_channelName));
      expect(source, contains(_collectMethod));
      for (final key in _iosExpectedKeys) {
        expect(source, contains('"$key"'));
      }
    });

    test('parses complete android payload with deviceModel signal', () {
      final collectedAt = DateTime(2026, 2, 25, 12);
      final signals = DeviceSignals.fromMap(<String, Object?>{
        'platform': 'android',
        'deviceModel': 'Pixel 8 Pro',
        'osVersion': '15',
        'totalRamBytes': 8 * _bytesPerGb,
        'isLowRamDevice': false,
        'mediaPerformanceClass': 13,
        'sdkInt': 35,
        'thermalState': 'fair',
        'thermalStateLevel': 1,
        'isLowPowerModeEnabled': true,
        'memoryPressureState': 'moderate',
        'memoryPressureLevel': 1,
        'frameDropState': 'moderate',
        'frameDropLevel': 1,
        'frameDropRate': 0.2,
        'frameDroppedCount': 12,
        'frameSampledCount': 60,
      }, collectedAt: collectedAt);

      expect(signals.platform, 'android');
      expect(signals.deviceModel, 'Pixel 8 Pro');
      expect(signals.osVersion, '15');
      expect(signals.totalRamBytes, 8 * _bytesPerGb);
      expect(signals.totalRamMb, 8192);
      expect(signals.isLowRamDevice, isFalse);
      expect(signals.mediaPerformanceClass, 13);
      expect(signals.sdkInt, 35);
      expect(signals.thermalState, 'fair');
      expect(signals.thermalStateLevel, 1);
      expect(signals.isLowPowerModeEnabled, isTrue);
      expect(signals.memoryPressureState, 'moderate');
      expect(signals.memoryPressureLevel, 1);
      expect(signals.frameDropState, 'moderate');
      expect(signals.frameDropLevel, 1);
      expect(signals.frameDropRate, 0.2);
      expect(signals.frameDroppedCount, 12);
      expect(signals.frameSampledCount, 60);
      expect(signals.toMap().keys, containsAll(_allSignalKeys));
    });

    test(
      'parses ios payload when optional mediaPerformanceClass is absent',
      () {
        final collectedAt = DateTime(2026, 2, 25, 12);
        final signals = DeviceSignals.fromMap(<String, Object?>{
          'platform': 'ios',
          'deviceModel': 'iPhone16,2',
          'osVersion': 'iOS 18.0',
          'totalRamBytes': '${6 * _bytesPerGb}',
          'isLowRamDevice': 'false',
          'sdkInt': 18,
          'thermalState': 'serious',
          'thermalStateLevel': 2,
          'isLowPowerModeEnabled': true,
          'memoryPressureState': 'critical',
          'memoryPressureLevel': 2,
          'frameDropState': 'critical',
          'frameDropLevel': '2',
          'frameDropRate': '0.35',
          'frameDroppedCount': '21',
          'frameSampledCount': 60,
        }, collectedAt: collectedAt);

        expect(signals.platform, 'ios');
        expect(signals.deviceModel, 'iPhone16,2');
        expect(signals.osVersion, 'iOS 18.0');
        expect(signals.totalRamBytes, 6 * _bytesPerGb);
        expect(signals.isLowRamDevice, isFalse);
        expect(signals.mediaPerformanceClass, isNull);
        expect(signals.sdkInt, 18);
        expect(signals.thermalState, 'serious');
        expect(signals.thermalStateLevel, 2);
        expect(signals.isLowPowerModeEnabled, isTrue);
        expect(signals.memoryPressureState, 'critical');
        expect(signals.memoryPressureLevel, 2);
        expect(signals.frameDropState, 'critical');
        expect(signals.frameDropLevel, 2);
        expect(signals.frameDropRate, 0.35);
        expect(signals.frameDroppedCount, 21);
        expect(signals.frameSampledCount, 60);
        expect(signals.toMap().keys, containsAll(_allSignalKeys));
      },
    );
  });
}

const String _androidHandlerPath =
    'android/src/main/kotlin/com/example/flutter_performance_tier/FlutterPerformanceTierPlugin.kt';
const String _iosAppDelegatePath =
    'ios/Classes/FlutterPerformanceTierPlugin.swift';

const String _channelName = 'performance_tier/device_signals';
const String _collectMethod = 'collectDeviceSignals';
const String _writeReportMethod = 'writePerformanceReport';
const String _listReportsMethod = 'listPerformanceReports';
const String _reportsDirectoryName = 'performance_tier_reports';
const int _bytesPerGb = 1024 * 1024 * 1024;

const List<String> _androidExpectedKeys = <String>[
  'platform',
  'deviceModel',
  'osVersion',
  'totalRamBytes',
  'isLowRamDevice',
  'mediaPerformanceClass',
  'sdkInt',
  'thermalState',
  'thermalStateLevel',
  'isLowPowerModeEnabled',
  'memoryPressureState',
  'memoryPressureLevel',
];

const List<String> _iosExpectedKeys = <String>[
  'platform',
  'deviceModel',
  'osVersion',
  'totalRamBytes',
  'isLowRamDevice',
  'sdkInt',
  'thermalState',
  'thermalStateLevel',
  'isLowPowerModeEnabled',
  'memoryPressureState',
  'memoryPressureLevel',
];

const List<String> _allSignalKeys = <String>[
  'platform',
  'deviceModel',
  'osVersion',
  'totalRamBytes',
  'isLowRamDevice',
  'mediaPerformanceClass',
  'sdkInt',
  'thermalState',
  'thermalStateLevel',
  'isLowPowerModeEnabled',
  'memoryPressureState',
  'memoryPressureLevel',
  'frameDropState',
  'frameDropLevel',
  'frameDropRate',
  'frameDroppedCount',
  'frameSampledCount',
  'collectedAt',
];

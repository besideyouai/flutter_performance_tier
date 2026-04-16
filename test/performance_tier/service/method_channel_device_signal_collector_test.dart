import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_performance_tier/flutter_performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('MethodChannelDeviceSignalCollector', () {
    test(
      'uses host platform fallback by default on non-mobile flutter_test hosts',
      () async {
        final calls = <MethodCall>[];
        final channel = const MethodChannel('test/perf_tier/default_host');
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, (MethodCall call) async {
              calls.add(call);
              return <String, Object?>{'deviceModel': 'should-not-be-used'};
            });
        addTearDown(() {
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
              .setMockMethodCallHandler(channel, null);
        });

        final collector = MethodChannelDeviceSignalCollector(
          methodChannel: channel,
        );

        final signals = await collector.collect();

        expect(signals.platform, Platform.operatingSystem);
        expect(signals.deviceModel, isNull);
        expect(calls, isEmpty);
      },
      skip: kIsWeb || Platform.isAndroid || Platform.isIOS,
    );

    test('returns web fallback signals without invoking the channel', () async {
      final calls = <MethodCall>[];
      final channel = const MethodChannel('test/perf_tier/web');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            calls.add(call);
            return <String, Object?>{'deviceModel': 'should-not-be-used'};
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });

      final collector = MethodChannelDeviceSignalCollector(
        methodChannel: channel,
        isWeb: true,
      );

      final signals = await collector.collect();

      expect(signals.platform, 'web');
      expect(signals.deviceModel, isNull);
      expect(calls, isEmpty);
    });

    test(
      'returns desktop fallback signals without invoking the channel',
      () async {
        final cases = <({TargetPlatform platform, String operatingSystem})>[
          (platform: TargetPlatform.macOS, operatingSystem: 'macos'),
          (platform: TargetPlatform.windows, operatingSystem: 'windows'),
          (platform: TargetPlatform.linux, operatingSystem: 'linux'),
          (platform: TargetPlatform.fuchsia, operatingSystem: 'fuchsia'),
        ];

        for (final testCase in cases) {
          final calls = <MethodCall>[];
          final channel = MethodChannel(
            'test/perf_tier/${testCase.operatingSystem}',
          );
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
              .setMockMethodCallHandler(channel, (MethodCall call) async {
                calls.add(call);
                return <String, Object?>{'deviceModel': 'should-not-be-used'};
              });
          addTearDown(() {
            TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
                .setMockMethodCallHandler(channel, null);
          });

          final collector = MethodChannelDeviceSignalCollector(
            methodChannel: channel,
            targetPlatform: testCase.platform,
          );

          final signals = await collector.collect();

          expect(signals.platform, testCase.operatingSystem);
          expect(signals.deviceModel, isNull);
          expect(calls, isEmpty);
        }
      },
      skip: kIsWeb,
    );

    test('keeps using the Android method-channel contract', () async {
      final calls = <MethodCall>[];
      final channel = const MethodChannel('test/perf_tier/android');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            calls.add(call);
            return <String, Object?>{
              'deviceModel': 'Pixel 8 Pro',
              'totalRamBytes': 8 * 1024 * 1024 * 1024,
              'sdkInt': 35,
            };
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });

      final collector = MethodChannelDeviceSignalCollector(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      final signals = await collector.collect();

      expect(calls, hasLength(1));
      expect(calls.single.method, 'collectDeviceSignals');
      expect(signals.platform, 'android');
      expect(signals.deviceModel, 'Pixel 8 Pro');
      expect(signals.totalRamBytes, 8 * 1024 * 1024 * 1024);
      expect(signals.sdkInt, 35);
    }, skip: kIsWeb);

    test('keeps using the iOS method-channel contract', () async {
      final calls = <MethodCall>[];
      final channel = const MethodChannel('test/perf_tier/ios');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            calls.add(call);
            return <String, Object?>{
              'deviceModel': 'iPhone16,2',
              'totalRamBytes': 6 * 1024 * 1024 * 1024,
              'sdkInt': 18,
              'thermalState': 'serious',
            };
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });

      final collector = MethodChannelDeviceSignalCollector(
        methodChannel: channel,
        targetPlatform: TargetPlatform.iOS,
      );

      final signals = await collector.collect();

      expect(calls, hasLength(1));
      expect(calls.single.method, 'collectDeviceSignals');
      expect(signals.platform, 'ios');
      expect(signals.deviceModel, 'iPhone16,2');
      expect(signals.totalRamBytes, 6 * 1024 * 1024 * 1024);
      expect(signals.sdkInt, 18);
      expect(signals.thermalState, 'serious');
    }, skip: kIsWeb);
  });
}

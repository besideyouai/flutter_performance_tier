import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_performance_tier/performance_tier/performance_tier.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('MethodChannelPerformanceReportStore', () {
    test('writes report through the Android method-channel contract', () async {
      final calls = <MethodCall>[];
      final channel = const MethodChannel('test/perf_tier/report_write');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            calls.add(call);
            final arguments = call.arguments as Map<Object?, Object?>;
            final content = arguments['content'] as String;
            final decoded = jsonDecode(content) as Map<String, dynamic>;
            expect(decoded['schemaVersion'], 1);
            expect(arguments['fileName'], contains('performance_tier_v1_'));
            return <String, Object?>{
              'reportId': arguments['reportId'],
              'fileName': arguments['fileName'],
              'relativePath':
                  'files/performance_tier_reports/${arguments['fileName']}',
              'bytes': content.length,
              'writtenAtEpochMs': 1781111111000,
            };
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });
      final store = MethodChannelPerformanceReportStore(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      final result = await store.write(_report());

      expect(calls, hasLength(1));
      expect(calls.single.method, 'writePerformanceReport');
      expect(result.reportId, 'report-1');
      expect(
        result.relativePath,
        startsWith('files/performance_tier_reports/'),
      );
      expect(result.bytes, greaterThan(0));
    }, skip: kIsWeb);

    test('rejects incomplete native write results', () async {
      final channel = const MethodChannel('test/perf_tier/report_incomplete');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            return <String, Object?>{'fileName': 'report.json', 'bytes': 12};
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });
      final store = MethodChannelPerformanceReportStore(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      expect(store.write(_report()), throwsA(isA<FormatException>()));
    }, skip: kIsWeb);

    test('rejects mismatched native write report id', () async {
      final channel = const MethodChannel('test/perf_tier/report_mismatch');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            return <String, Object?>{
              'reportId': 'other-report',
              'fileName': 'report.json',
              'relativePath': 'files/performance_tier_reports/report.json',
              'bytes': 12,
            };
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });
      final store = MethodChannelPerformanceReportStore(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      expect(store.write(_report()), throwsA(isA<FormatException>()));
    }, skip: kIsWeb);

    test('lists reports through the Android method-channel contract', () async {
      final calls = <MethodCall>[];
      final channel = const MethodChannel('test/perf_tier/report_list');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            calls.add(call);
            return <Object?>[
              <String, Object?>{
                'fileName': 'report-old.json',
                'relativePath':
                    'files/performance_tier_reports/report-old.json',
                'bytes': 10,
                'modifiedAtEpochMs': 1781111110000,
              },
              <String, Object?>{
                'fileName': 'report-no-time.json',
                'relativePath':
                    'files/performance_tier_reports/report-no-time.json',
                'bytes': 12,
              },
              <String, Object?>{
                'fileName': 'report-new.json',
                'relativePath':
                    'files/performance_tier_reports/report-new.json',
                'bytes': 20,
                'modifiedAtEpochMs': 1781111112000,
              },
            ];
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });
      final store = MethodChannelPerformanceReportStore(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      final reports = await store.list();

      expect(calls, hasLength(1));
      expect(calls.single.method, 'listPerformanceReports');
      expect(
        reports.map((PerformanceReportFile report) => report.fileName),
        <String>['report-new.json', 'report-old.json', 'report-no-time.json'],
      );
      expect(reports.first.bytes, 20);
    }, skip: kIsWeb);

    test('rejects malformed native list items', () async {
      final channel = const MethodChannel(
        'test/perf_tier/report_list_bad_item',
      );
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            return <Object?>[
              <String, Object?>{
                'fileName': 'report.json',
                'relativePath': 'files/performance_tier_reports/report.json',
                'bytes': 10,
              },
              'not-a-map',
            ];
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });
      final store = MethodChannelPerformanceReportStore(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      expect(store.list(), throwsA(isA<FormatException>()));
    }, skip: kIsWeb);

    test('rejects native list metadata with non-string keys', () async {
      final channel = const MethodChannel('test/perf_tier/report_list_bad_key');
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(channel, (MethodCall call) async {
            return <Object?>[
              <Object?, Object?>{
                1: 'report.json',
                'relativePath': 'files/performance_tier_reports/report.json',
                'bytes': 10,
              },
            ];
          });
      addTearDown(() {
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, null);
      });
      final store = MethodChannelPerformanceReportStore(
        methodChannel: channel,
        targetPlatform: TargetPlatform.android,
      );

      expect(store.list(), throwsA(isA<FormatException>()));
    }, skip: kIsWeb);

    test(
      'rejects non-Android hosts before invoking the channel',
      () async {
        final calls = <MethodCall>[];
        final channel = const MethodChannel('test/perf_tier/report_desktop');
        TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
            .setMockMethodCallHandler(channel, (MethodCall call) async {
              calls.add(call);
              return null;
            });
        addTearDown(() {
          TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
              .setMockMethodCallHandler(channel, null);
        });
        final store = MethodChannelPerformanceReportStore(
          methodChannel: channel,
          targetPlatform: TargetPlatform.macOS,
        );

        expect(store.write(_report()), throwsUnsupportedError);
        expect(calls, isEmpty);
      },
      skip: kIsWeb || Platform.isAndroid,
    );
  });
}

PerformanceReport _report() {
  return PerformanceReport.fromDecision(
    decision: TierDecision(
      tier: TierLevel.t1Mid,
      confidence: TierConfidence.medium,
      deviceSignals: DeviceSignals(
        platform: 'android',
        collectedAt: DateTime.utc(2026, 6, 11),
      ),
      decidedAt: DateTime.utc(2026, 6, 11, 8),
    ),
    generatedAt: DateTime.utc(2026, 6, 11, 8, 1),
    reportId: 'report-1',
  );
}

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../model/device_signals.dart';
import 'device_signal_collector.dart';
import 'host_platform_resolver.dart';

class MethodChannelDeviceSignalCollector implements DeviceSignalCollector {
  MethodChannelDeviceSignalCollector({
    MethodChannel methodChannel = const MethodChannel(_channelName),
    bool isWeb = kIsWeb,
    TargetPlatform? targetPlatform,
  }) : _methodChannel = methodChannel,
       _isWeb = isWeb,
       _targetPlatform = targetPlatform;

  static const String _channelName = 'performance_tier/device_signals';
  static const String _collectMethod = 'collectDeviceSignals';

  final MethodChannel _methodChannel;
  final bool _isWeb;
  final TargetPlatform? _targetPlatform;

  @override
  Future<DeviceSignals> collect() async {
    final now = DateTime.now();
    final operatingSystem = _resolveOperatingSystem();

    if (operatingSystem != 'android' && operatingSystem != 'ios') {
      return DeviceSignals(platform: operatingSystem, collectedAt: now);
    }

    final result = await _methodChannel.invokeMapMethod<String, dynamic>(
      _collectMethod,
    );
    final normalized = <String, dynamic>{
      'platform': operatingSystem,
      ...?result,
    };

    return DeviceSignals.fromMap(normalized, collectedAt: now);
  }

  String _resolveOperatingSystem() {
    return resolveHostOperatingSystem(
      isWeb: _isWeb,
      targetPlatform: _targetPlatform,
    );
  }
}

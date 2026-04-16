import 'package:flutter/foundation.dart';

import 'host_platform_resolver_default.dart'
    if (dart.library.io) 'host_platform_resolver_io.dart'
    as host_platform;

String resolveHostOperatingSystem({
  required bool isWeb,
  TargetPlatform? targetPlatform,
}) {
  if (isWeb) {
    return 'web';
  }

  if (targetPlatform != null) {
    return switch (targetPlatform) {
      TargetPlatform.android => 'android',
      TargetPlatform.iOS => 'ios',
      TargetPlatform.macOS => 'macos',
      TargetPlatform.windows => 'windows',
      TargetPlatform.linux => 'linux',
      TargetPlatform.fuchsia => 'fuchsia',
    };
  }

  return host_platform.resolveHostOperatingSystem();
}

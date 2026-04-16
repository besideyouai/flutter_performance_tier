import 'package:flutter/material.dart';

import 'demo/performance_tier_demo_app.dart';

void main() {
  runApp(const PerformanceTierInternalUploadProbeApp());
}

class PerformanceTierInternalUploadProbeApp extends StatelessWidget {
  const PerformanceTierInternalUploadProbeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const PerformanceTierDemoApp(
      title: 'Performance Tier Internal Upload Probe',
      introText:
          'Internal validation entrypoint. The default main demo now includes '
          'upload probe controls too; this target keeps the same workflow '
          'available as a dedicated entrypoint.',
      eagerBootstrapUploadProbe: true,
    );
  }
}

import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_performance_tier/main.dart';

void main() {
  testWidgets('renders structured diagnostics demo with refresh action', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(
      const PerformanceTierDemoApp(eagerBootstrapUploadProbe: false),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 50));

    expect(find.text('Performance Tier Diagnostics'), findsOneWidget);
    expect(find.byTooltip('Refresh decision'), findsOneWidget);
    expect(find.byTooltip('Copy AI report'), findsOneWidget);
    expect(
      find.textContaining('Structured diagnostics demo.'),
      findsOneWidget,
    );
    expect(find.text('Runtime signal preset'), findsOneWidget);
    expect(find.text('Live device'), findsOneWidget);
    expect(find.text('Memory critical'), findsOneWidget);
    expect(find.text('Thermal serious'), findsOneWidget);
    expect(find.text('Upload probe'), findsOneWidget);
    expect(find.text('Run /upload probe'), findsOneWidget);
    expect(find.text('Clear auth session'), findsOneWidget);
    expect(find.text('AI Diagnostics JSON'), findsOneWidget);
    expect(find.textContaining('"recentStructuredLogs"'), findsOneWidget);
    expect(find.textContaining('"demoRuntimeSignalPreset"'), findsOneWidget);
    expect(find.textContaining('"uploadProbe"'), findsOneWidget);
  });
}

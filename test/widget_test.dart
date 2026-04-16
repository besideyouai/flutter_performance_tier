import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_performance_tier/main.dart';

void main() {
  testWidgets(
    'renders public example view with internal tools hidden by default',
    (WidgetTester tester) async {
      await tester.pumpWidget(
        const PerformanceTierDemoApp(eagerBootstrapUploadProbe: false),
      );
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 50));

      expect(find.text('Performance Tier Diagnostics'), findsOneWidget);
      expect(find.byTooltip('Refresh decision'), findsOneWidget);
      expect(find.byTooltip('Copy AI report'), findsOneWidget);
      expect(find.textContaining('lightweight example'), findsOneWidget);
      expect(find.text('Decision Summary'), findsOneWidget);
      expect(find.text('Device Signals'), findsOneWidget);
      expect(find.text('Resolved Policies'), findsOneWidget);
      expect(find.text('Internal Tools'), findsOneWidget);
      expect(find.textContaining('tier='), findsWidgets);
      expect(find.textContaining('runtime='), findsWidgets);
      expect(find.textContaining('platform'), findsWidgets);
      expect(find.textContaining('animationLevel'), findsWidgets);
      expect(find.text('AI Diagnostics JSON'), findsOneWidget);
      expect(find.text('Run /upload probe'), findsNothing);
      expect(find.text('Clear auth session'), findsNothing);
      expect(find.text('Copy latest log'), findsNothing);
      expect(find.text('Runtime signal preset'), findsNothing);
      expect(find.text('Live device'), findsNothing);
      expect(find.text('Memory critical'), findsNothing);
      expect(find.text('Thermal serious'), findsNothing);

      await tester.ensureVisible(find.text('Internal Tools'));
      await tester.tap(find.text('Internal Tools'));
      await tester.pumpAndSettle();

      expect(find.text('Copy latest log'), findsOneWidget);
      expect(find.text('Runtime signal preset'), findsOneWidget);
      expect(find.text('Live device'), findsOneWidget);
      expect(find.text('Memory critical'), findsOneWidget);
      expect(find.text('Thermal serious'), findsOneWidget);
      expect(find.text('Run /upload probe'), findsOneWidget);
      expect(find.text('Clear auth session'), findsOneWidget);
    },
  );
}

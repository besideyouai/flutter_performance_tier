import 'dart:async';

import 'package:flutter/material.dart';

import 'demo_runtime_signal_support.dart';
import 'performance_tier_demo_controller.dart';
import 'performance_tier_diagnostics_scaffold.dart';
import 'performance_tier_upload_probe_controller.dart';

class PerformanceTierDemoApp extends StatelessWidget {
  const PerformanceTierDemoApp({
    super.key,
    this.title = 'Performance Tier Diagnostics',
    this.introText =
        'Structured diagnostics demo. Runtime signal presets and upload probe '
        'controls are available for local acceptance checks.',
    this.eagerBootstrapUploadProbe = true,
  });

  final String title;
  final String introText;
  final bool eagerBootstrapUploadProbe;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: title,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0B6E4F),
        ),
        useMaterial3: true,
      ),
      home: PerformanceTierDemoPage(
        title: title,
        introText: introText,
        eagerBootstrapUploadProbe: eagerBootstrapUploadProbe,
      ),
    );
  }
}

class PerformanceTierDemoPage extends StatefulWidget {
  const PerformanceTierDemoPage({
    super.key,
    required this.title,
    required this.introText,
    required this.eagerBootstrapUploadProbe,
  });

  final String title;
  final String introText;
  final bool eagerBootstrapUploadProbe;

  @override
  State<PerformanceTierDemoPage> createState() =>
      _PerformanceTierDemoPageState();
}

class _PerformanceTierDemoPageState extends State<PerformanceTierDemoPage> {
  late final PerformanceTierDemoController _controller =
      PerformanceTierDemoController();
  late final PerformanceTierUploadProbeController _uploadProbeController =
      PerformanceTierUploadProbeController(
        logger: _controller.recordDiagnosticLog,
      );
  late final Listenable _pageListenable =
      Listenable.merge(<Listenable>[_controller, _uploadProbeController]);

  @override
  void initState() {
    super.initState();
    unawaited(_controller.start());
    if (widget.eagerBootstrapUploadProbe) {
      unawaited(_uploadProbeController.start());
    }
  }

  @override
  void dispose() {
    unawaited(_uploadProbeController.dispose());
    unawaited(_controller.close());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pageListenable,
      builder: (BuildContext context, Widget? child) {
        return PerformanceTierDiagnosticsScaffold(
          title: widget.title,
          introText: widget.introText,
          headline: _controller.buildHeadline(),
          report: _buildAiReport(),
          error: _controller.error,
          isRefreshing: _controller.refreshing,
          onRefresh: _controller.refreshDecision,
          onCopyAiReport: () => _controller.copyAiReport(
            context,
            extraSections: _buildExtraSections(),
          ),
          onCopyLatestLogLine: () => _controller.copyLatestLogLine(context),
          controlButtons: <Widget>[
            FilledButton.icon(
              onPressed: _uploadProbeController.runningUpload
                  ? null
                  : _runUploadProbe,
              icon: _uploadProbeController.runningUpload
                  ? const SizedBox.square(
                      dimension: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.cloud_upload),
              label: Text(
                _uploadProbeController.runningUpload
                    ? 'Uploading...'
                    : 'Run /upload probe',
              ),
            ),
            OutlinedButton.icon(
              onPressed: _uploadProbeController.runningUpload ||
                      _uploadProbeController.clearingSession
                  ? null
                  : _clearAuthSession,
              icon: _uploadProbeController.clearingSession
                  ? const SizedBox.square(
                      dimension: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.logout),
              label: Text(
                _uploadProbeController.clearingSession
                    ? 'Clearing...'
                    : 'Clear auth session',
              ),
            ),
          ],
          sectionsBeforeReport: <Widget>[
            if (_controller.supportsRuntimeSignalPresets)
              _RuntimeSignalPresetPanel(
                currentPreset: _controller.runtimeSignalPreset,
                onSelected: _controller.selectRuntimeSignalPreset,
              ),
            _UploadProbePanel(controller: _uploadProbeController),
          ],
        );
      },
    );
  }

  Map<String, Object?> _buildExtraSections() {
    return <String, Object?>{
      ..._controller.buildDemoSections(),
      ..._uploadProbeController.buildReportSections(),
    };
  }

  String _buildAiReport() {
    return _controller.buildAiReport(extraSections: _buildExtraSections());
  }

  Future<void> _runUploadProbe() {
    return _uploadProbeController.runUploadProbe(reportBuilder: _buildAiReport);
  }

  Future<void> _clearAuthSession() {
    return _uploadProbeController.clearAuthSession();
  }
}

class _RuntimeSignalPresetPanel extends StatelessWidget {
  const _RuntimeSignalPresetPanel({
    required this.currentPreset,
    required this.onSelected,
  });

  final DemoRuntimeSignalPreset currentPreset;
  final Future<void> Function(DemoRuntimeSignalPreset preset) onSelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: theme.dividerColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Runtime signal preset',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'Acceptance helper: auto-polls every 1s. A pressure preset '
              'should reach active in about 1s; switching back to Live device '
              'should pass through cooldown and recover in about 4s.',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: DemoRuntimeSignalPreset.values.map((preset) {
                return ChoiceChip(
                  label: Text(preset.label),
                  selected: preset == currentPreset,
                  onSelected: (bool selected) {
                    if (!selected) {
                      return;
                    }
                    unawaited(onSelected(preset));
                  },
                );
              }).toList(),
            ),
            const SizedBox(height: 8),
            Text(
              currentPreset.summary,
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _UploadProbePanel extends StatelessWidget {
  const _UploadProbePanel({required this.controller});

  final PerformanceTierUploadProbeController controller;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final config = controller.config;
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: theme.dividerColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Upload probe',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'The default demo can upload the current diagnostics JSON '
              'directly. Configure auth with secure env or --dart-define '
              'before running the probe.',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Upload endpoint: ${config?.uploadUri ?? '-'}',
              style: theme.textTheme.bodySmall,
            ),
            Text(
              'Login endpoint: ${config?.authConfig.loginUrl ?? '-'}',
              style: theme.textTheme.bodySmall,
            ),
            Text(
              'Upload source: ${config?.source ?? '-'}',
              style: theme.textTheme.bodySmall,
            ),
            Text(
              'Auth status: ${controller.authStatus}',
              style: theme.textTheme.bodySmall,
            ),
            Text(
              'Auth subject: ${controller.authSubject}',
              style: theme.textTheme.bodySmall,
            ),
            Text(
              'Auth expiresAt: ${controller.authExpiresAt}',
              style: theme.textTheme.bodySmall,
            ),
            Text(
              'Auth token: ${controller.authTokenPreview}',
              style: theme.textTheme.bodySmall,
            ),
            if (controller.setupError != null) ...<Widget>[
              const SizedBox(height: 8),
              Text(
                'Upload setup error: ${controller.setupError}',
                style: TextStyle(color: theme.colorScheme.error),
              ),
            ],
            if (controller.uploadError != null) ...<Widget>[
              const SizedBox(height: 8),
              Text(
                'Upload error: ${controller.uploadError}',
                style: TextStyle(color: theme.colorScheme.error),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              'Upload result',
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 4),
            SelectableText(
              controller.uploadResult,
              style: const TextStyle(fontFamily: 'monospace'),
            ),
          ],
        ),
      ),
    );
  }
}

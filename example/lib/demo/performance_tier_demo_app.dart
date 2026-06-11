import 'dart:async';

import 'package:flutter/material.dart';

import 'demo_runtime_signal_support.dart';
import 'internal_tools_controller.dart';
import 'performance_tier_demo_controller.dart';
import 'performance_tier_diagnostics_scaffold.dart';
import 'performance_tier_upload_probe_controller.dart';
import 'package:flutter_performance_tier/flutter_performance_tier.dart';

class PerformanceTierDemoApp extends StatelessWidget {
  const PerformanceTierDemoApp({
    super.key,
    this.title = 'Performance Tier Diagnostics',
    this.introText =
        'A lightweight example of the performance tier decision flow. '
        'Internal tools are available for local acceptance checks.',
    this.eagerBootstrapUploadProbe = false,
  });

  final String title;
  final String introText;
  final bool eagerBootstrapUploadProbe;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: title,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0B6E4F)),
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
  late final InternalToolsController _internalToolsController =
      InternalToolsController();
  late final PerformanceTierDemoController _controller =
      PerformanceTierDemoController(
        internalToolsController: _internalToolsController,
      );
  late final Listenable _pageListenable = Listenable.merge(<Listenable>[
    _controller,
    _internalToolsController,
  ]);

  @override
  void initState() {
    super.initState();
    unawaited(_controller.start());
    if (widget.eagerBootstrapUploadProbe) {
      unawaited(_internalToolsController.start());
    }
  }

  @override
  void dispose() {
    unawaited(_internalToolsController.close());
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
          sectionsBeforeReport: <Widget>[
            _DecisionSummarySection(decision: _controller.decision),
            _DecisionSignalsSection(decision: _controller.decision),
            _ResolvedPoliciesSection(decision: _controller.decision),
            _InternalToolsSection(
              supportsRuntimeSignalPresets:
                  _controller.supportsRuntimeSignalPresets,
              currentPreset: _internalToolsController.runtimeSignalPreset,
              onSelectedPreset: _onSelectedPreset,
              writingAndroidReport: _controller.writingAndroidReport,
              listingAndroidReports: _controller.listingAndroidReports,
              lastReportWriteResult: _controller.lastReportWriteResult,
              androidReportFiles: _controller.androidReportFiles,
              androidReportError: _controller.androidReportError,
              androidReportCommands: _controller.buildAndroidReportCommands(),
              onWriteAndroidReport: _controller.writeAndroidReport,
              onListAndroidReports: _controller.listAndroidReports,
              onCopyAndroidReportCommands: () =>
                  _controller.copyAndroidReportCommands(context),
              uploadProbeController:
                  _internalToolsController.uploadProbeController,
              onRunUploadProbe: _runUploadProbe,
              onClearAuthSession: _internalToolsController.clearAuthSession,
              onCopyLatestLogLine: () =>
                  _internalToolsController.copyLatestLogLine(context),
            ),
          ],
        );
      },
    );
  }

  Map<String, Object?> _buildExtraSections() {
    return <String, Object?>{
      ..._internalToolsController.buildReportSections(),
      ..._controller.buildAndroidReportSections(),
    };
  }

  String _buildAiReport() {
    return _controller.buildAiReport(extraSections: _buildExtraSections());
  }

  Future<void> _runUploadProbe() {
    return _internalToolsController.runUploadProbe(
      reportBuilder: _buildAiReport,
    );
  }

  Future<void> _onSelectedPreset(DemoRuntimeSignalPreset preset) async {
    await _internalToolsController.selectRuntimeSignalPreset(preset);
    await _controller.syncWithInternalToolsState();
    await _controller.refreshDecision();
  }
}

class _DecisionSummarySection extends StatelessWidget {
  const _DecisionSummarySection({required this.decision});

  final TierDecision? decision;

  @override
  Widget build(BuildContext context) {
    final runtimeObservation = decision?.runtimeObservation;
    return _InfoSection(
      title: 'Decision Summary',
      rows: <String>[
        'tier=${decision?.tier.name ?? '-'}',
        'confidence=${decision?.confidence.name ?? '-'}',
        'runtime=${runtimeObservation?.status.wireName ?? '-'}',
        'reasons=${decision?.reasons.length ?? 0}',
      ],
    );
  }
}

class _DecisionSignalsSection extends StatelessWidget {
  const _DecisionSignalsSection({required this.decision});

  final TierDecision? decision;

  @override
  Widget build(BuildContext context) {
    final signals = decision?.deviceSignals;
    return _InfoSection(
      title: 'Device Signals',
      rows: <String>[
        'platform: ${signals?.platform ?? '-'}',
        'deviceModel: ${signals?.deviceModel ?? '-'}',
        'totalRamBytes: ${signals?.totalRamBytes ?? '-'}',
        'memoryPressureState: ${signals?.memoryPressureState ?? '-'}',
        'thermalState: ${signals?.thermalState ?? '-'}',
      ],
    );
  }
}

class _ResolvedPoliciesSection extends StatelessWidget {
  const _ResolvedPoliciesSection({required this.decision});

  final TierDecision? decision;

  @override
  Widget build(BuildContext context) {
    final policies = decision?.appliedPolicies ?? const <String, Object?>{};
    return _InfoSection(
      title: 'Resolved Policies',
      rows: <String>[
        'animationLevel: ${policies['animationLevel'] ?? '-'}',
        'mediaPreloadCount: ${policies['mediaPreloadCount'] ?? '-'}',
        'decodeConcurrency: ${policies['decodeConcurrency'] ?? '-'}',
        'imageMaxSidePx: ${policies['imageMaxSidePx'] ?? '-'}',
      ],
    );
  }
}

class _InfoSection extends StatelessWidget {
  const _InfoSection({required this.title, required this.rows});

  final String title;
  final List<String> rows;

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
            Text(title, style: theme.textTheme.titleMedium),
            const SizedBox(height: 8),
            for (final row in rows) ...<Widget>[
              Text(row, style: theme.textTheme.bodyMedium),
              const SizedBox(height: 4),
            ],
          ],
        ),
      ),
    );
  }
}

class _InternalToolsSection extends StatelessWidget {
  const _InternalToolsSection({
    required this.supportsRuntimeSignalPresets,
    required this.currentPreset,
    required this.onSelectedPreset,
    required this.writingAndroidReport,
    required this.listingAndroidReports,
    required this.lastReportWriteResult,
    required this.androidReportFiles,
    required this.androidReportError,
    required this.androidReportCommands,
    required this.onWriteAndroidReport,
    required this.onListAndroidReports,
    required this.onCopyAndroidReportCommands,
    required this.uploadProbeController,
    required this.onRunUploadProbe,
    required this.onClearAuthSession,
    required this.onCopyLatestLogLine,
  });

  final bool supportsRuntimeSignalPresets;
  final DemoRuntimeSignalPreset currentPreset;
  final Future<void> Function(DemoRuntimeSignalPreset preset) onSelectedPreset;
  final bool writingAndroidReport;
  final bool listingAndroidReports;
  final PerformanceReportWriteResult? lastReportWriteResult;
  final List<PerformanceReportFile> androidReportFiles;
  final String? androidReportError;
  final String androidReportCommands;
  final Future<void> Function() onWriteAndroidReport;
  final Future<void> Function() onListAndroidReports;
  final Future<void> Function() onCopyAndroidReportCommands;
  final PerformanceTierUploadProbeController uploadProbeController;
  final Future<void> Function() onRunUploadProbe;
  final Future<void> Function() onClearAuthSession;
  final Future<void> Function() onCopyLatestLogLine;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).dividerColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: ExpansionTile(
        title: const Text('Internal Tools'),
        subtitle: const Text(
          'Android reports, runtime presets, structured logs, and upload '
          'probe helpers for internal validation.',
        ),
        childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
        children: <Widget>[
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              onPressed: onCopyLatestLogLine,
              icon: const Icon(Icons.copy),
              label: const Text('Copy latest log'),
            ),
          ),
          const SizedBox(height: 8),
          _AndroidReportActions(
            writingReport: writingAndroidReport,
            listingReports: listingAndroidReports,
            onWriteReport: onWriteAndroidReport,
            onListReports: onListAndroidReports,
            onCopyCommands: onCopyAndroidReportCommands,
          ),
          const SizedBox(height: 8),
          _AndroidReportPanel(
            lastWriteResult: lastReportWriteResult,
            files: androidReportFiles,
            error: androidReportError,
            adbCommands: androidReportCommands,
          ),
          const SizedBox(height: 8),
          if (supportsRuntimeSignalPresets)
            _RuntimeSignalPresetPanel(
              currentPreset: currentPreset,
              onSelected: onSelectedPreset,
            ),
          if (supportsRuntimeSignalPresets) const SizedBox(height: 8),
          _UploadProbeActions(
            controller: uploadProbeController,
            onRunUploadProbe: onRunUploadProbe,
            onClearAuthSession: onClearAuthSession,
          ),
          const SizedBox(height: 8),
          _UploadProbePanel(controller: uploadProbeController),
        ],
      ),
    );
  }
}

class _AndroidReportActions extends StatelessWidget {
  const _AndroidReportActions({
    required this.writingReport,
    required this.listingReports,
    required this.onWriteReport,
    required this.onListReports,
    required this.onCopyCommands,
  });

  final bool writingReport;
  final bool listingReports;
  final Future<void> Function() onWriteReport;
  final Future<void> Function() onListReports;
  final Future<void> Function() onCopyCommands;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: <Widget>[
        FilledButton.icon(
          onPressed: writingReport || listingReports ? null : onWriteReport,
          icon: writingReport
              ? const SizedBox.square(
                  dimension: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.description_outlined),
          label: Text(writingReport ? 'Generating...' : 'Generate report'),
        ),
        OutlinedButton.icon(
          onPressed: writingReport || listingReports ? null : onListReports,
          icon: listingReports
              ? const SizedBox.square(
                  dimension: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.list_alt),
          label: Text(listingReports ? 'Listing...' : 'List reports'),
        ),
        OutlinedButton.icon(
          onPressed: onCopyCommands,
          icon: const Icon(Icons.copy),
          label: const Text('Copy adb command'),
        ),
      ],
    );
  }
}

class _AndroidReportPanel extends StatelessWidget {
  const _AndroidReportPanel({
    required this.lastWriteResult,
    required this.files,
    required this.error,
    required this.adbCommands,
  });

  final PerformanceReportWriteResult? lastWriteResult;
  final List<PerformanceReportFile> files;
  final String? error;
  final String adbCommands;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final latest = lastWriteResult;
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
            Text('Android report loop', style: theme.textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(
              'On-device dir: files/performance_tier_reports/',
              style: theme.textTheme.bodySmall,
            ),
            if (error != null) ...<Widget>[
              const SizedBox(height: 8),
              Text(
                'Report error: $error',
                style: TextStyle(color: theme.colorScheme.error),
              ),
            ],
            const SizedBox(height: 8),
            Text('Last write', style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            Text('fileName: ${latest?.fileName ?? '-'}'),
            Text('relativePath: ${latest?.relativePath ?? '-'}'),
            Text('bytes: ${latest?.bytes ?? '-'}'),
            const SizedBox(height: 8),
            Text('adb commands', style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            SelectableText(
              adbCommands,
              style: const TextStyle(fontFamily: 'monospace'),
            ),
            const SizedBox(height: 8),
            Text('Listed reports', style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            if (files.isEmpty)
              const Text('No report listed.')
            else
              for (final file in files.take(5))
                Text('${file.fileName} (${file.bytes} bytes)'),
          ],
        ),
      ),
    );
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
            Text('Runtime signal preset', style: theme.textTheme.titleMedium),
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
            Text(currentPreset.summary, style: theme.textTheme.bodySmall),
          ],
        ),
      ),
    );
  }
}

class _UploadProbeActions extends StatelessWidget {
  const _UploadProbeActions({
    required this.controller,
    required this.onRunUploadProbe,
    required this.onClearAuthSession,
  });

  final PerformanceTierUploadProbeController controller;
  final Future<void> Function() onRunUploadProbe;
  final Future<void> Function() onClearAuthSession;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: <Widget>[
        FilledButton.icon(
          onPressed: controller.runningUpload ? null : onRunUploadProbe,
          icon: controller.runningUpload
              ? const SizedBox.square(
                  dimension: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.cloud_upload),
          label: Text(
            controller.runningUpload ? 'Uploading...' : 'Run /upload probe',
          ),
        ),
        OutlinedButton.icon(
          onPressed: controller.runningUpload || controller.clearingSession
              ? null
              : onClearAuthSession,
          icon: controller.clearingSession
              ? const SizedBox.square(
                  dimension: 14,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.logout),
          label: Text(
            controller.clearingSession ? 'Clearing...' : 'Clear auth session',
          ),
        ),
      ],
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
            Text('Upload probe', style: theme.textTheme.titleMedium),
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
            Text('Upload result', style: theme.textTheme.titleSmall),
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

import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'example_app_factory.dart';
import 'internal_tools_controller.dart';
import 'package:flutter_performance_tier/flutter_performance_tier.dart';

class PerformanceTierDemoController extends ChangeNotifier {
  PerformanceTierDemoController({
    PerformanceTierService? service,
    required InternalToolsController internalToolsController,
    ExampleAppFactory? exampleAppFactory,
  }) : _providedService = service,
       _internalToolsController = internalToolsController,
       _exampleAppFactory = exampleAppFactory ?? ExampleAppFactory();

  final PerformanceTierService? _providedService;
  final InternalToolsController _internalToolsController;
  final ExampleAppFactory _exampleAppFactory;

  PerformanceTierService? _ownedService;
  RuntimeTierController? _ownedRuntimeTierController;
  bool? _usesPresetDecorator;

  StreamSubscription<TierDecision>? _subscription;
  Future<void>? _startInFlight;
  bool _started = false;
  bool _disposed = false;

  TierDecision? _decision;
  String? _error;
  bool _initializing = true;
  bool _refreshing = false;

  TierDecision? get decision => _decision;
  String? get error => _error;
  bool get initializing => _initializing;
  bool get refreshing => _refreshing;
  bool get supportsRuntimeSignalPresets => _providedService == null;

  Future<void> start() {
    if (_disposed || _started) {
      return Future<void>.value();
    }

    final inFlight = _startInFlight;
    if (inFlight != null) {
      return inFlight;
    }

    final next = _startSafely().whenComplete(() {
      _startInFlight = null;
    });
    _startInFlight = next;
    return next;
  }

  Future<void> refreshDecision() async {
    if (_disposed || _refreshing) {
      return;
    }

    _refreshing = true;
    _notifySafely();
    try {
      await _currentService.refresh();
    } catch (error) {
      _error = 'Refresh failed: $error';
    } finally {
      _refreshing = false;
      _notifySafely();
    }
  }

  Future<void> syncWithInternalToolsState() async {
    if (_disposed || !supportsRuntimeSignalPresets) {
      return;
    }

    final shouldUsePresetDecorator =
        _internalToolsController.hasActiveRuntimeSignalPreset;
    if (_ownedService == null ||
        _usesPresetDecorator == shouldUsePresetDecorator) {
      return;
    }

    await _restartOwnedService(usePresetDecorator: shouldUsePresetDecorator);
  }

  Future<void> copyAiReport(
    BuildContext context, {
    Map<String, Object?> extraSections = const <String, Object?>{},
  }) async {
    await _copyToClipboard(
      context,
      buildAiReport(extraSections: extraSections),
      successMessage: 'AI report copied.',
    );
  }

  String buildAiReport({
    Map<String, Object?> extraSections = const <String, Object?>{},
  }) {
    final report = <String, Object?>{
      'status': _error == null ? 'ok' : 'error',
      'generatedAt': DateTime.now().toIso8601String(),
      'initializing': _initializing,
      if (_decision != null) 'decision': _decision!.toMap(),
      if (_error != null) 'error': _error,
    };
    report.addAll(extraSections);
    return const JsonEncoder.withIndent('  ').convert(report);
  }

  String buildHeadline() {
    if (_initializing && _decision == null) {
      return 'Initializing service and waiting for first decision...';
    }
    if (_decision == null) {
      return _error ?? 'No decision yet.';
    }

    final currentDecision = _decision!;
    return 'tier=${currentDecision.tier.name}, '
        'confidence=${currentDecision.confidence.name}, '
        'runtime=${currentDecision.runtimeObservation.status.wireName}';
  }

  Future<void> close() async {
    if (_disposed) {
      return;
    }

    _disposed = true;
    final subscription = _subscription;
    _subscription = null;
    final disposeFuture = _providedService != null
        ? _providedService.dispose()
        : _ownedService?.dispose();
    await subscription?.cancel();
    await disposeFuture;
    super.dispose();
  }

  Future<void> _startSafely() async {
    _started = true;
    _subscription = _currentService.watchDecision().listen(
      _onDecision,
      onError: (Object error, StackTrace stackTrace) {
        if (_disposed) {
          return;
        }
        _initializing = false;
        _error = 'watchDecision failed: $error';
        _notifySafely();
      },
    );

    try {
      await _currentService.initialize();
      if (_disposed || _decision != null) {
        return;
      }
      _initializing = false;
      _notifySafely();
    } catch (error) {
      if (_disposed) {
        return;
      }
      _initializing = false;
      _error = 'Initialization failed: $error';
      _notifySafely();
    }
  }

  Future<void> _copyToClipboard(
    BuildContext context,
    String text, {
    required String successMessage,
  }) async {
    final messenger = ScaffoldMessenger.maybeOf(context);
    await Clipboard.setData(ClipboardData(text: text));
    if (_disposed || messenger == null) {
      return;
    }
    messenger.showSnackBar(SnackBar(content: Text(successMessage)));
  }

  void _onDecision(TierDecision decision) {
    if (_disposed) {
      return;
    }
    _decision = decision;
    _error = null;
    _initializing = false;
    _notifySafely();
  }

  void _notifySafely() {
    if (_disposed) {
      return;
    }
    notifyListeners();
  }

  PerformanceTierService get _currentService {
    return _providedService ??
        (_ownedService ??= _buildOwnedService(
          usePresetDecorator:
              _internalToolsController.hasActiveRuntimeSignalPreset,
        ));
  }

  PerformanceTierService _buildOwnedService({
    required bool usePresetDecorator,
  }) {
    _usesPresetDecorator = usePresetDecorator;
    return _exampleAppFactory.buildService(
      logEmitter: _internalToolsController.recordStructuredLog,
      presetProvider: usePresetDecorator
          ? () => _internalToolsController.runtimeSignalPreset
          : null,
      runtimeTierController: _ownedRuntimeTierController ??= _exampleAppFactory
          .buildRuntimeTierController(),
    );
  }

  Future<void> _restartOwnedService({required bool usePresetDecorator}) async {
    final previousSubscription = _subscription;
    final previousService = _ownedService;
    _subscription = null;
    _ownedService = _buildOwnedService(usePresetDecorator: usePresetDecorator);
    _started = true;
    _initializing = true;
    _error = null;
    _notifySafely();

    await previousSubscription?.cancel();
    await previousService?.dispose();

    _subscription = _currentService.watchDecision().listen(
      _onDecision,
      onError: (Object error, StackTrace stackTrace) {
        if (_disposed) {
          return;
        }
        _initializing = false;
        _error = 'watchDecision failed: $error';
        _notifySafely();
      },
    );

    try {
      await _currentService.initialize();
      if (_disposed || _decision != null) {
        return;
      }
      _initializing = false;
      _notifySafely();
    } catch (error) {
      if (_disposed) {
        return;
      }
      _initializing = false;
      _error = 'Initialization failed: $error';
      _notifySafely();
    }
  }
}

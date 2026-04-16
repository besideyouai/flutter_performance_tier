import 'dart:async';

import 'package:common/common.dart';
import 'package:flutter/foundation.dart';

import '../internal_upload_probe/upload_probe_client.dart';
import '../internal_upload_probe/upload_probe_runtime_config.dart';

typedef UploadProbeClientFactory =
    UploadProbeClient Function(
      UploadProbeRuntimeConfig config,
      void Function(String line)? logger,
    );

class PerformanceTierUploadProbeController extends ChangeNotifier {
  PerformanceTierUploadProbeController({
    required void Function(String line) logger,
    UploadProbeRuntimeConfig Function()? configResolver,
    UploadProbeClientFactory? clientFactory,
  }) : _logger = logger,
       _configResolver = configResolver ?? UploadProbeRuntimeConfig.resolve,
       _clientFactory =
           clientFactory ??
           ((
             UploadProbeRuntimeConfig config,
             void Function(String line)? logger,
           ) {
             return UploadProbeClient.secureStorage(
               config: config,
               logger: logger,
             );
           });

  final void Function(String line) _logger;
  final UploadProbeRuntimeConfig Function() _configResolver;
  final UploadProbeClientFactory _clientFactory;

  UploadProbeRuntimeConfig? _config;
  UploadProbeClient? _client;
  StreamSubscription<AuthState>? _authStateSubscription;
  Future<void>? _startInFlight;
  bool _started = false;
  bool _disposed = false;
  bool _runningUpload = false;
  bool _clearingSession = false;
  String? _setupError;
  String? _uploadError;
  String _uploadResult = 'Not run yet.';
  String _authStatus = AuthStatus.unknown.name;
  String _authTokenPreview = '-';
  String _authSubject = '-';
  String _authExpiresAt = '-';

  UploadProbeRuntimeConfig? get config => _config;
  bool get started => _started;
  bool get runningUpload => _runningUpload;
  bool get clearingSession => _clearingSession;
  String? get setupError => _setupError;
  String? get uploadError => _uploadError;
  String get uploadResult => _uploadResult;
  String get authStatus => _authStatus;
  String get authTokenPreview => _authTokenPreview;
  String get authSubject => _authSubject;
  String get authExpiresAt => _authExpiresAt;
  String get clientLabel => _client?.clientLabel ?? 'common.DioLogUploader';

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

  Future<void> runUploadProbe({
    required String Function() reportBuilder,
  }) async {
    if (_disposed || _runningUpload) {
      return;
    }

    await start();
    final client = _client;
    if (client == null) {
      _uploadError = _setupError ?? 'Upload probe is unavailable.';
      _notifySafely();
      return;
    }

    _runningUpload = true;
    _uploadError = null;
    _notifySafely();
    try {
      final result = await client.uploadReport(reportContent: reportBuilder());
      if (!result.success) {
        _uploadError = result.error ?? result.detail;
        return;
      }
      _uploadResult = result.detail;
    } finally {
      _runningUpload = false;
      _notifySafely();
    }
  }

  Future<void> clearAuthSession() async {
    if (_disposed || _clearingSession) {
      return;
    }

    await start();
    final client = _client;
    if (client == null) {
      _uploadError = _setupError ?? 'Upload probe is unavailable.';
      _notifySafely();
      return;
    }

    _clearingSession = true;
    _uploadError = null;
    _notifySafely();
    try {
      await client.clearSession();
      _logger('[upload_probe_auth] session cleared');
    } catch (error) {
      _uploadError = '$error';
    } finally {
      _clearingSession = false;
      _notifySafely();
    }
  }

  Map<String, Object?> buildReportSections() {
    return <String, Object?>{
      'auth': <String, Object?>{
        'status': _authStatus,
        'subjectId': _authSubject == '-' ? null : _authSubject,
        'accessTokenPreview': _authTokenPreview,
        'expiresAt': _authExpiresAt == '-' ? null : _authExpiresAt,
        'loginUrl': _config?.authConfig.loginUrl,
        'hasTokenFromEnv': _config?.authConfig.hasToken ?? false,
        'hasPasswordCredentials': _config?.authConfig.hasCredentials ?? false,
        'initialized': _started,
        if (_setupError != null) 'setupError': _setupError,
      },
      'uploadProbe': <String, Object?>{
        'url': _config?.uploadUri.toString(),
        'source': _config?.source,
        'client': clientLabel,
        'initialized': _started,
        'running': _runningUpload,
        'result': _uploadResult,
        if (_uploadError != null) 'error': _uploadError,
        if (_setupError != null) 'setupError': _setupError,
      },
    };
  }

  @override
  Future<void> dispose() async {
    super.dispose();
    if (_disposed) {
      return;
    }

    _disposed = true;
    await _authStateSubscription?.cancel();
    await _client?.dispose();
  }

  Future<void> _startSafely() async {
    UploadProbeClient? client;
    StreamSubscription<AuthState>? subscription;
    try {
      final config = _configResolver();
      client = _clientFactory(config, _logger);
      _config = config;
      _setupError = null;
      _uploadError = null;
      _updateAuthStateFields(client.currentState);
      subscription = client.watchState().listen(_onAuthState);
      await client.bootstrap();
      if (_disposed) {
        await subscription.cancel();
        await client.dispose();
        return;
      }
      _client = client;
      _authStateSubscription = subscription;
      _updateAuthStateFields(client.currentState);
      _started = true;
      _notifySafely();
    } catch (error) {
      await subscription?.cancel();
      await client?.dispose();
      _setupError = '$error';
      _logger('[upload_probe] unavailable: $_setupError');
      _notifySafely();
    }
  }

  void _onAuthState(AuthState state) {
    if (_disposed) {
      return;
    }
    _updateAuthStateFields(state);
    _notifySafely();
  }

  void _updateAuthStateFields(AuthState state) {
    _authStatus = state.status.name;
    _authTokenPreview = _previewToken(state.session?.tokens.accessToken);
    _authSubject = state.session?.subjectId ?? '-';
    _authExpiresAt = _formatExpiresAt(state.session?.expiresAt);
  }

  String _previewToken(String? token) {
    if (token == null || token.isEmpty) {
      return '-';
    }
    if (token.length <= 24) {
      return token;
    }
    return '${token.substring(0, 24)}...';
  }

  String _formatExpiresAt(DateTime? value) {
    if (value == null) {
      return '-';
    }
    return value.toLocal().toIso8601String();
  }

  void _notifySafely() {
    if (_disposed) {
      return;
    }
    notifyListeners();
  }
}

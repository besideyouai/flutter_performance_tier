import 'dart:async';
import 'dart:convert';

import 'package:common/common.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import 'demo/performance_tier_demo_controller.dart';
import 'demo/performance_tier_diagnostics_scaffold.dart';
import 'internal_upload_probe/upload_probe_auth_service.dart';

void main() {
  runApp(const PerformanceTierInternalUploadProbeApp());
}

class PerformanceTierInternalUploadProbeApp extends StatelessWidget {
  const PerformanceTierInternalUploadProbeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Performance Tier Internal Upload Probe',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF0B6E4F),
        ),
        useMaterial3: true,
      ),
      home: const PerformanceTierInternalUploadProbePage(),
    );
  }
}

class PerformanceTierInternalUploadProbePage extends StatefulWidget {
  const PerformanceTierInternalUploadProbePage({super.key});

  @override
  State<PerformanceTierInternalUploadProbePage> createState() =>
      _PerformanceTierInternalUploadProbePageState();
}

class _PerformanceTierInternalUploadProbePageState
    extends State<PerformanceTierInternalUploadProbePage> {
  static const String _uploadUrl = 'http://47.110.52.208:7777/upload';
  static const String _loginUrl = 'http://47.110.52.208:7777/user/login';
  static const String _uploadTokenFromEnv = String.fromEnvironment(
    'UPLOAD_PROBE_TOKEN',
  );
  static const String _uploadUsername = String.fromEnvironment(
    'UPLOAD_PROBE_USERNAME',
  );
  static const String _uploadPassword = String.fromEnvironment(
    'UPLOAD_PROBE_PASSWORD',
  );

  late final PerformanceTierDemoController _controller =
      PerformanceTierDemoController();
  late final Dio _dio = Dio();
  late final UploadProbeAuthConfig _authConfig = UploadProbeAuthConfig(
    loginUrl: _loginUrl,
    tokenFromEnv: _uploadTokenFromEnv,
    username: _uploadUsername,
    password: _uploadPassword,
  );
  late final UploadProbeAuthService _authService =
      UploadProbeAuthService.secureStorage(
    config: _authConfig,
    dio: _dio,
    logger: _controller.recordDiagnosticLog,
  );
  late final LogUploadClient _logUploadClient = LogUploadClient(
    uploader: DioLogUploader(dio: _dio),
    defaults: const LogUploadDefaults(
      timeout: Duration(seconds: 30),
      fields: <String, String>{'source': 'flutter_performance_tier'},
    ),
  );
  StreamSubscription<AuthState>? _authStateSubscription;

  String? _uploadError;
  String _uploadResult = 'Not run yet.';
  bool _runningUpload = false;
  bool _clearingSession = false;
  String _authStatus = AuthStatus.unknown.name;
  String _authTokenPreview = '-';
  String _authSubject = '-';
  String _authExpiresAt = '-';

  @override
  void initState() {
    super.initState();
    _updateAuthStateFields(_authService.currentState);
    _authStateSubscription = _authService.watchState().listen(_onAuthState);
    unawaited(_authService.bootstrap());
    unawaited(_controller.start());
  }

  @override
  void dispose() {
    unawaited(_authStateSubscription?.cancel());
    unawaited(_authService.dispose());
    unawaited(_controller.close());
    _dio.close(force: true);
    super.dispose();
  }

  Future<void> _runUploadProbe() async {
    if (_runningUpload) {
      return;
    }

    setState(() {
      _runningUpload = true;
      _uploadError = null;
    });

    try {
      final token = await _authService.resolveAccessToken();
      final now = DateTime.now();
      final fileName = 'performance_tier_report_'
          '${now.toUtc().toIso8601String().replaceAll(':', '').replaceAll('.', '')}.json';
      final uploadResult = await _logUploadClient.upload(
        uploadUri: Uri.parse(_uploadUrl),
        fileContent: _controller.buildAiReport(
          extraSections: _buildUploadProbeReport(),
        ),
        token: token,
        fileName: fileName,
        fields: <String, String>{'generatedAt': now.toIso8601String()},
      );
      final detail = _logUploadClient.formatResultDetail(
        uploadResult,
        responsePreviewMaxLength: 400,
      );
      if (!uploadResult.success) {
        _controller.recordDiagnosticLog('[dio_upload_probe] failed: $detail');
        setState(() {
          _uploadError = detail;
        });
        return;
      }

      _controller.recordDiagnosticLog('[dio_upload_probe] success: $detail');
      setState(() {
        _uploadResult = detail;
      });
    } on DioException catch (error) {
      final errorText = _formatDioException(error);
      _controller.recordDiagnosticLog('[dio_upload_probe] failed: $errorText');
      setState(() {
        _uploadError = errorText;
      });
    } catch (error) {
      _controller.recordDiagnosticLog('[dio_upload_probe] failed: $error');
      setState(() {
        _uploadError = '$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _runningUpload = false;
        });
      }
    }
  }

  Future<void> _clearAuthSession() async {
    if (_clearingSession) {
      return;
    }

    setState(() {
      _clearingSession = true;
      _uploadError = null;
    });

    try {
      await _authService.clearSession();
      _controller.recordDiagnosticLog('[upload_probe_auth] session cleared');
    } catch (error) {
      setState(() {
        _uploadError = '$error';
      });
    } finally {
      if (mounted) {
        setState(() {
          _clearingSession = false;
        });
      }
    }
  }

  void _onAuthState(AuthState state) {
    if (!mounted) {
      return;
    }
    setState(() {
      _updateAuthStateFields(state);
    });
  }

  String _formatDioException(DioException error) {
    final statusCode = error.response?.statusCode;
    final responsePreview = _formatResponsePreview(error.response?.data);
    final message = error.message?.trim();
    final cause = error.error?.toString().trim();
    final details = <String>[
      'type=${error.type.name}',
      if (message != null && message.isNotEmpty) 'message=$message',
      if (cause != null && cause.isNotEmpty && cause != message) 'cause=$cause',
      'url=${error.requestOptions.uri}',
    ].join(', ');
    if (statusCode == null) {
      return details;
    }
    return '$details, status=$statusCode, response=$responsePreview';
  }

  String _formatResponsePreview(Object? data) {
    if (data == null) {
      return '-';
    }
    if (data is List<int>) {
      return _truncatePreview(utf8.decode(data, allowMalformed: true));
    }
    if (data is String) {
      return _truncatePreview(data);
    }
    if (data is Map || data is List) {
      final text = const JsonEncoder.withIndent('  ').convert(data);
      return _truncatePreview(text);
    }
    return _truncatePreview(data.toString());
  }

  String _truncatePreview(String text) {
    if (text.length <= 400) {
      return text;
    }
    return '${text.substring(0, 400)}...';
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

  Map<String, Object?> _buildUploadProbeReport() {
    return <String, Object?>{
      'auth': <String, Object?>{
        'status': _authStatus,
        'subjectId': _authSubject == '-' ? null : _authSubject,
        'accessTokenPreview': _authTokenPreview,
        'expiresAt': _authExpiresAt == '-' ? null : _authExpiresAt,
        'loginUrl': _loginUrl,
        'hasTokenFromEnv': _uploadTokenFromEnv.isNotEmpty,
        'hasPasswordCredentials':
            _uploadUsername.isNotEmpty && _uploadPassword.isNotEmpty,
      },
      'uploadProbe': <String, Object?>{
        'url': _uploadUrl,
        'client': _logUploadClient.clientLabel,
        'running': _runningUpload,
        'result': _uploadResult,
        if (_uploadError != null) 'error': _uploadError,
      },
    };
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (BuildContext context, Widget? child) {
        return PerformanceTierDiagnosticsScaffold(
          title: 'Performance Tier Internal Upload Probe',
          introText:
              'Internal validation entrypoint. The default main demo stays '
              'focused on local diagnostics, while this target keeps the '
              'upload probe workflow isolated.',
          headline: _controller.buildHeadline(),
          report: _controller.buildAiReport(
            extraSections: _buildUploadProbeReport(),
          ),
          error: _controller.error,
          isRefreshing: _controller.refreshing,
          onRefresh: _controller.refreshDecision,
          onCopyAiReport: () => _controller.copyAiReport(
            context,
            extraSections: _buildUploadProbeReport(),
          ),
          onCopyLatestLogLine: () => _controller.copyLatestLogLine(context),
          controlButtons: <Widget>[
            FilledButton.icon(
              onPressed: _runningUpload ? null : _runUploadProbe,
              icon: _runningUpload
                  ? const SizedBox(
                      height: 14,
                      width: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.cloud_upload),
              label: Text(
                _runningUpload ? 'Uploading...' : 'Run /upload probe',
              ),
            ),
            OutlinedButton.icon(
              onPressed:
                  _runningUpload || _clearingSession ? null : _clearAuthSession,
              icon: _clearingSession
                  ? const SizedBox.square(
                      dimension: 14,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.logout),
              label: Text(
                _clearingSession ? 'Clearing...' : 'Clear auth session',
              ),
            ),
          ],
          sectionsBeforeReport: <Widget>[
            Text(
              'Upload endpoint: $_uploadUrl',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              'Login endpoint: $_loginUrl',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              'Auth status: $_authStatus',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              'Auth subject: $_authSubject',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              'Auth expiresAt: $_authExpiresAt',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            Text(
              'Auth token: $_authTokenPreview',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (_uploadError != null)
              Text(
                'Upload error: $_uploadError',
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            SelectableText(
              _uploadResult,
              style: const TextStyle(fontFamily: 'monospace'),
            ),
          ],
        );
      },
    );
  }
}

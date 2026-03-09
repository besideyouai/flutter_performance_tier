import 'dart:convert';

import 'package:common/common.dart';
import 'package:flutter_performance_tier/internal_upload_probe/upload_probe_auth_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  const config = UploadProbeAuthConfig(
    loginUrl: 'https://example.com/user/login',
    tokenFromEnv: '',
    username: 'probe_user',
    password: 'probe_password',
  );

  group('UploadProbeAuthService', () {
    test('resolveAccessToken reuses cached non-expired session', () async {
      final expiresAt = DateTime.utc(2026, 4, 1, 12);
      final token = _buildJwt(exp: expiresAt);
      final gateway = _FakeUploadProbeLoginGateway();
      final auth = CommonAuth.memory();
      final service = UploadProbeAuthService(
        auth: auth,
        config: config,
        loginGateway: gateway,
      );

      await auth.setSession(
        AuthSession(
          tokens: AuthTokenPair(accessToken: token),
          expiresAt: expiresAt,
          subjectId: 'probe_user',
        ),
      );
      await service.bootstrap();

      final resolvedToken = await service.resolveAccessToken();

      expect(resolvedToken, token);
      expect(gateway.callCount, 0);
      expect(service.currentState.status, AuthStatus.authenticated);
      expect(service.currentState.session?.expiresAt, expiresAt);

      await service.dispose();
    });

    test('resolveAccessToken logs in and persists session when missing',
        () async {
      final expiresAt = DateTime.utc(2026, 5, 1, 8);
      final token = _buildJwt(exp: expiresAt);
      final gateway = _FakeUploadProbeLoginGateway(
        results: <UploadProbeLoginResult>[
          UploadProbeLoginResult(
            statusCode: 200,
            token: token,
            subjectId: 'probe_user',
          ),
        ],
      );
      final service = UploadProbeAuthService.memory(
        config: config,
        loginGateway: gateway,
      );

      await service.bootstrap();
      final resolvedToken = await service.resolveAccessToken();

      expect(resolvedToken, token);
      expect(gateway.callCount, 1);
      expect(service.currentState.status, AuthStatus.authenticated);
      expect(service.currentState.session?.tokens.accessToken, token);
      expect(service.currentState.session?.expiresAt, expiresAt);
      expect(service.currentState.session?.subjectId, 'probe_user');

      await service.dispose();
    });

    test('resolveAccessToken relogs in when cached session is expired',
        () async {
      final expiredAt = DateTime.utc(2026, 1, 1);
      final expiredToken = _buildJwt(exp: expiredAt);
      final refreshedAt = DateTime.utc(2026, 7, 1, 10);
      final refreshedToken = _buildJwt(exp: refreshedAt);
      final gateway = _FakeUploadProbeLoginGateway(
        results: <UploadProbeLoginResult>[
          UploadProbeLoginResult(
            statusCode: 200,
            token: refreshedToken,
            subjectId: 'probe_user',
          ),
        ],
      );
      final auth = CommonAuth.memory(
        tokenRefresher: UploadProbePasswordLoginRefresher(
          loginGateway: gateway,
          username: config.normalizedUsername,
          password: config.password,
        ),
      );
      final service = UploadProbeAuthService(
        auth: auth,
        config: config,
        loginGateway: gateway,
      );

      await auth.setSession(
        AuthSession(
          tokens: AuthTokenPair(accessToken: expiredToken),
          expiresAt: expiredAt,
          subjectId: 'probe_user',
        ),
      );
      await service.bootstrap();

      final resolvedToken = await service.resolveAccessToken();

      expect(resolvedToken, refreshedToken);
      expect(gateway.callCount, 1);
      expect(service.currentState.status, AuthStatus.authenticated);
      expect(service.currentState.session?.tokens.accessToken, refreshedToken);
      expect(service.currentState.session?.expiresAt, refreshedAt);

      await service.dispose();
    });
  });
}

class _FakeUploadProbeLoginGateway implements UploadProbeLoginGateway {
  _FakeUploadProbeLoginGateway({
    List<UploadProbeLoginResult> results = const <UploadProbeLoginResult>[],
  }) : _results = List<UploadProbeLoginResult>.from(results);

  final List<UploadProbeLoginResult> _results;
  int callCount = 0;

  @override
  Future<UploadProbeLoginResult> login({
    required String username,
    required String password,
  }) async {
    callCount += 1;
    if (_results.isEmpty) {
      throw StateError('No fake login result configured.');
    }
    return _results.removeAt(0);
  }
}

String _buildJwt({required DateTime exp}) {
  String encode(Map<String, Object?> value) {
    return base64Url.encode(utf8.encode(jsonEncode(value))).replaceAll('=', '');
  }

  return '${encode(const <String, Object?>{'alg': 'none', 'typ': 'JWT'})}.'
      '${encode(<String, Object?>{
        'exp': exp.toUtc().millisecondsSinceEpoch ~/ 1000
      })}.'
      'signature';
}

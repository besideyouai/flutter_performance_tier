import 'package:common/env.dart';

part 'internal_upload_probe_env.g.dart';

const String uploadProbeDefaultUploadUrl = 'http://47.110.52.208:7777/upload';
const String uploadProbeDefaultLoginUrl =
    'http://47.110.52.208:7777/user/login';
const String uploadProbeDefaultToken = '';
const String uploadProbeDefaultUsername = '';
const String uploadProbeDefaultPassword = '';
const String uploadProbeDefaultSource = 'flutter_performance_tier';
const String uploadProbeDefaultAuthSessionKey =
    'flutter_performance_tier.upload_probe.auth_session_v1';

abstract interface class UploadProbeEnvSource {
  String get uploadUrl;
  String get loginUrl;
  String get uploadToken;
  String get uploadUsername;
  String get uploadPassword;
  String get uploadSource;
  String get authSessionKey;
}

final class SecureUploadProbeEnvSource implements UploadProbeEnvSource {
  const SecureUploadProbeEnvSource(this._env);

  factory SecureUploadProbeEnvSource.create() {
    return SecureUploadProbeEnvSource(InternalUploadProbeEnv.create());
  }

  final InternalUploadProbeEnv _env;

  @override
  String get uploadUrl => _env.uploadUrl;

  @override
  String get loginUrl => _env.loginUrl;

  @override
  String get uploadToken => _env.uploadToken;

  @override
  String get uploadUsername => _env.uploadUsername;

  @override
  String get uploadPassword => _env.uploadPassword;

  @override
  String get uploadSource => _env.uploadSource;

  @override
  String get authSessionKey => _env.authSessionKey;
}

@DotEnvGen(
  filename: '.env.internal_upload_probe',
  fieldRename: FieldRename.screamingSnake,
)
abstract class InternalUploadProbeEnv {
  static const _encryptionKey = 'JxdHpbfQMpnFdghEeyDHKO0zHJz3IkBlE7n5hodXzAo=';
  static const _iv = 'I9nqIzp5hTpEIr/LRcS4dg==';

  static InternalUploadProbeEnv create() {
    return InternalUploadProbeEnv(_encryptionKey, _iv);
  }

  const factory InternalUploadProbeEnv(String encryptionKey, String iv) =
      _$InternalUploadProbeEnv;

  const InternalUploadProbeEnv._();

  @FieldKey(name: 'UPLOAD_PROBE_URL', defaultValue: uploadProbeDefaultUploadUrl)
  String get uploadUrl;

  @FieldKey(
    name: 'UPLOAD_PROBE_LOGIN_URL',
    defaultValue: uploadProbeDefaultLoginUrl,
  )
  String get loginUrl;

  @FieldKey(name: 'UPLOAD_PROBE_TOKEN', defaultValue: uploadProbeDefaultToken)
  String get uploadToken;

  @FieldKey(
    name: 'UPLOAD_PROBE_USERNAME',
    defaultValue: uploadProbeDefaultUsername,
  )
  String get uploadUsername;

  @FieldKey(
    name: 'UPLOAD_PROBE_PASSWORD',
    defaultValue: uploadProbeDefaultPassword,
  )
  String get uploadPassword;

  @FieldKey(name: 'UPLOAD_PROBE_SOURCE', defaultValue: uploadProbeDefaultSource)
  String get uploadSource;

  @FieldKey(
    name: 'UPLOAD_PROBE_AUTH_SESSION_KEY',
    defaultValue: uploadProbeDefaultAuthSessionKey,
  )
  String get authSessionKey;
}

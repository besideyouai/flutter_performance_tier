Pod::Spec.new do |s|
  s.name             = 'flutter_performance_tier'
  s.version          = '1.0.0'
  s.summary          = 'Reusable Flutter performance tiering package.'
  s.description      = <<-DESC
Reusable Flutter performance tiering package with platform signal collection.
                       DESC
  s.homepage         = 'http://example.com'
  s.license          = { :file => '../LICENSE' }
  s.author           = { 'OpenAI' => 'support@openai.com' }
  s.source           = { :path => '.' }
  s.source_files     = 'Classes/**/*'
  s.dependency 'Flutter'
  s.platform         = :ios, '13.0'
  s.pod_target_xcconfig = {
    'DEFINES_MODULE' => 'YES',
    'EXCLUDED_ARCHS[sdk=iphonesimulator*]' => 'i386'
  }
  s.swift_version = '5.0'
end

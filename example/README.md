# flutter_performance_tier example

这个 `example/` 是 `flutter_performance_tier` 在当前 `harrypet_flutter` workspace 内的演示与联调工程，不是一个脱离 workspace 独立分发的公开样板。

## 入口说明

- 公开演示入口：`example/lib/main.dart`
- 内部 upload probe 入口：`example/lib/internal_upload_probe_main.dart`

默认展示的是面向接入方的诊断示例界面。`Internal Tools` 相关能力仍保留在 example 中，用于联调、验收和运行期信号注入，但不建议主工程直接照搬。

## 依赖边界

当前 example 仍依赖 workspace 内的 `common` 包以及内部 upload probe 配置，因此预期使用方式是：

1. 在当前 workspace 内执行
2. 作为 package 维护与验收辅助工程使用
3. 参考 `main.dart` 的公开接入链路，而不是把整个 example 当成外部分发模板

## 常用命令

```bash
flutter run -t lib/main.dart
flutter run -t lib/internal_upload_probe_main.dart
flutter test
```

如果你是在接入主工程，优先参考根目录 `README.md` 的接入方式和 `example/lib/main.dart` 的最小链路。

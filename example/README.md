# flutter_performance_tier example

这个 `example/` 是 `flutter_performance_tier` 在当前 `harrypet_flutter` workspace 内的演示与联调工程，不是一个脱离 workspace 独立分发的公开样板。

## 入口说明

- 公开演示入口：`example/lib/main.dart`
- Android report loop 验收入口：公开演示中的 `Internal Tools`
- 内部 upload probe 入口：`example/lib/internal_upload_probe_main.dart`

默认展示的是面向接入方的诊断示例界面。`Internal Tools` 相关能力仍保留在 example 中，用于联调、验收、运行期信号注入和 Android report loop 骨架验证，但不建议主工程直接照搬。

当前主线验收是 Android 性能报告闭环：

1. 展开 `Internal Tools`
2. 点击 `Generate report`
3. 点击 `List reports`
4. 点击 `Copy host commands`
5. 由人工在主机按复制顺序执行命令：开启 fail-fast，列出设备 report 目录，准备主机拉回目录，把设备内 report JSON 拉回电脑，确认拉回文件非空，允许 analyzer gate 失败状态捕获，运行 analyzer gate，捕获 gate status，恢复 fail-fast，打印 `android_report_gate.md`，检查 gate 状态，gate PASS 后生成 goal evidence 草稿并运行 evidence validator；即使 gate FAIL，也应先看到 Markdown 结果再看到命令失败状态

复制出的 builder 命令会用 `$(git branch --show-current)` 和 `$(git rev-parse --short HEAD)` 解析当前 host checkout，并把结果作为 `--branch` / `--commit` 传给 evidence builder。如果 evidence builder 仍不能解析 git branch 或 commit，用显式 `--branch <branch>` 和 `--commit <commit>` 重跑 builder 命令，再运行 evidence validator；最终 evidence 里的 branch / commit 必须与运行上下文一致。

旧的 upload probe 仍可作为内部对照工具，但不再是当前阶段的主要验收路径。真实设备 report gate / evidence 证据要求以根目录 `TEST.md` 为准。

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

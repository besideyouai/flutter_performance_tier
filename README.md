# Flutter Performance Tier

一个可复用的 Flutter 性能分级能力（Android / iOS），用于：

- 启动阶段快速给出设备分级（Tier）
- 将 Tier 映射为业务策略（动画、媒体、缓存等）
- 基于运行期信号做动态降级（热状态、低电量、内存压力、掉帧信号）

## 当前目标（2026-03）

- 库侧稳定输出结构化决策 JSON（`TierDecision`、`runtimeObservation`、`PERF_TIER_LOG`）。
- 业务侧通过自有上传服务将诊断 JSON 归档到 OSS，形成可追溯最小闭环。
- 当前阶段不以“统一日志平台接入 / 阈值回归报表看板”作为交付前置条件。

## 当前状态（2026-03-11）

- Android 真机首轮闭环已完成，当前可以视为“初步完善”状态。
- 已在 Android 真机跑通 `Live device -> Memory critical -> Thermal serious -> Live device`。
- 运行期降级、冷却、逐级恢复、结构化诊断 JSON 和 internal tools 中的 `/upload probe` 上传链路均已验证。
- iOS 侧仍待补真机样本与上传闭环。

## 当前边界（2026-04）

仓库现在按三层职责收敛：

- `lib/performance_tier/`：纯核心库，只负责信号采集、Tier 决策、运行期动态调整和策略解析。
- `lib/demo/`：轻量 public example，默认首页只展示可解释的决策摘要、设备信号和策略结果。
- `lib/demo/` 内的 `Internal Tools`：仅供联调 / 验收使用，承载 runtime preset、structured logs 和 `/upload probe`。

默认 public example 使用真实设备信号。
只有展开 `Internal Tools` 并启用 preset 后，才会走 example-only 的运行期信号注入链路。

## 开发命令

- `flutter pub get`
- `flutter analyze`
- `dart format lib test`
- `flutter test`
- `flutter run`
- `flutter run -t lib/internal_upload_probe_main.dart`
- `flutter pub run build_runner build --delete-conflicting-outputs --define flutter_secure_dotenv_generator:flutter_secure_dotenv=OUTPUT_FILE=encryption_key.json`

## 结构化日志优先

最新 example 已改为“public view + internal tools”结构。默认首页只保留轻量诊断视图，运行时预设和上传辅助能力统一放入折叠的 `Internal Tools`。
核心输出为 `PERF_TIER_LOG` 前缀的 JSON Line，便于直接复制给 AI 排查。

- 运行 `flutter run` 后，在控制台筛选 `PERF_TIER_LOG`
- App 内可一键复制 `AI Diagnostics JSON`
- `flutter test` 会输出 `PERF_TIER_TEST_RESULT` JSON 结果

默认 `main.dart` 现在提供轻量 public example，并将 runtime preset / structured logs / upload probe 收纳到 `Internal Tools`。
`flutter run -t lib/internal_upload_probe_main.dart` 仍保留，便于把上传链路作为独立入口单独验证。

## 上传探针配置

example 内的 `Internal Tools` 和 `internal_upload_probe_main.dart` 按以下优先级读取配置：

1. `--dart-define`
2. `lib/internal_upload_probe/internal_upload_probe_env.dart` 对应的 secure env

支持的键：

- `UPLOAD_PROBE_URL`
- `UPLOAD_PROBE_LOGIN_URL`
- `UPLOAD_PROBE_TOKEN`
- `UPLOAD_PROBE_USERNAME`
- `UPLOAD_PROBE_PASSWORD`
- `UPLOAD_PROBE_SOURCE`
- `UPLOAD_PROBE_AUTH_SESSION_KEY`

如需本地 secure env，可直接打开 `.env.internal_upload_probe.example`
或 `lib/internal_upload_probe/internal_upload_probe_env.dart`，
然后用 VS Code 插件生成；共享脚本会在缺少 `.env.internal_upload_probe`
时自动从 example 补齐。

推荐入口已经切到 VS Code 插件：

- 独立仓库：`D:\dev\vscode-extensions\secure-env-helper`
- 当前工程配置：`tool/internal_upload_probe_secure_env.json`

在 VS Code 中推荐直接这样用：

1. 打开 `.env.internal_upload_probe.example`
2. 点击编辑器标题上的 `Secure Env: Generate For Current Project`
3. 或在资源管理器里右键该文件 / `internal_upload_probe_env.dart` / `tool/internal_upload_probe_secure_env.json` 后生成

命令面板仍可用：

1. `Secure Env: Generate For Current Project`
2. `Secure Env: Pick Config And Generate`

如果不用插件，再直接调用共享生成器：

```powershell
pwsh -ExecutionPolicy Bypass -File ..\packages\common\tool\regenerate_secure_env.ps1 `
  -ProjectRoot . `
  -ConfigFile tool\internal_upload_probe_secure_env.json
```

共享生成器会自动补齐缺失的 `.env.internal_upload_probe`、在首次缺少固定 key/iv 时自动 bootstrap、后续沿用固定 `ENCRYPTION_KEY` / `IV` 重生成 secure env，并删除临时 `encryption_key.json`。

## 生命周期

`PerformanceTierService` 现在显式暴露 `dispose()`。  
业务侧在页面或应用生命周期结束时应主动释放服务，避免遗留 `Timer`、`StreamController` 和掉帧采样器。

```dart
final PerformanceTierService service = DefaultPerformanceTierService();

await service.initialize();
final decision = await service.getCurrentDecision();

// 页面或容器销毁时释放资源
await service.dispose();
```

## 快速接入：开启掉帧信号（可选）

默认情况下，掉帧信号关闭。  
若要开启，创建服务时传入 `enableFrameDropSignal: true`：

```dart
final service = DefaultPerformanceTierService(
  enableFrameDropSignal: true,
);

await service.initialize();
final decision = await service.getCurrentDecision();

final runtimeState = decision.runtimeObservation.status.wireName;
final runtimeStatusDurationMs =
    decision.runtimeObservation.statusDuration.inMilliseconds;
final downgradeTriggerCount =
    decision.runtimeObservation.downgradeTriggerCount;
final frameDropState = decision.deviceSignals.frameDropState; // normal/moderate/critical
final frameDropRate = decision.deviceSignals.frameDropRate; // 0.0 ~ 1.0
```

## 掉帧阈值联调模板（M3 收尾）

建议从以下模板起步，再按业务场景微调：

- `Balanced（默认）`：`window=30s`、`budget=16.667ms`、`rate=0.12/0.25`、`count=8/20`
- `Feed/Scroll`：`window=20s`、`budget=16.667ms`、`rate=0.10/0.20`、`count=18/45`
- `High Refresh（90/120Hz）`：`window=20s`、`budget=11.111ms/8.333ms`、`rate=0.08/0.18`、`count=24/60`

`Feed/Scroll` 参考接入示例：

```dart
final service = DefaultPerformanceTierService(
  enableFrameDropSignal: true,
  runtimeSignalRefreshInterval: const Duration(seconds: 10),
  frameDropSignalSampler: SchedulerFrameDropSignalSampler(
    sampleWindow: const Duration(seconds: 20),
    targetFrameBudget: const Duration(microseconds: 16667),
    minSampledFrameCount: 90,
    moderateDropRate: 0.10,
    criticalDropRate: 0.20,
    moderateDroppedFrameCount: 18,
    criticalDroppedFrameCount: 45,
  ),
  runtimeTierController: RuntimeTierController(
    config: const RuntimeTierControllerConfig(
      enableFrameDropSignal: true,
      downgradeDebounce: Duration(seconds: 3),
      recoveryCooldown: Duration(seconds: 35),
      upgradeDebounce: Duration(seconds: 12),
      moderateFrameDropLevel: 1,
      criticalFrameDropLevel: 2,
    ),
  ),
);
```

## 文档

- 文档导航：`docs/README.md`

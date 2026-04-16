# Flutter Performance Tier

`flutter_performance_tier` 是一个面向 Android / iOS 的 Flutter 性能分级 package，用于在应用启动阶段快速给出设备分级，并在运行期根据热状态、低电量、内存压力、掉帧等信号进行动态降级。

这个 `README.md` 现在只服务于外部主工程接入方：说明 package 提供什么能力、如何接入、如何消费结果。项目进度、计划、讨论、设计等内部资料统一放在 `docs/`，入口见 `docs/README.md`。

## 能力概览

- 启动阶段输出结构化 `TierDecision`
- 将 Tier 映射为可直接消费的策略参数
- 基于运行期信号做动态降级与恢复
- 支持结构化 JSON Line 日志，便于诊断和上传
- 默认通过 plugin 采集 Android / iOS 原生设备信号

## 仓库边界

- `lib/performance_tier/`：核心库与对外 API
- `android/`、`ios/`：plugin 侧原生信号采集实现
- `example/lib/`：对外演示用 example
- `example/lib/demo/` 内的 `Internal Tools`：仅供联调 / 验收，不是主工程默认接入路径

## 接入方式

当前 package 设为私有仓库依赖，`pubspec.yaml` 中 `publish_to: 'none'`。主工程通常通过 `path` 或私有 Git 依赖接入。

```yaml
dependencies:
  flutter_performance_tier:
    path: ../flutter_performance_tier
```

接入后导入：

```dart
import 'package:flutter_performance_tier/flutter_performance_tier.dart';
```

## 快速接入

最小接入链路只有四步：

1. 创建 `PerformanceTierService`
2. 在应用启动或容器初始化阶段调用 `initialize()`
3. 通过 `getCurrentDecision()` 或 `watchDecision()` 消费决策
4. 在页面、模块或应用生命周期结束时调用 `dispose()`

```dart
import 'package:flutter_performance_tier/flutter_performance_tier.dart';

final PerformanceTierService service = DefaultPerformanceTierService();

await service.initialize();

final TierDecision decision = await service.getCurrentDecision();
final PerformancePolicy policy = PerformancePolicy.fromMap(
  Map<String, Object?>.from(decision.appliedPolicies),
);

final TierLevel tier = decision.tier;
final int animationLevel = policy.animationLevel;
final int mediaPreloadCount = policy.mediaPreloadCount;
final ScenarioPolicy? feedPolicy = policy.scenarioById('feed_video_list');

await service.dispose();
```

## 你会拿到什么

`TierDecision` 是主工程最核心的输入，包含：

- `tier`：当前设备等级，范围为 `t0Low` / `t1Mid` / `t2High` / `t3Ultra`
- `confidence`：当前分级置信度
- `deviceSignals`：本次分级使用到的设备信号快照
- `runtimeObservation`：运行期降级状态、持续时间与触发次数
- `appliedPolicies`：当前 tier 对应的策略结果
- `reasons`：当前决策原因，便于解释和排查

典型主工程消费方式有两种：

- 直接使用 `decision.appliedPolicies` 中的结果驱动业务参数
- 基于 `decision.tier` 做主工程内的二次映射

## 持续监听与手动刷新

如果你的业务需要跟随运行期状态动态调整，可以直接监听 `watchDecision()`：

```dart
final subscription = service.watchDecision().listen((TierDecision decision) {
  // 根据最新 tier / policy 更新动画、媒体、缓存等策略
});

await service.refresh();

await subscription.cancel();
```

`DefaultPerformanceTierService` 初始化后会定期轮询运行期信号，默认间隔为 `15s`。如果你的页面切换、播放器状态或前后台切换需要立即重算，也可以主动调用 `refresh()`。

## 可选：开启掉帧信号

默认掉帧信号关闭。若主工程希望把帧稳定性也纳入运行期降级判断，可以在创建服务时开启：

```dart
final service = DefaultPerformanceTierService(
  enableFrameDropSignal: true,
);

await service.initialize();
final decision = await service.getCurrentDecision();

final runtimeState = decision.runtimeObservation.status.wireName;
final frameDropState = decision.deviceSignals.frameDropState;
final frameDropRate = decision.deviceSignals.frameDropRate;
```

如果你已经有明确的页面类型或帧预算，也可以自定义 `SchedulerFrameDropSignalSampler` 和 `RuntimeTierControllerConfig`，把阈值调成更贴近业务场景的版本。

## 可选：输出结构化日志

如果主工程需要把分级过程接入自己的日志、埋点或诊断上传链路，可以注入 `JsonLinePerformanceTierLogger`：

```dart
final service = DefaultPerformanceTierService(
  logger: JsonLinePerformanceTierLogger(
    prefix: 'PERF_TIER_LOG',
  ),
);
```

日志会输出 JSON Line，适合直接接控制台过滤、文件落盘或上传服务。`example/` 中的演示默认也是这套日志前缀。

## 平台与边界说明

- 默认原生信号采集仅覆盖 Android / iOS
- 对于桌面、Web 或特殊宿主环境，需要自行实现 `DeviceSignalCollector`
- plugin 原生通道名为 `performance_tier/device_signals`
- `example/lib/demo/` 中的 `Internal Tools`、preset 注入和 upload probe 仅用于联调验证，不建议主工程直接照搬

## 真机权限与隐私说明

### 运行这个 package 需要申请哪些权限

当前版本的 package 本身不声明 Android 权限，也不触发 iOS 的受保护资源权限申请。

- Android：plugin 的 `AndroidManifest.xml` 目前没有声明任何 `<uses-permission>`
- iOS：当前采集逻辑不访问相机、相册、定位、麦克风、蓝牙、通讯录等受保护资源，因此不需要额外的 `Info.plist` usage description
- Flutter 侧可选的掉帧信号采样基于调度帧统计，不需要额外权限

也就是说，主工程接入这个 package 后，默认不会因为它本身弹出系统权限框。

### 这个 package 当前会读取哪些信号

当前实现会读取或推导这些设备状态：

- Android：`deviceModel`、`totalRamBytes`、`isLowRamDevice`、`mediaPerformanceClass`、`sdkInt`、`memoryPressureState`、`memoryPressureLevel`
- iOS：`deviceModel`、`totalRamBytes`、`isLowRamDevice`、`sdkInt`、`thermalState`、`thermalStateLevel`、`isLowPowerModeEnabled`、`memoryPressureState`、`memoryPressureLevel`
- Flutter 运行期可选项：`frameDropState`、`frameDropRate`、`frameDroppedCount`、`frameSampledCount`

package 默认只在本地内存中使用这些信号做分级和运行期调整，不会自行上传到任何服务端。

### 真实工程需要在隐私说明里写什么

这部分建议分两种情况看：

1. 只在本地使用，不上传

如果主工程只是本地读取这些信号来做性能分级，并且不把 `TierDecision`、`deviceSignals`、结构化日志或诊断 JSON 上传到你们的服务器，那么通常不涉及这个 package 自身发起的数据出端采集。

- Apple 官方口径里，纯 on-device 处理、未上传到服务端的数据，不属于 App Privacy 中的“collected”
- Google Play Data safety 也主要关注你的 app 是否实际收集、共享或传输出设备外的数据

2. 上传到服务端做诊断、归档、分析

如果主工程会把这些信息上传到你们的后端、日志平台、崩溃分析平台或对象存储，那么建议在隐私政策和商店数据披露里明确说明你们会收集“设备性能与诊断信息”，用途一般可写成：

- 设备性能分级与功能降级
- 稳定性监控与问题排查
- 性能优化与兼容性分析

结合当前 package 的字段，实际可能涉及披露的内容通常包括：

- 设备信息：如机型、系统版本、内存等级或性能等级
- 诊断信息：如热状态、低电量状态、内存压力、掉帧状态、运行期降级记录

如果这些诊断数据还会和账号、设备唯一标识、会话 ID、埋点系统用户标识等关联，披露口径通常还需要再更严格一些。

### 推荐写法

如果主工程会上传这类数据，隐私政策里可以至少有一段类似说明：

“为实现设备性能分级、运行期性能保护、稳定性排查与兼容性优化，应用可能收集设备基础信息与性能诊断信息，例如设备型号、系统版本、内存状态、热状态、低电量状态、掉帧情况及性能分级结果。上述信息将仅用于应用功能保障、故障分析与性能优化。”

### 实务建议

- 如果你们只本地使用这个 package，不上传数据，README 和内部接入说明里写清楚“仅本地使用，不出端”即可
- 如果你们上传 `TierDecision`、`deviceSignals` 或结构化日志，建议同步更新隐私政策和应用商店披露
- 如果上传内容里混入账号、手机号、设备唯一标识或广告标识，需要按你们实际上报内容重新评估合规口径
- 这部分最终仍建议由你们的法务或隐私合规同学做最后确认，尤其是上架 App Store / Google Play 前

## 示例与验证

常用命令：

- `flutter pub get`
- `dart format lib test example/lib example/test`
- `flutter test test/performance_tier`
- `cd example && flutter test`
- `flutter run -t example/lib/main.dart`

`example/lib/main.dart` 展示的是面向接入方的公开示例。内部联调能力仍保留在 `Internal Tools` 和 `example/lib/internal_upload_probe_main.dart`，但它们不再作为这个 README 的主线内容。

## 文档导航

- `docs/README.md`：内部文档总入口
- `docs/plan/`：当前进度、验收与收口资料
- `docs/plans/`：分阶段执行计划
- `docs/design/`：设计与边界决策
- `docs/discussion/`：讨论类文档入口

如果你是在接入主工程，优先阅读本 README 和 `example/`；如果你是在维护 package 本身，再进入 `docs/` 查看内部资料。

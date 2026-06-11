# Flutter Performance Tier 项目开发计划

> 状态说明（2026-06-11）：本文件保留为历史阶段计划与背景资料，不再拥有当前项目状态。当前项目已调整为 Android-first 性能监测与设备侧报告拉取闭环，允许 breaking changes；事实源见 `../../SPEC.md`，验证口径见 `../../TEST.md`。

## 1. 项目目标

- 建立一个可复用的 Flutter 性能分级能力，面向 Android 与 iOS 双端。
- 在应用启动阶段快速给出设备性能等级（Tier），并输出可直接用于业务降级的策略集。
- 提供运行期信号监听（内存压力、温度/功耗信号、帧率波动）能力，支持动态降级。
- 支持本地默认策略 + 远程配置覆盖，做到可运营、可灰度、可回滚。
- 当时交付口径（2026-03）：优先保证结构化 `TierDecision` / `PERF_TIER_LOG` JSON 可稳定产出，并可由业务方通过自有服务上传 OSS；日志平台深度接入与报表闭环后置。

## 2. 范围与非目标

### 2.1 本期范围（MVP + V1）

- 平台：Android、iOS（Flutter 插件 + Dart API）。
- 能力：设备画像采集、静态分级、运行期状态更新、策略下发。
- 输出：统一 `PerformanceProfile` 与 `TierDecision`。

### 2.2 非目标（本期不做）

- Web、Windows、macOS、Linux 端支持。
- 自动机器学习分级模型训练。
- 大规模云端数据平台（仅预留埋点接口）。
- 业务日志平台深度接入（如统一埋点平台、可视化看板）与阈值回归报表体系建设。

## 3. 关键场景

- 首屏极限场景：根据机型能力决定首屏动画复杂度、首帧后预加载数量。
- 列表/视频场景：按 Tier 调整解码策略、缓存大小、并发预取数。
- 长时运行场景：收到内存压力或热状态升高后，自动降级渲染质量。

## 4. 总体架构

- Dart 层：
  - `PerformanceTierService`：统一入口，提供初始化、订阅、刷新与释放。
  - `TierEngine`：分级计算核心（规则引擎）。
  - `PolicyResolver`：把 Tier 映射为业务可用策略（开关/阈值）。
  - `ConfigProvider`：本地默认配置 + 远程配置合并。
- 平台层（Plugin）：
  - Android：采集 CPU/内存、`isLowRamDevice`、Media Performance Class 等信号。
  - iOS：采集机型标识、可用内存、热状态等信号。
- 观测层：
  - 埋点接口：初始化耗时、分级结果、降级触发次数、恢复次数。

## 5. 分级设计

### 5.1 数据输入

- 静态信号：RAM 总量、SoC/机型档位、系统版本、存储与 ABI 信息。
- 动态信号：内存压力、热状态、掉帧率（可选）、崩溃前告警信号（可选）。

### 5.2 分级结果

- Tier 建议：`T0_LOW` / `T1_MID` / `T2_HIGH` / `T3_ULTRA`。
- 置信度：`low` / `medium` / `high`（用于灰度策略与兜底）。
- 理由集合：记录命中的关键规则，便于排查。

### 5.3 策略输出（示例）

- UI：动画等级、阴影/模糊开关、图片默认分辨率。
- 媒体：预加载数量、解码并发、缓存阈值。
- 算法：模型大小选择（small/base/large）。

## 6. 里程碑计划

### M0（第 1 周）：项目与基础设施

- 新建 Flutter 项目（Android/iOS）。
- 目录规范、代码规范、lint 与 CI 基础流水线。
- 产出：可运行空壳 + 基础文档。

### M1（第 2-3 周）：静态分级 MVP

- 完成 Android/iOS 设备信号采集插件。
- 实现 `TierEngine` 首版规则（基于 RAM + 机型档位）。
- 提供同步/异步 API：`getCurrentTier()`、`getProfile()`。
- 产出：可稳定返回分级结果。

### M2（第 4 周）：策略映射与业务接入

- 实现 `PolicyResolver` 与默认策略模板。
- 提供示例接入（动画、列表预加载、图片质量）。
- 产出：分级结果能真实驱动性能降级。

### M3（第 5 周）：运行期动态降级

- 监听内存压力与热状态；支持动态降级/恢复。
- 加入防抖与冷却时间，避免频繁抖动。
- 产出：长时运行稳定，降级行为可观察。

### M4（第 6 周）：远程配置、灰度与发布

- 对接远程配置（可先抽象接口，后接 Firebase Remote Config 或自研）。
- 增加灰度开关与回滚策略。
- 完成文档、示例、发布检查清单。
- 产出：可用于生产环境的小版本上线。

## 7. 代码结构建议

```text
packages/flutter_performance_tier/
  lib/
    performance_tier/
      performance_tier_service.dart
      model/
      engine/
      policy/
      config/
      telemetry/
    main.dart
    internal_upload_probe_main.dart
  android/
  ios/
  docs/
    README.md
    plan/
      development_plan.md
      real_device_acceptance_checklist.md
    progress/
      initialization_baseline.md
      runtime_dynamic_tiering.md
    diagnostics_analysis_workflow.md
    rulebook.md
    archived/
      README.md
      scene_policy_mapping.md
```

## 8. API 草案

```dart
abstract class PerformanceTierService {
  Future<void> initialize();
  Future<TierDecision> getCurrentDecision();
  Stream<TierDecision> watchDecision();
  Future<void> refresh();
  Future<void> dispose();
}
```

- `TierDecision`：tier、confidence、reasons、appliedPolicies。
- 初始化要求：应用启动后 300ms 内返回首个可用结果（先粗分，后精化）。

## 9. 测试计划

- 单元测试：规则命中、边界值、配置覆盖优先级。
- 平台测试：Android/iOS 真实设备采集字段完整性。
- 性能测试：初始化耗时、分级计算耗时、运行期监听开销。
- 回归测试：策略切换对关键页面帧率与内存占用的影响。

## 10. 验收标准（首版）

- Android/iOS 设备均可输出稳定 Tier。
- Tier 与策略映射可在 demo 中可视化验证。
- 运行期降级触发可观测，且无明显抖动。
- 结构化诊断 JSON 可稳定导出，并可通过业务上传链路完成 OSS 归档。
- 关键 API 文档齐全，具备被业务方集成条件。

## 11. 风险与应对

- 机型碎片化导致规则误判：增加置信度与远程覆盖。
- 平台字段受系统版本限制：提供字段缺失兜底路径。
- 过度降级影响体验：分场景策略拆分 + A/B 验证。

## 12. 当前状态口径（2026-06-11）

本文件不再维护“当前阶段与下一步”。后续状态按以下事实源收口：

1. 当前项目方向、目标、非目标、breaking change 姿态：`../../SPEC.md`
2. 当前测试范围、真机报告拉取证据、adb / `@test-android-apps` 验证边界：`../../TEST.md`
3. 本地 setup、human-only 命令和 secrets：`../../LOCAL.md`

旧的 JSON + OSS upload probe 闭环可以作为历史背景或对照工具，但不再是 Android 性能监测重构阶段的主验收目标。

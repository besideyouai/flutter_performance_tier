# Flutter Performance Tier

`flutter_performance_tier` 是一个面向 Android / iOS 的 Flutter 性能分级 package，用于在应用启动阶段快速给出设备分级，并在运行期根据热状态、低电量、内存压力、掉帧等信号进行动态降级。

这个 `README.md` 现在只服务于外部主工程接入方：说明 package 提供什么能力、如何接入、如何消费结果。项目当前姿态、验证边界和本地规则见根目录事实源；计划、讨论、设计等内部资料统一放在 `docs/`，入口见 `docs/README.md`。

## 能力概览

- 启动阶段输出结构化 `TierDecision`
- 将 Tier 映射为可直接消费的策略参数
- 基于运行期信号做动态降级与恢复
- 支持生成 V1 `PerformanceReport`，用于 Android 设备侧落盘和主机侧拉取分析
- 支持结构化 JSON Line 日志，便于本地诊断和历史样本兼容
- 默认通过 plugin 采集 Android / iOS 原生设备信号

## 仓库边界

- `lib/performance_tier/`：核心库与对外 API
- `android/`、`ios/`：plugin 侧原生信号采集实现
- `example/lib/`：对外演示用 example
- `example/lib/demo/` 内的 `Internal Tools`：仅供联调 / 验收，不是主工程默认接入路径

## 接入方式

当前 package 作为 `harrypet_flutter` workspace 内的私有依赖维护，`pubspec.yaml` 中同时使用了 `publish_to: 'none'` 和 `resolution: workspace`。预期接入方式是当前 workspace 内的主工程、example 或其他成员包复用，不承诺脱离该 workspace 独立解析。

在当前 workspace 中，该包位于 `packages/flutter_performance_tier/`，主工程通常通过 `path` 依赖接入：

```yaml
dependencies:
  flutter_performance_tier:
    path: ../packages/flutter_performance_tier
```

接入后导入：

```dart
import 'package:flutter_performance_tier/flutter_performance_tier.dart';
```

## 快速接入

> BREAKING CHANGE：`PerformanceTierService` 当前已增加 `writeCurrentReport`
> 和 `listPerformanceReports`。如果主工程提供自定义 service 实现，需要补齐这
> 两个方法。`PerformanceReport` 如果包含 `metadata.serviceSessionId` 或
> `metadata.reportSequence`，现在要求两者同时存在，并要求 `reportId` 匹配
> `<serviceSessionId>-report-<reportSequence>`；自定义 report assembler 需要
> 同步生成这组三元 identity。`generatedAt` 也必须不早于
> `decision.decidedAt`。Android report loop 目前是骨架能力，
> consumer-ready 状态以 `TEST.md` 的真机 report、gate PASS 和
> evidence validator PASS 证据为准。

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

## Android 性能报告闭环

当前架构方向是先跑通 Android report loop：设备内生成结构化报告，写入 app 私有目录，再由开发机拉取并离线分析。这个能力目前仍是验收骨架，不宣称 consumer-ready；真机证据要求以 `TEST.md` 为准。

闭环分为五层：

1. `example/lib/demo/` 的 `Internal Tools` 触发生成、列出和复制 host commands；命令块按顺序完成 fail-fast 开启、report 目录列出、主机目录准备、adb 拉取、非空检查、analyzer gate 失败状态捕获、analyzer gate、gate status 捕获、fail-fast 恢复、gate Markdown 打印、gate 状态检查、evidence draft 生成和 validator 校验。
2. `DefaultPerformanceTierService` 获取当前 `TierDecision`，封装 V1 `PerformanceReport`。
3. `MethodChannelPerformanceReportStore` 通过 `performance_tier/device_signals` 调用 Android write/list 方法。
4. Android native 写入 app-private `files/performance_tier_reports/`。
5. 主机侧通过 adb 或 `@test-android-apps` 拉取 JSON，并交给 `tool/analyze_diagnostics.py` 分析。

默认文件名形态为：

```text
performance_tier_v<schemaVersion>_<utcTimestamp>_<reportId>.json
```

示例 app 的 application id 通常是 `com.example.flutter_performance_tier_example`。直接 adb 拉取命令形态为：

```bash
adb shell run-as '<applicationId>' ls 'files/performance_tier_reports'
adb exec-out run-as '<applicationId>' cat 'files/performance_tier_reports/<fileName>' > '<host-report-file>'
```

V1 不做自动 retention cleanup。报告会保留在 app 私有目录中，直到 app 数据被清除、应用被卸载，或人工在本地验证时删除特定报告文件。

主工程如果只需要消费分级结果，不需要直接调用 `Internal Tools`。如果主工程自定义了 `PerformanceTierService`，需要实现 `writeCurrentReport()` 和 `listPerformanceReports()`，否则 report loop 相关验收和测试替身会不完整。

**BREAKING CHANGE:** `PerformanceReport` 现在只接受当前 V1
`schemaName` 和 `schemaVersion`，并会拒绝空白 `reportId` / `source`。
如果 metadata 中出现
`serviceSessionId` 或 `reportSequence`，两者必须同时存在，且
`serviceSessionId` 必须是非空 string，`reportSequence` 必须是正 integer，
`reportId` 必须匹配 `<serviceSessionId>-report-<reportSequence>`。
`generatedAt` 必须不早于 `decision.decidedAt`，避免生成出的 V1 report 到
Host Analysis gate 才因为时间倒挂失败。直接构造报告或自定义
report service 的调用方需要传入非空且一致的身份字段和可信时间；自定义
assembler 可使用 `PerformanceReport.buildServiceReportId()` 生成一致的
`reportId`。使用
`DefaultPerformanceTierService.writeCurrentReport()` 的默认路径会自动生成符合
当前 V1 gate 的 `reportId` 和 metadata。自定义 native/store 实现如果在写入
前接受了非 V1 `schemaVersion` 或空白 `reportId`，会绕过当前 report loop
身份边界；默认 Android native writer 会拒绝这两类输入。自定义 native/store
实现如果在写入结果中返回了不同的非空 `reportId`，Dart store 会把它视为
contract error。

example 复制出的 host commands 只会使用 native 风格的安全 `.json`
report 文件名：优先刚写入的安全 report；否则从列表中选择 `modifiedAt`
最新的安全 report。命令会对 application id、设备侧 report 路径、主机 report
路径、analyzer 输出目录、gate Markdown 路径和 evidence 输出路径做 shell quote；命令块会开启
fail-fast，在 analyzer 前检查拉回的 JSON 文件非空；analyzer gate 返回 FAIL
时仍会捕获 gate status、恢复 fail-fast、打印 `android_report_gate.md`，再用 gate 退出码让整段命令失败，减少
人工验收时路径差异、空文件和找文件步骤导致的失败。gate PASS 后命令块会继续
用 `$(git branch --show-current)` 和 `$(git rev-parse --short HEAD)` 解析当前 host checkout，
把 `--branch` / `--commit` 显式传给 evidence builder，生成 goal evidence 草稿并运行 evidence validator；人工验收时不要重排复制出的
命令顺序。

真机报告拉回主机后，推荐用 analyzer 的 Android gate 做第一道验收：

```bash
python3 tool/analyze_diagnostics.py <pulled-report-file-or-directory> --output build/diagnostics_analysis_android_report_gate --android-report-gate
```

该命令会写出 `android_report_gate.md`，其中包含 PASS / FAIL、问题列表、
Gate Summary、Checks、performance report / decision 摘要表、Android signal
snapshot、Report Field Check 和 Identity Checklist，便于直接核对 report
id、session、device、OS version、SDK、tier、timestamp、RAM、power、memory
pressure、thermal 字段和 gate 判定准则，并把主要证据复制进 goal evidence。
gate section heading、Gate Summary keys / 顺序、顶部 status block 标签 / 顺序、PASS / FAIL
状态值、Gate Summary 的单个 `text` fenced key-value block、summary table
columns / 顺序、Report Field Check 标签 / 顺序、Checks、
Identity Checklist 标签 / 顺序、PASS gate 的空 Issues 文本和当前 report schema name
以及 gate Markdown 文件名由 `tool/android_report_gate_contract.py` 统一维护，
analyzer、evidence builder 和 evidence validator 共用同一份合同文本。
evidence draft / validator 的输出 marker、`## Run Context`、`## App-Side
Trigger`、`## Host Outputs`、`## Result` 字段标签、Host Commands section
标题、必含命令片段、脚本路径、gate status 检查命令和 host command 执行阶段顺序由
`tool/android_report_evidence_contract.py` 统一维护，避免
`android_report_evidence_status`、`android_report_evidence_draft`、failure
category 文案或人工 handoff 命令合同在 builder、validator 和模板之间漂移。

如果本轮是 goal 验收，`Copy host commands` 会在 gate PASS 后生成并校验
evidence 草稿。ready / done 证据以单个选中的安全 `.json` report 为单位；
目录输入可用于 analyzer 初筛，但最终 evidence draft 和 validator 需要绑定到
一个被拉回的 report 文件；该文件必须是顶层单个 V1 report JSON object，不是
目录、批量文件、JSON array 或非当前 schema 的 JSON object，且文件名必须是
native 风格的安全 `.json` report 文件名；builder 还会要求 report JSON 已具备
非空 `source`、可解析的 UTC ISO-8601 `generatedAt`、service session、正整数
sequence、匹配的 `reportId`、可解析的 ISO-8601 date-time
`decision.decidedAt`、且 `generatedAt` 不早于 `decision.decidedAt`，并具备
tier / confidence / runtime status 以及当前 Android gate 必需的 device / OS /
RAM / SDK / low-RAM / low-power / memory pressure / thermal 信号；对应的
`android_report_gate.md` 也必须可读取，并且必须是同一个 report 的单 report
PASS gate；顶部 status block 必须与 Gate Summary 一致，Performance Reports
表的 columns / 顺序必须匹配共享合同，Source 必须匹配本次 report 路径和文件名，且该表的 source tag、
session、sequence、tier、confidence、runtime、generated/decided timestamp
必须与当前 report JSON 一致；Android Signals 表的 report id、platform、
device、OS version、SDK、RAM、low-RAM、low-power、memory pressure 和 thermal
字段也必须与当前 report JSON 一致，且 Android Signals 表的 columns / 顺序必须匹配共享合同；Report Field Check 里的 schema、
identity、decision、Android signal 和 runtime 字段也必须逐项匹配当前 report
JSON，且 Report Field Check 字段集合与顺序必须精确匹配共享合同，额外、重复或重排
的字段行不会被接受；Identity And Gate Checklist 必须全部为 `yes`，且标签集合与顺序必须精确匹配共享合同，额外、重复或重排的 checklist 行不会被接受；`## Issues` 必须只有
`- None.`，`## Checks` 必须保留 analyzer gate 输出的完整检查清单。
也可以手动执行同一工具链；`build_android_report_evidence.py` 现在要求显式传入
本次运行上下文里的 `--application-id`，不要依赖默认值。builder 会从当前 git
工作树读取 branch / commit；如果当前环境无法读取，必须显式补
`--branch <branch>` 和 `--commit <commit>`。已知 branch / commit 时，推荐在
证据命令里显式保留它们，方便 validator 核对运行上下文：

```bash
python3 tool/build_android_report_evidence.py <pulled-report-file> --analysis-output-dir build/diagnostics_analysis_android_report_gate --branch <branch> --commit <commit> --output goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md --application-id <applicationId>
python3 tool/validate_android_report_evidence.py goals/2026-06-11-android-performance-report-loop/evidence/<filled-evidence-file>.md
```

The evidence validator requires the recorded host command block to include
fail-fast start, report-directory listing, host-directory preparation, pull,
non-empty file check, analyzer gate failure capture, analyzer gate, gate status
capture, fail-fast resume, gate Markdown print, gate status check, evidence
draft builder, and evidence validator commands in that order before the markdown
can count as readiness evidence. It also requires the
recorded `## App-Side Trigger` fields to match `Internal Tools` -> `Generate report`,
`Internal Tools` -> `List reports`, `Internal Tools` -> `Copy host commands`,
and `files/performance_tier_reports/`. The `## Run Context`, `## App-Side
Trigger`, `## Host Outputs`, and `## Result` fields must stay in their named
sections; matching labels elsewhere do not count. It rejects host command blocks that are
not a single `bash` fenced code block, contain unexpected commands, or contain
placeholders such as `<fileName>` or `<applicationId>`, and requires the
commands to parse as valid shell tokens and reference the same application id,
report file name, pulled report
path, and analyzer output directory recorded in the evidence; the adb list
command must exactly list `files/performance_tier_reports`, and the adb pull
command must exactly read
`files/performance_tier_reports/<fileName>` with stdout redirected to the
recorded pulled report path; analyzer, evidence builder, and evidence validator
commands must also match their exact expected argv shape without extra
arguments, and the evidence builder command must pass the same
`--application-id`, `--branch`, and `--commit` recorded in the run context,
plus the expected `--analysis-output-dir` and an explicit `--output` evidence
path; analyzer commands must include `--android-report-gate`; the branch and
commit options must be present together and must match the run context;
`App used` and the safe
report filename pattern are owned by
`tool/android_report_evidence_contract.py`; the pulled report
path basename must match the recorded report file name, and the evidence
validator command must target the same evidence file produced by the draft
builder. The Android Report Gate status block must match Gate Summary, and Gate
Summary row counts and summary tables must describe exactly one selected report.
Gate Summary must remain a single `text` fenced key-value block with the shared
field order; unfenced, extra, duplicate, or reordered `key=value` lines are not
accepted as readiness evidence.
The status block fields must remain directly under `# Android Report Gate`,
match the shared field order, and contain no extra, duplicate, or reordered
labels; matching labels elsewhere do not count.
The evidence must retain the analyzer `## Checks` list and a `## Issues`
section containing only `- None.`. The Performance Reports table Source must
match the pulled report path and the same selected report file name, and both
summary tables must match the shared column order with no extra, duplicate, or
reordered columns. The Android
Signals table must match the Report Field Check report id, platform, device, OS
version, SDK, RAM, low-RAM, low-power, memory pressure, and thermal fields. The
Report Field Check must have exactly one `### <reportId>` heading matching the
current selected report, its field labels must stay inside
`## Report Field Check`, match the shared field order with no extra, duplicate,
or reordered labels, and still show the current V1 schema, Android
platform, and the same device model, Android version, and SDK as the run
context. The Performance Reports table must match the Report Field Check report identity,
service session, decision, runtime, and timestamp fields. The Identity And Gate
Checklist labels must stay inside `## Identity And Gate Checklist`, all values
must be `yes`, and the checklist must match the shared order with no extra,
duplicate, or reordered labels. The reviewed Result section itself must contain
`Pass` with failure category `none`.

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
- 当前移动端最低平台要求为 Android `minSdk 24`、iOS `13.0`
- Web、macOS、Windows、Linux、Fuchsia 宿主当前可以安全编译并初始化服务，但默认不会调用原生通道，而是返回一份有限的 fallback `DeviceSignals`
- 因此，非移动端宿主默认更偏向“可运行 + 可给出保守分级”，如果你们需要更准确的设备分级，请自行实现并注入 `DeviceSignalCollector`
- plugin 原生通道名为 `performance_tier/device_signals`
- `example/lib/demo/` 中的 `Internal Tools`、Android report loop、preset 注入和 upload probe 仅用于联调验证，不建议主工程直接照搬

## 真机权限与隐私说明

### 运行这个 package 需要申请哪些权限

当前版本的 package 本身不声明 Android 权限，也不触发 iOS 的受保护资源权限申请。

- Android：plugin 的 `AndroidManifest.xml` 目前没有声明任何 `<uses-permission>`
- iOS：当前采集逻辑不访问相机、相册、定位、麦克风、蓝牙、通讯录等受保护资源，因此不需要额外的 `Info.plist` usage description
- Flutter 侧可选的掉帧信号采样基于调度帧统计，不需要额外权限

也就是说，主工程接入这个 package 后，默认不会因为它本身弹出系统权限框。

### 这个 package 当前会读取哪些信号

当前实现会读取或推导这些设备状态：

- Android：`deviceModel`、`osVersion`、`totalRamBytes`、`isLowRamDevice`、`mediaPerformanceClass`、`sdkInt`、`thermalState`、`thermalStateLevel`、`isLowPowerModeEnabled`、`memoryPressureState`、`memoryPressureLevel`
- iOS：`deviceModel`、`osVersion`、`totalRamBytes`、`isLowRamDevice`、`sdkInt`、`thermalState`、`thermalStateLevel`、`isLowPowerModeEnabled`、`memoryPressureState`、`memoryPressureLevel`
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

当前 `example/` 仍是 workspace 内的演示与联调工程，依赖了 workspace 本地包与内部 upload probe 配置，因此不建议把整个 `example/` 直接当作对外分发模板；如果你只想参考主工程接入方式，请优先看 `example/lib/main.dart`。Android report loop 的真机触发入口在 `Internal Tools` 中，具体 gate / evidence 证据要求以 `TEST.md` 为准。

## 文档导航

- `SPEC.md`：当前项目姿态、Android-first 性能监测方向、breaking change 口径
- `TEST.md`：测试范围、真机 report gate / evidence 证据、adb / `@test-android-apps` 验证边界
- `LOCAL.md`：本地 setup、human-only 命令、secret 和机器本地文件
- `docs/README.md`：内部文档总入口
- `docs/plan/`：历史阶段进度、验收与收口资料
- `docs/plans/`：分阶段执行计划
- `docs/design/`：设计与边界决策
- `docs/discussion/`：讨论类文档入口

如果你是在接入主工程，优先阅读本 README 和 `example/`；如果你是在维护 package 本身，先读 `SPEC.md`、`TEST.md` 和 `AGENTS.md`，再进入 `docs/` 查看内部资料。

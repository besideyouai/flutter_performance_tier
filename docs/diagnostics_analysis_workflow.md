# 性能报告与诊断数据分析流程

## 1. 输入前提

当前主输入是 Android 设备侧生成、再通过 `adb` 或 `@test-android-apps`
拉到主机的 V1 `PerformanceReport` JSON：

- `schemaName=flutter_performance_tier.performance_report`
- `schemaVersion=1`
- 顶层 `reportId`、`generatedAt`、`source`、`metadata`
- 顶层 `decision`，其中包含 `TierDecision`、`DeviceSignals` 和
  `RuntimeTierObservation`

脚本仍兼容历史输入，便于对照旧样本：

- Demo 页面复制出的 `AI Diagnostics JSON`
- `PERF_TIER_LOG` 结构化日志
- `.jsonl` / `.ndjson` / `.log` / `.txt` 中的 JSON Line

对应项目里的核心字段包括：

- `TierDecision`
- `DeviceSignals`
- `RuntimeTierObservation`
- `recentStructuredLogs`

## 2. 运行脚本

分析一批从 Android 设备拉回主机的 reports：

```powershell
python3 tool\analyze_diagnostics.py D:\path\to\pulled\performance_reports
```

同时分析多个目录：

```powershell
python3 tool\analyze_diagnostics.py D:\path\to\android_reports D:\path\to\legacy_logs
```

自定义输出目录：

```powershell
python3 tool\analyze_diagnostics.py D:\path\to\pulled\performance_reports --output build\diagnostics_analysis_run_01
```

对真机拉回的 Android V1 performance reports 做验收 gate：

```powershell
python3 tool\analyze_diagnostics.py D:\path\to\pulled\performance_reports --output build\diagnostics_analysis_run_01 --android-report-gate
```

`--android-report-gate` 会在以下情况返回非零退出码，并额外输出
`android_report_gate.md`：

- 没有识别到 V1 `flutter_performance_tier.performance_report`
- 存在 parse issue
- 输入中混入 legacy AI diagnostics、decision-only session、structured-log
  session 等非 performance-report session row
- `schemaVersion` 不是 JSON integer `1`（例如字符串 `"1"` 也会失败），
  顶层 `generatedAt` 不是 JSON string 形式的可解析 ISO-8601 UTC timestamp，或
  `decision.decidedAt` 不是 JSON string 形式的可解析 ISO-8601 date-time timestamp
- 顶层 `generatedAt` 和 `decision.decidedAt` 都带 timezone 时，`generatedAt`
  早于 `decision.decidedAt`
- report id、source、generatedAt、service session、report sequence、tier、runtime status 或关键 Android device signal 缺失，例如 device model、RAM、low-RAM classification、SDK、low-power mode、memory pressure；report id、source、service session 和 device model 必须是 trim 后非空的 JSON string，report sequence 必须是正 JSON integer，且 report id 必须匹配 `<serviceSessionId>-report-<reportSequence>`
- 同一 gate 输入文件集里出现重复 `reportId`，或重复
  `serviceSessionId + reportSequence` 组合
- tier、confidence、runtime status、platform、memory pressure state 或 SDK 29+ thermal state 不是非空 JSON string，或不在当前 package wire value 范围内；RAM、SDK、memory pressure level 和 SDK 29+ thermal level 必须是 JSON integer，low-RAM 与 low-power mode 必须是 JSON boolean，不能用字符串数字或字符串布尔值代替
- Android SDK 29+ report 缺少 thermal state 或 thermal state level
- report platform 不是 `android`
- 出现 fallback decision

`mediaPerformanceClass` 会在 Android 提供该值时进入报告，但部分设备不会声明
class，因此 gate 只记录它，不把它作为必填字段。

## 3. 产出文件

默认输出到 `build/diagnostics_analysis/`：

- `session_summary.csv`：每条诊断样本一行，适合看字段完整性、tier、runtime 状态
- `event_timeline.csv`：把结构化日志拍平成事件时间线
- `device_model_summary.csv`：按 `platform + deviceModel` 聚合
- `flagged_sessions.csv`：优先人工排查的异常样本
- `parse_issues.csv`：格式错误或不支持的输入
- `summary.md`：第一眼摘要
- `android_report_gate.md`：仅在使用 `--android-report-gate` 时输出，记录 Android report 验收 gate 的 PASS / FAIL、可复制的 Gate Summary、Checks、具体问题、performance report / decision 摘要表、Android signal snapshot、Report Field Check 和 Identity Checklist

## 4. 推荐分析顺序

1. 如果本轮是 Android report loop 验收，先确认输入文件或目录只包含拉回的 V1 performance reports，再用 `--android-report-gate` 看命令退出码和 `android_report_gate.md`。先复制顶部 status block、`Gate Summary`、Checks、summary tables、Report Field Check、Identity Checklist 和 Issues；顶部 status block、Gate Summary、summary tables、Report Field Check 和 Identity Checklist 都必须保留 analyzer 输出的共享字段集和字段顺序，Gate Summary 还必须保留单个 `text` fenced key-value block。如果需要调整 gate Markdown 文件名、gate section heading、Gate Summary keys / 顺序 / fence、顶部 status block 标签 / 顺序、PASS / FAIL 状态值、summary table columns / 顺序、Report Field Check 标签 / 顺序、Checks、Identity Checklist 标签 / 顺序、PASS gate 的空 Issues 文本或当前 report schema name，先改 `tool/android_report_gate_contract.py`，让 analyzer 输出、evidence builder 和 evidence validator 共用同一合同。 如果输出目录位于输入目录内，脚本会跳过输出目录，避免把本轮生成的 CSV / Markdown 再当作输入扫描。
2. 再看 `summary.md`，确认样本量、字段完整率、热点问题。
3. 再看 `parse_issues.csv`，先把坏数据和混合格式清掉。
4. 再看 `session_summary.csv`：
   - `source_type` 是否为 `performance-report`
   - `schema_name` / `schema_version` / `report_id` 是否完整
   - `device_model` 是否缺失
   - `total_ram_bytes` 是否缺失
   - `runtime_status` 是否异常
   - 是否出现 fallback 样本
5. 再看 `device_model_summary.csv`：
   - 同机型是否映射到多个 tier
   - 哪些机型 `active` / `cooldown` 比例高
   - 哪些机型 fallback 多
6. 再看 `event_timeline.csv`：
   - 触发重算的是哪个 trigger
   - runtime 状态有没有真正变化
   - tier 变化是否符合预期
7. 最后用 `flagged_sessions.csv` 作为人工深挖 shortlist。

## 5. 重点关注什么

### 静态分级

- 同一个 `deviceModel` 通常应该趋于稳定 tier。
- 低 RAM 设备不应该大量落在高 tier。
- 高 RAM + 高 `mediaPerformanceClass` 设备如果长期在低 tier，需要结合 `reasons` 解释。

### 运行期降级

- `runtime_status=active/cooldown` 应该能对应清晰的 `triggerReason`。
- `downgrade_trigger_count` 很高但恢复很少的样本要重点看。
- `frame_drop_rate` 很高但没有运行期降级，说明阈值可能过松。

### 数据质量

- `deviceModel`、`totalRamBytes` 缺失会直接削弱后续分析价值。
- fallback 多通常说明平台采集或上传封装不稳定。

## 6. 冒烟验证

仓库里带了一个 V1 performance report 样本：

```powershell
python3 tool\analyze_diagnostics.py tool\testdata\sample_performance_report.json --output build\diagnostics_analysis_sample
```

V1 Android report gate 样本：

```powershell
python3 tool\analyze_diagnostics.py tool\testdata\sample_performance_report.json --output build\diagnostics_analysis_gate_sample --android-report-gate
```

历史 AI diagnostics 样本仍可作为兼容性检查：

```powershell
python3 tool\analyze_diagnostics.py tool\testdata\sample_ai_report.json --output build\diagnostics_analysis_legacy_sample
```

这些样本命令能跑通后，就可以切换到真实 Android report 拉取目录。
真实设备 report 通过 gate 后，可以先生成 goal evidence 草稿；builder 必须显式传入
本次运行上下文里的 `--application-id`。如果当前目录无法读取 git branch /
commit，还要显式补 `--branch <branch>` 和 `--commit <commit>`。已知 branch /
commit 时，推荐在 evidence command 中显式保留：

```powershell
python3 tool\build_android_report_evidence.py build\pulled_performance_reports\<fileName> --analysis-output-dir build\diagnostics_analysis_android_report_gate --branch <branch> --commit <commit> --output goals\2026-06-11-android-performance-report-loop\evidence\<filled-evidence-file>.md --application-id <applicationId>
```

确认设备和运行上下文无误后，再运行：

```powershell
python3 tool\validate_android_report_evidence.py goals\2026-06-11-android-performance-report-loop\evidence\<filled-evidence-file>.md
```

输出 `android_report_evidence_status=PASS` 后，才把该 evidence 当作
Android report loop readiness 证据。readiness evidence 以单个选中的安全
`.json` report 为单位；目录输入可用于 analyzer 初筛，但最终 evidence draft
和 validator 需要绑定到一个被拉回的 report 文件；evidence draft builder 只接受
顶层单个当前 V1 report JSON object 和 native 风格的安全 `.json` report 文件名，
不接受目录、批量文件、JSON array、非当前 schema object、unsafe report 文件名
或缺少基础 identity/source/timestamp、tier、confidence、runtime status、当前
Android gate 必需信号的 report JSON；`generatedAt` 必须是可解析的 UTC
ISO-8601 timestamp，`decision.decidedAt` 必须是可解析的 ISO-8601 date-time
timestamp，且带 timezone 的情况下 `generatedAt` 不得早于
`decision.decidedAt`。builder 也不接受不可读取的
`android_report_gate.md`，且 gate Markdown 必须是同一个 report 的单 report
PASS gate，顶部 status block 必须与 Gate Summary 一致，
Performance Reports 表的 Source 必须匹配本次 report 路径和文件名，且表里的
source tag、session、sequence、tier、confidence、runtime、generated/decided
timestamp 必须与当前 report JSON 一致；Android Signals 表的 report id、
platform、device、OS version、SDK、RAM、low-RAM、low-power、memory pressure
和 thermal 字段也必须与当前 report JSON 一致；Report Field Check 里的 schema、
identity、decision、Android signal 和 runtime 字段也必须逐项匹配当前 report
JSON；Identity And Gate Checklist 必须全部为 `yes`，且标签集合与顺序必须精确匹配共享合同，额外、重复或重排的 checklist 行不计入可关闭证据；`## Issues` 必须只有
`- None.`，`## Checks` 必须保留 analyzer gate 输出的完整检查清单。

evidence draft / validator 的输出 marker、`## Run Context`、`## App-Side
Trigger`、`## Host Outputs`、`## Result` 字段标签、Host Commands section 标题、
必含命令片段、脚本路径、gate status 检查命令和 host command 执行阶段顺序由
`tool/android_report_evidence_contract.py` 统一维护；如果要改
`android_report_evidence_status`、`android_report_evidence_draft`、
`Pass / fail`、failure category 文案或人工 handoff 命令合同，先改这个合同源，
再同步 builder、validator 和模板测试。

validator 会同时检查
evidence 里记录的 host command block 是否按顺序包含开启 fail-fast、列出设备
report 目录、准备主机目录、拉取 report、非空文件检查、允许 analyzer gate
失败状态捕获、analyzer gate、捕获 gate status、恢复 fail-fast、gate Markdown
打印、gate 状态检查、evidence draft builder 和 evidence validator，避免只运行到
analyzer 的旧命令块、缺少 fail-fast 语义的命令块或重排后的命令块被误当成闭环
证据；也会拒绝合同阶段之外的额外 host command，防止人工 evidence 夹带未审计
命令；也会检查 App-Side Trigger 是否仍记录为 `Internal Tools` 的
`Generate report`、`List reports`、`Copy host commands` 和
`files/performance_tier_reports/` 目录；`## Run Context`、`## App-Side Trigger`、
`## Host Outputs` 和 `## Result` 的字段必须位于各自 section 内，散落在其他 section
的同名字段不计入 readiness evidence；也会拒绝仍包含
`<fileName>` 或 `<applicationId>` 等占位符的不可执行命令块，要求 Host Commands
section 保留为单个 `bash` fenced code block，且命令块每一行都能被 shell token 化
解析，避免坏掉的引号或半截命令进入 evidence；
也要求命令块里的 application id、report 文件名、拉回路径和 analyzer 输出目录
与 evidence 上下文一致，并要求 adb list 命令精确列出 `files/performance_tier_reports`，adb pull
命令精确读取 `files/performance_tier_reports/<fileName>` 并用 stdout 重定向到
记录的拉回路径，analyzer、evidence builder 和 evidence validator 命令也必须
精确匹配预期 argv 结构且不能夹带额外参数，evidence builder 命令还必须传入与运行上下文一致的
`--analysis-output-dir`、`--application-id`、`--branch`、`--commit` 和
`--output`，analyzer 命令必须包含 `--android-report-gate`，其中
`--branch` / `--commit` 必须成对出现并匹配运行上下文，builder
`--output` 必须指向同一个 evidence 文件，拉回路径 basename 与记录的
report 文件名一致，evidence validator 命令
验证的文件与 evidence draft builder 生成的文件一致；`App used` 可选值和安全
report 文件名 pattern 由 `tool/android_report_evidence_contract.py` 维护，并要求 Android Report Gate
顶部 status block 与 Gate Summary 一致，且 status block 字段必须直接位于
`# Android Report Gate` 顶部区域，并保持共享字段集和字段顺序；Gate Summary 必须是单个 `text` fenced
key-value block，裸散、额外、重复或重排的 `key=value` 行不计入证据；Checks 与 Issues section 完整，
Gate Summary 的 row count 和 summary tables 只描述一个选中的 report，
summary table columns 必须保持共享字段集和字段顺序，额外、重复或重排的列不计入可关闭证据，
Performance Reports 表的 Source 与拉回 report 路径和选中的 report 文件名一致，
Performance Reports 表与 Report Field Check 的 report identity、service
session、decision、runtime、timestamp 字段一致，Android Signals 表与 Report
Field Check 的 report id、platform、device、OS version、SDK、RAM、low-RAM、
low-power、memory pressure 和 thermal 字段一致，Report Field Check 必须只有一个
`### <reportId>` 标题且标题值匹配当前选中的 report，Report Field Check 字段也必须留在
`## Report Field Check` section 内，并保持共享字段集和字段顺序；额外、重复或重排的
Report Field Check 字段行不计入可关闭证据；Identity And Gate Checklist 字段也必须留在
`## Identity And Gate Checklist` section 内，并保持共享字段集和字段顺序，额外、重复或重排的 checklist 行不计入可关闭证据。当前 V1 schema、Android platform、device model、
Android version 和 SDK 与运行上下文一致，app variant 与最终 `## Result` section 内的
`Pass` / `none` 结论也已经填好。

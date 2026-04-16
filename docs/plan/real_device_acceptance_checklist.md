# 真机验收 Checklist（JSON + OSS 目标）

更新时间：2026-03-11（Android 首轮验收已完成）

适用范围：`flutter_performance_tier` 当前阶段交付目标（结构化 JSON 产出 + 经业务服务上传 OSS）。

## 1. 准备

- [x] Android：已使用真机（Redmi K40 / `M2012K11AC`）完成首轮验收。
- [ ] iOS：待补真机验收。
- [x] Android：`flutter run -t example/lib/main.dart` 启动成功，Demo 页面可见。
- [ ] iOS：同项未完成。
- [x] Android：上传鉴权参数可用（secure env 或 `--dart-define` 提供 `UPLOAD_PROBE_TOKEN`，或 `UPLOAD_PROBE_USERNAME` + `UPLOAD_PROBE_PASSWORD`）。
- [ ] iOS：同项未完成。

注：如需验证上传链路，可直接使用默认 Demo；如需隔离验证，也可使用 `flutter run -t example/lib/internal_upload_probe_main.dart`。

## 2. 核心功能（两端都做）

注：当前仅完成 Android 真机（Redmi K40）检查；iOS 尚未完成，以下按平台分别记录。

- [x] Android：首次进入后能拿到 `TierDecision`（页面 headline 不再是 initializing）。
- [ ] iOS：同项未完成。
- [x] Android：控制台能看到 `PERF_TIER_LOG` JSON Line。
- [ ] iOS：同项未完成。
- [x] Android：`AI Diagnostics JSON` 可复制，且 JSON 结构完整可解析。
- [ ] iOS：同项未完成。
- [x] Android：JSON 内包含 `runtimeObservation.status`。
- [ ] iOS：同项未完成。
- [x] Android：JSON 内包含 `runtimeObservation.statusDurationMs`。
- [ ] iOS：同项未完成。
- [x] Android：JSON 内包含 `runtimeObservation.downgradeTriggerCount` / `runtimeObservation.recoveryTriggerCount`。
- [ ] iOS：同项未完成。

## 3. 运行期变化验证（两端都做）

- [x] Android：已跑通 `Live device -> Memory critical -> Thermal serious -> Live device`，`runtimeObservation.status` 可见 `pending/active/cooldown/recovery-pending` 变化。
- [ ] iOS：同项未完成。
- [x] Android：恢复到 `Live device` 后，状态可进入恢复链路，且能观察到逐级恢复而非瞬时回到基线。
- [ ] iOS：同项未完成。
- [x] Android：点击刷新按钮后，日志可见 `decision.recompute.completed`。
- [ ] iOS：同项未完成。

## 4. 上传链路（重点）

- [x] Android：在 Demo 中点击 `Run /upload probe` 后上传成功。
- [ ] iOS：同项未完成。
- [x] Android：服务端返回成功信息可见，OSS 上可查到对应 JSON 对象。
- [ ] iOS：同项未完成。
- [x] Android：上传失败时（断网或鉴权错误）有清晰错误信息，恢复后可再次成功上传。
- [ ] iOS：同项未完成。

## 5. 通过标准

- [x] Android 当前阶段通过（结构化 JSON、运行期变化、上传闭环）。
- [ ] iOS 全部通过。
- [ ] 两端至少各完成 1 次“生成 JSON -> 上传 -> OSS 可查”的闭环。

## 6. 验收记录模板（可复制）

```markdown
# 真机验收记录

- 验收日期：
- 验收人：
- 分支/版本：

## 设备信息

- Android：
  - 品牌/型号：
  - 系统版本：
  - App 版本：
- iOS：
  - 机型：
  - 系统版本：
  - App 版本：

## 结果

- Android：通过 / 未通过
- iOS：通过 / 未通过

## 失败项与原因

- （如无可写“无”）

## OSS 归档样本

- Android 对象路径：
- iOS 对象路径：

## 结论

- 是否满足当前阶段交付标准：是 / 否
```

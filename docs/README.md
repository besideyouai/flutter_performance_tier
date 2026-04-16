# 文档导航

`docs/` 只保留少量长期维护的文档。

当前状态、下一步和收口事项统一维护在 `plan/development_plan.md`，不再单独拆分日期型的状态页或审查页。
当前文档口径：Android 真机首轮闭环已完成；iOS 仍待补齐验收。

当前仓库边界：

- 核心库：`lib/performance_tier/`
- plugin 平台实现：`android/`、`ios/`
- 轻量 public example：`example/lib/`
- example 内嵌 `Internal Tools`：runtime preset、structured logs、upload probe

阅读文档时，默认以“真实设备信号路径”为主线；preset 注入和 upload probe 视为 internal tools 语义，不作为主示例默认体验。

## 优先阅读

- `plan/development_plan.md`：项目目标、当前阶段、Android / iOS 收口状态与下一步。
- `plan/real_device_acceptance_checklist.md`：真机验收 checklist、当前通过项与记录模板。
- `progress/runtime_dynamic_tiering.md`：运行期动态降级规则、联调模板、测试说明与 Android 真机样本摘要。

## 补充参考

- `archived/initialization_baseline.md`：初始化耗时基线与测量口径。
- `rulebook.md`：默认阈值、覆盖优先级与规则链路说明。
- `diagnostics_analysis_workflow.md`：诊断数据批量分析流程与脚本用法。

## 历史资料

- `archived/README.md`：历史文档说明与归档用途。
- `archived/scene_policy_mapping.md`：首批高负载场景的历史策略映射定义。

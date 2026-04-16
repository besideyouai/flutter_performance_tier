# 文档导航

`docs/` 用于承载 package 自身的内部资料。根目录 `README.md` 只面向外部主工程接入方，不再承担项目进度跟踪、设计讨论或计划沉淀的职责。

当前文档按用途收口如下：

- `plan/`：当前进度、验收清单、阶段收口资料
- `plans/`：带日期的执行计划与任务拆解
- `design/`：设计方案、边界决策与结构调整说明
- `discussion/`：讨论类文档入口与后续沉淀位置
- `progress/`：专题进展记录
- `archived/`：历史资料与已归档文档

## 优先阅读

- `plan/development_plan.md`：当前项目进度、阶段目标与后续收口事项
- `plan/real_device_acceptance_checklist.md`：真机验收 checklist
- `progress/runtime_dynamic_tiering.md`：运行期动态分级规则、联调模板与测试说明

## 设计与计划

- `design/2026-04-16-example-demo-boundary-design.md`：example public view / internal tools 边界设计
- `design/2026-04-16-package-example-split-design.md`：package 与 example 的职责拆分设计
- `plans/2026-04-16-example-demo-boundary.md`：example 边界调整执行计划
- `plans/2026-04-16-package-example-split.md`：package/example 拆分执行计划

## 规则与补充资料

- `rulebook.md`：默认阈值、覆盖优先级与规则链路说明
- `diagnostics_analysis_workflow.md`：诊断数据批量分析流程与脚本用法

## 历史资料

- `archived/README.md`：归档说明
- `archived/initialization_baseline.md`：初始化耗时基线与测量口径
- `archived/scene_policy_mapping.md`：历史策略映射定义

新增的进度、计划、讨论、设计类文档请继续放在 `docs/` 对应目录下，避免再回流到根 `README.md`。

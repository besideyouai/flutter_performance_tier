# 文档导航

`docs/` 用于承载 package 自身的内部资料。根目录 `README.md` 只面向外部主工程接入方，不再承担项目进度跟踪、设计讨论或计划沉淀的职责。

当前项目状态、验证边界与本地规则优先看根目录事实源：

- `../SPEC.md`：当前项目姿态、Android-first 性能监测方向、breaking change 口径
- `../TEST.md`：测试范围、真机报告拉取证据、adb / `@test-android-apps` 验证边界
- `../LOCAL.md`：本地 setup、human-only 命令、secret 和机器本地文件
- `../PACKAGING.md`：package 身份、版本、签名与产物边界
- `../GENERATION.md`：生成文件、生成命令与输出归属

当前文档按用途收口如下：

- `plan/`：历史阶段进度、验收清单、阶段收口资料
- `plans/`：带日期的执行计划与任务拆解
- `design/`：设计方案、边界决策与结构调整说明
- `discussion/`：讨论类文档入口与后续沉淀位置
- `progress/`：专题进展记录
- `archived/`：历史资料与已归档文档

## 优先阅读

- `../SPEC.md`：当前阶段目标与兼容性姿态
- `../TEST.md`：当前验证范围与报告拉取验收口径
- `plan/development_plan.md`：历史阶段计划；当前状态以 `../SPEC.md` 为准
- `plan/real_device_acceptance_checklist.md`：历史 JSON + OSS 验收清单；当前报告拉取验收以 `../TEST.md` 为准
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

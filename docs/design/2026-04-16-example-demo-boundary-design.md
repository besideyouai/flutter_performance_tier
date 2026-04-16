# Performance Tier Example / Demo Boundary Design

**Date:** 2026-04-16

**Status:** Approved

**Goal**

将当前仓库从“诊断工作台式 demo”收敛为三层清晰结构：

- 纯净核心库：`lib/performance_tier/`
- 轻量对外 example：默认入口展示可解释的核心能力
- internal tools：保留运行期信号注入、结构化日志、upload probe 等内部测试能力，但不再占据主体验

## 背景

当前仓库功能已经基本成型，但 `demo`、信号注入、结构化日志缓存、upload probe 和页面状态管理耦合较深，导致以下问题：

- 对外演示语义与内部验收语义混在一起
- 真机问题难以区分是“真实采集问题”还是“demo 注入问题”
- iOS / Android 验收口径容易被预设信号干扰
- 核心库的边界不够清晰，不利于后续业务方集成

## 目标

本次收敛要达到以下目标：

1. 核心库目录不再依赖 demo、upload probe、页面文案或内部测试逻辑。
2. 默认 example 首页只呈现对外可解释的核心能力。
3. 运行期信号预设、结构化日志、upload probe 进入折叠的 internal tools 区域。
4. internal tools 的启停不影响核心 decision 链路。
5. iOS / Android 验收时可明确区分真实采集模式与 preset 注入模式。

## 非目标

本次不做以下事项：

- 不拆成多个 Dart package
- 不重写核心 tier 计算规则
- 不改变上传 probe 的业务能力本身
- 不把 internal tools 完全迁出仓库

## 方案对比

### 方案 A：一个对外 example，内部能力折叠隐藏

保留单一 example 入口，默认展示轻量演示；把 runtime preset、structured logs、upload probe 收进 `Internal Tools` 折叠区。

优点：

- 收敛成本最低
- 仓库结构变动较小
- 仍保留一站式联调能力

缺点：

- 如果边界控制不严，容易再次膨胀

### 方案 B：一个 example，两种模式

同一 example 按编译参数或开关切换 `public demo mode` / `internal test mode`。

优点：

- 边界更清晰

缺点：

- 配置复杂度更高
- 当前收尾阶段收益不如方案 A 明显

### 方案 C：对外 example + 独立内部 test app

对外 example 极简，internal tools 和 upload probe 迁入单独 app。

优点：

- 逻辑最清晰

缺点：

- 改动面最大
- 当前阶段维护成本偏高

### 结论

采用 **方案 A**。

原因：

- 当前项目已经接近收尾，优先级是收敛边界，不是扩张结构。
- 保留一个统一 example 入口可以降低维护成本。
- 只要把职责和默认展示路径切干净，就能同时满足对外演示和内部联调。

## 目标边界

### 1. 核心库

`lib/performance_tier/` 只包含：

- `config/`
- `engine/`
- `logging/`
- `model/`
- `policy/`
- `service/`
- `performance_tier.dart`
- `performance_tier_service.dart`

核心库职责：

- 采集设备信号
- 计算基础 tier
- 执行运行期动态升降级
- 输出策略与结构化决策

核心库禁止依赖：

- demo 页面
- upload probe
- 剪贴板 / SnackBar / Widget 文案
- runtime preset 注入

### 2. Example

example 只负责“组装”和“展示”核心库能力。

默认主视图保留以下内容：

- 当前决策摘要：`tier`、`confidence`、`runtime status`
- 基础设备信号：`platform`、`deviceModel`、`totalRam`、`isLowRamDevice`
- 解析后的策略结果：例如 `animationLevel`、`mediaPreloadCount`
- 基础操作：`Refresh`、`Copy decision JSON`

默认主视图不再包含：

- upload probe 主按钮
- runtime preset 切换主卡片
- AI diagnostics 作为主价值表达
- 最近日志列表作为主内容

### 3. Internal Tools

internal tools 继续留在 example 中，但默认折叠，并明确标记为仅内部联调 / 验收使用。

内部工具区包含：

- runtime signal preset 注入
- structured log 查看 / 复制
- upload probe 鉴权与上传能力

internal tools 的语义要求：

- 它们是 example 的辅助测试能力
- 它们不是核心库的一部分
- 它们不是默认主体验的一部分

## 代码结构调整

### 1. 拆分 example 装配职责

当前 `PerformanceTierDemoController` 同时承担：

- 依赖装配
- 页面状态控制
- runtime preset 管理
- structured log 缓存

后续应拆分为三个角色：

- `example_app_factory`
  - 负责组装 service、logger、collector decorator 和 feature flags
- `example_page_controller`
  - 只负责页面状态、初始化、刷新、decision 展示
- `internal_tools_controller`
  - 负责 runtime preset、structured logs、upload probe

### 2. runtime preset 显式改为装饰器语义

`DemoRuntimeSignalCollector` 的方向保留，但要明确为 example/internal tools 层的 collector decorator。

语义应始终保持为：

- 真实采集在前
- 预设覆写在后

这样可以明确区分：

- 真实设备采集链路
- 为了联调而进行的 demo 注入链路

### 3. upload probe 作为 example 的内部工具子模块

`lib/internal_upload_probe/` 可以保留，但依赖方向应是：

- example/internal tools -> internal_upload_probe
- internal_upload_probe -> `common` / `dio`
- 核心库不依赖 internal_upload_probe

## 数据流

### 默认 example 主路径

1. example factory 组装 `DefaultPerformanceTierService`
2. page controller 初始化并订阅 decision
3. 页面展示 tier / signals / policy / refresh
4. 用户可复制结构化 `decision JSON`

### internal tools 路径

1. 用户展开 internal tools
2. 工具控制器决定是否启用 runtime preset decorator
3. 工具控制器接收结构化日志并缓存显示
4. upload probe 使用当前 report 执行上传

## 错误处理

错误边界需要按层区分：

- 核心库错误：仍由 `TierDecision` fallback 和结构化日志表达
- example 页面错误：仅影响页面展示，不污染核心库实现
- internal tools 错误：仅影响工具区，不影响默认 example 主路径

特别要求：

- upload probe 初始化失败时，不得阻塞默认 decision 链路
- runtime preset 未启用时，不得改变真实 collector 的行为

## 测试策略

本次收敛后，测试应分层：

- 核心库测试：继续覆盖 engine、runtime controller、service orchestration
- example 组装测试：验证默认模式不注入 preset、不依赖 upload probe
- internal tools 测试：验证 preset decorator、structured log 缓存、upload probe 区域逻辑
- widget 测试：验证主视图与 internal tools 折叠区的边界

建议新增断言：

- 默认页面不展示 `Run /upload probe`
- 展开 internal tools 后才展示 upload probe 和 preset 入口
- 关闭 internal tools 时，decision 链路仍正常工作

## 迁移顺序

1. 先抽离 example 装配逻辑
2. 再拆页面主控制器和 internal tools 控制器
3. 再调整页面结构与文案
4. 最后做目录与命名收敛

## 验收标准

- `lib/performance_tier/` 不再引用 demo / internal tool 语义
- 默认 example 首页只保留轻量对外演示信息
- runtime preset、structured logs、upload probe 全部进入折叠的 internal tools 区
- internal tools 不影响默认 decision 主链路
- 文档明确区分核心库、example、internal tools 三层职责

## 决策摘要

本次收敛的最终方向是：

**把仓库从诊断工作台式 demo，收敛为一个纯净核心库 + 一个轻量对外 example + 一个内嵌 internal tools 区。**

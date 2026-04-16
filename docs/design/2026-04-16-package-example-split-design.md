# Performance Tier Package + Example Split Design

**Date:** 2026-04-16

**Status:** Implemented

## Goal

将当前 `flutter_performance_tier` 从“库代码 + 宿主 app + demo/internal tools 混合仓”收敛为标准 Flutter package/plugin 形态：

- 根包只承载可复用能力与平台实现
- 演示与联调入口统一迁入 `example/`
- 暂不拆成第二个 signals package

## Background

当前仓库已经在代码职责上把核心能力、demo 页面和 internal tools 基本拆开，但工程形态仍然存在三类混合：

1. demo 入口仍位于根包 `lib/main.dart`
2. upload probe 与 internal tools 仍随根包一起声明依赖
3. Android / iOS 的平台采集实现仍挂在宿主 app 目录，而不是标准 plugin 目录

这导致当前仓库“看起来像一个 app”，而不是“可复用 package + example”。

## Current State

### 已经具备的条件

- `lib/performance_tier/` 已经基本纯净，核心 API 与 service 边界明确
- `lib/demo/` 已经完成 public example 与 internal tools 的语义分离
- 测试已经开始验证默认 example 不依赖 internal tools

### 当前阻碍继续收敛的点

- 根入口仍直接导出并运行 demo
- `common`、`dio` 等 internal tools 依赖仍在根包 `pubspec.yaml`
- 原生 `MethodChannel` 实现位于 `android/app`、`ios/Runner`
- 平台完整性测试直接绑定当前宿主 app 文件路径

## Chosen Approach

采用“标准 package/plugin + example”方案。

### 目标结构

```text
packages/flutter_performance_tier/
  lib/
    flutter_performance_tier.dart
    performance_tier/
      config/
      engine/
      logging/
      model/
      policy/
      service/
      performance_tier.dart
      performance_tier_service.dart
  android/
    src/main/...
  ios/
    Classes/...
  example/
    lib/
      main.dart
      internal_upload_probe_main.dart
      demo/
      internal_upload_probe/
    test/
      widget_test.dart
      demo/
  test/
    performance_tier/
```

### 关键原则

- 根包只保留可复用 API、平台实现和核心测试
- `example/` 负责展示、联调、internal tools 和上传探针
- 平台采集能力仍属于同一个包，不额外拆第二个 package
- 未来若有明确复用需求，再考虑拆出 signals package

## Architecture

### 1. 根包职责

根包保留以下内容：

- `DeviceSignals`、`TierDecision`、`RuntimeTierController` 等核心模型与决策逻辑
- `MethodChannelDeviceSignalCollector` 的 Dart 封装
- Android / iOS 对应的平台 channel 实现
- 纯核心测试与平台 contract 测试

根包不再保留以下内容：

- demo widget 树
- internal tools controller
- upload probe runtime/config/client
- 任何 demo-only 的文案、剪贴板、上传动作

### 2. Example 职责

`example/` 负责：

- public example 首页
- internal tools 折叠区
- runtime preset decorator
- upload probe 与 secure env 配置
- widget test 与 demo 组装测试

example 对根包的依赖方式应为标准 path dependency。

### 3. 平台实现职责

平台原生实现从宿主 app 目录迁入 package/plugin 目录：

- Android 从 `android/app/src/main/...` 迁入 package 的标准 plugin Kotlin 入口
- iOS 从 `ios/Runner/AppDelegate.swift` 迁入 package 的标准 plugin Swift 实现

这样 `MethodChannelDeviceSignalCollector` 才真正依赖“包自己的平台实现”，而不是示例 app 的宿主实现。

## Migration Phases

### Phase 1: Example 迁移

目标：

- 把 demo/internal tools/internal upload probe 从根包 `lib/` 迁入 `example/lib/`
- 把 demo/widget 测试迁入 `example/test/`
- 根包新增标准导出入口 `lib/flutter_performance_tier.dart`
- 根包不再提供 `lib/main.dart`

收益：

- 用户一眼就能看出哪些是库代码，哪些是示例代码
- internal tools 依赖开始与核心库脱钩

### Phase 2: Plugin 规范化

目标：

- 将平台实现改为 package/plugin 自注册形态
- 从宿主 app 生命周期中移除信号采集实现
- 更新 platform contract 测试以断言新的 plugin 文件路径

收益：

- 根包真正可被外部 app 集成
- 不再依赖示例宿主才能完成平台采集

### Phase 3: 依赖收缩

目标：

- 从根包中移除 `common`、`dio`、secure env 相关依赖
- 仅在 `example/pubspec.yaml` 中保留这些依赖

收益：

- 核心包安装成本更低
- 发布和复用语义更清晰

## Compatibility Strategy

### API 兼容

- `lib/performance_tier/performance_tier.dart` 继续保留，避免已有内部 import 立即失效
- 新增 `lib/flutter_performance_tier.dart` 作为未来推荐入口
- `DefaultPerformanceTierService` 的公开构造参数保持不变

### 行为兼容

- 默认 example 仍保持当前“public view + Internal Tools”体验
- `internal_upload_probe_main.dart` 继续保留为 example 下的独立入口
- 运行期 preset 注入仍只在 example/internal tools 中出现

## Risks And Mitigations

### 风险 1：平台实现迁移后注册失败

应对：

- 先保留 channel 名与 method 名不变
- 迁移后优先补 platform contract test
- 通过 example 真机启动做 smoke verification

### 风险 2：测试路径迁移导致大面积 import 失效

应对：

- 先新增 `lib/flutter_performance_tier.dart`
- 迁移 example 测试时同步改 import
- 核心测试继续使用 package import，不依赖相对路径

### 风险 3：upload probe 配置与 secure env 迁移不完整

应对：

- 保持原配置 key 完全不变
- 把配置文件、生成说明和主入口一起迁到 `example/`
- README 与 docs 同步更新入口命令

### 风险 4：阶段 1 和阶段 2 混做导致回归面过大

应对：

- 分两批提交
- 先完成 example 迁移并通过核心测试 + example 测试
- 再单独处理 plugin 化

## Validation

迁移完成后应至少满足以下验证：

- 根包 `flutter test test/performance_tier`
- example 下的 widget/demo 测试可独立执行
- `flutter run -t example/lib/main.dart` 正常展示 public example
- `flutter run -t example/lib/internal_upload_probe_main.dart` 仍可启动 internal upload probe 入口
- Android / iOS 平台字段 contract 测试更新后仍通过

## Non-Goals

本次不做以下事项：

- 不拆成 `core` + `signals` 两个独立 package
- 不调整 tier 规则与阈值设计
- 不重写 internal tools 的交互
- 不引入新的远程配置或日志平台方案

## Decision Summary

当前阶段最合适的推进路径不是继续在根包中做目录级收敛，而是把现有职责边界升级为工程边界：

- 根包成为标准 package/plugin
- demo 与 internal tools 迁入 `example/`
- signals 仍留在同一个根包内

这样既能明显提升复用性和可维护性，又不会过早把项目拆成多个 package，符合当前阶段“先收敛，再扩展”的目标。

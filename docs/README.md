# 📚 Santiao Anti 项目文档统一归档与中文总目录

> **定位**：本目录（`docs/`）集中归档项目全部架构设计、工具引擎原理、多端平台指南、抓包取数复盘与专项需求测试用例文档；属于独立代码模块或业务用例库的就地 `README.md` / `AGENTS.md` 保留原目录位置，并在本索引中统一展示作用与直达入口。

---

## 📂 一、`docs/` 目录结构总览

| 目录 / 文件分类 | 目录路径 | 作用说明 |
| :--- | :--- | :--- |
| **总目录索引** | [README.md](README.md) | 统一展示 `docs/` 与全项目各类文档的位置、归类与核心作用 |
| **架构与环境基础指南** | `docs/*.md` | 三端互联测试架构设计、技术栈全景、功能执行顺序、抓包弱网及 Android 取库复盘 |
| **压测与工具引擎规范** | `docs/tools/` | 分布式长连接发包引擎、群组拓扑治理、端侧元数据逆向解析规范（自 `tools/` 归档） |
| **鸿蒙 NEXT 专项文档** | `docs/harmony_docs/` | 鸿蒙执行全链路规范、Appium 驱动重构、API 参考及历史驱动修复记录 |
| **iOS 自动化专项文档** | `docs/ios_docs/` & WDA 指南 | Windows/macOS 下 iOS WDA 部署、真机直连教程与核心原理资料（自 `IOS/docs/` 归档） |
| **专项需求测试用例集** | `docs/cases/` | 会员三期、基础优化、离线消息及登录专项用例文档（含原 `tests/login/md/` 归档） |
| **架构图表资源** | `docs/images/` | 三端网状互联、硬件端口拓扑、群聊广播时序与统一 POM 类图 PNG |
| **Python 语言参考** | `docs/python-3.13-plus/` | Python 3.13+/3.14 核心语法、内置函数与反射特性参考手册 |

---

## 🏗️ 二、架构设计、技术栈与测试执行顺序

| 文档名称 | 相对路径 | 核心作用与适用场景 |
| :--- | :--- | :--- |
| **三端互联自动化测试架构设计** | [tri_platform_mesh_architecture_design.md](tri_platform_mesh_architecture_design.md) | 定义 Android / HarmonyOS / iOS 三端互联自动化整体架构（v3.0.0），适合架构评审与多端统一 POM 设计参考 |
| **桌面端与测试用例技术栈分析** | [desktop_app_tech_stack_analysis.md](desktop_app_tech_stack_analysis.md) | 盘点桌面控制台 `desktop_app` 与 `tests/`、`core/`、`pages/` 的技术栈选型与结构约束 |
| **移动端 UI 审查器模块化架构与全文件手册** | [inspector_modular_architecture_guide.md](inspector_modular_architecture_guide.md) | 详述审查器 6 层 23 模块重构架构、三端隔离矩阵、每个文件内所有类与函数的作用、核心执行链路及 10 项修复记录 |
| **自动化用例功能执行顺序表** | [test_cases_functional_order.md](test_cases_functional_order.md) | 梳理从冒烟登录、会话单聊、多媒体附件、好友关系到群聊社交的完整用例执行编排顺序 |

### 🖼️ 架构图资产 (`docs/images/`)

| 图片文件 | 相对路径 | 展示内容 |
| :--- | :--- | :--- |
| **三端网状架构总览图** | [mesh_architecture_overview.png](images/mesh_architecture_overview.png) | 展示三端互联测试平台整体分层与通信关系 |
| **硬件与端口拓扑图** | [hardware_port_topology.png](images/hardware_port_topology.png) | 展示多端测试设备、端口映射与连接拓扑 |
| **群聊广播时序图** | [group_chat_broadcast_sequence.png](images/group_chat_broadcast_sequence.png) | 展示群聊多端消息广播与同步验证时序 |
| **统一 POM 类图** | [unified_pom_class_diagram.png](images/unified_pom_class_diagram.png) | 展示跨端页面对象抽象与类继承关系 |

---

## ⚙️ 三、压测与测试工具引擎规范 (`docs/tools/`)

> 原存放于 `tools/` 目录下的三份引擎流程文档已统一归档至此，对应 `tools/im_client.py` 与 `tools/im_group_client.py` 的底层实现与 SOP。

| 文档名称 | 相对路径 | 核心作用与适用场景 |
| :--- | :--- | :--- |
| **分布式长连接压测引擎规范** | [im_client_flow.md](tools/im_client_flow.md) | 详述 `tools/im_client.py` 的 Frida RPC 协议直投、两阶段首条建会话、全链路免落库 Hook、背压流控、CSV 语料加载及账号切换/脏数据隔离 SOP |
| **群组拓扑与数据治理规范** | [im_group_client_flow.md](tools/im_group_client_flow.md) | 详述 `tools/im_group_client.py` 的极速建群、退群、群主转让、一键解散机制，以及改名竞态纠偏、已解散群 `state=2` 识别和批量重建群标准流程 |
| **端侧元数据逆向与直投规范** | [im_metadata_extraction_flow.md](tools/im_metadata_extraction_flow.md) | 解释如何绕过 UI 直接从 Android 沙箱 SQLite 逆向提取发送方 `cust_id`/`openId` 与接收方元信息并直连长连接网关 |

---

## 🛠️ 四、Android 沙盒取库与抓包弱网指南

| 文档名称 | 相对路径 | 核心作用与适用场景 |
| :--- | :--- | :--- |
| **未 Root Android 沙盒取库复盘** | [debuggable_database_extraction_full_record.md](debuggable_database_extraction_full_record.md) | 复盘在未 Root 的 Android 11+ 真机上通过注入 `debuggable` 属性合法使用 `run-as` 提取分析客户端本地数据库的完整过程 |
| **Charles 抓包与弱网测试教程** | [charles_mobile_proxy_and_throttling_guide.md](charles_mobile_proxy_and_throttling_guide.md) | 新手向移动端代理抓包、SSL 证书配置及弱网限速/丢包测试操作指南 |

---

## 📱 五、HarmonyOS（鸿蒙 NEXT）专项文档 (`docs/harmony_docs/`)

| 文档名称 | 相对路径 | 核心作用与适用场景 |
| :--- | :--- | :--- |
| **鸿蒙测试全链路执行规范** | [harmony_test_execution_flow(执行流程).md](harmony_docs/harmony_test_execution_flow%28执行流程%29.md) | 从配置加载到用例执行全链路的鸿蒙 NEXT 自动化测试架构拆解与流程规范 |
| **Appium 鸿蒙驱动重构流程** | [appium_harmonyos_driver_execution_flow(重构加载流程).md](harmony_docs/appium_harmonyos_driver_execution_flow%28重构加载流程%29.md) | 记录弃用私有通道、全面切换至官方标准 `appium-harmonyos-driver` 的加载与执行架构 |
| **Appium 鸿蒙驱动 API 与工具指南** | [appium-harmonyos-driver_API与工具使用指南.md](harmony_docs/appium-harmonyos-driver_API与工具使用指南.md) | `zhihu/appium-harmonyos-driver`（v1.0.1）完整 API 手册与配套 CLI/调试工具说明 |
| **HarmonyDriver 修复优化说明** | [harmony_driver_repair_20261020.md](harmony_docs/harmony_driver_repair_20261020.md) | 记录 2026-10-20 对 `core/harmony_driver.py` 启动异常伪装、恢复代理与手势入口的修复记录 |
| **HMNextAuto API 参考（历史基线）** | [HMNextAuto API.md](harmony_docs/HMNextAuto%20API.md) | 原 `hmnextauto 1.7.0` 鸿蒙框架 API 参考留档（供维护历史脚本参考） |

---

## 🍎 六、iOS 自动化与 WDA 部署专项 (`docs/ios_docs/`)

> 原 `IOS/docs/` 下的 iOS 专项文档已归档至 `docs/ios_docs/`，与 WDA 实战指南配合使用。

| 文档名称 | 相对路径 | 核心作用与适用场景 |
| :--- | :--- | :--- |
| **Windows 11 WDA 部署落地指南** | [ios_wda_windows11_setup_guide.md](ios_wda_windows11_setup_guide.md) | 脱离 Mac 在 Windows 11 下完成 WDA 自签名、真机安装与 Appium 对接的详细实操指南 |
| **Windows 连接 iOS 真机教程** | [IOS_Windows_Automation_Guide.md](ios_docs/IOS_Windows_Automation_Guide.md) | Windows 直连 iOS 真机做 Appium 自动化的快速入门与结论总结 |
| **Windows/macOS 双端搭建操作指南** | [ios_operation_guide.md](ios_docs/ios_operation_guide.md) | 面向初学者的 macOS 本地与 Windows + 远程 Mac / `tidevice` 双端环境搭建手册 |
| **iOS 自动化核心原理与学习资料** | [ios_learning_materials.md](ios_docs/ios_learning_materials.md) | 系统讲解 iOS XCUITest 机制、元素定位策略、手势与 IM 专项测试技巧 |

---

## 🧪 七、专项测试用例与语言参考 (`docs/cases/`、`docs/python-3.13-plus/`)

| 文档名称 | 相对路径 | 核心作用与适用场景 |
| :--- | :--- | :--- |
| **会员三期测试用例** | [46. 会员三期.md](cases/46.%20会员三期.md) | 覆盖会员多档位扩容、赠送叠加、铭牌、气泡挂件、权益生命周期及动态配置测试场景 |
| **基础优化测试用例** | [48. 基础优化（视频播放、外部分享、动图、视频美颜、收藏内容复制）.md](cases/48.%20基础优化（视频播放、外部分享、动图、视频美颜、收藏内容复制）.md) | 覆盖视频播放、外部分享到三条、GIF 动图、收藏搜索/复制、视频美颜等基础优化用例 |
| **离线消息专项测试用例** | [离线消息测试用例.md](cases/离线消息测试用例.md) | 覆盖离线期间单聊/群聊产生消息及重连同步、展示、状态更新的跨端测试规范 |
| **登录模块测试用例（技术映射）** | [Login_Test_Cases.md](cases/Login_Test_Cases.md) | 根据 `tests/login/` 脚本提炼的登录正逆向、边界、异常与安全测试矩阵（自 `tests/login/md/` 归档） |
| **Python 3.13+ 核心语法教程** | [python-3.13-plus-syntax-builtins.md](python-3.13-plus/python-3.13-plus-syntax-builtins.md) | 面向框架维护者的 Python 3.13+/3.14 新语法、内置函数与反射机制内部参考 |

---

## 📌 八、保留原位的模块自述与业务用例库（工程就地文档）

> 以下文档直接服务于所在代码/业务目录，保留原路径避免破坏目录职责与既有工程入口：

| 文档名称 | 相对项目路径 | 核心作用 |
| :--- | :--- | :--- |
| **项目工程与测试架构规则** | [AGENTS.md](../AGENTS.md) | 规范 AI 协作角色、Python 3.13+ 约束、目录职责划分及等待/异常处理原则 |
| **业务测试用例全景总览手册** | [test_docs/README.md](../test_docs/README.md) | 面向产研测全员的零代码业务用例库导航，汇总 `00_综合 ~ 09_个人与举报` 共 9 大板块业务文档 |
| **接口高性能压测说明** | [performance/README.md](../performance/README.md) | 阐述 `performance/` 目录下基于 Locust + `FastHttpUser` 的 IM 接口高并发压测方案 |
| **Windows iOS USB 驱动说明** | [tools/drivers/ios/README.md](../tools/drivers/ios/README.md) | 说明 Apple 官方 64 位 USB 通信驱动组件（`AppleMobileDeviceSupport64.msi`）的作用与端口监听机制 |

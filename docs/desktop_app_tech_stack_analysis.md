# 🚀 IM 即时通讯多端自动化测试平台 · 桌面端与测试用例技术栈全景分析报告

> **报告版本**：v1.0.0  
> **文档归属**：Santiao Anti 类微信 IM 自动化测试体系  
> **编制人**：资深测试开发架构师  
> **适用范围**：桌面端控制台（`desktop_app`）、用例工程（`tests/`）、驱动与页面架构（`core/`、`pages/`）

---

## 一、 系统架构与执行拓扑

本测试体系采用 **“桌面控制台驱动层 ➔ 隔离子进程调度层 ➔ POM 业务与驱动层 ➔ 移动端/Web设备层”** 的四层解耦架构。桌面端 UI 与底层用例执行环境严格物理隔离，杜绝因 Python 全局解释器锁（GIL）或依赖库 DLL 冲突导致界面假死。

```mermaid
graph TD
    subgraph 桌面控制台 [桌面端控制台 (PyQt6 GUI)]
        UI[MainWindow 界面 / 布局记忆 / 主题引擎]
        Collector[TestCollector 用例静态/AST收集器]
        Thread[QThread 异步测试任务执行线程]
    end

    subgraph 运行环境 [宿主 / 内置便携运行环境]
        PyRuntime[内置免安装 python_runtime (Python 3.13 x64)]
        AllureCLI[内置 Allure-CLI (Java JRE 11+)]
        ADB[Android SDK ADB 工具链]
        AppiumSrv[Appium Server 2.x (Node.js 运行时)]
    end

    subgraph 用例与业务架构 [自动化测试工程体系]
        pytest[pytest 9.x 测试执行引擎]
        POM[Page Object 业务模型 (pages/)]
        Locators[定位器元数据 (locators/)]
        Core[DeviceManager / AppiumClient 工厂]
        EncryptEngine[测试用例加密保护引擎 (tests/)]
    end

    subgraph 被测端设备矩阵 [被测设备/服务]
        DeviceA[Sender 设备 (Android/HarmonyOS)]
        DeviceB[Receiver 设备 (Android/HarmonyOS)]
        WebBrowser[Web 端浏览器 (Chrome/Firefox/Safari)]
    end

    UI --> Collector
    UI --> Thread
    Thread -->|拉起独立进程调用| PyRuntime
    PyRuntime --> pytest
    pytest --> EncryptEngine
    pytest --> POM
    POM --> Locators
    POM --> Core
    Core -->|HTTP / WebDriver 协议| AppiumSrv
    AppiumSrv -->|ADB / UiAutomator2| DeviceA
    AppiumSrv -->|ADB / UiAutomator2| DeviceB
    Thread -->|生成与离线渲染| AllureCLI
```

---

## 二、 测试用例与工程开发语言矩阵

| 开发语言 | 版本基线 | 应用场景与模块分布 | 选型技术决策理由 |
| :--- | :--- | :--- | :--- |
| **Python** | **3.13+**（兼容 3.11+） | **核心用例与测试框架**：<br>• `tests/`：所有单聊、群聊、音视频、联系人等用例；<br>• `pages/`、`screens/`：Page Object 业务操作封装；<br>• `core/`、`common/`：驱动会话工厂、多端口调度与底层等待机制；<br>• `desktop_app/`：桌面端控制台后端控制、多线程、进程守护。 | **高效演进与动态性**：自动化测试业界事实标准，具备成熟生态（pytest、Appium Client、Allure）；类型注解（Type Hints）保证大型工程代码健壮性。 |
| **C++** | **C++17 / Native** | **底层 GUI 原生图形渲染管线**：<br>• PyQt6 底层调用的 Qt6 原生 C++ 动态链接库（`QtCore.dll`、`QtWidgets.dll` 等）。 | 提供 60FPS 流畅界面渲染、DirectX/OpenGL 硬件加速与操作系统原生级 DPI 缩放响应。 |
| **Pascal** | **Inno Setup 7 脚本** | **Windows 商业级打包与安装向导**：<br>• `installer.iss` 安装逻辑、便携环境自解压、安装路径记忆、开始菜单与桌面快捷方式注入。 | 极简可靠的安装包体积、极高执行效率与完备的 Windows 注册表/快捷方式管理能力。 |
| **YAML / JSON** | 规范标准 | **测试数据驱动与设备配置**：<br>• `config/`、`data/`：环境参数、多机 device_id、Appium 端口映射、账号凭证。 | 实现数据与用例逻辑彻底解耦，非开发人员无需变动代码即可调整设备与测试数据。 |
| **Shell / PowerShell** | 原生 | **CI/CD 流水线与一键构建自动化**：<br>• 本地一键构建脚本（`build_exe.py`、`build_native_exe.py` 内部调度脚本）。 | 统一研发团队构建与打包入口。 |

---

## 三、 核心开发与测试框架生态

### 1. 测试用例执行与断言框架
* **`pytest (9.0.2+)`**：
  * **角色**：核心测试组织、发现、参数化执行与夹具（Fixture）管理引擎。
  * **关键插件**：
    * `pytest-rerunfailures`：网络抖动、弱网卡顿、移动端弹出层干扰时的**自动重试机制**（避免 Flaky Test）；
    * `pytest-check`：**软断言支持**，单个用例多验证点失败时不中断后续断言；
    * `pytest-xdist`：多设备分布式并行执行扩展支持。

### 2. 移动端与 Web 端自动化驱动框架
* **`Appium-Python-Client (5.2.7+)`**：
  * **底层驱动**：对标 **Appium 2.x** 架构，Android 端接入 `UiAutomator2 Driver`，iOS 端预留 `XCUITest Driver`；
  * **架构封装**：在 `core/` 建立连接池管理，支持双机协同（`sender` 发送者设备 + `receiver` 接收者设备）在独立端口（4723、4725）上的并发会话。
* **`Selenium (4.41.0+)`**：
  * 配合 Web 平台/扫码登录场景进行兼容性测试维护，支持原生 Chrome/Firefox CDP 协议通信。

### 3. 多模态视觉断言与感知计算框架
针对 IM 软件高频出现的“表情包、语音气泡未读红点、防撤回提示、图片渲染”等传统 DOM 树难以断言的场景：
* **`PaddleOCR (2.10.0+)` / `CnOCR (2.3.2.2+)`**：用于动态文本定位、截图区域 OCR 文字识别提取与验证；
* **`Pillow (PIL 12.1.1+)` + `ImageHash (4.3.2+)`**：提供高精度的感知哈希（pHash / dHash）算法，支持富媒体图片、表情包在不同机型分辨率下的视觉一致性对比断言。

### 4. 接口与网络抓包专项框架
* **`Requests (2.32.5+)`**：REST API 自动化验证（登录 Token 获取、离线消息服务端同步、群成员拉取）；
* **`mitmproxy (10.x+)`**：透明代理流量注入，支持 IM 长连接/短连接消息拦截、Token 动态嗅探、弱网丢包模拟与报文篡改测试。

### 5. 可视化测试报告框架
* **`Allure Framework` (`allure-pytest` / `allure-python-commons 2.15.2`)**：
  * **用例元数据注解**：`@allure.feature`、`@allure.story`、`@allure.severity`、`@allure.step`；
  * **失败多维归因**：用例失败时自动触发 Hook，捕获**设备当前截屏、Logcat/系统日志、设备剪贴板数据与步骤追踪**。

### 6. 桌面端 GUI 控制台框架
* **`PyQt6 (6.8.0+)`**：
  * 采用现代轻奢深浅主题自适应、`QSplitter` 动态分栏拖拽与尺寸持久化记忆；
  * `QThread` 多线程后台并发执行架构，测试日志通过信号槽机制实时传输至嵌入式富文本终端；
  * 支持设备一键健康检测、免依赖独立执行、Allure 报告一键本地编译与自动打开。

### 7. 商业级知识产权保护引擎
* **自研混合加密引擎 (`encrypt_engine.py`)**：
  * **静态 AST 预提取**：静态解析 `tests/` 目录中的用例类与函数元数据，保留桌面控制台树形列表的展示能力；
  * **Bytecode/Marshal 保护壳**：生产打包时将明文 Python 源码编译固化为底层字节码，防止核心业务用例明文泄漏。

---

## 四、 软件运行环境与依赖矩阵

### 1. Python 运行时环境
* **内置独立便携式环境**：随安装包附带的免安装绿色 `python_runtime`（Python 3.13 x64）：
  * 内置预装完整的 pytest、Appium 驱动及业务依赖包；
  * 彻底解耦用户机器上的系统级 Python 环境，杜绝环境变量路径缺失或版本冲突。
* **宿主 Python 兼容要求**：Python 3.11 ~ 3.13（64-bit）。

### 2. 移动端自动化支撑环境
* **Node.js 运行时**：Node.js v18.x ~ v22.x LTS；
* **Appium Server**：Appium 2.x；
  * 驱动插件：`appium driver install uiautomator2`（Android）、`xcuitest`（iOS）；
* **Android SDK / 工具链**：
  * 必须配置 `ANDROID_HOME` / `ANDROID_SDK_ROOT`；
  * 必须包含 `platform-tools`（`adb` 命令）与 `build-tools`；
* **物理机/模拟器环境**：
  * Android 11 / 12 / 13 / 14；
  * 开发者选项中开启“USB 调试”、“USB 安装”以及“禁止权限监控/允许模拟点击”。

### 3. 测试报告渲染引擎环境
* **Java 运行环境**：JRE / JDK 11+（x64），作为内置 `allure-cli` 离线 HTML 报告渲染的唯一基础依赖；
* **系统浏览器**：Chrome / Edge / Firefox 最新版本（用于渲染 Allure 丰富交互式图形看板）。

### 4. 桌面操作系统支持矩阵
* **Windows 体系（主要生产部署目标）**：
  * Windows 10 (64-bit) 1809 及以上；
  * Windows 11 (64-bit) 全系列；
  * 支持 Inno Setup 7 打包的一键式安装向导与便携绿色版。
* **macOS 体系（跨端打包支持）**：
  * macOS 12 (Monterey) 及以上；
  * 兼容 Apple Silicon (M1/M2/M3/M4) 与 Intel x86_64 架构。

---

## 五、 架构师总结与维护演进建议

1. **便携性与零门槛运行**：
   桌面端通过内置 `python_runtime` 将复杂的自动化测试工程黑盒化封装，普通业务测试与产品人员无需配置 Python、Git、依赖库即可一键执行自动化套件。
2. **多机并发稳态升级**：
   在现有的 `DeviceManager` 基础上，建议后续引入设备动态插拔监听（`adb track-devices` 机制），实现插入真机即自动识别并映射 Appium 端口的即插即用体验。
3. **视觉多模态能力深化**：
   针对 IM 场景中的语音条波形动画、动态表情与音视频通话画面，持续完善 `PaddleOCR + ImageHash` 的断言基线阈值管理，保障 Flaky 故障率稳定低于 **2%**。

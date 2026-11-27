# HarmonyDriver 修复优化说明（2026-10-20）

## 1. 修复结论

本次修复围绕 `core/harmony_driver.py` 的真实启动和调用链展开，并同步处理直接影响鸿蒙驱动可用性的恢复代理、公共手势入口、主页调用错误与显式依赖。

修复后的主要原则如下：

1. 设备通信失败必须抛出明确异常，不能伪装成“元素不存在”或空截图。
2. 点击、滑动、输入、返回等有副作用操作，执行结果未知时禁止自动换通道重放。
3. 鸿蒙元素动作必须继续经过 `RecoverableDriver`，不能固定持有已经失效的底层驱动。
4. HMNextAuto 按设备缓存驱动实例，恢复前必须关闭旧实例，避免重建时继续复用坏连接。
5. HarmonyDriver 不声明支持 Selenium W3C Actions，公共页面层对鸿蒙明确走原生手势。
6. 方法按“连接设备 → 准备设备 → 启动应用 → 获取界面树 → 定位元素 → 执行动作 → 截图与探活 → 退出会话”的顺序组织。

## 2. 修改文件

| 文件 | 修改目的 |
| --- | --- |
| `core/harmony_driver.py` | 修复生命周期、HDC 异常、解锁、应用启动、界面树、元素代理、手势、截图、探活和退出逻辑 |
| `core/driver_factory.py` | 让鸿蒙通信异常、元素动作和 HMNextAuto 单例正确接入现有恢复机制 |
| `common/base_page.py` | 鸿蒙点击、长按和滑动改走原生手势，避免调用不存在的 W3C `execute` 接口 |
| `pages/home/harmony_home_page.py` | 修复屏幕尺寸接口的调用对象和字典解包错误 |
| `requirements.txt` | 显式固定项目直接导入的 `hmnextauto` 与 `lxml` 版本 |

对应的纯修复差异保存在：

- `docs/harmony_docs/harmony_driver_repair_20261020.diff`

该差异以本次开始修改前保存的五个目标文件快照为基线，不混入仓库中其他已有改动。
生成差异时忽略 CRLF/LF 行尾形式变化，仅保留实际逻辑和依赖修改。

## 3. 重点修复说明

### 3.1 HDC 命令与异常契约

- HDC 命令统一通过参数列表执行，避免本地路径含空格时被错误拆分。
- 增加总超时、退出码、标准错误和常见离线信息判断。
- 超时、设备离线、HDC 服务异常抛出 `HarmonyTransportError`，供恢复代理识别。
- 命令明确执行失败抛出 `HarmonyCommandError`，不再返回空字符串掩盖错误。
- 界面树为空、JSON 无效或结构错误抛出 `HarmonyLayoutError`，不再被误判为页面无元素。

### 3.2 有副作用操作保护

- 点击、双击、长按、滑动、输入、返回、按键、启动和停止应用统一经过 `_execute_side_effect()`。
- HMNextAuto 响应异常，或 HDC 有副作用命令发生通信中断时，抛出 `HarmonyCommandOutcomeUnknown`。
- 此场景不再自动切换 HDC 重复执行，避免双击、重复返回、重复输入或重复业务操作。
- 恢复代理会显式排除该异常，不触发整条用例自动重跑，避免再次执行结果未知的业务动作。
- 输入日志只记录字符长度，不记录密码、验证码或聊天内容明文。

### 3.3 设备唤醒与解锁

- 修复 `get_window_size()` 返回字典却按元组解包的问题。
- 不再内置默认解锁密码；需要密码时读取 `lock_password` 或 `unlock_password` capability。
- 数字 PIN 使用鸿蒙 KeyCode 输入，非数字密码使用聚焦文本输入。
- 解锁后通过可观察的锁屏界面标识复核结果，不再无条件返回成功。
- 密码缺失或解锁失败时抛出明确异常，阻止后续误启动和误操作。

### 3.4 应用生命周期与前台应用查询

- HMNextAuto 启动应用时同时传入配置的 `abilityName`。
- HDC 兜底启动保留 `bundleName`、`abilityName` 和 `moduleName`。
- `current_package` 改为查询真实前台应用；HMNextAuto 查询失败时从界面树读取 `bundleName`。
- 会话 ID 改为每次初始化生成唯一值，避免同设备多次会话显示相同标识。

### 3.5 界面树、XPath 与元素定位

- XPath 与 `page_source` 共用同一套 XML 转换规则，避免两者看到的标签和属性不一致。
- 规范化布尔属性、`resource-id` 和 `content-desc` 等常用别名。
- XML 标签名和属性名进行合法化处理，避免 ArkUI 特殊名称破坏 XML。
- 无效 XPath 抛出 `InvalidSelectorException`；合法定位无结果才抛出 `NoSuchElementException`。
- 支持当前项目需要的 XPath、ID、类型、名称、文本和 accessibility id 定位方式。

### 3.6 HarmonyWebElement 兼容与安全

- 增加标准 `rect`、`is_selected()`、属性别名和布尔值兼容。
- `bounds` 支持空格及负坐标；无有效尺寸时拒绝在 `(0, 0)` 附近误触。
- 元素点击、双击、长按、输入和清理统一回到 Driver 公共方法。
- `RecoverableDriver` 在返回元素后重新绑定代理，因此元素后续动作也能识别通信异常。
- `send_keys()` 支持普通文本、Enter 和 Backspace，并且不打印输入明文。
- `clear()` 按当前文本长度清理，同时由驱动限制最大退格次数，避免无上限循环。

### 3.7 原生手势与 BasePage

- `HarmonyDriver.w3c` 明确返回 `False`，因为当前驱动没有实现 Selenium W3C Actions 所需的 `execute` 协议。
- `BasePage.swipe()` 检测到鸿蒙驱动时直接调用原生 `swipe()`。
- `BasePage.tap_point()` 检测到鸿蒙驱动时直接调用原生 `tap()`。
- `BasePage.long_press_action()` 检测到鸿蒙元素时直接调用元素 `long_click()`。
- 鸿蒙原生动作失败后不再进入点击兜底，避免执行结果未知时重复注入。
- Android/Appium 原有 W3C 与 `mobile: longClickGesture` 路径保持不变。

### 3.8 截图与健康检查

- HMNextAuto 截图明确使用 `screenCap`，保证产物是 PNG，而不是默认 JPEG。
- 截图读取前校验 PNG 文件头；空文件或错误格式不再作为成功返回。
- HDC 截图和界面树均使用 UUID 临时文件，降低并发设备或并发命令互相覆盖的风险。
- 本地和设备端临时文件在成功或失败后均执行清理。
- `is_healthy(timeout)` 在同一总超时预算内检查设备列表和 UiTest 界面树服务。
- 健康检查不再只判断设备序列号存在，避免设备在线但自动化服务失效时出现假健康。

### 3.9 会话恢复与退出

- `RecoverableDriver` 能直接识别鸿蒙驱动标记的通信异常。
- 鸿蒙恢复前调用旧驱动 `quit()`，释放 HMNextAuto 的按设备单例和通信资源。
- `HarmonyDriver.quit()` 改为幂等实现；即使 `close()` 异常，也会尝试解除单例并清理本地引用。
- Android 仍保持原有策略：冻结会话不主动 `quit()`，由工厂清理 UiAutomator2 和端口残留。
- 恢复完成后仍抛出既有 `UiAutomator2RecoveryError`，保持 `pytest.ini` 的现有重跑规则兼容；错误信息已改为显示实际驱动类型。

### 3.10 主页调用与依赖

- `HarmonyHomePage.scroll_to_conversation()` 改为调用 `self.driver.get_window_size()`。
- 按 `{"width": ..., "height": ...}` 读取屏幕尺寸，不再错误执行元组解包。
- `requirements.txt` 新增本机已核实版本：`hmnextauto==1.7.0`、`lxml==6.0.2`。

## 4. 代码注释说明

本次仅在容易误解或涉及安全边界的位置增加注释，没有为简单赋值和直观分支堆叠注释。主要注释含义如下：

| 注释主题 | 说明 |
| --- | --- |
| HMNextAuto 日志处理 | 只调整 stderr 控制台处理器，不误改文件日志处理器 |
| 有副作用命令 | 响应异常不等于未执行，因此禁止自动换通道重放 |
| PIN KeyCode | 说明数字 0～9 与鸿蒙 KeyCode 的对应关系 |
| `screenCap` | 说明为什么必须指定该方式以获得 PNG |
| HMNextAuto 单例释放 | 说明恢复前关闭旧实例的原因 |
| 元素代理重新绑定 | 说明为什么元素不能固定持有旧底层 Driver |
| 鸿蒙原生手势分流 | 说明 HarmonyDriver 为什么不能进入 W3C ActionBuilder |
| 原生动作失败不兜底 | 说明阻止重复点击或重复注入的原因 |

## 5. 行为变化与兼容性

以下变化属于有意修正，调用方应按新契约处理：

1. HDC 失败不再返回空字符串，而是抛出 `WebDriverException` 体系内的明确异常。
2. 截图失败不再返回空字节，而是抛出异常，以便报告层记录真实失败原因。
3. 无效 XPath 不再返回空列表，而是抛出 `InvalidSelectorException`。
4. 未配置锁屏密码时不再尝试默认 PIN。
5. 有副作用操作结果未知时不会自动 HDC 重放，也不会伪装成操作成功。
6. `capabilities` 返回副本，外部修改不会污染当前会话配置。
7. `w3c=False` 表示不支持 Selenium W3C Actions 协议；常用手势已在 BasePage 中分流到鸿蒙原生实现。

公共方法的主要名称和业务调用方式保持不变，现有 `DriverFactory.get_driver()`、BasePage 定位、元素点击与截图调用无需改写。

## 6. 已完成的只读核对

- 核实本机 HMNextAuto 版本为 `1.7.0`，`lxml` 版本为 `6.0.2`。
- 核实 HMNextAuto 的 `start_app(package_name, page_name)`、`current_app()`、`display_size`、`screenCap`、`swipe()`、`input_text()`、`close()` 和单例注销接口。
- 核实 `core/harmony_driver.py` 中只保留一套 `execute_hdc()` 与 `execute_hdc_shell()`，不存在尾部旧方法覆盖新实现。
- 核实鸿蒙主页不再调用不存在的 `self.get_window_size()`。
- 核实元素交互代码不再直接访问 `driver.hm`，统一经过 Driver/恢复代理。
- 核实截图失败路径不再返回空字节。
- 核实输入日志不再输出 HarmonyDriver/HarmonyWebElement 的明文内容。
- 修复差异已通过 `git apply --check --reverse`，确认可与当前五个目标文件准确对应。

## 7. 未执行验证

按照项目规则，本次没有主动执行以下操作：

- `pytest` 或完整自动化用例；
- 真机启动、解锁、点击、滑动、截图和断线恢复；
- 编译、Lint、Black 或其他格式化命令；
- 依赖安装或升级；
- Git commit、push、pull、merge 或分支操作。

因此，本次结论是“代码静态修复和调用链核对完成”，不是“真机测试已通过”。

## 8. 建议的后续真机验证顺序

如后续授权执行验证，建议按以下顺序进行，便于快速定位问题：

1. 单设备、已解锁状态初始化，确认应用按配置 Ability 启动。
2. 息屏但无密码状态初始化，确认唤醒和上滑结果。
3. 配置正确 PIN 的锁屏状态初始化，确认解锁结果；再用缺失密码配置确认明确失败。
4. 执行 ID、XPath、文本和 accessibility id 定位，并读取 `page_source`。
5. 执行元素点击、输入、清理、长按，以及页面点击和滑动。
6. 执行 PNG 内存截图和文件截图，确认报告附件可打开。
7. 人工断开 HDC 或终止 UiTest，确认只读命令触发单次会话恢复。
8. 在有副作用动作返回异常的场景，确认不会自动重复注入同一动作。
9. 双鸿蒙设备并行运行，确认临时文件、设备序列号和 HMNextAuto 单例互不干扰。

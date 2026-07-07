# Windows 使用 iOS 自动化测试教程

## 1. 先明确边界

你是 Windows 电脑，可以在 Windows 上写代码、运行 pytest、打开 Appium Inspector 定位元素；但 iOS 自动化底层依赖 `Xcode + WebDriverAgent + XCUITest`，默认启动 WDA、模拟器、真机签名都需要 macOS。

推荐架构：

```
Windows 电脑
  ├─ 写 Python / pytest 用例
  ├─ 打开 Appium Inspector 定位元素
  └─ 连接 Mac 上的 Appium 服务

Mac 电脑 / Mac mini / 远程 Mac
  ├─ Xcode
  ├─ Appium Server
  ├─ XCUITest Driver
  ├─ WebDriverAgent
  └─ iPhone 真机 / iOS 模拟器
```

你的目标不是“Windows 直接控制 iPhone”，而是“Windows 远程连接 Mac 上的 iOS 自动化服务”。

## 2. 工具清单

| 工具                     | 安装位置     | 作用                          |
| ------------------------ | ------------ | ----------------------------- |
| Python                   | Windows      | 运行 pytest 自动化脚本        |
| Appium-Python-Client     | Windows      | Python 连接 Appium            |
| pytest / allure-pytest   | Windows      | 执行测试用例和生成报告        |
| Appium Inspector         | Windows      | 查看 iOS 页面元素、定位元素   |
| Node.js / npm            | Mac          | 安装 Appium                   |
| Appium Server            | Mac          | 接收 Windows 发来的自动化请求 |
| XCUITest Driver          | Mac          | Appium 的 iOS 驱动            |
| Xcode                    | Mac          | 编译和签名 WebDriverAgent     |
| WebDriverAgent           | Mac + iPhone | iOS 自动化实际执行器          |
| iPhone 真机或 iOS 模拟器 | Mac          | 被测设备                      |

## 3. Windows 环境安装

### 3.1 安装 Python

下载并安装 Python 3.10+：

```
python --version
pip --version
```

### 3.2 进入你的项目目录

```
cd D:\projects\santiao-anti
```

### 3.3 创建虚拟环境

```
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
```

### 3.4 安装项目依赖

```
pip install -r requirements.txt
pip install Appium-Python-Client selenium pytest pytest-check allure-pytest pytest-rerunfailures PyYAML
```

验证：

```
python -c "import appium, pytest, selenium; print('ok')"
```

### 3.5 安装 Appium Inspector

Windows 下载地址：

```
https://github.com/appium/appium-inspector/releases
```

下载 Windows 版本安装包，安装后打开 `Appium Inspector`。

Appium Inspector 作用：

- 查看 iOS 页面截图
- 查看元素树
- 获取 `name`、`label`、`value`、`type`
- 测试 locator 是否能找到元素
- 调试点击、输入、滑动

## 4. Mac 环境安装

### 4.1 安装 Xcode

在 Mac App Store 安装 Xcode，然后执行：

```
xcodebuild -version
xcode-select --install
```

打开一次 Xcode，同意协议。

### 4.2 安装 Node.js 和 Appium

```
node -v
npm -v
npm i --location=global appium
appium --version
```

Appium 官方安装命令就是全局安装 `appium`。

### 4.3 安装 iOS XCUITest Driver

```
appium driver install xcuitest
appium driver list
```

验证：

```
appium
```

日志里应能看到 XCUITest driver loaded。

也可以执行：

```
appium driver doctor xcuitest
```

## 5. iPhone 真机准备

### 5.1 连接并信任设备

1. iPhone 用数据线连接 Mac。
2. iPhone 弹出“信任此电脑”，点击信任。
3. Mac 打开 Xcode。
4. 打开 `Window -> Devices and Simulators`。
5. 确认 iPhone 出现在设备列表。

### 5.2 打开开发者设置

iOS 16+：

```
Settings -> Privacy & Security -> Developer Mode -> ON
```

打开 UI 自动化：

```
Settings -> Developer -> Enable UI Automation -> ON
```

关闭缩放，避免坐标偏移：

```
Settings -> Accessibility -> Zoom -> OFF
```

### 5.3 WebDriverAgent 签名

iOS 真机必须签名 WDA。Mac 执行：

```
appium driver run xcuitest open-wda
```

Xcode 会打开 WDA 工程。然后：

1. Xcode 登录 Apple Account。
2. 选择 `WebDriverAgentRunner` target。
3. Signing & Capabilities 里选择 Team。
4. Bundle Identifier 改成唯一值，例如：

```
com.yourcompany.WebDriverAgentRunner
```

如果 iPhone 提示开发者证书不受信任：

```
Settings -> General -> VPN & Device Management -> Trust Developer
```

## 6. Mac 启动 Appium 服务

查看 Mac IP：

```
ipconfig getifaddr en0
```

假设 Mac IP 是：

```
192.168.1.20
```

启动 Appium：

```
appium -a 0.0.0.0 -p 4723
```

双设备建议启动两个端口：

```
appium -a 0.0.0.0 -p 4723
appium -a 0.0.0.0 -p 4724
```

Windows 测试 Mac 端口是否通：

```
Test-NetConnection 192.168.1.20 -Port 4723
```

## 7. Appium Inspector 连接 iOS

Windows 打开 Appium Inspector：

```
Remote Host: 192.168.1.20
Remote Port: 4723
Remote Path: /
```

如果 Mac 上 Appium 用的是 `/wd/hub`，Remote Path 才填：

```
/wd/hub
```

真机 Capability 示例：

```
{
  "platformName": "iOS",
  "appium:automationName": "XCUITest",
  "appium:deviceName": "iPhone",
  "appium:udid": "你的iPhone-UDID",
  "appium:bundleId": "你的iOS包名",
  "appium:noReset": true,
  "appium:wdaLocalPort": 8100,
  "appium:xcodeOrgId": "你的Apple Team ID",
  "appium:xcodeSigningId": "Apple Development",
  "appium:updatedWDABundleId": "com.yourcompany.WebDriverAgentRunner"
}
```

模拟器 Capability 示例：

```
{
  "platformName": "iOS",
  "appium:automationName": "XCUITest",
  "appium:deviceName": "iPhone 15",
  "appium:platformVersion": "17.5",
  "appium:app": "/Users/xxx/Desktop/Santiao.app",
  "appium:noReset": true,
  "appium:wdaLocalPort": 8100
}
```

注意：`appium:app` 路径是 Mac 上的路径，不是 Windows 路径。Windows 远程连接 Mac 时，建议先让 iOS App 已安装在手机上，然后用 `bundleId` 启动。

## 8. Windows 先跑一个最小连接脚本

新建临时文件：

```
D:\projects\santiao-anti\ios_connection_check.py
```

内容：

```
from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy

caps = {
    "platformName": "iOS",
    "appium:automationName": "XCUITest",
    "appium:deviceName": "iPhone",
    "appium:udid": "你的iPhone-UDID",
    "appium:bundleId": "你的iOS包名",
    "appium:noReset": True,
    "appium:wdaLocalPort": 8100,
}

options = XCUITestOptions().load_capabilities(caps)
driver = webdriver.Remote("http://192.168.1.20:4723", options=options)

print(driver.capabilities)
print(driver.page_source[:500])

driver.quit()
```

执行：

```
python ios_connection_check.py
```

能打印 capabilities 和 page source，说明 Windows 已经能控制 Mac 上的 iOS 设备。

## 9. iOS 元素定位规则

优先级：

| 优先级 | 定位方式         | 示例                                                         |
| ------ | ---------------- | ------------------------------------------------------------ |
| 1      | Accessibility ID | `AppiumBy.ACCESSIBILITY_ID, "login_button"`                  |
| 2      | iOS Predicate    | `AppiumBy.IOS_PREDICATE, "name == '登录'"`                   |
| 3      | iOS Class Chain  | `AppiumBy.IOS_CLASS_CHAIN, "**/XCUIElementTypeButton[`name == '登录'`]"` |
| 4      | XPath            | 只在没办法时使用                                             |

Android 到 iOS 对照：

| Android                   | iOS                                 |
| ------------------------- | ----------------------------------- |
| `resource-id`             | `accessibilityIdentifier` / `name`  |
| `text`                    | `label` / `name` / `value`          |
| `android.widget.TextView` | `XCUIElementTypeStaticText`         |
| `android.widget.EditText` | `XCUIElementTypeTextField`          |
| `ANDROID_UIAUTOMATOR`     | `IOS_PREDICATE` / `IOS_CLASS_CHAIN` |
| Android Toast             | iOS 通常是 Alert 或 StaticText      |

iOS locator 示例：

```
from appium.webdriver.common.appiumby import AppiumBy

LOGIN_BTN = (AppiumBy.ACCESSIBILITY_ID, "login_button")
PHONE_INPUT = (AppiumBy.IOS_PREDICATE, "type == 'XCUIElementTypeTextField' AND name == 'phone_input'")
PASSWORD_INPUT = (AppiumBy.IOS_PREDICATE, "type == 'XCUIElementTypeSecureTextField'")
CHAT_TITLE = (AppiumBy.IOS_PREDICATE, "label CONTAINS '聊天'")
SEND_BTN = (AppiumBy.IOS_CLASS_CHAIN, "**/XCUIElementTypeButton[`name == '发送'`]")
```

## 10. 你的项目需要改造的位置

你当前项目 Android 驱动入口在：

```
D:\projects\santiao-anti\core\driver_factory.py
```

现在固定使用：

```
from appium.options.android import UiAutomator2Options
```

iOS 要增加：

```
from appium.options.ios import XCUITestOptions
```

按 `platformName` 判断：

```
platform_name = str(desired_caps.get("platformName", "")).lower()

if platform_name == "ios":
    options = XCUITestOptions().load_capabilities(desired_caps)
else:
    options = UiAutomator2Options().load_capabilities(desired_caps)
```

同时 iOS 不应该混入 Android 的：

```
appPackage
appActivity
systemPort
uiautomator2ServerLaunchTimeout
adbExecTimeout
```

建议把 `config/devices.yaml` 改成分平台配置，例如：

```
current_env: "ios_dev"

apps:
  android:
    "appium:automationName": "UiAutomator2"
    "appium:appPackage": "com.santiaotalk.im"
    "appium:appActivity": "com.vvchat.vcapp.activity.MainActivity"

  ios:
    "appium:automationName": "XCUITest"
    "appium:bundleId": "你的iOS包名"
    "appium:noReset": true

devices:
  ios_dev:
    sender:
      platformName: "iOS"
      udid: "发送方iPhone-UDID"
      deviceName: "Sender-iPhone"
      wdaLocalPort: 8100
      appiumServerUrl: "http://192.168.1.20:4723"

    receiver:
      platformName: "iOS"
      udid: "接收方iPhone-UDID"
      deviceName: "Receiver-iPhone"
      wdaLocalPort: 8101
      appiumServerUrl: "http://192.168.1.20:4724"
```

## 11. iOS 测试用例执行流程

Mac：

```
appium -a 0.0.0.0 -p 4723
```

Windows：

```
cd D:\projects\santiao-anti
.\.venv\Scripts\activate
$env:ENV="ios_dev"
pytest tests\smoke_test\test_smoke_chat.py::TestSmokeChatCore::test_send_text_message -vs
```

双设备时，Mac 启动两个 Appium 服务：

```
appium -a 0.0.0.0 -p 4723
appium -a 0.0.0.0 -p 4724
```

Windows 执行双设备用例：

```
$env:ENV="ios_dev"
pytest tests\chat\test_chat.py::TestChat::test_send_and_receive_text_message -vs
```

## 12. 推荐学习顺序

1. Windows 安装 Python、依赖、Appium Inspector。
2. Mac 安装 Xcode、Appium、XCUITest Driver。
3. Mac 真机跑通 WDA。
4. Windows Appium Inspector 连接 Mac Appium。
5. 定位登录页 3 个元素：账号输入框、密码输入框、登录按钮。
6. Windows 跑通 `ios_connection_check.py`。
7. 改造 `DriverFactory` 支持 iOS。
8. 新建一套 iOS locator，不要直接覆盖 Android locator。
9. 先迁移登录用例。
10. 再迁移聊天发送消息用例。
11. 最后迁移长按、相册、文件、双设备、网络异常等复杂场景。

## 13. 常见问题

| 问题                             | 原因                                 | 处理                                                |
| -------------------------------- | ------------------------------------ | --------------------------------------------------- |
| Windows 连不上 Appium            | Mac 防火墙或 Appium 只监听 127.0.0.1 | Mac 用 `appium -a 0.0.0.0 -p 4723`                  |
| Inspector 能连但启动失败         | WDA 签名失败                         | 重新配置 Xcode Team、Bundle ID                      |
| `xcodebuild exited with code 65` | 证书/签名问题                        | 检查 WDA Signing                                    |
| `xcodebuild exited with code 70` | Xcode 目标设备或版本不匹配           | 检查 iOS 版本、Xcode 版本、UDID                     |
| 找不到元素                       | iOS 没有稳定 accessibility id        | 找开发加 `accessibilityIdentifier`                  |
| XPath 很慢                       | iOS XPath 依赖 XML page source       | 优先使用 `ACCESSIBILITY_ID`、Predicate、Class Chain |
| 双设备启动冲突                   | 两台设备共用 WDA 端口                | sender 用 8100，receiver 用 8101                    |

## 14. 官方资料

- [Appium 安装文档](https://appium.io/docs/en/2.0/quickstart/install/)
- [XCUITest Driver 安装](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/installation/)
- [XCUITest 系统要求](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/system-requirements/)
- [iOS 设备准备](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/device-setup/)
- [WDA 签名配置](https://appium.github.io/appium-xcuitest-driver/latest/getting-started/provisioning-profile/)
- [XCUITest Capabilities](https://appium.github.io/appium-xcuitest-driver/latest/reference/capabilities/)
- [iOS Locator 策略](https://appium.github.io/appium-xcuitest-driver/latest/reference/locator-strategies/)
- [Appium Inspector](https://github.com/appium/appium-inspector)
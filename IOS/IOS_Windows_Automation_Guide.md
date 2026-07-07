# Windows 使用 iOS 自动化测试教程

下面是可直接复制成 `Windows_iOS_Real_Device_Appium_Guide.md` 的版本。

```
# Windows 连接 iOS 真机做 Appium 自动化教程

## 0. 先看结论

iOS 自动化默认依赖 `macOS + Xcode + WebDriverAgent(WDA)`。Appium XCUITest 官方要求常规 iOS 自动化需要 macOS、Xcode、Appium；如果在非 macOS 主机运行，只支持“真机 + 不依赖 Xcode 的模式”，并且必须提供 `udid`，再配合 `webDriverAgentUrl` 或 iOS 18+ 的 `usePreinstalledWDA`。

所以 Windows 上有两条路线：

| 路线 | 是否推荐 | 说明 |
|---|---:|---|
| Windows 写脚本，Mac 跑 Appium/WDA | 推荐 | 最稳，适合长期维护 |
| Windows 直接接 iPhone，使用已签名/已安装 WDA | 可行但复杂 | 需要先准备好可运行的 WDA |
| Windows 从 0 编译签名 WDA | 不现实 | 没有 Xcode，做不了标准签名编译 |

## 1. 需要准备的东西

| 类型 | 工具 |
|---|---|
| 自动化服务 | Appium 2/3 |
| iOS 驱动 | Appium XCUITest Driver |
| Python 客户端 | Appium-Python-Client |
| 元素查看 | Appium Inspector |
| iOS 设备通信 | tidevice 或 go-ios |
| 必需资产 | iPhone UDID、被测 App 的 `bundleId`、已签名 WDA、WDA Bundle ID |

## 2. Windows 安装基础环境

安装 Node.js LTS、Python 3.10+、iTunes 或 Apple Devices，确保 Apple Mobile Device Service 正常。

验证：

```powershell
node -v
npm -v
python --version
pip --version
```

安装 Appium：

```
npm install -g appium
appium -v
appium driver install xcuitest
appium driver list --installed
```

安装 Python 依赖：

```
python -m venv .venv
.\.venv\Scripts\activate
pip install Appium-Python-Client pytest selenium pyyaml allure-pytest pytest-check
```

## 3. 安装 iOS 真机通信工具

推荐先装 `tidevice`：

```
pip install -U "tidevice[openssl]"
tidevice version
tidevice pair
tidevice list
```

如果 `tidevice` 不稳定，再用 `go-ios`：

```
npm install -g go-ios
ios --help
ios list
```

iOS 17+ 使用 go-ios 时通常还需要 tunnel，Windows 需要按 go-ios 文档放置 `wintun.dll`。

## 4. iPhone 手机设置

1. 用数据线连接 Windows。
2. 手机弹窗选择“信任此电脑”。
3. 打开 `设置 -> 隐私与安全性 -> 开发者模式`。
4. 重启手机后确认开启开发者模式。
5. 确认设备能被识别：

```
tidevice list
```

记录输出里的 `udid`。

## 5. 准备 WDA

WDA 是 Appium 控制 iOS App 的核心服务。

你需要让 iOS 开发或一台 Mac 先完成一次：

1. 使用 Xcode 打开 Appium WebDriverAgent。
2. 给 `WebDriverAgentRunner` 配置开发者证书。
3. 修改唯一 Bundle ID，例如：`com.yourcompany.WebDriverAgentRunner`。
4. Build/Test 到你的 iPhone。
5. 在 iPhone 上信任开发者证书。
6. 确认 WDA 可以启动。

Windows 侧拿到这些信息：

```
iPhone UDID = xxxxx
iOS version = 17.x / 18.x
被测 App bundleId = com.santiaotalk.im.ios
WDA bundleId = com.yourcompany.WebDriverAgentRunner
```

## 6. Windows 启动 WDA 方式 A：tidevice

```
tidevice wdaproxy -B com.yourcompany.WebDriverAgentRunner --port 8200
```

验证 WDA：

```
Invoke-RestMethod http://127.0.0.1:8200/status
```

能返回 JSON 就说明 WDA 已经跑起来。

## 7. 启动 Appium

```
appium -a 0.0.0.0 -p 4723 --use-drivers xcuitest
```

Appium 2/3 默认地址通常是：

```
http://127.0.0.1:4723
```

不要默认写 `/wd/hub`，除非你启动 Appium 时显式设置了 base path。

## 8. Appium Inspector 连接真机

打开 Appium Inspector，填写：

```
Remote Host: 127.0.0.1
Remote Port: 4723
Remote Path: /
```

Capabilities 使用：

```
{
  "platformName": "iOS",
  "appium:automationName": "XCUITest",
  "appium:udid": "你的iPhoneUDID",
  "appium:bundleId": "你的被测AppBundleId",
  "appium:noReset": true,
  "appium:webDriverAgentUrl": "http://127.0.0.1:8200"
}
```

点击 Start Session。成功后可以查看页面结构、点击元素、复制 locator。

## 9. iOS 元素定位规则

优先级：

| 优先级 | 定位方式         | 示例                                                         |
| ------ | ---------------- | ------------------------------------------------------------ |
| 1      | Accessibility ID | `AppiumBy.ACCESSIBILITY_ID, "login_button"`                  |
| 2      | iOS Predicate    | `AppiumBy.IOS_PREDICATE, "label == '登录'"`                  |
| 3      | iOS Class Chain  | `AppiumBy.IOS_CLASS_CHAIN, "**/XCUIElementTypeButton[\`label == '登录'`]"` |
| 4      | XPath            | 最后兜底，慢且易碎                                           |

要求 iOS 开发给关键控件加 `accessibilityIdentifier`，否则后期维护成本很高。

## 10. 最小 Python 用例

保存为 `test_ios_smoke.py`：

```
from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.webdriver.common.appiumby import AppiumBy

caps = {
    "platformName": "iOS",
    "appium:automationName": "XCUITest",
    "appium:udid": "你的iPhoneUDID",
    "appium:bundleId": "你的被测AppBundleId",
    "appium:noReset": True,
    "appium:webDriverAgentUrl": "http://127.0.0.1:8200",
}

driver = webdriver.Remote(
    "http://127.0.0.1:4723",
    options=XCUITestOptions().load_capabilities(caps)
)

print(driver.page_source[:1000])

# 示例：点击登录按钮
# driver.find_element(AppiumBy.ACCESSIBILITY_ID, "login_button").click()

driver.quit()
```

执行：

```
pytest test_ios_smoke.py -vs
```

## 11. 接入你现有项目的改造方向

你现在项目是 Android 的 `driver_sender / driver_receiver` 双设备模型。iOS 也建议保留这个模型。

后续需要改造：

1. `core/driver_factory.py` 根据 `platformName` 选择：
   - Android：`UiAutomator2Options`
   - iOS：`XCUITestOptions`
2. `config/devices.yaml` 增加 iOS 环境：

```
current_env: "ios_local"

app_ios:
  "appium:automationName": "XCUITest"
  "appium:noReset": true

devices:
  ios_local:
    sender:
      platformName: "iOS"
      udid: "你的iPhoneUDID"
      deviceName: "iPhone"
      bundleId: "你的被测AppBundleId"
      appiumServerUrl: "http://127.0.0.1:4723"
      webDriverAgentUrl: "http://127.0.0.1:8200"
```

1. locator 分平台维护：

```
locators/
  android/
  ios/
```

1. 不要把 Android 的 `ANDROID_UIAUTOMATOR`、`resource-id`、`android.widget.*` 直接搬到 iOS。

## 12. 常见问题

| 问题                   | 原因                           | 处理                                           |
| ---------------------- | ------------------------------ | ---------------------------------------------- |
| 报 `xcodebuild` 找不到 | Appium 试图在 Windows 编译 WDA | 使用 `webDriverAgentUrl` 或远程 Mac            |
| Inspector 连不上       | Appium 地址/Path 错            | Appium 2/3 通常 Path 用 `/`                    |
| `tidevice list` 没设备 | 未信任电脑/Apple 驱动异常      | 重插线、信任、重启 Apple Mobile Device Service |
| WDA `/status` 无响应   | WDA 未启动或 Bundle ID 错      | 重新执行 `tidevice wdaproxy`                   |
| 元素找不到             | iOS 没有 accessibility id      | 找开发补 `accessibilityIdentifier`             |
| 双设备冲突             | WDA 端口冲突                   | sender 用 8200，receiver 用 8201               |

## 13. 推荐资料

- Appium 安装文档：https://appium.io/docs/en/latest/quickstart/install/
- Appium Server 参数：https://appium.io/docs/en/latest/reference/cli/server/
- XCUITest 系统要求：https://appium.github.io/appium-xcuitest-driver/latest/getting-started/system-requirements/
- XCUITest Capabilities：https://appium.github.io/appium-xcuitest-driver/latest/reference/capabilities/
- iOS 定位策略：https://appium.github.io/appium-xcuitest-driver/latest/reference/locator-strategies/
- 预安装 WDA：https://appium.github.io/appium-xcuitest-driver/latest/guides/run-preinstalled-wda/
- 自己管理 WDA：https://appium.github.io/appium-xcuitest-driver/latest/guides/wda-custom-server/
- Appium Inspector：https://github.com/appium/appium-inspector
- Appium Python Client：https://github.com/appium/python-client
- tidevice：https://github.com/alibaba/tidevice
- go-ios：https://github.com/danielpaulus/go-ios

```
关键点再强调一次：你要在 Windows 上直连 iOS 真机可以做，但前提是 WDA 已经被签名、安装，并且能通过 `tidevice wdaproxy` 或类似工具跑起来。没有这一步，Windows 不能像 Android 一样直接安装驱动后就开始定位元素。
```
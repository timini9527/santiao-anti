import allure
import pytest
from appium.webdriver.webdriver import WebDriver

from core.logger_utils import LogIcon, logger

# XCUITest 应用运行状态：4 = 前台运行 (RUNNING_IN_FOREGROUND)
APP_STATE_FOREGROUND: int = 4


def _get_bundle_id(driver: WebDriver) -> str:
    """从当前会话能力集中读取被测应用 Bundle ID (来源于 config/devices.yaml 的 appium:bundleId)"""
    bundle_id = driver.capabilities.get("bundleId") or driver.capabilities.get("appium:bundleId")
    assert bundle_id, "❌ 会话能力集中缺少 bundleId，请检查 config/devices.yaml 的 ios_app 配置"
    return str(bundle_id)


@pytest.mark.p2
@allure.severity(allure.severity_level.NORMAL)
@allure.epic("系统冒烟与通用功能")
@allure.feature("通用启动与流程Demo")
@allure.story("iOS App启动与前台状态校验")
@allure.title("验证 iOS App 启动后处于前台运行状态")
def test_ios_app_launch_state(driver_ios_sender: WebDriver) -> None:
    """
    测试用例：验证 WDA 链路连通，且被测 App 被拉起至前台。
    测试步骤：
    1. 读取会话 Bundle ID 并激活被测应用；
    2. 断言应用运行状态为前台运行；
    3. 断言 WDA 当前活动应用即为被测应用。
    """
    bundle_id = _get_bundle_id(driver_ios_sender)

    with allure.step(f"1. 激活被测应用: {bundle_id}"):
        logger.info(f"{LogIcon.ACTION} 正在激活 iOS 应用: {bundle_id}")
        driver_ios_sender.activate_app(bundle_id)

    with allure.step("2. 校验应用处于前台运行状态"):
        app_state = driver_ios_sender.query_app_state(bundle_id)
        assert app_state == APP_STATE_FOREGROUND, f"❌ 应用未处于前台，当前状态码: {app_state}"

    with allure.step("3. 校验 WDA 当前活动应用"):
        active_info: dict = driver_ios_sender.execute_script("mobile: activeAppInfo")
        assert active_info.get("bundleId") == bundle_id, f"❌ 当前活动应用不符: {active_info}"

    allure.attach(
        driver_ios_sender.get_screenshot_as_png(),
        name="iOS 启动页截图",
        attachment_type=allure.attachment_type.PNG,
    )
    logger.info(f"{LogIcon.SUCCESS} iOS App 启动状态校验通过")


@pytest.mark.p2
@allure.severity(allure.severity_level.NORMAL)
@allure.epic("系统冒烟与通用功能")
@allure.feature("通用启动与流程Demo")
@allure.story("iOS 控件树抓取能力校验")
@allure.title("验证 iOS 当前页面控件树可正常抓取")
def test_ios_page_source_available(driver_ios_sender: WebDriver) -> None:
    """
    测试用例：验证 WDA 能返回当前页面原生 XCUITest 控件树，作为后续元素定位的基础能力。
    测试步骤：
    1. 抓取当前页面控件树；
    2. 断言控件树包含 XCUIElementTypeApplication 根节点；
    3. 将控件树作为附件归档至 Allure 报告，便于定位器维护。
    """
    with allure.step("1. 抓取当前页面控件树"):
        page_source = driver_ios_sender.page_source

    with allure.step("2. 校验控件树根节点"):
        assert "XCUIElementTypeApplication" in page_source, "❌ 控件树缺少 Application 根节点，WDA 快照异常"

    allure.attach(page_source, name="iOS 页面控件树", attachment_type=allure.attachment_type.XML)
    logger.info(f"{LogIcon.SUCCESS} iOS 控件树抓取成功，长度: {len(page_source)}")


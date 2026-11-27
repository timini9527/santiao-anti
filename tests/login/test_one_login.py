import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon


@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-一键登录")
@allure.story("一键登录场景验证")
class TestOneLogin:
    """一键登录模块测试"""

    _has_entered_phone_login = False

    @pytest.fixture(autouse=True)
    def enter_phone_login_page(self, request, driver_sender):
        """智能路由：初始化页面对象，并根据用例标签决定是否进入手机号登录表单"""
        self.loginPage = LoginPage(driver_sender)
        current_test_node = request.node
        is_lo_test = current_test_node.get_closest_marker("no_login_entrance") is not None
        if not is_lo_test:
            if not TestOneLogin._has_entered_phone_login:
                logger.info(f"{LogIcon.ACTION} 首次进入手机号表单，执行点击操作。")
                self.loginPage.click_phone_login_button()
                TestOneLogin._has_entered_phone_login = True
            else:
                logger.debug(f"{LogIcon.ACTION} 检测到已经处于手机号表单页，跳过点击，直接开始测试。")
        else:
            logger.info(f"{LogIcon.ACTION} 探测到 @pytest.mark.no_login_entrance 标签，停留在登录首页，不进入手机号表单。")
        yield

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("无卡状态时，首页点击一键登录验证提示")
    @allure.title("无卡状态时，首页点击一键登录验证提示-状态：已完成")
    @pytest.mark.no_login_entrance
    def test_login_no_card_one_click(self):
        """验证无 SIM 卡状态下点击一键登录，按当前平台弹出对应网络/SIM 卡异常 Toast"""
        allure.dynamic.title("无卡状态时，首页点击一键登录验证提示")
        logger.info(f"{LogIcon.ACTION} 开始执行专属用例: 无卡状态时，一键登录验证")
        expected_toast = ToastMsg.SWITCH_NETWORK.for_platform(self.loginPage.platform)

        with allure.step("1. 点击首页一键登录按钮"):
            self.loginPage.click_one_click_login_button()

        with allure.step(f"2. 验证无卡/网络异常 Toast (预期: '{expected_toast}')"):
            msg = self.loginPage.get_toast_text(expected_toast=expected_toast)
            check.equal(msg, expected_toast, f"❌ 预期Toast为: '{expected_toast}', 实际: '{msg}'")
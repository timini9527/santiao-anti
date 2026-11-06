import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from utils.cv_recognition.ocr_utils import OcrUtils

@allure.epic('IM核心功能测试')
@allure.feature('登录注册模块-一键登录')
@allure.story("智能路由：根据用例标签决定进入哪个页面类级别前置：App 启动后只点一次'手机号登录'进入登录表单")
class TestOneLogin:
    _has_entered_phone_login = False

    @pytest.fixture(autouse=True)
    def enter_phone_login_page(self, request, driver_sender):
        """ 智能路由：根据用例标签决定进入哪个页面类级别前置：App 启动后只点一次'手机号登录'进入登录表单"""
        self.loginPage = LoginPage(driver_sender)
        current_test_node = request.node
        is_lo_test = current_test_node.get_closest_marker('no_login_entrance') is not None
        if not is_lo_test:
            if not TestOneLogin._has_entered_phone_login:
                logger.info(f'{LogIcon.ACTION} 首次进入手机号表单，执行点击操作。')
                self.loginPage.click_phone_login_button()
                TestOneLogin._has_entered_phone_login = True
            else:
                logger.debug(f'{LogIcon.ACTION} 检测到已经处于手机号表单页，跳过点击，直接开始测试。')
        else:
            logger.info(f'{LogIcon.ACTION} 探测到 @pytest.mark.no_login_entrance 标签，停留在登录首页，不进入手机号表单。')
        yield

    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, driver_sender):
        """每条用例运行前的初始化：实例化页面对象"""
        self.loginPage = LoginPage(driver_sender)
        self.ocr_utils = OcrUtils(driver_sender)
        yield

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('无卡状态时，首页点击一键登录验证弹窗')
    @allure.title('无卡状态时，首页点击一键登录验证弹窗-状态：已完成')
    @pytest.mark.no_login_entrance
    def test_login_no_card_one_click(self):
        allure.dynamic.title('无卡状态时，首页点击一键登录验证弹窗')
        logger.info(f'{LogIcon.ACTION} 开始执行专属用例: 无卡状态时，一键登录验证')
        with allure.step('1. 初始化由于防刷测试环境'):
            self.loginPage.click_one_click_login_button()
        with allure.step('2. 验证Toast'):
            msg = self.loginPage.get_toast_text()
            check.equal(msg, ToastMsg.SWITCH_NETWORK, f"❌ 预期Toast为: '{ToastMsg.SWITCH_NETWORK}', 实际: '{msg}'")
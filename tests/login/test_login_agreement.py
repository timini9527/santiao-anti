import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from core.logger_utils import logger
from utils.cv_recognition.ocr_utils import OcrUtils

@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-协议校验")
@allure.story("登录模块协议功能测试")
class TestLoginAgreement:
    """登录模块协议功能测试"""

    # 标记是否已经进入过手机号登录页面
    _has_entered_phone_login = False

    @pytest.fixture(autouse=True)
    def enter_phone_login_page(self, request, driver_sender):
        """智能路由：进入手机号登录表单"""
        self.loginPage = LoginPage(driver_sender)
        
        if not TestLoginAgreement._has_entered_phone_login:
            logger.info("🚀 首次进入手机号表单，执行点击操作。")
            self.loginPage.click_phone_login_button()
            TestLoginAgreement._has_entered_phone_login = True # 上锁
        else:
            logger.debug("⚡ 检测到已经处于手机号表单页，跳过点击，直接开始测试。")
            
        yield

    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, driver_sender):
        """每条用例运行前的初始化：实例化页面对象"""
        self.loginPage = LoginPage(driver_sender)
        self.ocr_utils = OcrUtils(driver_sender)
        yield

    @allure.story("验证用户协议、隐私协议和未成年协议三个协议是否正常展示")
    def test_verify_agreements_exist(self):
        """验证三个协议文本是否正常展示"""
        full_text = self.loginPage.get_agreement_text()
        with allure.step("断言包含所有协议名称"):
            assert "《用户协议》" in full_text, "缺少用户协议"
            assert "《隐私协议》" in full_text, "缺少隐私协议"
            assert "《未成年人个人信息保护规则》" in full_text, "缺少未成年人保护规则"

    @allure.story("验证用户协议、隐私协议和未成年协议文本展现及跳转逻辑")
    @pytest.mark.parametrize("agreement_name, expected_title, is_popup, click_login_btn", [
        # 主页面直接点击协议验证
        ("《用户协议》", "三条软件许可及服务协议", False, False),
        ("《隐私协议》", "三条软件 隐私政策", False, False),
        ("《未成年人个人信息保护规则》", "三条未成年人及儿童隐私保护政策", False, False),
        # 未勾选协议 -> 点击登录触发弹窗 -> 弹窗内点击协议验证 弹窗持续存在，所以仅第一次需要点击登录按钮
        ("《用户协议》", "三条软件许可及服务协议", True, True),
        ("《隐私协议》", "三条软件 隐私政策", True, False),
        ("《未成年人个人信息保护规则》", "三条未成年人及儿童隐私保护政策", True, False)
    ], ids=[
        "Main_UserAgreement", "Main_PrivacyPolicy", "Main_ChildrenPrivacy",
        "Popup_UserAgreement", "Popup_PrivacyPolicy", "Popup_ChildrenPrivacy"
    ])
    def test_verify_agreements_jump(self, agreement_name, expected_title, is_popup, click_login_btn):
        allure.dynamic.title(f"{'弹窗' if is_popup else '主页'}-{agreement_name}验证")
        logger.info(f"🚀 开始执行专属用例: {'弹窗' if is_popup else '主页'}-{agreement_name}验证")

        with allure.step("1. 点击登录按钮（以触发弹窗）"):
            if click_login_btn:
                self.loginPage.click_login_button()
            pre_title = self.loginPage.get_top_title()

        step_name = "2. 弹窗内验证" if is_popup else "1. 主页直接验证"
        with allure.step(f"{step_name}{agreement_name}"):
            # 弹窗场景中，使用 match_index=-1 保证点击位于视图最上层（即最底部的弹窗部分）
            m_idx = -1 if is_popup else 0
            success = self.ocr_utils.click_text_by_ocr(ocr_text=agreement_name, match_index=m_idx)
            check.is_true(success, f"未能通过 OCR 找到并点击{agreement_name}")
            
            protocol_title = self.loginPage.get_top_title()
            check.equal(protocol_title, expected_title, f"❌ 预期协议页面 top 标题为: '{expected_title}', 实际: '{protocol_title}'")

            if pre_title != protocol_title:
                self.loginPage.click_back_btn()

import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from utils.cv_recognition.ocr_utils import OcrUtils
from strategy.chat.chat_strategy import PRIVATE_USER1 



# 分平台登录冒烟默认账号配置（避免三端并行互踢，iOS 建议后续替换为无 999+ 会话的独立轻量号）
PLATFORM_SMOKE_ACCOUNTS: dict[str, tuple[str, str]] = {
    'harmonyos': ('19200000006', 'a1234567B'),
    'android': ('19200000007', 'a1234567B'),
    'ios': ('19200000008', 'a1234567B'),
}

# 分平台登录冒烟副账号配置（供连续切换账号场景使用，后续补充各端独立副号即可彻底消除三端并发互踢）
PLATFORM_SMOKE_SECONDARY_ACCOUNTS: dict[str, tuple[str, str]] = {
    'harmonyos': ('19200000016', 'a1234567B'),
    'android': ('19200000017', 'a1234567B'),
    'ios': ('19200000018', 'a1234567B'),
}


class BaseSmokeLogin:
    """登录注册模块的测试基类，提取公共的初始化和状态控制"""
    _has_entered_phone_login = False

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.loginPage = LoginPage(driver_sender)
        self.ocr_utils = OcrUtils(driver_sender)
        self.default_account, self.default_password = PLATFORM_SMOKE_ACCOUNTS.get(
            self.loginPage.platform,
            PLATFORM_SMOKE_ACCOUNTS['android'],
        )
        self.secondary_account, self.secondary_password = PLATFORM_SMOKE_SECONDARY_ACCOUNTS.get(
            self.loginPage.platform,
            PLATFORM_SMOKE_SECONDARY_ACCOUNTS['android'],
        )
        if not BaseSmokeLogin._has_entered_phone_login:
            logger.info(f'{LogIcon.ACTION} 首次进入手机号表单，执行点击操作。')
            self.loginPage.click_phone_login_button()
            BaseSmokeLogin._has_entered_phone_login = True
        yield

@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-登录注册-协议校验')
class TestSmokeLoginAgreement(BaseSmokeLogin):
    """登录模块协议功能及未登录前置校验冒烟用例"""

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('验证协议存在')
    @allure.title('验证用户协议、隐私协议和未成年协议三个协议是否正常展示-状态：已完成')
    def test_agreement_display(self):
        full_text = self.loginPage.get_agreement_text()
        with allure.step('断言包含所有协议名称'):
            check.is_true('《用户协议》' in full_text, '缺少用户协议')
            check.is_true('《隐私协议》' in full_text or '《隐私政策》' in full_text , '缺少隐私协议')
            check.is_true('《未成年人个人信息保护规则》' in full_text, '缺少未成年人保护规则')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story('验证协议跳转')
    @allure.title('主页-《用户协议》跳转验证-状态：已完成')
    def test_agreement_jump(self):
        agreement_name = '《用户协议》'
        expected_title = '三条软件许可及服务协议 | 用户协议'
        with allure.step('1. 获取进入前的标题'):
            pre_title = self.loginPage.get_top_title()
        with allure.step(f'2. 点击 {agreement_name} 并校验跳转页面标题'):
            if self.loginPage.platform == 'ios':
                success = self.loginPage.click_agreement_link(agreement_name)
            else:
                success = self.ocr_utils.click_text_by_ocr(ocr_text=agreement_name, match_index=0)
            check.is_true(success, f'未能找到并点击 {agreement_name}')
            protocol_title = self.loginPage.get_top_title()
            check.is_in(protocol_title, expected_title, f"❌ 预期协议页面 top 标题为: '{expected_title}', 实际: '{protocol_title}'")
            if pre_title != protocol_title:
                self.loginPage.click_back_btn()

    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @allure.story('协议拦截与弹窗处理')
    @allure.title('未勾选协议直接点击登录 - 弹出服务协议确认框并可拒绝/同意-状态：已完成')
    def test_login_without_agreement_popup(self):
        """未勾选协议点击登录时，应弹出确认协议弹窗；点击拒绝能留在登录页；点击同意并登录能成功登录"""
        account = self.default_account
        password = self.default_password
        with allure.step('1. 初始化登录环境并输入数据（不勾选协议）'):
            self.loginPage.click_password_login_button()
            self.loginPage.input_account(account)
            self.loginPage.input_password(password)
        with allure.step('2. 未勾选协议，直接点击登录按钮，验证协议弹窗弹出'):
            self.loginPage.click_login_button(auto_dismiss_save_pwd=False)
            popup_title = self.loginPage.get_agreement_popup_title()
            check.is_in('用户协议及隐私政策', popup_title, '❌ 未弹出服务协议与隐私政策确认框')
        with allure.step('3. 点击‘不同意并退出’（拒绝），验证仍留在登录页面'):
            self.loginPage.close_agreement_popup()
            check.is_true(self.loginPage.is_on_phone_login_page(), '❌ 拒绝协议弹窗后未停留在账号密码登录页')
        with allure.step('4. 再次点击登录按钮，并同意弹窗协议，验证登录成功'):
            self.loginPage.click_login_button(auto_dismiss_save_pwd=False)
            self.loginPage.click_handle_agreement_popup()
            is_success = False
            try:
                is_success = self.loginPage.is_login_success()
                check.is_true(is_success, '❌ 同意协议弹窗后，未能成功进入主页')
            finally:
                with allure.step('5. 环境清理：确保账号登出'):
                    if is_success:
                        self.loginPage.logout_if_logged_in(wait_toast=False)
                        self.loginPage.wait_for_login_page()
                        # 鸿蒙/iOS 登出后回到登录入口主页，重置标记确保后续用例正常点击进入手机号表单
                        BaseSmokeLogin._has_entered_phone_login = False



@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-登录注册-密码登录')
class TestSmokeLoginPwd(BaseSmokeLogin):
    """手机账号密码正常登录与记住账号逻辑冒烟用例"""

    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.smoke
    @allure.story('账号密码成功登录')
    @allure.title('手机账号密码登录场景回归验证-状态：已完成')
    def test_pwd_login_success(self):
        account = self.default_account
        password = self.default_password
        with allure.step('1. 初始化登录环境并输入数据'):
            self.loginPage.click_password_login_button()
            self.loginPage.input_account(account)
            self.loginPage.input_password(password)
        with allure.step('2. 同意协议并执行登录'):
            self.loginPage.click_user_agreement()
            self.loginPage.click_login_button()
        is_success = False
        try:
            with allure.step('3. 最终登录进入主页面验证'):
                is_success = self.loginPage.is_login_success()
                check.is_true(is_success, '❌ 预期登录成功进入主页，但未检测到主页元素')
        finally:
            with allure.step('4. 环境清理：确保账号登出'):
                if is_success:
                    logger.info(f'{LogIcon.SETUP} 环境清理：检测到账号处于登录状态，执行强制登出...')
                    msg = self.loginPage.logout_if_logged_in()
                    if self.loginPage.platform == 'android':
                        check.equal(msg, ToastMsg.LOGOUT_SUCCESS, '⚠️ 环境清理失败：退出登录动作未成功！')
                    is_back = self.loginPage.wait_for_login_page()
                    check.is_true(is_back, '❌ 退出登录后未回到登录页')
                    BaseSmokeLogin._has_entered_phone_login = False

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('手机账号记住功能')
    @allure.title('连续登录退出不同账号，验证手机号记住功能-状态：已完成')
    def test_login_remember_account(self):
        users = [
            {'account': self.default_account, 'password': self.default_password},
            {'account': self.secondary_account, 'password': self.secondary_password},
        ]
        for idx, user in enumerate(users, 1):
            account = user['account']
            password = user['password']
            is_success = False
            is_back = False
            try:
                with allure.step(f'账号 {idx} ({account}) - 1. 输入账号密码并勾选协议登录'):
                    self.loginPage.click_password_login_button()
                    self.loginPage.input_account(account)
                    self.loginPage.input_password(password)
                    self.loginPage.click_user_agreement()
                    self.loginPage.click_login_button()
                with allure.step(f'账号 {idx} ({account}) - 2. 验证登录成功'):
                    is_success = self.loginPage.is_login_success()
                    check.is_true(is_success, f'❌ 账号 {account} 登录失败')
            finally:
                if is_success:
                    with allure.step(f'账号 {idx} ({account}) - 3. 退出登录并确认返回登录页'):
                        self.loginPage.logout_if_logged_in(wait_toast=False)
                        is_back = self.loginPage.wait_for_login_page()
                        check.is_true(is_back, f'❌ 账号 {account} 退出登录后未回到登录页')
                        BaseSmokeLogin._has_entered_phone_login = False

            if not is_success or not is_back:
                # 登录失败或未回到登录页时直接终止，避免停留在原表单造成“记住账号”假通过
                break

            with allure.step(f'账号 {idx} ({account}) - 4. 校验输入框中是否自动填充了刚登录的账号'):
                self.loginPage.click_phone_login_button()
                BaseSmokeLogin._has_entered_phone_login = True
                saved_account = (self.loginPage.get_phone_number() or '').strip()
                check.equal(saved_account, account, f'❌ 未能记住上一次登录成功的账号: {account}')
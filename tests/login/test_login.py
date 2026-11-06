import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_yaml_data
from dataclasses import dataclass


def load_login_test_cases():
    """从 YAML 加载并返回用例列表，过滤已标记但不需要加载的字段"""
    try:
        data = load_yaml_data("login/test_login_data.yaml")
        cases = data.get('login_cases', [])
        for item in cases:
            item.pop('priority', None)  # 过滤优先级说明字段
        return cases
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} 加载 YAML 用例失败: {e}")
        return []

@dataclass
class LoginCaseData:
    """登录测试用例数据模型"""
    id: str = "Unknown_ID"
    desc: str = "无描述"
    account: str = ""
    password: str = ""
    check_agreement: bool = True
    eye_click: bool = False
    popup_action: str = ""
    assert_ui_state: str = ""
    expected_status: str = "fail"
    expected_toast: str = ""


@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-账号密码登录")
@allure.story("登录模块全路径功能测试")
class TestLogin:
    """登录模块全路径功能测试"""

    # 标记是否已经进入过手机号登录页面
    _has_entered_phone_login = False

    @pytest.fixture(autouse=True)
    def enter_phone_login_page(self, request, driver_sender):
        """ 智能路由：根据用例标签决定进入哪个页面类级别前置：App 启动后只点一次'手机号登录'进入登录表单"""
        self.loginPage = LoginPage(driver_sender)

        # 获取当前运行的这个具体的测试函数 (node)
        current_test_node = request.node
        
        # 嗅探当前测试函数身上有没有贴 @pytest.mark.no_login_entrance 标签
        is_lo_test = current_test_node.get_closest_marker("no_login_entrance") is not None

        # 智能页面路由 (Smart Routing)
        if not is_lo_test:
            if not TestLogin._has_entered_phone_login:
                logger.info(f"{LogIcon.ACTION} 首次进入手机号表单，执行点击操作。")
                self.loginPage.click_phone_login_button()
                TestLogin._has_entered_phone_login = True # 上锁
            else:
                logger.debug(f"{LogIcon.ACTION} 检测到已经处于手机号表单页，跳过点击，直接开始测试。")
        else:
            logger.info(f"{LogIcon.ACTION} 探测到 @pytest.mark.no_login_entrance 标签，停留在登录首页，不进入手机号表单。")
            
        yield

    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, driver_sender):
        """每条用例运行前的初始化：实例化页面对象"""
        self.loginPage = LoginPage(driver_sender)
        yield



    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.story("手机账号密码登录场景回归验证")
    @allure.title("手机账号密码登录场景回归验证-状态：已完成")
    @pytest.mark.parametrize("case_dict", load_login_test_cases(), ids=lambda x: x.get('id', 'TC'))
    def test_login_scenarios(self, case_dict):
        case = LoginCaseData(**case_dict)

        allure.dynamic.title(f"[{case.id}] 登录场景 - {case.desc}")
        logger.info(f"{LogIcon.ACTION} 开始执行用例: [{case.id}] {case.desc}")

        with allure.step("1. 初始化登录环境并输入数据"):
            self.loginPage.click_password_login_button()
            
            if case.password == "[LONG_STRING_1000]":
                case.password = "A" * 1000
                logger.info(f"{LogIcon.ACTION} 动态生成了 1000 位超长密码测试数据")
                
            self.loginPage.input_account(case.account)
            self.loginPage.input_password(case.password)

        # ========================================================
        # 独立分支：纯 UI 状态验证 (不触发真实登录请求)
        # ========================================================
        if case.assert_ui_state:
            with allure.step(f"2. 校验 UI 交互状态: {case.assert_ui_state}"):
                if case.assert_ui_state == "button_disabled":
                    is_enabled = self.loginPage.is_login_button_enabled()
                    check.is_true(is_enabled, f"❌ 预期登录按钮禁用，但实际可点击")
                    
                elif case.assert_ui_state == "password_masked":
                    pwd_text = self.loginPage.get_password()
                    check.not_equal(pwd_text, case.password, f"❌ 预期密码为掩码，实际暴露明文: {pwd_text}")
                    
                elif case.assert_ui_state == "password_toggle":
                    pwd_before = self.loginPage.get_password()
                    self.loginPage.click_password_visible_btn()
                    pwd_after = self.loginPage.get_password()
                    check.not_equal(pwd_before, pwd_after, f"❌ 点击眼睛后，密码明密文状态未发生反转")
            
            logger.info(f"{LogIcon.FIND} UI 状态验证完毕，提前结束本条用例。")
            return  # 【正常退出】不需要清理登录态，因为根本没点登录

        # ========================================================
        # 核心业务分支：执行登录动作
        # ========================================================
        with allure.step("3. 执行登录与协议处理"):
            if case.eye_click:
                self.loginPage.click_password_visible_btn() # 测试明文模式下发起登录

            if case.check_agreement:
                self.loginPage.click_user_agreement()
                
            self.loginPage.click_login_button()

            # 只有未勾选协议时，才处理弹窗逻辑
            if not case.check_agreement:
                with allure.step(f"3.1 拦截处理：隐私协议弹窗 (动作: {case.popup_action})"):
                    actual_popup_title = self.loginPage.get_agreement_popup_title()
                    check.equal(actual_popup_title, case.expected_toast,
                                f"❌ 预期弹出协议框 '{case.expected_toast}', 实际看到 '{actual_popup_title}'")
                    
                    if case.popup_action == "agree":
                        self.loginPage.click_handle_agreement_popup()
                    elif case.popup_action == "reject":
                        self.loginPage.close_agreement_popup()
                        pwd_element = self.loginPage.get_password_element()
                        check.is_not_none(pwd_element, f"❌ [{case.id}] 拒绝隐私协议后，未发现对应的登录页密码输入框")
                    else:
                        self.loginPage.close_agreement_popup() # 兜底防止弹窗遗留
                        pwd_element = self.loginPage.get_password_element()
                        check.is_not_none(pwd_element, f"❌ [{case.id}] 关闭隐私协议后，未发现对应的登录页密码输入框")

        # ========================================================
        # 结果校验与极其关键的环境保护 (Teardown)
        # ========================================================
        try:
            with allure.step(f"4. 最终业务结果验证 (预期: {case.expected_status})"):
                if case.expected_status == "success":
                    is_success = self.loginPage.is_login_success()
                    check.is_true(is_success, f"❌ 预期登录成功进入主页，但未检测到主页元素")
                    
                elif case.expected_status == "fail":
                    if case.expected_toast and case.check_agreement: 
                        # 注：未勾选协议时 expected_toast 用于验证弹窗title，所以加上 check_agreement 条件区分
                        actual_toast = self.loginPage.get_toast_text(expected_toast=case.expected_toast)
                        check.equal(case.expected_toast, actual_toast,
                                    f"❌ Toast校验失败 | 预期: '{case.expected_toast}', 实际: '{actual_toast}'")

                    is_success = self.loginPage.is_login_success()
                    check.is_false(is_success, f"❌ 预期登录失败，但发生了极其严重的越权：成功进入了主页！")
        finally:
            with allure.step("5. 环境清理：确保账号登出"):
                if self.loginPage.is_login_success():  
                    logger.info(f"{LogIcon.SETUP} 环境清理：检测到账号处于登录状态，执行强制登出...")
                    msg = self.loginPage.logout_if_logged_in()
                    check.equal(msg, ToastMsg.LOGOUT_SUCCESS, f"⚠️ 环境清理失败：退出登录动作未成功！")
                    is_success = self.loginPage.wait_for_login_page()
                    check.is_true(is_success, f"❌ 账号 {case.account} 退出登录失败，未回到登录页")
                

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("登录成功新号，手机账号记住功能")
    @allure.title("连续登录退出不同由于，验证手机号记住功能-状态：已完成")
    def test_login_remember_account(self):
        allure.dynamic.title("连续登录退出不同由于，验证手机号记住功能")
        logger.info(f"{LogIcon.ACTION} 开始执行专属用例: 连续登录不同账号，验证最后一次账号被准确记住")
        
        users = [
            {"account": "38100000225", "password": "a1234567B9"},
            {"account": "38100000224", "password": "a1234567B9"}
        ]
        
        for idx, user in enumerate(users, 1):
            account = user["account"]
            password = user["password"]
            
            with allure.step(f"账号 {idx} ({account}) - 1. 初始化并输入账号密码网络环境"):
                self.loginPage.click_password_login_button()
                self.loginPage.input_account(account)
                self.loginPage.input_password(password)
            
            with allure.step(f"账号 {idx} ({account}) - 2. 同意并登录"):
                self.loginPage.click_user_agreement()
                self.loginPage.click_login_button()
            
            with allure.step(f"账号 {idx} ({account}) - 3. 验证登录状态"):
                is_success = self.loginPage.is_login_success()
                check.is_true(is_success, f"❌ 账号 {account} 预期登录成功进入主页，但未检测到主页元素")
            
            with allure.step(f"账号 {idx} ({account}) - 4. 退出登录并验证状态"):
                msg = self.loginPage.logout_if_logged_in()
                check.equal(msg, ToastMsg.LOGOUT_SUCCESS, f"⚠️ 环境清理失败：退出登录动作未成功！")
                is_success = self.loginPage.wait_for_login_page()
                check.is_true(is_success, f"❌ 账号 {account} 退出登录失败，未回到登录页")
            
            with allure.step(f"账号 {idx} ({account}) - 5. 验证该账号是否被记住"):
                aft_acc = self.loginPage.get_phone_number()
                check.equal(aft_acc, account, f"❌ 预期退出后回显账号为 '{account}'，实际为 '{aft_acc}'")
            
    
    @allure.story("登录次数过多时，操作频繁验证")
    @allure.title("异常行为监控 - 连续多次发起登录请求触发防刷-状态：未完成")
    @pytest.mark.skip
    def test_login_too_frequent(self):
        allure.dynamic.title("异常行为监控 - 连续多次发起登录请求触发防刷")
        logger.info(f"{LogIcon.ACTION} 开始执行专属用例: 操作频繁防刷验证")

        account = "38100000225"
        password = "wrong_password_for_frequent_test"
        
        with allure.step("1. 初始化由于防刷测试环境"):
            self.loginPage.click_password_login_button()
            self.loginPage.input_account(account)
            self.loginPage.input_password(password)
            self.loginPage.click_user_agreement()

        with allure.step("2. 连续短时间内多次提交登录申请"):
            is_frequent_intercepted = False
            
            for i in range(1, 16):
                logger.info(f"{LogIcon.FAIL} ➡️ 发起第 {i} 次错误登录请求")
                self.loginPage.click_login_button()
                
                msg = self.loginPage.get_toast_text()
                
                if "频繁" in msg or "次数过多" in msg:
                    is_frequent_intercepted = True
                    logger.info(f"{LogIcon.SUCCESS} 成功在第 {i} 次触发了频率限制: {msg}")
                    break
            check.is_true(is_frequent_intercepted, f"❌ 连续下发 15 次登录请求，竟然没有触发操作频繁拦截，最后一次Toast为: '{msg}'")
        # 兜底校验
        is_success = self.loginPage.is_login_success()
        check.is_false(is_success, "❌ 预期应该是登录失败被拦截，但检测到了主页！")
    

    


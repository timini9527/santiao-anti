import time
import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data
from dataclasses import dataclass
from utils.cv_recognition.ocr_utils import OcrUtils

def load_verification_login_test_cases():
    """从 YAML 加载并返回验证码登录的用例列表"""
    try:
        data = load_yaml_data("login/test_verification_login_data.yaml")
        cases = data.get('verification_cases', [])
        for item in cases:
            item.pop('priority', None)  # 过滤优先级说明字段
        return cases
    except Exception as e:
        logger.error(f"加载 YAML 用例失败: {e}")
        return []

@dataclass
class VerificationLoginCaseData:
    """验证码登录测试用例数据模型"""
    id: str = "Unknown_ID"
    desc: str = "无描述"
    account: str = ""
    verify_code: str = ""
    check_agreement: bool = True
    trigger_verify: bool = True
    popup_action: str = ""
    expected_status: str = "fail"
    expected_toast: str = ""
    expected_agreement_title: str = ""
    expected_send_toast: str = ""


@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-验证码登录")
@allure.story("每条用例运行前的初始化：实例化页面对象")
class TestVerificationLogin:
    
    # 标记是否已经进入过验证码登录页面
    _has_entered_verification_login = False
    
    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, driver_sender):
        """每条用例运行前的初始化：实例化页面对象"""
        self.loginPage = LoginPage(driver_sender)
        self.ocr_utils = OcrUtils(driver_sender)
        yield

    @pytest.fixture(autouse=True)
    def enter_verification_login_page(self, request, driver_sender):
        """ 智能路由：根据用例标签决定进入哪个页面类级别前置：App 启动后只点一次'手机号登录'进入登录表单"""
        self.loginPage = LoginPage(driver_sender)

        # 获取当前运行的这个具体的测试函数 (node)
        current_test_node = request.node
        
        # 嗅探当前测试函数身上有没有贴 @pytest.mark.no_login_entrance 标签
        is_lo_test = current_test_node.get_closest_marker("no_login_entrance") is not None

        # 智能页面路由 (Smart Routing)
        if not is_lo_test:
            if not TestVerificationLogin._has_entered_verification_login:
                logger.info("🚀 首次进入验证码登录表单，执行点击操作。")
                self.loginPage.click_phone_login_button()
                TestVerificationLogin._has_entered_verification_login = True # 上锁
            else:
                logger.debug("⚡ 检测到已经处于验证码登录表单页，跳过点击，直接开始测试。")
        else:
            logger.info("👉 探测到 @pytest.mark.no_login_entrance 标签，停留在登录首页，不进入手机号表单。")
            
        yield


    @pytest.mark.p0
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.story("验证码登录场景回归验证")
    @allure.title("验证码登录场景-状态：已完成")
    @pytest.mark.parametrize("case_dict", load_verification_login_test_cases(), ids=lambda x: x.get('id', 'TC'))
    def test_verification_login_scenarios(self, case_dict):
        case = VerificationLoginCaseData(**case_dict)

        allure.dynamic.title(f"[{case.id}] 验证码登录场景 - {case.desc}")
        logger.info(f"🚀 开始执行用例: [{case.id}] {case.desc}")

        with allure.step("1. 初始化登录环境并输入验证码和账号"):
            self.loginPage.input_account(case.account)
            
            if case.check_agreement:
                self.loginPage.click_user_agreement()
            else:
                self.loginPage.cancel_user_agreement()
                
            self.loginPage.click_login_button()

        # ========================================================
        # 拦截：未勾选协议的分支
        # ========================================================
        if not case.check_agreement:
            with allure.step(f"1.1 拦截处理：未勾选隐私协议弹窗 (预期标题: '{case.expected_agreement_title}')"):
                actual_popup_title = self.loginPage.get_agreement_popup_title()
                check.equal(actual_popup_title, case.expected_agreement_title,
                            f"❌ 预期弹出协议框标题为 '{case.expected_agreement_title}', 实际看到 '{actual_popup_title}'")

                if case.popup_action == "agree":
                    self.loginPage.click_handle_agreement_popup()
                elif case.popup_action == "reject":
                    self.loginPage.close_agreement_popup()
                    num_title = self.loginPage.get_top_title()
                    check.equal(num_title, "手机号登录", f"❌ 预期停留在登录页，实际非此界面")
                    return
                else:
                    self.loginPage.close_agreement_popup() # 兜底防止弹窗遗留
                    num_title = self.loginPage.get_top_title()
                    check.equal(num_title, "手机号登录", f"❌ 预期停留在登录页，实际非此界面")
                    return

        # ========================================================
        # 拦截：基于规则（如位数不足或为空）不触发后续手机号校验
        # ========================================================
        if not case.trigger_verify:
            with allure.step(f"1.2 预期规则拦截不触发验证 (预期提示: '{case.expected_toast}')"):
                early_toast = self.loginPage.get_toast_text(expected_toast=case.expected_toast)
                check.equal(early_toast, case.expected_toast, f"❌ 预期早期拦截 '{case.expected_toast}', 实际 '{early_toast}'")
                return 
                    
        # ========================================================
        # 业务分支：验证码分发、获取倒计时、最终业务输入
        # ========================================================
        try:
            with allure.step(f"2. 验证人机校验 UI 交互状态 (预期发码状态: '{case.expected_send_toast}')"):
                self.loginPage.click_human_verification_button()
                toast_message = self.loginPage.get_login_toast_message()
                
                if case.expected_send_toast:
                    check.equal(toast_message, case.expected_send_toast, f"❌ 发送验证码状态提示不符: 预期'{case.expected_send_toast}', 实际'{toast_message}'")
                    
                    # ⚠️ 如果业务本身就因如‘手机号错误’等后端拦截了获取验证码动作，就不可能进入倒计时和输入验证码的格子了
                    if case.expected_send_toast != "验证码已发送":
                        logger.info(f"由于获取验证码阶段被业务规则拦截或失败 ('{case.expected_send_toast}')，安全跳出后续倒计时及填验证码流程。")
                        return
            
            with allure.step("3. 验证人机校验 UI 交互状态: 验证码倒计时"):
                countdown_text = self.loginPage.get_verification_code_countdown_text()
                check.is_in('s', countdown_text, f"点击灰色按钮后，未发现正确验证码倒计时特征字符 's': {countdown_text}")  

            with allure.step(f"4. 输入验证码并验证预期结果 (输入:{case.verify_code} / 预期:{case.expected_status})"):
                self.loginPage.input_verify_code_robust(case.verify_code)
                
                if case.expected_status == "fail":
                    verify_code_toast = self.loginPage.get_toast_text()
                    check.equal(verify_code_toast, case.expected_toast, f"❌ 输入验证码后 Toast 提示不符合预期: {verify_code_toast}")
                    
                    is_success = self.loginPage.is_login_success()
                    check.is_false(is_success, f"❌ [危险] 预期登录失败，但发生了极其严重的漏洞：成功进入了主页！")
                    
                # elif case.expected_status == "success":
                #     is_success = self.loginPage.is_login_success()
                #     check.is_true(is_success, f"❌ 预期登录成功进入主页，但未检测到主页特征元素！")

        # ========================================================
        # Teardown 环境清理
        # ========================================================
        finally:
            with allure.step("5. 环境清理：确保账号登出或重置界面栈"):
                if self.loginPage.is_login_success():  
                    logger.info("环境清理：检测到账号处于登录状态，执行强制登出和环境重置...")
                    msg = self.loginPage.logout_if_logged_in()
                    check.equal(msg, '已退出登录', f"⚠️ 环境清理失败：退出登录动作未成功！")
                    
                    # 为了下一条验证码用例回归正常态，需要再切一次验证码模式
                    self.loginPage.click_code_login_button() 
                else:
                    # 对于登录失败（填写错误验证码）的用例，弹窗会停留在四个格子的验证码独立页面中
                    is_in_code_page = self.loginPage.is_on_verification_login_page()
                    if is_in_code_page:
                        logger.info("当前界面遗留在验证码四宫格输入页，执行点击左上角返回至手机号表单...")
                self.loginPage.click_back_btn()

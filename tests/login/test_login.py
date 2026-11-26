import os
import pytest
import allure
import pytest_check as check
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_yaml_data, render_template_data
from dataclasses import dataclass


def _load_login_yaml() -> dict:
    """加载登录 YAML 数据文件（包含顶层 vars 变量区与 login_cases 用例列表）"""
    try:
        return load_yaml_data("login/test_login_data.yaml") or {}
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} 加载 YAML 用例失败: {e}")
        return {}


_LOGIN_YAML_DATA = _load_login_yaml()


def load_login_test_cases() -> list[dict]:
    """返回登录回归参数化用例列表"""
    return _LOGIN_YAML_DATA.get("login_cases", [])


def resolve_app_env(driver: object = None) -> str:
    """
    解析当前被测 App 后端业务环境（test / gray / prod）。
    优先级：环境变量 APP_ENV > devices.yaml 的 app_env > 环境变量 ENV > driver._factory_env > devices.yaml 的 current_env > 'test'
    """
    env_from_os = (os.environ.get("APP_ENV") or "").strip().lower()
    if env_from_os:
        return env_from_os

    try:
        devices_cfg = load_yaml_data("devices.yaml") or {}
    except Exception:
        devices_cfg = {}

    app_env = str(devices_cfg.get("app_env") or "").strip().lower()
    if app_env:
        return app_env

    fallback_env = (
        os.environ.get("ENV")
        or getattr(driver, "_factory_env", None)
        or devices_cfg.get("current_env")
        or "test"
    )
    return str(fallback_env).strip().lower()


def resolve_login_vars(platform: str, app_env: str | None = None, driver: object = None) -> dict[str, str]:
    """
    按「业务环境 (app_env) -> 运行平台 (platform)」两级路由解析 YAML 顶层 vars 变量表，并生成派生变量：
    - 优先级：env_accounts[app_env][platform] > env_accounts[app_env]['default'] > 顶层 vars 默认值；
    - password_swapcase：自动反转当前环境密码大小写，供大小写敏感用例使用；
    - long_string_1000：动态生成 1000 位超长密码测试串。
    """
    raw_vars = _LOGIN_YAML_DATA.get("vars") or {}
    variables: dict[str, str] = {
        key: str(value)
        for key, value in raw_vars.items()
        if not isinstance(value, (dict, list))
    }

    resolved_env = (app_env or resolve_app_env(driver)).strip().lower()
    platform_key = (platform or "").strip().lower()

    env_accounts = raw_vars.get("env_accounts")
    if isinstance(env_accounts, dict):
        env_block = env_accounts.get(resolved_env)
        if isinstance(env_block, dict):
            # 命中指定环境后，严格与该环境隔离，不再误用顶层其他环境的兜底账号
            env_vars: dict[str, str] = {}
            # 1. 先应用当前环境的 default 账号配置
            env_default = env_block.get("default")
            if isinstance(env_default, dict):
                for key, value in env_default.items():
                    if value is not None and str(value).strip():
                        env_vars[key] = str(value)
            # 2. 再应用当前环境下的平台专属账号覆盖（三端防互踢）
            platform_override = env_block.get(platform_key)
            if isinstance(platform_override, dict):
                for key, value in platform_override.items():
                    if value is not None and str(value).strip():
                        env_vars[key] = str(value)
            variables["account"] = env_vars.get("account", "")
            variables["password"] = env_vars.get("password", "")
            variables["secondary_account"] = env_vars.get("secondary_account", "")
            variables["secondary_password"] = env_vars.get("secondary_password", "")
            variables["frequent_account"] = env_vars.get("frequent_account", "")
        else:
            logger.warning(
                f"{LogIcon.WARN} [LoginVars] test_login_data.yaml 未配置环境 '{resolved_env}' 的账号池，回退顶层默认账号"
            )

    # 支持 CI / 正式环境通过环境变量注入账号密码，避免敏感凭证写入仓库
    if os.environ.get("LOGIN_ACCOUNT"):
        variables["account"] = os.environ["LOGIN_ACCOUNT"].strip()
    if os.environ.get("LOGIN_PASSWORD"):
        variables["password"] = os.environ["LOGIN_PASSWORD"]
    if os.environ.get("LOGIN_SECONDARY_ACCOUNT"):
        variables["secondary_account"] = os.environ["LOGIN_SECONDARY_ACCOUNT"].strip()
    if os.environ.get("LOGIN_SECONDARY_PASSWORD"):
        variables["secondary_password"] = os.environ["LOGIN_SECONDARY_PASSWORD"]
    if os.environ.get("LOGIN_FREQUENT_ACCOUNT"):
        variables["frequent_account"] = os.environ["LOGIN_FREQUENT_ACCOUNT"].strip()

    if not variables.get("account") or not variables.get("password"):
        raise ValueError(
            f"环境 '{resolved_env}'（平台: {platform_key}）未配置有效测试账号或密码，"
            f"请在 data/login/test_login_data.yaml 的 vars.env_accounts.{resolved_env} 中填写，"
            f"或通过环境变量 LOGIN_ACCOUNT / LOGIN_PASSWORD 注入。"
        )

    password = variables.get("password", "")
    variables["app_env"] = resolved_env
    variables.setdefault("password_swapcase", password.swapcase())
    variables.setdefault("long_string_1000", "A" * 1000)
    return variables

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
    priority: str = "P1"


_PRIORITY_SEVERITY_MAP = {
    "P0": allure.severity_level.BLOCKER,
    "P1": allure.severity_level.CRITICAL,
    "P2": allure.severity_level.NORMAL,
}



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

    @pytest.mark.p0
    @allure.story("手机账号密码登录场景回归验证")
    @allure.title("手机账号密码登录场景回归验证-状态：已完成")
    @pytest.mark.parametrize("case_dict", load_login_test_cases(), ids=lambda x: x.get('id', 'TC'))
    def test_login_scenarios(self, case_dict):
        platform_key = (self.loginPage.platform or "").strip().lower()
        login_vars = resolve_login_vars(platform_key, driver=self.loginPage.driver)
        rendered_case = render_template_data(case_dict, login_vars)
        # 按当前设备平台合并差异化预期配置（如 G3_TC04 在 iOS 允许超长输入导致后端拦截失败）
        platform_overrides = rendered_case.pop("platform_overrides", None)
        if isinstance(platform_overrides, dict):
            override = platform_overrides.get(platform_key)
            if isinstance(override, dict):
                rendered_case.update(override)
        case = LoginCaseData(**rendered_case)

        allure.dynamic.title(f"[{case.id}] 登录场景 - {case.desc}")
        allure.dynamic.severity(
            _PRIORITY_SEVERITY_MAP.get(case.priority.upper(), allure.severity_level.NORMAL)
        )
        logger.info(
            f"{LogIcon.ACTION} 开始执行用例: [{case.id}] {case.desc} "
            f"(环境: {login_vars['app_env']} | 平台: {self.loginPage.platform})"
        )

        with allure.step("1. 初始化登录环境并输入数据"):
            self.loginPage.click_password_login_button()
            self.loginPage.input_account(case.account)
            self.loginPage.input_password(case.password)

        # ========================================================
        # 独立分支：纯 UI 状态验证 (不触发真实登录请求)
        # ========================================================
        if case.assert_ui_state:
            with allure.step(f"2. 校验 UI 交互状态: {case.assert_ui_state}"):
                if case.assert_ui_state == "button_disabled":
                    is_gray = self.loginPage.is_login_button_gray()
                    check.is_true(is_gray, "❌ 预期登录按钮置灰（未激活），但视觉校验为高亮激活状态")

                elif case.assert_ui_state == "password_masked":
                    pwd_text = self.loginPage.get_password()
                    check.not_equal(pwd_text, case.password, f"❌ 预期密码为掩码，实际暴露明文: {pwd_text}")

                elif case.assert_ui_state == "password_toggle":
                    pwd_before = self.loginPage.get_password()
                    self.loginPage.click_password_visible_btn()
                    pwd_after = self.loginPage.get_password()
                    check.not_equal(pwd_before, pwd_after, "❌ 首次点击眼睛后，密码明密文状态未发生反转")
                    # 再次点击验证双向切换并恢复默认密文状态，避免污染后续用例
                    self.loginPage.click_password_visible_btn()
                    pwd_restored = self.loginPage.get_password()
                    check.equal(pwd_restored, pwd_before, "❌ 再次点击眼睛后，密码未恢复为初始密文状态")

            logger.info(f"{LogIcon.FIND} UI 状态验证完毕，提前结束本条用例。")
            return

        # ========================================================
        # 核心业务分支：执行登录动作
        # ========================================================
        with allure.step("3. 执行登录与协议处理"):
            if case.eye_click:
                self.loginPage.click_password_visible_btn()

            if case.check_agreement:
                self.loginPage.click_user_agreement()
            else:
                self.loginPage.cancel_user_agreement()

            auto_dismiss_save_pwd = case.expected_status == "success" and case.check_agreement
            self.loginPage.click_login_button(auto_dismiss_save_pwd=auto_dismiss_save_pwd)

            if not case.check_agreement:
                with allure.step(f"3.1 拦截处理：隐私协议弹窗 (动作: {case.popup_action or 'close'})"):
                    actual_popup_title = self.loginPage.get_agreement_popup_title()
                    check.equal(
                        actual_popup_title,
                        case.expected_toast,
                        f"❌ 预期弹出协议框 '{case.expected_toast}', 实际看到 '{actual_popup_title}'",
                    )

                    if case.popup_action == "agree":
                        self.loginPage.click_handle_agreement_popup()
                    else:
                        self.loginPage.close_agreement_popup()
                        check.is_true(
                            self.loginPage.is_on_phone_login_page(),
                            f"❌ [{case.id}] 拒绝/关闭隐私协议弹窗后，未停留在账号密码登录页",
                        )

        # ========================================================
        # 结果校验与环境保护 (Teardown)
        # ========================================================
        is_success = False
        try:
            with allure.step(f"4. 最终业务结果验证 (预期: {case.expected_status})"):
                if case.expected_status == "success":
                    is_success = self.loginPage.is_login_success()
                    check.is_true(is_success, "❌ 预期登录成功进入主页，但未检测到主页元素")

                elif case.expected_status == "fail":
                    # 仅 Android 端存在业务 Toast 校验；未勾选协议时 expected_toast 用于校验弹窗标题
                    if (
                        self.loginPage.platform == "android"
                        and case.expected_toast
                        and case.check_agreement
                    ):
                        actual_toast = self.loginPage.get_toast_text(expected_toast=case.expected_toast)
                        check.equal(
                            case.expected_toast,
                            actual_toast,
                            f"❌ Toast校验失败 | 预期: '{case.expected_toast}', 实际: '{actual_toast}'",
                        )

                    is_success = self.loginPage.is_login_success()
                    check.is_false(is_success, "❌ 预期登录失败，但发生了越权：成功进入了主页！")
        finally:
            with allure.step("5. 环境清理：确保账号登出"):
                if is_success:
                    logger.info(f"{LogIcon.SETUP} 环境清理：检测到账号处于登录状态，执行强制登出...")
                    msg = self.loginPage.logout_if_logged_in()
                    if self.loginPage.platform == "android":
                        check.equal(msg, ToastMsg.LOGOUT_SUCCESS, "⚠️ 环境清理失败：退出登录动作未成功！")
                    is_back = self.loginPage.wait_for_login_page()
                    check.is_true(is_back, f"❌ 账号 {case.account} 退出登录失败，未回到登录页")
                    # 鸿蒙/iOS 登出后回到登录入口主页，重置标记确保下一条参数化用例正常重新进入手机号表单
                    TestLogin._has_entered_phone_login = False
                

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("登录成功新号，手机账号记住功能")
    @allure.title("连续登录退出不同账号，验证手机号记住功能-状态：已完成")
    def test_login_remember_account(self):
        login_vars = resolve_login_vars(self.loginPage.platform, driver=self.loginPage.driver)
        secondary_account = login_vars.get("secondary_account", "")
        secondary_password = login_vars.get("secondary_password", "")
        if not secondary_account or not secondary_password:
            raise ValueError(
                f"环境 '{login_vars['app_env']}'（平台: {self.loginPage.platform}）未配置副账号，"
                f"请在 data/login/test_login_data.yaml 的 vars.env_accounts.{login_vars['app_env']} "
                f"中补充 secondary_account / secondary_password。"
            )

        logger.info(
            f"{LogIcon.ACTION} 开始执行专属用例: 连续登录不同账号，验证最后一次账号被准确记住 "
            f"(环境: {login_vars['app_env']} | 平台: {self.loginPage.platform})"
        )

        users = [
            {"account": login_vars["account"], "password": login_vars["password"]},
            {"account": secondary_account, "password": secondary_password},
        ]

        for idx, user in enumerate(users, 1):
            account = user["account"]
            password = user["password"]
            is_success = False
            is_back = False

            try:
                with allure.step(f"账号 {idx} ({account}) - 1. 初始化并输入账号密码"):
                    self.loginPage.click_password_login_button()
                    self.loginPage.input_account(account)
                    self.loginPage.input_password(password)

                with allure.step(f"账号 {idx} ({account}) - 2. 同意并登录"):
                    self.loginPage.click_user_agreement()
                    self.loginPage.click_login_button()

                with allure.step(f"账号 {idx} ({account}) - 3. 验证登录状态"):
                    is_success = self.loginPage.is_login_success()
                    check.is_true(is_success, f"❌ 账号 {account} 预期登录成功进入主页，但未检测到主页元素")
            finally:
                if is_success:
                    with allure.step(f"账号 {idx} ({account}) - 4. 退出登录并确认返回登录页"):
                        msg = self.loginPage.logout_if_logged_in()
                        if self.loginPage.platform == "android":
                            check.equal(msg, ToastMsg.LOGOUT_SUCCESS, "⚠️ 环境清理失败：退出登录动作未成功！")
                        is_back = self.loginPage.wait_for_login_page()
                        check.is_true(is_back, f"❌ 账号 {account} 退出登录失败，未回到登录页")
                        # 鸿蒙/iOS 登出后回到登录入口主页，重置标记确保重新进入手机号表单
                        TestLogin._has_entered_phone_login = False

            if not is_success or not is_back:
                # 登录失败或未返回登录页时直接终止，避免停留在原表单造成“记住账号”假通过
                break

            with allure.step(f"账号 {idx} ({account}) - 5. 重新进入表单并验证该账号是否被记住"):
                self.loginPage.click_phone_login_button()
                TestLogin._has_entered_phone_login = True
                aft_acc = (self.loginPage.get_phone_number() or "").strip()
                check.equal(aft_acc, account, f"❌ 预期退出后回显账号为 '{account}'，实际为 '{aft_acc}'")
            
    # TODO：
    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @allure.story("登录次数过多时，操作频繁验证")
    @allure.title("异常行为监控 - 连续多次发起登录请求触发防刷-状态：未完成")
    # @pytest.mark.skip(reason="需配置独立防刷专用账号 (frequent_account) 且仅在非正式环境按需执行，避免锁死主回归账号")
    def test_login_too_frequent(self):
        login_vars = resolve_login_vars(self.loginPage.platform, driver=self.loginPage.driver)
        if login_vars["app_env"] != "prod":
            pytest.skip("正式环境禁止执行高频错误登录防刷用例")

        account = login_vars.get("frequent_account", "")
        if not account:
            pytest.skip(
                f"环境 '{login_vars['app_env']}'（平台: {self.loginPage.platform}）未配置独立防刷账号 frequent_account，"
                f"跳过执行以避免锁死主回归账号"
            )

        password = "wrong_password_for_frequent_test"
        logger.info(
            f"{LogIcon.ACTION} 开始执行专属用例: 操作频繁防刷验证 "
            f"(环境: {login_vars['app_env']} | 平台: {self.loginPage.platform} | 专用账号: {account})"
        )

        with allure.step("1. 初始化防刷测试环境"):
            self.loginPage.click_password_login_button()
            self.loginPage.input_account(account)
            self.loginPage.input_password(password)
            self.loginPage.click_user_agreement()

        with allure.step("2. 连续短时间内多次提交错误登录请求"):
            is_frequent_intercepted = False
            msg = ""

            for i in range(1, 16):
                logger.info(f"{LogIcon.ACTION} ➡️ 发起第 {i} 次错误登录请求")
                # 禁用 2s 保存密码弹窗探测，保证高频点击节奏且不错过短时 Toast
                self.loginPage.click_login_button(auto_dismiss_save_pwd=False)
                msg = self.loginPage.get_toast_text(timeout=1.5)

                if "频繁" in msg or "次数过多" in msg:
                    is_frequent_intercepted = True
                    logger.info(f"{LogIcon.SUCCESS} 成功在第 {i} 次触发频率限制: {msg}")
                    break

            check.is_true(
                is_frequent_intercepted,
                f"❌ 连续下发 15 次登录请求，未触发操作频繁拦截，最后一次 Toast 为: '{msg}'",
            )

        with allure.step("3. 兜底校验：确认未被放行进入主页"):
            is_success = self.loginPage.is_login_success()
            check.is_false(is_success, "❌ 预期登录失败被拦截，但检测到了主页元素！")
    

    


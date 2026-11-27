import os
import pytest
import allure
import pytest_check as check
from dataclasses import dataclass
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from utils.account_pool import VerificationAccountPool, is_rate_limit_toast
from utils.file_reader.data_loader import load_yaml_data, render_template_data


def _load_verification_yaml() -> dict:
    """加载验证码登录 YAML 数据文件（含顶层 vars 变量区与 verification_cases 用例列表）"""
    try:
        return load_yaml_data("login/test_verification_login_data.yaml") or {}
    except Exception as e:
        logger.error(f"{LogIcon.FAIL} 加载验证码登录 YAML 用例失败: {e}")
        return {}


_VERIFICATION_YAML_DATA = _load_verification_yaml()


def load_verification_login_test_cases() -> list[dict]:
    """返回验证码登录参数化用例列表"""
    return _VERIFICATION_YAML_DATA.get("verification_cases", [])


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


def resolve_verification_vars(
    platform: str,
    app_env: str | None = None,
    driver: object = None,
    use_account_pool: bool = False,
) -> dict[str, str]:
    """
    按「业务环境 (app_env) -> 运行平台 (platform)」两级路由解析验证码登录变量表：
    - gray / test 默认提供万能验证码 9999；
    - prod（正式环境）严禁使用万能验证码，强制保持 verify_code 为空；
    - 当 use_account_pool=True 且当前环境/平台配置了 account_pool（且未通过 LOGIN_ACCOUNT 强行固定账号）时，
      自动从三端隔离的持久化号池轮转取号，避免单号重复发码触发「触发天极流控 / 触发小时级流控」。
    """
    raw_vars = _VERIFICATION_YAML_DATA.get("vars") or {}
    variables: dict[str, str] = {
        key: str(value)
        for key, value in raw_vars.items()
        if not isinstance(value, (dict, list))
    }

    resolved_env = (app_env or resolve_app_env(driver)).strip().lower()
    platform_key = (platform or "").strip().lower()
    pool_cfg: dict | None = None

    env_accounts = raw_vars.get("env_accounts")
    if isinstance(env_accounts, dict):
        env_block = env_accounts.get(resolved_env)
        if isinstance(env_block, dict):
            env_vars: dict[str, str] = {}
            env_default = env_block.get("default")
            if isinstance(env_default, dict):
                for key, value in env_default.items():
                    if key == "account_pool" and isinstance(value, dict):
                        pool_cfg = value
                    elif value is not None and not isinstance(value, (dict, list)) and str(value).strip():
                        env_vars[key] = str(value)
            platform_override = env_block.get(platform_key)
            if isinstance(platform_override, dict):
                for key, value in platform_override.items():
                    if key == "account_pool" and isinstance(value, dict):
                        pool_cfg = value
                    elif value is not None and not isinstance(value, (dict, list)) and str(value).strip():
                        env_vars[key] = str(value)
            variables["account"] = env_vars.get("account", "")
            variables["verify_code"] = env_vars.get("verify_code", "")
        else:
            logger.warning(
                f"{LogIcon.WARN} [VerifyVars] test_verification_login_data.yaml 未配置环境 '{resolved_env}' 的账号池，回退顶层默认变量"
            )

    explicit_account = (os.environ.get("LOGIN_ACCOUNT") or "").strip()
    if explicit_account:
        variables["account"] = explicit_account
    elif (
        use_account_pool
        and resolved_env != "prod"
        and isinstance(pool_cfg, dict)
        and pool_cfg.get("prefix")
        and pool_cfg.get("start") is not None
        and pool_cfg.get("end") is not None
    ):
        variables["account"] = VerificationAccountPool.acquire(
            app_env=resolved_env,
            platform=platform_key or "default",
            prefix=str(pool_cfg["prefix"]),
            start=int(pool_cfg["start"]),
            end=int(pool_cfg["end"]),
            width=int(pool_cfg.get("width", 4)),
        )

    # 正式环境严禁使用万能验证码
    if resolved_env == "prod":
        variables["verify_code"] = ""

    if not variables.get("account"):
        raise ValueError(
            f"环境 '{resolved_env}'（平台: {platform_key}）未配置验证码登录测试账号，"
            f"请在 data/login/test_verification_login_data.yaml 的 vars.env_accounts.{resolved_env} 中填写。"
        )

    variables["app_env"] = resolved_env
    return variables


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
    priority: str = "P1"


_PRIORITY_SEVERITY_MAP = {
    "P0": allure.severity_level.BLOCKER,
    "P1": allure.severity_level.CRITICAL,
    "P2": allure.severity_level.NORMAL,
}


@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-验证码登录")
@allure.story("验证码登录全路径功能测试")
class TestVerificationLogin:
    """验证码登录全路径功能测试"""

    # 标记是否已经进入过手机号/验证码登录表单页
    _has_entered_verification_login = False

    @pytest.fixture(autouse=True)
    def enter_verification_login_page(self, request, driver_sender):
        """智能路由：初始化页面对象，并根据用例标签决定是否首次点击进入手机号登录表单"""
        self.loginPage = LoginPage(driver_sender)

        current_test_node = request.node
        is_lo_test = current_test_node.get_closest_marker("no_login_entrance") is not None

        if not is_lo_test:
            if not TestVerificationLogin._has_entered_verification_login:
                logger.info(f"{LogIcon.ACTION} 首次进入验证码登录表单，执行点击操作。")
                self.loginPage.click_phone_login_button()
                TestVerificationLogin._has_entered_verification_login = True
            else:
                logger.debug(f"{LogIcon.ACTION} 检测到已经处于验证码登录表单页，跳过点击，直接开始测试。")
        else:
            logger.info(f"{LogIcon.ACTION} 探测到 @pytest.mark.no_login_entrance 标签，停留在登录首页，不进入手机号表单。")

        yield

    @pytest.mark.p0
    @allure.story("验证码登录场景回归验证")
    @allure.title("验证码登录场景-状态：已完成")
    @pytest.mark.parametrize("case_dict", load_verification_login_test_cases(), ids=lambda x: x.get("id", "TC"))
    def test_verification_login_scenarios(self, case_dict):
        platform_key = (self.loginPage.platform or "").strip().lower()

        # 先按当前设备平台合并差异化预期配置（如 V3_TC04 在 iOS 允许超长输入导致后端拦截，不真实发码）
        effective_case_dict = dict(case_dict)
        platform_overrides = effective_case_dict.pop("platform_overrides", None)
        if isinstance(platform_overrides, dict):
            override = platform_overrides.get(platform_key)
            if isinstance(override, dict):
                effective_case_dict.update(override)

        # 仅当本用例会向 ${account} 真实发码时才向号池轮转取新号，不浪费池额度
        raw_account_tpl = str(effective_case_dict.get("account", ""))
        will_send_real_sms = (
            "${account}" in raw_account_tpl
            and bool(effective_case_dict.get("trigger_verify", True))
            and (
                bool(effective_case_dict.get("check_agreement", True))
                or str(effective_case_dict.get("popup_action", "")) == "agree"
            )
            and str(effective_case_dict.get("expected_send_toast", "")) == ToastMsg.VERIFY_CODE_SENT
        )

        verify_vars = resolve_verification_vars(
            platform_key,
            driver=self.loginPage.driver,
            use_account_pool=will_send_real_sms,
        )
        rendered_case = render_template_data(effective_case_dict, verify_vars)
        case = VerificationLoginCaseData(**rendered_case)

        allure.dynamic.title(f"[{case.id}] 验证码登录场景 - {case.desc}")
        allure.dynamic.severity(
            _PRIORITY_SEVERITY_MAP.get(case.priority.upper(), allure.severity_level.NORMAL)
        )

        if case.expected_status == "success" and (verify_vars["app_env"] == "prod" or not case.verify_code):
            pytest.skip(f"环境 '{verify_vars['app_env']}' 不支持万能验证码，跳过成功登录用例 [{case.id}]")

        logger.info(
            f"{LogIcon.ACTION} 开始执行用例: [{case.id}] {case.desc} "
            f"(环境: {verify_vars['app_env']} | 平台: {platform_key} | 账号: {case.account})"
        )

        with allure.step("1. 切换至短信验证码登录模式并输入手机号"):
            self.loginPage.click_code_login_button()
            self.loginPage.input_account(case.account)

            if case.check_agreement:
                self.loginPage.click_user_agreement()
            else:
                self.loginPage.cancel_user_agreement()

            self.loginPage.click_login_button(auto_dismiss_save_pwd=False)

        if not case.check_agreement:
            with allure.step(f"1.1 拦截处理：未勾选隐私协议弹窗 (预期标题: '{case.expected_agreement_title}')"):
                actual_popup_title = self.loginPage.get_agreement_popup_title()
                check.equal(
                    actual_popup_title,
                    case.expected_agreement_title,
                    f"❌ 预期弹出协议框标题为 '{case.expected_agreement_title}', 实际看到 '{actual_popup_title}'",
                )

                if case.popup_action == "agree":
                    self.loginPage.click_handle_agreement_popup()
                else:
                    self.loginPage.close_agreement_popup()
                    check.is_true(
                        self.loginPage.is_on_phone_login_page(),
                        f"❌ [{case.id}] 拒绝/关闭隐私协议弹窗后，未停留在手机号登录表单页",
                    )
                    return

        # ========================================================
        # 拦截：基于前端规则（如位数不足或为空）不触发人机校验
        # ========================================================
        if not case.trigger_verify:
            with allure.step(f"1.2 预期前端规则拦截不触发校验 (预期提示: '{case.expected_toast}')"):
                if platform_key in ("android", "harmonyos") and case.expected_toast:
                    early_toast = self.loginPage.get_toast_text(expected_toast=case.expected_toast)
                    check.equal(
                        early_toast,
                        case.expected_toast,
                        f"❌ 预期早期拦截 Toast '{case.expected_toast}', 实际 '{early_toast}'",
                    )
                check.is_true(
                    self.loginPage.is_on_phone_login_page(),
                    f"❌ [{case.id}] 预期被前端规则拦截留在登录表单页，但当前已离开表单页",
                )
                return

        is_success = False
        entered_code_page = False
        try:
            with allure.step(f"2. 完成人机校验并校验发码结果 (预期发码状态: '{case.expected_send_toast}')"):
                self.loginPage.click_human_verification_button()
                if platform_key in ("android", "harmonyos") and case.expected_send_toast:
                    if platform_key == "harmonyos":
                        # 鸿蒙端走原生精确文本 + 流控关键字直查捕获短时发码 Toast，避免误抓静态副标题
                        toast_message = self.loginPage.get_toast_text(
                            timeout=3.0,
                            expected_toast=case.expected_send_toast,
                            detect_rate_limit=(case.expected_send_toast == ToastMsg.VERIFY_CODE_SENT),
                        )
                    else:
                        toast_message = self.loginPage.get_login_toast_message()

                    # 若命中「触发天极流控 / 触发小时级流控」，立即将该号加入当日号池熔断列表并快速失败，
                    # 避免鸿蒙端被拦截在表单页后在倒计时步骤空等超时，且重跑时会自动分配新号
                    if is_rate_limit_toast(toast_message):
                        VerificationAccountPool.mark_rate_limited(
                            app_env=verify_vars["app_env"],
                            platform=platform_key,
                            account=verify_vars["account"],
                            reason=toast_message,
                        )
                        pytest.fail(
                            f"❌ [{case.id}] 账号 {verify_vars['account']} 触发短信流控 ('{toast_message}')，"
                            f"已加入今日号池熔断列表（重跑将自动分配下一个可用账号）"
                        )

                    check.equal(
                        toast_message,
                        case.expected_send_toast,
                        f"❌ 发送验证码状态提示不符: 预期 '{case.expected_send_toast}', 实际 '{toast_message}'",
                    )

                # 若发码阶段预期被业务规则拦截（如手机号不合法），则不会进入验证码四宫格页面
                if case.expected_send_toast and case.expected_send_toast != ToastMsg.VERIFY_CODE_SENT:
                    is_in_code_page = self.loginPage.is_on_verification_login_page(timeout=1)
                    check.is_false(
                        is_in_code_page,
                        f"❌ [{case.id}] 预期发码阶段被拦截 ('{case.expected_send_toast}')，却意外进入了验证码输入页",
                    )
                    logger.info(
                        f"{LogIcon.SUCCESS} 发码阶段已按预期拦截 ('{case.expected_send_toast}')，结束后续流程。"
                    )
                    return

            with allure.step("3. 校验进入验证码输入页与倒计时状态"):
                countdown_text = self.loginPage.get_verification_code_countdown_text()
                entered_code_page = True
                check.is_in("s", countdown_text, f"❌ 未发现验证码倒计时特征字符 's': '{countdown_text}'")

            with allure.step(f"4. 输入验证码并验证预期结果 (输入: '{case.verify_code}' / 预期: {case.expected_status})"):
                if case.verify_code:
                    self.loginPage.input_verify_code_robust(case.verify_code)

                if case.expected_status == "success":
                    is_success = self.loginPage.is_login_success()
                    check.is_true(is_success, "❌ 预期验证码登录成功进入主页，但未检测到主页特征元素！")
                elif case.expected_status == "fail":
                    if case.expected_toast:
                        verify_code_toast = self.loginPage.get_toast_text(expected_toast=case.expected_toast)
                        check.equal(
                            verify_code_toast,
                            case.expected_toast,
                            f"❌ 输入验证码后 Toast 不符 | 预期: '{case.expected_toast}', 实际: '{verify_code_toast}'",
                        )

                    is_success = self.loginPage.is_login_success()
                    check.is_false(is_success, "❌ [危险] 预期登录失败，但发生了越权：成功进入了主页！")

        finally:
            with allure.step("5. 环境清理：确保账号登出或从验证码页安全复位"):
                if is_success:
                    logger.info(f"{LogIcon.SETUP} 环境清理：检测到账号处于登录状态，执行强制登出...")
                    msg = self.loginPage.logout_if_logged_in()
                    if platform_key == "android":
                        check.equal(msg, ToastMsg.LOGOUT_SUCCESS, "⚠️ 环境清理失败：退出登录动作未成功！")
                    is_back = self.loginPage.wait_for_login_page()
                    check.is_true(is_back, f"❌ 账号 {case.account} 退出登录失败，未回到登录页")
                    # 鸿蒙/iOS 登出后回到登录入口主页，重置标记确保下一条用例正常重新进入手机号表单
                    TestVerificationLogin._has_entered_verification_login = False
                elif entered_code_page or self.loginPage.is_on_verification_login_page(timeout=1):
                    logger.info(f"{LogIcon.FIND} 当前停留在验证码四宫格输入页，点击左上角返回至手机号表单...")
                    self.loginPage.click_back_btn()

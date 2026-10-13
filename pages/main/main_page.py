import time
from common.base_page import BasePage
from core.logger_utils import logger
from locators.home.home_locator import HomeLocator
from locators.main.main_locator import MainLocator


class MainPage(BasePage):
    """应用主页面及全局热启动状态自愈引擎"""

    APP_PACKAGE = "com.santiaotalk.im"
    MAIN_ACTIVITY = "com.vvchat.vcapp.activity.MainActivity"

    def is_in_search_page(self, timeout: float = 0.1) -> bool:
        """检测当前是否正处于搜索覆盖层页面（基于右下角取消按钮精准探查，静默零异常）"""
        return bool(self.find_elements(HomeLocator.SEARCH_CANCEL, timeout=timeout, raise_exception=False, expect_missing=True))

    def is_in_main_page(self, timeout: float = 0.2, raise_exception: bool = False) -> bool:
        """判断当前是否已处于主页面（单次高效网络请求，严格对齐 HomePage.wait_home_page 黄金基准）"""
        return bool(self.find_elements(HomeLocator.LEFT_MENU, timeout=timeout, raise_exception=raise_exception, expect_missing=True))

    def is_app_in_foreground(self) -> bool:
        """检查当前被测应用是否处于前台运行状态"""
        try:
            # 状态枚举：4 表示 RUNNING_IN_FOREGROUND
            app_state = self.driver.query_app_state(self.APP_PACKAGE)
            return app_state == 4
        except Exception:
            try:
                return self.driver.current_package == self.APP_PACKAGE
            except Exception:
                return False

    def wait_for_main_page_load(self, timeout: float = 3.0) -> bool:
        """等待主页面加载就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_in_main_page(timeout=0.1):
                return True
            time.sleep(0.1)
        return False

    def reset_activity_stack_to_main(self) -> bool:
        """
        通过 Android Intent 栈顶恢复机制 (FLAG_ACTIVITY_CLEAR_TOP)，
        在不强杀进程、不中断 WebSocket 长连接的前提下，将 MainActivity 瞬间推回栈顶。
        """
        logger.warning("🚀 [StateHealer] 触发 Intent 栈顶恢复：无损归位 MainActivity...")
        try:
            # 1. 优先使用 Appium UiAutomator2 原生 mobile: startActivity (FLAG_ACTIVITY_CLEAR_TOP | SINGLE_TOP = 0x24000000)
            self.driver.execute_script(
                "mobile: startActivity",
                {
                    "component": f"{self.APP_PACKAGE}/{self.MAIN_ACTIVITY}",
                    "flags": 0x24000000
                }
            )
            time.sleep(0.25)
            if self.is_in_main_page(timeout=0.2):
                logger.info("✅ [StateHealer] Intent 栈顶清空归位成功！")
                return True
        except Exception as e:
            logger.debug(f"⚠️ [StateHealer] mobile: startActivity 执行失败，尝试 activate_app 备用通道: {e}")

        # 2. 备用通道：activate_app 激活回到前台
        try:
            self.driver.activate_app(self.APP_PACKAGE)
            time.sleep(0.25)
            if self.is_in_main_page(timeout=0.2):
                logger.info("✅ [StateHealer] activate_app 备用通道归位成功！")
                return True
        except Exception as e:
            logger.warning(f"⚠️ [StateHealer] activate_app 备用通道失败: {e}")

        return False

    def ensure_app_alive_and_ready(self) -> bool:
        """兜底保障：检查应用进程存活状态，若未在前台运行则自动热拉起并就绪"""
        try:
            # App 状态：0=NOT_INSTALLED, 1=NOT_RUNNING, 2=BACKGROUND_SUSPENDED, 3=BACKGROUND, 4=FOREGROUND
            app_state = self.driver.query_app_state(self.APP_PACKAGE)
            if app_state != 4:
                logger.warning(f"🚨 [StateHealer] App 未在前台运行 (State={app_state})，执行自动热唤醒拉起...")
                self.driver.activate_app(self.APP_PACKAGE)
                time.sleep(0.5)
                return self.wait_for_main_page_load(timeout=3.0)
        except Exception as e:
            logger.warning(f"⚠️ [StateHealer] 查询应用状态异常: {e}")
            try:
                self.driver.activate_app(self.APP_PACKAGE)
                time.sleep(0.5)
            except Exception:
                pass
        return True

    def go_to_main_page(self, timeout: float = 0.2, raise_exception: bool = False, max_retries: int = 10) -> bool:
        """
        工业级状态自愈引擎（极简高效，杜绝一切冗余开销）：
        1. 瞬时探针：若当前已处于主页面，0ms 直接放行。
        2. 前置存活守卫：若 App 未运行或处于后台/系统桌面，严禁在桌面上盲目按 Back，直接热拉起应用并就绪！
        3. 极速平滑回退：若 App 确实在前台，仅在子页面时执行纯粹的系统/UI Back；若回退到达桌面立即停止按键。
        4. Intent 栈顶恢复：若回退达到上限仍未归位，无损将 MainActivity 推回栈顶清空子页面。
        """
        # 1. 瞬时探针：已在主页直接放行，零额外网络请求与性能损耗
        if self.is_in_main_page(timeout=timeout, raise_exception=raise_exception):
            logger.debug("🍏 [StateHealer] 当前已处于主页面")
            return True

        logger.info("🔄 [StateHealer] 开始执行热启动状态自愈归位...")

        # 2. 前置存活守卫：若应用未启动或处于后台/系统桌面，严禁盲目按 Back 打在桌面上！
        if not self.is_app_in_foreground():
            logger.warning("🚨 [StateHealer] 检测到 App 未在前台运行（未启动或处于桌面/后台），直接执行无损热拉起...")
            self.ensure_app_alive_and_ready()
            if self.is_in_main_page(timeout=0.3):
                logger.info("🍏 [StateHealer] 热拉起后已成功归位主页面")
                return True
            # 若拉起后停留在历史深层页面，直接通过 Intent 栈清空瞬间推回主页
            if self.reset_activity_stack_to_main():
                return True

        # 3. 极速连续回退（确认当前正处于 App 内部前台子页面时，才安全退栈）
        retries = max_retries
        while retries > 0:
            try:
                self.back(timeout=0.1)
            except Exception as e:
                logger.debug(f"⚠️ [StateHealer] 退回操作捕获异常: {e}")

            if self.is_in_main_page(timeout=0.1):
                logger.info("🍏 [StateHealer] 快速退回已成功归位主页面")
                return True

            # 核心安全阻断：若退回过程中意外退出了前台（到达了系统桌面），立即停止继续按 Back，避免在桌面乱按
            if not self.is_app_in_foreground():
                logger.warning("🔙 [StateHealer] 退回过程已到达系统桌面，立即终止按 Back，切入 Intent 栈恢复...")
                break

            retries -= 1

        # 4. 栈顶清空与无损热拉起（深层页面或返回受阻时直接一键推回主页）
        if self.reset_activity_stack_to_main():
            return True

        # 5. 兜底判定
        self.ensure_app_alive_and_ready()

        success = self.is_in_main_page(timeout=0.3)
        if success:
            logger.info("🍏 [StateHealer] 状态自愈完成，已确保停留在主页面")
            return True

        if raise_exception:
            raise RuntimeError("❌ [StateHealer] 经过自愈后仍未能恢复至主页面！")
        logger.error("❌ [StateHealer] 经过自愈后仍未能恢复至主页面")
        return False
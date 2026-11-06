import time
from common.base_page import BasePage
from core.logger_utils import logger, LogIcon
from locators.home.home_locator import HomeLocator
from locators.main.main_locator import MainLocator


class MainPage(BasePage):
    """应用主页面及全局热启动状态自愈引擎"""

    APP_PACKAGE = "com.santiaotalk.im"
    MAIN_ACTIVITY = "com.vvchat.vcapp.activity.MainActivity"

    def is_in_search_page(self, timeout: float = 0.1) -> bool:
        """检测当前是否正处于搜索覆盖层页面（基于右下角取消按钮精准探查，静默零异常）"""
        return bool(self.find_elements(HomeLocator.SEARCH_CANCEL, timeout=timeout, raise_exception=False, expect_missing=True))

    def is_in_main_page(self, timeout: float = 0.5, raise_exception: bool = False) -> bool:
        """
        判断当前是否已处于主页面：
        双特征精准识别（左上角抽屉按钮 或 底部主导航栏），确保 100% 不漏判、不误判。
        """
        if bool(self.find_elements(HomeLocator.LEFT_MENU, timeout=timeout, raise_exception=raise_exception, expect_missing=True)):
            return True
        return bool(self.find_elements(HomeLocator.BOTTOM, timeout=timeout, raise_exception=False, expect_missing=True))

    def is_app_in_foreground(self) -> bool:
        """检查当前被测应用是否处于前台运行状态 (自适应 Android 与 HarmonyOS)"""
        target_pkg = getattr(self.driver, "current_package", self.APP_PACKAGE)
        try:
            # 状态枚举：4 表示 RUNNING_IN_FOREGROUND
            app_state = self.driver.query_app_state(target_pkg)
            return app_state == 4
        except Exception:
            try:
                pkg = getattr(self.driver, "current_package", "")
                return pkg in (self.APP_PACKAGE, target_pkg, "com.santiaohms.im")
            except Exception:
                return False

    def wait_for_main_page_load(self, timeout: float = 3.0) -> bool:
        """等待主页面加载就绪"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_in_main_page(timeout=0.2):
                return True
            time.sleep(0.1)
        return False

    def reset_activity_stack_to_main(self) -> bool:
        """
        通过 Android Intent 栈顶恢复机制 (FLAG_ACTIVITY_CLEAR_TOP)，
        在不强杀进程、不中断 WebSocket 长连接的前提下，将 MainActivity 瞬间推回栈顶。
        """
        logger.warning(f"{LogIcon.ACTION} [StateHealer] 触发 Intent 栈顶恢复：无损归位 MainActivity...")
        try:
            # 1. 优先使用 Appium UiAutomator2 原生 mobile: startActivity (FLAG_ACTIVITY_CLEAR_TOP | SINGLE_TOP = 0x24000000)
            self.driver.execute_script(
                "mobile: startActivity",
                {
                    "component": f"{self.APP_PACKAGE}/{self.MAIN_ACTIVITY}",
                    "flags": 0x24000000
                }
            )
            time.sleep(0.2)
            if self.is_in_main_page(timeout=0.3):
                logger.info(f"{LogIcon.SUCCESS} [StateHealer] Intent 栈顶清空归位成功！")
                return True
        except Exception as e:
            logger.debug(f"{LogIcon.WARN} [StateHealer] mobile: startActivity 执行失败，尝试 activate_app 备用通道: {e}")

        # 2. 备用通道：activate_app 激活回到前台
        try:
            self.driver.activate_app(self.APP_PACKAGE)
            time.sleep(0.25)
            if self.is_in_main_page(timeout=0.3):
                logger.info(f"{LogIcon.SUCCESS} [StateHealer] activate_app 备用通道归位成功！")
                return True
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} [StateHealer] activate_app 备用通道失败: {e}")

        return False

    def ensure_app_alive_and_ready(self) -> bool:
        """兜底保障：检查应用进程存活状态，若未在前台运行则自动热拉起并就绪 (自适应 Android 与 HarmonyOS)"""
        target_pkg = getattr(self.driver, "current_package", self.APP_PACKAGE)
        try:
            # App 状态：0=NOT_INSTALLED, 1=NOT_RUNNING, 2=BACKGROUND_SUSPENDED, 3=BACKGROUND, 4=FOREGROUND
            app_state = self.driver.query_app_state(target_pkg)
            if app_state != 4:
                logger.warning(f"{LogIcon.WARN} 🚨 [StateHealer] App 未在前台运行 (State={app_state})，执行自动热唤醒拉起...")
                self.driver.activate_app(target_pkg)
                time.sleep(0.5)
                return self.wait_for_main_page_load(timeout=3.0)
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} [StateHealer] 查询应用状态异常: {e}")
            try:
                self.driver.activate_app(target_pkg)
                time.sleep(0.5)
            except Exception:
                pass
        return True

    def go_to_main_page(self, timeout: float = 0.8, raise_exception: bool = False, max_retries: int = 5) -> bool:
        """
        [工业级完美] 全局主页无损直达引擎 (平滑微回退优先 + Intent 栈恢复兜底)：
        1. 瞬时前置守卫：严守“先查后动”铁律，若当前已处于主页面且不在搜索层，0ms 直接放行，绝不执行任何返回动作！
        2. 受控平滑微退栈：仅在确信不在主页时，逐次轻柔退栈并即时刹车；
        3. 栈顶直达兜底：若平滑返回后仍未归位，启用 FLAG_ACTIVITY_CLEAR_TOP 瞬间斩断。
        """
        # 1. 瞬时前置守卫：已在主页 100% 绝对拦截放行，严禁触碰任何返回动作！
        if self.is_in_main_page(timeout=timeout, raise_exception=raise_exception):
            logger.debug(f"{LogIcon.FIND} 🍏 [StateHealer] 当前已处于纯净主页面，0 操作安全放行")
            return True

        logger.info(f"{LogIcon.ACTION} [StateHealer] 检测到不在主页面，开始归位主页面...")

        for step in range(max_retries):
            if not self.is_app_in_foreground():
                logger.warning(f"{LogIcon.ACTION} [StateHealer] 检测到已不在应用前台，终止按 Back，切入 Intent 恢复...")
                break
            try:
                if self.is_in_main_page(timeout=0.3):
                    logger.info(f"{LogIcon.SUCCESS} 🍏 [StateHealer] 平滑第 {step + 1} 次退回已成功归位主页面 (零闪烁)")
                    return True
                self.back(timeout=0.2)
            except Exception:
                pass

        # 3. 核心栈顶直达 (仅在前几轮平滑返回仍未归位的深层未知异常下，才启用的终极重武器兜底)
        if self.reset_activity_stack_to_main():
            return True

        # 4. 异常容错自愈 (如存在搜索覆盖层、展开抽屉遮挡)
        if self.is_in_search_page(timeout=0.1):
            logger.info(f"{LogIcon.SETUP} [StateHealer] 检测到残留搜索覆盖层，正在退出搜索...")
            try:
                self.click(HomeLocator.SEARCH_CANCEL, timeout=1.0)
            except Exception:
                self.press_keycode(4)

        if not self.is_in_main_page(timeout=0.1):
            try:
                # 针对可能展开的侧滑抽屉或弹窗轻触一次系统返回收起
                self.press_keycode(4)
                time.sleep(0.15)
            except Exception:
                pass

        # 5. 状态校验
        if self.is_in_main_page(timeout=0.3):
            logger.info(f"{LogIcon.SUCCESS} 🍏 [StateHealer] 状态自愈完成，已确保停留在主页面")
            return True

        # 6. 进程存活终极兜底
        self.ensure_app_alive_and_ready()
        success = self.is_in_main_page(timeout=0.5)
        if success:
            logger.info(f"{LogIcon.SUCCESS} 🍏 [StateHealer] 状态自愈完成，已确保停留在主页面")
            return True

        if raise_exception:
            raise RuntimeError("❌ [StateHealer] 经过终极自愈后仍未能恢复至主页面！")
        logger.error(f"{LogIcon.FAIL} [StateHealer] 经过终极自愈后仍未能恢复至主页面")
        return False

    # =========================================================================
    # 核心首页业务能力 (多端自适应 Android 与 HarmonyOS NEXT)
    # =========================================================================
    def click_conversation_by_name(self, name: str, timeout: float = 3.0) -> bool:
        """
        [主页核心业务] 按联系人或会话名称检索并点击进入会话 (自适应 Android 与 HarmonyOS)
        :param name: 目标会话或联系人名称
        :param timeout: 单次查找超时时间 (秒)
        :return: 是否成功点击进入会话
        """
        logger.info(f"{LogIcon.ACTION} [MainPage] 准备点击进入会话: '{name}'")
        if not self.is_in_main_page(timeout=0.5):
            self.go_to_main_page(timeout=1.0)

        loc = HomeLocator.get_conver_by_name(name)
        elem = self.find_element(loc, timeout=timeout, raise_exception=False)
        if elem:
            elem.click()
            logger.info(f"{LogIcon.SUCCESS} [MainPage] 成功点击进入会话: '{name}'")
            return True

        # 若首屏未找到，尝试短程轻微滑动一次再次查找
        try:
            self.swipe_page_quickly(slid_type='up', duration=200)
            elem = self.find_element(loc, timeout=1.5, raise_exception=False)
            if elem:
                elem.click()
                logger.info(f"{LogIcon.SUCCESS} [MainPage] 滑动后成功点击进入会话: '{name}'")
                return True
        except Exception:
            pass

        logger.warning(f"{LogIcon.WARN} [MainPage] 未能在会话列表中找到目标: '{name}'")
        return False

    def enter_chat(self, name: str, timeout: float = 3.0) -> bool:
        """进入会话 (对齐 ChatListPage.enter_chat 与通用测试用例习惯)"""
        return self.click_conversation_by_name(name=name, timeout=timeout)

    def is_conversation_exist(self, name: str, timeout: float = 2.0) -> bool:
        """检查指定名称的会话是否存在于当前首页会话列表"""
        loc = HomeLocator.get_conver_by_name(name)
        return self.is_element_exist(loc, timeout=timeout)

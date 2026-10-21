import time
import pytest
import allure
import pytest_check as check
from pages.home.harmony_home_page import HarmonyHomePage
from core.logger_utils import logger, LogIcon


class BaseSmokeHarmony:
    """鸿蒙冒烟测试公共基类，统一管理 Page 实例化与原生状态自愈"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_harmony_sender):
        """用例前置：注入 HarmonyHomePage，后置：执行鸿蒙原生主页自愈"""
        self.driver = driver_harmony_sender
        self.homePage = HarmonyHomePage(driver_harmony_sender)
        yield
        try:
            logger.info(f"{LogIcon.SETUP} [Teardown] 执行鸿蒙端主页轻量自愈与状态复原...")
            self.homePage.ensure_in_home_page(max_retries=2)
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} [Teardown] 状态复位异常（非阻断）: {e}")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-鸿蒙端-主页与生命周期")
class TestSmokeHarmony(BaseSmokeHarmony):
    """鸿蒙 NEXT 平台冒烟测试套件（原生鸿蒙 Page Object 架构规范）"""

    @pytest.mark.p0
    @pytest.mark.smoke
    @allure.severity(allure.severity_level.BLOCKER)
    @allure.story("应用生命周期与主页加载")
    @allure.title("验证鸿蒙端App冷启动与主页核心元素渲染-状态：已完成")
    def test_harmony_launch_and_home_render(self):
        """
        用例ID: TC_HARMONY_SMOKE_001
        测试步骤：
        1. 验证目标应用处于前台且主页面完全渲染就绪；
        2. 获取主页顶部中间标题，验证标题文本正常展示。
        """
        with allure.step("1. 验证主页面加载完成"):
            is_loaded = self.homePage.wait_home_page(timeout=10)
            check.is_true(is_loaded, "❌ 鸿蒙端主页加载超时或核心元素未呈现")

        with allure.step("2. 获取主页顶部中间标题并断言"):
            top_title = self.homePage.get_top_middle_title(timeout=3)
            logger.info(f"{LogIcon.FIND} 鸿蒙主页标题文本: '{top_title}'")
            check.is_true(bool(top_title and top_title.strip()), "❌ 主页顶部中间标题为空")

    @pytest.mark.p1
    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("主页侧边栏与菜单交互")
    @allure.title("验证鸿蒙端主页侧滑抽屉菜单打开与返回-状态：已完成")
    def test_harmony_drawer_menu_interaction(self):
        """
        用例ID: TC_HARMONY_SMOKE_002
        测试步骤：
        1. 点击主页左上角菜单按钮打开侧边栏；
        2. 触发返回关闭侧边栏，验证能顺畅返回主页面。
        """
        with allure.step("1. 点击左上角菜单打开侧边栏"):
            self.homePage.open_left_menu(timeout=3)

        with allure.step("2. 执行返回操作并校验主页面状态"):
            self.homePage.back(timeout=0.3)
            is_main = self.homePage.is_home_page_loaded(timeout=1.0)
            check.is_true(is_main, "❌ 关闭侧边栏后未能正确返回主页面")

    @pytest.mark.p1
    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.story("右上角功能菜单交互")
    @allure.title("验证鸿蒙端主页右上角加号菜单展开交互-状态：已完成")
    def test_harmony_add_button_expand(self):
        """
        用例ID: TC_HARMONY_SMOKE_003
        测试步骤：
        1. 点击主页右上角 + 号按钮展开菜单；
        2. 触发返回收起菜单，验证环境正常复位。
        """
        with allure.step("1. 点击右上角 + 菜单按钮"):
            self.homePage.click_add_button(timeout=3)
            time.sleep(0.5)

        with allure.step("2. 验证主页面平滑复位"):
            self.homePage.back(timeout=0.3)
            is_main = self.homePage.is_home_page_loaded(timeout=1.0)
            check.is_true(is_main, "❌ 收起加号菜单后主页面状态异常")

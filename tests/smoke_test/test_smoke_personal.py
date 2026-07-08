import pytest
import allure
import pytest_check as check
from pages.system.main.main_page import MainPage
from pages.system.home.home_page import HomePage
from pages.system.home.side_slip_page import SideSlipPage
from pages.personal.other_page import OtherPage
from core.logger_utils import logger

class BaseSmokePersonal:
    """个人资料模块测试基类"""

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        self.otherPage = OtherPage(driver_sender)

        with allure.step("前置步骤：从首页导航到个人信息详情页"):
            self.mainPage.go_to_main_page()
            self.homePage.open_left_menu()
            self.sideSlipPage.click_INFO()
            
        yield
        
        try:
            logger.info("🧹 [Method Teardown] 尝试恢复页面状态至首页...")
            self.otherPage.back_to_personal_info()
            self.mainPage.go_to_main_page()
        except Exception as e:
            logger.error(f"❌ [Method Teardown] 清理状态失败: {e}")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-个人资料与设置")
class TestSmokePersonal(BaseSmokePersonal):
    """个人资料与设置模块冒烟用例集"""

    @allure.story("个人昵称修改")
    @allure.title("修改个人昵称并验证修改成功")
    def test_smoke_modify_nickname(self):
        new_nickname = "测试烟测试"
        
        with allure.step("1. 获取修改前的初始昵称"):
            pre_nickname = self.otherPage.get_nickname()
            if pre_nickname == new_nickname:
                new_nickname = "测试烟测试二"

        with allure.step(f"2. 输入新昵称 '{new_nickname}' 并保存"):
            self.otherPage.click_nickname()
            self.otherPage.click_clear()
            self.otherPage.change_nickname(new_nickname)
            self.otherPage.click_done()

        with allure.step("3. 校验昵称是否成功更新"):
            aft_nickname = self.otherPage.get_nickname()
            check.equal(aft_nickname, new_nickname, f"❌ 昵称更新失败，UI显示值仍为 '{aft_nickname}'")

        # 4. 环境还原
        with allure.step("4. 将昵称恢复为原始昵称（环境还原）"):
            self.otherPage.click_nickname()
            self.otherPage.click_clear()
            self.otherPage.change_nickname(pre_nickname)
            self.otherPage.click_done()

    @allure.story("手机号隐私切换")
    @allure.title("手机号显示与隐藏（明文/密文）状态切换校验")
    def test_smoke_phone_toggle_display(self):
        with allure.step("1. 获取手机号初始状态"):
            initial_phone = self.otherPage.get_phone_num()
            is_initially_hidden = '*' in initial_phone

        with allure.step("2. 点击眼睛图标切换状态"):
            self.otherPage.click_phone_eyes()
            phone = self.otherPage.get_phone_num()

        with allure.step("3. 断言状态已翻转并符合格式"):
            if is_initially_hidden:
                check.is_not_in('*', phone, f"❌ 预期密文应成功切换为明文，当前: '{phone}'")
                check.is_true(self.otherPage.verify_phone_num_show(phone), "❌ 明文手机号格式不符合全数字要求")
            else:
                check.is_in('*', phone, f"❌ 预期明文应成功切换为密文，当前: '{phone}'")

        with allure.step("4. 点击眼睛图标恢复初始显示状态（环境还原）"):
            self.otherPage.click_phone_eyes()

    @allure.story("我的二维码")
    @allure.title("查看我的二维码界面并保存到手机相册")
    def test_smoke_qrcode_and_save(self):
        expected_nickname = self.otherPage.get_nickname()

        with allure.step("1. 点击进入我的二维码页面"):
            self.otherPage.click_my_qrcode()

        with allure.step("2. 校验页面基础元素是否存在"):
            all_exist = self.otherPage.find_all_qrcode_attr()
            check.is_true(all_exist, "❌ 二维码页面的关键UI元素未找齐")

            qr_nickname = self.otherPage.get_qrcode_nickname()
            check.equal(qr_nickname, expected_nickname, f"❌ 二维码页昵称 '{qr_nickname}' 与个人信息页昵称 '{expected_nickname}' 不一致")

        with allure.step("3. 点击保存二维码并校验成功 Toast"):
            self.otherPage.click_save_qrcode()
            toast_msg = self.otherPage.get_qrcode_toase()
            check.is_in("已保存到相册", toast_msg, f"❌ 保存二维码失败或未捕获到对应Toast提示，实际提示: '{toast_msg}'")

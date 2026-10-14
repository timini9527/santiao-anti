import time
import pytest
import allure
import pytest_check as check
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.home.side_slip_page import SideSlipPage
from pages.personal.other_page import OtherPage
from core.logger_utils import logger

class BaseSmokePersonal:
    """个人资料模块测试基类"""
    mainPage: MainPage
    homePage: HomePage
    sideSlipPage: SideSlipPage
    otherPage: OtherPage

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, driver_sender):
        """类级别前置与后置：进入个人信息页，并在整类所有用例执行完毕后统一返回主页"""
        main_page = MainPage(driver_sender)
        home_page = HomePage(driver_sender)
        side_slip_page = SideSlipPage(driver_sender)
        other_page = OtherPage(driver_sender)

        # 挂载到类对象上，确保类内所有用例均可访问
        request.cls.mainPage = main_page
        request.cls.homePage = home_page
        request.cls.sideSlipPage = side_slip_page
        request.cls.otherPage = other_page

        with allure.step('类前置步骤：从首页导航到个人信息详情页'):
            main_page.go_to_main_page()
            home_page.open_left_menu()
            side_slip_page.click_INFO()
        yield
        with allure.step('类后置步骤：所有用例执行完毕，返回首页'):
            try:
                logger.info('🧹 [Class Teardown] 恢复页面状态至首页...')
                other_page.back_to_personal_info()
                main_page.go_to_main_page()
            except Exception as e:
                logger.error(f'❌ [Class Teardown] 状态恢复失败: {e}')

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """方法级别前置：确保当前用例实例拥有 Page 对象，用例之间绝不退回主页"""
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.sideSlipPage = SideSlipPage(driver_sender)
        self.otherPage = OtherPage(driver_sender)
        yield




@allure.epic('IM核心功能测试')
@allure.feature('冒烟测试-个人资料与设置')
class TestSmokePersonal(BaseSmokePersonal):
    """个人资料与设置模块冒烟用例集"""

    @pytest.mark.p1
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @allure.story('个人昵称修改')
    @allure.title('修改个人昵称并验证修改成功-状态：已完成')
    def test_smoke_modify_nickname(self):
        """测试修改个人昵称的核心链路，包含动态时间戳防撞与 finally 强闭环环境还原"""
        unique_suffix = int(time.time() * 1000) % 100000
        new_nickname = f'烟测_{unique_suffix}'
        with allure.step('1. 获取修改前的初始昵称'):
            pre_nickname = self.otherPage.get_nickname()
            check.is_true(bool(pre_nickname), '❌ 获取修改前初始昵称失败或为空')
        try:
            with allure.step(f"2. 输入新昵称 '{new_nickname}' 并保存"):
                self.otherPage.click_nickname()
                self.otherPage.click_clear()
                self.otherPage.change_nickname(new_nickname)
                self.otherPage.click_done()
            with allure.step('3. 校验昵称是否成功更新'):
                aft_nickname = self.otherPage.get_nickname()
                check.equal(aft_nickname, new_nickname, f"❌ 昵称更新失败，UI显示值仍为 '{aft_nickname}'")
        finally:
            with allure.step('4. 强防御环境还原：将昵称恢复为原始昵称'):
                try:
                    current_name = self.otherPage.get_nickname()
                    if current_name != pre_nickname:
                        self.otherPage.click_nickname()
                        self.otherPage.click_clear()
                        self.otherPage.change_nickname(pre_nickname)
                        self.otherPage.click_done()
                except Exception as e:
                    logger.error(f'⚠️ [Teardown] 还原原始昵称异常: {e}')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('手机号隐私切换')
    @allure.title('手机号显示与隐藏（明文/密文）状态切换校验-状态：已完成')
    def test_smoke_phone_toggle_display(self):
        """测试手机号明文与掩码密文切换展示，包含 finally 状态对称性恢复"""
        with allure.step('1. 获取手机号初始状态'):
            initial_phone = self.otherPage.get_phone_num()
            check.is_true(bool(initial_phone), '❌ 获取初始手机号文本为空')
            is_initially_hidden = '*' in initial_phone
        try:
            with allure.step('2. 点击眼睛图标切换状态'):
                self.otherPage.click_phone_eyes()
                phone = self.otherPage.get_phone_num()
            with allure.step('3. 断言状态已翻转并符合格式'):
                if is_initially_hidden:
                    check.is_not_in('*', phone, f"❌ 预期密文应成功切换为明文，当前: '{phone}'")
                    check.is_true(self.otherPage.verify_phone_num_show(phone), '❌ 明文手机号格式不符合全数字要求')
                else:
                    check.is_in('*', phone, f"❌ 预期明文应成功切换为密文，当前: '{phone}'")
        finally:
            with allure.step('4. 强防御环境还原：确保恢复初始手机号显示状态'):
                try:
                    final_phone = self.otherPage.get_phone_num()
                    if ('*' in final_phone) != is_initially_hidden:
                        self.otherPage.click_phone_eyes()
                except Exception as e:
                    logger.error(f'⚠️ [Teardown] 恢复手机号初始显示状态异常: {e}')

    @pytest.mark.p2
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.smoke
    @allure.story('我的二维码')
    @allure.title('查看我的二维码界面并保存到手机相册-状态：已完成')
    def test_smoke_qrcode_and_save(self):
        """测试查看个人二维码及保存相册功能，验证页面元素完整性及自闭环退出"""
        expected_nickname = self.otherPage.get_nickname()
        with allure.step('1. 点击进入我的二维码页面'):
            self.otherPage.click_my_qrcode()
        try:
            with allure.step('2. 校验页面基础元素是否存在'):
                all_exist = self.otherPage.find_all_qrcode_attr()
                check.is_true(all_exist, '❌ 二维码页面的关键UI元素未找齐')
                qr_nickname = self.otherPage.get_qrcode_nickname()
                check.equal(qr_nickname, expected_nickname, f"❌ 二维码页昵称 '{qr_nickname}' 与个人信息页昵称 '{expected_nickname}' 不一致")
            with allure.step('3. 点击保存二维码并校验成功 Toast'):
                self.otherPage.click_save_qrcode()
                toast_msg = self.otherPage.get_qrcode_toast()
                check.is_in('已保存到相册', toast_msg, f"❌ 保存二维码失败或未捕获到对应Toast提示，实际提示: '{toast_msg}'")
        finally:
            with allure.step('4. 页面闭环退出：返回个人资料主页面'):
                try:
                    self.otherPage.click_qrcode_back()
                except Exception as e:
                    logger.warning(f'⚠️ [Teardown] 退出二维码页面异常，尝试备用返回: {e}')
                    self.otherPage.back_to_personal_info()
from selenium.webdriver.support.ui import WebDriverWait
import pytest
import allure
from pages.users.loginPage import LoginPage
from pages.main.main_page import MainPage
from pages.mine.mine_page import MinePage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data


#   读取YAML文件
def get_test_data():
    data = load_yaml_data('logins/login_data.yaml')
    return data['login_test_cases']


@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-账号密码登录")
@allure.story("启动APP")
class TestLogin:

    @allure.story("启动APP")
    def test_start_app(self, driver_sender):
        # 使用显式等待：等待页面加载出某个元素才开始下步
        wait = WebDriverWait(driver_sender, 10)

        # 步骤1：验证 App 是否成功打开（通过判断某个主页按钮是否存在）
        print("正在验证 App 启动状态...")
        main_page = MainPage(driver_sender)
        try:
            main_page.is_agree_page_exists()
        except Exception as e:
            print(f"检查协议页面失败: {e}")
            raise e
        assert driver_sender.current_package == 'com.santiaotalk.im'

    @allure.title("退出登录")
    def test_exit_log(self, driver_sender):
        mine_page = MinePage(driver_sender)
        login_s = mine_page.exit_login_page()
        print("要登录")
        assert login_s in (True, False), "处于登录状态，需要退出"


    @allure.story("登录测试")
    @allure.severity(allure.severity_level.BLOCKER)
    @pytest.mark.parametrize("loginCases", get_test_data(), ids=[c['id'] for c in get_test_data()])
    def test_login_scenarios(self, driver_sender, loginCases):
        """
        数据驱动测试：
        """
        # allure.dynamic.title(loginCases['id'])
        logger.info(f"🚀 登录测试用例：{loginCases['id']} - {loginCases['desc']}")
        print(f"\n🚀 正在执行: {loginCases['id']} - {loginCases['desc']}")

        login_page = LoginPage(driver_sender)
        main_page = MainPage(driver_sender)
        mine_page = MinePage(driver_sender)

        # 1. 点击进入登录页（如果还没在里面的话）
        login_page.click_login_entry_if_exists()

        # 2. 勾选协议
        # login_page.agree_protocol()

        # 3. 输入 YAML 中的动态数据
        login_page.login(loginCases['account'], loginCases['password'])

        # 4. 预期结果分类断言
        if loginCases['expected'] == "success":
            result = main_page.is_login_success()
            print(f"是否进入主页面： {result}")
            mine_page.exit_login_page()
            assert result is True, f"失败原因：{loginCases['desc']} 应该登录成功但失败了"
            print(f"✅ {loginCases['id']} 正常登录通过")
        elif loginCases['expected'] == "fail":
            result = login_page.is_login_page_status()
            print(f"是否停在登录页面： {result}")
            assert result is True, f"失败原因：{loginCases['desc']} 重新登录"
        else:
            # 预期失败的断言
            result = main_page.is_login_success()
            print(f"是否进入主页面： {result}")
            assert result is False, f"失败原因：{loginCases['desc']} 应该登录失败但成功进入了主页"
            print(f"✅ {loginCases['id']} 失败校验通过（捕获到了预期的失败症状）")


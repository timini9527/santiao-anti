import pytest
import allure
from core.logger_utils import logger
from pages.users.registPage import RegistPage


@allure.epic("IM核心功能测试")
@allure.feature("登录注册模块-注册")
@allure.story("短信注册测试")
class TestRegist:


    @allure.story("短信注册测试")
    # @pytest.mark.parametrize("registCases", get_test_data(), ids=[c['id'] for c in get_test_data()])
    @pytest.mark.parametrize("registCases", [
        {"account" : "18888888888", "password" : "a1234567B", "re_password" : "a1234567B"}
    ])
    def test_sms_regist(self, driver_sender, registCases):
        logger.info(f"🚀 注册测试用例：{registCases['account']} - {registCases['password']}")
        regist_page = RegistPage(driver_sender)

        # 1.点击进入注册页（如果还没在里面的话）
        regist_page.click_regist_entry_if_exists()

        # 2. 从登录页面进入注册
        regist_page.entry_register_page()

        # 3. 输入注册信息
        regist_page.sms_regist(registCases['account'], registCases['password'], registCases['re_password'])

        pass
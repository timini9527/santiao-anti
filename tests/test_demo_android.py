import time
from selenium.webdriver.support.ui import WebDriverWait
import pytest
import allure
from pages.home.home_page import HomePage
from core.logger_utils import logger, LogIcon


@pytest.mark.p2
@allure.severity(allure.severity_level.NORMAL)
@allure.epic('系统冒烟与通用功能')
@allure.feature('通用启动与流程Demo')
@allure.story('App启动与基础包名校验')
@allure.title('验证App启动状态与基础会话流转-状态：已完成')
def test_full_flow(driver_sender):
    wait = WebDriverWait(driver_sender, 15)
    HomePage(driver_sender).open_left_menu()
    logger.info(f"{LogIcon.ACTION} 正在验证 App 启动状态...")
    assert driver_sender.current_package == 'com.santiaotalk.im'
    logger.info(f"{LogIcon.SUCCESS} 业务测试流程执行完毕！")
    time.sleep(10)
import time
from selenium.webdriver.support.ui import WebDriverWait
import pytest
import allure
import sys
import os
from pages.system.home.home_page import HomePage
from pages.personal.other_page import OtherPage
from pages.auth.users.loginPage import LoginPage
from utils.file_reader.csv_handler import RegionCrawler


def test_full_flow(driver_sender):
    # 使用显式等待：等待页面加载出某个元素才开始下步，比 time.sleep 科学
    wait = WebDriverWait(driver_sender, 15)
    # wait = WebDriverWait(driver_receiver, 15)

    HomePage(driver_sender).open_left_menu()

    # 步骤1：验证 App 是否成功打开（通过判断某个主页按钮是否存在）
    print("正在验证 App 启动状态...")
    assert driver_sender.current_package == 'com.santiaotalk.im'
    # assert driver_receiver.current_package == 'com.santiaotalk.im'
    print("业务测试流程执行完毕！")
    time.sleep(10)
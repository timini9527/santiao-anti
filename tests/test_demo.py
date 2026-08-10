import time
from selenium.webdriver.support.ui import WebDriverWait
import pytest
import allure
import sys
import os
from pages.home.home_page import HomePage
from pages.personal.other_page import OtherPage
from pages.login.login_page import LoginPage
from utils.file_reader.csv_handler import RegionCrawler

def test_full_flow(driver_sender):
    wait = WebDriverWait(driver_sender, 15)
    HomePage(driver_sender).open_left_menu()
    print('正在验证 App 启动状态...')
    assert driver_sender.current_package == 'com.santiaotalk.im'
    print('业务测试流程执行完毕！')
    time.sleep(10)
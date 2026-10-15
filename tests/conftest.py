import pytest
from common.base_page import BasePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.main.main_page import MainPage
from pages.home.side_slip_page import SideSlipPage
from pages.home.home_page import HomePage
from core.logger_utils import logger, LogIcon

@pytest.fixture(scope='class')
def enter_personal_info(driver_sender):
    """
    前置：只在第一个用例开始前，从首页导航到个人信息页
    """
    logger.info(f'{LogIcon.SETUP} [Class Setup] 正在初始化页面并导航至个人信息页...')
    home_page = HomePage(driver_sender)
    side_slip_page = SideSlipPage(driver_sender)
    home_page.open_left_menu()
    side_slip_page.click_INFO()
    yield
    logger.info(f'{LogIcon.SETUP} [Class Teardown] 当前类测试结束，清理类级别状态...')

@pytest.fixture(scope='class')
def message_page(driver_sender):
    """
    完整前置流程：启动 App -> 判断是否在消息 -> 进入消息页面
    返回 MessagePage 对象给测试类使用
    """
    main_page = MainPage(driver_sender)
    main_page.go_to_main_page()
    yield main_page

@pytest.fixture(scope='function')
def go_to_message_list(driver_sender):
    """
    完整前置流程：启动 App -> 判断是否在消息 -> 进入消息页面 -> 进入第一个对话
    :param driver_sender:
    :return:
    """
    basePage = BasePage(driver_sender)
    mainPage = MainPage(driver_sender)
    chatListPage = ChatListPage(driver_sender)
    chatListPage.enter_private_chat()
    yield
    basePage.back()
    mainPage.go_to_main_page()
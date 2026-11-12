# -*- coding: utf-8 -*-
"""
iOS 消息发送验证测试 (XCUITest / WebDriverAgent 原生架构)
覆盖选择好友、进入会话、发送消息核心操作链路。
"""
import os
import time
import allure
import pytest
from appium.webdriver.webdriver import WebDriver

from core.logger_utils import LogIcon, logger
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage

# 默认进入的目标私聊会话名称 (支持环境变量覆盖)
DEFAULT_SESSION_NAME: str = os.environ.get("PRIVATE_CHAT_NAME") or "测试0222"


@allure.epic("IM核心功能测试")
@allure.feature("iOS 端消息收发")
class TestDemoIos:
    """
    iOS 端消息发送测试：
    纯净验证：选择好友 -> 进入会话 -> 发送消息。
    """

    @pytest.mark.p0
    @allure.story("发送文本消息")
    @allure.title("iOS 发送消息验证: 选择好友 -> 进入会话 -> 发送消息")
    def test_ios_send_message(self, driver_ios_sender: WebDriver) -> None:
        """
        iOS 测试发送消息（极简三步流程，无断言与冗余逻辑）：
        1. 选择好友
        2. 进入会话
        3. 发送消息
        """
        chat_page = ChatPage(driver_ios_sender)
        chat_list_page = ChatListPage(driver_ios_sender)

        # 1. 选择好友 & 2. 进入会话
        with allure.step(f"1. 选择好友并进入会话: 【{DEFAULT_SESSION_NAME}】"):
            logger.info(f"{LogIcon.ACTION} 选择好友并进入会话: 【{DEFAULT_SESSION_NAME}】")
            chat_list_page.enter_chat(DEFAULT_SESSION_NAME)

        # 3. 发送消息
        msg_content = f"iOS测试消息_{time.strftime('%H%M%S')}"
        with allure.step(f"2. 发送文本消息: {msg_content}"):
            logger.info(f"{LogIcon.ACTION} 发送文本消息: {msg_content}")
            chat_page.send_message(msg_content)
            logger.info(f"{LogIcon.SUCCESS} 消息已发送完成")

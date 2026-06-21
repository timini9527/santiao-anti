import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException

def test_mock_success():
    """模拟一个执行成功的用例"""
    print("执行正向流程成功！")
    assert True

def test_mock_assertion_error():
    """模拟业务 Bug，即 Assertion 失败"""
    print("开始验证业务数据...")
    actual_title = "未读消息(2)"
    expected_title = "未读消息(3)"
    assert actual_title == expected_title, f"业务校验失败: 期望值为 {expected_title}, 实际为 {actual_title}"

def test_mock_no_such_element():
    """模拟元素定位失败 (NoSuchElementException)"""
    print("试图寻找登录按钮...")
    login_btn_locator = "//*[@id='login_btn']"
    if login_btn_locator == "//*[@id='login_btn']":
        raise NoSuchElementException("Message: An element could not be located on the page using the given search parameters. (xpath: //*[@id='login_btn'])")
    else:
        print(f"[OK] 动态自愈成功！使用的是修改后的定位器: {login_btn_locator}")
        assert True

def test_mock_timeout():
    """模拟显式等待超时 (TimeoutException)"""
    print("等待聊天气泡弹出，设置超时 5 秒...")
    # 模拟显式等待超时
    raise TimeoutException("Message: Waiting for element to be clickable: //div[@class='message-bubble'] (timeout 5s)")

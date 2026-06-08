import sys
import os

# 1. 处理无窗口模式丢失 stdout 的问题 (如果你去掉了 -w 参数，这一段可以不写)
# if sys.stdout is None or sys.stderr is None: ...

# ==========================================
# 2. 强行导入所有隐式依赖，骗过 PyInstaller 让它打包
import pytest
import appium
from appium import webdriver
# 如果你还用了其他的第三方库，比如 requests, allure, selenium 等，全在这里 import 一下
# import requests 
# import time

# 把你自己的核心目录也导入一下，防止找不到
import core.driver_factory
# ==========================================

def get_current_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    report_path = os.path.join(get_current_path(), 'report.html')
    
    # 3. 注意这里的参数！加上 '--assert=plain'
    # 因为 pytest 默认会重写 assert 来提供详细报错，这在 exe 环境下极易崩溃
    pytest.main(['-s', '-v', '--assert=plain', f'--html={report_path}', 'tests/chat_options/voice/test_voice.py'])
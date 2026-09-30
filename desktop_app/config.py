# -*- coding: utf-8 -*-
"""
=======================================================
三条 IM 自动化测试控制台 (原生桌面端) - 配置与持久化管理
=======================================================
负责所有选择状态、设备端口、UDID、聊天好友昵称、测试视角等参数的本地持久化记忆，
确保软件关闭或切换页面后 100% 保持上一次的配置，绝不重置。
"""
import os
import sys
import json
from typing import Dict, Any

def resolve_project_root() -> str:
    """自适应获取真实项目根目录（支持源码运行和 PyInstaller 打包环境）"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        candidates = [
            exe_dir,
            os.path.dirname(exe_dir),
            os.getcwd(),
            r"D:\projects\santiao-anti"
        ]
        for cand in candidates:
            if os.path.exists(os.path.join(cand, "tests")):
                return cand
        return exe_dir
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

PROJECT_ROOT = resolve_project_root()
CONFIG_FILE = os.path.join(PROJECT_ROOT, "config", "desktop_settings.json")

DEFAULT_SETTINGS: Dict[str, Any] = {
    # 移动端测试默认状态
    "mobile": {
        "os_type": "Android",
        "remote_appium": "127.0.0.1:4723",
        "remote_udid": "QFF0219A11009305",
        "remote_appium2": "127.0.0.1:4724",
        "remote_udid2": "20a5fa17",
        "private_chat_name": "王强",
        "group_chat_name": "测试交流群",
        "env": "dev",
        "debug_mode": True,
        "role": "business",  # 默认业务精简视角
        "selected_test_file": "",
        "auto_scroll_log": True
    },
    # Web 端测试默认状态
    "web": {
        "browser": "chromium",
        "headless": False,
        "base_url": "https://test.im.example.com",
        "env": "dev"
    },
    # 接口端测试默认状态
    "api": {
        "target_env": "dev",
        "concurrency": 1
    },
    # 窗口大小与位置
    "window": {
        "width": 1440,
        "height": 920,
        "maximized": False
    }
}

class DesktopConfigManager:
    """桌面应用配置管理器"""
    
    def __init__(self):
        self._settings = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 递归合并默认配置，防止缺失键
                    merged = json.loads(json.dumps(DEFAULT_SETTINGS))
                    for k, v in data.items():
                        if isinstance(v, dict) and k in merged:
                            merged[k].update(v)
                        else:
                            merged[k] = v
                    return merged
            except Exception as e:
                print(f"[Config] 加载本地配置异常: {e}")
        return json.loads(json.dumps(DEFAULT_SETTINGS))

    def save(self):
        """将当前内存中的配置保存至本地磁盘"""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Config] 保存本地配置失败: {e}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        return self._settings.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        if section not in self._settings:
            self._settings[section] = {}
        self._settings[section][key] = value
        self.save()

    def get_section(self, section: str) -> Dict[str, Any]:
        return self._settings.get(section, {})

# 全局单例
desktop_config = DesktopConfigManager()

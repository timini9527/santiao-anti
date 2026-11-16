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
    """自适应获取真实项目根目录（基于 SmartPathResolver 动态雷达定位）"""
    try:
        from desktop_app.core.path_resolver import SmartPathResolver
        return SmartPathResolver.get_project_root()
    except Exception:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(current_dir)

PROJECT_ROOT = resolve_project_root()
try:
    if sys.platform == "darwin" and os.path.abspath(PROJECT_ROOT).startswith("/Volumes/"):
        raise PermissionError("DMG 只读卷")
    _cfg_dir = os.path.join(PROJECT_ROOT, "config")
    os.makedirs(_cfg_dir, exist_ok=True)
    _probe = os.path.join(_cfg_dir, ".cfg_probe")
    with open(_probe, "w", encoding="utf-8") as _f:
        _f.write("ok")
    os.remove(_probe)
    CONFIG_FILE = os.path.join(_cfg_dir, "desktop_settings.json")
except Exception:
    _user_cfg_dir = os.path.join(os.path.expanduser("~"), "SantiaoAutoTest", "config")
    os.makedirs(_user_cfg_dir, exist_ok=True)
    CONFIG_FILE = os.path.join(_user_cfg_dir, "desktop_settings.json")

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
        "auto_scroll_log": True,
        # 布局与分割器持久化记忆
        "splitter_h_sizes": [450, 850],   # 左右布局分割器尺寸记忆 (左边栏 : 右工作区)
        "splitter_v_sizes": [450, 230],   # 上下报告与日志分割器尺寸记忆 (上方看板 : 下方日志)
        "log_collapsed": False,           # 日志控制台吸底折叠状态
        "last_log_height": 230,           # 折叠前日志高度记忆
        "params_collapsed": False,        # 远程测试与设备配置面板折叠状态记忆
        "node_status_map": {},            # 用例执行状态映射记忆
        "expanded_targets": [],           # 用例树展开节点记忆
        # 默认 Web 回执表单结构
        "web_receipt_fields": [
            {"key": "设备1", "val": ""},
            {"key": "私聊用户1", "val": ""},
            {"key": "私聊用户2", "val": ""},
            {"key": "群聊名称1", "val": ""},
            {"key": "群聊名称2", "val": ""},
        ]
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
    # 窗口大小与位置 (支持非最大化时的窗口坐标与尺寸完整记忆)
    "window": {
        "x": None,
        "y": None,
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

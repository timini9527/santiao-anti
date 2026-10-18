import json
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple, Union
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from core.logger_utils import logger, LogIcon


class HarmonyWebElement:
    """鸿蒙原生 UI 元素代理对象，封装对鸿蒙组件属性与交互事件的处理"""

    def __init__(self, driver: "HarmonyDriver", node_data: Dict[str, Any]):
        self.driver = driver
        self.node_data = node_data
        self.attributes = node_data.get("attributes", {})
        self._init_bounds()

    def _init_bounds(self) -> None:
        """解析鸿蒙边界坐标 [left, top][right, bottom]"""
        bounds_str = self.attributes.get("bounds", "[0,0][0,0]")
        match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
        if match:
            self.left = int(match.group(1))
            self.top = int(match.group(2))
            self.right = int(match.group(3))
            self.bottom = int(match.group(4))
        else:
            self.left = self.top = self.right = self.bottom = 0

        self.center_x = (self.left + self.right) // 2
        self.center_y = (self.top + self.bottom) // 2
        self.width = max(0, self.right - self.left)
        self.height = max(0, self.bottom - self.top)

    @property
    def text(self) -> str:
        """获取控件文本，优先读取 originalText，若为空读取 text"""
        return self.attributes.get("originalText") or self.attributes.get("text", "")

    @property
    def tag_name(self) -> str:
        """组件类型，如 Text, Button, Row, Column, Stack 等"""
        return self.attributes.get("type", "Component")

    @property
    def location(self) -> Dict[str, int]:
        """元素左上角坐标"""
        return {"x": self.left, "y": self.top}

    @property
    def size(self) -> Dict[str, int]:
        """元素尺寸"""
        return {"width": self.width, "height": self.height}

    def is_displayed(self) -> bool:
        """判断组件是否可见"""
        return self.attributes.get("visible") == "true" and (self.width > 0 and self.height > 0)

    def is_enabled(self) -> bool:
        """判断组件是否处于可用激活状态"""
        return self.attributes.get("enabled", "true") == "true"

    def click(self) -> None:
        """通过鸿蒙系统 uitest 注入点击中心坐标"""
        logger.debug(f"{LogIcon.ACTION} [HarmonyWebElement] 点击元素 ({self.center_x}, {self.center_y}) - {self.tag_name}")
        self.driver.execute_hdc_shell(f"uitest uiInput click {self.center_x} {self.center_y}")
        time.sleep(0.3)

    def double_click(self) -> None:
        """双击元素"""
        self.driver.execute_hdc_shell(f"uitest uiInput doubleClick {self.center_x} {self.center_y}")
        time.sleep(0.3)

    def long_click(self) -> None:
        """长按元素"""
        self.driver.execute_hdc_shell(f"uitest uiInput longClick {self.center_x} {self.center_y}")
        time.sleep(0.5)

    def send_keys(self, *values: Any) -> None:
        """输入文本内容，如果未聚焦则先点击聚焦"""
        text = "".join(str(v) for v in values)
        logger.info(f"{LogIcon.ACTION} [HarmonyWebElement] 向控件输入文本: '{text}'")
        # 1. 确保控件获得焦点
        self.click()
        time.sleep(0.2)
        # 2. 注入文本内容
        self.driver.execute_hdc_shell(f"uitest uiInput inputText {self.center_x} {self.center_y} '{text}'")
        time.sleep(0.3)

    def clear(self) -> None:
        """清空输入框内容（长按并模拟全选删除）"""
        self.click()
        # 鸿蒙退格键模拟
        for _ in range(15):
            self.driver.execute_hdc_shell("uitest uiInput keyEvent 2055")

    def get_attribute(self, name: str) -> Optional[str]:
        """获取鸿蒙控件特定属性"""
        return self.attributes.get(name)


class HarmonyDriver:
    """
    鸿蒙原生自动化驱动适配器
    基于 HDC 与 HarmonyOS NEXT 内置 uitest 服务实现，
    提供与 Appium / Selenium 完全一致的 Driver API，无缝融入 BasePage。
    """

    def __init__(self, desired_caps: Dict[str, Any]):
        self.caps = desired_caps
        self.udid: str = str(desired_caps.get("udid", "")).strip()
        self.bundle_name: str = desired_caps.get("bundleName") or desired_caps.get("appium:appPackage") or "com.santiaohms.im"
        self.ability_name: str = desired_caps.get("abilityName") or "EntryAbility"
        self.module_name: str = desired_caps.get("moduleName") or "phone"
        self._last_layout_tree: Optional[Dict[str, Any]] = None

        logger.info(f"{LogIcon.SETUP} [HarmonyDriver] 正在初始化鸿蒙驱动，目标设备: {self.udid}, 应用: {self.bundle_name}")
        self._prepare_device()
        self.activate_app(self.bundle_name)

    def _prepare_device(self) -> None:
        """准备并唤醒鸿蒙设备，确保屏幕处于点亮和解锁就绪状态"""
        # 1. 检查 hdc 连接可用性
        result = self.execute_hdc("checkserver")
        if "Ver:" not in result and "server" not in result.lower():
            logger.warning(f"{LogIcon.WARN} [HarmonyDriver] hdc 服务状态异常，重新拉起服务")
            self.execute_hdc("start")

        # 2. 点亮屏幕
        self.execute_hdc_shell("power-shell wakeup")
        time.sleep(0.5)

        # 3. 模拟向上滑动解锁（针对未设密码或已唤醒状态）
        self.execute_hdc_shell("uinput -T -m 500 2000 500 500 300")
        time.sleep(0.5)

    def execute_hdc(self, cmd: str) -> str:
        """执行基础 hdc 指令"""
        full_cmd = ["hdc"]
        if self.udid:
            full_cmd.extend(["-t", self.udid])
        full_cmd.extend(cmd.split())
        try:
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=20,
            )
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [HarmonyDriver] 执行 hdc 失败: {cmd}, 错误: {e}")
            return ""

    def execute_hdc_shell(self, shell_cmd: str) -> str:
        """执行 hdc shell 命令"""
        full_cmd = ["hdc"]
        if self.udid:
            full_cmd.extend(["-t", self.udid])
        full_cmd.extend(["shell", shell_cmd])
        try:
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=25,
            )
            return res.stdout.strip()
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} [HarmonyDriver] 执行 hdc shell 失败: {shell_cmd}, 错误: {e}")
            return ""

    def activate_app(self, bundle_id: Optional[str] = None) -> None:
        """拉起/激活鸿蒙应用"""
        target_bundle = bundle_id or self.bundle_name
        logger.info(f"{LogIcon.ACTION} [HarmonyDriver] 启动鸿蒙应用: {target_bundle}/{self.ability_name}")
        cmd = f"aa start -b {target_bundle} -a {self.ability_name} -m {self.module_name}"
        output = self.execute_hdc_shell(cmd)
        if "error:" in output.lower():
            logger.warning(f"{LogIcon.WARN} [HarmonyDriver] 启动应用警告: {output}")
        time.sleep(1.5)

    def terminate_app(self, bundle_id: Optional[str] = None) -> None:
        """强杀鸿蒙应用进程"""
        target_bundle = bundle_id or self.bundle_name
        logger.info(f"{LogIcon.ACTION} [HarmonyDriver] 终止鸿蒙应用: {target_bundle}")
        self.execute_hdc_shell(f"aa force-stop {target_bundle}")
        time.sleep(0.5)

    @property
    def current_package(self) -> str:
        """兼容 Appium 属性：返回当前包名"""
        return self.bundle_name

    @property
    def page_source(self) -> str:
        """
        获取当前屏幕页面源信息：
        通过鸿蒙原生 uitest dumpLayout 获取布局 JSON，并转换构造成标准 XML 格式
        """
        remote_path = f"/data/local/tmp/dump_layout_{int(time.time())}.json"
        self.execute_hdc_shell(f"uitest dumpLayout -p {remote_path}")
        time.sleep(0.2)
        json_content = self.execute_hdc_shell(f"cat {remote_path}")

        # 清理远程临时文件
        self.execute_hdc_shell(f"rm -f {remote_path}")

        if not json_content or not json_content.strip().startswith("{"):
            return "<Hierarchy />"

        try:
            data = json.loads(json_content)
            self._last_layout_tree = data
            root_elem = ET.Element("Hierarchy", attrib={"platform": "HarmonyOS"})
            self._convert_json_node_to_xml(data, root_elem)
            return ET.tostring(root_elem, encoding="utf-8").decode("utf-8")
        except Exception as e:
            logger.debug(f"{LogIcon.WARN} [HarmonyDriver] 布局转 XML 异常: {e}")
            return "<Hierarchy />"

    def _convert_json_node_to_xml(self, json_node: Dict[str, Any], parent_xml: ET.Element) -> None:
        """递归将 uitest JSON 树转换为兼容 XML"""
        attrs = json_node.get("attributes", {})
        tag = attrs.get("type") or "Component"
        # 过滤非法 XML 字符
        clean_tag = re.sub(r"[^\w\.-]", "_", tag)
        clean_attrs = {}
        for k, v in attrs.items():
            if isinstance(v, (str, int, float, bool)):
                clean_attrs[str(k)] = str(v)

        elem = ET.SubElement(parent_xml, clean_tag, attrib=clean_attrs)
        for child in json_node.get("children", []):
            self._convert_json_node_to_xml(child, elem)

    def _get_layout_data(self) -> Dict[str, Any]:
        """获取当前界面的原始布局字典"""
        remote_path = f"/data/local/tmp/layout_quick_{int(time.time() * 1000)}.json"
        self.execute_hdc_shell(f"uitest dumpLayout -p {remote_path}")
        json_content = self.execute_hdc_shell(f"cat {remote_path}")
        self.execute_hdc_shell(f"rm -f {remote_path}")
        try:
            return json.loads(json_content)
        except Exception:
            return {}

    def find_elements(self, by: By, value: str) -> List[HarmonyWebElement]:
        """
        根据定位策略在鸿蒙 DOM 树中查找所有匹配的元素
        """
        layout_root = self._get_layout_data()
        matched_nodes: List[Dict[str, Any]] = []

        def search_node(node: Dict[str, Any]) -> None:
            attrs = node.get("attributes", {})
            hit = False

            if by == By.ID:
                # 兼容鸿蒙的 id / key / accessibilityId
                clean_target = value.split("/")[-1].split(":")[-1]
                node_id = attrs.get("id", "")
                node_key = attrs.get("key", "")
                if value in (node_id, node_key) or clean_target in (node_id, node_key):
                    hit = True
            elif by == By.XPATH:
                # 简易文本与属性 XPath 匹配: //*[contains(@text, 'xxx')] 或 //*[@id='xxx']
                if "@text=" in value:
                    expected_text = value.split("@text=")[1].strip("'\" ]")
                    if attrs.get("text") == expected_text or attrs.get("originalText") == expected_text:
                        hit = True
                elif "contains(@text" in value:
                    match_sub = re.search(r"contains\(@text,\s*['\"]([^'\"]+)['\"]\)", value)
                    if match_sub:
                        sub = match_sub.group(1)
                        if sub in attrs.get("text", "") or sub in attrs.get("originalText", ""):
                            hit = True
                elif "@id=" in value:
                    expected_id = value.split("@id=")[1].strip("'\" ]")
                    if attrs.get("id") == expected_id or attrs.get("key") == expected_id:
                        hit = True
                elif value.startswith("//"):
                    # 匹配 tag 类型
                    tag_name = value.strip("/[]")
                    if attrs.get("type") == tag_name:
                        hit = True
            elif by in (By.CLASS_NAME, By.TAG_NAME):
                if attrs.get("type") == value:
                    hit = True
            elif by in (By.NAME, By.LINK_TEXT):
                if attrs.get("text") == value or attrs.get("originalText") == value:
                    hit = True

            if hit:
                matched_nodes.append(node)

            for child in node.get("children", []):
                search_node(child)

        search_node(layout_root)
        return [HarmonyWebElement(self, n) for n in matched_nodes]

    def find_element(self, by: By, value: str) -> HarmonyWebElement:
        """查找单一元素，若未找到则抛出 NoSuchElementException"""
        elements = self.find_elements(by, value)
        if not elements:
            raise NoSuchElementException(f"在鸿蒙界面中无法通过 {by}='{value}' 定位到元素")
        return elements[0]

    def get_screenshot_as_file(self, filename: str) -> bool:
        """截取当前屏幕并保存到本地"""
        os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
        remote_png = f"/data/local/tmp/screen_{int(time.time())}.png"
        self.execute_hdc_shell(f"uitest screenCap -p {remote_png}")
        # 从设备拉取到本地
        pull_cmd = f"file recv {remote_png} {os.path.abspath(filename)}"
        self.execute_hdc(pull_cmd)
        self.execute_hdc_shell(f"rm -f {remote_png}")
        return os.path.exists(filename)

    def get_screenshot_as_png(self) -> bytes:
        """截取当前屏幕并返回 PNG 二进制数据，兼容 Allure 与 pytest 自动截图钩子"""
        import tempfile
        remote_png = f"/data/local/tmp/screen_{int(time.time() * 1000)}.png"
        self.execute_hdc_shell(f"uitest screenCap -p {remote_png}")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            self.execute_hdc(f"file recv {remote_png} {tmp_path}")
            self.execute_hdc_shell(f"rm -f {remote_png}")
            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                with open(tmp_path, "rb") as f:
                    return f.read()
            return b""
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} [HarmonyDriver] 截图转 PNG 失败: {e}")
            return b""
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def back(self) -> None:
        """模拟点击系统物理返回键"""
        logger.debug(f"{LogIcon.ACTION} [HarmonyDriver] 触发系统返回键")
        self.execute_hdc_shell("uitest uiInput keyEvent 2")
        time.sleep(0.3)

    def is_healthy(self) -> bool:
        """探活鸿蒙设备与 HDC 服务状态"""
        try:
            targets = self.execute_hdc("list targets")
            if not self.udid:
                return bool(targets and "Empty" not in targets)
            return self.udid in targets
        except Exception:
            return False

    @property
    def raw_driver(self) -> "HarmonyDriver":
        """获取底层原始驱动实例"""
        return self

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 800) -> None:
        """模拟滑动操作"""
        velocity = max(200, min(40000, int(1000000 / max(1, duration))))
        self.execute_hdc_shell(f"uitest uiInput swipe {start_x} {start_y} {end_x} {end_y} {velocity}")
        time.sleep(0.3)

    def tap(self, positions: List[Tuple[int, int]], duration: Optional[int] = None) -> None:
        """点击指定位置"""
        for x, y in positions:
            self.execute_hdc_shell(f"uitest uiInput click {x} {y}")

    def quit(self) -> None:
        """退出并释放驱动会话"""
        logger.info(f"{LogIcon.SETUP} [HarmonyDriver] 退出鸿蒙测试会话 (设备: {self.udid})")
        # 保证后台进程不残留临时文件
        self.execute_hdc_shell("rm -f /data/local/tmp/dump_layout_*.json")

    @property
    def session_id(self) -> str:
        """返回当前会话唯一标识符"""
        return f"harmony_session_{self.udid or 'default'}"

    @property
    def capabilities(self) -> Dict[str, Any]:
        """返回会话 Capabilities 字典"""
        return self.caps

    @property
    def w3c(self) -> bool:
        """对齐 W3C 协议标准"""
        return True

    def implicitly_wait(self, time_to_wait: float) -> None:
        """对齐隐式等待（鸿蒙推荐配合 BasePage 显式等待，此处保留兼容实现）"""
        pass

    def get_window_size(self, windowHandle: str = "current") -> Dict[str, int]:
        """获取鸿蒙设备屏幕分辨率"""
        # 通过 wm 探测真实分辨率
        res = self.execute_hdc_shell("hidumper -s WindowManagerService -a -a")
        # 兜底默认分辨率 1080x2400
        width, height = 1080, 2400
        match = re.search(r"displayRect:\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]", res)
        if match:
            width = int(match.group(3))
            height = int(match.group(4))
        return {"width": width, "height": height}


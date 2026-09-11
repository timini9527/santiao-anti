import os
import re
import time
import allure
from typing import Union, List
from contextlib import contextmanager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from core.logger_utils import logger
from utils.except_utils import catch_exception, check_element_status, catch_elements_exception
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


# 预编译文本清理正则，避免在频繁调用的 clean_ui_text 中重复编译，提升性能
_ASCII_CONTROL_RE = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]')
_UNICODE_CONTROL_RE = re.compile(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufffc\ufffd]')


class BasePage:
    PACKAGE_ID = 'com.santiaotalk.im:id'

    def __init__(self, driver):
        self.driver = driver

    # 使用装饰器包裹，自动处理异常和日志
    @catch_exception
    def find_element(self, locator: tuple, condition: str = "visibility",
                     timeout: int = 10, raise_exception: bool = True,
                     expect_missing: bool = False) -> WebElement | None:
        """
        查找并返回元素，用于后续点击或输入
        :param timeout: 超时时间
        :param locator: 元素定位
        :param condition: 等待条件，默认等待可见('visibility')，可选存在('presence')
        :param raise_exception: 用于异常中判断，避免异常就直接结束
        :param expect_missing: 预期元素不存在 (用于断言元素不应出现的场景)
        :return:
        """
        logger.info(f"🔎 正在查找元素: {locator} (模式: {condition})")
        wait = WebDriverWait(self.driver, timeout, poll_frequency=0.2)
        # 如果这里超时报错， @catch_exception 会自动捕获、截图、写 error 日志
        if condition == "visibility":  # 等待可见
            element = wait.until(
                EC.visibility_of_element_located(locator)
            )
        elif condition == "clickable":  # 对于这种容易挂的按钮，增加一次性的抗震动处理
            element = wait.until(
                EC.element_to_be_clickable(locator)
            )
        else:  # 等待存在，但隐藏
            element = wait.until(
                EC.presence_of_element_located(locator)
            )
        return element

    @catch_elements_exception
    def find_elements(self, locator: tuple, condition: str = 'visibility', timeout: int = 10,
                      raise_exception: bool = True, expect_missing: bool = False) -> list[WebElement]:
        """
        查找并返回元素，用于后续查询判断
        :param timeout: 超时时间
        :param locator: 元素定位 tuple 格式
        :param condition:   等待条件，默认等待可见('visibility')，可选存在('presence')
        :param raise_exception: 如果没找到，是否抛出异常（设为 False 用于探测元素是否存在）
        :param expect_missing: 预期元素不存在 (用于断言元素不应出现的场景) 
        :return: 元素对象的列表。如果 raise_exception 为 False 且没找到，返回空列表 []
        """
        logger.info(f"🔎 正在查找元素: {locator} (模式: {condition})")
        wait = WebDriverWait(self.driver, timeout)
        if condition == 'visibility':
            # 注意：不使用 visibility_of_all_elements_located —— 它要求匹配到的【所有】元素都可见，
            # 长列表中只要有一个元素滚出屏幕(不可见)就会判定不满足，一直等到超时返回空。
            # 改为先用 presence 取到 DOM 中全部元素，再过滤出当前可见的，避免整体丢失。
            all_elements = wait.until(
                EC.presence_of_all_elements_located(locator)
            )
            elements = []
            for el in all_elements:
                try:
                    if el.is_displayed():
                        elements.append(el)
                except Exception:
                    # 元素在判断瞬间失效(stale)等情况，跳过即可
                    continue
        else:
            elements = wait.until(
                EC.presence_of_all_elements_located(locator)
            )
        return elements

    def is_element_exist(self, locator: tuple, timeout: int = 10, condition: str = "visibility",
                         raise_exception: bool = True, expect_missing: bool = False) -> bool:
        """
        判断元素是否存在/可见，直接返回布尔值，不中断代码流
        :param locator: 元素定位
        :param timeout: 超时时间
        :param condition: 验证条件 (visibility-可见, presence-存在DOM中)
        :param raise_exception: 保持签名兼容
        :param expect_missing: 保持签名兼容
        :return: True(存在) / False(不存在)
        """
        logger.info(f"🔎 探查元素状态: {locator} (模式: {condition}, 超时: {timeout}s)")

        elements = self.find_elements(locator=locator, timeout=timeout, condition=condition,
                                    raise_exception=raise_exception, expect_missing=expect_missing)
        is_exist = len(elements) > 0
        if is_exist:
            logger.info(f"✅ 元素存在: {locator}")
        else:
            logger.warning(f"⚠️ 元素不存在: {locator}")
        return is_exist

    def wait_until_element_disappear(self, locator: tuple, timeout: int = 10) -> bool:
        """
        等待某个元素从页面上彻底消失（用于处理加载图标、发送状态等）。
        :param locator: 定位器元组
        :param timeout: 最大等待时间
        :return: 元素成功消失返回 True，超时仍存在返回 False
        """
        try:
            logger.info(f"⏳ [Wait] 等待元素消失: {locator}")
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(
                EC.invisibility_of_element_located(locator)
            )
            return True
        except Exception:
            logger.warning(f"⚠️ [Wait] 元素在 {timeout}s 内未能从页面消失: {locator}")
            return False

    def wait_for_element(self, locator: tuple, timeout: int = 15, interval: float = 1.0,
                         text: str = None) -> bool:
        """轮询等待元素出现（用于撤回/警告/禁言等异步上屏的场景）
        与 find_element 的区别：本方法用"短超时多次轮询"而非"一次等满"，
        且恒返回 bool 不抛异常、不触发失败截图，适合赌异步时机的等待点，
        从根上替代"裸 find_element 等满 10s 静默失败 → 下一步对 None 操作崩溃"的反模式。

        :param locator: 定位器元组
        :param timeout: 总最大等待时间（秒）
        :param interval: 每轮探测间隔（秒）
        :param text: 可选，要求元素文本包含此子串才算命中（用于等"特定内容"的消息）
        :return: 命中返回 True，超时未命中返回 False
        """
        logger.info(f"⏳ [Wait] 轮询等待元素出现: {locator} (总超时 {timeout}s, 间隔 {interval}s"
                    f"{', 文本含 ' + repr(text) if text else ''})")
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                elements = self.driver.find_elements(*locator)
                for el in elements:
                    if text is None:
                        logger.info(f"✅ [Wait] 已检测到目标元素: {locator}")
                        return True
                    if text in (el.text or ""):
                        logger.info(f"✅ [Wait] 已检测到包含文本【{text}】的元素")
                        return True
            except Exception:
                # 探测期间的 stale / 查找异常都忽略，继续下一轮轮询
                pass
            time.sleep(interval)
        logger.warning(f"⚠️ [Wait] 等待 {timeout}s 仍未检测到目标元素: {locator}"
                       f"{'（文本含 ' + repr(text) + '）' if text else ''}")
        return False


    @allure.step("获取元素属性值")
    def get_attribute(self, locator: tuple, attr: str, timeout: int = 2, raise_exception: bool = True, expect_missing: bool = False) -> str:
        """
        获取元素指定属性值
        :param locator: 元素定位 (AppiumBy.ID, "xxx")
        :param attr: 属性名，例如 "text"、"checked"、"enabled"
        :return: 属性值（字符串）
        """
        logger.info(f"🔎 获取元素属性: {locator} -> attr='{attr}'")
        element = self.find_element(locator, timeout=timeout, raise_exception=raise_exception, expect_missing=expect_missing)
        if element is not None:
            value = element.get_attribute(attr)
            logger.info(f"✅ base - 属性获取成功: {attr} = {value}")
            return value
        return ""

    @allure.step("点击元素: {locator}")
    def click(self, locator: tuple, force_wait: bool = False, timeout: int = 10) -> None:
        """
        点击元素，支持通过 force_wait 切换等待条件以解决点击无效或遮挡问题
        :param locator: 元素定位元组
        :param force_wait: 为 True 时使用 'clickable'，否则使用 'visibility'
        :param timeout: 超时时间
        """
        condition = "clickable" if force_wait else "visibility"
        element = self.find_element(locator, condition=condition, timeout=timeout)
        if element:
            logger.info(f"🖱️ 以 {condition} 模式点击元素: {locator}")
            element.click()
        else:
            logger.error(f"❌ 点击失败，未找到元素: {locator}")
            raise NoSuchElementException(f"无法点击，元素未找到: {locator}")

    @allure.step("input -> 输入文本: {text}")
    def send_keys(self, locator, text):
        ele = self.find_element(locator)
        if not ele:
            logger.warning(f"未找到元素: {locator}")
            raise NoSuchElementException(f"未找到元素: {locator}")
        ele.clear()
        ele.send_keys(text)
        logger.info(f"[Action] 输入消息: {text}")

    @catch_exception
    @allure.step("input -> W3C ActionChains 物理键盘事件流输入: {text}")
    def send_keys_by_actions(self, target: Union[tuple, WebElement], text: str, clear: bool = True, timeout: int = 10) -> bool:
        """
        使用 W3C ActionChains 事件链模拟真实物理键盘按键输入流。
        能 100% 触发 App 前端的 KeyListener、InputFilter 和 TextWatcher 拦截器。
        :param target: 元素定位元组 (AppiumBy.ID, "xx") 或已定位的 WebElement 对象
        :param text: 待输入的文本内容
        :param clear: 是否在输入前先清空已有内容
        :param timeout: 元素查找超时时间
        :return: 输入成功返回 True
        """
        ele = target if isinstance(target, WebElement) else self.find_element(target, timeout=timeout)
        if not ele:
            logger.error(f"❌ 物理按键输入失败，未找到元素: {target}")
            raise NoSuchElementException(f"无法输入，元素未找到: {target}")
        if clear:
            try:
                ele.clear()
            except Exception:
                pass
        ActionChains(self.driver).click(ele).send_keys(text).perform()
        logger.info(f"⌨️ [Action] ActionChains 物理键盘按键输入成功: {text}")
        return True

    @allure.step("input -> 极速内存注入文本: {text}")
    def fast_send_keys(self, locator, text):
        """
        利用 Appium 底层 replaceElementValue 接口直接内存注入文本。
        绕过输入法模拟按键，速度极快（瞬发），且 100% 避免高频输入下的输入法假死/崩溃。
        """
        ele = self.find_element(locator)
        if not ele:
            logger.warning(f"未找到元素: {locator}")
            raise NoSuchElementException(f"未找到元素: {locator}")
        self.driver.execute_script("mobile: replaceElementValue", {"elementId": ele.id, "text": text})
        logger.info(f"[Action] 极速注入文本成功: {text}")


    @allure.step("智能UI安全返回")
    def back(self, prefer_ui: bool = True):
        """
        标准智能安全返回（以应用 UI 导航栈为绝对核心）：
        1. 软键盘抑制：若软键盘处于开启状态，先行收起，防止遮挡。
        2. UI 按钮精准回退：极速定位并点击页面顶部左上角 UI 返回按钮（精准回退 Fragment 栈）。
        3. 系统返回极简兜底：若未找到 UI 按钮，仅在必要时执行一次系统返回。
        """
        # 1. 软键盘静默收起防遮挡
        # try:
        #     if hasattr(self.driver, "is_keyboard_shown") and self.driver.is_keyboard_shown():
        #         self.driver.hide_keyboard()
        #         time.sleep(0.2)
        # except Exception:
        #     pass

        # 1. 优先执行系统返回 driver.back()
        try:
            self.driver.back()
            logger.info("🔙 [Action] 执行系统返回 driver.back()")
            time.sleep(0.3)
            return
        except Exception as e:
            logger.warning(f"⚠️ [Back] 系统返回未响应或执行失败: {e}")

        # 2. 兜底点击页面内 UI 返回组件
        # if prefer_ui:
        #     try:
        #         pkg = CommonLocator.PACKAGE_ID
        #         unified_xpath = (
        #             f"//*[("
        #             f"@resource-id='{pkg}/back' or "
        #             f"@resource-id='{pkg}/iv_back' or "
        #             f"@resource-id='{pkg}/action_back' or "
        #             f"@resource-id='{pkg}/ps_iv_left_back' or "
        #             f"@resource-id='{pkg}/back_bnt' or "
        #             f"@content-desc='返回' or "
        #             f"@content-desc='转到上一层级' or "
        #             f"@content-desc='Navigate up' or "
        #             f"@text='返回'"
        #             f") and (not(@clickable) or @clickable='true')]"
        #         )
        #         elems = self.driver.find_elements(AppiumBy.XPATH, unified_xpath)
        #         for elem in elems:
        #             if elem.is_displayed():
        #                 elem.click()
        #                 logger.info(f"🔙 [Action] 成功点击 UI 返回组件: {elem.get_attribute('resource-id') or elem.get_attribute('content-desc')}")
        #                 time.sleep(0.4)
        #                 return
        #     except Exception:
        #         pass

    @allure.step("匹配所有 Toast 弹窗")
    def toast_message(self, expected_toast: str = "", timeout: float = 3.0) -> str:
        """
        获取当前屏幕上显示的任意 Toast 文本的内容 (直接调用高稳定性 get_toast)
        """
        return self.get_toast(expected_toast=expected_toast, timeout=timeout)
    
    @allure.step("获取当前屏幕匹配所有 Toast 弹窗内容")
    def get_toast(self, expected_toast: str = "", timeout: float = 3.0) -> Union[str, bool]:
        """
        获取当前屏幕上显示的任意 Toast 文本的内容 (支持 XML + OCR 降级双通道检测)
        :param expected_toast: 期望的 Toast 内容。为空时返回捕获到的文本字符串；不为空时返回布尔值(True/False)。
        :param timeout: 超时时间（秒）
        """
        from utils.cv_recognition.ocr_utils import OcrUtils

        locator = CommonLocator.TOAST_MSG
        logger.info(f"⏳ 开始监听提示框 (期望值: '{expected_toast}', 超时: {timeout}s)")
        
        # 1. 优先通道：XML 定位器快速轮询探测
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                element = WebDriverWait(self.driver, 0.4, 0.05).until(
                    EC.presence_of_element_located(locator)
                )
                try:
                    toast_text = element.text
                except Exception:
                    try:
                        toast_text = element.get_attribute("text")
                    except Exception:
                        toast_text = ""
                
                if toast_text:
                    if expected_toast:
                        if expected_toast in toast_text:
                            logger.info(f"✅ basePage-get_toast XML 成功捕获预期提示框: {toast_text}")
                            return True
                        else:
                            logger.debug(f"XML 捕获到无关提示框: {toast_text}，继续监听期望值: '{expected_toast}'")
                    else:
                        logger.info(f"✅ basePage-get_toast XML 成功捕获提示框: {toast_text}")
                        return toast_text
            except Exception:
                pass
            time.sleep(0.05)
            
        # 2. 兜底通道：当 XML 快速轮询结束后，如果指定了 expected_toast 且未能在 XML 中捕获，才执行一次 OCR 降级扫描
        if expected_toast:
            logger.info("⏳ XML 快速探测结束，未匹配到目标，开始执行 OCR 兜底扫描...")
            try:
                ocr = OcrUtils(self.driver)
                ocr_list = ocr.get_all_text()
                # 优化点：避免全局文本无间隔拼接引发误判，改为遍历每一行进行匹配
                if any(expected_toast in text for text in ocr_list):
                    logger.info(f"🎯 basePage-get_toast OCR 成功匹配到屏幕提示文字: '{expected_toast}'")
                    return True
            except Exception as e:
                logger.debug(f"OCR 提示框扫描异常: {e}")
                
        logger.warning(f"⏱️ basePage-get_toast 未能捕获到预期【{expected_toast}】的提示框 (XML和OCR通道均未命中)")
        return False if expected_toast else ""

    @allure.step("获取 Toast 弹窗文本")
    def get_toast_text(self, timeout: float = 3.0) -> str:
        """
        监听并获取当前屏幕上显示的任意 Toast 提示框的文本内容（确保仅返回 str）。
        :param timeout: 超时时间（秒）
        :return: 捕获到的 Toast 文本；若超时未命中，则返回空字符串 ""
        """
        res = self.get_toast(expected_toast="", timeout=timeout)
        if isinstance(res, str):
            return res
        return ""

    @allure.step("校验 Toast 弹窗是否存在")
    def verify_toast_exist(self, expected_toast: str, timeout: float = 3.0) -> bool:
        """
        在指定时间内校验是否存在包含指定期望文本的 Toast 弹窗（确保仅返回 bool）。
        :param expected_toast: 期望的 Toast 文本内容
        :param timeout: 超时时间（秒）
        :return: 存在且匹配返回 True，超时未命中返回 False
        """
        if not expected_toast:
            return False
        res = self.get_toast(expected_toast=expected_toast, timeout=timeout)
        return bool(res)


    @allure.step("轮询等待指定元素的文本符合预期条件")
    def wait_for_element_text(self, locator: tuple, expected_text: Union[str, list, tuple],
                                 timeout: float = 10.0, raise_exception: bool = True,
                                 poll_frequency: float = 0.2) -> bool:
        """
        通用底层函数：在指定时间内轮询探测元素的 text 文本，直至匹配预期条件
        :param locator: 定位器元组 (By, value)
        :param expected_text: 期望的文本（支持单字符串、或包含多个可选值的列表/元组）
        :param timeout: 超时时间（秒）
        :param raise_exception: 是否在超时未匹配时抛出异常
        :param poll_frequency: 轮询探测频率（秒）
        :return: 匹配成功返回 True，超时未匹配返回 False
        """
        end_time = time.time() + timeout
        expected_list = [expected_text] if isinstance(expected_text, str) else expected_text

        while time.time() < end_time:
            try:
                text = self.get_attribute(locator, "text", timeout=poll_frequency, raise_exception=raise_exception)
                if text:
                    for exp in expected_list:
                        if exp in text:
                            logger.info(f"✅ [BasePage-wait_element_text] 成功匹配文本: '{text}' (预期包含: '{exp}')")
                            return True
            except Exception:
                pass
            time.sleep(poll_frequency)

        if raise_exception:
            logger.error(f"❌ [BasePage-wait_element_text] 超时 {timeout}s 未等到 {locator} 匹配文本: {expected_text}")
        else:
            logger.warning(f"⚠️ [BasePage-wait_element_text] 未在 {timeout}s 内匹配到文本: {expected_text} (探测判定不存在)")
        return False


    @allure.step("获取网格/列表布局指标")
    def get_grid_layout_metrics(self, container_locator: tuple, item_locator: tuple) -> dict:
        """
        计算容器与网格元素的布局指标。
        :param container_locator: 容器定位符
        :param item_locator: 列表/网格内单个元素的定位符
        :return: 包含布局元数据的字典
        """
        logger.info(f"🔎 正在计算布局指标: 容器={container_locator}, 元素={item_locator}")
        try:
            container = self.find_element(container_locator, 'visibility', timeout=2)
            item = self.find_element(item_locator, 'visibility', timeout=2)
            
            if not container or not item:
                logger.warning("未能获取到足够的元素进行布局计算")
                return {}

            c_rect = container.rect
            i_rect = item.rect
            
            # 核心几何计算
            pkg_per_row = c_rect['width'] // i_rect['width']
            pkg_per_col = c_rect['height'] // i_rect['height']
            stride_y = int(i_rect['height'] * 1.05)             # 默认 5% 的步进冗余
            
            metrics = {
                "container_rect": c_rect,                   # 容器整体的尺寸和屏幕坐标 (x, y, width, height)
                "item_rect": i_rect,                        # 单个子元素的尺寸和屏幕坐标 (x, y, width, height)
                "item_height": i_rect['height'],            # 单个子元素的高度（像素）
                "item_width": i_rect['width'],              # 单个子元素的宽度（像素）
                "pkg_per_row": pkg_per_row,                 # 网格中每一行能容纳的元素个数
                "pkg_per_col": pkg_per_col,                 # 网格中每一列能容纳的元素个数（即一屏显示多少行）
                "max_per_screen": pkg_per_row * pkg_per_col,# 满屏状态下最多能显示的元素总数
                "stride_y": stride_y,                       # 滑动一行的基准距离（已包含 5% 的行间距冗余）
                "container_top_y": c_rect['y']              # 容器的顶部 Y 坐标（用于判断第一排元素是否被顶部遮挡/裁切）
            }
            logger.info(f"✅ 布局指标计算完成: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"❌ 布局指标计算失败: {e}")
            return {}

    @allure.step("获取元素中心点坐标")
    def get_element_center(self, element: WebElement) -> tuple[int, int]:
        """
        获取元素的中心点坐标
        :param element: 目标元素
        :return: (x, y) 坐标元组
        """
        rect = element.rect
        return int(rect['x'] + rect['width'] / 2), int(rect['y'] + rect['height'] / 2)
    
    @allure.step("通过坐标进行点击: {x}, {y}")
    def click_by_coordinate(self, x: int | float, y: int | float):
        """ 点击固定坐标 """
        self.driver.tap([(x, y)])
        logger.info(f"[Action] 通过坐标进行点击，点击坐标: {x}, {y}")


    @allure.step("长按元素，获取弹窗")
    @allure.step("有多条数据存在时, 长按某一条, 获取弹窗")
    def long_press_action(self, found_ele: WebElement, hold_time: int = 1000):
        """
        长按元素，兼容 Appium 原生 longClickGesture 与 W3C Action 坐标长按
        """
        try:
            # 1. 优先使用 Appium 原生的 longClickGesture 绕过 USB 模拟限制与坐标序列化错误
            self.driver.execute_script(
                'mobile: longClickGesture',
                {'elementId': found_ele.id, 'duration': hold_time}
            )
            logger.info("✅ [Gesture] 使用 Appium 原生 longClickGesture 成功长按元素")
        except Exception as e:
            logger.warning(f"⚠️ [Gesture] Appium 原生 longClickGesture 失败: {e}，尝试 W3C Action 坐标长按")
            # 2. 备用方案：采用精准中心点坐标的 W3C Action 链，规避越界报错
            try:
                x, y = self.get_element_center(found_ele)
                actions = ActionBuilder(self.driver)
                finger = PointerInput(interaction.POINTER_TOUCH, "finger")
                actions.add_device(finger)

                actions.pointer_action.move_to_location(x, y)
                actions.pointer_action.pointer_down()
                actions.pointer_action.pause(hold_time / 1000.0)
                actions.pointer_action.pointer_up()
                actions.perform()
                logger.info("✅ [Gesture] 使用 W3C Action 坐标长按成功")
            except Exception as w3c_err:
                logger.error(f"❌ [Gesture] 长按操作彻底失败: {w3c_err}")
                raise w3c_err
        time.sleep(0.5)

        # logger.info(f"长按元素,获取弹窗完成: {el}")
        # print(f"长按元素,获取弹窗完成: {actions}")
        # print(f"长按元素,获取弹窗完成: {finger}")

    @allure.step("初始化 W3C 动作链及触控笔输入源")
    def init_w3c_actions(self) -> tuple[ActionChains, PointerInput]:
        """
        初始化 W3C 动作链及触控笔输入源
        1. 初始化基础动作链对象
        2. 创建一个触控类型的指针输入源，并命名为 "finger"
        3. 通过 ActionBuilder 将触控输入源绑定到动作链的 w3c_actions 属性中
        :return: ActionChains 和 PointerInput 对象
        """
        actions = ActionChains(self.driver)
        touch_input = PointerInput(interaction.POINTER_TOUCH, "finger")
        actions.w3c_actions = ActionBuilder(self.driver, mouse=touch_input)
        return actions, touch_input

    @allure.step("在指定坐标按下并悬停")
    def pointer_down_and_hold(self, actions: ActionChains, x: int, y: int, duration: float = 1.0):
        """
        在指定坐标按下并悬停
        :param actions: ActionChains 对象（需已初始化好 w3c_actions）
        :param x: X坐标
        :param y: Y坐标
        :param duration: 悬停时间（秒）
        """
        actions.w3c_actions.pointer_action.move_to_location(x, y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(duration)
        actions.perform()

    @allure.step("在指定坐标抬起手指")
    def pointer_up_at_location(self, touch_input: PointerInput, x: int, y: int):
        """
        在指定坐标抬起手指（释放触控）
        :param touch_input: 初始化时使用的 PointerInput 对象
        :param x: 当前手指所在的 X 坐标
        :param y: 当前手指所在的 Y 坐标
        """
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(self.driver, mouse=touch_input)
        # 必须先移动到当前坐标，防止 InvalidArgumentException
        actions.w3c_actions.pointer_action.move_to_location(x, y)
        actions.w3c_actions.pointer_action.pointer_up()
        actions.perform()

    @allure.step("执行滑动操作，A->B 任意区域")
    def perform_gesture(self, start_elem, end_elem):
        """
        执行滑动操作，从 A->B 任意区域
        :param start_elem: 起始元素
        :param end_elem: 结束元素
        """
        # 起点 (计算麦克风中心点)
        start_x, start_y = self.get_element_center(start_elem)
        
        # 终点 (计算试听区域中心点)
        end_x, end_y = self.get_element_center(end_elem)

        actions, touch_input = self.init_w3c_actions()
        
        # 步骤 A：手指移动到麦克风并按下
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.pause(5) # 按住麦克风 0.5 秒录点声音
        
        # 步骤 B：手指滑动到试听区域 (假设用 0.5 秒滑过去)
        # 注意：如果直线滑过去会触发"上滑取消"，可能需要拐弯滑，根据实际App交互调整
        actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
        
        # 步骤 C：【核心】在试听区域上方悬停停顿 3 秒！(给主线程留出抓取 UI 的时间)
        actions.w3c_actions.pointer_action.pause(3.0) 
        
        # 步骤 D：松开手指
        actions.w3c_actions.pointer_action.pointer_up()
        
        # 执行整套动作
        actions.perform()
    
    @allure.step("W3C 标准的坐标强点 (模拟人类手指真实触摸)")
    def tap_point(self, click_elem: WebElement = None, x: float = None, y: float = None, duration: int = 300):
        """
        [W3C 标准] 模拟手指触摸指定坐标点 (模拟人类手指真实触摸)
        :param click_elem: 点击元素（如果传入，将自动计算元素的中心点坐标）
        :param x: 目标点的 X 坐标（在不传入 click_elem 时必须提供）
        :param y: 目标点的 Y 坐标（在不传入 click_elem 时必须提供）
        :param duration: 持续时间，毫秒
        """
        try:
            if click_elem:
                # 1. 获取元素的坐标矩形区域 (x, y, width, height)
                rect = click_elem.rect
                # 2. 计算元素的中心点坐标
                center_x = rect['x'] + rect['width'] / 2
                center_y = rect['y'] + rect['height'] / 2
            elif x is not None and y is not None:
                center_x = x
                center_y = y
            else:
                logger.error("❌ 坐标强点失败: 必须提供 click_elem 或者具体的 (x, y) 坐标参数")
                return

            logger.info(f"👉 模拟手指点击屏幕坐标: ({center_x}, {center_y})")

            # 3. 使用 W3C ActionChains 执行物理点击 (兼容 Appium 2.x)
            actions, touch_input = self.init_w3c_actions()
            actions.w3c_actions.pointer_action.move_to_location(center_x, center_y)
            actions.w3c_actions.pointer_action.pointer_down()
            actions.w3c_actions.pointer_action.pause(duration / 1000.0)  # 稍微停顿，防止点太快系统没反应
            actions.w3c_actions.pointer_action.pointer_up()
            actions.perform()

            logger.info("✅ 坐标强点执行完毕")

        except Exception as e:
            logger.warning(f"坐标强点失败，尝试退回原生 click() 兜底: {e}")
            if click_elem:
                click_elem.click()
    
    @allure.step("检查页面 DOM 是否发生变化")
    def is_page_source_changed(self, last_source: str) -> tuple[bool, str]:
        """
        判断页面 DOM 是否有变化 (用于控制滑动翻页结束)
        :param last_source: 上一次的 page_source
        :return: (是否有变化, 最新的 source)
        """
        current_source = self.driver.page_source
        is_changed = True
        if last_source:
            is_changed = (current_source != last_source)
            logger.info(f"页面 DOM 是否发生变化: {is_changed}")
            if not is_changed:
                logger.info("✅ 页面 DOM 已无变化，认定已至边界！")
        return is_changed, current_source

    @allure.step("检查指定区域的 DOM 是否发生变化")
    def is_element_source_changed(self, locator: tuple, last_element_source: str) -> tuple[bool, str]:
        """
        判断指定区域的内容/布局是否有变化 (用于控制滑动翻页结束)。
        [优化重构]：优先采用轻量级子元素属性与坐标签名算法，避免每次都获取并全量解析整页 XML。
        若获取子元素异常，自动降级回退到 XML 全量解析兜底。
        """
        # 1. 尝试使用极速子元素状态签名方式 (首选，耗时约 50ms)
        try:
            child_loc = None
            if locator[0] == AppiumBy.ID:
                child_loc = (AppiumBy.XPATH, f'//*[@resource-id="{locator[1]}"]/*')
            elif locator[0] == AppiumBy.XPATH:
                base_xpath = locator[1].rstrip('/')
                child_loc = (AppiumBy.XPATH, f'{base_xpath}/*')

            if child_loc:
                elements = self.find_elements(child_loc, timeout=2, raise_exception=False, expect_missing=True)
                features = []
                for el in elements:
                    try:
                        text = el.text or ""
                        res_id = el.get_attribute("resource-id") or ""
                        y = el.rect.get("y", 0)
                        features.append(f"{res_id}_{text}_{y}")
                    except Exception:
                        pass
                if features:
                    signature = "|".join(features)
                    is_changed = (signature != last_element_source) if last_element_source else True
                    logger.info(f"⚡ [Fast Detection] 区域子元素状态是否变化: {is_changed} (签名长度: {len(signature)})")
                    return is_changed, signature
        except Exception as fast_err:
            logger.debug(f"极速节点状态特征计算失败: {fast_err}，将使用全量 XML 降级兜底...")

        # 2. 降级兜底：获取 page_source 并做 XML 局部解析 (耗时约 1500-3000ms)
        import xml.etree.ElementTree as ET
        full_source = self.driver.page_source
        try:
            root = ET.fromstring(full_source.encode('utf-8'))
            target_node = None
            if locator[0] == AppiumBy.ID:
                target_id = locator[1]
                for node in root.iter():
                    if node.get('resource-id') == target_id:
                        target_node = node
                        break
            elif locator[0] == AppiumBy.XPATH:
                xpath_expr = locator[1]
                if xpath_expr.startswith('//'):
                    xpath_expr = '.' + xpath_expr
                elif xpath_expr.startswith('/'):
                    xpath_expr = '.' + xpath_expr
                
                try:
                    target_node = root.find(xpath_expr)
                except Exception:
                    import re
                    match = re.search(r"@resource-id=['\"]([^'\"]+)['\"]", locator[1])
                    if match:
                        res_id = match.group(1)
                        for node in root.iter():
                            if node.get('resource-id') == res_id:
                                target_node = node
                                break

            if target_node is not None:
                current_element_source = ET.tostring(target_node, encoding='unicode')
                is_changed = (current_element_source != last_element_source) if last_element_source else True
                return is_changed, current_element_source
            else:
                logger.warning(f"在当前 DOM 中未找到目标区域: {locator}")
                return True, ""
                
        except Exception as e:
            logger.error(f"降级提取指定区域 XML 失败: {e}")
            return True, ""


    @allure.step("执行滑动操作")
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500, toptime: int = 50):
        """
        核心滑动执行器 (W3C 标准)
        :param duration: 滑动持续时间，默认500毫秒
        :param toptime: 按下起点后的短暂贴合停顿时间(ms)，默认50毫秒（严防触发 Android 500ms 长按阈值）
        """
        try:
            logger.info(f"滑动轨迹: ({start_x}, {start_y}) -> ({end_x}, {end_y}) | 时长: {duration}ms | 贴合: {toptime}ms")
            actions, touch_input = self.init_w3c_actions()

            # 动作序列: 移动至起点 -> 按下 -> 短暂停顿贴合 -> 平滑移动至终点 -> 终点停顿120ms(初速度归零杀死Fling惯性) -> 抬起手指
            touch_input.create_pointer_move(x=start_x, y=start_y, duration=0, origin="viewport")
            touch_input.create_pointer_down(button=0)
            touch_input.create_pause(toptime / 1000) 
            touch_input.create_pointer_move(x=end_x, y=end_y, duration=duration, origin="viewport")
            touch_input.create_pause(0.2)  # 强制将抬手瞬间加速度归零，彻底杀死列表抛滑(Fling)惯性
            touch_input.create_pointer_up(button=0)
            actions.perform()
            time.sleep(0.1)
        except Exception as e:
            logger.error(f"滑动操作失败: {e}")
            raise RuntimeError(f"执行手指手势操作失败: {str(e)}")

    @allure.step("在指定的坐标边界内容固定按预定距离滑动")
    def swipe_to_distance(self, slid_type: str = "up", rect: dict = None, duration: int = 300, times: int = 1, x_ratio: float = 0.5, y_ratio: float = 0.5, toptime: int = 50) -> None:
        """
        在指定字典区域的边界内计算滑动（预留 20% 安全区防误触）
        :param slid_type: 'up'(手指上滑) / 'down'(手指下滑) / 'left'(手指左滑) / 'right'(手指右滑)
        :param x_ratio: 纵向滑动时，X轴位置占区域宽度的比例，默认 0.5
        :param y_ratio: 横向滑动时，Y轴位置占区域高度的比例，默认 0.5
        :param toptime: 按下贴合停顿时间(ms)，默认50ms
        """
        if not rect:
            return

        x, y, w, h = rect['x'], rect['y'], rect['width'], rect['height']
        
        target_x = int(x + w * x_ratio)
        target_y = int(y + h * y_ratio)

        # 构建防越界安全隔离区(20% ~ 80%)
        top_y = int(y + h * 0.2)
        bottom_y = int(y + h * 0.8)
        left_x = int(x + w * 0.2)
        right_x = int(x + w * 0.8)

        for _ in range(times):
            if slid_type.lower() == "up":      # 手指从下往上滑，页面下降
                start_x, start_y, end_x, end_y = target_x, bottom_y, target_x, top_y
            elif slid_type.lower() == "down":  # 手指从上往下滑，页面上升
                start_x, start_y, end_x, end_y = target_x, top_y, target_x, bottom_y
            elif slid_type.lower() == "left":  # 手指从右向左滑，页面向左移
                start_x, start_y, end_x, end_y = right_x, target_y, left_x, target_y
            elif slid_type.lower() == "right": # 手指从左向右滑，页面向右移
                start_x, start_y, end_x, end_y = left_x, target_y, right_x, target_y
            else:
                raise ValueError(f"不支持的滑动方向: {slid_type}")

            self.swipe(start_x, start_y, end_x, end_y, duration, toptime=toptime)
    
    @allure.step("屏幕全局滑动")
    def swipe_page(self, slid_type: str = 'up', duration: int = 500, times: int = 1, x_ratio: float = 0.5, y_ratio: float = 0.5, toptime: int = 50):
        """ 全屏滑动：封装成全屏尺寸后转交 swipe_to_distance 处理 """
        size = self.driver.get_window_size()
        rect = {'x': 0, 'y': 0, 'width': size['width'], 'height': size['height']}
        self.swipe_to_distance(slid_type=slid_type, rect=rect, duration=duration, times=times, x_ratio=x_ratio, y_ratio=y_ratio, toptime=toptime)

    @allure.step("元素内局域滑动")
    def swipe_on_element(self, element, slid_type: str = "left", duration: int = 600, toptime: int = 50):
        """ 元素内滑动：提取元素物理 rect 后转交 swipe_to_distance 处理 """
        if element is None:
            raise ValueError("必须提供有效的元素对象")
        self.swipe_to_distance(slid_type=slid_type, rect=element.rect, duration=duration, times=1, toptime=toptime)

    @allure.step("以指定固定区域(rect)的偏移中心点为起滑基准，按给定的 X/Y 偏移量进行精确滑动")
    def swipe_by_offset(self, rect: dict, start_x_offset: int = 0, start_y_offset: int = 0, 
                        x_offset: int = 0, y_offset: int = 0, duration: int = 500, toptime: int = 50):
        """
        以指定固定区域(rect)的中心点（叠加起始偏移）为起滑基准，按给定的 X/Y 偏移量进行精确滑动。
        :param rect: 固定的安全容器边界字典 {'x':., 'y':., 'width':., 'height':.}
        :param start_x_offset: 起点相对于容器中心点的 X 轴偏移量（正数向右，负数向左）
        :param start_y_offset: 起点相对于容器中心点的 Y 轴偏移量（正数向下，负数向上）
        :param x_offset: X轴手指偏移量（负数=手指左移/页面右偏，正数=手指右移/页面左偏）
        :param y_offset: Y轴手指偏移量（负数=手指上移/页面下偏，正数=手指下移/页面上偏）
        :param duration: 滑动动作耗时(ms)
        :param toptime: 按下贴合停顿时间(ms)，默认50ms
        """
        if not rect:
            raise ValueError("必须提供有效的安全区域 rect (如容器元素的 rect)")
            
        if x_offset == 0 and y_offset == 0:
            logger.warning("滑动被忽略：x_offset 和 y_offset 均为 0")
            return

        # 1. 计算滑动起点：取传入容器中心点并累加起始偏移量，防止触发系统手势
        start_x = int(rect['x'] + rect['width'] * 0.5) + start_x_offset
        start_y = int(rect['y'] + rect['height'] * 0.5) + start_y_offset
        
        # 2. 根据精确偏移量计算终点坐标
        end_x = start_x + x_offset
        end_y = start_y + y_offset
        
        # 3. 边界防溢出保护
        size = self.driver.get_window_size()
        max_x, max_y = size['width'], size['height']
        
        # 限制起点和终点坐标均在屏幕内，留 5px 的安全边距
        start_x = max(5, min(start_x, max_x - 5))
        start_y = max(5, min(start_y, max_y - 5))
        end_x = max(5, min(end_x, max_x - 5))
        end_y = max(5, min(end_y, max_y - 5))

        self.swipe(start_x, start_y, end_x, end_y, duration, toptime=toptime)
        time.sleep(0.08)

    @allure.step("极速滑动与状态检测(刷底/刷顶)")
    def swipe_page_quickly(self, element=None, slid_type: str = "down", duration: int = 100, max_swipes: int = 10, item_locator: tuple | None = None, toptime: int = 50):
        """ 智能边界嗅探：不停滑动直到 DOM (page_source) 或列表条目停止变化 """
        if isinstance(element, str):
            slid_type = element
            element = None
        logger.info(f"极速滑动自动探测边界启动 (Max:{max_swipes}次)")
        previous_source = ""
        previous_items_text = []
        
        for i in range(max_swipes):
            # 1. 优先采用列表条目指纹比对（100% 免疫阻尼回弹坐标抖动）
            if item_locator:
                elems = self.find_elements(item_locator, timeout=1, expect_missing=True)
                current_items_text = [e.text for e in elems if e.text]
                if i > 0 and current_items_text and current_items_text == previous_items_text:
                    logger.info(f"✅ [Swipe] 列表条目指纹无变化，确认已触达边界 (滑动次数: {i})")
                    break
                previous_items_text = current_items_text
            else:
                is_changed, previous_source = self.is_page_source_changed(previous_source)
                if not is_changed:
                    break
            if element:
                self.swipe_on_element(element=element, slid_type=slid_type, duration=duration, toptime=toptime)
            else:
                self.swipe_page(slid_type=slid_type, duration=duration, times=1, toptime=toptime)
            time.sleep(0.2)
        else:
            logger.warning(f"⚠️ 滑满上限({max_swipes}次)仍见变化，强制挂起停止")

    @allure.step("智能滚动查找指定元素")
    def scroll_to_element(
        self,
        locator: tuple,
        container: WebElement = None,
        max_swipes: int = 5,
        slid_type: str = "up",
        duration: int = 400,
        toptime: int = 50
    ) -> WebElement | None:
        """
        [通用动作] 智能滚动查找元素：先探测当前视口，未找到则沿指定方向平滑滑动查找
        :param locator: 元素定位符元组 (By, value)
        :param container: 可选的局域滑动容器 WebElement 对象（若为 None 则默认全屏滑动）
        :param max_swipes: 最大滑动查找次数，默认 5 次
        :param slid_type: 滑动方向 ('up': 手指上滑/页面下移, 'down': 手指下滑/页面上移)
        :param duration: 每次滑动动作耗时(ms)，默认 400ms
        :param toptime: 按下起点贴合停顿时间(ms)，默认 50ms
        :return: 找到的 WebElement 对象，若未找到返回 None
        """
        element = self.find_element(locator, timeout=1, raise_exception=False, expect_missing=True)
        if element:
            return element

        for i in range(max_swipes):
            if container:
                self.swipe_on_element(container, slid_type=slid_type, duration=duration, toptime=toptime)
            else:
                self.swipe_page(slid_type=slid_type, duration=duration, times=1, toptime=toptime)
            time.sleep(0.3)
            element = self.find_element(locator, timeout=1, raise_exception=False, expect_missing=True)
            if element:
                logger.info(f"🔍 [Scroll] 滑动第 {i + 1} 次成功找到元素: {locator}")
                return element

        logger.warning(f"⚠️ [Scroll] 滑动 {max_swipes} 次后仍未找到目标元素: {locator}")
        return None

    @allure.step("按键操作: 触发物理/软键盘按键")
    def press_keycode(self, keycode: int = 66, input_locator=None) -> bool:
        """
        [通用动作] 模拟发送物理/软键盘 Keycode 按键 (默认 66 为 ENTER/SEARCH 键，4 为 BACK 返回键)
        :param keycode: Android 按键码 (66: ENTER/搜索, 4: BACK/返回, 67: DELETE/退格 等)
        :param input_locator: 输入框定位符 (iOS/Web 兼容回落模式)
        """
        try:
            # 方式 A: Appium Android 原生 press_keycode
            if hasattr(self, 'driver') and hasattr(self.driver, 'press_keycode'):
                logger.info(f"👉 使用 Android Keycode {keycode} 触发按键")
                self.driver.press_keycode(keycode)
                return True

            # 方式 B: 通用 Selenium Keys (iOS / Web 兼容回落)
            elif input_locator:
                logger.info("👉 使用 send_keys(Keys.ENTER) 触发搜索")
                element = self.find_element(*input_locator)
                element.send_keys(Keys.ENTER)
                return True

            else:
                logger.warning(f"⚠️ 无法触发 Keycode {keycode}: 当前驱动无 press_keycode 且未传入 input_locator")
                return False
        except Exception as e:
            logger.error(f"❌ 触发键盘按键 Keycode {keycode} 失败: {e}")
            raise e
    
    @allure.step("读取手机剪贴板内容")
    def paste_clipboard_text(self):
        """读取手机剪贴板内容 (Appium 原生支持)"""
        clipboard_text = self.driver.get_clipboard_text()
        logger.info(f"剪贴板读取成功: {clipboard_text}")
        return clipboard_text

    @allure.step("设置网络状态")
    def set_network_connection(self, network_status: str):
        """
        设置网络状态
        :param network_status: 网络状态 (offline/none/wifi/data/mobile/all/online)
        """
        logger.info(f"设置网络状态为: {network_status}")
        # Appium 网络连接状态码:
        # 0 (None), 1 (Airplane Mode), 2 (Wifi only), 4 (Data only), 6 (All network on)
        status_map = {
            "offline": 0,
            "none": 0,
            "data": 4,
            "mobile": 4,
            "wifi": 2,
            "all": 6,
            "online": 6
        }
        val = status_map.get(network_status.lower(), 6)
        try:
            self.driver.set_network_connection(val)
            logger.info(f"✅ 成功设置网络状态为: {network_status} ({val})")
        except Exception as e:
            logger.error(f"❌ 设置网络状态失败: {e}")

    @allure.step("设置弱网状态 (网络不好)")
    def set_weak_network(self, enable: bool = True):
        """
        设置弱网状态模拟（网络不好状态）
        :param enable: True 启用弱网模式 (GPRS/限速)，False 恢复正常网络
        """
        if enable:
            logger.info("⚡ [Network] 启用弱网环境 (网络不好)")
            try:
                self.driver.set_network_speed("gprs")
            except Exception as e:
                logger.warning(f"底层环境不支持 set_network_speed，降级为切断网络流模拟: {e}")
                self.set_network_connection("none")
        else:
            logger.info("⚡ [Network] 恢复正常全网连接")
            try:
                self.driver.set_network_speed("full")
            except Exception:
                pass
            self.set_network_connection("all")

    @allure.step("清理从 UI 获取的文本")
    def clean_ui_text(self, data: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        清理从 UI 获取的文本，去除 Appium 抓取时夹带的不可见控制字符/排版字符，保留正常文本和表情(Emoji)。
        支持处理单个字符串或字符串列表。
        :param data: 原始文本或文本列表 (例如: ['0131测试群1', '12\x12345'])
        :return: 清洗后的文本或列表 (例如: ['0131测试群1', '12345'])
        """
        # 如果传入的是列表，递归处理列表中的每一项
        if isinstance(data, list):
            return [self.clean_ui_text(item) for item in data]

        # 如果不是字符串（比如 None 或数字），直接原样返回
        if not isinstance(data, str):
            return data

        # 1. 清除 ASCII 控制字符 (如 \x00-\x1f, \x7f-\x9f)，但保留 \t, \n, \r
        # \x12 就是在这个范围内被干掉的
        cleaned_text = _ASCII_CONTROL_RE.sub('', data)

        # 2. 清除常见的 Unicode 零宽字符/排版控制字符 (这些经常在 Android UI 中引起乱码)
        cleaned_text = _UNICODE_CONTROL_RE.sub('', cleaned_text)

        # 3. 剥离可能存在的两端空白字符
        cleaned_text = cleaned_text.strip()
        return cleaned_text
    
    @allure.step("触发系统级截屏")
    def trigger_system_screenshot(self) -> bool:
        """
        触发系统级截屏
        """
        # 1. 优先尝试使用物理按键 Keycode 120 (Print Screen / SysRq) 触发系统截屏
        try:
            logger.info("🎹 尝试发送系统级 Print Screen 按键触发截屏...")
            self.driver.press_keycode(120)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"⚠️ 发送 Print Screen 键值被设备拒绝: {e}，将采用文件注入模拟方式")

        # 2. 模拟写入截图文件到标准目录，触发 App 监听的 FileObserver
        timestamp = int(time.time())
        phone_path = f"/sdcard/Pictures/Screenshots/screenshot_{timestamp}.png"
        
        logger.info("📸 正在使用 Appium 原生 push_file 写入模拟截图文件...")
        try:
            # 获取当前屏幕的 base64 数据
            screenshot_b64 = self.driver.get_screenshot_as_base64()
            # 推送到设备标准截图目录
            self.driver.push_file(phone_path, screenshot_b64)
            logger.info(f"✅ 成功模拟写入截图文件: {phone_path}")
            return True
        except Exception as e:
            logger.error(f"❌ 模拟写入截图文件失败: {e}")
            return False

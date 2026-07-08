import os
import re
import time
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
import allure
from core.logger_utils import logger
from utils.except_utils import catch_exception, check_element_status, catch_elements_exception
from appium.webdriver.common.appiumby import AppiumBy



# 预编译文本清理正则，避免在频繁调用的 clean_ui_text 中重复编译，提升性能
_ASCII_CONTROL_RE = re.compile(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]')
_UNICODE_CONTROL_RE = re.compile(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f]')


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
        wait = WebDriverWait(self.driver, timeout)
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

    @catch_exception
    def find_element_gird(self, element: WebElement, locator: tuple) -> WebElement:
        """
        在父元素内查找子元素
        :param element: 父级 WebElement 对象
        :param locator: 子元素定位器
        :return: 子级 WebElement
        """
        logger.info(f"🔎 在父元素内查找子元素: {locator}")
        child = element.find_element(*locator)
        return child

    def wait_until_element_disappear(self, locator: tuple, timeout: int = 10) -> bool:
        """
        等待某个元素从页面上彻底消失（用于处理加载图标、发送状态等）。
        :param locator: 定位器元组
        :param timeout: 最大等待时间
        :return: 元素成功消失返回 True，超时仍存在返回 False
        """
        try:
            logger.info(f"⏳ [Wait] 等待元素消失: {locator}")
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(locator)
            )
            return True
        except Exception:
            logger.warning(f"⚠️ [Wait] 元素在 {timeout}s 内未能从页面消失: {locator}")
            return False

    def wait_for_element(self, locator: tuple, timeout: int = 15, interval: float = 1.0,
                         text: str = None) -> bool:
        """轮询等待元素出现（用于撤回/警告/禁言等异步上屏的场景）。

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

    @allure.step("通过 android uiautomator 定位, ID 和 Instance 获取元素")
    def find_element_by_id_instance(self, res_id: str, index: int = 0) -> WebElement:
        """
            通过 android uiautomator 定位, ID 和 Instance 动态查找元素
        :param res_id: 完整的 resource-id，例如 'com.qq.im:id/content'
        :param index:  索引，0 代表第 1 个
        :return:
        """
        uiautomator_str = f'new UiSelector().resourceId("{res_id}").instance({index})'
        locator = (AppiumBy.ANDROID_UIAUTOMATOR, uiautomator_str)
        ele = self.find_element(locator)
        return ele

    @allure.step("通过查询子元素进行点击元素")
    def click_by_id_instance(self, res_id: str, index: int = 0):
        el = self.find_element_by_id_instance(res_id, index)
        if not el:
            logger.warning(f"通过查询子元素未找到: {res_id}")
            raise NoSuchElementException(f"通过查询子元素未找到: {res_id}")
        logger.info(f"通过查询子元素进行点击元素: {res_id}")
        el.click()

    @allure.step("通过查询子元素进行获取属性值")
    def query_attr_by_id(self, res_id: str, index: int = 0, name: str = "text") -> tuple:
        """
        通过查询子元素进行获取属性值
        :param res_id: 完整的 resource-id
        :param index: 索引，0 代表第 1 个
        :param name: 属性名
        :return: (WebElement对象, 属性值(str)) 未找到时返回 (None, "")
        """
        el = self.find_element_by_id_instance(res_id, index)
        if el is not None:
            attr = el.get_attribute(name)
            logger.info(f" 获取多个子元素 {name} 的属性值: {attr}")
            return el, attr
        return None, ""

    @allure.step("通过 xpath 定位, ID  动态查找元素")
    def find_element_by_id_xpath(self, res_id: str, index: int = 1) -> WebElement:
        """
            通过 xpath 定位, ID  动态查找元素
        :param res_id: 完整的 resource-id，例如 'com.qq.im:id/content'
        :param index:  索引，0 代表第 1 个
        """
        # 使用 * 代表任意 class (TextView, Button, EditText 等)
        xpath_str = f'(//*[@resource-id="{res_id}"])[{index}]'
        locator_xpath = (AppiumBy.XPATH, xpath_str)
        ele = self.find_element(locator_xpath)
        return ele

    @allure.step("通过 xpath 获取元素属性值")
    def query_attr_by_id_xpath(self, res_id: str, index: int = 1, name: str = "text") -> str:
        ele = self.find_element_by_id_xpath(res_id, index)
        if ele is not None:
            attr = ele.get_attribute(name)
            logger.info(f" 获取多个子元素 {name} 的属性值: {attr}")
            return attr
        return ""

    @allure.step("通过 new UiSelector().text('X') 定位 查找元素")
    def find_element_by_UiSelector_text(self, text_str: str, timeout: int = 3) -> WebElement:
        """
            通过 new UiSelector().text('X') 定位 查找元素
        :param text_str: 完整的 文本字符，例如 'new UiSelector().text("啦啦啦啦啦啦啦啦")'
        :param timeout: 查找元素超时时间
        :return 返回找到的 WebElement 对象
        """
        # 使用 * 代表任意 class (TextView, Button, EditText 等)
        UiSelector_str = f'new UiSelector().text("{text_str}")'
        locator_xpath = (AppiumBy.ANDROID_UIAUTOMATOR, UiSelector_str)
        ele = self.find_element(locator_xpath, timeout=timeout)
        return ele

    @allure.step("通过 new UiSelector().text('X') 进行 click")
    def click_by_UiSelector_text(self, text_str: str):
        ele = self.find_element_by_UiSelector_text(text_str)
        if not ele:
            logger.warning(f"未找到元素: {text_str}")
            raise NoSuchElementException(f"未找到元素: {text_str}")
        ele.click()

    @check_element_status
    def is_element_exist(self, locator: tuple, timeout: int = 10, condition: str = "visibility",
                         raise_exception: bool = True, expect_missing: bool = False) -> bool:
        """
        判断元素是否存在/可见，直接返回布尔值，不中断代码流
        :param locator: 元素定位
        :param timeout: 超时时间
        :param condition: 验证条件 (visibility-可见, presence-存在DOM中)
        :param raise_exception: 探测方法恒不抛异常，此参数仅为与 find_element/find_elements
                                保持调用签名一致而保留，传入与否均不改变行为
        :param expect_missing: 同上，探测方法不做断言，保留仅为签名兼容
        :return: True(存在) / False(不存在)
        """
        logger.info(f"🔎 探查元素状态: {locator} (模式: {condition}, 超时: {timeout}s)")
        wait = WebDriverWait(self.driver, timeout)
        if condition == "visibility":
            wait.until(EC.visibility_of_element_located(locator))
        else:
            wait.until(EC.presence_of_element_located(locator))
        return True

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

    # 点击固定坐标
    @allure.step("通过坐标进行点击: {x}, {y}")
    def click_by_coordinate(self, x, y):
        logger.info(f"[Action] 通过坐标进行点击，点击坐标: {x}, {y}")
        self.driver.tap([(x, y)])

    @allure.step("input -> 输入文本: {text}")
    def send_keys(self, locator, text):
        ele = self.find_element(locator)
        if not ele:
            logger.warning(f"未找到元素: {locator}")
            raise NoSuchElementException(f"未找到元素: {locator}")
        ele.clear()
        ele.send_keys(text)
        logger.info(f"[Action] 输入消息: {text}")


    @allure.step("系统返回")
    def back(self):
        self.driver.back()
        logger.info("🔙 [Action] 系统返回")

    @allure.step("匹配所有 Toast 弹窗")
    def toast_message(self) -> str:
        """
        获取当前屏幕上显示的任意 Toast 文本的内容
        """
        locator = (AppiumBy.XPATH, "//android.widget.Toast")
        toast = self.find_element(locator, "presence", timeout=2)
        if toast is None:
            return ""
        toast_text = toast.text
        # print(f" 💬 Toast 弹窗内容: {toast_text}")
        logger.info(f" 💬 Toast 弹窗内容: {toast_text}")
        return toast_text
    
    @allure.step("获取当前屏幕 Toast 弹窗内容")
    def get_toast(self, expected_toast: str = "", timeout: float = 3.0) -> str:
        """
        获取当前屏幕上显示的任意 Toast 文本的内容 (支持 XML + OCR 降级双通道检测)
        """
        from locators.system.common.common_locator import CommonLocator
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
                            return toast_text
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
                    return expected_toast
            except Exception as e:
                logger.debug(f"OCR 提示框扫描异常: {e}")
                
        logger.warning(f"⏱️ basePage-get_toast 未能捕获到预期【{expected_toast}】的提示框 (XML和OCR通道均未命中)")
        return ""

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
            container = self.find_element(container_locator, 'visibility', timeout=3)
            item = self.find_element(item_locator, 'visibility', timeout=3)
            
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
    
    @allure.step("长按数据, 获取长按弹窗")
    @allure.step("有多条数据存在时, 长按某一条, 获取弹窗")
    def long_press_action(self, found_ele, hold_time: int = 1000):
        """
        长按数据, 获取长按弹窗
        :param found_ele: 已查找到的元素
        :return: 元素数量
        """
        # 2. 执行长按操作 (Long Press) Appium 新版使用 W3C Actions API
        # 使用 ActionBuilder 创建长按操作
        actions = ActionBuilder(self.driver)
        # 获取指针输入设备
        finger = actions.pointer_inputs

        # 移动到目标元素位置
        actions.pointer_action.move_to(found_ele)
        # 按下指针（开始长按）
        actions.pointer_action.pointer_down()
        # 暂停1.5秒实现长按效果
        actions.pointer_action.pause(hold_time/1000)  
        # 释放指针（结束长按）
        actions.pointer_action.pointer_up()
        # 执行整个动作序列
        actions.perform()
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
        import xml.etree.ElementTree as ET
        
        full_source = self.driver.page_source
        try:
            # 1. 解析完整 XML
            root = ET.fromstring(full_source.encode('utf-8'))
            
            target_node = None
            # 2. 增强型节点查找
            if locator[0] == AppiumBy.ID:
                target_id = locator[1]
                # 遍历所有节点寻找匹配的 resource-id
                for node in root.iter():
                    if node.get('resource-id') == target_id:
                        target_node = node
                        break
            elif locator[0] == AppiumBy.XPATH:
                # 修复核心报错：如果 XPath 以 / 或 // 开头，ElementTree 会报错
                xpath_expr = locator[1]
                if xpath_expr.startswith('//'):
                    xpath_expr = '.' + xpath_expr
                elif xpath_expr.startswith('/'):
                    xpath_expr = '.' + xpath_expr
                
                try:
                    target_node = root.find(xpath_expr)
                except Exception:
                    # 如果 XPath 太复杂 ElementTree 搜不到，尝试提取 ID 兜底
                    import re
                    match = re.search(r"@resource-id=['\"]([^'\"]+)['\"]", locator[1])
                    if match:
                        res_id = match.group(1)
                        for node in root.iter():
                            if node.get('resource-id') == res_id:
                                target_node = node
                                break

            # 3. 比较结果
            if target_node is not None:
                current_element_source = ET.tostring(target_node, encoding='unicode')
                is_changed = (current_element_source != last_element_source) if last_element_source else True
                return is_changed, current_element_source
            else:
                logger.warning(f"在当前 DOM 中未找到目标区域: {locator}")
                return True, ""
                
        except Exception as e:
            logger.error(f"提取指定区域 XML 失败: {e}")
            return True, ""

    @allure.step("执行滑动操作")
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500):
        """
        核心滑动执行器 (W3C 标准)
        :param duration: 滑动持续时间，默认1000毫秒
        """
        try:
            logger.info(f"滑动轨迹: ({start_x}, {start_y}) -> ({end_x}, {end_y}) | 时长: {duration}ms")
            actions, touch_input = self.init_w3c_actions()

            # 3. 构建动作序列 移动 -> 按下 -> 暂停 -> 移动 -> 松开
            touch_input.create_pointer_move(x=start_x, y=start_y, duration=0, origin="viewport")
            touch_input.create_pointer_down(button=0)
            touch_input.create_pause(duration/1000) 
            touch_input.create_pointer_move(x=end_x, y=end_y, duration=duration, origin="viewport")
            touch_input.create_pause(0.1) # 强制加速度归零防止列表抛滑(Fling)
            touch_input.create_pointer_up(button=0)
            actions.perform()
            time.sleep(0.5)
        except Exception as e:
            logger.error(f"滑动操作失败: {e}")
            raise RuntimeError(f"执行手指手势操作失败: {str(e)}")

    @allure.step("在指定的坐标边界内容固定按预定距离滑动")
    def swipe_to_distance(self, slid_type: str = "up", rect: dict = None, duration: int = 300, times: int = 1) -> None:
        """
        在指定字典区域的边界内计算滑动（预留 20% 安全区防误触）
        :param slid_type: 'up'(手指上滑) / 'down'(手指下滑) / 'left'(手指左滑) / 'right'(手指右滑)
        """
        if not rect:
            return

        x, y, w, h = rect['x'], rect['y'], rect['width'], rect['height']
        
        center_x = int(x + w * 0.5)
        center_y = int(y + h * 0.5)

        # 构建防越界安全隔离区(20% ~ 80%)
        top_y = int(y + h * 0.2)
        bottom_y = int(y + h * 0.8)
        left_x = int(x + w * 0.2)
        right_x = int(x + w * 0.8)

        for _ in range(times):
            if slid_type.lower() == "up":      # 手指从下往上滑，页面下降
                start_x, start_y, end_x, end_y = center_x, bottom_y, center_x, top_y
            elif slid_type.lower() == "down":  # 手指从上往下滑，页面上升
                start_x, start_y, end_x, end_y = center_x, top_y, center_x, bottom_y
            elif slid_type.lower() == "left":  # 手指从右向左滑，页面向左移
                start_x, start_y, end_x, end_y = right_x, center_y, left_x, center_y
            elif slid_type.lower() == "right": # 手指从左向右滑，页面向右移
                start_x, start_y, end_x, end_y = left_x, center_y, right_x, center_y
            else:
                raise ValueError(f"不支持的滑动方向: {slid_type}")

            self.swipe(start_x, start_y, end_x, end_y, duration)
    
    @allure.step("屏幕全局滑动")
    def swipe_page(self, slid_type: str = 'up', duration: int = 500, times: int = 1):
        """ 全屏滑动：封装成全屏尺寸后转交 swipe_to_distance 处理 """
        size = self.driver.get_window_size()
        rect = {'x': 0, 'y': 0, 'width': size['width'], 'height': size['height']}
        self.swipe_to_distance(slid_type=slid_type, rect=rect, duration=duration, times=times)

    @allure.step("元素内局域滑动")
    def swipe_on_element(self, element, slid_type: str = "left", duration: int = 600):
        """ 元素内滑动：提取元素物理 rect 后转交 swipe_to_distance 处理 """
        if element is None:
            raise ValueError("必须提供有效的元素对象")
        self.swipe_to_distance(slid_type=slid_type, rect=element.rect, duration=duration, times=1)

    @allure.step("以指定固定区域(rect)的偏移中心点为起滑基准，按给定的 X/Y 偏移量进行精确滑动")
    def swipe_by_offset(self, rect: dict, start_x_offset: int = 0, start_y_offset: int = 0, 
                        x_offset: int = 0, y_offset: int = 0, duration: int = 500):
        """
        以指定固定区域(rect)的中心点（叠加起始偏移）为起滑基准，按给定的 X/Y 偏移量进行精确滑动。
        :param rect: 固定的安全容器边界字典 {'x':., 'y':., 'width':., 'height':.}
        :param start_x_offset: 起点相对于容器中心点的 X 轴偏移量（正数向右，负数向左）
        :param start_y_offset: 起点相对于容器中心点的 Y 轴偏移量（正数向下，负数向上）
        :param x_offset: X轴手指偏移量（负数=手指左移/页面右偏，正数=手指右移/页面左偏）
        :param y_offset: Y轴手指偏移量（负数=手指上移/页面下偏，正数=手指下移/页面上偏）
        :param duration: 滑动动作耗时(ms)
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

        self.swipe(start_x, start_y, end_x, end_y, duration)
        time.sleep(0.5)

    @allure.step("极速滑动与状态检测(刷底/刷顶)")
    def swipe_page_quickly(self, element=None, slid_type: str = "down", duration: int = 100, max_swipes: int = 10):
        """ 智能边界嗅探：不停滑动直到 DOM (page_source) 停止变化 """
        logger.info(f"极速滑动自动探测边界启动 (Max:{max_swipes}次)")
        previous_source = ""
        
        for i in range(max_swipes):
            is_changed, previous_source = self.is_page_source_changed(previous_source)
            if not is_changed:
                break
            # 若给定了目标元素则作局部探测，否则执行全屏盲探
            if element:
                self.swipe_on_element(element=element, slid_type=slid_type, duration=duration)
            else:
                self.swipe_page(slid_type=slid_type, duration=duration, times=1)
        else:
            logger.warning(f"⚠️ 滑满上限({max_swipes}次)仍见变化，强制挂起停止")

    @allure.step("通用动作: 模拟键盘点击“搜索/回车”")
    def press_search_action(self, input_locator=None):
        """
        [通用动作] 模拟键盘点击“搜索/回车”
        :param input_locator: 输入框定位符 (仅用于通用 Keys 方式，Android Keycode 方式不需要)
        """
        try:
            # 方式 A: Android 原生 Keycode (推荐用于 Android Appium)
            # 66 是 Android 的回车/搜索键 (KEYCODE_ENTER)
            if hasattr(self, 'driver') and hasattr(self.driver, 'press_keycode'):
                logger.info("👉 使用 Android Keycode 66 触发搜索")
                self.driver.press_keycode(66)

            # 方式 B: 通用 Selenium Keys (推荐用于 Web 或 iOS，或者 Android 兼容模式)
            elif input_locator:
                logger.info("👉 使用 send_keys(Keys.ENTER) 触发搜索")
                # 找到输入框，向其发送回车指令
                element = self.find_element(*input_locator)
                element.send_keys(Keys.ENTER)

            else:
                logger.error("❌ 无法触发搜索：未找到 driver.press_keycode 且未传入 input_locator")
        except Exception as e:
            logger.error(f"❌ 触发键盘搜索失败: {e}")
    
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

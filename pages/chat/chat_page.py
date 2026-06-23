import re
import time
import allure
from typing import Optional, Literal
from selenium.common import NoSuchElementException
from common.base_page import BasePage
from core.logger_utils import logger
from locators.chat.chat_locator import ChatLocator
from utils.cv_recognition.screenshot_utils import ScreenshotUtils, CropRect, ImageComparator
from selenium.webdriver.remote.webelement import WebElement


@allure.story("聊天页面")
class ChatPage(BasePage):

    # 消息类型(msg_type)+方向(side) -> 定位器 映射表。
    # 内容全为 ChatLocator 静态类属性，与入参无关，提为类常量避免每次调用 get_message_elements 重建。
    _MSG_LOC_MAP = {
        ('text', 'sent'): ChatLocator.SENT_TEXT_MESSAGE_ITEM,
        ('text', 'received'): ChatLocator.RECEIVED_TEXT_MESSAGE_ITEM,
        ('text', 'all'): ChatLocator.TEXT_MESSAGE_VIEW_XPATH,
        ('image', 'sent'): ChatLocator.SEND_IMAGE_ITEM,
        ('image', 'received'): ChatLocator.RECEIV_IMAGE_ITEM,
        ('image', 'all'): ChatLocator.IMAGE_ITEM,
        ('videoDuration', 'sent'): ChatLocator.SENT_VIDEO_DURATION_ITEM,
        ('videoDuration', 'received'): ChatLocator.RECEIVE_VIDEO_DURATION_ITEM,
        ('videoDuration', 'all'): ChatLocator.VIDEO_DURATION_ITEM,
        ('videoPlay', 'sent'): ChatLocator.SENT_VIDEO_PLAY_BUTTON_ITEM,
        ('videoPlay', 'received'): ChatLocator.RECEIVE_VIDEO_PLAY_BUTTON_ITEM,
        ('videoPlay', 'all'): ChatLocator.VIDEO_PLAY_BUTTON_ITEM,
        ('locTitle', 'sent'): ChatLocator.SENT_LOCATION_MESSAGE_TITLE,
        ('locTitle', 'received'): ChatLocator.RECEIVE_LOCATION_MESSAGE_TITLE,
        ('locTitle', 'all'): ChatLocator.LOCATION_MESSAGE_TITLE,
        ('locSubTitle', 'sent'): ChatLocator.SENT_LOCATION_MESSAGE_SUBTITLE,
        ('locSubTitle', 'received'): ChatLocator.RECEIVE_LOCATION_MESSAGE_SUBTITLE,
        ('locSubTitle', 'all'): ChatLocator.LOCATION_MESSAGE_SUBTITLE,
        ('card', 'sent'): ChatLocator.SENT_CARD_NAME_ITEM,
        ('card', 'received'): ChatLocator.RECEIVE_CARD_NAME_ITEM,
        ('card', 'all'): ChatLocator.CARD_NICKNAME_ITEM,
        ('card_detail', 'sent'): ChatLocator.SENT_CARD_ST_ITEM,
        ('card_detail', 'received'): ChatLocator.RECEIVE_CARD_ST_ITEM,
        ('card_detail', 'all'): ChatLocator.CARD_ST_ITEM,
        ('fileName', 'sent'): ChatLocator.SENT_FILE_NAME_ITEM,
        ('fileName', 'received'): ChatLocator.RECEIVE_FILE_NAME_ITEM,
        ('fileName', 'all'): ChatLocator.FILE_NAME_ITEM,
        ('fileSize', 'sent'): ChatLocator.SENT_FILE_SIZE_ITEM,
        ('fileSize', 'received'): ChatLocator.RECEIVE_FILE_SIZE_ITEM,
        ('fileSize', 'all'): ChatLocator.FILE_SIZE_ITEM,
        ('fileStatus', 'sent'): ChatLocator.SENT_FILE_STATUS_ITEM,
        ('fileStatus', 'received'): ChatLocator.RECEIVE_FILE_STATUS_ITEM,
        ('fileStatus', 'all'): ChatLocator.FILE_STATUS_ITEM,
        ('history', 'sent'): ChatLocator.SENT_CHAT_HISTORY_CONTENT,
        ('history', 'received'): ChatLocator.RECEIVE_CHAT_HISTORY_CONTENT,
        ('history', 'all'): ChatLocator.CHAT_HISTORY_CONTENT,
    }

    # 页面导航-等待聊天页面加载完成
    def wait_for_chat_page_load(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """页面导航-等待聊天页面加载完成"""
        logger.info(f"⏳ [Wait] 等待聊天主页面加载完成，超时时间 {timeout} 秒")
        try:
            chat_page_is_visible = len(self.find_elements(ChatLocator.CHAT_INPUT, timeout=timeout, raise_exception=raise_exception))
            logger.info(f"✅ [Wait] 聊天主页面加载完成, 元素个数为 {chat_page_is_visible}")
            return bool(chat_page_is_visible)
        except Exception:
            logger.warning(f"⚠️ [Wait] 聊天主页面加载超时")
            return False

    # 页面导航-返回到聊天主页面
    def back_to_chat_page(self, max_retries: int = 10) -> bool:
        """页面导航-返回到聊天主页面"""
        logger.info(f"🚀[Action-chat] - 开始循环尝试返回聊天页面，最大重试次数: {max_retries}")
        
        for i in range(max_retries):
            if self.wait_for_chat_page_load(timeout=2):
                logger.info(f"✅ [Action-chat] - 确认当前已处于聊天页面 (尝试次数: {i})")
                return True

            logger.info(f"🔄 [Action-chat] - 未检测到聊天主界面，执行第 {i+1} 次返回...")
            self.back()
            time.sleep(0.1)
        logger.error(f"❌ [Action-chat] - 尝试返回 {max_retries} 次后仍未能回到聊天页面")
        return False

    # 页面导航-点击顶部返回按钮
    def click_back_button(self):
        """页面导航-点击顶部返回按钮"""
        self.click(ChatLocator.TOP_BACK_BUTTON)
        logger.info("🚀[Action-chat] - chat 点击返回按钮")

    # 聊天信息-获取顶部聊天对象昵称
    def get_top_name(self) -> str:
        """聊天信息-获取顶部聊天对象昵称"""
        name = self.get_attribute(ChatLocator.TOP_USER_NAME_XPATH, 'text')
        logger.info(f"🚀[Action-chat] - chat 获取顶部聊天对象昵称: {name}")
        return name

    # 聊天信息-获取群聊名称并过滤括号
    def get_group_name(self) -> str:
        """聊天信息-获取群聊名称并过滤括号"""
        group_name = self.get_top_name()
        # 使用 r"\s*\(\d+\)" 正则匹配 0 个或多个空格 + 左括号 + 1 个或多个数字 + 右括号
        cleaned_name = re.sub(r"\s*\(\d+\)", "", group_name)
        logger.info(f"🚀[Action-chat] - chat 获取群聊名称并过滤括号: '{group_name}' -> '{cleaned_name}'")
        return cleaned_name 
    
    # 系统辅助-获取系统 Toast 提示文本
    def get_toast_text(self) -> str:
        """系统辅助-获取系统 Toast 提示文本"""
        toast = self.get_toast()
        logger.info(f"🚀[Action-chat] - chat chat-page 获取 toast: {toast}")
        return toast

    # ==============================================================================
    # 更多页面元素操作 相关
    # ==============================================================================
    # 页面导航-点击顶部更多设置按钮
    def click_more_button(self):
        """页面导航-点击顶部更多设置按钮"""
        self.click(ChatLocator.TOP_MORE_BUTTON)
        logger.info("🚀[Action-chat] - chat 点击更多按钮")
        time.sleep(0.3)

    # =============================================
    # 聊天页面元素操作相关
    # =============================================
    # 聊天信息-获取停用账号发送消息的提示数量
    def get_disable_message_tip(self) -> int:
        """聊天信息-获取停用账号发送消息的提示数量"""
        count = len(self.find_elements(ChatLocator.DISABLE_MESSAGE_TIP))
        logger.info(f"🚀[Action-chat] - chat 获取给停用账号发送消息提示数量: {count}")
        return count

    # 聊天输入-获取聊天页面底部输入框容器
    def get_chat_input_container(self) -> int:
        """聊天输入-获取聊天页面底部输入框容器"""
        input_container = self.find_element(ChatLocator.CHAT_INPUT)
        logger.info(f"🚀[Action-chat] - chat 获取聊天页面底部 chat_input 输入框容器: {input_container}")
        return input_container

    # 聊天输入-获取底部输入框是否被禁用及其提示信息
    def get_input_disabled_info(self) -> tuple[str, str]:
        """聊天输入-获取底部输入框是否被禁用及其提示信息"""
        disable_title_text = self.get_attribute(ChatLocator.TV_NOT_IN_TIPS_TITLE, 'text', raise_exception=False)
        disable_tip_time = self.get_attribute(ChatLocator.TV_NOT_IN_TIPS, 'text', raise_exception=False)
        
        if not disable_title_text and not disable_tip_time:
            logger.info(f"🚀[Action-chat] - 输入框未被禁用")
            return "", ""
        elif not disable_tip_time:
            logger.info(f"🚀[Action-chat] - 输入框被禁言，禁言标题：{disable_title_text}，无具体禁言时间")
            return disable_title_text, ""
        logger.info(f"🚀[Action-chat] - 输入框被禁言，禁言标题：{disable_title_text}，禁言时间: {disable_tip_time}")
        return disable_title_text, disable_tip_time
    
    # 聊天输入-判断底部文本输入框是否被禁用
    def is_input_disabled(self) -> bool:
        """聊天输入-判断底部文本输入框是否被禁用"""
        disable_title_text, _ = self.get_input_disabled_info()
        return bool(disable_title_text)

    # 聊天输入-解析被禁言的剩余总分钟数
    def get_mute_remaining_minutes(self, disable_tip_time: str = None) -> int | None:
        """聊天输入-解析被禁言的剩余总分钟数"""
        if disable_tip_time is None:
            _, disable_tip_time = self.get_input_disabled_info()
        if not disable_tip_time:
            return None
        match = re.search(r"剩余(\d+):(\d+):(\d+)", disable_tip_time)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return round((h * 3600 + m * 60 + s) / 60)
        return None

    # 聊天输入-点击底部语音输入按钮
    def click_voice_button(self):
        """聊天输入-点击底部语音输入按钮"""
        self.click(ChatLocator.VOICE_BUTTON)
        logger.info("🚀[Action-chat] - chat 点击底部语音按钮")

    # 聊天输入-在文本输入框中输入数据
    def input_text(self, text: str):
        """聊天输入-在文本输入框中输入数据"""
        self.send_keys(ChatLocator.TEXT_INPUT, text)
        logger.info(f"🚀[Action-chat] - chat 输入框输入数据: {text}")

    # 聊天输入-点击底部表情按钮
    def click_emoji_button(self):
        """聊天输入-点击底部表情按钮"""
        if self.get_attribute(ChatLocator.EMOJI_BUTTON, 'checked') != 'true':
            self.click(ChatLocator.EMOJI_BUTTON, force_wait=True)
            logger.info("🚀[Action-chat] - chat 点击表情按钮")
        else:
            logger.info("🚀[Action-chat] - chat 表情按钮已选中，无需点击")

    # 聊天输入-点击 + 号按钮，展开其它功能面板按钮
    def click_add_button(self):
        """聊天输入-点击 + 号按钮，展开其它功能面板按钮"""
        if self.get_attribute(ChatLocator.ADD_BUTTON, 'checked') != 'true':
            self.click(ChatLocator.ADD_BUTTON, force_wait=True)
            logger.info("🚀[Action-chat] - chat 点击 + 号按钮，展开其它功能元素")
        else:
            logger.info("🚀[Action-chat] - chat + 号按钮已选中，无需点击")
    
    # 聊天输入-点击发送消息按钮
    def click_send_button(self):
        """聊天输入-点击发送消息按钮"""
        self.click(ChatLocator.SEND_BUTTON, force_wait=True)
        logger.info("🚀[Action-chat] - chat 点击发送按钮")
        time.sleep(0.5)

    # 快捷功能-检测快捷功能面板是否可左右滑动
    def has_input_more_scrollable_indicator(self) -> bool:
        """快捷功能-检测快捷功能面板是否可左右滑动"""
        has_scrollable_indicator = len(self.find_elements(ChatLocator.INPUT_MORE_SCROLLABLE_INDICATOR, timeout=2)) > 0
        if not has_scrollable_indicator:
            logger.info(f"🚀[Action-chat] - chat 检测加号面板没有可左右滑动标识")
            return False
        logger.info(f"🚀[Action-chat] - chat 检测加号面板有可左右滑动标识")
        return True
    
    # 快捷功能-对快捷功能面板进行左右滑动
    def swip_input_more_page(self, slide: str = 'left') -> bool:
        """快捷功能-对快捷功能面板进行左右滑动"""
        input_more_pager = self.find_element(ChatLocator.INPUT_MORE_PAGER, timeout=2)
        if not input_more_pager:
            logger.error(f"❌ [Action-chat] - 未检测到加号面板滑动区域，请确保已点击加号按钮")
            return False
        self.swipe_on_element(element=input_more_pager, slid_type=slide, duration=300)
        logger.info(f"🚀[Action-chat] - chat 加号面板向 {'左' if slide == 'left' else '右'} 滑动成功")
        return True
    
    # 消息接收-获取聊天页面消息所有行容器列表
    def get_message_layout_items(self) -> list:
        """消息接收-获取聊天页面消息所有行容器列表"""
        message_layout_items = self.find_elements(ChatLocator.MESSAGE_LAYOUT_ITEM, timeout=2, expect_missing=True)
        logger.info(f"🚀[Action-chat] - chat 获取聊天页面消息所有容器数量: {len(message_layout_items)}")
        return message_layout_items

    # 消息接收-获取当前聊天页面的消息总数量
    def get_total_message_count(self) -> int:
        """消息接收-获取当前聊天页面的消息总数量"""
        count = len(self.get_message_layout_items())
        logger.info(f"🚀[Action-chat] - chat 获取聊天页面消息总数: {count}")
        return count
    
    # 消息状态-获取页面所有发送失败的消息红点列表
    def get_message_send_fail_status_list(self) -> list:
        """消息状态-获取页面所有发送失败的消息红点列表"""
        fail_msg_elems = self.find_elements(ChatLocator.FAIL_MSG, timeout=2, expect_missing=True)
        logger.info(f"🚀[Action-chat] - chat 获取屏幕消息发送失败的状态数量: {len(fail_msg_elems)}")
        return fail_msg_elems
    
    # 消息状态-获取特定方向的消息发送失败标识元素
    def get_message_fail_items(self, side: Literal['sent', 'received'] = 'sent') -> list:
        """消息状态-获取特定方向的消息发送失败标识元素"""
        locator = ChatLocator.SENT_MESSAGE_FAIL_ITEM if side == 'sent' else ChatLocator.RECEIVE_MESSAGE_FAIL_ITEM
        fail_items = self.find_elements(locator, timeout=2, expect_missing=True)
        side_name = "发送方" if side == 'sent' else "接收方"
        logger.info(f"🚀[Action-chat] - chat 获取 {side_name} 消息发送失败数量: {len(fail_items)}")
        return fail_items

    # 消息接收-查找并获取页面中的聊天记录气泡元素及数量
    def find_chat_bubbles(self) -> tuple:
        """消息接收-查找并获取页面中的聊天记录气泡元素及数量"""
        message_container_items = self.find_elements(ChatLocator.MESSAGE_CONTAINER_ITEM)
        count = len(message_container_items)
        logger.info(f"🚀[Action-chat] - chat 查找页面聊天记录气泡数量: {count}")
        return message_container_items, count
        
    # 快捷功能-打开底部表情面板
    def enter_emoji_page(self):
        """快捷功能-打开底部表情面板"""
        self.click_emoji_button()
        logger.info("🚀[Action-chat] - chat 打开表情面板")
        time.sleep(1)

    # 聊天输入-清空文本输入框中的内容
    def clear_input_text(self):
        """聊天输入-清空文本输入框中的内容"""
        self.find_element(ChatLocator.TEXT_INPUT).clear()
        logger.info("🚀[Action-chat] - chat 清空输入框中的数据")

    # 聊天输入-获取当前文本输入框中的内容
    def get_input_text(self) -> str:
        """聊天输入-获取当前文本输入框中的内容"""
        input_text = self.get_attribute(ChatLocator.TEXT_INPUT, 'text')
        logger.info(f"[Assert] 获取输入框中的数据: {input_text}")
        return input_text
    
    # 消息接收-获取发送方的所有聊天行容器元素
    def get_sent_message_row_item(self) -> list:
        """消息接收-获取发送方的所有聊天行容器元素"""
        items = self.find_elements(ChatLocator.SENT_MESSAGE_ROW_ITEM, timeout=3)
        if not items:
            logger.warning(f"🚀[Action-chat] - chat 未检测到发送方聊天行容器")
            return []
        logger.info(f"🚀[Action-chat] - chat 获取发送方聊天行容器数量: {len(items)}")
        return items
    
    # 消息接收-获取发送方的所有消息内容容器元素
    def get_sent_message_content_item(self) -> list:
        """消息接收-获取发送方的所有消息内容容器元素"""
        items = self.find_elements(ChatLocator.SENT_MESSAGE_CONTENT_ITEM, timeout=3)
        if not items:
            logger.warning(f"🚀[Action-chat] - chat 未检测到发送方聊天内容容器")
            return []
        logger.info(f"🚀[Action-chat] - chat 获取发送方聊天内容容器数量: {len(items)}")
        return items
        
    # 消息接收-获取接收方的所有消息内容容器元素
    def get_received_message_content_item(self) -> list:
        """消息接收-获取接收方的所有消息内容容器元素"""
        items = self.find_elements(ChatLocator.RECEIVED_MESSAGE_CONTENT_ITEM, timeout=3)
        if not items:
            logger.warning(f"🚀[Action-chat] - chat 未检测到接收方聊天内容容器")
            return []
        logger.info(f"🚀[Action-chat] - chat 获取接收方聊天内容容器数量: {len(items)}")
        return items

    # 消息接收-根据类型和方向获取聊天页面中的消息元素列表
    def get_message_elements(self, msg_type: Literal['text', 'image', 'videoDuration', 'videoPlay', 'locTitle', 'locSubTitle', 'card', 'card_detail', 'fileName', 'fileSize', 'fileStatus', 'history'], 
                              side: Literal['sent', 'received', 'all'] = 'all', 
                              expect_missing: bool = False) -> list[WebElement]:
        """消息接收-根据类型和方向获取聊天页面中的消息元素列表"""
        locator = self._MSG_LOC_MAP.get((msg_type, side))
        if not locator:
            raise ValueError(f"❌ ChatPage.get_message_elements - 不支持的消息类型或方向: msg_type={msg_type}, side={side}")

        items = self.find_elements(locator, timeout=3, expect_missing=expect_missing)
        return items if items else []

    # 消息接收-统计聊天页面中指定类型与方向的消息数量
    def get_message_count(self, msg_type: Literal['text', 'image', 'videoDuration', 'videoPlay', 'locTitle', 'locSubTitle', 'card', 'card_detail', 'fileName', 'fileSize', 'fileStatus', 'history'] = 'text', side: Literal['sent', 'received', 'all'] = 'all') -> int:
        """消息接收-统计聊天页面中指定类型与方向的消息数量"""
        items = self.get_message_elements(msg_type, side)
        count = len(items)
        logger.info(f"📊 [Count] 当前可见 {side} {msg_type} 消息数: {count}")
        return count

    # 消息接收-通过文本内容查找发送的文本消息气泡
    def find_sent_message_by_bubble(self, message: str) -> str:
        """消息接收-通过文本内容查找发送的文本消息气泡"""
        locator = ChatLocator.get_message_item_by_text(message)
        bubble_elems = self.find_elements(locator, condition='visibility', timeout=3)
        if bubble_elems:
            result = bubble_elems[-1].text
            logger.info(f"🚀[Action-chat] - chat 通过气泡框查找发送的文本消息: {result}")
            return result
        logger.info("🚀[Action-chat] - chat 通过气泡框未找到发送的文本消息")
        return  ""

    # 消息发送-发送一条文本消息并等待
    def send_message(self, message: str):
        """消息发送-发送一条文本消息并等待"""
        self.input_text(message)
        self.click_send_button()
        logger.info(f"🚀[Action-chat] - chat 发送消息: {message}")
        time.sleep(0.5)

    # 消息接收-获取指定索引与方向的消息文本内容
    def find_message_content(self, index: int = -1, side: Literal['sent', 'received'] = 'sent') -> str:
        """消息接收-获取指定索引与方向的消息文本内容"""
        send_text_items = self.get_message_elements(msg_type="text", side=side, expect_missing=True)
        if not send_text_items:
            logger.error(f"没有找到 {side} 的文本消息元素")
            raise NoSuchElementException(f"没有找到 {side} 的文本消息元素")
        actual_text = send_text_items[index].text
        actual_text = actual_text.replace("\uFFFC ", "").strip()  # 去掉这个字符 ￼
        logger.info(f"[Assert] 获取 {side} 第 {index} 条文本消息的内容: {actual_text}")
        return actual_text

    # ========================================================================================
    # 逻辑相关
    # ========================================================================================
    # 消息状态-等待最后一条发送的消息完成
    def wait_for_last_sent_message_completed(self, timeout: int = 60) -> bool:
        """消息状态-等待最后一条发送的消息完成"""
        logger.info(f"⏳ [Status] 等待发送状态图标 (btn_state) 消失...")
        start_time = time.time()

        is_disappeared = self.wait_until_element_disappear(ChatLocator.FAIL_MSG, timeout=timeout)
        if is_disappeared:
            logger.info(f"✅ 发送标识消失，共耗时 {int(time.time() - start_time)}s，判定发送成功。")
            return True
        else:
            logger.error(f"❌ 监控超时({timeout}s)，状态图标仍未消失，判定为失败。")
            return False

    # 消息状态-智能监控最后一条消息的发送状态
    def wait_for_last_message_send_status(self, timeout: int = 120) -> bool:
        """消息状态-智能监控最后一条消息的发送状态"""
        logger.info(f"⏳ [Status] 启动智能监控：等待消息最终结果 (Max: {timeout}s)...")
        start_time = time.time()
        last_log_time = start_time

        while time.time() - start_time < timeout:
            try:
                last_item = self._get_last_message_layout_item()
                status_icons = last_item.find_elements(*ChatLocator.FAIL_MSG)
                
                if not status_icons:
                    logger.info(f"✅ [Status] 标识消失，发送成功！(耗时: {int(time.time() - start_time)}s)")
                    return True
                
                if status_icons[0].get_attribute("clickable") == "true":
                    logger.error("❌ [Status] 监测到红点标识，判定为发送失败。")
                    return False
                
                if time.time() - last_log_time >= 5:
                    logger.info(f"⏳ [Status] 文件正在上传中... 已耗时 {int(time.time() - start_time)}s")
                    last_log_time = time.time()
            except Exception:
                pass 
            time.sleep(0.5)
        logger.error(f"❌ [Status] 监控超时，未能在 {timeout}s 内确认最终状态")
        return False

    # 消息接收-获取最后一条消息的行容器组件
    def _get_last_message_layout_item(self):
        """消息接收-获取最后一条消息的行容器组件"""
        msg_layout_items = self.get_message_layout_items()
        if not msg_layout_items or len(msg_layout_items) == 0:
            logger.info("没有找到已发送的消息元素")
            raise NoSuchElementException("没有找到已发送的消息元素")
        return msg_layout_items[-1]

    # 消息接收-获取最后一条消息的气泡内容容器
    def get_message_content_bubble(self):
        """消息接收-获取最后一条消息的气泡内容容器"""
        last_item = self._get_last_message_layout_item()
        return last_item.find_element(*ChatLocator.MESSAGE_CONTENT_ITEM)

    # 消息状态-获取最后一条消息是否包含发送失败状态
    def get_last_message_send_fail_status(self) -> bool:
        """消息状态-获取最后一条消息是否包含发送失败状态"""
        last_item = self._get_last_message_layout_item()
        fail_msgs = last_item.find_elements(*ChatLocator.FAIL_MSG)
        
        status = len(fail_msgs) > 0
        logger.info(f"最后一条消息发送{'失败' if status else '成功'}")
        return status
    

    # 视频消息-验证最后一条视频消息的状态是否完整成功
    def get_last_message_video_status(self) -> bool:
        """视频消息-验证最后一条视频消息的状态是否完整成功"""
        last_item = self._get_last_message_layout_item()
        
        has_play = len(last_item.find_elements(*ChatLocator.VIDEO_PLAY_BUTTON_ITEM)) > 0
        has_duration = len(last_item.find_elements(*ChatLocator.VIDEO_DURATION_ITEM)) > 0
        has_fail = len(last_item.find_elements(*ChatLocator.FAIL_MSG)) > 0
        
        status = has_play and has_duration and not has_fail
        logger.info(f"最后一条视频消息状态校验: {'通过' if status else '不通过(缺失组件或存在红点)'}")
        return status

    # 消息接收-智能识别最后一条消息的媒体类型
    def get_last_message_type(self) -> str:
        """消息接收-智能识别最后一条消息的媒体类型"""
        last_item = self._get_last_message_layout_item()
        
        if len(last_item.find_elements(*ChatLocator.VIDEO_DURATION_ITEM)) > 0:
            return "video"
        if len(last_item.find_elements(*ChatLocator.SENT_IMAGE_ITEM)) > 0 or \
           len(last_item.find_elements(*ChatLocator.RECEIV_IMAGE_ITEM)) > 0:
            return "image"
        if len(last_item.find_elements(*ChatLocator.MESSAGE_CONTENT)) > 0:
            return "text"
        
        return "unknown"

    # 消息接收-通过输入内容在聊天气泡中查找并验证内容
    def verify_message_content_by_input(self, message: str) -> str:
        """消息接收-通过输入内容在聊天气泡中查找并验证内容"""
        # locator = ChatLocator.get_specific_message_locator("sender", message) # UI 变化前
        locator = ChatLocator.get_sent_text_message_locator()
        bubble_elems = self.find_elements(locator, condition='visibility', timeout=3)
        if not bubble_elems or len(bubble_elems) == 0:
            logger.error("没有找到已发送的消息元素")
            return ""
        logger.info(f"[Assert] 获取已发送消息内容: {bubble_elems[-1].text}")
        return bubble_elems[-1].text

    # 快捷功能-点击快捷功能面板中的指定子功能按钮
    def open_child_elem(self, attrName: str):
        """快捷功能-点击快捷功能面板中的指定子功能按钮"""
        elems_button = self.find_elements(ChatLocator.ELEM_BUTTON)
        if not elems_button:
            logger.error(f"✖️ 未找到快捷功能面板中的任何功能按钮")
            raise NoSuchElementException("功能面板按钮加载失败")
            
        for i, elem in enumerate(elems_button):
            child_elem = self.find_element_gird(element=elem, locator=ChatLocator.ELEM_GIRD_TEXT)
            if child_elem and child_elem.text == attrName:
                logger.info(f"🚀 [Action-chat] 找到 {attrName} 按钮，点击进入")
                child_elem.click()
                return
        logger.error(f"✖️ 功能面板中未匹配到指定按钮: {attrName}")

    

    # =========================================================================================
    # 聊天页面【长按操作】文本消息相关
    # =========================================================================================
    # 文本消息-获取聊天页面中所有文本消息内容
    def get_all_text_message_contents(self, side: str = "sent") -> list:
        """文本消息-获取聊天页面中所有文本消息内容"""
        tx_elems = self.get_message_elements(msg_type="text", side=side)
        if not tx_elems or len(tx_elems) == 0:
            logger.error(f"没有找到聊天页面中的文本消息元素: side={side}")
            return []
        txs = [tx.text for tx in tx_elems]
        logger.info(f"[Assert] side={side} - 获取聊天页面所有文本消息内容: {txs}")
        return txs


    # 文本消息-获取第 n 条文本消息内容
    def get_text_message_content_by_index(self, index: int = -1, side: str = "sent", expect_missing: bool = False) -> str:
        """文本消息-获取第 n 条文本消息内容"""
        st_elems = self.get_message_elements(msg_type="text", side=side, expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有文本消息，跳过该消息的断言")
            return ""
        if not st_elems:
            logger.error("❌ 没有找到任何文本消息")
            return ""
        if index >= len(st_elems) or index < -len(st_elems):
            logger.error(f"❌ 索引 {index} 超出范围，当前文本消息数为: {len(st_elems)}")
            return ""
        
        message_content = st_elems[index].get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条文本消息内容: {message_content}")
        return message_content
    
    # 图片消息-获取指定索引图片消息的哈希值
    def get_chat_image_hash(self, index: int = -1, expect_missing: bool = False) -> str:
        """图片消息-获取指定索引图片消息的哈希值"""
        image_elements = self.get_message_elements(msg_type="image", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有图片，跳过该消息的断言")
            return ""
        if not image_elements:
            logger.error(f"❌ [Action-chat] - 未找到任何图片")
            return ""
        if index >= len(image_elements):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的图片")
            return ""
        
        image_ele = image_elements[index]
        actual_image_hash = ScreenshotUtils.dhash_auto(element=image_ele)
        return actual_image_hash
    
    # 图片消息-获取所有图片消息的哈希值列表
    def get_chat_all_image_hash(self) -> list:
        """图片消息-获取所有图片消息的哈希值列表"""
        image_elements = self.get_message_elements(msg_type="image", side='all')
        if not image_elements:
            logger.error(f"❌ [Action-chat] - 未找到任何图片")
            return []
        
        image_hashes = []
        for image_ele in image_elements:
            actual_image_hash = ScreenshotUtils.dhash_auto(element=image_ele)
            image_hashes.append(actual_image_hash)
        logger.info(f"📊 [Content] 所有图片 hash 值: {image_hashes}")    
        return image_hashes

    # 图片消息-点击指定索引的图片消息进入大图浏览
    def click_image_message_by_index(self, index: int = -1, expect_missing: bool = False):
        """图片消息-点击指定索引的图片消息进入大图浏览"""
        image_elements = self.get_message_elements(msg_type="image", side='sent', expect_missing=expect_missing)
        if not image_elements or len(image_elements) == 0:
            logger.error("🚀[Action-chat] - chat 没有找到已发送的图片")
            raise NoSuchElementException("🚀[Action-chat] - chat 没有找到已发送的图片")
        if index >= len(image_elements) or index < -len(image_elements):
            logger.error("🚀[Action-chat] - chat 图片索引超出范围")
            raise IndexError("🚀[Action-chat] - chat 图片索引超出范围")
        image_elements[index].click()
        logger.info(f"🚀[Action-chat] - chat 点击图片: {index}，等待消息详情页面加载...")

    # 图片消息-长按预览的图片
    def long_press_preview_image(self):
        """图片消息-长按预览的图片"""
        preview_image = self.find_element(ChatLocator.PREVIEW_IMAGE_ITEM)
        self.long_press_action(element=preview_image)
        logger.info("🚀[Action-chat] - chat 长按预览的图片")

    # 图片消息-点击预览图上的下载图标
    def click_download_icon_in_image_preview(self):
        """图片消息-点击预览图上的下载图标"""
        self.click(ChatLocator.IV_DOWNLOAD_ITEM)
        logger.info("🚀[Action-chat] - chat 点击图片下载图标")

    
    # 视频消息-获取指定索引的视频消息时长文本
    def get_chat_video_duration(self, index: int = -1, expect_missing: bool = False) -> str:
        """视频消息-获取指定索引的视频消息时长文本"""
        vd_elems = self.get_message_elements(msg_type="videoDuration", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有视频时长，跳过该消息的断言")
            return ""
        if not vd_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何视频时长控件")
            return ""
        if index >= len(vd_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的视频时长")
            return ""
        vd_elem = vd_elems[index]
        avd = vd_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条视频时长: {avd}")
        return avd
    
    # 视频消息-获取所有视频消息的时长文本列表
    def get_chat_all_video_duration(self) -> list:
        """视频消息-获取所有视频消息的时长文本列表"""
        vd_elems = self.get_message_elements(msg_type="videoDuration", side='all')
        if not vd_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何视频时长控件")
            return []
        
        video_durations = []
        for vd_elem in vd_elems:
            video_durations.append(vd_elem.get_attribute('text'))
        logger.info(f"📊 [Content] 所有视频时长: {video_durations}")    
        return video_durations
    

    # 文件消息-获取所有文件消息 of 名列表
    def get_chat_all_file_name(self) -> list:
        """文件消息-获取所有文件消息的名称列表"""
        file_elems = self.get_message_elements(msg_type="fileName", side='all')
        if not file_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何文件名称控件")
            return []
        
        file_names = []
        for file_elem in file_elems:
            file_names.append(file_elem.get_attribute('text'))
        logger.info(f"📊 [Content] 所有文件名称: {file_names}")    
        return file_names
    
    # 位置消息-获取指定索引的位置消息标题文本
    def get_chat_location_title(self, index: int = -1, expect_missing: bool = False) -> str:
        """位置消息-获取指定索引的位置消息标题文本"""
        title_elems = self.get_message_elements(msg_type="locTitle", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有位置消息标题，跳过该消息的断言")
            return ""
        if not title_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何位置消息的标题")
            return ""
        if index >= len(title_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的位置消息的标题")
            return ""
        title_elem = title_elems[index]
        title_name = title_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条位置消息标题: {title_name}")
        return title_name
    
    # 位置消息-获取指定索引的位置消息副标题文本
    def get_chat_location_subtitle(self, index: int = -1, expect_missing: bool = False) -> str:
        """位置消息-获取指定索引的位置消息副标题文本"""
        subtitle_elems = self.get_message_elements(msg_type="locSubTitle", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有位置消息副标题，跳过该消息的断言")
            return ""
        if not subtitle_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何位置消息的副标题")
            return ""
        if index >= len(subtitle_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的位置消息的副标题")
            return ""
        subtitle_elem = subtitle_elems[index]
        subtitle_text = subtitle_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条位置消息副标题: {subtitle_text}")
        return subtitle_text
    
    # 名片消息-获取指定索引的名片消息姓名标题
    def get_chat_card_name(self, index: int = -1, expect_missing: bool = False) -> str:
        """名片消息-获取指定索引的名片消息姓名标题"""
        title_elems = self.get_message_elements(msg_type="card", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有名片消息标题，跳过该消息的断言")
            return ""
        if not title_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何名片消息的标题")
            return ""
        if index >= len(title_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的名片消息的标题")
            return ""
        title_elem = title_elems[index]
        title_name = title_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条名片消息标题: {title_name}")
        return title_name
    
    # 名片消息-获取指定索引的名片消息副标题文本
    def get_chat_card_subtitle(self, index: int = -1, expect_missing: bool = False) -> str:
        """名片消息-获取指定索引的名片消息副标题文本"""
        subtitle_elems = self.get_message_elements(msg_type="card_detail", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有名片消息副标题，跳过该消息的断言")
            return ""
        if not subtitle_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何名片消息的副标题")
            return ""
        if index >= len(subtitle_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的名片消息的副标题")
            return ""
        subtitle_elem = subtitle_elems[index]
        subtitle_text = subtitle_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条名片消息副标题: {subtitle_text}")
        return subtitle_text
    
    # 文件消息-获取指定索引的文件消息文件名
    def get_chat_file_name(self, index: int = -1, expect_missing: bool = False) -> str:
        """文件消息-获取指定索引的文件消息文件名"""
        title_elems = self.get_message_elements(msg_type="fileName", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有文件消息标题，跳过该消息的断言")
            return ""
        if not title_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何文件消息的标题")
            return ""
        if index >= len(title_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的文件消息的标题")
            return ""
        title_elem = title_elems[index]
        title_name = title_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条文件消息标题: {title_name}")
        return title_name
    
    # 文件消息-获取指定索引的文件消息大小
    def get_chat_file_size(self, index: int = -1, expect_missing: bool = False) -> str:
        """文件消息-获取指定索引的文件消息大小"""
        subtitle_elems = self.get_message_elements(msg_type="fileSize", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有文件消息大小，跳过该消息的断言")
            return ""
        if not subtitle_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何文件消息的大小")
            return ""
        if index >= len(subtitle_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的文件消息的大小")
            return ""
        subtitle_elem = subtitle_elems[index]
        subtitle_text = subtitle_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条文件消息大小: {subtitle_text}")
        return subtitle_text
    
    # 文件消息-获取指定索引的文件消息传输状态文本
    def get_chat_file_status(self, index: int = -1, expect_missing: bool = False) -> str:
        """文件消息-获取指定索引的文件消息传输状态文本"""
        status_elems = self.get_message_elements(msg_type="fileStatus", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有文件消息状态，跳过该消息的断言")
            return ""
        if not status_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何文件消息的状态")
            return ""
        if index >= len(status_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的文件消息的状态")
            return ""
        status_elem = status_elems[index]
        status_text = status_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条文件消息状态: {status_text}")
        return status_text


    # =========================================================================================
    # 聊天页面【长按操作】图片和视频消息相关 
    # =========================================================================================
    # 媒体消息-验证连续发送的多条媒体消息数量与描述文本
    def verify_batch_sent_messages(self, expected_count: int, msg_type: Literal['image', 'video'], expect_text: str = "", max_slide: int = 5) -> tuple[int, bool, int]:
        """媒体消息-验证连续发送的多条媒体消息数量与描述文本"""
        time.sleep(3)  
        found_count = 0
        fail_count = 0
        text_matched = False
        seen_container_ids = set()          # 存储 container.id，用于同屏或缓存元素的快速去重
        seen_elements = []                  # 存储 (md5, absolute_y) 结合坐标防止同一屏幕的相同元素被错误去重
        total_scroll = 0                    # 累计滑动距离
        global_index = 0                    # 全局消息序号（0 为最新一条）

        chat_input_elem = self.get_chat_input_container()
        cie = chat_input_elem.rect if chat_input_elem else None

        logger.info(f"🔍 准备分页校验聊天区: 预期{msg_type} {expected_count} 张/条, 预期描述 '{expect_text}'")

        for slide in range(max_slide):
            row_elems = self.get_sent_message_row_item() or []
            if not row_elems:
                logger.warning(f"第 {slide} 次滑动后未获取到任何消息元素")
                break

            re_elems = list(reversed(row_elems))
            new_elements_in_slide = 0
            for container in re_elems:
                try:
                    container_id = container.id
                    c_rect = CropRect.from_rect_dict(container.rect)
                    msg_id = ScreenshotUtils.md5_auto(element=container, rect=c_rect)

                    current_y = container.rect['y']
                    absolute_y = current_y - total_scroll

                    # MD5 + 坐标的严格去重判断，防止复用控件带来误伤。
                    if container_id in seen_container_ids:
                        is_duplicate = False
                        for seen_md5, seen_abs_y in seen_elements:
                            # 只要误差在一个消息体高度内，且 MD5 一致，就认为是重复元素。
                            if seen_md5 == msg_id and abs(seen_abs_y - absolute_y) < 200:
                                is_duplicate = True 
                                break
                        if is_duplicate:
                            continue
                    else:
                        seen_container_ids.add(container_id)
                    
                    seen_elements.append((msg_id, absolute_y))
                    new_elements_in_slide += 1

                    fail_elems = container.find_elements(*ChatLocator.SENT_MESSAGE_FAIL_ITEM)
                    if fail_elems:
                        logger.info(f"❌ [索引:{global_index}] 找到发送失败的消息(带红点)")
                        fail_count += 1
                        continue
                    
                    is_valid_msg = False
                    is_media = False
                    if msg_type == 'image':
                        images = container.find_elements(*ChatLocator.IMAGE_ITEM)
                        if images and len(images) > 0:
                            is_valid_msg = is_media = True
                            logger.info(f"📸 [索引:{global_index}] 找到第 {found_count + 1}/{expected_count} 张图片")
                    elif msg_type == 'video':
                        play_btns = container.find_elements(*ChatLocator.VIDEO_PLAY_BUTTON_ITEM)
                        durations = container.find_elements(*ChatLocator.VIDEO_DURATION_ITEM)
                        if play_btns and durations:
                            is_valid_msg = is_media = True
                            logger.info(f"🎥 [索引:{global_index}] 找到第 {found_count + 1}/{expected_count} 条视频")

                        
                    global_index += 1
                    if expect_text and not text_matched:
                        text_views = container.find_elements(*ChatLocator.TEXT_MESSAGE_VIEW_ITEM)
                        if text_views:
                            text_nodes = text_views[0].find_elements(*ChatLocator.TEXT_MESSAGE_VIEW_CLASS)
                            if text_nodes:
                                logger.debug(f'text_nodes-text: {text_nodes[0].text}')
                                if expect_text in text_nodes[0].text:
                                    text_matched = True
                                    logger.info(f"💬 [索引:{global_index}] 匹配到描述文本 '{expect_text}'")

                    if is_valid_msg:
                        if is_media:
                            if found_count < expected_count:
                                found_count += 1
                                
                    if found_count >= expected_count and (text_matched or not expect_text):
                        logger.info(f"✅ 找齐了！共 {found_count} 条 {msg_type} 且文本已匹配。")
                        return found_count, text_matched, fail_count

                except Exception as e:
                    logger.warning(f"⚠️ 遍历过程中元素引用失效(Stale)，尝试跳过当前项并刷新列表: {e}")
                    break 
                
            # 触顶防抖检测
            if slide > 0 and new_elements_in_slide == 0:
                logger.info("⚠️ 检测到本次滑动没有发现任何新元素，已触达聊天记录顶部！")
                break
                
            if found_count >= expected_count and (text_matched or not expect_text):
                logger.info(f"✅ 找齐了！共 {found_count} 条{msg_type}且文本已匹配。")
                return found_count, text_matched, fail_count
                
            if found_count < expected_count and cie and re_elems:
                logger.info(f"✅ 触达页尾且未找齐(实得:{found_count}/{expected_count})，执行滑动加载更多...")
                try:
                    cr = container.rect
                    offset_y = (cie['y'] - cr['y'])
                    total_scroll += offset_y
                    self.swipe_by_offset(rect=cr, start_x_offset=-cr['width']/2, 
                                         start_y_offset=-cr['height']/2 + 5, 
                                         x_offset=0, y_offset=offset_y, duration=2500)
                    time.sleep(1) 
                except Exception as e:
                    logger.warning(f"滑动操作异常，可能控件失效: {e}")
                    
            logger.info(f"⚠️ 第 {slide+1} 次循环未找齐(实得:{found_count}/{expected_count})，尝试下滑...")
        return found_count, text_matched, fail_count

    # 页面导航-验证当前是否处于聊天页面
    def verify_is_on_chat_page(self) -> bool:
        """页面导航-验证当前是否处于聊天页面"""
        if self.wait_for_chat_page_load(timeout=2):
            logger.info("✔️ 确认目前处于聊天主页面")
            return True
        else:
            logger.error("✖️ 未检测到聊天页面关键特征")
            return False

    # 消息状态-验证最后一条消息的发送成功状态
    def verify_message_sent_status(self) -> bool:
        """消息状态-验证最后一条消息的发送成功状态"""
        resend_btns = self.find_elements(ChatLocator.FAIL_MSG, timeout=2)
        if not resend_btns:
            logger.info("✅ 未检测到重发按钮，消息发送正常")
            return True
        return False

    # =========================================================================================
    # 聊天页面【长按操作】位置消息相关方法 
    # =========================================================================================
    # 位置消息-获取所有位置消息的标题列表
    def get_all_location_titles(self):
        """位置消息-获取所有位置消息的标题列表"""
        titles = self.find_elements(ChatLocator.SENT_LOCATION_MESSAGE_TITLE)
        if not titles:
            logger.warning("未找到任何位置消息标题")
            return []
        msg_titles = [title.get_attribute("text") for title in titles]
        logger.info(f"所有位置消息标题: {msg_titles}")
        return msg_titles

    # 位置消息-验证已发送位置消息的标题与副标题并返回
    def verify_location_sent_status(self) -> dict:
        """位置消息-验证已发送位置消息的标题与副标题并返回"""
        title_locator = ChatLocator.get_avatar_bubble_locator(ChatLocator.LOCATION_MESSAGE_TITLE_ID, is_sender=True)
        subtitle_locator = ChatLocator.get_avatar_bubble_locator(ChatLocator.LOCATION_MESSAGE_SUBTITLE_ID, is_sender=True)
        
        titles = self.find_elements(title_locator, timeout=2)
        subtitles = self.find_elements(subtitle_locator, timeout=2)
        
        if not titles or not subtitles:
            logger.error("没有找到已发送的位置气泡")
            raise NoSuchElementException("位置气泡未上屏")

        address_dict = {
            "title": titles[-1].text,
            "detail_address": subtitles[-1].text
        }
        logger.info(f"✅ 发送位置校验: {address_dict}")
        return address_dict

    # 位置消息-点击最后一条位置消息进入地图详情页面
    def verify_location_enter_map_detail(self):
        """位置消息-点击最后一条位置消息进入地图详情页面"""
        map_locator = ChatLocator.get_avatar_bubble_locator(ChatLocator.LOCATION_MESSAGE_MAP_ID, is_sender=True)
        maps = self.find_elements(map_locator, timeout=2)
        if not maps:
            logger.error("没有找到已发送的位置气泡，无法点击详情")
            raise NoSuchElementException("无法进入地图详情")
        maps[-1].click()
        logger.info("🚀 [Action-chat] 点击位置气泡进入地图详情")
        time.sleep(2)
    

    # =========================================================================================
    # 聊天页面【长按操作】名片功能相关逻辑
    # =========================================================================================
    # 名片消息-获取所有已发送名片的信息列表
    def get_all_send_contact_card_infos(self):
        """名片消息-获取所有已发送名片的信息列表"""
        # time.sleep(2)
        titles = self.find_elements(ChatLocator.SENT_CARD_NAME_ITEM, timeout=2)
        stIds = self.find_elements(ChatLocator.SENT_CARD_ST_ITEM, timeout=2)
        card_types = self.find_elements(ChatLocator.SENT_CARD_TAG_ITEM, timeout=2)
        
        if not titles or not stIds or not card_types:
            logger.error("没有找到已发送的名片气泡")
            raise NoSuchElementException("名片气泡未上屏")

        card_info_list = []
        for title, stIds, card_types in zip(titles, stIds, card_types):
            card_info = {
                "name": title.text,
                "stId": stIds.text,
                "card_type": card_types.text
            }
            card_info_list.append(card_info)
        logger.info(f"🚀 [Info] 已发送名片信息: {card_info_list}")
        return card_info_list

    # 名片消息-验证聊天气泡中是否成功显示指定名片信息
    def verify_card_in_chat(self, name: str) -> tuple[bool, dict]:
        """名片消息-验证聊天气泡中是否成功显示指定名片信息"""
        card_info_list = self.get_all_send_contact_card_infos()
        if not card_info_list:
            logger.warning("⚠️ 未检测到已发送的名片气泡")
            return False, None

        last_info = card_info_list[-1]
        if last_info['name'] == name:
            logger.info(f"✅ [Assert] 聊天气泡成功显示名片信息，名片名称={last_info['name']}, stId={last_info['stId']}, 名片类型={last_info['card_type']}")
            return True, last_info
        else:
            logger.error(f"❌ 聊天气泡没有显示名片信息，期待的名片是{name}, 实际是{last_info['name']}")
            return False, None

    # 名片消息-点击最后一条名片消息进入详情页面
    def click_last_card_message(self):
        """名片消息-点击最后一条名片消息进入详情页面"""
        elem_card = self._get_last_message_layout_item()
        if not elem_card:
            logger.error("❌ 未找到名片消息，无法进入详情页")
            raise Exception("未找到名片消息")
        elem_card.click()
        logger.info("🚀 [Action-chat] 点击名片消息进入名片详情页")


    # =========================================================================================
    # 聊天页面【长按操作】收藏功能相关逻辑
    # =========================================================================================
    # 收藏夹-验证从收藏夹发送的消息类型与内容是否正确
    def verify_from_collection_message_content(self, col_type: str = "text", exp_content: str = None, msg: str = None) -> bool:
        """收藏夹-验证从收藏夹发送的消息类型与内容是否正确"""
        if not exp_content and not msg:
            logger.error("❌ [Error] 调用校验函数失败：未提供任何预期值")
            return False
            
        self.wait_for_chat_page_load()
        text_elements = self.find_elements(ChatLocator.TEXT_MESSAGE_VIEW_XPATH, timeout=5)
        actual_text_msgs = [m.get_attribute("text") for m in text_elements[-2:]] if text_elements else []

        # 1. 核心负载校验 (Content)
        check_content = True
        check_msg = True
        actual_info = f"文本内容: {actual_text_msgs}"

        if col_type == "text":
            if exp_content:
                if not actual_text_msgs:
                    logger.error("❌ 校验失败：未发现文本气泡")
                    return False
                check_content = any(exp_content in am for am in actual_text_msgs)
        
        elif col_type == "image":
            image_elements = self.find_elements(ChatLocator.IMAGE_ITEM, timeout=5)
            if not image_elements:
                logger.error("❌ 校验失败：未找到图片消息")
                return False
            actual_image_hash = ScreenshotUtils.dhash_auto(element=image_elements[-1])
            actual_info += f" | 图片哈希: {actual_image_hash}"
            check_content = ImageComparator.is_hash_similar(exp_content, actual_image_hash) if exp_content else True

        # 2. 校验留言内容
        if msg:
            if not actual_text_msgs:
                logger.error("❌ 校验失败：期待留言但未找到文本消息")
                check_msg = False
            else:
                check_msg = any(msg in am for am in actual_text_msgs)

        # 3. 结果汇总与多维度诊断日志
        result = check_content and check_msg
        status_label = "✅" if result else "❌"
        logger.info(f"{status_label} [{col_type}] 验证完毕 | 详情: {actual_info}")
        
        if not result:
            logger.error(f"🔍 [Fail] 期待内容: {exp_content} | 期待留言: {msg}")
            
        return result


    # =========================================================================================
    # 聊天页面【长按操作】多选转发相关逻辑
    # =========================================================================================
    # 多选操作-等待多选编辑页面加载完成
    def wait_for_multi_select_page_load(self, timeout=10) -> bool:
        """多选操作-等待多选编辑页面加载完成"""
        multi_select_button = self.is_element_exist(ChatLocator.IV_SHARE, timeout=timeout)
        if not multi_select_button:
            logger.error("❌ 多选转发页面未加载完成")
            return False
        logger.info("✅ 多选转发页面加载完成")
        return True
    
    # 多选操作-点击多选页面的转发按钮
    def click_forward_button(self):
        """多选操作-点击多选页面的转发按钮"""
        self.click(ChatLocator.IV_SHARE)
        logger.info("✅ 点击多选转发页面转发按钮")
    
    # 多选操作-点击多选页面的删除按钮
    def click_delete_button(self):
        """多选操作-点击多选页面的删除按钮"""
        self.click(ChatLocator.IV_DELETE)
        logger.info("✅ 点击多选转发页面删除按钮")
    
    # 多选操作-点击多选的逐条转发选项
    def click_batch_forward_button(self):
        """多选操作-点击多选的逐条转发选项"""
        self.click(ChatLocator.TV_FORWARD_ONE_BY_ONE)
        logger.info("✅ 点击多选转发逐条转发按钮")
    
    # 多选操作-点击多选的合并转发选项
    def click_merge_forward_button(self):
        """多选操作-点击多选的合并转发选项"""
        self.click(ChatLocator.TV_FORWARD_COMBINE)
        logger.info("✅ 点击多选转发合并转发按钮")
    
    # 多选操作-点击取消多选编辑状态
    def click_cancel_button(self):
        """多选操作-点击取消多选编辑状态"""
        self.click(ChatLocator.TV_CANCEL, force_wait=True)
        logger.info("✅ 点击多选转发取消按钮")
    
    # 多选操作-在聊天记录选择页中点击取消发送
    def click_cancel_send_button(self):
        """多选操作-在聊天记录选择页中点击取消发送"""
        self.click(ChatLocator.LEFT_TEXT)
        logger.info("✅ 点击取消发送按钮（聊天记录）")
    
    # 多选操作-获取当前页面所有可勾选的消息复选框元素
    def _get_select_checkbox_buttons(self) -> list[WebElement]:
        """多选操作-获取当前页面所有可勾选的消息复选框元素"""
        check_btns = self.find_elements(ChatLocator.BT_SELECT_NOT_FAIL, timeout=2)
        if not check_btns:
            logger.error("❌ 未找到多选转发页面不包含发送失败消息的勾选按钮")
            return []
        logger.info(f"✅ 多选转发页面加载完成，获取到 {len(check_btns)} 个不包含发送失败消息的勾选按钮")
        return check_btns

    # 多选操作-点击勾选指定索引的消息复选框
    def click_select_checkbox_button(self, index=-1):
        """多选操作-点击勾选指定索引的消息复选框"""
        check_btn = self._get_select_checkbox_buttons()[index]
        check_btn.click()
        logger.info("✅ 点击勾选消息按钮")

    # 合并转发-点击合并转发的消息卡片内容
    def click_merge_forward_message_content(self):
        """合并转发-点击合并转发的消息卡片内容"""
        self.click(ChatLocator.CHAT_HISTORY_CONTENT)
        logger.info("✅ 点击合并转发的消息内容")

    # 多选操作-批量勾选 X 条消息并支持滑动加载与上限拦截
    def click_x_select_checkbox_buttons(self, target_count: int, max_swipes: int = 100) -> int | str:
        """
        勾选指定数量(target_count)的消息。
        如果当前屏幕上的未勾选按钮不足，则滑动加载更多并继续勾选。
        如果尝试勾选第 101 条消息，将捕获 Toast 拦截提示并以字符串形式返回。
        """
        selected_count = 0
        swipes = 0
        
        while selected_count < target_count and swipes < max_swipes:
            check_btns = self._get_select_checkbox_buttons()
            if not check_btns:
                logger.error("❌ 未找到多选页面勾选按钮")
                break
            
            check_btns = check_btns[::-1]
            for btn in check_btns:
                if selected_count >= target_count:
                    break
                
                is_checked = btn.get_attribute("checked") == "true" or btn.get_attribute("selected") == "true"
                
                if not is_checked:
                    btn.click()
                    
                    # 当已经成功勾选 100 条后，再去点击第 101 条时，App 会进行 Toast 阻断
                    if selected_count == 100:
                        toast_msg = self.get_toast()
                        if toast_msg:
                            logger.info(f"✅ 成功捕获到多选上限拦截提示: {toast_msg}")
                            return toast_msg
                        else:
                            logger.warning("⚠️ 尝试勾选第 101 条但未捕获到屏幕 Toast")
                            return "超过100条消息！"
                    
                    selected_count += 1
                    logger.info(f"✅ 点击勾选消息按钮，已勾选 {selected_count}/{target_count} 条")
                    
            if selected_count >= target_count:
                logger.info(f"🎉 成功完成勾选目标: {target_count} 条消息")
                return selected_count
                
            logger.warning("⚠️ 当前屏幕消息不足或已全部勾选，尝试向下滑动加载更多...")
            self.swipe_page(slid_type="down", duration=600)
            swipes += 1

        if selected_count < target_count:
            logger.warning(f"⚠️ 已达到最大滑动次数({max_swipes})，最终仅勾选了 {selected_count} 条消息")
        return selected_count

    # 合并转发-等待合并转发消息详情页面加载完成
    def wait_for_chat_merge_forward_page_load(self, timeout: int = 10) -> bool:
        """合并转发-等待合并转发消息详情页面加载完成"""
        res = self.is_element_exist(ChatLocator.CHAT_MERGE_FORWARD_TITLE, timeout=timeout)
        if not res:
            logger.warning("❌ 聊天页面合并转发标题未加载完成")
            return False
        logger.info("✅ 聊天页面合并转发标题加载完成")
        return True

    # 合并转发-获取最新合并转发消息卡片的标题
    def get_merge_forward_message(self, expect_missing: bool = False) -> str:
        """合并转发-获取最新合并转发消息卡片的标题"""
        title_elements = self.get_message_elements(msg_type="locTitle", side='sent', expect_missing=expect_missing)
        if not title_elements:
            logger.error("❌ 未找到聊天消息")
            return ""
        forward_title = title_elements[-1].get_attribute("text")
        return forward_title

    # 合并转发-等待聊天记录合并转发的发送状态提示消失
    def wait_for_history_send_complete(self, timeout=60) -> bool:
        """合并转发-等待聊天记录合并转发的发送状态提示消失"""
        hist_sending = self.wait_until_element_disappear(ChatLocator.MULIT_TOAST_MESSAGE, timeout=timeout)
        if not hist_sending:
            logger.error("❌ 聊天记录（合并转发）后 toast 发送中 未消失")
            return False
        logger.info("✅ 聊天记录（合并转发）后 toast 发送中 消失")
        return True

    # 合并转发-等待聊天记录合并转发详情页标题栏加载完成
    def wait_for_history_title_layout(self, timeout=10) -> bool:
        """合并转发-等待聊天记录合并转发详情页标题栏加载完成"""
        history_title_layout = self.is_element_exist(ChatLocator.HISTORY_TITLE_LAYOUT, timeout=timeout)
        if not history_title_layout:
            logger.error("❌ 聊天记录（合并转发）标题栏未加载完成")
            return False
        logger.info("✅ 聊天记录（合并转发）标题栏加载完成")
        return True

    # 合并转发-校验合并转发卡片内消息条数并穿透点击详情验证
    def verify_chat_history_content(self, expected_count: int, expect_missing: bool = False) -> bool:
        """合并转发-校验合并转发卡片内消息条数并穿透点击详情验证"""
        his_elems = self.get_message_elements(msg_type="history", side='sent', expect_missing=expect_missing)
        if not his_elems:
            logger.error("❌ 未找到聊天记录内容元素")
            return False

        preview_text = his_elems[-1].get_attribute("text")
        actual_lines = [line for line in preview_text.split('\n') if line.strip()]
        logger.info(f"✅ 获取到合并转发卡片预览文本: {len(actual_lines)} 条 - \n {preview_text}")
        if len(actual_lines) != expected_count:
            logger.error(f"❌ 预览文本中解析出 {len(actual_lines)} 条消息，期望为 {expected_count} 条")
            return False

        logger.info("进行穿透测试，点击进入聊天记录详情页验证是否 Crash...")
        his_elems[-1].click()
        is_opened = self.wait_for_history_title_layout(timeout=5)
        
        self.click_back_button()
        
        if not is_opened:
            logger.error("❌ 点击聊天记录卡片后，未能成功打开详情页（可能发生 Crash 或卡死）")
            return False
        return True


    # =========================================================================================
    # 聊天页面【长按操作】撤回相关逻辑
    # =========================================================================================
    # 撤回消息-获取指定索引的撤回系统提示及其上一条正常消息
    def get_withdraw_message(self, index=-1) -> tuple[str, str] | None:
        """撤回消息-获取指定索引的撤回系统提示及其上一条正常消息"""
        elements = self.find_elements(ChatLocator.WITHDRAW_MESSAGE_ITEM, timeout=2)
        if not elements:
            logger.error("❌ 未找到撤回消息")
            return None

        withmsg = elements[index].get_attribute("text")
        # 防越界：前一条正常消息可能不存在
        prev_index = index - 1
        smsg = elements[prev_index].get_attribute("text") if -len(elements) <= prev_index < len(elements) else ""
        logger.info(f"✅ 获取到撤回消息: {withmsg}, 正常消息: {smsg}")
        return withmsg, smsg


    
    # =========================================================================================
    # 聊天页面【长按操作】删除相关逻辑
    # =========================================================================================
    # 消息删除-等待删除确认弹窗显示
    def wait_for_del_dialog(self, timeout=2) -> bool:
        """消息删除-等待删除确认弹窗显示"""
        del_dialog = self.is_element_exist(ChatLocator.DEL_CONFIRM, timeout=timeout)
        if not del_dialog:
            logger.error("❌ 未找到删除弹窗")
            return False
        logger.info("✅ 找到删除弹窗")
        return True

    # 消息删除-点击弹窗中的二次确认删除按钮
    def click_del_confirm(self) -> None:
        """消息删除-点击弹窗中的二次确认删除按钮"""
        self.click(ChatLocator.DEL_CONFIRM, force_wait=True)
        logger.info("✅ 点击二次确认删除按钮")
        time.sleep(1)

    # 消息删除-点击弹窗中的取消删除按钮
    def click_del_cancel(self) -> None:
        """消息删除-点击弹窗中的取消删除按钮"""
        self.click(ChatLocator.DEL_CANCEL, force_wait=True)
        logger.info("✅ 点击取消删除按钮")
    
    # 系统辅助-等待指定时间的倒计时并执行防息屏保活
    def wait_for_x_minutes(self, ti: int = 120) -> bool:
        """系统辅助-等待指定时间的倒计时并执行防息屏保活"""
        logger.info("⏳ 正在等待两分钟倒计时")
        
        while ti > 0:
            time.sleep(1)
            
            # 每 30 秒触发一次防息屏保活操作 (极微小滑动，不影响原有页面)
            if ti > 0 and ti % 30 == 0:
                logger.info(f"⏳ 剩余时间: {ti} 秒 (触发防息屏机制...)")
                try:
                    # 获取屏幕尺寸，并在屏幕中央滑动 1 像素，模拟触屏重置系统的息屏倒计时
                    size = self.driver.get_window_size()
                    center_x = int(size['width'] * 0.1)
                    center_y = int(size['height'] * 0.5)
                    self.driver.swipe(center_x, center_y, center_x, center_y + 1, duration=100)
                except Exception as e:
                    pass
            elif ti == 60:
                # 正常倒计时播报
                logger.info(f"⏳ 剩余时间: {ti} 秒")
            ti -= 1
        logger.info("✅ 两分钟倒计时结束")



    # =========================================================================================
    # 横幅通知相关
    # =========================================================================================
    # 横幅通知消息-等待横幅通知消息消失
    def wait_banner_message_disappear(self) -> bool:
        """横幅通知消息-等待横幅通知消息消失"""
        is_disappear = self.wait_until_element_disappear(ChatLocator.TV_PREVIEW)
        if is_disappear:
            logger.info("✅ [Action] ChatPage 聊天页 - 横幅消息已消失")
            time.sleep(1)
            return True
        logger.warning("⚠️ [Action] ChatPage 聊天页 - 横幅消息未消失")
        return False

    # 群公告/群邀请-获取横幅群公告/群邀请文本内容
    def get_group_notice_content(self) -> str | None:
        """群公告/群邀请-获取横幅群公告/群邀请文本内容"""
        banner_text = self.get_attribute(ChatLocator.NEW_ANNOUNCEMENT_CONTENT, 'text')
        if banner_text:
            logger.info(f"✅ [Action] ChatPage 聊天页 - 获取到横幅群公告/群邀请文本内容: {banner_text}")
            return banner_text
        logger.warning("⚠️ [Action] ChatPage 聊天页 - 未获取到横幅群公告/群邀请文本内容")
        return None
    
    # 点击横幅公告/群邀请
    def click_group_notice(self):
        """点击横幅公告/群邀请"""
        self.click(ChatLocator.NEW_ANNOUNCEMENT_CONTENT)
        logger.info("🚀 [Action] ChatPage 聊天页 - 点击横幅群公告/群邀请")
        time.sleep(0.5)


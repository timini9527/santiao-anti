import re
import time
import allure
from typing import Callable, Optional, Literal
from selenium.common import NoSuchElementException
from appium.webdriver.common.appiumby import AppiumBy
from common.base_page import BasePage
from core.logger_utils import logger
from locators.chat.core.chat_locator import ChatLocator
from utils.cv_recognition.screenshot_utils import ScreenshotUtils, CropRect, ImageComparator
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement


@allure.story("聊天页面")
class ChatPage(BasePage):

    # 消息类型与对应基础定位器映射表 (全类统一单一映射源)
    _MSG_BASE_LOCATORS = {
        # 基础消息与多媒体大类
        'text':          ChatLocator.MESSAGE_CONTENT_ITEM,
        'emoji':         ChatLocator.MESSAGE_CONTENT_ITEM,
        'image':         ChatLocator.IMAGE_ITEM,
        'package':       ChatLocator.IMAGE_ITEM,
        'video':         ChatLocator.VIDEO_PLAY_BUTTON_ITEM,
        'voice':         ChatLocator.AUDIO_BUBBLE,
        'file':          ChatLocator.FILE_CARD_ITEM,
        'position':      ChatLocator.LOCATION_CARD_ITEM,
        'location':      ChatLocator.LOCATION_CARD_ITEM,
        'history':       ChatLocator.MERGE_CARD_MSG,
        'historyPreview':ChatLocator.MERGE_CARD_PREVIEW,
        'cardBubble':   ChatLocator.PROFILE_CARD_ITEM,
        'call':          ChatLocator.CALL_CARD_ITEM,
        'callBubble':    ChatLocator.CALL_CARD_ITEM,
        # 细粒度子组件 (用于物理贴边过滤与精细文本断言)
        'card':          ChatLocator.CARD_NICKNAME_ITEM,
        'cardDetail':    ChatLocator.CARD_ST_ITEM,
        'callTitle':     ChatLocator.CALL_TITLE_ITEM,
        'callSubtitle':  ChatLocator.CALL_SUBTITLE_ITEM,
        'locTitle':      ChatLocator.LOCATION_MESSAGE_TITLE,
        'locSubTitle':   ChatLocator.LOCATION_MESSAGE_SUBTITLE,
        'fileName':      ChatLocator.FILE_NAME_ITEM,
        'fileSize':      ChatLocator.FILE_SIZE_ITEM,
        'fileStatus':    ChatLocator.FILE_STATUS_ITEM,
        'videoDuration': ChatLocator.VIDEO_DURATION_ITEM,
        'videoPlay':     ChatLocator.VIDEO_PLAY_BUTTON_ITEM,
    }



    # ==============================================================================
    # 一、页面生命周期与顶部导航相关 (Page Lifecycle & Navigation)
    # ==============================================================================
    # 页面导航-等待聊天页面加载完成
    def wait_for_chat_page_load(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """页面导航-等待聊天页面加载完成"""
        logger.info(f"⏳ [Wait] 等待聊天主页面加载完成，超时时间 {timeout} 秒")
        elements = self.find_elements(ChatLocator.CHAT_INPUT, timeout=timeout, raise_exception=raise_exception)
        if elements:
            logger.info(f"✅ [Wait] 聊天主页面加载完成，元素个数为 {len(elements)}")
            return True
        logger.warning("⚠️ [Wait] 聊天主页面加载超时")
        return False

    # 页面导航-验证当前是否处于聊天页面
    def verify_is_on_chat_page(self) -> bool:
        """页面导航-验证当前是否处于聊天页面"""
        if self.wait_for_chat_page_load(timeout=2):
            logger.info("✔️ 确认目前处于聊天主页面")
            return True
        else:
            logger.error("✖️ 未检测到聊天页面关键特征")
            return False

    # 页面导航-返回到聊天主页面
    def back_to_chat_page(self, max_retries: int = 10) -> bool:
        """页面导航-返回到聊天主页面"""
        logger.info(f"🚀[Action-chat] - 开始循环尝试返回聊天页面，最大重试次数: {max_retries}")
        for i in range(max_retries):
            if self.wait_for_chat_page_load(timeout=1, raise_exception=False):
                logger.info(f"✅ [Action-chat] - 确认当前已处于聊天页面 (尝试次数: {i})")
                return True
            logger.info(f"🔄 [Action-chat] - 未检测到聊天主界面，执行第 {i+1} 次返回...")
            self.back()
        logger.error(f"❌ [Action-chat] - 尝试返回 {max_retries} 次后仍未能回到聊天页面")
        return False

    # 页面导航-点击顶部返回按钮
    def click_back_button(self) -> None:
        """页面导航-点击顶部返回按钮"""
        logger.info("🚀[Action-chat] - chat 点击返回按钮")
        self.click(ChatLocator.TOP_BACK_BUTTON)

    # 页面导航-点击顶部返回按钮 (兼容别名)
    def click_top_back_bnt(self) -> None:
        """页面导航-点击顶部返回按钮"""
        logger.info("🚀[Action-chat] - chat 点击返回按钮")
        self.click(ChatLocator.TOP_BACK_BNT)

    # 聊天信息-获取顶部聊天对象昵称
    def get_top_name(self) -> str:
        """聊天信息-获取顶部聊天对象昵称"""
        logger.info("🚀[Action-chat] - chat 获取顶部聊天对象昵称")
        name = self.get_attribute(ChatLocator.TOP_USER_NAME_XPATH, 'text')
        if not name:
            logger.error("❌[Action-chat] - chat 未获取到聊天对象昵称")
            return None
        logger.info(f"🚀[Action-chat] - chat 成功获取顶部聊天对象昵称: {name}")
        return name
 

    # 聊天信息-获取群聊名称并过滤括号
    def get_group_name(self) -> Optional[str]:
        """聊天信息-获取群聊名称并过滤括号"""
        logger.info("🚀[Action-chat] - chat 开始获取群聊名称")
        group_name = self.get_top_name()
        if not group_name:
            logger.error("❌[Action-chat] - chat 未获取到群聊名称")
            return None
        cleaned_name = re.sub(r"\s*\(\d+\)", "", group_name).strip()
        logger.info(f"🚀[Action-chat] - chat 获取群聊名称: '{group_name}' -> '{cleaned_name}'")
        return cleaned_name
   
    # 聊天信息-获取群聊人数并过滤括号
    def get_group_number_count(self) -> Optional[int]:
        """聊天信息-获取顶部群聊人数控件中的数字"""
        logger.info("🚀[Action-chat] - chat 开始获取群聊人数")
        text = self.get_attribute(ChatLocator.GROUP_NUMBER_COUNT, 'text', raise_exception=False)
        if not text:
            logger.warning("⚠️[Action-chat] - chat 未获取到群聊人数控件文本")
            return None
        # 提取括号内的数字或纯数字 (例如 "(3)" 提取出 3)
        match = re.search(r'\d+', text)
        if match:
            number = int(match.group())
            logger.info(f"🚀[Action-chat] - chat 成功解析群聊人数: '{text}' -> {number}")
            return number
        logger.warning(f"⚠️[Action-chat] - chat 未能在人数文本中提取到有效数字: '{text}'")
        return None

    # 聊天信息-获取群聊ID
    def get_group_id(self) -> Optional[str]:
        """聊天信息-获取群聊ID"""
        logger.info("🚀[Action-chat] - chat 获取群聊ID")
        text = self.get_attribute(ChatLocator.TOP_SHORT_NUMBER, 'text', raise_exception=False)
        if not text:
            logger.error("❌[Action-chat] - chat 未获取到群聊ID")
            return None
        group_id = text.replace('ID:', '').strip()
        logger.info(f"🚀[Action-chat] - chat 成功获取群聊ID: {group_id}")
        return group_id

    # 页面导航-获取更多按钮
    def get_top_more_button(self) -> Optional[WebElement]:
        """页面导航-获取更多按钮"""
        logger.info("🚀[Action-chat] - chat 获取更多按钮")
        more_button = self.find_element(ChatLocator.TOP_MORE_BUTTON)
        if not more_button:
            logger.error("❌[Action-chat] - chat 未获取到更多按钮")
            return None
        return more_button

    # 页面导航-点击顶部更多设置按钮
    def click_more_button(self) -> None:
        """页面导航-点击顶部更多设置按钮"""
        logger.info("🚀[Action-chat] - chat 点击更多按钮")
        self.click(ChatLocator.TOP_MORE_BUTTON)
        time.sleep(0.3)


    # ==============================================================================
    # 二、底部输入栏与输入状态相关 (Chat Input & Mute Status)
    # ==============================================================================
    # 聊天输入-获取聊天页面底部输入框容器
    def get_chat_input_container(self) -> Optional[WebElement]:
        """聊天输入-获取聊天页面底部输入框容器"""
        logger.info("🚀[Action-chat] - chat 获取聊天页面底部 chat_input 输入框容器")
        input_container = self.find_element(ChatLocator.CHAT_INPUT)
        if not input_container:
            logger.error("❌[Action-chat] - chat 未获取到输入框容器")
            return None
        return input_container

    # 聊天输入-获取输入框元素
    def get_input_text_element(self) -> Optional[WebElement]:
        """聊天输入-获取输入框元素"""
        logger.info("🚀[Action-chat] - chat 获取输入框元素")
        input_elem = self.find_element(ChatLocator.TEXT_INPUT)
        return input_elem

    # 聊天输入-在文本输入框中输入数据
    def input_text(self, text: str, fast: bool = False) -> None:
        """
        聊天输入-在文本输入框中输入数据
        :param text: 输入文本内容
        :param fast: 是否使用快速注入（降低驱动层开销）
        """
        logger.info(f"🚀[Action-chat] - 准备向输入框输入数据: {text}")
        if fast:
            logger.info(f"🚀[Action-chat] - chat 输入框快速注入数据: {text}")
            self.fast_send_keys(ChatLocator.TEXT_INPUT, text)
        else:
            logger.info(f"🚀[Action-chat] - chat 输入框输入数据: {text}")
            self.send_keys(ChatLocator.TEXT_INPUT, text)

    # 聊天输入-在文本输入框末尾追加数据
    def append_input_text(self, text: str) -> None:
        """在文本输入框当前内容末尾追加数据"""
        if not text:
            logger.info("ℹ️ [Action-chat] 追加文本为空，跳过输入")
            return
        logger.info(f"✍️ [Action-chat] 准备向输入框末尾追加数据: '{text}'")
        current_text = self.get_input_text() or ""
        prefix = " " if (current_text and not current_text.endswith(" ") and not text.startswith(" ")) else ""
        self.send_keys(ChatLocator.TEXT_INPUT, f"{prefix}{text}", append=True)
        logger.info(f"✅ [Action-chat] 追加数据完成，当前输入框完整内容: '{self.get_input_text()}'")


    # 聊天输入-清空文本输入框中的内容
    def clear_input_text(self) -> None:
        """聊天输入-清空文本输入框中的内容"""
        logger.info("🚀[Action-chat] - chat 清空输入框中的数据")
        self.find_element(ChatLocator.TEXT_INPUT).clear()

    # 聊天输入-获取当前文本输入框中的内容
    def get_input_text(self) -> str:
        """聊天输入-获取当前文本输入框中的内容"""
        logger.info("🚀[Action-chat] - 获取输入框中的数据")
        input_text = self.get_attribute(ChatLocator.TEXT_INPUT, 'text')
        logger.info(f"[Assert] 输入框中的数据为: {input_text}")
        return input_text

    # 聊天输入-点击发送消息按钮
    def click_send_button(self) -> None:
        """聊天输入-点击发送消息按钮"""
        logger.info("🚀[Action-chat] - chat 点击发送按钮")
        self.click(ChatLocator.SEND_BUTTON, force_wait=True)

    # 聊天输入-点击底部语音输入按钮
    def click_voice_button(self) -> None:
        """聊天输入-点击底部语音输入按钮"""
        logger.info("🚀[Action-chat] - chat 点击底部语音按钮")
        self.click(ChatLocator.VOICE_BUTTON)

    # 聊天输入-点击底部表情按钮
    def click_emoji_button(self, is_open: bool = True) -> None:
        """
        聊天输入-点击底部表情按钮，展开或收起表情面板
        :param is_open: True 为展开表情面板，False 为收起/关闭表情面板
        """
        logger.info(f"🚀[Action-chat] - 准备切换表情按钮 (is_open={is_open})...")
        is_checked = self.get_attribute(ChatLocator.EMOJI_BUTTON, 'checked') == 'true'
        if is_open:
            if not is_checked:
                logger.info("🚀[Action-chat] - chat 点击表情按钮，展开表情面板")
                self.click(ChatLocator.EMOJI_BUTTON, force_wait=True)
            else:
                logger.info("🚀[Action-chat] - chat 表情面板已处于展开状态，无需重复点击")
        else:
            if is_checked:
                logger.info("🚀[Action-chat] - chat 点击表情按钮，收起/关闭表情面板")
                self.click(ChatLocator.EMOJI_BUTTON, force_wait=True)
            else:
                logger.info("🚀[Action-chat] - chat 表情面板已处于关闭状态，无需重复点击")

    # 快捷功能-打开底部表情面板
    def enter_emoji_page(self, is_open: bool = True) -> None:
        """快捷功能-打开底部表情面板"""
        logger.info(f"🚀[Action-chat] - chat {'打开' if is_open else '关闭'}表情面板")
        self.click_emoji_button(is_open=is_open)
        time.sleep(0.5)

    # 聊天输入-点击 + 号按钮，展开或收起其它功能面板按钮
    def click_add_button(self, is_open: bool = True) -> None:
        """
        聊天输入-点击 + 号按钮，展开或收起其它功能面板按钮
        :param is_open: True 为展开面板，False 为收起/关闭面板
        """
        logger.info(f"🚀[Action-chat] - 准备切换加号面板按钮 (is_open={is_open})...")
        is_checked = self.get_attribute(ChatLocator.ADD_BUTTON, 'checked') == 'true'
        if is_open:
            if not is_checked:
                logger.info("🚀[Action-chat] - chat 点击 + 号按钮，展开其它功能元素")
                self.click(ChatLocator.ADD_BUTTON, force_wait=True)
            else:
                logger.info("🚀[Action-chat] - chat + 号按钮已处于展开状态，无需重复点击")
        else:
            if is_checked:
                logger.info("🚀[Action-chat] - chat 点击 + 号按钮，收起/关闭其它功能元素")
                self.click(ChatLocator.ADD_BUTTON, force_wait=True)
            else:
                logger.info("🚀[Action-chat] - chat + 号按钮已处于关闭状态，无需重复点击")

    # 快捷功能-检测快捷功能面板是否可左右滑动
    def has_input_more_scrollable_indicator(self) -> bool:
        """快捷功能-检测快捷功能面板是否可左右滑动"""
        logger.info("🚀[Action-chat] - chat 检测快捷功能面板是否可左右滑动")
        has_scrollable_indicator = len(self.find_elements(ChatLocator.INPUT_MORE_SCROLLABLE_INDICATOR, timeout=2)) > 0
        if not has_scrollable_indicator:
            logger.info("🚀[Action-chat] - chat 检测加号面板没有可左右滑动标识")
            return False
        logger.info("🚀[Action-chat] - chat 检测加号面板有可左右滑动标识")
        return True

    # 快捷功能-对快捷功能面板进行左右滑动
    def swip_input_more_page(self, slide: str = 'left', duration: int = 300) -> bool:
        """快捷功能-对快捷功能面板进行左右滑动"""
        logger.info(f"🚀[Action-chat] - chat 准备对加号面板向 {'左' if slide == 'left' else '右'} 滑动")
        input_more_pager = self.find_element(ChatLocator.INPUT_MORE_PAGER, timeout=2)
        if not input_more_pager:
            logger.error("❌ [Action-chat] - 未检测到加号面板滑动区域，请确保已点击加号按钮")
            return False
        self.swipe_on_element(element=input_more_pager, slid_type=slide, duration=duration)
        logger.info(f"🚀[Action-chat] - chat 加号面板向 {'左' if slide == 'left' else '右'} 滑动成功")
        return True

    # 聊天信息-获取停用账号发送消息的提示数量
    def get_disable_message_tip(self) -> int:
        """聊天信息-获取停用账号发送消息的提示数量"""
        logger.info("🚀[Action-chat] - chat 获取给停用账号发送消息提示数量")
        count = len(self.find_elements(ChatLocator.DISABLE_MESSAGE_TIP))
        logger.info(f"🚀[Action-chat] - chat 获取给停用账号发送消息提示数量为: {count}")
        return count

    # 聊天输入-获取底部输入框是否被禁用及其提示信息
    def get_input_disabled_info(self) -> tuple[str, str]:
        """聊天输入-获取底部输入框是否被禁用及其提示信息"""
        logger.info("🚀[Action-chat] - 获取底部输入框是否被禁用及其提示信息")
        disable_title_text = self.get_attribute(ChatLocator.TV_NOT_IN_TIPS_TITLE, 'text', raise_exception=False)
        disable_tip_time = self.get_attribute(ChatLocator.TV_NOT_IN_TIPS, 'text', raise_exception=False)
        
        if not disable_title_text and not disable_tip_time:
            logger.info("🚀[Action-chat] - 输入框未被禁用")
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
    def get_mute_remaining_minutes(self, disable_tip_time: Optional[str] = None) -> Optional[int]:
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


    # ==============================================================================
    # 三、消息发送与状态监控相关 (Message Sending & Status Monitoring)
    # ==============================================================================
    # 消息发送-发送一条文本消息并等待
    def send_message(self, message: str, fast: bool = False, wait_time: float = 0.5) -> None:
        """
        消息发送-发送一条文本消息并等待
        :param message: 文本内容
        :param fast: 是否使用极速内存注入
        :param wait_time: 发送后等待时间（秒），默认 0.5s（满足 100条/分钟 限流要求）
        """
        logger.info(f"🚀[Action-chat] - chat {'极速' if fast else ''}发送消息: {message}")
        self.input_text(message, fast=fast)
        self.click_send_button()
        if wait_time > 0:
            time.sleep(wait_time)

    # 聊天输入-通过键盘按键输入@符号 (触发群聊选人浮层)
    def input_at_by_keyboard(self) -> None:
        """
        通过软键盘真实按键输入 @ 符号（KEYCODE_AT = 77），
        而非使用内存赋值/直接填充，确保触发系统的按键监听事件以唤起群聊@选人界面
        """
        logger.info("⌨️ [Action-chat] 点击输入框激活输入焦点，并通过软键盘按键输入【@】(KEYCODE_AT=77)")
        self.click(ChatLocator.TEXT_INPUT)
        self.press_keycode(77)

    # 消息发送-群聊中通过键盘输入@并从弹出的选人列表中选择所有人或指定成员发送强提醒
    def mention_and_send(self, target: str = "all", member_name: str = "", append_text: str = "") -> None:
        """
        群聊中通过键盘按键输入@并从弹出的选人列表中选择所有人或指定成员，随后发送强提醒消息
        :param target: 目标类型，'at_all' / 'all' 为@所有人，'at_me' / 'member' 为@指定成员
        :param member_name: 被@的成员昵称（当 target 为指定成员时必传）
        :param append_text: 选中后追加输入的文字（可选）
        """
        logger.info(f"🚀 [Action-chat] 群聊通过键盘按键输入 @ 触发选人列表 (target='{target}', member='{member_name}')")
        self.input_at_by_keyboard()

        from pages.chat.mention.chat_mention_page import ChatMentionPage
        ChatMentionPage(self.driver).select_mention_target(target=target, member_name=member_name)

        if append_text:
            logger.info(f"✍️ [Action-chat] 追加输入文本: {append_text}")
            self.append_input_text(append_text)
        self.click_send_button()
        logger.info("✅ [Action-chat] @强提醒消息发送成功")

    # 消息发送-批量极速发送文本消息集合（元素句柄复用 + 平滑恒速流控）
    def send_messages_batch(self, message_list: list[str], interval: float = 0.65) -> None:
        """
        消息发送-批量极速发送文本消息集合（平滑恒速流控：单条间隔 ~0.65s，自然满足 100条/分钟 限制）
        :param message_list: 待发送文本列表
        :param interval: 单条发送间隔（秒），默认 0.65s（约 92 条/分钟，均匀顺畅且绝不超限）
        """
        logger.info(f"🚀 [Batch Send] 准备平滑批量消息发送，共 {len(message_list)} 条消息")
        input_elem = self.find_element(ChatLocator.TEXT_INPUT)
        if not input_elem:
            raise NoSuchElementException("未找到聊天输入框")

        send_btn = None
        total = len(message_list)
        logger.info(f"🚀 [Batch Send] 启动平滑批量消息发送通道，共 {total} 条消息，每条间隔 {interval}s...")

        for idx, msg in enumerate(message_list):
            self.driver.execute_script("mobile: replaceElementValue", {"elementId": input_elem.id, "text": msg})
            if not send_btn:
                send_btn = self.find_element(ChatLocator.SEND_BUTTON, timeout=2)
            if send_btn:
                send_btn.click()
            else:
                self.click(ChatLocator.SEND_BUTTON, force_wait=True)

            if interval > 0:
                time.sleep(interval)

            if (idx + 1) % 20 == 0 or idx + 1 == total:
                logger.info(f"⚡ [Batch Send] 发送进度: {idx + 1}/{total}")

    # 消息状态-等待最后一条发送的消息完成（转发调用智能监控器）
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
        """消息状态-智能监控最后一条消息的发送状态（通过状态标识消失判定，兼容私聊与群聊）"""
        logger.info(f"⏳ [Status] 启动智能监控：等待消息最终结果 (Max: {timeout}s)...")
        start_time = time.time()
        last_log_time = start_time
        time.sleep(0.3)

        while time.time() - start_time < timeout:
            try:
                last_item = self.get_last_message_layout_item()
                read_status = last_item.find_elements(*ChatLocator.READ_STATUS_ITEM)
                if read_status and any(r.is_displayed() for r in read_status):
                    logger.info(f"✅ [Status] 判定条件 1：监测到已读/未读状态，发送成功！(耗时: {int(time.time() - start_time)}s)")
                    return True
                status_icons = last_item.find_elements(*ChatLocator.FAIL_MSG)
                visible_icons = [icon for icon in status_icons if icon.is_displayed()]

                if not visible_icons:
                    logger.info(f"✅ [Status] 判定条件 2：发送中状态标识已消失，发送成功！(耗时: {int(time.time() - start_time)}s)")
                    return True
                if time.time() - last_log_time >= 3:
                    logger.info(f"⏳ [Status] 判定条件 3：消息正在发送中(转圈)... 已等待 {int(time.time() - start_time)}s")
                    last_log_time = time.time()
            except Exception:
                pass
            time.sleep(0.3)
        logger.error(f"❌ [Status] 监控超时({timeout}s)，状态图标仍未消失(转为失败红点)，判定发送失败。")
        return False

    # 消息状态-智能等待批量多媒体消息挂载并完成发送
    def wait_for_batch_media_send_completed(
        self, 
        expected_count: int,
        msg_type: Literal['image', 'video'], 
        timeout: int = 30
    ) -> bool:
        """
        消息状态-智能等待批量多媒体消息挂载并完成发送（工业级四重闭环保障）
        1. 页面守卫：确保回到聊天主页（输入框可见）
        2. 挂载守卫：轮询等待屏幕内目标媒体开始挂载，最新消息变为目标媒体
        3. 传输守卫：全局监控当前屏幕内所有发送中转圈(delivery_status)全部消失
        4. 防抖确认：持续 0.5s 无状态翻转，确保后端 ACK 完全持久化
        :param expected_count: 预期批量发送的消息数量
        :param msg_type: 'image' 或 'video'
        :param timeout: 最大超时时间(秒)
        :return: 是否全部就绪并发送成功
        """
        logger.info(f"⏳ [Media-Wait] 启动批量 {msg_type} × {expected_count} 消息就绪监控 (Max: {timeout}s)...")
        start_time = time.time()

        # 1. 页面守卫：确保已彻底从相册退回聊天主页
        self.wait_for_chat_page_load(timeout=5, raise_exception=False)

        target_locator = ChatLocator.IMAGE_ITEM if msg_type == 'image' else ChatLocator.VIDEO_PLAY_BUTTON_ITEM
        mounted = False

        # 2. 挂载守卫：等待最新消息确认为目标媒体，且至少有消息开始挂载
        mount_start = time.time()
        while time.time() - mount_start < min(12, timeout):
            last_item = self.get_last_message_layout_item()
            if last_item:
                media_elems = last_item.find_elements(*target_locator)
                if media_elems:
                    mounted = True
                    logger.info(f"✅ [Media-Wait] 最新消息已成功挂载为 {msg_type} (耗时: {round(time.time() - mount_start, 2)}s)")
                    break
            time.sleep(0.3)

        if not mounted:
            logger.warning(f"⚠️ [Media-Wait] 超时未检测到最新的 {msg_type} 消息挂载至列表底部")
            return False

        logger.info(f"✅ [Media-Wait] 检测到首批 {msg_type} 消息已挂载上屏，开始监控整批上传状态...")

        # 3. 传输守卫 + 防抖确认：监控当前聊天流内所有发送中转圈彻底清零
        quiescent_count = 0  # 连续静默采样计数
        last_log_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # 获取当前屏幕上所有可能正在发送的图标
                status_icons = self.find_elements(ChatLocator.FAIL_MSG, timeout=1, expect_missing=True) or []
                
                # 检查是否有处于展示态的发送中图标
                in_flight = any(icon.is_displayed() for icon in status_icons)

                if not in_flight:
                    quiescent_count += 1
                    # 连续 2 次采样（跨越 0.6s）均无转圈中图标，确认状态彻底稳定
                    if quiescent_count >= 2:
                        logger.info(f"🎉 [Media-Wait] 全部 {msg_type} 消息发送状态闭环就绪！(耗时: {round(time.time() - start_time, 2)}s)")
                        return True
                else:
                    quiescent_count = 0
                    if time.time() - last_log_time >= 3:
                        logger.info(f"⏳ [Media-Wait] 检测到多媒体正在后台并发上传中... 已等待 {int(time.time() - start_time)}s")
                        last_log_time = time.time()

            except Exception as e:
                logger.debug(f"状态轮询异常，继续重试: {e}")

            time.sleep(0.3)

        logger.warning(f"⚠️ [Media-Wait] 达到最大等待上限({timeout}s)，进入后续校验")
        return False

    # 消息状态-获取最后一条消息是否包含发送失败状态
    def get_last_message_send_fail_status(self) -> bool:
        """ 消息状态-获取最后一条消息是否包含发送失败状态 (显示红色失败感叹号) """
        logger.info("🚀[Action-chat] - 正在检测最后一条消息是否包含发送失败状态(感叹号红点)...")
        last_item = self.get_last_message_layout_item()
        if not last_item:
            return False
        fail_msgs = [icon for icon in last_item.find_elements(*ChatLocator.FAIL_MSG) if icon.is_displayed()]
        status = len(fail_msgs) > 0
        logger.info(f"最后一条消息发送{'失败 (存在感叹号)' if status else '未见失败感叹号'}")
        return status

    # 消息状态-获取页面所有发送失败的消息红点列表
    def get_message_send_fail_status_list(self) -> list[WebElement]:
        """消息状态-获取页面所有发送失败的消息红点列表"""
        logger.info("🚀[Action-chat] - 正在获取屏幕中所有发送失败的消息红点列表...")
        fail_msg_elems = self.find_elements(ChatLocator.FAIL_MSG, timeout=2, expect_missing=True)
        logger.info(f"🚀[Action-chat] - chat 获取屏幕消息发送失败的状态数量: {len(fail_msg_elems)}")
        return fail_msg_elems

    # 消息状态-获取特定方向的消息发送失败标识元素
    def get_message_fail_items(self, side: Literal['sent', 'received'] = 'sent') -> list[WebElement]:
        """消息状态-获取特定方向的消息发送失败标识元素"""
        side_name = "发送方" if side == 'sent' else "接收方"
        logger.info(f"🚀[Action-chat] - 正在获取 {side_name} 消息发送失败标识元素...")
        fail_items = self.find_elements(ChatLocator.FAIL_MSG, timeout=2, expect_missing=True)
        logger.info(f"🚀[Action-chat] - chat 获取 {side_name} 消息发送失败数量: {len(fail_items)}")
        return fail_items


    # ==============================================================================
    # 四、通用消息行容器与内容解析相关 (General Message Layout & Parsing)
    # ==============================================================================
    # 消息接收-获取聊天页面消息所有行容器列表
    def get_message_layout_items(self, timeout: int = 2, raise_exception: bool = True) -> list[WebElement]:
        """消息接收-获取聊天页面消息所有行容器列表"""
        logger.info("🚀[Action-chat] - 正在获取聊天页面所有消息行容器列表...")
        message_layout_items = self.find_elements(ChatLocator.MESSAGE_LAYOUT_ITEM, timeout=timeout, raise_exception=raise_exception)
        if message_layout_items:
            logger.info(f"🚀[Action-chat] - chat 获取聊天页面消息所有容器数量: {len(message_layout_items)}")
        else:
            logger.error(f"❌ [Action-chat] - 未检测到聊天页面消息所有容器，当前会话可能存在异常")
        return message_layout_items

    # 消息接收-获取当前聊天页面的消息总数量
    def get_total_message_count(self) -> int:
        """消息接收-获取当前聊天页面的消息总数量"""
        logger.info("🚀[Action-chat] - 正在统计当前聊天页面消息总数...")
        items = self.get_message_layout_items(raise_exception=False) or []
        count = len(items)
        logger.info(f"🚀[Action-chat] - chat 获取聊天页面消息总数: {count}")
        return count

    # 消息接收-获取最后一条消息的行容器组件
    def get_last_message_layout_item(self, index: int = -1) -> WebElement:
        """消息接收-获取最后一条消息的行容器组件"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的消息行容器组件...")
        msg_layout_items = self.get_message_layout_items()
        if not msg_layout_items or len(msg_layout_items) == 0:
            logger.warning(" ⚠️ 没有找到已发送的消息元素")
            raise NoSuchElementException("没有找到已发送的消息元素")
        return msg_layout_items[index]

    # 消息接收-获取最后一条消息的具体内容组件元素（智能穿透外层 ViewGroup 行容器）
    def get_last_message_content_element(self, msg_type: Optional[str] = None) -> WebElement:
        """
        消息接收-获取最后一条消息的具体内容组件元素（智能穿透外层 ViewGroup 行容器，精确定位到具体的 message_image、video_cover、message_text 等）
        :param msg_type: 消息类型，可选 'text', 'image', 'video', 'voice', 'file', 'position', 'location', 'card', 'package', 'emoji'
        :return: 消息内容组件的 WebElement
        """
        logger.info(f"🚀[Action-chat] - 正在获取最后一条消息内容组件(期望类型: {msg_type or '智能探测'})...")
        last_row = self.get_last_message_layout_item()
        
        # 1. 若指定了类型，优先查找对应定位器
        if msg_type:
            loc = self._MSG_BASE_LOCATORS.get(msg_type)
            if loc:
                elems = last_row.find_elements(*loc)
                if elems:
                    return elems[0]
            logger.warning(f"⚠️ 在最后一条消息行中未直接匹配到指定类型 [{msg_type}] 的组件，尝试智能探测...")

        # 2. 智能探测：按富媒体/卡片/气泡优先级扫描当前行
        _probe_order = ['voice', 'video', 'image', 'package', 'file', 'position', 'history', 'cardBubble', 'card', 'text', 'emoji']
        for t in _probe_order:
            loc = self._MSG_BASE_LOCATORS.get(t)
            if loc:
                elems = last_row.find_elements(*loc)
                if elems:
                    logger.debug(f"🔍 自动命中最后一条消息的组件类型: {t}")
                    return elems[0]

        # 3. 子元素穿透过滤：排除头像、发送状态、已读未读等辅助控件
        try:
            children = last_row.find_elements(AppiumBy.XPATH, "./*")
            content_children = [
                c for c in children
                if not any(k in (c.get_attribute("resource-id") or "") for k in ["avatar", "read_status", "delivery_status", "sender_name"])
            ]
            if content_children:
                return content_children[0]
        except Exception:
            pass

        return last_row

    # 消息接收-获取最后一条消息的气泡内容容器，是否包含某种类型的消息
    def get_last_message_content_bubble_has_type(self, msg_type: str, index: int = -1) -> bool:
        """消息接收-检查指定索引的消息行容器是否包含某种类型的消息组件"""
        logger.info(f"🚀[Action-chat] - 正在检查索引为 {index} 的消息行是否包含组件类型: {msg_type}...")
        layout_items = self.get_message_layout_items()
        if not layout_items:
            logger.error("❌ 页面中未找到任何消息行容器")
            return False

        target_row = layout_items[index]
        loc = self._MSG_BASE_LOCATORS.get(msg_type)
        if not loc:
            raise ValueError(f"❌ 不支持的消息类型: {msg_type}")

        elems = target_row.find_elements(*loc)
        return len(elems) > 0

    # 消息接收-根据类型和方向获取聊天页面中的消息元素列表
    def get_message_elements(
        self,
        msg_type: Literal[
            'text', 'emoji', 'image', 'package', 'video', 'voice', 'file',
            'position', 'location', 'history', 'cardBubble',
            'card', 'cardDetail', 'locTitle', 'locSubTitle',
            'fileName', 'fileSize', 'fileStatus', 'videoDuration', 'videoPlay'
        ],
        side: Literal['sent', 'received', 'all'] = 'all',
        expect_missing: bool = False
    ) -> list[WebElement]:
        """
        消息接收-根据类型和方向获取聊天页面中的消息元素列表。
        区分发送方和接收方时，使用同一消息行内头像与目标元素的实际中心 X 坐标。
        没有头像的系统通知不归入 sent/received。
        """
        logger.info(f"🚀[Action-chat] - 正在检索聊天消息元素: 类型={msg_type}, 方向={side}...")
        locator = self._MSG_BASE_LOCATORS.get(msg_type)
        if not locator:
            raise ValueError(f"❌ ChatPage.get_message_elements - 不支持的消息类型: {msg_type}")

        if side not in {'sent', 'received', 'all'}:
            raise ValueError(f"❌ ChatPage.get_message_elements - 不支持的消息方向: {side}")

        if side == 'all':
            return self.find_elements(locator, timeout=2, expect_missing=expect_missing) or []
        
        message_rows = self.find_elements(ChatLocator.MESSAGE_LAYOUT_ITEM, expect_missing=expect_missing) or []
        try:
            screen_width = self.driver.get_window_size()['width']
        except Exception:
            screen_width = 1080
        mid_x = screen_width / 2.0

        filtered_elements = []
        for row in message_rows:
            try:
                avatars = row.find_elements(*ChatLocator.AVATAR_ITEM)
                row_elements = row.find_elements(*locator)

                if not avatars or not row_elements:
                    logger.debug(f"[Action-chat] - chat 跳过无法判断方向的消息行: {row}")
                    continue
                avatar_x = avatars[0].rect['x']
                is_sent_row = avatar_x > mid_x

                if (side == 'sent' and is_sent_row) or (side == 'received' and not is_sent_row):
                    filtered_elements.extend(row_elements)
            except Exception as exc:
                logger.debug(f"跳过无法判断方向的消息行: {exc}")
        return filtered_elements

    # 消息接收-统计聊天页面中指定类型与方向的消息数量
    def get_message_count(
        self,
        msg_type: Literal[
            'text', 'emoji', 'image', 'package', 'video', 'voice', 'file',
            'position', 'location', 'history', 'cardBubble', 'call', 'callBubble',
            'card', 'cardDetail', 'callTitle', 'callSubtitle', 'locTitle', 'locSubTitle',
            'fileName', 'fileSize', 'fileStatus', 'videoDuration', 'videoPlay'
        ] = 'text',
        side: Literal['sent', 'received', 'all'] = 'all'
    ) -> int:
        """消息接收-统计聊天页面中指定类型与方向的消息数量"""
        logger.info(f"🚀[Action-chat] - 正在统计聊天消息数量: 类型={msg_type}, 方向={side}...")
        items = self.get_message_elements(msg_type, side)
        count = len(items)
        logger.info(f"📊 [Count] 当前可见 {side} {msg_type} 消息数: {count}")
        return count

    # 消息接收-通过文本内容查找发送的文本消息气泡
    def find_sent_message_by_bubble(self, message: str) -> str:
        """消息接收-通过文本内容查找发送的文本消息气泡"""
        logger.info(f"🚀[Action-chat] - 正在通过气泡框查找发送的文本消息: '{message}'...")
        locator = ChatLocator.get_message_item_by_text(message)
        bubble_elems = self.find_elements(locator, condition='visibility', timeout=3)
        if bubble_elems:
            result = bubble_elems[-1].text
            logger.info(f"🚀[Action-chat] - chat 通过气泡框查找发送的文本消息: {result}")
            return result
        logger.info("🚀[Action-chat] - chat 通过气泡框未找到发送的文本消息")
        return ""

    # 消息接收-通过输入内容在聊天气泡中查找并验证内容
    def verify_message_content_by_input(self, message: str) -> str:
        """消息接收-通过输入内容在聊天气泡中查找并验证内容"""
        logger.info(f"🚀[Action-chat] - 正在获取已发送文本消息气泡进行内容校验: '{message}'...")
        bubble_elems = self.get_message_elements('text', side='sent')
        if not bubble_elems or len(bubble_elems) == 0:
            logger.error("没有找到已发送的消息元素")
            return ""
        logger.info(f"[Assert] 获取已发送消息内容: {bubble_elems[-1].text}")
        return bubble_elems[-1].text

    # 媒体消息-验证连续发送的多条媒体消息数量与描述文本
    def verify_batch_sent_messages(self, expected_count: int, msg_type: Literal['image', 'video'], expect_text: str = "", max_slide: int = 5) -> tuple[int, bool, int]:
        """
        媒体消息-验证连续发送的多条媒体消息数量与描述文本（自适应沉浸式透明顶底栏安全视口）
        :param expected_count: 预期成功发送的媒体数量
        :param msg_type: 'image' 或 'video'
        :param expect_text: 期待匹配的基准锚点文本（用于圈定本次批量发送的边界）
        :param max_slide: 最大向上回溯滑动次数
        :return: (实际找到的媒体消息数, 描述文本是否匹配成功, 失败红点消息数)
        """
        # 1. 智能等待最新一条媒体消息挂载并完成发送
        self.wait_for_batch_media_send_completed(expected_count=expected_count, msg_type=msg_type, timeout=30)
        
        found_count = 0
        fail_count = 0
        text_matched = False
        seen_container_ids = set()          # 记录已扫描消息容器的唯一元素标识 (高效防重)
        global_index = 0                    # 全局消息序号（0 为最新一条）

        # 2. 动态计算可视安全视口（避开顶部与底部透明栏的透光遮挡区）
        window_size = self.driver.get_window_size()
        win_w, win_h = window_size['width'], window_size['height']

        more_button = self.get_top_more_button()
        if more_button:
            safe_top_ys = more_button.rect['y']
            safe_top_ye = more_button.rect['y'] + more_button.rect['height'] + 5
        else:
            safe_top_ys = 118
            safe_top_ye = 239 + 5

        chat_input_container = self.get_chat_input_container()
        if chat_input_container:
            safe_bottom_ys = chat_input_container.rect['y']
            safe_bottom_ye = chat_input_container.rect['y'] + chat_input_container.rect['height']
        else:
            safe_bottom_ys = 2213
            safe_bottom_ye = 2326

        safe_height = max(100, safe_bottom_ys - safe_top_ye)
        logger.info(f"🔍 [Batch Verify] 安全可视视口锁定: Y∈[{safe_top_ye}, {safe_bottom_ys}], 高度={safe_height}px, 预期 {msg_type} × {expected_count}")

        for slide in range(max_slide):
            row_elems = self.get_message_layout_items(raise_exception=False) or []
            if not row_elems:
                logger.warning(f"第 {slide + 1} 次滑动后未获取到任何消息布局")
                break

            re_elems = list(reversed(row_elems))
            new_elements_in_slide = 0

            for container in re_elems:
                try:
                    c_rect = container.rect
                    elem_y = c_rect['y']
                    elem_h = c_rect['height']
                    elem_bottom = elem_y + elem_h

                    # 🌟 优先检测基准锚点文本（前置检测：无论是否被顶部导航栏或群公告遮挡，只要DOM中存在即可标记命中）
                    if expect_text and not text_matched:
                        text_nodes = container.find_elements(*ChatLocator.MESSAGE_CONTENT_ITEM)
                        if text_nodes:
                            content = text_nodes[0].text or text_nodes[0].get_attribute('text') or ""
                            if expect_text in content:
                                text_matched = True
                                logger.info(f"💬 [索引:{global_index}] 成功在DOM中匹配到基准锚点文本 '{expect_text}' (Y={elem_y})")

                    # 🌟 核心过滤 1：过滤被顶部透明导航栏遮挡的元素（元素底部在导航栏底边之上）
                    if elem_y < safe_top_ye:
                        logger.warning(f"⚠️ 元素Y坐标 {elem_y} 位于顶部导航栏区域({safe_top_ys} - {safe_top_ye})之上, 跳过")
                        continue

                    # 🌟 核心过滤 2：过滤被底部透明输入栏遮挡的元素（元素顶部在底部输入栏顶边之下）
                    if elem_bottom > safe_bottom_ys:
                        logger.warning(f"⚠️ 元素底部Y坐标 {elem_bottom} 位于底部导航栏区域({safe_bottom_ys} - {safe_bottom_ye})之下, 跳过")
                        continue

                    # 基于容器元素原生唯一 ID 去重，杜绝重复统计
                    if container.id in seen_container_ids:
                        continue

                    seen_container_ids.add(container.id)
                    new_elements_in_slide += 1

                    # 检查是否为发送失败的红点消息
                    fail_elems = container.find_elements(*ChatLocator.FAIL_MSG)
                    if fail_elems:
                        logger.warning(f"❌ [索引:{global_index}] 找到发送失败的消息(带感叹号红点)")
                        fail_count += 1
                        continue

                    # 检查是否包含目标类型的媒体
                    is_media = False
                    if msg_type == 'image':
                        images = container.find_elements(*ChatLocator.IMAGE_ITEM)
                        if images:
                            is_media = True
                            logger.info(f"📸 [索引:{global_index}] 匹配到第 {found_count + 1}/{expected_count} 张图片")
                    elif msg_type == 'video':
                        play_btns = container.find_elements(*ChatLocator.VIDEO_PLAY_BUTTON_ITEM)
                        durations = container.find_elements(*ChatLocator.VIDEO_DURATION_ITEM)
                        if play_btns and durations:
                            is_media = True
                            logger.info(f"🎥 [索引:{global_index}] 匹配到第 {found_count + 1}/{expected_count} 条视频")

                    global_index += 1

                    if is_media and found_count < expected_count:
                        found_count += 1

                    # 若数量已找齐且文本已命中，提前闭环退出
                    if found_count >= expected_count and (text_matched or not expect_text):
                        logger.info(f"✅ 找齐全部 {found_count} 条 {msg_type} 消息，校验通过！")
                        return found_count, text_matched, fail_count

                except Exception as e:
                    logger.warning(f"⚠️ 遍历过程中元素引用失效(Stale)，跳过当前项: {e}")
                    continue

            # 触顶防抖检测：若滑动后没有新消息进入视野，说明已到达聊天流顶部
            if slide > 0 and new_elements_in_slide == 0:
                logger.info("⚠️ 检测到本次滑动无新有效消息载入，已触达聊天记录顶部")
                break

            if found_count >= expected_count and (text_matched or not expect_text):
                return found_count, text_matched, fail_count

            # 3. 执行精准下拉滑动，拉出上方更早的历史消息
            if found_count < expected_count:
                logger.info(f"🔄 当前找到 {found_count}/{expected_count}，执行精准下拉以加载更多历史消息...")
                try:
                    target_elem = None
                    if row_elems:
                        try:
                            first_rect = row_elems[0].rect
                            first_y = first_rect['y']
                            first_bottom = first_y + first_rect['height']
                            if (first_y < safe_top_ye or first_bottom <= safe_top_ye) and len(row_elems) > 1:
                                logger.info(f"📍 开头首个元素(Y={first_y}, Bottom={first_bottom})被顶部遮挡，选用第二个元素作为起滑点")
                                target_elem = row_elems[1]
                            else:
                                logger.info(f"📍 开头首个元素满足要求，选用首个元素作为起滑点")
                                target_elem = row_elems[0]
                        except Exception as e:
                            logger.warning(f"获取首选元素坐标异常: {e}，将采用兜底坐标")

                    if target_elem:
                        elem_rect = target_elem.rect
                        start_x = int(elem_rect['x'] + elem_rect['width'] * 0.5)
                        start_y = int(elem_rect['y'] + elem_rect['height'] * 0.5)
                    else:
                        start_x = int(win_w * 0.5)
                        start_y = safe_top_ye + 50
                    start_y = max(safe_top_ye + 10, start_y)
                    end_x = start_x
                    end_y = max(start_y + 100, safe_bottom_ys - 10)

                    logger.info(f"🖐️ 执行下拉滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y})，滑动跨度: {end_y - start_y}px")
                    self.swipe(start_x, start_y, end_x, end_y, duration=1000)
                    time.sleep(0.5)
                except Exception as e:
                    logger.warning(f"滑动操作异常: {e}")

        logger.info(f"📊 批量消息校验结束: 实际匹配 {found_count}/{expected_count} 条 {msg_type}, 文本匹配: {text_matched}, 失败红点: {fail_count}")
        return found_count, text_matched, fail_count


    # ==============================================================================
    # 五、各具体消息类型专项操作 (Specific Message Types)
    # ==============================================================================
    # --------------------------------------------------------------------------
    # 1. 文本消息相关 (Text Messages)
    # --------------------------------------------------------------------------
    # 文本消息-获取聊天页面中所有文本消息内容
    def get_all_text_message_contents(self, side: str = "sent") -> list[str]:
        """文本消息-获取聊天页面中所有文本消息内容"""
        tx_elems = self.get_message_elements(msg_type="text", side=side)
        if not tx_elems or len(tx_elems) == 0:
            logger.error(f"没有找到聊天页面中的文本消息元素: side={side}")
            return []
        txs = [tx.text for tx in tx_elems]
        logger.info(f"[Assert] side={side} - 获取聊天页面所有文本消息内容: {txs}")
        return txs

    # 文本消息-点击第 n 条文本消息
    def click_text_message_by_index(self, index: int = -1, side: str = "sent", expect_missing: bool = False) -> None:
        """文本消息-点击第 n 条文本消息"""
        tx_elems = self.get_message_elements(msg_type="text", side=side, expect_missing=expect_missing)
        if not tx_elems or len(tx_elems) == 0:
            logger.error(f"没有找到聊天页面中的文本消息元素: side={side}")
            return
        logger.info(f"🚀[Action-chat] - chat 文本消息-准备点击第 {index} 条文本消息")
        tx_elems[index].click()

    # 文本消息-获取第 n 条文本消息内容
    def get_text_message_content_by_index(self, index: int = -1, side: str = "sent", expect_missing: bool = False) -> str:
        """文本消息-获取第 n 条文本消息内容"""
        st_elems = self.get_message_elements(msg_type="text", side=side, expect_missing=expect_missing)
        if not st_elems:
            logger.error(f"❌ 没有找到聊天页面中的文本消息元素: side={side}")
            return ""
        if index >= len(st_elems) or index < -len(st_elems):
            logger.error(f"❌ 索引 {index} 超出范围，当前文本消息数为: {len(st_elems)}")
            return ""
        
        raw_text = st_elems[index].get_attribute('text') or st_elems[index].text or ""
        message_content = raw_text.replace("\uFFFC ", "").replace("\uFFFC", "").strip()
        logger.info(f"📊 [Content] 第 {index} 条文本消息内容: {message_content}")
        return message_content

    # --------------------------------------------------------------------------
    # 2. 图片消息相关 (Image Messages)
    # --------------------------------------------------------------------------
    # 图片消息-获取指定索引图片消息的哈希值
    def get_chat_image_hash(self, index: int = -1, expect_missing: bool = False) -> str:
        """图片消息-获取指定索引图片消息的哈希值"""
        image_elements = self.get_message_elements(msg_type="image", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning("⚠️ [Content] - 已知没有图片，跳过该消息的断言")
            return ""
        if not image_elements:
            logger.error("❌ [Action-chat] - 未找到任何图片")
            return ""
        if index >= len(image_elements):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的图片")
            return ""
        
        image_ele = image_elements[index]
        actual_image_hash = ScreenshotUtils.dhash_auto(element=image_ele)
        return actual_image_hash

    # 图片消息-获取所有图片消息的哈希值列表
    def get_chat_all_image_hash(self) -> list[str]:
        """图片消息-获取所有图片消息的哈希值列表"""
        image_elements = self.get_message_elements(msg_type="image", side='all')
        if not image_elements:
            logger.error("❌ [Action-chat] - 未找到任何图片")
            return []
        
        image_hashes = []
        for image_ele in image_elements:
            actual_image_hash = ScreenshotUtils.dhash_auto(element=image_ele)
            image_hashes.append(actual_image_hash)
        logger.info(f"📊 [Content] 所有图片 hash 值: {image_hashes}")    
        return image_hashes

    # 图片消息-点击指定索引的图片消息进入大图浏览
    def click_image_message_by_index(self, index: int = -1, expect_missing: bool = False) -> None:
        """图片消息-点击指定索引的图片消息进入大图浏览"""
        image_elements = self.get_message_elements(msg_type="image", side='sent', expect_missing=expect_missing)
        if not image_elements or len(image_elements) == 0:
            logger.error("🚀[Action-chat] - chat 没有找到已发送的图片")
            raise NoSuchElementException("🚀[Action-chat] - chat 没有找到已发送的图片")
        if index >= len(image_elements) or index < -len(image_elements):
            logger.error("🚀[Action-chat] - chat 图片索引超出范围")
            raise IndexError("🚀[Action-chat] - chat 图片索引超出范围")
        logger.info(f"🚀[Action-chat] - chat 点击图片: {index}，等待消息详情页面加载...")
        image_elements[index].click()

    # 图片消息-长按预览的图片
    def long_press_preview_image(self) -> None:
        """图片消息-长按预览的图片"""
        preview_image = self.find_element(ChatLocator.PREVIEW_IMAGE_ITEM)
        logger.info("🚀[Action-chat] - chat 长按预览的图片")
        self.long_press_action(found_ele=preview_image)

    # 图片消息-点击预览图上的下载图标
    def click_download_icon_in_image_preview(self) -> None:
        """图片消息-点击预览图上的下载图标"""
        logger.info("🚀[Action-chat] - chat 点击图片下载图标")
        self.click(ChatLocator.IV_DOWNLOAD_ITEM)

    # --------------------------------------------------------------------------
    # 3. 视频消息相关 (Video Messages)
    # --------------------------------------------------------------------------
    # 视频消息-验证最后一条视频消息的状态是否完整成功
    def get_last_message_video_status(self) -> bool:
        """视频消息-验证最后一条视频消息的状态是否完整成功"""
        last_item = self.get_last_message_layout_item()
        
        has_play = len(last_item.find_elements(*ChatLocator.VIDEO_PLAY_BUTTON_ITEM)) > 0
        has_duration = len(last_item.find_elements(*ChatLocator.VIDEO_DURATION_ITEM)) > 0
        has_fail = len(last_item.find_elements(*ChatLocator.FAIL_MSG)) > 0
        
        status = has_play and has_duration and not has_fail
        logger.info(f"最后一条视频消息状态校验: {'通过' if status else '不通过(缺失组件或存在红点)'}")
        return status

    # 视频消息-获取指定索引的视频消息时长文本
    def get_chat_video_duration(self, index: int = -1, expect_missing: bool = False) -> str:
        """视频消息-获取指定索引的视频消息时长文本"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的视频消息时长文本...")
        vd_elems = self.get_message_elements(msg_type="videoDuration", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning(f"⚠️ [Content] - 已知没有视频时长，跳过该消息的断言")
            return ""
        if not vd_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何音频或视频时长控件")
            return ""
        if index >= len(vd_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的视频时长")
            return ""
        vd_elem = vd_elems[index]
        avd = vd_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条视频时长: {avd}")
        return avd

    # 视频消息-获取所有视频消息的时长文本列表
    def get_chat_all_video_duration(self) -> list[str]:
        """视频消息-获取所有视频消息的时长文本列表"""
        logger.info("🚀[Action-chat] - 正在获取屏幕中所有视频消息的时长文本列表...")
        vd_elems = self.get_message_elements(msg_type="videoDuration", side='all')
        if not vd_elems:
            logger.error(f"❌ [Action-chat] - 未找到任何视频时长控件")
            return []
        
        video_durations = []
        for vd_elem in vd_elems:
            video_durations.append(vd_elem.get_attribute('text'))
        logger.info(f"📊 [Content] 所有视频时长: {video_durations}")    
        return video_durations

    # --------------------------------------------------------------------------
    # 4. 文件消息相关 (File Messages)
    # --------------------------------------------------------------------------
    # 文件消息-获取指定索引的文件消息文件名
    def get_chat_file_name(self, index: int = -1, expect_missing: bool = False) -> str:
        """文件消息-获取指定索引的文件消息文件名"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的文件消息名称...")
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
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的文件消息大小...")
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
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的文件消息传输状态...")
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

    # 文件消息-获取所有文件消息 of 名列表
    def get_chat_all_file_name(self) -> list[str]:
        """文件消息-获取所有文件消息的名称列表"""
        logger.info("🚀[Action-chat] - 正在获取屏幕中所有文件消息的名称列表...")
        file_elems = self.get_message_elements(msg_type="fileName", side='all')
        if not file_elems:
            logger.error("❌ [Action-chat] - 未找到任何文件名称控件")
            return []
        
        file_names = []
        for file_elem in file_elems:
            file_names.append(file_elem.get_attribute('text'))
        logger.info(f"📊 [Content] 所有文件名称: {file_names}")    
        return file_names

    # --------------------------------------------------------------------------
    # 5. 位置消息相关 (Location Messages)
    # --------------------------------------------------------------------------
    # 位置消息-获取指定索引的位置消息标题文本
    def get_chat_location_title(self, index: int = -1, expect_missing: bool = False) -> str:
        """位置消息-获取指定索引的位置消息标题文本"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的位置消息标题文本...")
        title_elems = self.get_message_elements(msg_type="locTitle", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning("⚠️ [Content] - 已知没有位置消息标题，跳过该消息的断言")
            return ""
        if not title_elems:
            logger.error("❌ [Action-chat] - 未找到任何位置消息的标题")
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
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的位置消息副标题文本...")
        subtitle_elems = self.get_message_elements(msg_type="locSubTitle", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning("⚠️ [Content] - 已知没有位置消息副标题，跳过该消息的断言")
            return ""
        if not subtitle_elems:
            logger.error("❌ [Action-chat] - 未找到任何位置消息的副标题")
            return ""
        if index >= len(subtitle_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的位置消息的副标题")
            return ""
        subtitle_elem = subtitle_elems[index]
        subtitle_text = subtitle_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条位置消息副标题: {subtitle_text}")
        return subtitle_text

    # 位置消息 - 获取所有位置消息的标题列表
    def get_all_location_titles(self) -> list[str]:
        """位置消息 - 获取所有位置消息的标题列表"""
        logger.info("🚀[Action-chat] - 正在获取屏幕中所有位置消息的标题列表...")
        titles = self.get_message_elements('locTitle', side='sent')
        if not titles:
            logger.warning("未找到任何位置消息标题")
            return []
        msg_titles = [title.get_attribute("text") for title in titles]
        logger.info(f"所有位置消息标题: {msg_titles}")
        return msg_titles

    # 位置消息 - 获取已发送最后一条位置消息的标题与副标题
    def verify_location_sent_status(self) -> dict[str, str]:
        """位置消息 - 获取已发送最后一条位置消息的标题与副标题字典"""
        logger.info("🚀[Action-chat] - 正在获取已发送最后一条位置消息的标题与副标题...")
        titles = self.get_message_elements('locTitle', side='sent')
        subtitles = self.get_message_elements('locSubTitle', side='sent')
        
        if not titles or not subtitles:
            logger.error("❌ 没有找到已发送的位置气泡")
            raise NoSuchElementException("位置气泡未上屏")

        address_dict = {
            "title": titles[-1].text,
            "detail_address": subtitles[-1].text
        }
        logger.info(f"✅ 获取发送位置气泡信息: {address_dict}")
        return address_dict

    # 位置消息-点击最后一条位置消息进入地图详情页面
    def verify_location_enter_map_detail(self) -> None:
        """位置消息-点击最后一条位置消息进入地图详情页面"""
        logger.info("🚀 [Action-chat] 准备点击位置气泡进入地图详情")
        loc_elems = self.get_message_elements('locTitle', side='sent')
        if not loc_elems:
            logger.error("❌ 没有找到已发送的位置气泡，无法点击详情")
            raise NoSuchElementException("无法进入地图详情")
        loc_elems[-1].click()
        time.sleep(2)

    # --------------------------------------------------------------------------
    # 6. 名片消息相关 (Contact Card Messages)
    # --------------------------------------------------------------------------
    # 名片消息-获取指定索引的名片消息姓名标题
    def get_chat_card_name(self, index: int = -1, expect_missing: bool = False) -> str:
        """名片消息-获取指定索引的名片消息姓名标题"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的名片消息姓名标题...")
        title_elems = self.get_message_elements(msg_type="card", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning("⚠️ [Content] - 已知没有名片消息标题，跳过该消息的断言")
            return ""
        if not title_elems:
            logger.error("❌ [Action-chat] - 未找到任何名片消息的标题")
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
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的名片消息副标题文本...")
        subtitle_elems = self.get_message_elements(msg_type="cardDetail", side='sent', expect_missing=expect_missing)
        if expect_missing:
            logger.warning("⚠️ [Content] - 已知没有名片消息副标题，跳过该消息的断言")
            return ""
        if not subtitle_elems:
            logger.error("❌ [Action-chat] - 未找到任何名片消息的副标题")
            return ""
        if index >= len(subtitle_elems):
            logger.error(f"❌ [Action-chat] - 未找到索引为 {index} 的名片消息的副标题")
            return ""
        subtitle_elem = subtitle_elems[index]
        subtitle_text = subtitle_elem.get_attribute('text')
        logger.info(f"📊 [Content] 第 {index} 条名片消息副标题: {subtitle_text}")
        return subtitle_text

    # 名片消息-获取所有已发送名片的信息列表
    def get_all_send_contact_card_infos(self) -> list[dict[str, str]]:
        """名片消息-获取所有已发送名片的信息列表"""
        logger.info("🚀[Action-chat] - 正在获取屏幕中所有已发送名片的信息列表...")
        time.sleep(2)
        titles = self.get_message_elements('card', side='sent')
        stIds = self.get_message_elements('cardDetail', side='sent')
        card_types = self.find_elements(ChatLocator.CARD_TAG, timeout=2, expect_missing=True)
        
        if not titles or not stIds:
            logger.error("没有找到已发送的名片气泡")
            raise NoSuchElementException("名片气泡未上屏")

        card_info_list = []
        for i, (title, st_id) in enumerate(zip(titles, stIds)):
            c_type = card_types[i].text if i < len(card_types) else "个人名片"
            card_info = {
                "name": title.text,
                "stId": st_id.text,
                "card_type": c_type
            }
            card_info_list.append(card_info)
        logger.info(f"🚀 [Info] 已发送名片信息: {card_info_list}")
        return card_info_list

    # 名片消息-验证聊天气泡中是否成功显示指定名片信息
    def verify_card_in_chat(self, name: str) -> tuple[bool, Optional[dict[str, str]]]:
        """名片消息-验证聊天气泡中是否成功显示指定名片信息"""
        logger.info(f"🚀[Action-chat] - 正在验证聊天气泡中是否成功显示名片: '{name}'...")
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
    def click_last_card_message(self) -> None:
        """名片消息-点击最后一条名片消息进入详情页面"""
        logger.info("🚀 [Action-chat] 点击名片消息进入名片详情页")
        elem_card = self.get_last_message_layout_item()
        if not elem_card:
            logger.error("❌ 未找到名片消息，无法进入详情页")
            raise NoSuchElementException("未找到名片消息")
        elem_card.click()


    # --------------------------------------------------------------------------
    # 7. 音视频通话记录卡片消息相关 (Call Card Messages)
    # --------------------------------------------------------------------------
    # 通话卡片消息-获取指定索引的通话卡片标题 (如 "未接来电" / "已取消" / "已拒绝" / "通话时长 00:03")
    def get_chat_call_title(self, index: int = -1, side: Literal['sent', 'received', 'all'] = 'all', expect_missing: bool = False) -> str:
        """通话卡片消息-获取指定索引的通话卡片标题"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的通话卡片标题(方向: {side})...")
        title_elems = self.get_message_elements(msg_type="callTitle", side=side, expect_missing=expect_missing)
        if not title_elems:
            logger.error("❌ [Action-chat] 未找到任何通话卡片的标题")
            return ""
        if index >= len(title_elems):
            logger.error(f"❌ [Action-chat] 未找到索引为 {index} 的通话卡片标题")
            return ""
        title = title_elems[index].text
        logger.info(f"📞 [Content] 第 {index} 条通话卡片标题: {title}")
        return title

    # 通话卡片消息-获取指定索引的通话卡片副标题 (如 "轻触回拨")
    def get_chat_call_subtitle(self, index: int = -1, side: Literal['sent', 'received', 'all'] = 'all', expect_missing: bool = False) -> str:
        """通话卡片消息-获取指定索引的通话卡片副标题"""
        logger.info(f"🚀[Action-chat] - 正在获取索引为 {index} 的通话卡片副标题(方向: {side})...")
        sub_elems = self.get_message_elements(msg_type="callSubtitle", side=side, expect_missing=expect_missing)
        if not sub_elems:
            logger.error("❌ [Action-chat] 未找到任何通话卡片的副标题")
            return ""
        if index >= len(sub_elems):
            logger.error(f"❌ [Action-chat] 未找到索引为 {index} 的通话卡片副标题")
            return ""
        subtitle = sub_elems[index].text
        logger.info(f"📞 [Content] 第 {index} 条通话卡片副标题: {subtitle}")
        return subtitle

    # 通话卡片消息-点击最后一条通话卡片 (触发回拨呼叫)
    def click_last_call_message(self, side: Literal['sent', 'received', 'all'] = 'all') -> None:
        """通话卡片消息-点击最后一条通话卡片触发回拨呼叫"""
        logger.info(f"📞 [Action-chat] 点击最后一条通话卡片触发回拨(方向: {side})")
        cards = self.get_message_elements(msg_type="call", side=side)
        if not cards:
            logger.error("❌ 未找到通话卡片消息，无法点击")
            raise NoSuchElementException("通话卡片消息未上屏")
        cards[-1].click()


    # ==============================================================================
    # 六、收藏夹消息验证相关 (Collection Messages)
    # ==============================================================================
    # 收藏夹-验证从收藏夹发送的消息类型与内容是否正确
    def verify_from_collection_message_content(self, col_type: str = "text", exp_content: Optional[str] = None, msg: Optional[str] = None) -> bool:
        """收藏夹-验证从收藏夹发送的消息类型与内容是否正确"""
        logger.info(f"🚀[Action-chat] - 正在校验从收藏夹发送的消息(类型: {col_type}, 期望内容: '{exp_content}', 留言: '{msg}')...")
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


    # ==============================================================================
    # 七、消息多选与转发相关 (Multi-Select & Forwarding)
    # ==============================================================================
    # 多选操作-等待多选编辑页面加载完成
    def wait_for_multi_select_page_load(self, timeout: int = 10) -> bool:
        """多选操作-等待多选编辑页面加载完成"""
        logger.info(f"🚀[Action-chat] - 正在等待多选编辑页面加载(超时: {timeout}s)...")
        multi_select_button = self.is_element_exist(ChatLocator.IV_SHARE, timeout=timeout)
        if not multi_select_button:
            logger.error("❌ 多选转发页面未加载完成")
            return False
        logger.info("✅ 多选转发页面加载完成")
        return True

    # 多选操作-点击多选页面的转发按钮
    def click_forward_button(self) -> None:
        """多选操作-点击多选页面的转发按钮"""
        logger.info("✅ 点击多选转发页面转发按钮")
        self.click(ChatLocator.IV_SHARE)

    # 多选操作-点击多选页面的删除按钮
    def click_delete_button(self) -> None:
        """多选操作-点击多选页面的删除按钮"""
        logger.info("✅ 点击多选转发页面删除按钮")
        self.click(ChatLocator.IV_DELETE)

    # 多选操作-点击多选的逐条转发选项
    def click_batch_forward_button(self) -> None:
        """多选操作-点击多选的逐条转发选项"""
        logger.info("✅ 点击多选转发逐条转发按钮")
        self.click(ChatLocator.TV_FORWARD_ONE_BY_ONE)

    # 多选操作-点击多选的合并转发选项
    def click_merge_forward_button(self) -> None:
        """多选操作-点击多选的合并转发选项"""
        logger.info("✅ 点击多选转发合并转发按钮")
        self.click(ChatLocator.TV_FORWARD_COMBINE)

    # 多选操作-点击取消多选编辑状态
    def click_cancel_button(self) -> None:
        """多选操作-点击取消多选编辑状态"""
        logger.info("✅ 点击多选转发取消按钮")
        self.click(ChatLocator.TV_CANCEL, force_wait=True)

    # 多选操作-在聊天记录选择页中点击取消发送
    def click_cancel_send_button(self) -> None:
        """多选操作-在聊天记录选择页中点击取消发送"""
        logger.info("✅ 点击取消发送按钮（聊天记录）")
        self.click(ChatLocator.TOP_BACK_UNREAD_BG)

    # 多选操作-获取勾选的数量
    def get_select_num(self) -> int:
        """多选操作-获取勾选的数量"""
        text = self.get_attribute(ChatLocator.TV_SELECT_NUM, 'text')
        if not text:
            logger.error("❌ 未找到勾选数量")
            return 0
        return int(text.split("/")[0])

    # 多选操作-获取当前页面所有可勾选的消息复选框元素
    def _get_select_checkbox_buttons(self, filter_safe_area: bool = True) -> list[WebElement]:
        """多选操作-获取当前页面所有可勾选的消息复选框元素（自动过滤被顶部/底部固定栏遮挡的危险元素）"""
        check_btns = self.find_elements(ChatLocator.BT_SELECT_NOT_FAIL, timeout=2)
        if not check_btns:
            logger.error("❌ 未找到多选转发页面不包含发送失败消息的勾选按钮")
            return []

        if not filter_safe_area:
            return check_btns

        # 动态计算安全可视区域，防止滑动时顶部复选框与导航栏“取消”按键重叠导致误触退出多选
        try:
            # 1. 动态获取顶部“取消”按钮 (TOP_BACK_BUTTON) 的下边缘作为安全顶线
            top_back_elem = self.find_element(ChatLocator.TOP_BACK_BUTTON, timeout=1, expect_missing=True)
            if top_back_elem:
                min_y = top_back_elem.rect['y'] + top_back_elem.rect['height']
            else:
                min_y = int(self.driver.get_window_size()['height'] * 0.15)

            # 2. 动态获取底部“转发”按钮 (IV_SHARE) 的上边缘作为安全底线
            share_elem = self.find_element(ChatLocator.IV_SHARE, timeout=1, expect_missing=True)
            if share_elem:
                max_y = share_elem.rect['y']
            else:
                max_y = int(self.driver.get_window_size()['height'] * 0.86)
        except Exception:
            window_size = self.driver.get_window_size()
            min_y = int(window_size['height'] * 0.15)
            max_y = int(window_size['height'] * 0.86)

        safe_btns = []
        for btn in check_btns:
            try:
                rect = btn.rect
                btn_top = rect['y']
                btn_bottom = rect['y'] + rect['height']

                # 严格判定：复选框的顶部必须在顶部栏下方（留 15px 缓冲），且底部必须在底部栏上方（留 15px 缓冲）
                if (btn_top >= min_y + 15) and (btn_bottom <= max_y - 15):
                    safe_btns.append(btn)
                else:
                    logger.info(
                        f"🛡️ [SafeArea] 复选框 Y 范围 [{btn_top}, {btn_bottom}] 处于遮挡区 (安全区: {min_y + 15} ~ {max_y - 15})，跳过以防误触取消/操作栏"
                    )
            except Exception:
                safe_btns.append(btn)

        logger.info(f"✅ 多选页面已过滤安全可视区勾选按钮: {len(safe_btns)}/{len(check_btns)}")
        return safe_btns

    # 多选操作-点击勾选指定索引的消息复选框
    def click_select_checkbox_button(self, index: int = -1) -> None:
        """多选操作-点击勾选指定索引的消息复选框"""
        check_btn = self._get_select_checkbox_buttons()[index]
        logger.info(f"✅ 点击勾选消息按钮 (索引: {index})")
        check_btn.click()

    # 多选操作-批量勾选 X 条消息并支持滑动加载与上限拦截
    def click_x_select_checkbox_buttons(self, target_count: int, max_swipes: int = 100) -> int | str:
        """
        勾选指定数量(target_count)的消息。
        如果当前屏幕上的未勾选按钮不足，则滑动加载更多并继续勾选。
        利用 get_select_num 结合批次校准，避免每次点击重复查询 UI，提升多选性能与稳定性。
        如果尝试勾选第 101 条消息，将捕获 Toast 拦截提示并以字符串形式返回。
        """
        selected_count = 0
        swipes = 0
        current_selected = self.get_select_num()
        logger.info(f"📊 [MultiSelect] 进入多选，当前初始已勾选数量: {current_selected}/{target_count}")

        if current_selected >= target_count:
            return current_selected

        while current_selected < target_count and swipes < max_swipes:
            check_btns = self._get_select_checkbox_buttons()
            if not check_btns:
                logger.error("❌ 未找到多选页面勾选按钮")
                break

            check_btns = check_btns[::-1]
            for btn in check_btns:
                if current_selected >= target_count:
                    logger.info(f"🎉 成功完成勾选目标: {current_selected} 条消息")
                    break

                is_checked = btn.get_attribute("checked") == "true" or btn.get_attribute("selected") == "true"
                if not is_checked:
                    btn.click()
                    current_selected += 1

                    # 当已经成功勾选 100 条后，再去点击第 101 条时，App 会进行 Toast 阻断
                    if current_selected > 100:
                        toast_msg = self.get_toast()
                        if toast_msg:
                            logger.info(f"✅ 成功捕获到多选上限拦截提示: {toast_msg}")
                            return toast_msg
                        else:
                            logger.warning("⚠️ 尝试勾选第 101 条但未捕获到屏幕 Toast")
                            return "超过100条消息！"

                    logger.info(f"✅ 点击勾选消息按钮，当前预计已勾选 {current_selected}/{target_count} 条")

            real_selected = self.get_select_num()
            if real_selected > 0:
                current_selected = real_selected
            logger.info(f"📊 [MultiSelect] 当前屏幕批次勾选完成，已勾选 {current_selected}/{target_count} 条")

            if current_selected >= target_count:
                logger.info(f"🎉 成功完成勾选目标: {current_selected} 条消息")
                return current_selected

            logger.warning("⚠️ 当前屏幕消息不足或已全部勾选，尝试向下滑动加载更多...")
            self.swipe_page(slid_type="down", duration=600)
            swipes += 1

        final_count = self.get_select_num()
        if final_count < target_count:
            logger.warning(f"⚠️ 已达到最大滑动次数({max_swipes})，最终仅勾选了 {final_count} 条消息")
        return final_count

    # 合并转发-点击合并转发的消息卡片内容
    def click_merge_forward_message_content(self) -> None:
        """合并转发-点击合并转发的消息卡片内容"""
        logger.info("✅ 点击合并转发的消息内容")
        self.click(ChatLocator.CHAT_HISTORY_TEXT_CONTENT)

    # 合并转发-等待合并转发消息详情页面加载完成
    def wait_for_chat_merge_forward_page_load(self, timeout: int = 10) -> bool:
        """合并转发-等待合并转发消息详情页面加载完成"""
        res = self.is_element_exist(ChatLocator.HISTORY_TITLE_LAYOUT, timeout=timeout)
        if not res:
            logger.warning("❌ 聊天页面合并转发标题未加载完成")
            return False
        logger.info("✅ 聊天页面合并转发标题加载完成")
        return True

    # 合并转发-校验最新一条消息是否为合并转发记录卡片
    def get_merge_forward_message(self) -> bool:
        """合并转发-校验最新一条消息是否为合并转发记录卡片"""
        elem = self.get_last_message_layout_item()
        state = elem.find_elements(*ChatLocator.MERGE_CARD_KIND)
        if not state:
            logger.error("❌ 最后一条消息未找到合并转发标识组件 (MERGE_CARD_KIND)")
            return False
        kind_text = state[0].text or "聊天记录"
        logger.info(f"✅ 成功命中合并转发消息卡片，标识文案为: 【{kind_text}】")
        return True

    # 合并转发-等待聊天记录合并转发的发送状态提示消失
    def wait_for_history_send_complete(self, timeout: int = 60) -> bool:
        """合并转发-等待聊天记录合并转发的发送状态提示消失"""
        from locators.common.common_locator import CommonLocator
        hist_sending = self.wait_until_element_disappear(CommonLocator.TOAST_MSG, timeout=timeout)
        if not hist_sending:
            logger.error("❌ 聊天记录（合并转发）后 toast 发送中 未消失")
            return False
        logger.info("✅ 聊天记录（合并转发）后 toast 发送中 消失")
        return True

    # 合并转发-等待聊天记录合并转发详情页标题栏加载完成
    def wait_for_history_title_layout(self, timeout: int = 10) -> bool:
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
        his_elems = self.get_message_elements(msg_type="historyPreview", side='sent', expect_missing=expect_missing)
        if not his_elems:
            logger.error("❌ 未找到聊天记录内容元素")
            return False
    
        preview_text = his_elems[-1].get_attribute("text") or ""
        actual_lines = [line for line in preview_text.split('\n') if line.strip()]
        logger.info(f"✅ 获取到合并转发卡片预览文本: {len(actual_lines)} 条 - \n{preview_text}")

        # 合并转发气泡卡片外层最多展示 4 行预览摘要（超大批次如 100 条仅展示前 4 行）
        expected_preview_lines = min(expected_count, 4)
        if len(actual_lines) < expected_preview_lines:
            logger.warning(f"⚠️ 预览文本中解析出 {len(actual_lines)} 条，期望至少展示 {expected_preview_lines} 条预览摘要")

        logger.info("进行穿透测试，点击进入聊天记录详情页验证是否 Crash...")
        his_elems[-1].click()
        is_opened = self.wait_for_history_title_layout(timeout=3)
        self.click_back_button()

        if not is_opened:
            logger.error("❌ 点击聊天记录卡片后，未能成功打开详情页（可能发生 Crash 或卡死）")
            return False
        return True


    # ==============================================================================
    # 八、消息撤回、删除与二次确认弹窗相关 (Withdraw, Delete & Dialogs)
    # ==============================================================================
    # 撤回消息-获取指定索引的撤回系统提示及其上一条正常消息
    def get_withdraw_message(self, index: int = -1) -> Optional[tuple[str, str]]:
        """
        撤回消息-获取指定索引的撤回系统提示及其上一条正常文本消息
        :param index: 撤回系统提示索引，默认为 -1 (最新一条)
        :return: (withmsg, smsg) -> (撤回提示文本, 上一条正常发送的文本消息内容)
        """
        cmd_elements = self.find_elements(ChatLocator.CMD_MESSAGE_ITEM, timeout=2)
        if not cmd_elements:
            logger.error("❌ 未找到撤回等系统通知消息")
            return None
        withmsg = cmd_elements[index].text if abs(index) <= len(cmd_elements) else cmd_elements[-1].text
        normal_text_elements = self.get_message_elements('text', side='sent', expect_missing=True)
        smsg = normal_text_elements[-1].text if normal_text_elements else ""
        logger.info(f"✅ 获取到撤回系统提示: '{withmsg}', 上一条正常消息: '{smsg}'")
        return withmsg, smsg

    # 消息删除-等待删除确认弹窗显示
    def wait_for_del_dialog(self, timeout: int = 2) -> bool:
        """消息删除-等待删除确认弹窗显示"""
        del_dialog = self.is_element_exist(ChatLocator.TV_CONFIRM, timeout=timeout)
        if not del_dialog:
            logger.error("❌ 未找到删除弹窗")
            return False
        logger.info("✅ 找到删除弹窗")
        return True

    # 消息删除-点击弹窗中的二次确认删除按钮
    def click_del_confirm(self) -> None:
        """消息删除-点击弹窗中的二次确认删除按钮"""
        logger.info("✅ 点击二次确认删除按钮")
        self.click(ChatLocator.TV_CONFIRM, force_wait=True)
        time.sleep(1)

    # 消息删除-点击弹窗中的取消删除按钮
    def click_del_cancel(self) -> None:
        """消息删除-点击弹窗中的取消删除按钮"""
        logger.info("✅ 点击取消删除按钮")
        self.click(ChatLocator.TV_CANCEL, force_wait=True)

    # 消息弹窗-点击弹窗中的二次确认按钮
    def click_two_confirm(self) -> None:
        """消息弹窗-点击弹窗中的二次确认按钮"""
        logger.info("✅ 点击弹窗二次确认按钮")
        self.click(ChatLocator.TWO_CONFIRM, force_wait=True)
        time.sleep(1)

    # 消息弹窗-点击弹窗中的二次取消按钮
    def click_two_cancel(self) -> None:
        """消息弹窗-点击弹窗中的二次取消按钮"""
        logger.info("✅ 点击弹窗二次取消按钮")
        self.click(ChatLocator.TWO_CANCEL, force_wait=True)


    # ==============================================================================
    # 九、群成员昵称与系统/CMD通知相关 (Group Members & Notifications)
    # ==============================================================================
    # 群聊页面-获取群聊页面显示用户昵称
    def get_group_chat_user_name_elements(self, timeout: int = 2) -> list[WebElement]:
        """群聊页面-获取群聊页面显示用户昵称"""
        logger.info("🚀[Action-chat] - 获取群聊页面显示用户昵称")
        user_names = self.find_elements(ChatLocator.GROUP_CHAT_USER_NAME_ITEM, timeout=timeout)
        if not user_names or len(user_names) == 0:
            logger.error("没有找到群聊页面显示用户昵称")
            return []
        logger.info(f"[Assert] 获取群聊页面显示用户昵称成功，数量为: {len(user_names)}")
        return user_names

    # 群聊页面-获取群聊页面某个用户的昵称
    def get_group_chat_user_name_by_index(self, index: int = -1, timeout: int = 2) -> str:
        """群聊页面-获取群聊页面某个用户的昵称"""
        user_names = self.get_group_chat_user_name_elements(timeout=timeout)
        if not user_names or len(user_names) == 0:
            logger.error("没有找到群聊页面显示用户昵称")
            return ""
        user_name = user_names[index].text
        logger.info(f"[Assert] 获取群聊页面显示用户昵称: {user_name}")
        return user_name

    # CMD通知-获取聊天界面所有系统CMD通知消息: 包含撤回、截屏、进群消息、群聊等
    def get_all_cmd_notifications(self, timeout: int = 2) -> list[WebElement]:
        """CMD通知-获取聊天界面所有系统CMD通知消息: 包含撤回、截屏、进群消息、群聊等"""
        logger.info("🚀[Action-chat] - 获取聊天界面所有CMD通知消息")
        cmd_elems = self.find_elements(ChatLocator.CMD_MESSAGE_ITEM, timeout=timeout)
        if not cmd_elems or len(cmd_elems) == 0:
            logger.error("没有找到聊天界面中的CMD通知消息")
            return []
        logger.info(f"[Assert] 获取聊天界面所有CMD通知消息成功，数量为: {len(cmd_elems)}")
        return cmd_elems

    # CMD通知-获取聊天界面所有CMD通知消息-texts内容
    def get_cmd_notification_texts(self, index: Optional[int] = None, timeout: int = 2) -> list[str] | str:
        """CMD通知-获取聊天界面所有CMD通知消息-texts内容"""
        cmd_elems = self.get_all_cmd_notifications(timeout=timeout)
        if not cmd_elems:
            return [] if index is None else ""
        cmd_texts = [cmd.text for cmd in cmd_elems]
        logger.info(f"[Assert] 获取聊天界面所有CMD通知消息texts内容: {cmd_texts}")
        if index is None:
            return cmd_texts
        try:
            return cmd_texts[index]
        except IndexError:
            logger.error(f"❌ [Assert] 索引 {index} 越界，当前共有 {len(cmd_texts)} 条通知消息")
            return ""

    # CMD通知-校验指定索引的通知消息是否匹配特定正则表达式模式
    def is_cmd_notification_matching(self, pattern: str, index: int = -1, timeout: int = 2) -> bool:
        """CMD通知-校验指定索引的通知消息是否匹配特定正则表达式模式"""
        text = self.get_cmd_notification_texts(index=index, timeout=timeout)
        if not text:
            logger.warning(f"⚠️ [Assert] 未获取到索引为 {index} 的 CMD 通知文本")
            return False
        match_res = re.search(pattern, text)
        if match_res:
            logger.info(f"✅ [Assert] 找到匹配 of CMD 通知: '{text}' 匹配模式 '{pattern}'")
            return True
        logger.warning(f"❌ [Assert] CMD 通知不匹配: '{text}' 不匹配模式 '{pattern}'")
        return False

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
    def get_group_notice_content(self) -> Optional[str]:
        """群公告/群邀请-获取横幅群公告/群邀请文本内容"""
        banner_text = self.get_attribute(ChatLocator.NOTICE_TEXT, 'text')
        if banner_text:
            logger.info(f"✅ [Action] ChatPage 聊天页 - 获取到横幅群公告/群邀请文本内容: {banner_text}")
            return banner_text
        logger.warning("⚠️ [Action] ChatPage 聊天页 - 未获取到横幅群公告/群邀请文本内容")
        return None

    # 点击横幅公告/群邀请
    def click_group_notice(self) -> None:
        """点击横幅公告/群邀请"""
        logger.info("🚀 [Action] ChatPage 聊天页 - 点击横幅群公告/群邀请")
        self.click(ChatLocator.NOTICE_ANNOUNCEMENT)
        time.sleep(0.5)


    # ==============================================================================
    # 十、系统辅助与计时保活相关 (System Helpers & Timing)
    # ==============================================================================
    # 系统辅助-获取系统 Toast 提示文本
    def get_toast_text(self) -> str:
        """系统辅助-获取系统 Toast 提示文本"""
        logger.info("🚀[Action-chat] - 获取系统 Toast 提示文本")
        toast = self.get_toast()
        logger.info(f"🚀[Action-chat] - chat 获取 toast 结果: {toast}")
        return toast

    # 系统辅助-等待指定时间的倒计时并执行防息屏保活
    def wait_for_x_minutes(self, ti: int = 120) -> bool:
        """系统辅助-等待指定时间的倒计时并执行防息屏保活"""
        logger.info(f"⏳ 正在等待 {ti} 秒倒计时并执行防息屏保活")
        
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
                except Exception:
                    pass
            elif ti == 60:
                # 正常倒计时播报
                logger.info(f"⏳ 剩余时间: {ti} 秒")
            ti -= 1
        logger.info("✅ 倒计时结束")
        return True


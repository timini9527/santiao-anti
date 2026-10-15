from dataclasses import dataclass
from typing import List
import time
from core.logger_utils import logger, LogIcon
from pages.chat.core.chat_page import ChatPage




# ==========================================
# 1. 策略定义模型 (Strategy Model)
# ==========================================
@dataclass
class MessageStrategy:
    type_name: str                  # 消息类型名称
    expected_menus: List[str]       # 长按时制造数据并弹出菜单项的预期选项
    prepare_action_name: str        # 造数据对应的方法名

class MessageTypeStrategy:
    """定义不同消息类型的断言数据与执行策略"""
    
    TEXT = MessageStrategy("text", ["复制", "收藏", "转发", "多选", "回复", "撤回/删除"], "_prepare_text_msg")
    EMOJI = MessageStrategy("emoji", ["复制", "收藏", "转发", "多选", "回复", "撤回/删除"], "_prepare_emoji_msg")
    IMAGE = MessageStrategy("image", ["收藏", "转发", "多选", "回复", "撤回/删除", "添加表情"], "_prepare_image_msg")
    VOICE = MessageStrategy("voice", ["多选", "回复", "撤回/删除", "听筒"], "_prepare_voice_msg")
    VIDEO = MessageStrategy("video", ["转发", "多选", "撤回/删除"], "_prepare_video_msg")
    POSITION = MessageStrategy("position", ["转发", "多选", "撤回/删除"], "_prepare_position_msg")
    CARD = MessageStrategy("card", ["转发", "多选", "撤回/删除"], "_prepare_card_msg")
    GROUP_CARD = MessageStrategy("group_card", ["转发", "多选", "撤回/删除"], "_prepare_group_card_msg")
    FILE = MessageStrategy("file", ["转发", "多选", "回复", "撤回/删除"], "_prepare_file_msg")
    PACKAGE = MessageStrategy("package", ["转发", "多选", "撤回/删除", "添加表情"], "_prepare_package_msg")
    LINK = MessageStrategy("link", ["复制", "收藏", "转发", "多选", "回复", "撤回/删除"], "_prepare_link_msg")


    @classmethod
    def get_strategy(cls, msg_type: str) -> MessageStrategy:
        for attr_name, strategy in cls.__dict__.items():
            if isinstance(strategy, MessageStrategy) and strategy.type_name == msg_type.lower():
                return strategy
        raise ValueError(f"❌ 不支持的消息策略类型: {msg_type}")

# ==========================================
# 2. 数据建造者 (Data Builder)
# ==========================================
class ChatMessageBuilder(ChatPage):
    """
    专门负责构造各种聊天消息的工厂类。
    继承自 ChatPage，用于访问底层的点击发送行为，但将测试数据准备逻辑与验证逻辑剥离。
    """
    
    def build_message(self, strategy_name: str, **kwargs) -> bool:
        strategy = MessageTypeStrategy.get_strategy(strategy_name)
        logger.info(f"{LogIcon.SETUP} DataBuilder 准备测试数据，类型: {strategy.type_name}")
        handler = getattr(self, strategy.prepare_action_name, None)
        if not handler:
            raise NotImplementedError(f"❌ 未找到对应的构造方法: {strategy.prepare_action_name}")
        res = handler(**kwargs)
        time.sleep(0.5)
        return False if res is False else True

    def _prepare_text_msg(self, **kwargs) -> bool:
        content = kwargs.get("content", "发送收藏消息进行测试‼️⚠️🚀✔️✅♏🧑‍🚀🪲🍎✖️")
        self.send_message(content)
        # self.click_new_message_indicator()
        self.close_keyboard_or_panel()
        return True
    
    def _prepare_emoji_msg(self, **kwargs) -> bool:
        """发送/准备 Emoji 表情消息（长按/多选等专项测试数据准备：仅快速发送第一排表情，高效省时）"""
        from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
        emojiPage = ChatEmojiPage(self.driver)
        self.enter_emoji_page()
        emojiPage.sent_first_row_emoji(count=kwargs.get("count", 8))
        self.click_send_button()
        self.enter_emoji_page(is_open=False)
        self.click_new_message_indicator()
        self.close_keyboard_or_panel()
        return True
    
    def _prepare_package_msg(self, **kwargs) -> bool:
        """发送/准备第三方表情包消息"""
        from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage
        emoji_package = ChatEmojiPackagePage(self.driver)
        self.enter_emoji_page()
        try:
            emoji_package.switch_to_emoji_package(index=1)
            emoji_package.sent_emoji_package(strategy="first", count=1)
        finally:
            self.enter_emoji_page(is_open=False)
            self.close_keyboard_or_panel()
        return True
    
    # 收藏表情包专项：用于验证“收藏表情”功能，重置测试环境
    def _prepare_collection_emoji_msg(self, **kwargs) -> bool:
        """重置测试环境，清理所有收藏表情"""
        from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
        from pages.chat_options.emojis.chat_emoji_manage_page import ChatEmojiManagePage
        emojiPage = ChatEmojiPage(self.driver)
        emojiManagePage = ChatEmojiManagePage(self.driver)
        self.enter_emoji_page()
        emojiPage.open_collection_emoji_manage()
        is_delete = emojiManagePage.clear_all_collection_emojis()
        self.enter_emoji_page()
        return is_delete
    
    # 收藏表情包专项：用于验证“已添加表情包”是否成功
    def _prepare_has_pkg_msg(self, **kwargs) -> bool:
        """校验当前是否已添加表情包"""
        from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
        emojiPage = ChatEmojiPage(self.driver)
        self.enter_emoji_page()
        emojiPage.open_collection_emoji_manage()
        has_pkg = emojiPage.get_collection_emoji_pkg_item() >= 1
        logger.info(f"{LogIcon.SETUP} DataBuilder 准备测试数据，has_pkg: {has_pkg}")
        self.enter_emoji_page()
        return has_pkg

    def _prepare_image_msg(self, **kwargs) -> bool:
        """发送/准备单张相册图片消息"""
        from pages.chat_options.images.chat_image_page import ChatImagePage
        img = ChatImagePage(self.driver)
        img.open_panel_to_album()
        img.select_single_image(mode=1)
        img.click_send_button()
        self.click_add_button()
        return True

    def _prepare_voice_msg(self, **kwargs) -> bool:
        """发送/准备语音消息"""
        from pages.chat_options.voice.chat_voice_page import ChatVoicePage
        voice = ChatVoicePage(self.driver)
        voice.click_voice_button()
        voice.get_voice_list_snapshot()
        voice.send_voice_message(hold_time=kwargs.get("hold_time", 5))
        voice.click_voice_button()
        return True

    def _prepare_video_msg(self, **kwargs) -> bool:
        """发送/准备单张视频消息"""
        from pages.chat_options.videos.chat_video_page import ChatVideoPage
        video = ChatVideoPage(self.driver)
        video.open_panel_to_album()
        video.select_single_video(mode=1)
        video.click_send_button()
        return True

    def _prepare_position_msg(self, **kwargs) -> bool:
        """发送/准备地理位置消息"""
        from pages.chat_options.location.chat_position_page import ChatPositionPage
        pos = ChatPositionPage(self.driver)
        try:
            pos.open_panel_enter_location_page()
            pos.click_current_location_button()
            toast = pos.get_toast(timeout=1.5)
            if bool(toast):
                logger.warning(f"{LogIcon.WARN} 获取地理位置出现提示: {toast}，跳过本次位置消息发送")
                self.back_to_chat_page()
                return False
            pos.click_send_button()
            self.click_add_button()
            return True
        except Exception as e:
            logger.error(f"{LogIcon.FAIL} 发送地理位置过程发生异常: {e}")
            self.back_to_chat_page()
            raise RuntimeError(f"{LogIcon.FAIL} [前置数据准备失败] 发送地理位置异常: {e}")

    def _prepare_card_msg(self, **kwargs) -> bool:
        """发送/准备联系人名片消息"""
        from pages.friend.profile.chat_contact_card_page import ChatContactCardPage
        from pages.common.contact_select_page import ContactSelectPage
        ChatContactCardPage(self.driver).open_panel_enter_contact_card_page()
        contact = kwargs.get("contact_name", "测试0222")
        ContactSelectPage(self.driver).click_contact_by_name(name=contact, select_type="share")
        ContactSelectPage(self.driver).click_confirm()
        self.click_add_button()
        return True

    def _prepare_file_msg(self, **kwargs) -> bool:
        """发送/准备本地文件消息（使用固定文件名搜索并发送，稳定高效）"""
        from pages.chat_options.file.chat_file_page import ChatFilePage
        file_page = ChatFilePage(self.driver)
        file_page.open_panel_enter_file_page()
        file_page.wait_for_file_page_load()
        file_name = kwargs.get("file_name", "测试-图片")
        file_page.search_and_select_file_by_name(file_name)
        # 若软键盘或加号/表情面板处于打开状态，执行收起关闭
        self.close_keyboard_or_panel()
        return True

    def _prepare_group_card_msg(self, **kwargs) -> bool:
        """准备/发送群名片消息"""
        from pages.groups.setting.general.group_setting_page import GroupSettingPage
        from pages.common.session_select_page import SessionSelectPage
        from pages.chat.list.chat_list_page import ChatListPage
        from pages.main.main_page import MainPage

        target_name = self.get_group_name() or self.get_top_name()
        default_group = kwargs.get("group_name", "测试群aaaaa")
        backup_group = kwargs.get("backup_group_name", "测试群bbbbb")
        source_group = backup_group if target_name == default_group else default_group

        logger.info(f"{LogIcon.ACTION} 准备从群【{source_group}】分享群名片至目标会话【{target_name}】")
        main_page = MainPage(self.driver)
        chat_list = ChatListPage(self.driver)
        group_setting = GroupSettingPage(self.driver)
        session_select = SessionSelectPage(self.driver)

        main_page.go_to_main_page()
        chat_list.enter_chat(source_group)
        self.wait_for_chat_page_load()
        self.click_more_button()
        group_setting.wait_for_setting_page_load()
        group_setting.click_group_share()
        session_select.wait_for_session_page_load(msg_type=1)

        is_selected = session_select.select_session_by_name(target_name)
        if is_selected:
            session_select.send_share_and_verify_toast('转发成功')
            logger.info(f"{LogIcon.SUCCESS} 成功将群【{source_group}】名片分享至【{target_name}】并恢复至聊天界面")
        else:
            logger.warning(f"{LogIcon.WARN} [GroupCard] 会话选择页未找到目标会话: 【{target_name}】")

        main_page.go_to_main_page()
        chat_list.enter_chat(target_name)
        self.wait_for_chat_page_load()
        return is_selected

    def _prepare_link_msg(self, **kwargs) -> bool:
        """发送/准备链接消息"""
        url = kwargs.get("url", "https://www.baidu.com")
        self.send_message(url)
        return True


    # 统一消息特征值提取方法，将分散的提取逻辑集中起来，方便维护和扩展
    def get_message_feature(self, msg_type: str, expect_missing: bool = False, index: int = -1) -> dict:
        logger.info(f"{LogIcon.FIND} 正在提取 {msg_type} 消息的 UI 特征 (index={index})")
        
        if msg_type == "package":
            from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage
            emojiPackagePage = ChatEmojiPackagePage(self.driver)

        m_type = msg_type.lower()
        if m_type in ["text", "emoji"]:
            return {"内容": self.get_text_message_content_by_index(index=index, expect_missing=expect_missing)}
        elif m_type == "image":
            return {"哈希值": self.get_chat_image_hash(index=index, expect_missing=expect_missing)}
        elif m_type == "package":
            return {"表情哈希": emojiPackagePage.get_emoji_hashcode(index=index, expect_missing=expect_missing)}
        elif m_type in ["voice", "video"]:
            return {"时长": self.get_chat_video_duration(index=index, expect_missing=expect_missing)}
        elif m_type == "position":
            return {
                "标题": self.get_chat_location_title(index=index, expect_missing=expect_missing),
                "副标题": self.get_chat_location_subtitle(index=index, expect_missing=expect_missing)
            }
        elif m_type == "card":
            return {
                "名字": self.get_chat_card_name(index=index, expect_missing=expect_missing),
                "副标题": self.get_chat_card_subtitle(index=index, expect_missing=expect_missing)
            }
        elif m_type == "file":
            return {
                "文件名": self.get_chat_file_name(index=index, expect_missing=expect_missing),
                "文件状态": self.get_chat_file_status(index=index, expect_missing=expect_missing)
            }
        return {}


# ==========================================
# 3. 菜单操作与断言策略 (Action & Verify Strategy)
# ==========================================
@dataclass
class MenuActionStrategy:
    action_method: str      # 执行的方法名（映射到 Page 对象中的具体方法）
    verify_type: str        # 校验方式（toast, page_change, msg_disappear 等）
    expect_value: str       # 预期结果的关键字或特征值

class MenuActionConfig:
    """定义长按菜单项的自动化执行与断言策略"""
    
    STRATEGIES = {
        "复制": MenuActionStrategy("click_copy", "toast", "已复制到剪贴板"),
        "收藏": MenuActionStrategy("click_favorite", "toast", "添加成功"),
        "转发": MenuActionStrategy("click_forward", "page_change", "选择"),
        "多选": MenuActionStrategy("click_multi_select", "ui_state", "multi_select_bar"),
        "回复": MenuActionStrategy("click_reply", "ui_state", "reply_layout"),
        "撤回": MenuActionStrategy("click_revoke", "msg_disappear", "revoke_tip"),
        "删除": MenuActionStrategy("click_delete", "msg_disappear", "deleted"),
        "听筒": MenuActionStrategy("click_speaker", "toast", "听筒"),
        "扬声器": MenuActionStrategy("click_speaker", "toast", "扬声器"),
        "添加表情": MenuActionStrategy("click_add_emoji", "toast", "添加成功"),
    }

    @classmethod
    def get_strategy(cls, menu_name: str) -> MenuActionStrategy:
        return cls.STRATEGIES.get(menu_name)

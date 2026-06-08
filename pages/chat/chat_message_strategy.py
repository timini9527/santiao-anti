from dataclasses import dataclass
from typing import List
import time
from core.logger_utils import logger
from pages.chat.chat_page import ChatPage




# ==========================================
# 1. 策略定义模型 (Strategy Model)
# ==========================================
@dataclass
class MessageStrategy:
    type_name: str                  # 消息类型名称
    expected_menus: List[str]       # 长按时预期弹出的菜单项
    prepare_action_name: str        # 造数据对应的方法名

class MessageTypeStrategy:
    """定义不同消息类型的断言数据与执行策略"""
    
    TEXT = MessageStrategy("text", ["复制", "收藏", "转发", "多选", "回复", "撤回/删除"], "_prepare_text_msg")
    EMOJI = MessageStrategy("emoji", ["复制", "收藏", "转发", "多选", "回复", "撤回/删除"], "_prepare_emoji_msg")
    IMAGE = MessageStrategy("image", ["收藏", "转发", "多选", "回复", "撤回/删除"], "_prepare_image_msg")
    VOICE = MessageStrategy("voice", ["多选", "回复", "撤回/删除", "听筒"], "_prepare_voice_msg")
    VIDEO = MessageStrategy("video", ["转发", "多选", "撤回/删除"], "_prepare_video_msg")
    POSITION = MessageStrategy("position", ["转发", "多选", "撤回/删除"], "_prepare_position_msg")
    CARD = MessageStrategy("card", ["转发", "多选", "撤回/删除"], "_prepare_card_msg")
    FILE = MessageStrategy("file", ["转发", "多选", "回复", "撤回/删除"], "_prepare_file_msg")
    PACKAGE = MessageStrategy("package", ["转发", "多选", "撤回/删除", "添加表情"], "_prepare_package_msg")

    @classmethod
    def get_strategy(cls, msg_type: str) -> MessageStrategy:
        for attr_name, strategy in cls.__dict__.items():
            # 1. isinstance(strategy, MessageStrategy): 
            #    过滤掉类中的内置属性（如 __doc__, __module__ 等）和方法，只查找我们定义的 MessageStrategy 实例
            # 2. strategy.type_name == msg_type.lower(): 
            #    将传入的字符串转为小写进行比对，实现大小写不敏感的匹配（例如传 "TEXT" 或 "text" 都能匹配到）
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
    
    def build_message(self, strategy_name: str, **kwargs):
        """
        根据策略名称，自动分发执行对应的发送逻辑。
        
        核心机制说明：
        1. 先通过 MessageTypeStrategy.get_strategy() 拿到策略对象（如 TEXT 策略）
        2. 策略对象中包含一个字符串属性 prepare_action_name（如 "_prepare_text_msg"）
        3. 通过 Python 内置的 getattr() 反射机制，将这个字符串"变"成当前类中真正可调用的方法
        4. 最后执行该方法，完成消息的发送

        举例：
            strategy_name = "text"
            → strategy.prepare_action_name = "_prepare_text_msg"
            → getattr(self, "_prepare_text_msg") → 返回 self._prepare_text_msg 方法对象
            → handler(**kwargs) 等价于 self._prepare_text_msg(**kwargs)

        这样做的好处是：新增消息类型时，只需在 MessageTypeStrategy 中添加一条配置，
        并在本类中实现对应的 _prepare_xxx_msg 方法即可，无需修改 build_message 本身。
        """
        # 1. 根据传入的类型名（如 "text"、"image"），从策略枚举中获取完整的策略配置
        strategy = MessageTypeStrategy.get_strategy(strategy_name)
        
        logger.info(f"🧪 [Setup] - DataBuilder 正在准备测试数据，类型: {strategy.type_name}")
        
        # 2. 反射获取方法：将策略中配置的方法名字符串（如 "_prepare_text_msg"）
        #    动态解析为本类中实际存在的方法对象。如果找不到则返回 None。
        handler = getattr(self, strategy.prepare_action_name, None)
        if not handler:
            raise NotImplementedError(f"❌ 未找到对应的构造方法: {strategy.prepare_action_name}")
        
        # 3. 执行该方法，**kwargs 会透传给具体的 _prepare_xxx_msg，
        #    使调用方可以灵活定制参数（如 content、hold_time、contact_name 等）
        handler(**kwargs)
        time.sleep(0.5)

    def _prepare_text_msg(self, **kwargs):
        content = kwargs.get("content", "发送收藏消息进行测试‼️⚠️🚀✔️✅♏🧑‍🚀🪲🍎✖️")
        self.send_message(content)
    
    def _prepare_emoji_msg(self, **kwargs):
        from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
        emojiPage = ChatEmojiPage(self.driver)
        self.enter_emoji_page()
        emojiPage.sent_all_emoji()
        input_text = self.get_input_text()
        self.click_send_button()
        self.enter_emoji_page()
    
    def _prepare_package_msg(self, **kwargs):
        from pages.chat_options.emojis.chat_emoji_package_page import ChatEmojiPackagePage
        emoji_package = ChatEmojiPackagePage(self.driver)
        self.enter_emoji_page()
        emoji_package.switch_to_emoji_package(index=1)
        emoji_package.sent_emoji_package(strategy="first", count=1)
        self.enter_emoji_page()
    
    # 收藏表情包专项：用于验证“收藏表情”功能，重置测试环境
    def _prepare_collection_emoji_msg(self, **kwargs) -> bool:
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
        from pages.chat_options.emojis.chat_emoji_page import ChatEmojiPage
        emojiPage = ChatEmojiPage(self.driver)
        self.enter_emoji_page()
        emojiPage.open_collection_emoji_manage()
        has_pkg = emojiPage.get_collection_emoji_pkg_item() >= 1
        logger.info(f"🧪 [Setup] - DataBuilder 正在准备测试数据，has_pkg: {has_pkg}")
        self.enter_emoji_page()
        return has_pkg

    def _prepare_image_msg(self, **kwargs):
        from pages.chat_options.images.chat_image_page import ChatImagePage
        img = ChatImagePage(self.driver)
        img.open_panel_to_album()
        img.select_single_image(mode=1)
        img.click_send_button()
        self.click_add_button()

    def _prepare_voice_msg(self, **kwargs):
        from pages.chat_options.voice.chat_voice_page import ChatVoicePage
        voice = ChatVoicePage(self.driver)
        voice.click_voice_button()
        voice.get_voice_list_snapshot()
        voice.send_voice_message(hold_time=kwargs.get("hold_time", 10))
        voice.click_voice_button()

    def _prepare_video_msg(self, **kwargs):
        from pages.chat_options.videos.chat_video_page import ChatVideoPage
        video = ChatVideoPage(self.driver)
        video.open_panel_to_album()
        video.select_single_video(mode=1)
        video.click_send_button()
        self.click_add_button()

    def _prepare_position_msg(self, **kwargs):
        from pages.chat_options.location.chat_position_page import ChatPositionPage
        pos = ChatPositionPage(self.driver)
        pos.open_panel_enter_location_page()
        pos.click_current_location_button()
        pos.click_send_button()
        self.click_add_button()

    def _prepare_card_msg(self, **kwargs):
        from pages.chat_options.contact.chat_contact_card_page import ChatContactCardPage
        from pages.common.contact_select_page import ContactSelectPage
        ChatContactCardPage(self.driver).open_panel_enter_contact_card_page()
        contact = kwargs.get("contact_name", "测试0222")
        ContactSelectPage(self.driver).click_contact_by_name(name=contact, select_type="share")
        ContactSelectPage(self.driver).click_confirm()
        self.click_add_button()

    def _prepare_file_msg(self, **kwargs):
        from pages.chat_options.file.chat_file_page import ChatFilePage
        file_page = ChatFilePage(self.driver)
        file_page.open_panel_enter_file_page()
        file_page.wait_for_file_page_load()
        file_page.click_file_menu_button()
        file_page.click_sub_menu_item(kwargs.get("sub_menu", "图片"))
        file_page.select_any_file_in_dir(
            primary_dir=kwargs.get("dir", "santiaotalk"),
            file_type=kwargs.get("file_type", 'image')
        )
        file_page.click_send_file()
        self.click_add_button()

    # 统一消息特征值提取方法，将分散的提取逻辑集中起来，方便维护和扩展
    def get_message_feature(self, msg_type: str, expect_missing: bool = False, index: int = -1) -> dict:
        """
        根据策略名称统一提取当前消息的 UI 特征值，并封装为字典返回。
        :param msg_type: 消息类型 ("text", "image", "file" 等)
        :param expect_missing: 断言元素消失时设为 True，防止抛出 NoSuchElementException
        :param index: 消息下标（默认提取最后一条 -1）
        """
        logger.info(f"🔎 正在提取 {msg_type} 消息的 UI 特征 (index={index})")
        
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
                # "文件大小": self.get_chat_file_size(index=index, expect_missing=expect_missing),
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
        "复制": MenuActionStrategy("click_copy", "toast", "已复制"),
        "收藏": MenuActionStrategy("click_favorite", "toast", "收藏成功"),
        "转发": MenuActionStrategy("click_forward", "page_change", "选择联系人"),
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












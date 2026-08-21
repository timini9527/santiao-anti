import os
import json
from dataclasses import dataclass
from typing import List, Optional

from locators.chat.core.chat_locator import ChatLocator
from locators.home.home_locator import HomeLocator

@dataclass
class ChatSessionStrategy:
    """
    会话策略类：封装不同会话类型的差异数据
    """
    desc: str                                                       # 描述 (用于 Allure 报告显示)
    name: str                                                       # 会话名称 (私聊名 或 群聊名)
    phone: str = ""                                                 # 搜索的手机号或STID或群ID
    st_id: str = ""                                                 # 搜索的STID
    is_admin: bool = False                                          # 身份标识：是否为管理员/群主 (影响长按菜单项)
    notice_locator: tuple = HomeLocator.CONVERSATION_MUTE_TEXT      # 默认通知校验元素
    top_locator: tuple = HomeLocator.CONVERSATION_TOP_TEXT          # 默认置顶校验元素
    delete_locator: tuple = HomeLocator.CONVERSATION_DELETE_TEXT    # 默认删除校验元素

    def __str__(self):
        return self.desc

# --- 解析 Web 传入的动态回执表单 ---
web_receipt = {}
receipt_str = os.environ.get("WEB_RECEIPT_DATA")
if receipt_str:
    try:
        web_receipt = json.loads(receipt_str)
    except Exception:
        pass

# --- 定义具体策略实例 ---
# 1. 私聊策略
# PRIVATE_USER = ChatSessionStrategy(
#     desc="私聊模式",
#     name=os.environ.get("PRIVATE_CHAT_NAME") or "1234567890",
#     phone="38100000225",
#     st_id=""
# )
PRIVATE_USER1 = ChatSessionStrategy(
    desc="私聊模式",
    name=os.environ.get("PRIVATE_CHAT_NAME") or "测试0222",
    phone="38100000222",
    st_id="MN0123"
)
PRIVATE_USER2 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户1") or "测试0224",
    phone="38100000224",
    st_id=""
)
PRIVATE_USER3 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户2") or "测试0225",
    # name=web_receipt.get("私聊用户2") or "测试114",
    phone="38100000225",
    st_id="",
)

PRIVATE_USER4 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户3") or "测试0229",
    phone="38100000229"
)


PRIVATE_USER5 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户5") or "测试0226",
    phone="38100000226"
)
PRIVATE_USER6 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户6") or "测试0227",
    phone="38100000227"
)
PRIVATE_USER7 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户7") or "测试0228",
    phone="38100000228"
)
PRIVATE_USER8 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户8") or "测试0229",
    phone="38100000229"
)

# 停用或注销用户
PRIVATE_DISABLE1 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户4") or "测试0221",
    phone="38100000221"
)
PRIVATE_DISABLE2 = ChatSessionStrategy(
    desc="私聊模式",
    name=web_receipt.get("私聊用户5") or "ST_FdhwIr7",
    phone=""
)
# 2. 群聊策略
GROUP_STRATEGY = ChatSessionStrategy(
    desc="群聊模式",
    name=os.environ.get("GROUP_CHAT_NAME") or "测试群aaaaa",
    is_admin=True
)
GROUP_STRATEGY2 = ChatSessionStrategy(
    desc="群聊模式",
    name=web_receipt.get("群聊名称1") or "测试群bbbbb",
    is_admin=True
)
GROUP_STRATEGY3 = ChatSessionStrategy(
    desc="群聊模式",
    name=web_receipt.get("群聊名称3") or "测试群ccccc",
    is_admin=True
)
GROUP_STRATEGY4 = ChatSessionStrategy(
    desc="群聊模式",
    name=web_receipt.get("群聊名称4") or "测试群ddddd",
    is_admin=True
)
GROUP_STRATEGY5 = ChatSessionStrategy(
    desc="群聊模式",
    name=web_receipt.get("群聊名称5") or "测试群eeeee",
    is_admin=True
)

TEST_GROUPS = [
    ChatSessionStrategy(
        desc="群聊模式",
        name=f"测试{i:03d}",
        is_admin=True
    )
    for i in range(1, 6)
]


# 3.侧滑置顶策略
SLIDE_STRATEGY = ChatSessionStrategy(
    desc="侧滑模式",
    name="侧滑"
)

# 3. 侧滑操作策略
@dataclass
class SlideSettingAction:
    story: str                      # 测试故事描述 (用于 Allure 报告)
    locator_attr: str               # 对应的定位器属性名 (如 notice_locator, top_locator)
    expected_menu_texts: List[str]  # 侧滑菜单中预期的文本选项列表
    get_status_method: str          # 获取当前状态的方法名
    expected_status: str            # 操作后预期的状态值 ("true" 或 "false")
    action_desc: str                # 动作简述 (用于测试用例命名或日志)

# 配置侧滑各项具体操作的参数，将这些实例推入测试用例中
SETTING_ACTIONS = [
    SlideSettingAction("侧滑设置(静音)", "notice_locator", ["静音", "取消静音", "免打扰"], "get_switch_remind_status", "true", "打开静音"),
    SlideSettingAction("侧滑设置(取消静音)", "notice_locator", ["静音", "取消静音", "免打扰"], "get_switch_remind_status", "false", "关闭静音"),
    SlideSettingAction("侧滑设置置顶", "top_locator", ["置顶", "取消置顶"], "get_switch_top_status", "true", "置顶状态"),
    SlideSettingAction("侧滑设置取消置顶", "top_locator", ["置顶", "取消置顶"], "get_switch_top_status", "false", "取消置顶状态"),
]

# 4. 侧滑删除操作策略
@dataclass
class SlideDeleteAction:
    story: str
    dialog_action_method: str  # 在弹窗上执行点击动作页面的方法名
    expected_session_exists: Optional[bool]  # 操作后预期会话是否存在于列表中。为空则表示需要特殊处理（如进入会话校验条数）
    action_desc: str

DELETE_ACTIONS = [
    SlideDeleteAction("侧滑删除会话(取消删除)", "click_conversation_delete_dialog_cancel", True, "取消删除"),
    SlideDeleteAction("侧滑删除会话(清空聊天记录)", "click_conversation_delete_dialog_clear_chat_record", None, "清空聊天记录"),
    SlideDeleteAction("侧滑删除会话(确认删除)", "click_conversation_delete_dialog_confirm", False, "确认删除"),
]

# 5. 置顶会话折叠验证策略
@dataclass
class TopFoldScenario:
    """
    置顶折叠验证场景：驱动 test_top_fold 的参数化数据
    所有验证行为由字段控制，测试方法体内无需 if/elif 分支
    """
    desc: str                       # 场景描述 (用于 Allure 报告和 pytest ids)
    story: str                      # Allure story
    pin_count: int                  # 需要置顶的会话数量
    expect_fold_visible: bool       # 最终校验时折叠入口是否可见
    unpin_one: bool = False         # 置顶后是否取消一个再校验
    check_fold_count: bool = False  # 是否校验折叠数量 == pin_count
    check_fold_click: bool = False  # 是否校验点击折叠后会话被隐藏或展开

    def __str__(self):
        return self.desc

TOP_FOLD_SCENARIOS = [
    TopFoldScenario(
        desc="置顶<5个_无折叠",
        story="置顶会话数量<5，不显示折叠状态",
        pin_count=4,
        expect_fold_visible=False,
    ),
    TopFoldScenario(
        desc="置顶>=5个_有折叠",
        story="置顶会话数量>=5，显示折叠状态，并且折叠数量与置顶数量一致，点击折叠置顶会话被折叠",
        pin_count=5,
        expect_fold_visible=True,
        check_fold_count=True,
        check_fold_click=True,
    ),
    TopFoldScenario(
        desc="置顶5->4个_折叠消失",
        story="置顶会话数量5->4，折叠会话状态消失",
        pin_count=5,
        expect_fold_visible=False,
        unpin_one=True,
    ),
    TopFoldScenario(
        desc="置顶 8 个_折叠显示",
        story="置顶会话数量 8，折叠会话状态显示",
        pin_count=8,
        expect_fold_visible=True,
        check_fold_count=True,
    ),
]


# 6. 气泡消息验证策略
@dataclass
class BubbleMessageScenario:
    """
    气泡消息验证场景：封装发送方与接收方气泡的差异化校验
    """
    desc: str                       # 场景描述
    message_content: str            # 发送的消息内容
    is_sender: bool                 # 是否为发送方-True，False-为接收方
    bubble_locator: str             # 气泡定位器ID
    avatar_locator: tuple           # 头像定位器
    status_locator: Optional[tuple] = None  # 状态标志定位器 (如发送成功/已读，仅发送方常用)

    def __str__(self):
        return self.desc

# --- 定义具体气泡策略实例 ---
SENDER_BUBBLE_STRATEGY = BubbleMessageScenario(
    desc="发送方气泡验证",
    message_content="这是发送方测试消息",
    is_sender=True,
    bubble_locator=ChatLocator.AVATAR_ID,
    avatar_locator=ChatLocator.AVATAR_ITEM,
    status_locator=None
)
RECEIVER_BUBBLE_STRATEGY = BubbleMessageScenario(
    desc="接收方气泡验证",
    message_content="这是接收方测试消息",
    is_sender=False,
    bubble_locator=ChatLocator.AVATAR_ID,
    avatar_locator=ChatLocator.AVATAR_ITEM,
    status_locator=None
)

# 7. 文件发送策略
@dataclass
class FileTestScenario:
    desc: str                   # 场景描述 (例如: 发送Word并预览)
    file_name: str              # 手机提前备好的测试文件名称 (如 test_doc.docx)
    file_type: str              # 文件类型 (word, excel, pdf, txt, image, video)
    expect_send_success: bool   # 期望是否发送成功
    preview_locator: Optional[tuple] = None # 预览打开后，用于断言预览成功的核心定位器

# 8. 会话内容显示策略
@dataclass
class ChatContentStrategy:
    """
    会话内容在列表页的缩略展示策略
    """
    desc: str                # 测试报告显示的描述，如 "图片消息展示"
    expected_text: str       # 列表页预期的展示文本，如 "[图片]"
    send_action: str         # 发送方法名，如 "send_image_message"
    send_args: tuple = ()    # 发送参数

    def __str__(self):
        return self.desc

CHAT_CONTENT_SCENARIOS = [
    ChatContentStrategy("语音消息展示", "[语音]", "send_voice_message"),
    ChatContentStrategy("图片消息展示", "[图片]", "send_image_message"),
    ChatContentStrategy("视频消息展示", "[视频]", "send_video_message"),
    ChatContentStrategy("位置消息展示", "[位置]", "send_location_message"),
    ChatContentStrategy("文件消息展示", "[文件]", "send_file_message"),
    ChatContentStrategy("视频聊天展示", "[视频通话]", "send_video_chat"),
    ChatContentStrategy("语音聊天展示", "[语音通话]", "send_voice_chat"),
    ChatContentStrategy("个人名片展示", "[个人名片]", "send_personal_card"),
    ChatContentStrategy("群名片展示", "[群名片]", "send_group_card"),
    ChatContentStrategy("进群邀请展示", "[进群邀请]", "send_group_invite"),
    ChatContentStrategy("表情消息展示", "[动画表情]", "send_emoji_message"),
    ChatContentStrategy("链接分享展示", "[链接分享]", "send_link_message"),
]

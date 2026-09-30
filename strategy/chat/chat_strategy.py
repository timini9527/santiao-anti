import os
import json
from dataclasses import dataclass
from typing import List, Optional, Union, Tuple

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


TEST_PRIVATE_USERS = [
    ChatSessionStrategy(
        desc="私聊模式",
        name="003",
        phone="19200000003"
    ),
    # ChatSessionStrategy(
    #     desc="私聊模式",
    #     name="19200000064",
    #     phone="19200000064"
    # ),
    # ChatSessionStrategy(
    #     desc="私聊模式",
    #     name="19200000611",
    #     phone="19200000611"
    # ),
    # ChatSessionStrategy(
    #     desc="私聊模式",
    #     name="19200000612",
    #     phone="19200000612"
    # ),
    # *(
    #     ChatSessionStrategy(
    #         desc="私聊模式",
    #         name=f"测试13{i}",
    #         phone=f"1920000013{i}"
    #     )
    #     for i in range(0, 6)
    # ),
    # ChatSessionStrategy(
    #     desc="私聊模式",
    #     # name="测试0225",
    #     name="3T_im7i3EO",
    #     phone=""
    # )
]


TEST_GROUPS = [
    ChatSessionStrategy(
        desc="群聊模式",
        name=f"测试群{i:03d}",
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

    def __str__(self):
        return self.action_desc

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

    def __str__(self):
        return self.action_desc


DELETE_ACTIONS = [
    SlideDeleteAction("侧滑删除会话(取消删除)", "click_conversation_delete_dialog_cancel", True, "取消删除"),
    SlideDeleteAction("侧滑删除会话(清空聊天记录)", "click_conversation_delete_dialog_clear_chat_record", None, "清空聊天记录"),
    SlideDeleteAction("侧滑删除会话(隐藏会话)", "click_conversation_delete_dialog_hide", False, "隐藏会话"),
]

# 5. 置顶会话折叠验证策略 (连贯状态机流水线设计)
@dataclass
class TopFoldScenario:
    """
    置顶折叠验证场景：驱动 test_top_fold 的连贯流水线参数化数据
    用例 1~4 业务流程连贯，消除重复上下滑与无谓清理：
      1. 置顶 4 个 -> 校验无折叠
      2. 增量置顶 1 个 (达 5 个) -> 校验显示折叠条及展开/收起
      3. 增量取消 1 个 (回落至 4 个) -> 校验折叠条消失
      4. 增量置顶 4 个 (达到 8 个) -> 校验显示折叠条及数量 8，测试结束时清理现场
    """
    desc: str                       # 场景描述 (用于 Allure 报告和 pytest ids)
    story: str                      # Allure story
    action_type: str                # 本次执行动作: '置顶' 或 '取消置顶'
    action_count: int               # 本次增量操作数量 (4, 1, 1, 4)
    expected_total: int             # 操作后预期的置顶总数 (4, 5, 4, 8)
    expect_fold_visible: bool       # 最终校验时折叠入口是否可见
    check_fold_count: bool = False  # 是否校验折叠数量 == expected_total
    check_fold_click: bool = False  # 是否校验点击折叠后展开与收起
    is_first: bool = False          # 是否为首个场景 (执行前置环境清空)
    is_last: bool = False           # 是否为最后一个场景 (执行现场彻底清理)

    # 兼容历史属性
    @property
    def pin_count(self) -> int:
        return self.expected_total

    def __str__(self):
        return self.desc


TOP_FOLD_SCENARIOS = [
    TopFoldScenario(
        desc="1.置顶4个_无折叠",
        story="置顶会话数量<5，不显示折叠状态",
        action_type="置顶",
        action_count=4,
        expected_total=4,
        expect_fold_visible=False,
        is_first=True,
    ),
    TopFoldScenario(
        desc="2.置顶+1(达5个)_显示折叠",
        story="置顶会话数量>=5，显示折叠状态，并且折叠数量与置顶数量一致，点击折叠置顶会话被折叠",
        action_type="置顶",
        action_count=1,
        expected_total=5,
        expect_fold_visible=True,
        check_fold_count=True,
        check_fold_click=True,
    ),
    TopFoldScenario(
        desc="3.取消1个(降为4个)_折叠消失",
        story="置顶会话数量5->4，折叠会话状态消失",
        action_type="取消置顶",
        action_count=1,
        expected_total=4,
        expect_fold_visible=False,
    ),
    TopFoldScenario(
        desc="4.再置顶4个(达8个)_折叠显示",
        story="置顶会话数量 8，折叠会话状态显示",
        action_type="置顶",
        action_count=4,
        expected_total=8,
        expect_fold_visible=True,
        check_fold_count=True,
        is_last=True,
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
    msg_type: str            # 消息类型，对应 ChatMessageBuilder 的 strategy_name（如 "image", "package"）
    build_args: dict = None  # 构造参数字典

    def __post_init__(self):
        # 若未传参则兜底为空字典，防止用例中 ** 解包时抛出 TypeError
        if self.build_args is None:
            self.build_args = {}

    def __str__(self):
        # 返回场景描述，供测试报告和日志直接展示清晰名称，避免显示内存地址
        return self.desc


# 单端自闭环展示场景（严格对应用户用例顺序：表情包、图片、视频、语音、位置、文件、个人名片、群名片、链接分享）
CHAT_CONTENT_SCENARIOS = [
    ChatContentStrategy("表情包消息展示", "[动态表情]", "package"),
    ChatContentStrategy("图片消息展示", "[图片]", "image"),
    ChatContentStrategy("视频消息展示", "[视频]", "video"),
    ChatContentStrategy("语音消息展示", "[语音]", "voice"),
    ChatContentStrategy("位置消息展示", "[位置]", "position"),
    ChatContentStrategy("文件消息展示", "[文件]", "file"),
    ChatContentStrategy("个人名片展示", "[个人名片]", "card"),
    ChatContentStrategy("群名片展示", "[群名片]", "group_card"),
    # ChatContentStrategy("链接分享展示", "[链接分享]", "link"),
]

# 双端协同展示场景（音视频通话、进群邀请等依赖双端信令交互与对端动作）
CHAT_CONTENT_DOUBLE_SCENARIOS = [
    ChatContentStrategy("视频聊天展示", "[视频通话]", "video_call"),
    ChatContentStrategy("语音聊天展示", "[语音通话]", "voice_call"),
    ChatContentStrategy("进群邀请展示", "[进群邀请]", "group_invite"),
]


@dataclass
class ChatCallStrategy:
    """音视频通话双端协同场景策略"""
    desc: str                                        # 用例标题描述 (如 "视频通话-主叫挂断")
    call_type: str                                   # 通话类型 ("video_call" / "voice_call")
    action: str                                      # 交互行为 ("cancel" / "reject" / "accept" / "timeout" / "interrupt")
    expected_text_s: Union[str, tuple, list]         # 主叫端会话预期展示文本（支持单文本、斜杠多选或候选列表）
    expected_text_r: Union[str, tuple, list]         # 被叫端会话预期展示文本（支持单文本、斜杠多选或候选列表）

    def __str__(self):
        return self.desc

    @property
    def expected_s_candidates(self) -> list[str]:
        """获取主叫端多候选预期列表"""
        return self._parse_candidates(self.expected_text_s)

    @property
    def expected_r_candidates(self) -> list[str]:
        """获取被叫端多候选预期列表"""
        return self._parse_candidates(self.expected_text_r)

    @staticmethod
    def _parse_candidates(val: Union[str, tuple, list]) -> list[str]:
        """解析多候选文本集合，支持斜杠语法与序列类型"""
        if isinstance(val, (list, tuple)):
            return [str(x).strip() for x in val if str(x).strip()]
        if isinstance(val, str) and "/" in val:
            return [x.strip() for x in val.split("/") if x.strip()]
        return [str(val).strip()] if val else []


# 音视频通话双端协同场景集（涵盖 5 大生命周期状态机终态）
CHAT_CALL_DOUBLE_SCENARIOS = [
    # 1. 主叫挂断 -> 主叫会话显示【已取消】，被叫会话显示【对方已取消】
    ChatCallStrategy("视频通话-主叫挂断", "video_call", "cancel", expected_text_s="已取消", expected_text_r="对方已取消"),
    ChatCallStrategy("语音通话-主叫挂断", "voice_call", "cancel", expected_text_s="已取消", expected_text_r="对方已取消"),

    # 2. 被叫拒绝 -> 主叫会话显示【对方已拒绝】，被叫会话显示【已拒绝】
    ChatCallStrategy("视频通话-被叫拒绝", "video_call", "reject", expected_text_s="对方已拒绝", expected_text_r="已拒绝"),
    ChatCallStrategy("语音通话-被叫拒绝", "voice_call", "reject", expected_text_s="对方已拒绝", expected_text_r="已拒绝"),

    # 3. 通话接通 -> 主叫会话显示【通话时长】，被叫会话显示【通话结束】
    ChatCallStrategy("视频通话-通话接通", "video_call", "accept", expected_text_s="通话时长", expected_text_r="通话时长"),
    ChatCallStrategy("语音通话-通话接通", "voice_call", "accept", expected_text_s="通话时长", expected_text_r="通话时长"),

    # 4. 主被超时 -> 主叫会话显示【对方无应答】，被叫会话显示【未接来电/对方已取消】
    ChatCallStrategy("视频通话-主被超时", "video_call", "timeout", expected_text_s="对方无应答", expected_text_r="对方已取消/未接来电"),
    ChatCallStrategy("语音通话-主被超时", "voice_call", "timeout", expected_text_s="对方无应答", expected_text_r="对方已取消/未接来电"),

    # 5. 通话中断 -> 双方断网，双方会话显示【通话中断】
    ChatCallStrategy("视频通话-通话中断", "video_call", "interrupt", expected_text_s="通话中断", expected_text_r="通话时长"),
    ChatCallStrategy("语音通话-通话中断", "voice_call", "interrupt", expected_text_s="通话中断", expected_text_r="通话时长"),

]





# 9. 群聊特有会话内容与强提醒状态策略
@dataclass
class ChatGroupRemindStrategy:
    """
    群聊特有会话内容状态策略（进群申请、加入群聊系统通知、有人@我、@所有人、复合提醒）
    """
    desc: str                           # 场景测试标题描述
    expected_tag: str                   # 预期提醒标签（tv_user_name，如 "[进群申请]"、"[有人@我]"、"[@所有人]"）
    expected_content: str               # 预期会话消息内容（tv_message，如 "加入了群聊"）
    remind_type: str                    # 场景分类类型 ("apply", "join_notify", "at_me", "at_all", "both_apply_and_at")
    required_role: str = "member"       # 权限约束："member"(全员可见)、"admin_or_owner"(仅群主或具备进群审批权限的管理员可见)
    check_disappear_after_enter: bool = False  # 是否验证进入会话查看后强提醒标签消失

    def __str__(self):
        return self.desc


# 群聊特有会话状态场景集（包含：群主/管理员进群申请可见、普通成员无权限不可见、某某某加入群聊、有人@我、查看@人消息消失、@所有人消失、申请与@并存）
CHAT_GROUP_CONTENT_SCENARIOS = [
    ChatGroupRemindStrategy(
        desc="进群申请（群主/有权限管理员可见）",
        expected_tag="[进群申请]",
        expected_content="",
        remind_type="apply",
        required_role="admin_or_owner",
        check_disappear_after_enter=False
    ),
    ChatGroupRemindStrategy(
        desc="进群申请（普通成员无权限不可见）",
        expected_tag="",
        expected_content="",
        remind_type="apply",
        required_role="member",
        check_disappear_after_enter=False
    ),
    ChatGroupRemindStrategy(
        desc="进群后显示某某某加入群聊",
        expected_tag="",
        expected_content="加入了群聊",
        remind_type="join_notify",
        required_role="member",
        check_disappear_after_enter=False
    ),
    ChatGroupRemindStrategy(
        desc="有人@我",
        expected_tag="[有人@我]",
        expected_content="",
        remind_type="at_me",
        required_role="member",
        check_disappear_after_enter=False
    ),
    ChatGroupRemindStrategy(
        desc="查看@人消息消失",
        expected_tag="[有人@我]",
        expected_content="",
        remind_type="at_me",
        required_role="member",
        check_disappear_after_enter=True
    ),
    ChatGroupRemindStrategy(
        desc="@所有人，查看@所有人消息消失",
        expected_tag="[@所有人]",
        expected_content="",
        remind_type="at_all",
        required_role="member",
        check_disappear_after_enter=True
    ),
    ChatGroupRemindStrategy(
        desc="群主/管理员进群申请和@消息同时存在",
        expected_tag="[进群申请]",
        expected_content="",
        remind_type="both_apply_and_at",
        required_role="admin_or_owner",
        check_disappear_after_enter=False
    ),
]




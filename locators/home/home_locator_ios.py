# -*- coding: utf-8 -*-
"""
iOS 平台主页与会话列表元素定位器 (XCUITest / WebDriverAgent 原生架构)
全面规范化为 Apple 官方 XCUIElementType* 元素类型与高效定位策略 (Predicate / Class Chain / Accessibility ID)
覆盖顶部导航、搜索交互、底部页签、联系人列表、会话列表流及侧滑/长按动作。
核心原则：有 name 属性就不冗余使用 label，保持表达式最纯粹高效。
"""
from typing import Tuple
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_ios import _CommonLocatorIos


class _HomeLocatorIos:
    """
    iOS 平台主页与会话列表元素定位器 (XCUITest / WebDriverAgent 原生架构)

    定位策略优先级 (按 XCUITest 原生性能与稳定性排序)：
    1. ACCESSIBILITY_ID：对应 accessibilityIdentifier，哈希索引直达，最稳定首选；
    2. IOS_PREDICATE：NSPredicate 原生谓词，组合 XCUIElementType 与 name 过滤，不依赖视图层级；
    3. IOS_CLASS_CHAIN：原生层级链，用于精准父子/后代遍历 (如导航栏首尾按钮、搜索输入框内部清除按钮)；
    4. XPATH：规范使用 XCUIElementType* 前缀，仅用于复杂祖先/跨分支反向锚定场景。

    注意：本类不继承 CommonLocator。DynamicLocatorProxy 在类定义阶段解析基类，
    若继承会固化为 Android 基类，导致 iOS 页面继承到 resource-id 定位器。
    """

    # iOS 应用 Bundle ID (与 config/devices.yaml 中 appium:bundleId 保持一致)
    PACKAGE_ID = _CommonLocatorIos.PACKAGE_ID

    # 静态文本类控件类型集合
    _TEXT_TYPES = "{'XCUIElementTypeStaticText', 'XCUIElementTypeTextView'}"
    # 可点击类控件类型集合
    _BUTTON_TYPES = "{'XCUIElementTypeButton'}"

    # --------------------------------------------------------------------------
    # 1. 顶部全局导航栏与通用菜单 (Top Navigation Bar & Menus)
    # --------------------------------------------------------------------------
    # 顶部左上角抽屉菜单/个人中心头像入口
    LEFT_MENU = (
        AppiumBy.ACCESSIBILITY_ID,
        "ic home left drawer close",
    )

    # 顶部中间标题 (应用名 "三条" 或 消息连接状态)
    MIDDLE_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND (name CONTAINS '三条')",
    )

    # 顶部右上角添加 "+" 功能菜单按钮 (导航栏右侧按钮)
    RIGHT_MENU = (
        AppiumBy.ACCESSIBILITY_ID,
        "ic head more 48",
    )

    # 展开菜单 - 发起群聊
    EXPAND_START_GROUP_CHAT = (
        AppiumBy.IOS_PREDICATE,
        "//XCUIElementTypeStaticText[@name='发起群聊']",
    )

    # 展开菜单 - 添加朋友 / 加好友/群
    EXPAND_ADD_FRIEND = (
        AppiumBy.IOS_PREDICATE,
        "//XCUIElementTypeStaticText[@name='加好友/群']",
    )

    # 展开菜单 - 扫一扫
    EXPAND_SCAN = (
        AppiumBy.IOS_PREDICATE,
        "//XCUIElementTypeStaticText[@name='扫一扫']",
    )

    # 顶部统一标题 (与 _CommonLocatorIos 对齐)
    TOP_TV_TITLE = _CommonLocatorIos.TOP_TV_TITLE

    # --------------------------------------------------------------------------
    # 2. 全局搜索交互体系 (Search Bar & Overlay)
    # --------------------------------------------------------------------------
    # 底部容器标识 (兼容性定义)
    BOTTOM_ID = "compose_bottom_bar"
    BOTTOM = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeTabBar', 'XCUIElementTypeToolbar'}",
    )

    # 主页全局搜索栏入口 (底部或列表顶部的搜索栏)
    SEARCH = (
        AppiumBy.IOS_PREDICATE,
        "//XCUIElementTypeOther[XCUIElementTypeImage[@name='st_tabbar_search']]",
    )

    # 搜索输入框 (获取焦点后的编辑组件)
    SEARCH_INPUT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeStaticText[@name='搜索']",
    )

    # 搜索输入框内容一键清空按钮
    SEARCH_CLEAR = (
        AppiumBy.ACCESSIBILITY_ID,
        "清除文本",
    )
    Field_Text = (
        AppiumBy.XPATH,
        "//XCUIElementTypeTextField[@label='搜索']"
    )

    # 搜索取消/退出按钮 (关闭搜索覆盖层回到主会话列表)
    SEARCH_CANCEL = (
        AppiumBy.ACCESSIBILITY_ID,
        "//XCUIElementTypeOther[XCUIElementTypeImage[@name='st_tabbar_search_close']]",
    )

    # --------------------------------------------------------------------------
    # 3. 底部主导航栏与分类页签 (Bottom Navigation Tabs)
    # --------------------------------------------------------------------------
    # 底部展开分类菜单按钮
    EXPAND_MENU = (
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeImage[@name='st_tabbar_search_close']]",
    )

    # 底部收起/折叠分类菜单按钮
    COLLAPSE_MENU = EXPAND_MENU

    # 分类页签 - 好友
    FRIEND = (
        AppiumBy.IOS_PREDICATE,
        'type == "XCUIElementTypeButton" AND name == "好友"',
    )

    # 分类页签 - 群聊
    GROUP = (
        AppiumBy.IOS_PREDICATE,
        'type == "XCUIElementTypeButton" AND name == "群聊"',
    )

    # 分类页签 - 通话
    TELL = (
        AppiumBy.IOS_PREDICATE,
        'type == "XCUIElementTypeButton" AND name == "通话"'
    )



    # --------------------------------------------------------------------------
    # 4. 好友页面与分类标签体系 (Contacts & Category Manager)
    # --------------------------------------------------------------------------
    # 朋友圈 / 好友动态容器与入口
    LL_FRIEND_MOMENTS = (
        AppiumBy.XPATH,
        "//XCUIElementTypeOther[XCUIElementTypeImage[@name='ic_friend_news']]"
    )
    FRIEND_MOMENTS = LL_FRIEND_MOMENTS

    # 好友动态图标
    DYNAMIC_IV = (AppiumBy.ACCESSIBILITY_ID, 'ic_friend_news')
    
    # 好友动态
    DYNAMIC = (
        AppiumBy.IOS_PREDICATE,
        'type == "XCUIElementTypeStaticText" AND name == "好友动态"'
    )

    # 好友动态未读消息红点/数量徽标
    DYNAMIC_UNREAD_MSG = (
        AppiumBy.XPATH,
        "//XCUIElementTypeStaticText[@name='好友动态']/following-sibling::XCUIElementTypeOther/XCUIElementTypeStaticText"
    )
    
    # 好友动态 - 新的内容
    DYNAMIC_NEW_CONTENT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeImage[@name='ic_friend_news']/following-sibling::XCUIElementTypeImage"
    )

    # 新的朋友条目容器
    NEW_FRIEND = (
        AppiumBy.IOS_PREDICATE,
        "//XCUIElementTypeOther[XCUIElementTypeImage[@name='ic_friend_new_friends']]"
    )
    # 新的朋友图标
    NEW_FRIEND_IV = (
        AppiumBy.ACCESSIBILITY_ID,
        "ic_friend_new_friends"
    )
    # 新的朋友文本
    NEW_FRIEND_TV = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '新的朋友'"
    )
    # 新的朋友未读消息数
    NEW_FRIEND_FB_BADGE_COUNT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeStaticText[@name='新的朋友']/following-sibling::XCUIElementTypeOther/XCUIElementTypeStaticText"
    )
    NEW_FRIEND_FB_BADGE_COUNT_XPATH = NEW_FRIEND_FB_BADGE_COUNT

    # 分组管理容器
    CATEGORY_MANAGER = (
        AppiumBy.IOS_PREDICATE,
        "//XCUIElementTypeOther[XCUIElementTypeImage[@name='ic_friends_category_manage']]"
    )
    # 分组管理图标
    CATEGORY_MANAGER_IV = (
        AppiumBy.ACCESSIBILITY_ID,
        'ic_friend_new_friends',
    )
    # 分组管理文本
    CATEGORY_MANAGER_TV = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '分组管理'",
    )

    # --------------------------------------------------------------------------
    # 5. 会话列表与条目容器 (Conversation List & Item)
    # --------------------------------------------------------------------------
    # 会话列表外层可滚动大容器
    CONVERSATION_LIST = (
        AppiumBy.IOS_CLASS_CHAIN,
        "**/XCUIElementTypeOther",
    )

    # 单个会话卡片条目根容器
    CONVERSATION_ITEM = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeCell'",
    )

    # 会话标题/联系人或群聊名称
    CONVERSATION_NAME = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[1]",
    )

    # 会话最后更新时间标签
    CONVERSATION_TIME = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, ':') or contains(@name, '昨天') or contains(@name, '前天') or contains(@name, '月') or contains(@name, '日')]",
    )

    # 会话最新消息预览内容
    CONVERSATION_CONTENT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[2]",
    )

    # 会话未读消息数量气泡/红点
    CONVERSATION_UNREAD_COUNT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[number(@name) > 0 or @name='99+']",
    )
    CONVERSATION_UNREAD_COUNT_INNER = CONVERSATION_UNREAD_COUNT

    # 会话静音快捷操作按钮与文本
    CONVERSATION_MUTE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name CONTAINS '静音'",
    )
    CONVERSATION_MUTE_ICON = CONVERSATION_MUTE
    CONVERSATION_MUTE_TEXT = CONVERSATION_MUTE

    # 会话置顶快捷操作按钮与文本
    CONVERSATION_TOP = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name CONTAINS '置顶'",
    )
    CONVERSATION_TOP_ICON = CONVERSATION_TOP
    CONVERSATION_TOP_TEXT = CONVERSATION_TOP

    # 会话删除快捷操作按钮与文本
    CONVERSATION_DELETE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name CONTAINS '删除'",
    )
    CONVERSATION_DELETE_ICON = CONVERSATION_DELETE
    CONVERSATION_DELETE_TEXT = CONVERSATION_DELETE

    # 会话隐藏
    CONVERSATION_HIDE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name CONTAINS '隐藏'",
    )

    # 会话删除确认弹窗 - 清空聊天记录并隐藏
    CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND (name CONTAINS '清空' OR name CONTAINS '记录')",
    )

    # 会话删除确认弹窗 - 确认删除
    CONVERSATION_DELETE_DIALOG_CONFIRM = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name IN {'删除', '确认删除', '确定'}",
    )

    # 会话删除确认弹窗 - 取消
    CONVERSATION_DELETE_DIALOG_CANCEL = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name == '取消'",
    )

    # 置顶折叠入口与折叠数量
    CONVERSATION_FOLD_ENTRY = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell[.//XCUIElementTypeStaticText[contains(@name, '折叠')]]",
    )
    CONVERSATION_FOLD_COUNT_TEXT = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeStaticText[contains(@name, '折叠')]",
    )
    CONVERSATION_FOLD_VIEWGROUP = CONVERSATION_FOLD_ENTRY

    # 会话草稿状态
    CONVERSATION_DRAFT = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '草稿'",
    )

    # 会话停用/免打扰状态 (静音图标)
    CONVERSATION_DISABLE = (
        AppiumBy.XPATH,
        "//XCUIElementTypeCell//XCUIElementTypeImage[contains(@name, 'mute') or contains(@name, 'deactivate') or contains(@name, '静音')]",
    )

    # 会话未读/已读状态
    CONVERSATION_UNREAD = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name IN {'未读', '已读'}",
    )

    # 会话强提醒前缀标签 (@人的消息、进群验证消息，如 [有人@我], [@所有人], [进群申请])
    CONVERSATION_USER_NAME = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name BEGINSWITH '['",
    )

    # --------------------------------------------------------------------------
    # 6. 首次登录主页引导弹窗（选择你偏好的首页布局）
    # --------------------------------------------------------------------------
    # 引导弹窗标题（原生 Predicate 极速探测，无弹窗时不触发 XPath）
    HOME_LAYOUT_GUIDE_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name == '选择你偏好的首页布局'",
    )
    # 引导弹窗右上角关闭按钮（优先锁定与标题同容器的按钮，兜底复用系统关闭图标）
    HOME_LAYOUT_GUIDE_CLOSE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeButton' AND name =='关闭'",
    )

    # --------------------------------------------------------------------------
    # 6. 输入聊天密码弹窗 (Chat Password Dialog)
    # --------------------------------------------------------------------------
    # 输入聊天密码弹窗标题
    CHAT_PASSWORD_DIALOG_TITLE = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '密码'",
    )
    # 聊天密码弹窗内容
    CHAT_PASSWORD_DIALOG_CONTENT = (
        AppiumBy.IOS_PREDICATE,
        "type == 'XCUIElementTypeStaticText' AND name CONTAINS '聊天密码'",
    )
    # 忘记密码入口
    CHAT_PASSWORD_TV_FORGOT_PASSWORD = (
        AppiumBy.IOS_PREDICATE,
        "type IN {'XCUIElementTypeButton', 'XCUIElementTypeStaticText'} AND name CONTAINS '忘记密码'",
    )
    # 输入密码框容器
    CHAT_PASSWORD_VIEW_INPUT_CODE = (
        AppiumBy.XPATH,
        "//XCUIElementTypeSecureTextField | //XCUIElementTypeTextField",
    )
    # 密码单个输入框列表
    CHAT_PASSWORD_VIEW_INPUT_CODE_LIST = (
        AppiumBy.XPATH,
        "//XCUIElementTypeSecureTextField | //XCUIElementTypeTextField",
    )

    # --------------------------------------------------------------------------
    # 7. 动态参数化定位器工厂方法 (Dynamic Factories)
    # --------------------------------------------------------------------------
    @classmethod
    def get_conver_by_name(cls, name: str) -> Tuple[str, str]:
        """按会话或联系人名称定位会话单元格或标题 (点击可直接进入聊天会话)"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.IOS_PREDICATE,
            f"type == 'XCUIElementTypeCell' AND name CONTAINS '{safe_name}'",
        )

    @classmethod
    def get_message_by_name(cls, name: str) -> Tuple[str, str]:
        """通过联系人/会话名称精准获取其会话卡片内的最新消息预览内容"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[2]",
        )

    @classmethod
    def get_session_by_name(cls, name: str) -> Tuple[str, str]:
        """通过会话名称反向向上获取该条目的外层 Cell 根容器"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]",
        )

    @classmethod
    def get_time_by_name(cls, name: str) -> Tuple[str, str]:
        """通过会话名称获取右侧最新消息发送时间文本 (如 '18:59')"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[contains(@name, ':') or contains(@name, '昨天') or contains(@name, '前天') or contains(@name, '月') or contains(@name, '日')]",
        )

    @classmethod
    def get_disable_by_name(cls, name: str) -> Tuple[str, str]:
        """精确获取某一个会话条目中的停用/免打扰静音图标"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeImage[contains(@name, 'mute') or contains(@name, 'deactivate') or contains(@name, '静音')]",
        )

    @classmethod
    def get_unread_count_by_name(cls, name: str) -> Tuple[str, str]:
        """精确获取某一个会话条目中的未读消息数红点/数字文本"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[number(@name) > 0 or @name='99+']",
        )

    @classmethod
    def get_read_status_by_name(cls, name: str) -> Tuple[str, str]:
        """精确获取某一个会话的消息阅读状态 (未读/已读)"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[@name='未读' or @name='已读']",
        )

    @classmethod
    def get_password_input_by_index(cls, index: int) -> Tuple[str, str]:
        """获取聊天密码弹窗中第 index+1 个独立输入框"""
        return (
            AppiumBy.XPATH,
            f"(//XCUIElementTypeSecureTextField | //XCUIElementTypeTextField)[{index + 1}]",
        )

    @classmethod
    def get_remind_status_by_name(cls, name: str) -> Tuple[str, str]:
        """精确获取某一个会话的状态提醒标签 (@人的消息、进群验证消息，如 [有人@我], [@所有人], [进群申请])"""
        safe_name = name.replace("'", "\\'")
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[starts-with(@name, '[')]",
        )

    @classmethod
    def get_status_tag_by_name(cls, name: str, tag: str = "") -> Tuple[str, str]:
        """
        获取指定会话的前缀状态标签 (如: 草稿、未读、已读、进群申请、@所有人、@我)
        :param name: 会话或联系人名称
        :param tag: 可选指定特定标签过滤文本
        """
        safe_name = name.replace("'", "\\'")
        if tag:
            safe_tag = tag.replace("'", "\\'")
            return (
                AppiumBy.XPATH,
                f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[contains(@name, '{safe_tag}')]",
            )
        return (
            AppiumBy.XPATH,
            f"//XCUIElementTypeCell[.//*[@name='{safe_name}']]//XCUIElementTypeStaticText[starts-with(@name, '[')]",
        )

    @classmethod
    def get_draft_by_name(cls, name: str) -> Tuple[str, str]:
        """获取指定会话条目中的 '[草稿]' 标识"""
        return cls.get_status_tag_by_name(name, tag="草稿")

    @classmethod
    def get_mute_action_by_name(cls, name: str) -> Tuple[str, str]:
        """获取指定会话侧滑菜单中的静音操作按钮"""
        return (
            AppiumBy.IOS_PREDICATE,
            "type == 'XCUIElementTypeButton' AND name CONTAINS '静音'",
        )

    @classmethod
    def get_top_action_by_name(cls, name: str) -> Tuple[str, str]:
        """获取指定会话侧滑菜单中的置顶操作按钮"""
        return (
            AppiumBy.IOS_PREDICATE,
            "type == 'XCUIElementTypeButton' AND name CONTAINS '置顶'",
        )

    @classmethod
    def get_delete_action_by_name(cls, name: str) -> Tuple[str, str]:
        """获取指定会话侧滑菜单中的删除操作按钮"""
        return (
            AppiumBy.IOS_PREDICATE,
            "type == 'XCUIElementTypeButton' AND name CONTAINS '删除'",
        )

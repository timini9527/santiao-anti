from appium.webdriver.common.appiumby import AppiumBy


class HomeLocatorHos:
    """
    鸿蒙 NEXT 平台主页元素定位器 (HarmonyOS ArkUI 专享架构)
    底层原生支持 ArkUI 控件标签 (Text, Button, Image, Search, TextInput, List, ListItem, Stack, Row, Column 等)
    全面覆盖顶部导航、搜索体系、底部页签、会话列表流及上下文操作。
    """

    # --------------------------------------------------------------------------
    # 1. 顶部全局导航栏 (Top Navigation Bar)
    # --------------------------------------------------------------------------

    # 顶部左上角抽屉菜单/个人中心头像入口 (基于列表前驱结构定位，稳定度 100%)
    LEFT_MENU = (AppiumBy.XPATH, "(//NavDestinationContent//Stack/__Common__//Row[2]/Column/Row/Stack/Image)[1]")

    # 顶部中间标题 (应用名 "三条" 或 消息连接状态)
    MIDDLE_TITLE = (AppiumBy.XPATH, "//Text[contains(@text, '三条')]")

    # 顶部右上角添加 "+" 功能菜单按钮 (完全脱离页面标题)
    RIGHT_MENU = (AppiumBy.XPATH, "(//NavDestinationContent//Stack/__Common__//Row[2]/Column/Image)[1]")

    # 展开菜单 - 发起群聊
    EXPAND_START_GROUP_CHAT = (AppiumBy.XPATH, "//Text[@text='发起群聊'] | //Dialog//Row/Text[1]")

    # 展开菜单 - 添加朋友
    EXPAND_ADD_FRIEND = (AppiumBy.XPATH, "//Text[@text='加好友/群'] | //Dialog//Row/Text[2]")

    # 展开菜单 - 扫一扫
    EXPAND_SCAN = (AppiumBy.XPATH, "//Text[@text='扫一扫'] | //Dialog//Row/Text[3]")



    # --------------------------------------------------------------------------
    # 2. 搜索交互体系 (Search Bar & Overlay)
    # --------------------------------------------------------------------------

    # 主页全局搜索栏入口 (底部 Row 内左侧搜索栏 Stack/Search)
    SEARCH = (AppiumBy.XPATH, "//Search | //Stack[Search] | //*[@id='__SearchField__'] | //Row[last()]/Stack[1]")

    # 搜索输入框 (获取焦点后的编辑组件)
    SEARCH_INPUT = (AppiumBy.XPATH, "//*[@id='__SearchField__'] | //TextInput | //Search")

    # 搜索输入框内容一键清空按钮
    SEARCH_CLEAR = (AppiumBy.XPATH, "//Button[@id='clear' or contains(@text, '清除')]")

    # 搜索取消/退出按钮 (关闭搜索覆盖层回到主会话列表)
    SEARCH_CANCEL = (AppiumBy.XPATH, "//Text[@text='取消'] | //Button[@text='取消']")



    # --------------------------------------------------------------------------
    # 3. 底部主导航栏与分类页签 (Bottom Navigation Tabs)
    # --------------------------------------------------------------------------

    # 底部主导航栏容器 (包含搜索与展开菜单的底部 Row)
    BOTTOM = (AppiumBy.XPATH, "//Stack/Search")

    # 底部展开分类菜单按钮 (未展开时跟在 Search 后的 Stack 节点)
    EXPAND_MENU = (
        AppiumBy.XPATH,
        "//Stack[Search]/following-sibling::Stack | //Row/Row/following-sibling::Stack[Image]"
    )

    # 底部收起/折叠分类菜单按钮 (展开后跟在分类页签后的 Stack 节点)
    COLLAPSE_MENU = (
        AppiumBy.XPATH,
        "//Row/Row/following-sibling::Stack[Image] | //Stack[Search]/following-sibling::Stack"
    )

    # 分类页签 - 好友
    FRIEND = (AppiumBy.XPATH, "//Row//Column[.//Text[@text='好友']]")

    # 分类页签 - 群聊
    GROUP = (AppiumBy.XPATH, "//Row//Column[.//Text[@text='群聊']]")

    # 分类页签 - 动态
    DYNAMIC = (AppiumBy.XPATH, "//Row//Column[.//Text[@text='动态']]")

    # 动态未读消息红点/数量徽标
    DYNAMIC_UNREAD_MSG = (AppiumBy.XPATH, "//Row/Badge/Text")



    # --------------------------------------------------------------------------
    # 4. 会话列表与条目容器 (Conversation List & Item)
    # --------------------------------------------------------------------------

    # 会话列表外层可滚动大容器
    CONVERSATION_LIST = (AppiumBy.XPATH, "//List")

    # 单个会话卡片条目根容器
    CONVERSATION_ITEM = (AppiumBy.XPATH, "//ListItem")

    # 会话标题/联系人或群聊名称 (锁定 ListItem 标题区域首个 Text 节点，兼容 Flex 与直属结构)
    CONVERSATION_NAME = (AppiumBy.XPATH, "//ListItem//Row[2]//Flex/Text[1] | //ListItem//Flex/Text[1] | //ListItem//Text[1]")

    # 会话发送者和自己发送消息的内容
    CONVERSATION_SENDER = (AppiumBy.XPATH, "//ListItem//Row[2]//Row[2]//Row/Text[last()]")

    # 会话最新消息预览内容 (锁定第二行具有文本的有效内容，自动避开末尾空占位 Text)
    CONVERSATION_CONTENT = (AppiumBy.XPATH, "//ListItem//Row[2]//Text[@text][last()]")

    # 会话最后更新时间标签 (位于第一行右侧)
    CONVERSATION_TIME = (AppiumBy.XPATH, "//ListItem//Row[1]/Text[last()]")

    # 会话未读消息数量气泡/红点 (真机真实结构为 Badge 容器内的独立角标 Text)
    CONVERSATION_UNREAD_COUNT = (AppiumBy.XPATH, "//Badge/Text")

    # 置顶会话折叠入口容器与图标
    CONVERSATION_FOLD_ENTRY = (AppiumBy.XPATH, "//ListItem/Column/Row")

    # 置顶会话折叠数量文本
    CONVERSATION_FOLD_COUNT_TEXT = (AppiumBy.XPATH, "//ListItem/Column/Row/Text")

    # 会话状态标识：已停用/免打扰
    CONVERSATION_DISABLE = (AppiumBy.XPATH, "//ListItem//Flex/Image[2]")

    # 会话状态前缀标签 (公用支持: 草稿、未读/已读、进群申请、@所有人、有人@我)
    CONVERSATION_STATUS_TAG = (
        AppiumBy.XPATH,
        "//ListItem//Text[contains(@text, '草稿') or contains(@text, '未读') or contains(@text, '已读') or contains(@text, '进群申请') or contains(@text, '@所有人') or contains(@text, '@我') or starts-with(@text, '[@')]"
    )

    # 细分状态标签定位 (基于真实会话结构精准过滤)
    CONVERSATION_DRAFT = (AppiumBy.XPATH, "//ListItem//Text[contains(@text, '草稿')]")
    CONVERSATION_UNREAD = (AppiumBy.XPATH, "//ListItem//Text[contains(@text, '未读') or contains(@text, '已读')]")
    CONVERSATION_REMIND_TAG = (AppiumBy.XPATH, "//ListItem//Text[contains(@text, '@所有人') or contains(@text, '有人@我') or contains(@text, '进群申请') or starts-with(@text, '[@')]")



    # --------------------------------------------------------------------------
    # 5. 会话侧滑快捷动作与删除确认弹窗 (Swipe Actions & Confirmation)
    # --------------------------------------------------------------------------

    # 侧滑菜单 - 会话静音
    CONVERSATION_MUTE = (AppiumBy.XPATH, "//ListItem//Row/Column/Text[contains(@text, '静音') or contains(@text, '取消静音')]")

    # 侧滑菜单 - 会话置顶 / 取消置顶
    CONVERSATION_TOP = (AppiumBy.XPATH, "//ListItem//Row/Column/Text[contains(@text, '置顶') or contains(@text, '取消置顶')]")

    # 侧滑菜单 - 会话删除
    CONVERSATION_DELETE = (AppiumBy.XPATH, "//ListItem//Row/Column/Text[contains(@text, '删除')]")

    # 删除会话弹窗 - 隐藏
    CONVERSATION_HIDE = (AppiumBy.XPATH, "//Dialog//Column[@clickable='true' and .//Text[@text='清空聊天记录']]")

    # 会话删除二次确认弹窗 - 清空聊天记录并隐藏
    CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD = (AppiumBy.XPATH, "//Dialog//Column[@clickable='true' and .//Text[@text='确认删除']]")

    # 会话删除二次确认弹窗 - 确认删除
    CONVERSATION_DELETE_DIALOG_CONFIRM = (AppiumBy.XPATH, "//Button[@text='删除' or @text='确定'] | //Text[@text='删除' or @text='确定']")

    # 会话删除二次确认弹窗 - 取消操作 (锁定 Dialog 弹窗下的取消组件，避免底层会话列表干扰)
    CONVERSATION_DELETE_DIALOG_CANCEL = (AppiumBy.XPATH, "//Dialog//Column//Text[@clickable='true' and @text='取消']")

    # --------------------------------------------------------------------------
    # 6. 聊天安全密码保护弹窗 (Chat Password Dialog)
    # --------------------------------------------------------------------------

    # 关闭窗口按钮
    CHAT_PASSWORD_DIALOG_CLOSE = (AppiumBy.XPATH, "//Dialog//Row/Image[@clickable='true']")

    # 输入聊天密码对话框标题
    CHAT_PASSWORD_DIALOG_TITLE = (AppiumBy.XPATH, "//Text[@text='请输入密码']")

    # 聊天密码弹窗提示描述
    CHAT_PASSWORD_DIALOG_CONTENT = (AppiumBy.XPATH, "//Text[@text='聊天密码']")

    # 忘记聊天密码入口
    CHAT_PASSWORD_TV_FORGOT_PASSWORD = (AppiumBy.XPATH, "//Dialog//Row[2]/Text | //Text[@text='忘记密码']")

    # 聊天密码通用输入框
    CHAT_PASSWORD_INPUT = (AppiumBy.XPATH, "//Dialog//Row[1]/Text")

    # --------------------------------------------------------------------------
    # 7. 动态参数化精准元素定位器工厂 (Parameterized Locators)
    # --------------------------------------------------------------------------

    @classmethod
    def get_conver_by_name(cls, name: str) -> tuple[str, str]:
        """按会话或联系人名称精准定位会话标题 Text 元素 (点击可直接进入聊天会话)"""
        return (AppiumBy.XPATH, f"//ListItem//Row[1]//Text[1][@text='{name}']")

    @classmethod
    def get_time_by_name(cls, name: str) -> tuple[str, str]:
        """通过会话名称获取右侧最新消息发送时间文本 (如 '18:59')"""
        return (AppiumBy.XPATH, f"//ListItem//Row[1]//Text[1][@text='{name}']//ancestor::Row/Text[last()]")

    @classmethod
    def get_session_by_name(cls, name: str) -> tuple[str, str]:
        """通过会话名称反向向上获取该条目的外层 ListItem 根容器 (精准限定最近一级祖先 ListItem)"""
        return (AppiumBy.XPATH, f"//ListItem//Row[1]//Text[1][@text='{name}']/ancestor::ListItem[1]")

    @classmethod
    def get_prefix_by_name(cls, name: str) -> tuple[str, str]:
        """通过联系人/群名称精准获取其消息发送状态"""
        return (AppiumBy.XPATH, f"//ListItem//Row[1]//Text[1][@text='{name}']//ancestor::Row[1]/following-sibling::Row//Image")

    @classmethod
    def get_message_by_name(cls, name: str) -> tuple[str, str]:
        """通过联系人/群名称精准获取其会话卡片内的最新消息预览内容 (锁定卡片第二行有效文本，自动避开状态标签与末尾空占位)"""
        return (AppiumBy.XPATH, f"//ListItem//Row[1]//Text[1][@text='{name}']//ancestor::Row[1]/following-sibling::Row//Row/Text[@text][last()]")

    @classmethod
    def get_unread_count_by_name(cls, name: str) -> tuple[str, str]:
        """精准获取指定会话卡片上的未读消息计数气泡 (同时兼容 Badge 内部 Text 节点与其自带 text 属性)"""
        return (AppiumBy.XPATH, f"//ListItem//Row[1]//Text[1][@text='{name}']//ancestor::Row[1]/following-sibling::Row//Text[@text][last()]")

    @classmethod
    def get_status_tag_by_name(cls, name: str, tag: str = "") -> tuple[str, str]:
        """
        获取指定会话的前缀状态标签 (公用统一支持: [草稿]、[未读]、[已读]、[进群申请]、[@所有人]、[@我])
        :param name: 会话或联系人名称
        :param tag: 可选指定特定标签过滤文本 (如 '草稿'、'未读'、'已读'、'进群申请'、'@所有人'、'@我')；留空则匹配任意状态标签
        """
        if tag:
            return (AppiumBy.XPATH, 
                    f"//ListItem//Row[1]//Text[1][@text='{name}']//ancestor::Row[1]/following-sibling::Row//Row/Text[@text='{tag}']"
                    )
        return (
            AppiumBy.XPATH,
            f"//ListItem//Row[1]//Text[1][@text='{name}']//ancestor::Row[1]/following-sibling::Row//Row/Text[@text]"
        )

    @classmethod
    def get_draft_by_name(cls, name: str) -> tuple[str, str]:
        """获取指定会话条目中的 '[草稿]' 标识 (公用底层通用状态标签定位)"""
        return cls.get_status_tag_by_name(name, tag="[草稿]")

    @classmethod
    def get_remind_status_by_name(cls, name: str) -> tuple[str, str]:
        """精准获取指定会话的状态强提醒标签 (如 [@所有人], [有人@我], [进群申请]) (公用底层通用状态标签定位)"""
        return cls.get_status_tag_by_name(name)

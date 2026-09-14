from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class ChatMentionLocator(CommonLocator):
    """
    群聊@强提醒选人列表组件定位器 (Mention / At Member Picker)
    在群聊输入框输入 @ 符号后弹出的独立选人界面
    包含：
    1. 顶部导航栏与搜索/取消
    2. 顶部【@所有人】整行容器、勾选框、文本
    3. 成员列表 RecyclerView 及其多选/单选条目（勾选框、头像、昵称）
    4. 右侧字母索引栏与 UiScrollable 滑动检索定位器
    """
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # =========================================================================
    # 1. 顶部导航栏与通用控制
    # =========================================================================
    BACK_BTN = CommonLocator.TOP_BAR_BACK_BTN                                            # 顶部返回/取消按钮
    TV_TITLE = CommonLocator.TOP_TV_TITLE                                                # 顶部标题 (如 "选择提醒的人")
    CONFIRM_BTN = CommonLocator.TOP_BAR_EDIT_TO_BTN                                      # 右上角确认/完成按钮 (若有多选)

    # 搜索框
    SEARCH_EDIT_ID = f"{PACKAGE_ID}/search_edit_text"
    SEARCH_EDIT = (AppiumBy.ID, SEARCH_EDIT_ID)                                          # 搜索成员输入框
    SEARCH_CLEAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_clear_search")                        # 清除搜索按钮

    # =========================================================================
    # 2. 顶部【@所有人】相关元素
    # =========================================================================
    LL_AT_ALL_ID = f"{PACKAGE_ID}/ll_at_all"
    LL_AT_ALL = (AppiumBy.ID, LL_AT_ALL_ID)                                              # @所有人 整行容器
    CHECK_AT_ALL_ID = f"{PACKAGE_ID}/check_at_all"
    CHECK_AT_ALL = (AppiumBy.ID, CHECK_AT_ALL_ID)                                       # @所有人 勾选状态图标
    AT_ALL_TEXT = (AppiumBy.XPATH, f"//*[@resource-id='{LL_AT_ALL_ID}']//android.widget.TextView")  # @所有人 文本

    # =========================================================================
    # 3. 成员列表 RecyclerView
    # =========================================================================
    MEMBER_LIST_RV_ID = f"{PACKAGE_ID}/member_list_rv"
    MEMBER_LIST_RV = (AppiumBy.ID, MEMBER_LIST_RV_ID)                                   # 群成员列表 RecyclerView
    INDEX_BAR_ID = f"{PACKAGE_ID}/index_bar"
    INDEX_BAR = (AppiumBy.ID, INDEX_BAR_ID)                                             # 右侧字母索引栏 (A-Z)

    # =========================================================================
    # 4. 成员行列表项元素 (Item View)
    # =========================================================================
    CHECK_MEMBER_ID = f"{PACKAGE_ID}/check_member"
    CHECK_MEMBER = (AppiumBy.ID, CHECK_MEMBER_ID)                                       # 成员勾选状态图标
    FRIEND_HEADER_ID = f"{PACKAGE_ID}/friend_header"
    FRIEND_HEADER = (AppiumBy.ID, FRIEND_HEADER_ID)                                     # 成员头像
    FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"
    FRIEND_NAME = (AppiumBy.ID, FRIEND_NAME_ID)                                         # 成员姓名文本

    # 所有可见成员行列表
    ALL_MEMBER_ITEMS = (AppiumBy.XPATH, f"//*[@resource-id='{MEMBER_LIST_RV_ID}']/android.view.ViewGroup")


    # =========================================================================
    # 5. 动态定位器 (精准定位与滑动定位)
    # =========================================================================
    @classmethod
    def get_member_name_by_text(cls, name: str) -> tuple:
        """在群成员列表中定位指定成员的昵称文本控件"""
        return (AppiumBy.XPATH, 
                f"//*[@resource-id='{cls.MEMBER_LIST_RV_ID}']//*[@resource-id='{cls.FRIEND_NAME_ID}' and @text='{name}']")

    @classmethod
    def get_member_item_by_name(cls, name: str) -> tuple:
        """
        在群成员列表中定位包含指定成员的整行容器 ViewGroup
        (点击整行触发命中率最高，避免文本框热区过小问题)
        """
        return (AppiumBy.XPATH, 
                f"//*[@resource-id='{cls.MEMBER_LIST_RV_ID}']/android.view.ViewGroup[.//android.widget.TextView[@resource-id='{cls.FRIEND_NAME_ID}' and @text='{name}']]")

    @classmethod
    def get_checkbox_by_name(cls, name: str) -> tuple:
        """通过成员姓名定位其对应的 check_member 勾选框控件"""
        return (AppiumBy.XPATH, 
                f"//*[@resource-id='{cls.MEMBER_LIST_RV_ID}']/android.view.ViewGroup[.//android.widget.TextView[@resource-id='{cls.FRIEND_NAME_ID}' and @text='{name}']]//*[@resource-id='{cls.CHECK_MEMBER_ID}']")

    @classmethod
    def get_member_by_scroll(cls, name: str) -> tuple:
        """
        使用 UiScrollable 自动在 RecyclerView 列表中平滑滚动查找指定成员
        (解决成员不在首屏、长列表展示时的查找失败与 Flaky 问题)
        """
        return (AppiumBy.ANDROID_UIAUTOMATOR, 
                f'new UiScrollable(new UiSelector().resourceId("{cls.MEMBER_LIST_RV_ID}"))'
                f'.scrollIntoView(new UiSelector().resourceId("{cls.FRIEND_NAME_ID}").text("{name}"))')

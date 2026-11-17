from typing import Tuple
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator_hos import _CommonLocatorHos


class _ContactSelectLocatorHos(_CommonLocatorHos):
    """
    鸿蒙 NEXT 平台通用好友/群聊选择组件定位器 (HarmonyOS ArkUI 专享架构)
    底层深度原生对齐 ArkUI 控件树标签 (NavDestination, List, ListItem, Search, TextInput, Checkbox, Toggle, Image, Text, Dialog 等)
    全面覆盖顶部导航、搜索过滤、联系人与群组列表流、勾选复选框、右侧字母索引及二次转发确认弹窗。
    """

    # 顶部导航栏
    IV_BACK_BTN = _CommonLocatorHos.TOP_IV_BACK_BTN          # 返回按钮
    TV_TITLE = _CommonLocatorHos.TOP_TV_TITLE                # 标题
    TV_FB_ACTION = _CommonLocatorHos.TOP_IV_CONFIRM_BTN      # 确定按钮

    # 创建新的会话按钮
    CREATE_NEW_CONVERSATION = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Column/Row/Text | //Text[@text='创建新的会话']")

    # 创建会话-搜索框
    SEARCH_EDIT = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Column/Row/TextInput")                 # 搜索输入框
    SEARCH_CLEAR = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Column/Row/__Common__/Stack/Image")   # 搜索清除按钮
    SEARCH_ICON = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Column/Row/Image")                     # 搜索图标

    # 列表容器 List 列表
    CONTACT_LIST_RV = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/List")

    # 创建会话-好友条目元素（转发图片页面）
    RECYCLER_VIEW = CONTACT_LIST_RV                                                                 # List 列表
    CONTACT_FIRST_CHAR = (AppiumBy.XPATH, "//ListItemGroup/Text")                                   # 首字母排序字符
    CONTACT_CHECK = (AppiumBy.XPATH, "//ListItem/Column/Row/Image")                                 # 勾选框
    CONTACT_AVATAR = (AppiumBy.XPATH, "//ListItem/Column/Row//__Common__/Image")                    # 头像
    CONTACT_ITEM_ROW = (AppiumBy.XPATH, "//ListItem/Column/Row")                                    # 单个好友行容器
    CONTACT_NAME_ID = "__ContactName__"
    CONTACT_NAME = (AppiumBy.XPATH, "//ListItem/Column/Row/Column/Row/Text")                        # 好友姓名/群名称

    # 创建会话-右侧索引栏
    INDEX_BAR = (AppiumBy.XPATH, "//NavDestinationContent/Stack/Column/Text")                       # 字母索引栏 (A-Z)

    # 会话页面
    CONVERSATION_NAME = (AppiumBy.XPATH, "//ListItem/Column/Row/Row/Text")                          # 会话名称
    # 转发页面
    CREATE_GROUP = CONTACT_LIST_RV                                                                  # 创建群聊
    FRIEND_RV_ID = "__FriendRv__"
    FRIEND_RV = CONTACT_LIST_RV                                                                     # 好友列表
    FRIEND_NAME_ID = "__FriendName__"
    FRIEND_NAME = (AppiumBy.XPATH, "//ListItem/Column/Row/Column/Row/Text")                         # 好友名字
    RV_FRIENDS_ID = "__RvFriends__"
    RV_FRIENDS = CONTACT_LIST_RV                                                                    # 好友列表

    # 好友选择页面（创建群聊/转发）
    CB_SELECT_ID = "__CheckboxSelect__"
    CB_SELECT = (AppiumBy.XPATH, "//ListItem/Column/Row/Image")                                     # 好友勾选按钮
    # 好友未勾选
    CB_SELECT_NO_CHECK = (
        AppiumBy.XPATH,
        "//ListItem/Column/Row/Column/Row/Text[not(contains(@text, 'Abel 江湖' or @text='black'))]",
    )
    # 好友已勾选
    CB_SELECT_CHECKED = (
        AppiumBy.XPATH,
        "//ListItem//Checkbox[@checked='true'] | "
        "//ListItem//Toggle[@checked='true'] | "
        "//ListItem/Column/Row/Image[@checked='true']",
    )

    # 好友页面通过好友名字定位
    @classmethod
    def get_contact_by_name(cls, name: str) -> Tuple[str, str]:
        """
        通过好友名称精准定位好友条目或文本节点
        :param name: 好友姓名/昵称
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//ListItem/Column/Row/Column/Row/Text[@text='{name}']",
        )

    # 转发页面通过好友名字定位
    @classmethod
    def get_forward_contact_by_name(cls, name: str) -> Tuple[str, str]:
        """
        通过名称精准定位转发列表中的好友条目或文本节点
        :param name: 转发目标好友姓名/群名称
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//ListItem/Column/Row/Column/Row/Text[@text='{name}']",
        )

    # 通过群名称定位
    @classmethod
    def get_group_by_name(cls, name: str) -> Tuple[str, str]:
        """
        通过群名称精准定位群聊条目或文本节点
        :param name: 群聊名称
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//ListItem//Text[@text='{name}'] | //ListItem[.//Text[@text='{name}']]",
        )

    # 动态参数化：根据好友姓名获取其专属勾选框
    @classmethod
    def get_checkbox_by_contact_name(cls, name: str) -> Tuple[str, str]:
        """
        通过好友名称精准定位该好友行内的勾选框控件
        :param name: 好友姓名
        :return: (AppiumBy.XPATH, xpath_expression)
        """
        return (
            AppiumBy.XPATH,
            f"//ListItem/Column/Row/Column/Row/Text[@text='{name}']/ancestor::Row/Image",
        )

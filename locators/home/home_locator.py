from typing import TYPE_CHECKING
from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class _HomeLocatorAndroid:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部左上角菜单
    LEFT_MENU = (AppiumBy.ID, f'{PACKAGE_ID}/iv_menu')

    # 顶部中间标题
    MIDDLE_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_state')

    # 顶部右上角菜单 + 按钮
    RIGHT_MENU = (AppiumBy.ID, f'{PACKAGE_ID}/iv_plus')
    # 展开 发起群聊
    EXPAND_START_GROUP_CHAT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_create_groups')
    # 展开 添加朋友
    EXPAND_ADD_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/tv_add_friends')
    # 展开 扫一扫
    EXPAND_SCAN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_scan')

    # 底部
    BOTTOM_ID = f'{PACKAGE_ID}/compose_bottom_bar'
    BOTTOM = (AppiumBy.ID, BOTTOM_ID)
    # 底部搜索
    SEARCH = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("搜索")')
    SEARCH_INPUT = (AppiumBy.CLASS_NAME, "android.widget.EditText")           # 搜索输入框
    # SEARCH_INPUT = (AppiumBy.XPATH, "//android.widget.EditText[.//android.widget.TextView[@text='搜索']]")
    SEARCH_CLEAR = (AppiumBy.CLASS_NAME, 'android.widget.Button')             # 搜索清除按钮
    SEARCH_CANCEL = (AppiumBy.XPATH, "//android.widget.EditText/parent::android.view.View/following-sibling::android.view.View/android.view.View")


    # 底部展开聊天类型菜单
    EXPAND_MENU = (AppiumBy.XPATH,
                   f'//*[@resource-id="{BOTTOM_ID}"]/android.view.View/android.view.View[2]')
    # 好友
    FRIEND = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("好友")')
    # 群聊
    GROUP = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("群主")')
    # 动态
    DYNAMIC = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("动态")')

    # 动态未读消息红点
    DYNAMIC_UNREAD_MSG = (AppiumBy.XPATH, f'//*[@content-desc="动态"]/following-sibling::android.view.View/android.widget.TextView')


    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE


    # 好友页面
    LL_FRIEND_MOMENTS = (AppiumBy.ID, f'{PACKAGE_ID}/ll_friend_moments')    # 朋友圈
    FRIEND_MOMENTS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("好友动态")')
    NEW_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/ll_new_friends')              # 新的朋友容器
    NEW_FRIEND_IV = (AppiumBy.ID, f'{PACKAGE_ID}/new_friends_iv')           # 新的朋友图标
    NEW_FRIEND_TV = (AppiumBy.ID, f'{PACKAGE_ID}/new_friends_tv')           # 新的朋友文本
    NEW_FRIEND_FB_BADGE_COUNT_ID = f'{PACKAGE_ID}/fb_badge_count'
    NEW_FRIEND_FB_BADGE_COUNT = (AppiumBy.ID, NEW_FRIEND_FB_BADGE_COUNT_ID)     # 新的朋友未读消息数
    NEW_FRIEND_FB_BADGE_COUNT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{NEW_FRIEND_FB_BADGE_COUNT_ID}"]/android.widget.TextView')     # 新的朋友未读消息数文本
    
    # 分组管理下的分类标签
    CATEGORY_MANAGER_ROOT_ID = f"{PACKAGE_ID}/ll_category"
    CATEGORY_MANAGER = (AppiumBy.ID, CATEGORY_MANAGER_ROOT_ID)                  # 分组管理容器
    CATEGORY_MANAGER_IV = (AppiumBy.ID, f'{PACKAGE_ID}/category_manager_iv')    # 分组管理图标
    # 分组管理名称
    CATEGORY_MANAGER_TV = (AppiumBy.XPATH, f'//*[@resource-id="{CATEGORY_MANAGER_ROOT_ID}"]//android.widget.TextView')        # 分组管理文本
    



    # 会话列表整个框
    CONVERSATION_LIST = (AppiumBy.ID, f"{PACKAGE_ID}/rv_conversation")
    # 会话
    CONVERSATION_ID = f'{PACKAGE_ID}/cl_item'
    CONVERSATION_ITEM = (AppiumBy.ID, CONVERSATION_ID)
    # 会话名称
    CONVERSATION_NAME_ID = f"{PACKAGE_ID}/tv_name"
    CONVERSATION_NAME = (AppiumBy.ID, CONVERSATION_NAME_ID)

    # 返回不同会话定位
    @classmethod
    def get_conver_by_name(cls, name: str):
        return (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{name}")')

    # 会话时间
    CONVERSATION_TIME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_time")
    # 会话内容
    CONVERSATION_CONTENT_ID = f"{PACKAGE_ID}/tv_message"
    CONVERSATION_CONTENT = (AppiumBy.ID, CONVERSATION_CONTENT_ID)
    # 会话未读消息数外部
    CONVERSATION_UNREAD_COUNT = (AppiumBy.ID, f"{PACKAGE_ID}/fb_msg_unread_count")
    # 会话未读消息数内部
    CONVERSATION_UNREAD_COUNT_INNER = (AppiumBy.ID, f"{PACKAGE_ID}/tv_unread_count")

    # 会话静音整个容器
    CONVERSATION_MUTE = (AppiumBy.ID, f"{PACKAGE_ID}/ll_swipe_mute")
    # 会话静音图标
    CONVERSATION_MUTE_ICON = (AppiumBy.ID, f"{PACKAGE_ID}/iv_swipe_mute")
    # 会话静音文本
    CONVERSATION_MUTE_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_swipe_mute")

    # 会话置顶整个容器
    CONVERSATION_TOP = (AppiumBy.ID, f"{PACKAGE_ID}/ll_swipe_top")
    # 会话置顶图标
    CONVERSATION_TOP_ICON = (AppiumBy.ID, f"{PACKAGE_ID}/iv_swipe_top")
    # 会话置顶文本
    CONVERSATION_TOP_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_swipe_top")

    # 会话删除整个容器
    CONVERSATION_DELETE = (AppiumBy.ID, f"{PACKAGE_ID}/ll_swipe_delete")
    # 会话删除图标
    CONVERSATION_DELETE_ICON = (AppiumBy.ID, f"{PACKAGE_ID}/iv_swipe_delete")
    # 会话删除文本
    CONVERSATION_DELETE_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("删除")')
    # 会话隐藏
    CONVERSATION_HIDE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_hide_conversation")
    # 会话删除弹窗 清空聊天记录并隐藏
    CONVERSATION_DELETE_DIALOG_CLEAR_CHAT_RECORD = (AppiumBy.ID, f"{PACKAGE_ID}/tv_clear_history_and_hide")
    # 会话删除弹窗 确认删除
    CONVERSATION_DELETE_DIALOG_CONFIRM = (AppiumBy.ID, f"{PACKAGE_ID}/tv_delete")
    # 会话删除弹窗 取消
    CONVERSATION_DELETE_DIALOG_CANCEL = (AppiumBy.ID, f"{PACKAGE_ID}/fb_cancel")

    # 置顶折叠入口 图标
    CONVERSATION_FOLD_ENTRY = (AppiumBy.ID, f"{PACKAGE_ID}/iv_fold")
    # 置顶折叠数量文本
    CONVERSATION_FOLD_COUNT_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_fold_count")
    # 置顶折叠入口整个元素 ViewGroup (直接父级，防止 ancestor 遍历命中外层大容器)
    CONVERSATION_FOLD_VIEWGROUP = (AppiumBy.XPATH,
                                   f"//*[@resource-id='{PACKAGE_ID}/tv_fold_count']/parent::android.view.ViewGroup")

    # 会话草稿状态
    CONVERSATION_DRAFT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_msg_status")
    # 会话停用状态
    CONVERSATION_DISABLE = (AppiumBy.ID, f"{PACKAGE_ID}/iv_deactivate")
    # 会话未读状态
    CONVERSATION_UNREAD = (AppiumBy.ID, f"{PACKAGE_ID}/tvIsRead")
    # 会话未读消息数
    CONVERSATION_UNREAD_COUNT = (AppiumBy.XPATH, f"//*[@resource-id='{PACKAGE_ID}/fb_msg_unread_count']/android.widget.TextView")

    # 会话封禁状态 - 待完善
    # 会话发送消息状态=发送中，待完善
    # 会话发送消息状态=发送失败，待完善


    # 聊天密码
    # 输入聊天密码弹窗
    CHAT_PASSWORD_DIALOG_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_dialog_title")             # 请输入密码标题
    CHAT_PASSWORD_DIALOG_CONTENT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_dialog_content")         # 聊天密码
    CHAT_PASSWORD_TV_FORGOT_PASSWORD = (AppiumBy.ID, f"{PACKAGE_ID}/tv_forgot_password")    # 忘记密码
    # 输入6位数字聊天密码框
    CHAT_PASSWORD_VIEW_INPUT_CODE_ID = f"{PACKAGE_ID}/view_input_code"
    CHAT_PASSWORD_VIEW_INPUT_CODE = (AppiumBy.ID, CHAT_PASSWORD_VIEW_INPUT_CODE_ID)          
    # 密码单个输入框
    CHAT_PASSWORD_VIEW_INPUT_CODE_LIST = (AppiumBy.XPATH, f"//*[@resource-id='{CHAT_PASSWORD_VIEW_INPUT_CODE_ID}']/android.widget.EditText") 


    # 通过好友昵称获取他的会话下面消息的定位
    @classmethod
    def get_message_by_name(cls, name: str):
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.CONVERSATION_ID}" '
                f' and .//*[@resource-id="{cls.CONVERSATION_NAME_ID}" and @text="{name}"]]'
                f'//*[@resource-id="{cls.CONVERSATION_CONTENT_ID}"]')

    # 通过会话名称获取它的会话的定位 反向定位 //*[@text="奥利奥利奥利奥"]/ancestor::*[@resource-id="com.santiaotalk.im:id/cl_item"]
    @classmethod
    def get_session_by_name(cls, name: str):
        return (AppiumBy.XPATH,
                f'//*[@text="{name}"]/ancestor::*[@resource-id="{cls.CONVERSATION_ID}"]')
    
    # 精确获取某一个会话的停用状态
    @classmethod
    def get_disable_by_name(cls, name: str):
        return (AppiumBy.XPATH, 
                f'//*[@resource-id="{cls.CONVERSATION_ID}" and .//*[@text="{name}"]]'
                f'//*[@resource-id="{cls.PACKAGE_ID}/iv_deactivate"]')

    # 精确获取某一个会话的未读消息数
    @classmethod
    def get_unread_count_by_name(cls, name: str):
        return (AppiumBy.XPATH, 
                f'//*[@resource-id="{cls.CONVERSATION_ID}" and .//*[@text="{name}"]]'
                f'//*[@resource-id="{cls.PACKAGE_ID}/fb_msg_unread_count"]/android.widget.TextView')

    # 精确获取某一个会话的消息阅读状态 (未读/已读)
    @classmethod
    def get_read_status_by_name(cls, name: str):
        return (AppiumBy.XPATH, 
                f'//*[@resource-id="{cls.CONVERSATION_ID}" and .//*[@text="{name}"]]'
                f'//*[@resource-id="{cls.PACKAGE_ID}/tvIsRead"]')

    # 获取某一个聊天密码输入框
    @classmethod
    def get_password_input_by_index(cls, index: int):
        return (AppiumBy.XPATH, 
                f'//*[@resource-id="{cls.CHAT_PASSWORD_VIEW_INPUT_CODE_ID}"]/android.widget.EditText[{index+1}]')

    # 会话强提醒前缀标签 ID (@人的消息、进群验证消息，如 [有人@我], [@所有人], [进群申请])
    CONVERSATION_USER_NAME_ID = f"{PACKAGE_ID}/tv_user_name"
    CONVERSATION_USER_NAME = (AppiumBy.ID, CONVERSATION_USER_NAME_ID)

    # 精确获取某一个会话的状态提醒标签 (@人的消息、进群验证消息，如 [有人@我], [@所有人], [进群申请])
    @classmethod
    def get_remind_status_by_name(cls, name: str):
        return (AppiumBy.XPATH, 
                f'//*[@resource-id="{cls.CONVERSATION_ID}" and .//*[@resource-id="{cls.CONVERSATION_NAME_ID}" and contains(@text, "{name}")]]'
                f'//*[@resource-id="{cls.CONVERSATION_USER_NAME_ID}"]')


# =========================================================================
# 跨端通用定位器透明代理 (自动识别 Android / HarmonyOS NEXT / iOS)
# =========================================================================
from core.locator_manager import DynamicLocatorMeta
from locators.home.home_locator_hos import _HomeLocatorHos
from locators.home.home_locator_ios import _HomeLocatorIos


class HomeLocator(_HomeLocatorIos, _HomeLocatorAndroid, _HomeLocatorHos, metaclass=DynamicLocatorMeta):
    """跨端主页与会话列表定位器（支持 IDE Ctrl + 鼠标左键直接跳转定义，运行时按设备平台动态分发）"""

    _android_cls = _HomeLocatorAndroid
    _harmony_cls = _HomeLocatorHos
    _ios_cls = _HomeLocatorIos

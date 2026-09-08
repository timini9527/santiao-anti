from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class SessionSelectLocator(CommonLocator):
    """通用会话选择组件定位器 (常用于转发、分享群名片等场景)"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部导航栏
    # 导航条
    BAR_CONTAINER = (AppiumBy.ID, f"{PACKAGE_ID}/top_bar")                      # 导航条容器
    BACK_BUTTON = (AppiumBy.ID, f"{PACKAGE_ID}/back")                           # 返回按钮
    TITLE_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/title_tv")                        # 页面标题
    FINISH_BUTTON = (AppiumBy.ID, f"{PACKAGE_ID}/edit_to")                      # 确定按钮
    
    # 列表容器
    SHARE_RV = (AppiumBy.ID, f"{PACKAGE_ID}/share_rv")                          # RecyclerView 列表 (通常复用主页 ID)
    FRIEND_RV = (AppiumBy.ID, f"{PACKAGE_ID}/friend_rv")                        # 好友列表
    
    # 会话条目元素
    SESSION_CHECKBOX = (AppiumBy.ID, f"{PACKAGE_ID}/check_member")              # 会话条目CheckBox
    SESSION_FRIEND_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/friend_header")        # 头像
    SESSION_FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"
    SESSION_FRIEND_NAME = (AppiumBy.ID, SESSION_FRIEND_NAME_ID)                 # 会话名称 (好友名/群名)
    CONTACT_NAME_ID = f"{PACKAGE_ID}/tv_name"
    CONTACT_NAME = (AppiumBy.ID, CONTACT_NAME_ID)                               # 好友姓名/群名称

    # 分享/转发确认弹层
    TV_TITLE = CommonLocator.TOP_TV_TITLE                                       # 弹层标题(发送给)
    CLOSE = (AppiumBy.ID, f'{PACKAGE_ID}/close')                                # 关闭/取消按钮
    COMMENT_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/comment_input')                # 留言输入框(带句话~)
    EMOJI_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_button')                  # 表情按钮
    SEND_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/send_button')                    # 发送按钮



    @classmethod
    def get_session_by_name(cls, name: str):
        """通过名称精确获取会话条目"""
        return (AppiumBy.ANDROID_UIAUTOMATOR, 
                f'new UiSelector().resourceId("{cls.SESSION_FRIEND_NAME_ID}").text("{name}")')

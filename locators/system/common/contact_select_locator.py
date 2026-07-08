from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator

class ContactSelectLocator(CommonLocator):
    """通用好友/群聊选择组件定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部导航栏
    BACK_BUTTON = CommonLocator.TOP_IV_BACK_BTN                     # 返回按钮
    TITLE_TEXT = CommonLocator.TOP_TV_TITLE                         # 页面标题 (如: 选择好友)
    FB_ACTION = CommonLocator.TOP_FB_ACTION_BTN                     # 确定按钮
    
    # 搜索框
    SEARCH_EDIT = (AppiumBy.ID, f"{PACKAGE_ID}/et_search")          # 搜索输入框
    SEARCH_CLEAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_clear_search")   # 搜索清除按钮
    SEARCH_ICON = (AppiumBy.ID, f"{PACKAGE_ID}/iv_search_icon")     # 搜索图标

    # 列表容器
    CONTACT_LIST_RV = (AppiumBy.ID, f"{PACKAGE_ID}/rv_friends")     # RecyclerView 列表
    
    # 好友条目元素（转发图片页面）
    RECYCLER_VIEW = (AppiumBy.ID, f"{PACKAGE_ID}/recycler_view")    # RecyclerView 列表
    CONTACT_FIRST_CHAR = (AppiumBy.ID, f"{PACKAGE_ID}/tv_char")     # 首字母排序字符
    CONTACT_AVATAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_avatar")       # 头像
    CONTACT_ITEM_ROW = (AppiumBy.ID, f"{PACKAGE_ID}/cl_top")        # 单个好友行容器
    CONTACT_NAME_ID = f"{PACKAGE_ID}/tv_name"
    CONTACT_NAME = (AppiumBy.ID, CONTACT_NAME_ID)                   # 好友姓名/群名称

    # 右侧索引栏
    INDEX_BAR = (AppiumBy.ID, f"{PACKAGE_ID}/slider_index_bar")     # 字母索引栏 (A-Z)

    # 二次弹窗容器
    SECOND_DIALOG_CONTAINER = (AppiumBy.ID, f"{PACKAGE_ID}/content")            # 二次弹窗容器
    SECOND_DIALOG_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_dialog_title")        # 二次弹窗标题
    SECOND_DIALOG_CANCEL_BUTTON = CommonLocator.DIALOG_CANCEL_BTN               # 二次弹窗取消按钮
    SECOND_DIALOG_CONFIRM_BUTTON = CommonLocator.DIALOG_CONFIRM_BTN             # 二次弹窗确认按钮

    
    # 转发页面
    CREATE_GROUP = (AppiumBy.ID, f"{PACKAGE_ID}/create_group")                  # 创建群聊
    FRIEND_RV_ID = f"{PACKAGE_ID}/friend_rv"
    FRIEND_RV = (AppiumBy.ID, FRIEND_RV_ID)                                     # 好友列表
    FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"
    FRIEND_NAME = (AppiumBy.ID, FRIEND_NAME_ID)                                 # 好友名字
    RV_FRIENDS_ID = f"{PACKAGE_ID}/rv_friends"
    RV_FRIENDS = (AppiumBy.ID, RV_FRIENDS_ID)                                   # 好友列表


    # 好友选择页面（创建群聊/转发）
    CB_SELECT_ID = f"{PACKAGE_ID}/cb_select"
    CB_SELECT = (AppiumBy.ID, CB_SELECT_ID)                                     # 好友勾选按钮      
    # 好友未勾选
    # CB_SELECT_NO_CHECK = (AppiumBy.XPATH, f'//*[@resource-id="{RV_FRIENDS_ID}"]/android.view.ViewGroup/*[@resource-id="{CB_SELECT_ID}" and @checked="false"]') 
    CB_SELECT_NO_CHECK = (
        AppiumBy.XPATH,
        f'//*[@resource-id="{RV_FRIENDS_ID}"]/android.view.ViewGroup'
        f'[not(.//*[@resource-id="{CONTACT_NAME_ID}" and (@text="Abel 江湖" or @text="black")])]'
        f'//*[@resource-id="{CB_SELECT_ID}" and @checked="false"]'
    )
    # 好友已勾选    
    CB_SELECT_CHECKED = (AppiumBy.XPATH, f'//*[@resource-id="{RV_FRIENDS_ID}"]/android.view.ViewGroup/*[@resource-id="{CB_SELECT_ID}" and @checked="true"]')        

    

    # 好友页面通过好友名字定位
    @classmethod
    def get_contact_by_name(cls, name: str):
        """通过名称精确获取好友条目"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@resource-id="{cls.CONTACT_NAME_ID}" and @text="{name}"]')
    
    # 转发页面通过好友名字定位
    @classmethod
    def get_forward_contact_by_name(cls, name: str):
        """通过名称精确获取好友条目"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@resource-id="{cls.FRIEND_NAME_ID}" and @text="{name}"]')

    # 通过群名称定位
    @classmethod
    def get_group_by_name(cls, name: str):
        """通过群名称精确获取群聊条目"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@resource-id="{cls.CONTACT_NAME_ID}" and @text="{name}"]')




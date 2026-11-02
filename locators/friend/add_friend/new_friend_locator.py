from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator
from locators.friend.profile.contact_detail_locator import ContactDetailLocator

class NewFriendLocator(ContactDetailLocator):
    """新的朋友申请列表页面定位器 (基于 0.4 添加好友模块 - 申请列表 UI)"""
    
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 1. 顶部标题栏元素
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN                             # 返回按钮
    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE                               # 页面标题 "新的朋友"
    TOP_IV_ACTION_BTN = CommonLocator.TOP_IV_ACTION_BTN                         # 右上角清空（垃圾桶）按钮

    CONFIRM_BTN = CommonLocator.DIALOG_CONFIRM_BTN                      # 确认清空按钮
    CANCEL_BTN = CommonLocator.DIALOG_CANCEL_BTN                        # 取消清空按钮

    # 2. 搜索框
    FB_SEARCH_ID = f"{PACKAGE_ID}/fb_search"
    FB_SEARCH = (AppiumBy.ID, FB_SEARCH_ID)                             # 搜索框
    ET_SEARCH = (AppiumBy.XPATH, f'//*[@resource-id="{FB_SEARCH_ID}"]/android.widget.TextView')  
    

    # 3. 申请项列表及条目
    RV_NEW_FRIENDS = (AppiumBy.ID, f"{PACKAGE_ID}/rv_new_friends")      # 申请列表 RecyclerView

    CL_ITEM_ID = f"{PACKAGE_ID}/cl_item"
    CL_ITEM = (AppiumBy.ID, CL_ITEM_ID)                                 # 申请条目容器
    IV_AVATAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_avatar")                # 头像容器
    TV_NAME_ID = f"{PACKAGE_ID}/tv_name"
    TV_NAME = (AppiumBy.ID, TV_NAME_ID)                                 # 申请人昵称
    TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TV_NAME_ID}"]/android.widget.TextView')
    TV_MESSAGE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_message")              # 申请消息内容
    FB_STATUS_ID = f"{PACKAGE_ID}/fb_status"
    FB_STATUS = (AppiumBy.ID, FB_STATUS_ID)                             # 申请状态
    FB_STATUS_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{FB_STATUS_ID}"]/android.widget.TextView')
    LL_SWIPE_DELETE = (AppiumBy.ID, f"{PACKAGE_ID}/ll_swipe_delete")    # 左滑删除布局


    # 5. 申请详情页元素
    APPLY_ADD_FRIEND_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/apply_addFriend")
    

    # 4. 动态匹配特定发送人的申请行容器
    @classmethod
    def get_apply_item_by_name(cls, sender_name: str) -> tuple:
        """根据发送人昵称，动态定位整行申请条目（常用于点击进入验证详情页）"""
        return (
            AppiumBy.XPATH,
            f'//*[@resource-id="{cls.TV_NAME_ID}"]//*[contains(@text, "{sender_name}")]'
            f'/ancestor::*[@resource-id="{cls.CL_ITEM_ID}"]'
        )

    # 动态匹配特定发送人的接受按钮
    @classmethod
    def get_accept_btn_by_name(cls, sender_name: str) -> tuple:
        """根据发送人昵称，动态定位其右侧的[接受/同意]按钮"""
        return (
            AppiumBy.XPATH,
            f'//*[@resource-id="{cls.TV_NAME_ID}"]//*[contains(@text, "{sender_name}")]'
            f'/ancestor::*[@resource-id="{cls.CL_ITEM_ID}"]'
            f'//*[@resource-id="{cls.FB_STATUS_ID}"]//*[contains(@text, "接受") or contains(@text, "同意")]'
        )

    # 动态匹配特定发送人的状态展示文本
    @classmethod
    def get_status_text_by_name(cls, sender_name: str, status_text: str) -> tuple:
        """根据发送人昵称与期望状态文字，动态定位其右侧的状态文本（如：已添加、已拒绝）"""
        return (
            AppiumBy.XPATH,
            f'//*[@resource-id="{cls.TV_NAME_ID}"]//*[contains(@text, "{sender_name}")]'
            f'/ancestor::*[@resource-id="{cls.CL_ITEM_ID}"]'
            f'//*[contains(@text, "{status_text}")]'
        )


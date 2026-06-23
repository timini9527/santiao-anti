from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class GroupManagerLocator:
    """群管理页面定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部导航
    IV_BACK = (AppiumBy.ID, f"{PACKAGE_ID}/iv_back")                                                     # 返回按钮
    TV_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_title")                                                   # 页面标题 "群管理"

    # 列表项
    VIEW_UPDATE_GROUP = (AppiumBy.ID, f"{PACKAGE_ID}/view_update_group")                                 # 升级群组
    IT_GROUP_MANAGER = (AppiumBy.ID, f"{PACKAGE_ID}/it_group_manager")                                   # 管理员
    JOIN_TO_GROUP_APPLY = (AppiumBy.ID, f"{PACKAGE_ID}/join_to_group_apply")                             # 进群申请
    GROUP_MEMBER_MUTE = (AppiumBy.ID, f"{PACKAGE_ID}/group_member_mute")                                 # 指定成员禁言
    GROUP_BLACK_MEMBER = (AppiumBy.ID, f"{PACKAGE_ID}/group_black_member")                               # 群黑名单
    GROUP_GIVE = (AppiumBy.ID, f"{PACKAGE_ID}/group_give")                                               # 转让群主
    DISMISS_GROUP = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupDismiss")                             # 解散群组

    # 具有 Switch 开关的配置项及其对应的开关按钮
    GROUP_ID_SEARCH_SWITCH = (AppiumBy.XPATH, 
        "//*[contains(@resource-id, 'group_id_search')]//*[contains(@resource-id, 'switch_btn')]")                   # 群ID搜索开关
    JOIN_TO_GROUP_VERIFY_SWITCH = (AppiumBy.XPATH, 
        "//*[contains(@resource-id, 'join_to_group_verify')]//*[contains(@resource-id, 'switch_btn')]")              # 进群验证开关
    ALL_MEMBER_MUTE_SWITCH = (AppiumBy.XPATH, 
        "//*[contains(@resource-id, 'all_member_mute')]//*[contains(@resource-id, 'switch_btn')]")                   # 全员禁言开关
    UN_ADD_FRIEND_EACH_OTHER_SWITCH = (AppiumBy.XPATH, 
        "//*[contains(@resource-id, 'all_member_unAddFriend_eachOther')]//*[contains(@resource-id, 'switch_btn')]")  # 禁止群成员互相加好友开关



    # ===================================================================================
    # 指定禁言页面相关
    # ===================================================================================
    RECYCLER_ID = f"{PACKAGE_ID}/recycler"
    RECYCLE_VIEW_MEMBER = (AppiumBy.ID, RECYCLER_ID)                                        # 成员列表区域
    IMG_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/img_header")                                  # 群成员头像
    RECYCLE_VIEW_MEMBER_TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                    # 成员姓名
    RECYCLE_VIEW_MEMBER_TV_STATUS = (AppiumBy.ID, f"{PACKAGE_ID}/tv_status")                # 禁言状态及时间
    TV_CANCEL_MUTE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_remove")                               # 解除禁言按钮

    # 已禁言 Item（包含头像、名称、状态、操作按钮）
    MUTED_MEMBER = (AppiumBy.XPATH, f"//*[@resource-id='{RECYCLER_ID}']/android.view.ViewGroup//android.view.ViewGroup")

    # 移除禁言后的二次弹窗
    TV_DIALOG_MSG = (AppiumBy.ID, f"{PACKAGE_ID}/message")                                  # 弹窗内容
    POSITIVE_BUTTON = (AppiumBy.ID, f"{PACKAGE_ID}/positiveButton")                         # 确认按钮
    NEGATIVE_BUTTON = (AppiumBy.ID, f"{PACKAGE_ID}/negativeButton")                         # 取消按钮
    

    # 通过昵称定位到成员
    @classmethod
    def get_member_by_name(cls, name: str) -> tuple:
        """通过昵称定位到成员"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.RECYCLER_ID}']//*[@resource-id='{cls.RECYCLE_VIEW_MEMBER_TV_NAME}'][contains(@text, '{name}')]/ancestor::android.view.ViewGroup[1]")




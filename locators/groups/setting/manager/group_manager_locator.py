from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class GroupManagerLocator(CommonLocator):
    """群管理页面定位器"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部导航
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                                             # 返回按钮
    TV_TITLE = CommonLocator.TOP_TV_TITLE                                               # 顶部标题
    TITLE_TV = CommonLocator.TOPBAR_TITLE                                               # 标题
    FB_BTN = CommonLocator.TOP_FB_ACTION_BTN                                            # 完成/确定
    EDIT_TO_BTN = CommonLocator.TOPBAR_RIGHT_FINISH_BTN                                 # 编辑完成按钮


    # 列表项
    VIEW_UPDATE_GROUP = (AppiumBy.ID, f"{PACKAGE_ID}/view_update_group")                                 # 升级群组
    IT_GROUP_MANAGER = (AppiumBy.ID, f"{PACKAGE_ID}/it_group_manager")                                   # 管理员
    JOIN_TO_GROUP_APPLY = (AppiumBy.ID, f"{PACKAGE_ID}/join_to_group_apply")                             # 进群申请
    GROUP_MEMBER_MUTE = (AppiumBy.ID, f"{PACKAGE_ID}/group_member_mute")                                 # 指定成员禁言
    GROUP_BLACK_MEMBER = (AppiumBy.ID, f"{PACKAGE_ID}/group_black_member")                               # 群黑名单
    GROUP_GIVE = (AppiumBy.ID, f"{PACKAGE_ID}/group_give")                                               # 转让群主
    DISMISS_GROUP = (AppiumBy.ID, f"{PACKAGE_ID}/setting_chat_groupDismiss")                             # 解散群组
    SWITCH_BTN_ID = f"{PACKAGE_ID}/switch_btn"
    SWITCH_BTN = (AppiumBy.ID, SWITCH_BTN_ID)                                                            # Switch 开关


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
    # 管理员列表相关
    # ===================================================================================
    EDIT_SEARCH = (AppiumBy.ID, f"{PACKAGE_ID}/edit_search")                                    # 管理员搜索框
    MEMBER_TYPE = (AppiumBy.ID, f"{PACKAGE_ID}/member_type")                                    # 管理员/群成员标签标识
    IT_ADD_FRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/lt_add_friend")                                # 新增管理员按钮
    search_edit_text = (AppiumBy.ID, f"{PACKAGE_ID}/search_edit_text")                          # 成员搜索输入框
    TV_FRIEND_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/friend_header")                             # 成员头像
    TV_FRIEND_NAME_ID = f"{PACKAGE_ID}/friend_name"
    TV_FRIEND_NAME = (AppiumBy.ID, TV_FRIEND_NAME_ID)                                           # 成员名称

    # 管理员内部权限管理
    IC_LAYOUT = (AppiumBy.ID, f"{PACKAGE_ID}/ic_layout")                                        # 权限 LAYOUT
    SURE_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/sure")                                              # 移除管理员按钮
    TV_CONTENT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_content")                                      # 二次弹窗移除按钮

    
    # 通过姓名获取成员
    @classmethod
    def get_member_by_text(cls, name: str) -> tuple:
        """通过姓名获取成员"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.TV_FRIEND_NAME_ID}' and @text='{name}']")

    # 通过 checked 状态定位到switch：false/true状态的开关
    @classmethod
    def get_switch_by_checked_value(cls, checked: str) -> tuple:
        """通过 checked 状态定位到 switch：false/true状态的开关"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.SWITCH_BTN_ID}' and @checked='{checked}']")


    # ===================================================================================
    # 指定禁言页面相关
    # ===================================================================================
    RECYCLER_ID = f"{PACKAGE_ID}/recycler"
    RECYCLE_VIEW_MEMBER = (AppiumBy.ID, RECYCLER_ID)                                        # 成员列表区域
    IMG_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/img_header")                                  # 群成员头像
    TV_NAME_ID = f"{PACKAGE_ID}/tv_name"
    RECYCLE_VIEW_MEMBER_TV_NAME = (AppiumBy.ID, TV_NAME_ID)                                 # 成员姓名
    TV_STATUS_ID = f"{PACKAGE_ID}/tv_status"
    RECYCLE_VIEW_MEMBER_TV_STATUS = (AppiumBy.ID, TV_STATUS_ID)                             # 禁言状态及时间
    TV_CANCEL_MUTE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_remove")                               # 解除禁言按钮

    # 已禁言 Item（包含头像、名称、状态、操作按钮）
    MUTED_MEMBER = (AppiumBy.XPATH, f"//*[@resource-id='{RECYCLER_ID}']/android.view.ViewGroup//android.view.ViewGroup")

    # 移除禁言后的二次弹窗
    TV_DIALOG_MSG = (AppiumBy.ID, f"{PACKAGE_ID}/message")                                  # 弹窗内容
    POSITIVE_BUTTON = (AppiumBy.ID, f"{PACKAGE_ID}/positiveButton")                         # 确认按钮
    NEGATIVE_BUTTON = (AppiumBy.ID, f"{PACKAGE_ID}/negativeButton")                         # 取消按钮

    
    # 禁言设置页面
    CB_1 = (AppiumBy.ID, f"{PACKAGE_ID}/cb_1")                                              # 永久禁言
    CB_2 = (AppiumBy.ID, f"{PACKAGE_ID}/cb_2")                                              # 临时禁言
    TV_TIME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_time")                                        # 临时禁言时长
    ED_CONTENT = (AppiumBy.ID, f"{PACKAGE_ID}/et_content")                                  # 禁言原因输入框
    LOOP_SELECTOR = (AppiumBy.ID, f"{PACKAGE_ID}/loop")                                     # 循环滚动选择器
    TV_SURE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_sure")                                        # 确认按钮
    
    MUTE_CONFIRM_BTN = CommonLocator.DIALOG_CONFIRM_BTN                                     # 指定禁言二次确认-确认按钮
    MUTE_CANCEL_BTN = CommonLocator.DIALOG_CANCEL_BTN                                       # 指定禁言二次确认-取消按钮

    
    # 通过昵称定位到成员
    @classmethod
    def get_member_by_name(cls, name: str) -> tuple:
        """通过昵称定位到成员"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.TV_NAME_ID}' and @text='{name}']")
        # return (AppiumBy.XPATH, f"//*[@resource-id='{cls.RECYCLER_ID}']//*[@resource-id='{cls.RECYCLE_VIEW_MEMBER_TV_NAME}'][contains(@text, '{name}')]/ancestor::android.view.ViewGroup[1]")

    # 通过昵称定位到其禁言状态元素
    @classmethod
    def get_mute_status_by_name(cls, name: str) -> tuple:
        """通过昵称定位到其禁言状态元素"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.TV_NAME_ID}' and @text='{name}']/following-sibling::*[@resource-id='{cls.TV_STATUS_ID}']")


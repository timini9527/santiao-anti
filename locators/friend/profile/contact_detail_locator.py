from typing import Tuple

from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ContactDetailLocator:
    """好友资料详情页定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID
    
    # 头部个人资料区域
    AVATAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_avatar")               # 头像
    TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")               # 顶部显示的昵称
    TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/tv_name"]//android.widget.TextView')
    
    # 详情信息行
    INFO_NICKNAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_small_name")    # 昵称标签处的文字
    ST_ID = (AppiumBy.ID, f"{PACKAGE_ID}/tv_santiao_id")            # 三条 ID 标签处的文字
    LOCATION = (AppiumBy.ID, f"{PACKAGE_ID}/tv_location")           # 所在地标签处的文字
    
    # 业务功能列表项
    SET_REMARK_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/title_remark")   # 设置备注
    RECOMMEND_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/share_to_friend") # 推荐给朋友
    MOMENTS_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/title_moments")     # 动态
    MORE_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/title_more")           # 更多
    MAIN = (AppiumBy.ID, f"{PACKAGE_ID}/main")                      # 更多-NEW
    
    # 底部操作按钮区域
    BOTTOM_BAR = (AppiumBy.ID, f"{PACKAGE_ID}/friend")              # 底部按钮容器包含发送消息和视频通话
    SEND_MSG_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/send_message")      # 发送消息
    CALL_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/video_call")            # 视频通话


    # === 非好友详情页面 ===
    WHITE_UNFRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/white_unfriend")  # 申请添加好友按钮



    # === 添加好友页面 ===
    # 添加好友页面 - 头像
    ADD_FRIEND_IV_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_avatar')
    # 添加好友页面 - 昵称
    ADD_FRIEND_TV_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_name')
    ADD_FRIEND_TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/tv_name"]//android.widget.TextView')
    # 添加好友页面 - 所在地
    ADD_FRIEND_TV_LOCATION = (AppiumBy.ID, f'{PACKAGE_ID}/tv_location')
    # 添加好友页面 - 好友资料容器
    ADD_FRIEND_LL= (AppiumBy.ID, f'{PACKAGE_ID}/ll')
    # 好友资料容器 - 好友资料标题行
    ADD_FRIEND_TITLE_REMARK = (AppiumBy.ID, f'{PACKAGE_ID}/title_remark')
    # 好友资料容器 - 资料卡标题容器
    ADD_FRIEND_TV_PROFILE_CARD_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/profile_card_title')
    # 好友资料容器 - 资料卡描述容器
    ADD_FRIEND_TV_PROFILE_CARD_DESC = (AppiumBy.ID, f'{PACKAGE_ID}/profile_card_desc')

    # 添加好友页面 - 好友动态
    ADD_FRIEND_TITLE_MOMENTS = (AppiumBy.ID, f'{PACKAGE_ID}/title_moments')  
    ADD_FRIEND_TITLE_TV = (AppiumBy.ID, f'{PACKAGE_ID}/title_tv')

    # 添加好友页面 - 未添加好友
    ADD_FRIEND_TV_NOT_FRIENDS = (AppiumBy.ID, f'{PACKAGE_ID}/cl_un_friends')
    ADD_FRIEND_TV_ADD_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/add_friend')
    ADD_FRIEND_TV_ADD_FRIEND_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/add_friend"]//android.widget.TextView')

    # 好友详情页顶部
    IV_RIGHT = (AppiumBy.ID, f"{PACKAGE_ID}/iv_right")                      # 右上角更多图标
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN                                 # 返回按钮
    CONFIRM_TWO_BTN = CommonLocator.DIALOG_CONFIRM_BTN                      # 二次确认按钮
    CANCEL_TWO_BTN = CommonLocator.DIALOG_CANCEL_BTN                        # 二次取消按钮
    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE                                   # 页面标题



    # 好友详情页面 - 资料卡电话号码
    ROW_PROFILE_PHONE = (AppiumBy.ID, f'{PACKAGE_ID}/row_profile_phone')            # 电话行
    TV_PROFILE_PHONE_LABEL = (AppiumBy.ID, f'{PACKAGE_ID}/tv_profile_phone_label')  # 电话标签
    TV_PROFILE_PHONE_VALUE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_profile_phone_value')  # 电话号码
    
    # 电话资料卡详情页面
    DESIGN_BOTTOM_SHEET = (AppiumBy.ID, f'{PACKAGE_ID}/design_bottom_sheet')        # 电话资料卡详情页
    IV_CLOSE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_close')                              # 关闭按钮
    RV_LIST = (AppiumBy.ID, f'{PACKAGE_ID}/rv_list')                                # 电话列表
    TV_PHONE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_phone')                              # 电话号码
    IV_COPY = (AppiumBy.ID, f'{PACKAGE_ID}/iv_copy')                                # 复制按钮
    IV_CALL = (AppiumBy.ID, f'{PACKAGE_ID}/iv_call')                                # 拨号按钮
    # 呼叫页面1
    TV_NUMBER = (AppiumBy.ID, f'{PACKAGE_ID}/tv_number')                            # 电话号码
    TV_CALL = (AppiumBy.ID, f'{PACKAGE_ID}/tv_call')                                # 拨号
    TV_COPY = (AppiumBy.ID, f'{PACKAGE_ID}/tv_copy')                                # 复制
    TV_CANCEL = CommonLocator.TV_CANCEL_BTN                                         # 取消
    # 呼叫页面2
    CONTENT_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/content_layout')                  # 布局容器
    CALL_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("呼叫")')     # 呼叫
    CANCEL_TEXT = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("取消")')   # 取消



    # 更多页面
    ROW_RECOMMEND = (AppiumBy.ID, f'{PACKAGE_ID}/row_recommend')            # 推荐给朋友ROW
    TV_RECOMMEND = (AppiumBy.ID, f'{PACKAGE_ID}/tv_recommend')              # 推荐标题
    ROW_BLACKLIST = (AppiumBy.ID, f'{PACKAGE_ID}/row_blacklist')            # 黑名单ROW
    TV_BLACKLIST = (AppiumBy.ID, f'{PACKAGE_ID}/tv_blacklist')              # 黑名单标题
    SWITCH_BLACKLIST = (AppiumBy.ID, f'{PACKAGE_ID}/switch_blacklist')      # 黑名单开关
    BLACK_CANCEL_LAYOUT_ID = f'{PACKAGE_ID}/black_cancel_layout'
    BLACK_CANCEL_LAYOUT = (AppiumBy.ID, BLACK_CANCEL_LAYOUT_ID)             # 黑名单取消布局
    BLACK_CANCEL_LAYOUT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{BLACK_CANCEL_LAYOUT_ID}"]//android.widget.TextView')    

    CARD_REPORT = (AppiumBy.ID, f'{PACKAGE_ID}/card_report')                # 举报card
    # 好友详情页解除好友关系
    UNFRIEND_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/card_unfriend")            # 解除好友关系
    UNFRIEND_TV_UNFRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_unfriend")       # 解除好友

   


    # === 设置备注与标签页面 (RemarkSetting) ===
    TV_CARD_REMARK = (AppiumBy.ID, f"{PACKAGE_ID}/card_remark")             # 设置备注与标签
    REMARK_NAME_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/item_remark_name")      # 备注名item
    ET_REMARK = (AppiumBy.ID, f"{PACKAGE_ID}/et_remark")                    # 备注名输入框
    IV_REMARK_CLEAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_remark_clear")        # 备注名清除按钮
    TV_NICKNAME_HINT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_nickname_hint")      # 昵称提示

    ITEM_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/item_phone")                  # 电话
    ROW_ADD_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/row_add_phone")            # 添加电话
    CARD_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/card_phone")                  # 电话资料卡
    IV_ADD_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/iv_add_phone")              # 添加电话图标按钮
    RV_PHONE_LIST = (AppiumBy.ID, f"{PACKAGE_ID}/rv_phone_list")            # 电话列表
    SWIPE_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/swipe_phone")                # 电话行
    IV_PHONE_LEFT = (AppiumBy.ID, f"{PACKAGE_ID}/iv_phone_left")            # 电话左侧图标
    TV_PHONE_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_phone_value")          # 电话值
    ET_PHONE_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/et_phone_value")          # 电话输入框
    BTN_DELETE_PHONE = (AppiumBy.ID, f"{PACKAGE_ID}/btn_delete_phone")      # 删除电话按钮
    
    ROOT = (AppiumBy.ID, f"{PACKAGE_ID}/root")                              # 标签根容器
    ITEM_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/item_tag")                      # 标签容器
    TV_TAG_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_tag_title")              # 标签标题
    TV_PROFILE_TAG_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_profile_tag_value")  # 标签值
    CARD_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/card_tag")                      # 标签资料卡
    TV_TAG_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_tag_value")              # 标签值
    ROW_ADD_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/row_add_tag")                # 添加标签行容器
    TV_ADD_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/tv_add_tag")                  # 添加标签文字
    FB_DONE = (AppiumBy.ID, f"{PACKAGE_ID}/fb_done")                        # 完成按钮
    ET_SEARCH = (AppiumBy.ID, f"{PACKAGE_ID}/et_search")                    # 搜索输入框
    LL_CREATE_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/ll_create_tag")            # 创建新标签容器
    TV_CREATE_TAG = (AppiumBy.ID, f"{PACKAGE_ID}/tv_create_tag")            # 创建新标签按钮
    ET_TAG_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/et_tag_name")                # 标签名称输入框
    FB_CREATE_DONE = (AppiumBy.ID, f"{PACKAGE_ID}/fb_create_done")          # 创建新标签完成按钮
    CHIP_GROUP_ID = f"{PACKAGE_ID}/chip_group"                              # 标签组容器 ID
    CHIP_GROUP = (AppiumBy.ID, CHIP_GROUP_ID)                               # 标签组容器
    # 标签组中的所有TextView(标签item)
    CHIP_GROUP_TAG_TEXTVIEWS = (AppiumBy.XPATH, f'//*[@resource-id="{CHIP_GROUP_ID}"]//android.widget.TextView')

    ITEM_MEMO = (AppiumBy.ID, f"{PACKAGE_ID}/item_memo")                    # 备忘卡片容器
    TV_MEMO_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_memo_title")            # 备忘标题
    TV_MEMO_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_memo_value")            # 备忘值
    CARD_MEMO = (AppiumBy.ID, f"{PACKAGE_ID}/card_memo")                    # 备忘卡片
    ET_MEMO = (AppiumBy.ID, f"{PACKAGE_ID}/et_memo")                        # 备忘输入框
    IV_MEMO_CLEAR = (AppiumBy.ID, f"{PACKAGE_ID}/iv_memo_clear")            # 备忘清除按钮
    TV_PROFILE_MEMO_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_profile_memo_value") # 资料页备忘值
    
    
    # 更多信息与共同群聊
    ITEM_COMMON_GROUPS = (AppiumBy.ID, f"{PACKAGE_ID}/item_common_groups")          # 共同群聊
    TV_COMMON_GROUPS_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_common_groups_title")  # 共同群聊标题
    TV_COMMON_GROUPS_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_common_groups_value")  # 共同群聊数量
    
    # 共同群聊详情页面
    TV_SEARCH_HINT = (AppiumBy.ID, f"{PACKAGE_ID}/tv_search_hint")                  # 搜索共同群聊
    TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                                # 群聊列表项

    # 共同群聊 - 通过群名称获取对应的列表项
    @classmethod
    def get_common_group_by_name(cls, group_name: str) -> Tuple[str, str]:
        """通过共同群聊名称获取对应的群聊项定位器"""
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.PACKAGE_ID}/tv_name" and @text="{group_name}"]')


    # 标签 - 通过 tag_name 获取对应的标签
    @classmethod
    def get_tag_element(cls, tag_name: str) -> Tuple[str, str]:
        """通过标签名称获取对应的标签定位器"""
        selector = f'new UiSelector().resourceId("{cls.CHIP_GROUP_ID}").childSelector(new UiSelector().text("{tag_name}"))'
        return (AppiumBy.ANDROID_UIAUTOMATOR, selector)


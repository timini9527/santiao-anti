from appium.webdriver.common.appiumby import AppiumBy

from locators.chat.core.chat_locator import ChatLocator
from locators.common.common_locator import CommonLocator


class ChatEmojiLocator(ChatLocator):
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部菜单
    EMOJI_TOP_MENU = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_container')
    EMOJI_TOP_MENU_ITEM_ID =f'{PACKAGE_ID}/emoji_tab_image'
    EMOJI_TOP_MENU_ITEM = (AppiumBy.ID, EMOJI_TOP_MENU_ITEM_ID)

    # =======================================================
    # emoji 页面元素
    # 表情包商店 0 - new UiSelector().resourceId("com.santiaotalk.im:id/emoji_tab_image").instance(0)
    # =======================================================
    EMOJI_STORE = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{EMOJI_TOP_MENU_ITEM_ID}").instance(0)')
    EMOJI_BACK = CommonLocator.TOP_IV_BACK_BTN           # 左上角返回按钮
    EMOJI_SETTING = CommonLocator.TOP_FB_ACTION_BTN      # 右上角设置
    EMOJI_STORE_NAME = CommonLocator.TOP_TV_TITLE        # 表情包商店名称
    # 热门排行
    RANK_HOT = (AppiumBy.ID, f'{PACKAGE_ID}/rank_hot')
    EMOJI_PACKAGE_ID = f'{PACKAGE_ID}/emoji_img'         # 表情包图片
    EMOJI_PACKAGE_IMG = (AppiumBy.ID, EMOJI_PACKAGE_ID)
    EMOJI_NAME_ID = f'{PACKAGE_ID}/emoji_name'           # 表情包标题名字 new UiSelector().text("蟑小螂")
    EMOJI_PACKAGE_NAME = (AppiumBy.ID, EMOJI_NAME_ID)
    EMOJI_PACKAGE_ADDED_ID = f'{PACKAGE_ID}/emoji_added' # 已添加图标
    EMOJI_PACKAGE_ADDED = (AppiumBy.ID, EMOJI_PACKAGE_ADDED_ID)
    # 精确获取已添加的图标
    EMOJI_PACKAGE_ADDED_BY_NAME = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_NAME_ID}"]/following-sibling::*[@resource-id="{EMOJI_PACKAGE_ADDED_ID}"]')
    # 精确获取不包含已添加图标的元素 
    EMOJI_PACKAGE_NOT_ADDED_NAME = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_NAME_ID}" and not(following-sibling::*[@resource-id="{EMOJI_PACKAGE_ADDED_ID}"])]')
    EMOJI_ADD_OR_DEL_ID = f'{PACKAGE_ID}/edit_to'                                   # 添加、已添加、移除按钮
    EMOJI_ADD_OR_DEL_BTN = (AppiumBy.ID, EMOJI_ADD_OR_DEL_ID)
    EMOJI_SUB_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_sub_name')                  # 表情包副标题
    EMOJI_PACKAGE_DETAIL_IMG_ID = f'{PACKAGE_ID}/emoji_detail_img'                  # 表情包详情页图片
    EMOJI_PACKAGE_DETAIL_IMG = (AppiumBy.ID, EMOJI_PACKAGE_DETAIL_IMG_ID)
    EMOJI_PACKAGE_DETAIL_NAME_ID = f'{PACKAGE_ID}/emoji_detail_name'                # 表情包详情页名字
    EMOJI_PACKAGE_DETAIL_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_detail_name')
    # 添加成功弹窗
    ADD_SUCCESS_TOAST = CommonLocator.TOAST_MSG
    # 我的表情页面
    MY_EMOJI = (AppiumBy.ID, f'{PACKAGE_ID}/my_emoji')

    # =======================================================
    # 添加的单个表情 1-收藏表情包 - new UiSelector().resourceId({PACKAGE_ID}/emoji_tab_image").instance(1)
    # =======================================================
    EMOJI_MANAGE = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{EMOJI_TOP_MENU_ITEM_ID}").instance(1)')
    # 管理表情包和添加的表情包
    COLLECT_EMOJI_ID = f'{PACKAGE_ID}/collect_image'                                    # 设置和添加的表情包
    COLLECT_EMOJI_PKG_ITEM = (AppiumBy.ID, COLLECT_EMOJI_ID)
    COLLECT_RECYCLER = (AppiumBy.ID, f'{PACKAGE_ID}/collect_recycler')                  # 收藏表情包列表框
    # 管理表情包内部
    COLLECT_LIST_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/collect_list')                # 收藏表情包列表容器
    COLLECT_BACK_BTN = CommonLocator.TOP_BACK_BTN                                       # 左上角返回按钮
    COLLECT_RIGHT_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/right_text')                       # 右上角整理和取消
    COLLECT_MOVE_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_move')                           # 移动按钮
    COLLECT_DEL_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/tv_delete')                          # 删除按钮
    COLLECT_DEL_CONFIRM_BTN = CommonLocator.DIALOG_CONFIRM_BTN                          # 二次删除确认按钮
    COLLECT_DEL_CANCEL_BTN = CommonLocator.DIALOG_CANCEL_BTN                            # 二次删除取消按钮


    # =======================================================
    # 表情 2-表情 - new UiSelector().resourceId({PACKAGE_ID}/emoji_tab_image").instance(2)
    # =======================================================
    # 表情按钮
    EMOJI_BTN_ID = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{EMOJI_TOP_MENU_ITEM_ID}").instance(2)')
    # 表情面板容器
    EMOJI_PANEL_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_view_pager')         # 表情面板容器
    # 表情整个框
    EMOJI_PANEL_OUT = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_layout')                   # 外部框
    EMOJI_PANEL_IN = (AppiumBy.ID, f'{PACKAGE_ID}/emoji_scroll')                    # 内部框
    EMOJI_ID = f'{PACKAGE_ID}/iv_emoji'                                             # 内部表情 ex:微笑
    EMOJI_ITEM = (AppiumBy.ID, EMOJI_ID)
    # 最近使用整个框
    EMOJI_RECENT_ID = f'{PACKAGE_ID}/history_emojis'
    EMOJI_RECENT = (AppiumBy.ID, f'{EMOJI_RECENT_ID}')
    # 最近使用下的所有表情
    EMOJI_RECENT_ITEM_IN = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_RECENT_ID}"]'
                                         f'//*[@resource-id="{EMOJI_ID}"]')             # 最近使用内部框
    EMOJI_RECENT_ITEM_OUT = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_RECENT_ID}"]'
                                             f'//android.widget.FrameLayout')           # 最近使用外部框
    # 所有表情整个框
    EMOJI_ALL_ID = f'{PACKAGE_ID}/all_emojis' # 内部框
    EMOJI_ALL = (AppiumBy.ID, EMOJI_ALL_ID)
    EMOJI_ALL_ITEM_OUT = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_ALL_ID}"]'
                                         f'//android.widget.FrameLayout')               # 所有表情外部框
    EMOJI_ALL_ITEM_IN = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_ALL_ID}"]//*[@resource-id="{EMOJI_ID}"]') # 所有表情内部框
    
    # =======================================================
    # 更新后UI
    # =======================================================
    EMOJI_PANEL_OUT_FRAME = (AppiumBy.XPATH, f'//*[@resource-id="{EMOJI_ALL_ID}"]/android.widget.FrameLayout') # 外部框

    EMOJI_DEL_BTN = (AppiumBy.ANDROID_UIAUTOMATOR, f'{PACKAGE_ID}/delImage')        # 删除表情按钮

    # 商店添加的表情包1 3 - new UiSelector().resourceId(f"{EMOJI_TOP_MENU_ITEM_ID}").instance(3)
    # 添加的表情包2 4 - new UiSelector().resourceId(f"{EMOJI_TOP_MENU_ITEM_ID}").instance(4)
    # 依次内推......
    EMOJI_PACKAGE_ITEM = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().resourceId("{EMOJI_TOP_MENU_ITEM_ID}")')
    # 表情包标题
    EMOJI_PACKAGE_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/downloaded_emoji_title')
    # 表情包容器
    EMOJI_PACKAGE_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/downloaded_emojis')

    # 表情包定位元素
    CHAT_EMOJI_PACKAGE = (AppiumBy.XPATH, f'(//*[@resource-id="{ChatLocator.AVATAR_ID}"]'
                                        f'/following-sibling::*[@resource-id="{ChatLocator.MESSAGE_CONTENT_ID}"]//android.widget.ImageView)')
    # 表情包定位元素最后一条
    CHAT_EMOJI_LAST_PACKAGE = (AppiumBy.XPATH, f'(//*[@resource-id="{ChatLocator.AVATAR_ID}"]'
                                        f'/following-sibling::*[@resource-id="{ChatLocator.MESSAGE_CONTENT_ID}"]//android.widget.ImageView)[last()]')

    EMOJI_PACKAGE_IMG_ID = f"//android.widget.ImageView"
    # 发送方表情包
    SENT_CHAT_EMOJI_PACKAGE = ChatLocator._BUBBLE_XPATH_TEXT("preceding-sibling", EMOJI_PACKAGE_IMG_ID)
    # 接收方表情包
    RECEIVE_CHAT_EMOJI_PACKAGE = ChatLocator._BUBBLE_XPATH_TEXT("following-sibling", EMOJI_PACKAGE_IMG_ID)


    # ---- 常量区 ----
    _FIXED_TAB_COUNT = 3  # 商店 + 收藏 + 默认表情，固定占用前3个坑位
    _SLIDE_TRIGGER_INDEX = 4  # 点击第5个图标(index=4)会触发自动左滑
    _MAX_STALE_RETRIES = 2  # 单次点击因StaleElement失败的最大重试次数








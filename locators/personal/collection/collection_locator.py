from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator
from locators.chat.core.chat_locator import ChatLocator
from locators.chat.core.chat_panel_locator import ChatPanelLocator



class CollectionLocator(CommonLocator):
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 聊天页面：收藏入口
    CHAT_COLLECTION_BUTTON = ChatPanelLocator.BTN_COLLECTION

    # 收藏入口 (通常在“我的”页面)
    MINE_COLLECTION_ENTRANCE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("收藏")')

    # 收藏列表页面元素整个容器
    COLL_RECYCLER_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/recyclerView')                # 收藏列表容器

    # 收藏 Item 容器
    COLL_CONTENT_CONTAINER_ID = f'{PACKAGE_ID}/content_container'
    COLL_CONTENT_CONTAINER = (AppiumBy.ID, COLL_CONTENT_CONTAINER_ID)               # 收藏 Item 容器
    COLL_CONTENT_TEXT_ID = f'{PACKAGE_ID}/tv_text_content'
    COLL_CONTENT_TEXT = (AppiumBy.ID, COLL_CONTENT_TEXT_ID)                         # 收藏文本
    COLL_CONTENT_IMAGE_ID = f'{PACKAGE_ID}/tv_image_content'
    COLL_CONTENT_IMAGE = (AppiumBy.ID, COLL_CONTENT_IMAGE_ID)                       # 收藏图片
    COLL_META = (AppiumBy.ID, f'{PACKAGE_ID}/tv_meta')                              # 收藏的用户昵称
    COLL_TIME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_time')                              # 收藏时间
    
    
    # 发送板块
    CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/content')
    CONTENT_AVATAR = ChatLocator.AVATAR_ITEM                                        # 头像
    CONTENT_NICKNAME_ID = f'{PACKAGE_ID}/tv_nickname'                               # 昵称
    CONTENT_NICKNAME = (AppiumBy.ID, CONTENT_NICKNAME_ID)
    CONTENT_NICKNAME_ITEM = (AppiumBy.ID, f'//*[@resource-id="{CONTENT_NICKNAME_ID}"]/android.widget.TextView')  
    CONTENT_TEXT_BUBBLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_msg_bubble')              # 文本内容气泡
    CONTENT_IMAGE_BUBBLE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_msg_bubble')             # 图片内容
    CONTENT_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_input')                         # 输入框
    CONTENT_EMOJI = (AppiumBy.ID, f'{PACKAGE_ID}/input_expression_bnt')             # 表情按钮
    CONTENT_SEND = (AppiumBy.ID, f'{PACKAGE_ID}/send_bnt')                          # 发送按钮

    # 右滑/左滑菜单项
    SWIPE_RIGHT = f'{PACKAGE_ID}/swipe_right'
    # 分享
    SWIPE_RIGHT_SHARE_ITEM = (AppiumBy.XPATH, f'(//*[@resource-id="{SWIPE_RIGHT}"]//android.widget.ImageView)[1]')               
    # 删除
    SWIPE_RIGHT_DELETE_ITEM = (AppiumBy.XPATH, f'(//*[@resource-id="{SWIPE_RIGHT}"]//android.widget.ImageView)[2]')               

    # 空状态页面
    EMPTY_LAYOUT = (AppiumBy.ID, f'{PACKAGE_ID}/layout_empty')
    # 空状态页面文字
    EMPTY_LAYOUT_TEXT = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/layout_empty"]//android.widget.TextView')




    # 通过text/image元素，相对向上定位其所在的卡片容器
    @staticmethod
    def get_coll_item_by_type(col_type: str = 'text'):
        content_id = (
            CollectionLocator.COLL_CONTENT_TEXT_ID 
            if col_type == 'text' 
            else CollectionLocator.COLL_CONTENT_IMAGE_ID
        )
        return (
            AppiumBy.XPATH, 
            f'//*[@resource-id="{content_id}"]/ancestor::*[@resource-id="{CollectionLocator.COLL_CONTENT_CONTAINER_ID}"]'
        )

    # 当前元素的直接父节点
    COLL_ITEM_PARENT = (AppiumBy.XPATH, "./..")

    @staticmethod
    def get_coll_item_parent_by_type(col_type: str = "text", index: int = 0):
        content_id_map = {
            "text": CollectionLocator.COLL_CONTENT_TEXT_ID,
            "image": CollectionLocator.COLL_CONTENT_IMAGE_ID,
        }

        content_id = content_id_map.get(col_type)
        if not content_id:
            raise ValueError(f"不支持的收藏类型: {col_type}")

        return (
            AppiumBy.XPATH,
            f'(//*[@resource-id="{content_id}"]/parent::*)[{index + 1}]'
        )

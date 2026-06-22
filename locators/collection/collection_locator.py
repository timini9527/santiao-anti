from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator
from locators.chat.chat_locator import ChatLocator

class CollectionLocator(CommonLocator):
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 聊天页面：收藏入口
    CHAT_COLLECTION_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/collect_btn')

    # 收藏入口 (通常在“我的”页面)
    MINE_COLLECTION_ENTRANCE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("收藏")')

    # 收藏列表页面元素整个容器
    COLL_RECYCLER_VIEW = (AppiumBy.ID, f'{PACKAGE_ID}/recyclerView')                # 收藏列表容器

    # 收藏 Item 容器
    COLL_CONTENT_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/content_container')       # 收藏 Item 容器
    COLL_CONTENT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_text_content')              # 收藏文本
    COLL_CONTENT_IMAGE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_image_content')            # 收藏图片
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




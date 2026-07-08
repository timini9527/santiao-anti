from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class MomentsLocator:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 朋友圈入口 (通常在“发现”或“消息”页，假设从主页某个入口进入)
    # 这里假设已经进入了朋友圈页面 动态
    
    # 朋友圈主页元素
    POST_MOMENTS_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_post_moments') # 发布朋友圈按钮 (相机图标)
    MOMENTS_LIST = (AppiumBy.ID, f'{PACKAGE_ID}/moments_list') # 朋友圈列表
    
    # 发布页面元素
    EDIT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/et_moments_content') # 文字输入框
    ADD_IMAGE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_add_image') # 添加图片按钮
    PUBLISH_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/tv_publish') # 发表按钮
    
    # 互动元素 (针对列表中的某一项)
    LIKE_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_like') # 点赞按钮
    COMMENT_BUTTON = (AppiumBy.ID, f'{PACKAGE_ID}/iv_comment') # 评论按钮
    COMMENT_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/et_comment') # 评论输入框
    COMMENT_SEND = (AppiumBy.ID, f'{PACKAGE_ID}/btn_send_comment') # 评论发送按钮

    # 列表项中的内容
    MOMENT_CONTENT_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_content') # 动态正文内容

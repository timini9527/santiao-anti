from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator
from locators.chat.chat_options.media_select_locator import MediaSelectLocator
from locators.chat.core.chat_locator import ChatLocator


class ChatImageLocator(MediaSelectLocator):
    """聊天功能 - 底部加号面板 - 相册内部相关的元素定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 注：所有基础的相册网格定位已继承自 MediaSelectLocator


    # 定向勾选（XPath 过滤，不含视频/长图/webp/gif 等媒体）
    # 仅纯图片元素
    PHOTO_ONLY_IMAGE_ITEM = (AppiumBy.XPATH, f'//*[./*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]'
                                            f'and not(./*[@resource-id="{MediaSelectLocator.PHOTO_VIDEO_DURATTON_VIEW_ID}"])'
                                            f'and not(./*[@resource-id="{MediaSelectLocator.PHOTO_LONG_IMAGE_VIEW_ID}"])]'
                                            f'/*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]')
    # 仅纯图片勾选按钮
    PHOTO_CHECK_BUTTON_NOT_MEDIA = (AppiumBy.XPATH, f'//*[./*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]'
                                                    f' and not(./*[@resource-id="{MediaSelectLocator.PHOTO_VIDEO_DURATTON_VIEW_ID}"])'
                                                    f' and not(./*[@resource-id="{MediaSelectLocator.PHOTO_LONG_IMAGE_VIEW_ID}"])]'
                                                    f'/*[@resource-id="{MediaSelectLocator.PHOTO_CHECK_BUTTON_ID}"]')

    # 仅不包含视频元素
    PHOTO_NOT_VIDEO_ITEM = (AppiumBy.XPATH, f'//*[./*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]'
                                            f'and not(./*[@resource-id="{MediaSelectLocator.PHOTO_VIDEO_DURATTON_VIEW_ID}"])]'
                                            f'/*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]')
    # 仅不包含视频的勾选按钮
    PHOTO_CHECK_BUTTON_NOT_VIDEO = (AppiumBy.XPATH, f'//*[./*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]'
                                                    f' and not(./*[@resource-id="{MediaSelectLocator.PHOTO_VIDEO_DURATTON_VIEW_ID}"])]'
                                                    f'/*[@resource-id="{MediaSelectLocator.PHOTO_CHECK_BUTTON_ID}"]')

    # 仅视频元素
    PHOTO_VIDEO_ITEM = (AppiumBy.XPATH,     f'//*[@resource-id="{MediaSelectLocator.PHOTO_VIDEO_DURATTON_VIEW_ID}"]'
                                        f'/preceding-sibling::*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]')
    # 仅视频勾选按钮
    PHOTO_CHECK_BUTTON_VIDEO      = (AppiumBy.XPATH, f'//*[@resource-id="{MediaSelectLocator.PHOTO_VIDEO_DURATTON_VIEW_ID}"]'
                                                     f'/preceding-sibling::*[@resource-id="{MediaSelectLocator.PHOTO_CHECK_BUTTON_ID}"]')
    
    # 仅长图、webp图片、gif图片元素
    PHOTO_IMAGE_LONG_WEBP_GIF_ITEM = (AppiumBy.XPATH, f'//*[@resource-id="{MediaSelectLocator.PHOTO_LONG_IMAGE_VIEW_ID}"]'
                                            f'/preceding-sibling::*[@resource-id="{MediaSelectLocator.PHOTO_ITEM_ID}"]')
    # 仅长图、webp图片、gif图片勾选按钮
    PHOTO_CHECK_BUTTON_IMAGE_LONG_WEBP_GIF = (AppiumBy.XPATH, f'//*[@resource-id="{MediaSelectLocator.PHOTO_LONG_IMAGE_VIEW_ID}"]'
                                                     f'/preceding-sibling::*[@resource-id="{MediaSelectLocator.PHOTO_CHECK_BUTTON_ID}"]')


    # 完成兼容性别名转换，不新增新的元素定位
    PHOTO_CHECK_BUTTON_LONG_WEBP_GIF = PHOTO_CHECK_BUTTON_IMAGE_LONG_WEBP_GIF
    PHOTO_ONLY_VIDEO_ITEM = PHOTO_VIDEO_ITEM


    # ==================== 聊天页面中的图片气泡 ====================
    IMAGE_ID = ChatLocator.IMAGE_ID
    IMAGE_ITEM = ChatLocator.IMAGE_ITEM
    SEND_IMAGE_ITEM = ChatLocator.SEND_IMAGE_ITEM
    RECEIV_IMAGE_ITEM = ChatLocator.RECEIV_IMAGE_ITEM











from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator

class GroupQrCodeLocator:
    """群二维码页面定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 页面基础元素
    TITLE = CommonLocator.TOP_TV_TITLE                                              # 页面标题
    BACK_BTN = CommonLocator.TOP_IV_BACK_BTN                                        # 返回按钮

    QR_CARD_LAYOUT = (AppiumBy.ID, f"{PACKAGE_ID}/qr_card_layout")                  # 二维码卡片布局
    GROUP_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/group_header")                      # 群聊头像
    GROUP_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/group_name")                          # 群聊名称
    GROUP_CODE = (AppiumBy.ID, f"{PACKAGE_ID}/group_code")                          # 群聊二维码
    SYSTEM_INFO = (AppiumBy.ID, f"{PACKAGE_ID}/system_info")                        # 系统信息
    QR_TIME_TIPS = (AppiumBy.ID, f"{PACKAGE_ID}/qr_time_tips")                      # 二维码有效时间

    LAYOUT_SELECT_TIME = (AppiumBy.ID, f"{PACKAGE_ID}/layout_select_time")          # 修改有效期布局

    CARD_DOWN = (AppiumBy.ID, f"{PACKAGE_ID}/card_down")                            # 二维码卡片下载
    CARD_SHARE = (AppiumBy.ID, f"{PACKAGE_ID}/card_share")                          # 二维码卡片分享

    # 操作按钮
    SAVE_QRCODE_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/group_download_code")            # 保存群二维码到本地
    SHARE_QRCODE_BTN = (AppiumBy.ID, f"{PACKAGE_ID}/tv_share")                      # 分享群二维码

    # 修改有效期相关
    TV_SURE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_sure")                                # 修改有效期弹窗确定按钮
    RECYCLER_VIEW = (AppiumBy.ID, f"{PACKAGE_ID}/recycler_view")                    # 有效期选项列表
    TV_CONTENT_ID = f"{PACKAGE_ID}/tv_content"
    TV_CONTENT = (AppiumBy.ID, TV_CONTENT_ID)                                       # 有效期内容

    @classmethod
    def validity_option_by_text(cls, value: str):
        """根据有效期的值定位"""
        mapping = {
            "30m": "30分钟",
            "2h": "2小时",
            "24h": "24小时",
            "7d": "7天内",
            "30d": "30天内",
            "90d": "90天内",
            "forever": "永久有效",
        }
        str_value = mapping.get(value)
        if str_value is None:
            raise ValueError(f"不支持的有效期: {value}")
        return (AppiumBy.XPATH, f"//android.widget.TextView[@resource-id='{cls.TV_CONTENT_ID}' and @text='{str_value}']")
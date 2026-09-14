from common.base_page import BasePage
from core.logger_utils import logger
from locators.groups.setting.qrcode.group_qrcode_locator import GroupQrCodeLocator

class GroupQrCodePage(BasePage):
    """群二维码子页面操作类"""

    # 等待群二维码页面加载
    def wait_for_qrcode_page_load(self, timeout: int = 10) -> bool:
        """等待群二维码页面加载"""
        logger.info(f"⏳ [Action] GroupQrCodePage - 等待群二维码页面加载 (超时: {timeout}s)")
        res = self.wait_for_element_text(GroupQrCodeLocator.TITLE, expected_text="群二维码", timeout=timeout)
        logger.info(f"⏳ [Action] GroupQrCodePage - 页面加载{'成功' if res else '超时'}")
        return res

    # 二维码卡片布局是否可见
    def is_qr_card_layout_visible(self) -> bool:
        """二维码卡片布局是否可见"""
        logger.info("👁️ [Action] GroupQrCodePage - 检查二维码卡片布局是否可见")
        res = self.is_element_exist(GroupQrCodeLocator.QR_CARD_LAYOUT)
        return res

    # 群头像是否可见
    def is_group_header_visible(self) -> bool:
        """群头像是否可见"""
        logger.info("👁️ [Action] GroupQrCodePage - 检查群头像是否可见")
        res = self.is_element_exist(GroupQrCodeLocator.GROUP_HEADER)
        return res

    # 获取二维码界面上显示的群名称
    def get_group_name(self) -> str:
        """获取二维码界面上显示的群名称"""
        logger.info("📖 [Action] GroupQrCodePage - 获取群名称")
        res = self.get_attribute(GroupQrCodeLocator.GROUP_NAME, "text")
        return res or ""

    # 群二维码是否可见
    def is_group_code_visible(self) -> bool:
        """群二维码是否可见"""
        logger.info("👁️ [Action] GroupQrCodePage - 检查群二维码是否可见")
        res = self.is_element_exist(GroupQrCodeLocator.GROUP_CODE)
        return res

    # 获取系统信息文案
    def get_system_info(self) -> str:
        """获取系统信息文案"""
        logger.info("📖 [Action] GroupQrCodePage - 获取系统信息")
        res = self.get_attribute(GroupQrCodeLocator.SYSTEM_INFO, "text")
        return res or ""

    # 获取当前展示的群二维码有效期截止文案
    def get_validity_text(self) -> str:
        """获取当前展示的群二维码有效期截止文案"""
        logger.info("📖 [Action] GroupQrCodePage - 获取有效期文字")
        res = self.get_attribute(GroupQrCodeLocator.QR_TIME_TIPS, "text")
        return res or ""

    # 点击修改有效日期入口
    def click_change_date_row(self) -> None:
        """点击修改有效日期入口"""
        logger.info("📅 [Action] GroupQrCodePage - 点击【修改二维码有效期】")
        self.click(GroupQrCodeLocator.LAYOUT_SELECT_TIME)

    # 点击卡片下载
    def click_card_download(self) -> None:
        """点击卡片下载（CARD_DOWN）"""
        logger.info("💾 [Action] GroupQrCodePage - 点击【卡片下载】")
        self.click(GroupQrCodeLocator.CARD_DOWN)

    # 点击卡片分享
    def click_card_share(self) -> None:
        """点击卡片分享（CARD_SHARE）"""
        logger.info("📤 [Action] GroupQrCodePage - 点击【卡片分享】")
        self.click(GroupQrCodeLocator.CARD_SHARE)

    # 点击保存群二维码按钮
    def click_save_qrcode(self) -> None:
        """点击保存群二维码按钮"""
        logger.info("💾 [Action] GroupQrCodePage - 点击【保存群二维码】")
        self.click(GroupQrCodeLocator.SAVE_QRCODE_BTN)

    # 点击分享群二维码按钮
    def click_share_qrcode(self) -> None:
        """点击分享群二维码按钮"""
        logger.info("📤 [Action] GroupQrCodePage - 点击【分享群二维码】")
        self.click(GroupQrCodeLocator.SHARE_QRCODE_BTN)

    # 有效期选项列表弹窗是否可见
    def is_validity_options_dialog_visible(self) -> bool:
        """有效期选项列表弹窗是否可见"""
        logger.info("👁️ [Action] GroupQrCodePage - 检查有效期选项列表是否可见")
        res = self.is_element_exist(GroupQrCodeLocator.RECYCLER_VIEW)
        return res

    # 选择二维码有效期
    def select_validity_option(self, option: str) -> None:
        """选择二维码有效期。支持的值: '30m', '2h', '24h', '7d', '30d', '90d', 'forever'"""
        logger.info(f"📆 [Action] GroupQrCodePage - 选择二维码有效期选项: {option}")
        option_locator = GroupQrCodeLocator.validity_option_by_text(option)
        self.click(option_locator)
        self.click(GroupQrCodeLocator.TV_SURE)

    # 点击返回按钮
    def click_back_button(self) -> None:
        """点击返回按钮"""
        logger.info("🔙 [Action] GroupQrCodePage - 点击返回")
        self.click(GroupQrCodeLocator.BACK_BTN)

    # 获取图片中的数据
    def get_image_data(self) -> list[str]:
        """获取二维码图片中的文本数据"""
        logger.info("📖 [Action] GroupQrCodePage - 获取图片中的数据")
        from utils.cv_recognition.ocr_utils import OcrUtils
        ocr_util = OcrUtils(self.driver)
        img_data = ocr_util.get_all_text(image_name="group_qrcode.png")
        logger.info(f"📖 [Action] GroupQrCodePage - 获取图片中的数据结果: '{img_data}'")
        return img_data

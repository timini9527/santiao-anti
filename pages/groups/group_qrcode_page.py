from common.base_page import BasePage
from core.logger_utils import logger
from locators.groups.group_qrcode_locator import GroupQrCodeLocator

class GroupQrCodePage(BasePage):
    """群二维码子页面操作类"""

    def wait_for_qrcode_page_load(self, timeout=10) -> bool:
        """等待群二维码页面加载"""
        res = self.get_attribute(GroupQrCodeLocator.TITLE, "text") == "群二维码"
        logger.info(f"⏳ [Action] GroupQrCodePage - 页面加载{'成功' if res else '超时'}")
        return res

    def is_qr_card_layout_visible(self) -> bool:
        """二维码卡片布局是否可见"""
        res = self.is_element_exist(GroupQrCodeLocator.QR_CARD_LAYOUT)
        logger.info(f"👁️ [Action] GroupQrCodePage - 二维码卡片布局是否可见: {res}")
        return res

    def is_group_header_visible(self) -> bool:
        """群头像是否可见"""
        res = self.is_element_exist(GroupQrCodeLocator.GROUP_HEADER)
        logger.info(f"👁️ [Action] GroupQrCodePage - 群头像是否可见: {res}")
        return res

    def get_group_name(self) -> str:
        """获取二维码界面上显示的群名称"""
        res = self.get_attribute(GroupQrCodeLocator.GROUP_NAME, "text")
        logger.info(f"📖 [Action] GroupQrCodePage - 获取群名称: '{res}'")
        return res

    def is_group_code_visible(self) -> bool:
        """群二维码是否可见"""
        res = self.is_element_exist(GroupQrCodeLocator.GROUP_CODE)
        logger.info(f"👁️ [Action] GroupQrCodePage - 群二维码是否可见: {res}")
        return res

    def get_system_info(self) -> str:
        """获取系统信息文案"""
        res = self.get_attribute(GroupQrCodeLocator.SYSTEM_INFO, "text")
        logger.info(f"📖 [Action] GroupQrCodePage - 获取系统信息: '{res}'")
        return res

    def get_validity_text(self) -> str:
        """获取当前展示的群二维码有效期截止文案"""
        res = self.get_attribute(GroupQrCodeLocator.QR_TIME_TIPS, "text")
        logger.info(f"📖 [Action] GroupQrCodePage - 获取有效期文字: '{res}'")
        return res

    def click_change_date_row(self):
        """点击修改有效日期入口"""
        self.click(GroupQrCodeLocator.LAYOUT_SELECT_TIME)
        logger.info("📅 [Action] GroupQrCodePage - 点击【修改二维码有效期】")

    def click_card_download(self):
        """点击卡片下载（CARD_DOWN）"""
        self.click(GroupQrCodeLocator.CARD_DOWN)
        logger.info("💾 [Action] GroupQrCodePage - 点击【卡片下载】")

    def click_card_share(self):
        """点击卡片分享（CARD_SHARE）"""
        self.click(GroupQrCodeLocator.CARD_SHARE)
        logger.info("📤 [Action] GroupQrCodePage - 点击【卡片分享】")

    def click_save_qrcode(self):
        """点击保存群二维码按钮"""
        self.click(GroupQrCodeLocator.SAVE_QRCODE_BTN)
        logger.info("💾 [Action] GroupQrCodePage - 点击【保存群二维码】")

    def click_share_qrcode(self):
        """点击分享群二维码按钮"""
        self.click(GroupQrCodeLocator.SHARE_QRCODE_BTN)
        logger.info("📤 [Action] GroupQrCodePage - 点击【分享群二维码】")

    def is_validity_options_dialog_visible(self) -> bool:
        """有效期选项列表弹窗是否可见"""
        res = self.is_element_exist(GroupQrCodeLocator.RECYCLER_VIEW)
        logger.info(f"👁️ [Action] GroupQrCodePage - 有效期选项列表是否可见: {res}")
        return res

    def select_validity_option(self, option: str):
        """选择二维码有效期。支持的值: '30m', '2h', '24h', '7d', '30d', '90d', 'forever'"""
        option_locator = GroupQrCodeLocator.validity_option_by_text(option)
        self.click(option_locator)
        self.click(GroupQrCodeLocator.TV_SURE)
        logger.info(f"📆 [Action] GroupQrCodePage - 选择二维码有效期选项: {option}")

    def click_back_button(self):
        """点击返回按钮"""
        self.click(GroupQrCodeLocator.BACK_BTN)
        logger.info("🔙 [Action] GroupQrCodePage - 点击返回")

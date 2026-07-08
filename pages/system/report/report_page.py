from common.base_page import BasePage
from locators.system.report.report_locator import ReportLocator
from core.logger_utils import logger
import time

class ReportPage(BasePage):

    # 等待投诉首屏加载完成
    def wait_for_report_page_load(self, timeout: int = 3) -> bool:
        """等待投诉首屏加载完成"""
        logger.info("⏱️ [Action-Report] 等待投诉首屏加载完成")
        sta = self.get_attribute(locator=ReportLocator.TOP_TV_TITLE, attr="text", timeout=timeout) == "投诉"
        if sta:
            logger.info("✅ [Action-Report] 投诉首屏加载完成")
            return True
        logger.warning("❌ [Action-Report] 投诉首屏加载失败")
        return False

    # 校验指定的投诉分类项文本是否展示
    def is_category_visible(self, category: str, timeout: int = 3) -> bool:
        """校验指定的投诉分类项文本是否展示"""
        logger.info(f"🔍 [Action-Report] 检查分类项是否存在: {category}")
        locator = ReportLocator.get_option_by_text(category)
        element = self.find_element(locator, timeout=timeout)
        if element:
            logger.info(f"✅ [Action-Report] 分类项存在: {category}")
            return True
        logger.warning(f"❌ [Action-Report] 未找到分类项: {category}")
        return False

    # 根据传入的类别层级，依次点击进入子选项
    def select_report_path(self, category_path: list[str]):
        """
        根据传入的类别层级，依次点击进入子选项
        例如: ["色情", "色情低俗"]
        """
        for category in category_path:
            logger.info(f"👉 [Action-Report] 正在点击投诉选项: {category}")
            locator = ReportLocator.get_option_by_text(category)
            self.click(locator)
            if self.find_elements(locator, timeout=2, raise_exception=False):
                logger.info(f"👉 [Action-Report] 第一次点击失效, 正在点击投诉选项: {category} 第二次")
                self.click(locator)

    # 点击返回按钮
    def click_back(self):
        """点击返回按钮"""
        logger.info("↩️ [Action-Report] 点击投诉页返回按钮")
        self.click(ReportLocator.TOP_IV_BACK_BTN)

    # 输入金额
    def input_amount(self, amount: str = "13800138000"):
        """输入金额（如果存在金额输入框）"""
        edit_texts = self.find_elements(ReportLocator.INPUT_EDIT_TEXT, timeout=2, raise_exception=False)
        if len(edit_texts) > 1:
            for edit in edit_texts[:-1]:
                logger.info(f"✍️ [Action-Report] 发现输入框，输入金额: {amount}")
                edit.clear()
                edit.send_keys(amount)
        else:
            logger.info("ℹ️ [Action-Report] 当前页面未发现金额输入框，跳过金额输入")
        
    # 上传图片
    def click_upload_image(self):
        """点击上传图片"""
        logger.info(f"📎 [Action-Report] 点击上传图片")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE)
        time.sleep(0.5)

    # 点击从相册选择
    def click_album(self):
        """点击从相册选择"""
        logger.info(f"📎 [Action-Report] 点击从相册选择")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE_FROM_ALBUM)
    
    # 拍照
    def click_take_photo(self):
        """点击拍照"""
        logger.info(f"📸 [Action-Report] 点击拍照")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE_TAKE_PHOTO)    
    
    # 取消上传图片
    def click_cancel_upload(self):
        """点击取消上传图片"""
        logger.info(f"❌ [Action-Report] 点击取消上传图片")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE_CANCEL)    
    
    # 选择一张照片上传
    def click_upload_image_from_album(self):
        """点击选择一张照片上传"""
        from pages.chat_options.images.chat_image_page import ChatImagePage
        imagePage = ChatImagePage(self.driver)
        imagePage.wait_for_image_page_load()
        imagePage.select_single_image()
        imagePage.click_send_image()
        
    
    # 输入问题描述
    def input_question_description(self, desc: str = "012345678909876543210"):
        """输入问题描述"""
        edit_texts = self.find_elements(ReportLocator.INPUT_EDIT_TEXT, timeout=2)
        if len(edit_texts) >= 2:
            logger.info(f"✍️ [Action-Report] 检测到两个输入框，向第二个输入问题描述: {desc}")
            edit_texts[-1].clear()
            edit_texts[-1].send_keys(desc)
        elif len(edit_texts) == 1:
            logger.info(f"✍️ [Action-Report] 检测到一个输入框，输入问题描述: {desc}")
            edit_texts[0].clear()
            edit_texts[0].send_keys(desc)
        else:
            logger.warning("❌ [Action-Report] 页面上未找到任何输入框")
    
    # 提交投诉
    def submit_report(self) -> str:
        """
        提交投诉并捕获 Toast 成功提示
        :return: 捕获到的 Toast 文本
        """
        logger.info("📤 [Action-Report] 点击提交投诉按钮")
        self.click(ReportLocator.REPORT_SUBMIT_BTN)
        toast_msg = self.get_toast()
        logger.info(f"🎉 [Action-Report] 捕获到提交反馈 Toast: {toast_msg}")
        return toast_msg

    # =======================
    # 提交投诉整个流程
    # =======================
    def submit_report_complete_flow(self):
        """
        提交投诉整个流程
        :return: 
        """
        self.input_amount()
        self.click_upload_image()
        self.click_album()
        self.click_upload_image_from_album()
        self.input_question_description()
    
        
    




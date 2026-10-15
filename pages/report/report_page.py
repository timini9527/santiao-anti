import time
from common.base_page import BasePage
from locators.report.report_locator import ReportLocator
from core.logger_utils import logger, LogIcon


class ReportPage(BasePage):
    """投诉/举报页面对象"""

    # 投诉页 - 等待投诉首屏加载完成
    def wait_for_report_page_load(self, timeout: int = 3) -> bool:
        """ 等待投诉首屏加载完成 """
        logger.info(f"{LogIcon.WAIT} 等待投诉首屏加载完成")
        try:
            sta = self.is_element_exist(ReportLocator.TV_REPORT_XPATH, timeout=timeout)
            if sta:
                logger.info(f"{LogIcon.SUCCESS} 投诉首屏加载完成")
                return True
        except Exception:
            pass
        logger.warning(f"{LogIcon.FAIL} 投诉首屏加载失败")
        return False

    # 投诉页 - 校验指定的投诉分类项文本是否展示
    def is_category_visible(self, category: str, timeout: int = 3) -> bool:
        """ 校验指定的投诉分类项文本是否展示 """
        logger.info(f"{LogIcon.FIND} 检查分类项是否存在: {category}")
        locator = ReportLocator.get_option_by_text(category)
        element = self.find_element(locator, timeout=timeout)
        if element:
            logger.info(f"{LogIcon.SUCCESS} 分类项存在: {category}")
            return True
        logger.warning(f"{LogIcon.FAIL} 未找到分类项: {category}")
        return False

    # 投诉页 - 根据传入的类别层级，依次点击进入子选项
    def select_report_path(self, category_path: list[str]) -> None:
        """
        根据传入的类别层级，依次点击进入子选项
        例如: ["色情", "色情低俗"]
        """
        logger.info(f"{LogIcon.ACTION} 准备选择投诉路径: {category_path}")
        for category in category_path:
            logger.info(f"{LogIcon.ACTION} 正在点击投诉选项: {category}")
            locator = ReportLocator.get_option_by_text(category)
            self.click(locator)
            if self.find_elements(locator, timeout=2, raise_exception=False):
                logger.info(f"{LogIcon.ACTION} 第一次点击失效, 正在点击投诉选项: {category} 第二次")
                self.click(locator)

    # 投诉页 - 点击返回按钮
    def click_back(self) -> None:
        """ 点击返回按钮 """
        logger.info(f"{LogIcon.ACTION} ↩️ [Action-Report] 点击投诉页返回按钮")
        self.click(ReportLocator.TOP_IV_BACK_BTN)

    # 投诉页 - 输入金额
    def input_amount(self, amount: str = "13800138000") -> None:
        """ 输入金额（如果存在金额输入框） """
        logger.info(f"{LogIcon.SETUP} 准备输入金额: {amount}")
        edit_texts = self.find_elements(ReportLocator.INPUT_EDIT_TEXT, timeout=2, raise_exception=False)
        if len(edit_texts) > 1:
            for edit in edit_texts[:-1]:
                logger.info(f"{LogIcon.ACTION} 发现输入框，输入金额: {amount}")
                edit.clear()
                edit.send_keys(amount)
        else:
            logger.info(f"{LogIcon.STEP} ℹ️ [Action-Report] 当前页面未发现金额输入框，跳过金额输入")
        
    # 投诉页 - 上传图片
    def click_upload_image(self) -> None:
        """ 点击上传图片 """
        logger.info(f"{LogIcon.ACTION} 📎 [Action-Report] 点击上传图片")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE)
        time.sleep(0.5)

    # 投诉页 - 点击从相册选择
    def click_album(self) -> None:
        """ 点击从相册选择 """
        logger.info(f"{LogIcon.ACTION} 📎 [Action-Report] 点击从相册选择")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE_FROM_ALBUM)
    
    # 投诉页 - 拍照
    def click_take_photo(self) -> None:
        """ 点击拍照 """
        logger.info(f"{LogIcon.CAMERA} 点击拍照")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE_TAKE_PHOTO)    
    
    # 投诉页 - 取消上传图片
    def click_cancel_upload(self) -> None:
        """ 点击取消上传图片 """
        logger.info(f"{LogIcon.FAIL} 点击取消上传图片")
        self.click(ReportLocator.REPORT_UPLOAD_IMAGE_CANCEL)    
    
    # 投诉页 - 选择一张照片上传
    def click_upload_image_from_album(self) -> None:
        """ 点击选择一张照片上传 """
        logger.info(f"{LogIcon.SETUP} 准备从相册选择一张照片上传")
        from pages.chat_options.images.chat_image_page import ChatImagePage
        imagePage = ChatImagePage(self.driver)
        imagePage.wait_for_image_page_load()
        imagePage.select_single_image()
        imagePage.click_send_image()
        
    # 投诉页 - 输入问题描述
    def input_question_description(self, desc: str = "012345678909876543210") -> None:
        """ 输入问题描述 """
        logger.info(f"{LogIcon.SETUP} 准备输入问题描述: {desc}")
        edit_texts = self.find_elements(ReportLocator.INPUT_EDIT_TEXT, timeout=2)
        if len(edit_texts) >= 2:
            logger.info(f"{LogIcon.ACTION} 检测到两个输入框，向第二个输入问题描述: {desc}")
            edit_texts[-1].clear()
            edit_texts[-1].send_keys(desc)
        elif len(edit_texts) == 1:
            logger.info(f"{LogIcon.ACTION} 检测到一个输入框，输入问题描述: {desc}")
            edit_texts[0].clear()
            edit_texts[0].send_keys(desc)
        else:
            logger.warning(f"{LogIcon.FAIL} 页面上未找到任何输入框")
    
    # 投诉页 - 提交投诉
    def submit_report(self) -> str:
        """
        提交投诉并捕获 Toast 成功提示
        :return: 捕获到的 Toast 文本
        """
        logger.info(f"{LogIcon.ACTION} 📤 [Action-Report] 点击提交投诉按钮")
        self.click(ReportLocator.REPORT_SUBMIT_BTN)
        toast_msg = self.get_toast()
        logger.info(f"{LogIcon.SUCCESS} 捕获到提交反馈 Toast: {toast_msg}")
        return toast_msg

    # 投诉页 - 提交投诉整个流程
    def submit_report_complete_flow(self) -> None:
        """ 提交投诉整个流程 """
        logger.info(f"{LogIcon.SETUP} 开始执行提交投诉全流程")
        self.input_amount()
        self.click_upload_image()
        self.click_album()
        self.click_upload_image_from_album()
        self.input_question_description()

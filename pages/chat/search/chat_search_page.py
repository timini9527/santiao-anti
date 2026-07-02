import time
from common.base_page import BasePage
from locators.chat.search.chat_search_locator import ChatSearchLocator
from core.logger_utils import logger
from appium.webdriver.webelement import WebElement
from utils.cv_recognition.screenshot_utils import ScreenshotUtils


class ChatSearchPage(BasePage):
    """聊天记录搜索页面 Object"""

    # 等待搜索框出现，不抛异常，返回boolean值
    def wait_for_search_page_load(self, timeout: int = 10) -> bool:
        """等待搜索页面加载完成"""
        search_sta = self.is_element_exist(ChatSearchLocator.SEARCH_INPUT, timeout=timeout)
        if search_sta:
            logger.info("⏱️ [Action-Search] 等待搜索输入框出现")
        else:
            logger.error("❌ [Action-Search] 搜索页面未加载")
        return search_sta

    # 输入搜索关键字
    def input_search_keyword(self, keyword: str):
        """输入搜索关键字"""
        self.send_keys(ChatSearchLocator.SEARCH_INPUT, keyword)
        time.sleep(1.0)  # 等待本地搜索过滤完成
        logger.info(f"✍️ [Action-Search] 输入搜索关键字: {keyword}")

    # 获取搜索结果列表数量
    def get_search_results_count(self) -> int:
        """获取搜索结果列表项的数量"""
        logger.info("🔍 [Action-Search] 统计搜索匹配结果数量")
        results = self.find_elements(ChatSearchLocator.TV_CONTENT, timeout=3)
        if not results:
            logger.warning("⚠️ [Action-Search] 未找到任何搜索结果列表项")
            return 0
        logger.info(f"✅ [Action-Search] 找到 {len(results)} 条搜索结果")
        return len(results)

    # 点击搜索结果项
    def click_search_result_item(self, index: int = 0):
        """点击指定索引的搜索结果项，跳转回聊天页面"""
        logger.info(f"🖱️ [Action-Search] 点击第 {index + 1} 条搜索结果项以定位消息")
        results = self.find_elements(ChatSearchLocator.TV_CONTENT, timeout=3)
        if len(results) > index:
            results[index].click()
            time.sleep(1.0)
        else:
            raise IndexError(f"❌ 搜索结果索引 {index} 超出范围")

    # 点击日期选项
    def click_date_option(self):
        """点击‘日期’快速分类搜索"""
        logger.info("🖱️ [Action-Search] 点击‘日期’筛选分类")
        self.click(ChatSearchLocator.OPTION_DATE)


    # 点击图片选项
    def click_image_option(self):
        """点击‘图片’快速分类搜索"""
        logger.info("🖱️ [Action-Search] 点击‘图片’筛选分类")
        self.click(ChatSearchLocator.OPTION_IMAGE)

    # 点击视频选项
    def click_video_option(self):
        """点击‘视频’快速分类搜索"""
        logger.info("🖱️ [Action-Search] 点击‘视频’筛选分类")
        self.click(ChatSearchLocator.OPTION_VIDEO)
    
    # 等待聊天记录中媒体分类页面加载
    def wait_for_media_page_load(self, timeout: int = 10) -> bool:
        """等待聊天记录中媒体分类页面完全加载完成"""
        logger.info("⏳ [Action-Search] 等待媒体分类页面加载")
        try:
            elems = self.find_elements(ChatSearchLocator.PICTURE_RV, timeout=timeout, )
            if not elems:
                logger.error("❌ [Action-Search] 未找到媒体分类页面")
                return False
            logger.info("✅ [Action-Search] 媒体分类页面加载完成")
            return True
        except Exception:
            logger.error("❌ [Action-Search] 媒体分类页面加载超时或失败")
            return False


    # 点击文件选项
    def click_file_option(self):
        """点击‘文件’快速分类搜索"""
        logger.info("🖱️ [Action-Search] 点击‘文件’筛选分类")
        self.click(ChatSearchLocator.OPTION_FILE)

    # 点击群成员选项
    def click_group_member_option(self):
        """点击‘群成员’快速分类搜索"""
        logger.info("🖱️ [Action-Search] 点击‘群成员’筛选分类")
        self.click(ChatSearchLocator.OPTION_GROUP_MEMBER)

    
    # 等待聊天记录中文件分类页面加载
    def wait_for_file_page_load(self, timeout: int = 10) -> bool:
        """等待聊天记录中文件分类页面完全加载完成"""
        logger.info("⏳ [Action-Search] 等待文件分类页面加载")
        try:
            elems = self.find_elements(ChatSearchLocator.BY_FILE_RV, timeout=timeout, expect_missing=True)
            if not elems:
                logger.error("❌ [Action-Search] 未找到文件分类页面")
                return False
            logger.info("✅ [Action-Search] 文件分类页面加载完成")
            return True
        except Exception:
            logger.error("❌ [Action-Search] 文件分类页面加载超时或失败")
            return False

    # 获取日期容器
    def get_date_container(self) -> list[WebElement]:
        """获取日期容器"""
        day_grid = self.find_elements(ChatSearchLocator.DAY_GRID, timeout=2)
        if not day_grid:
            logger.error("❌ [Action-Search] 未找到日期容器 - 可能没有与该会话的聊天内容")
            raise Exception("未找到日期容器 - 可能没有与该会话的聊天内容")
        logger.info(f"✅ [Action-Search] 获取到日期容器, 共 {len(day_grid)} 个")
        return day_grid
    
    # 获取指定年月的标题元素
    def get_month_title_element(self, year_month: str) -> WebElement | None:
        """获取指定年月的标题元素"""
        locator = ChatSearchLocator.get_month_title_locator(year_month)
        title_element = self.find_element(locator, timeout=2, raise_exception=False)
        if not title_element:
            logger.info(f"ℹ️ [Action-Search] 当前页面未显示月份标题: {year_month}")
            return None
        logger.info(f"✅ [Action-Search] 获取到月份标题元素: {year_month}")
        return title_element

    # 获取指定某天的元素
    def get_calendar_day_element(self, year_month: str, day: str) -> WebElement | None:
        """获取指定某天的元素"""
        locator = ChatSearchLocator.get_calendar_day_locator(year_month, int(day))
        day_element = self.find_element(locator, timeout=1, raise_exception=False)
        if not day_element:
            return None
        logger.info(f"✅ [Action-Search] 获取到日期元素: {year_month} - {day}日")
        return day_element

    # 判断日历中某天是否为灰色（即无消息状态）
    def is_day_gray(self, element: WebElement = None) -> bool:
        """
        判断日历中某天是否呈现为灰色（代表当天无消息记录）
        """
        from business_helpers.verify_color import VerifyColor
        if not element:
            logger.warning("⚠️ [Action-Search] 未找到日期元素，无法判断是否为灰色")
            return False
        is_gray = VerifyColor.verify_btn_is_gray(element)
        logger.info(f"📊 [Action-Search] 日期是否为灰色(无消息): {is_gray}")
        return is_gray

    # 点击日历中的指定日期以查看当天聊天消息
    def click_calendar_day(self, element: WebElement = None):
        """点击日历中的指定日期以查看当天聊天消息"""
        if not element:
            logger.warning("⚠️ [Action-Search] 未找到日期元素，无法点击")
            return
        element.click()
        logger.info(f"🖱️ [Action-Search] 点击日历上的日期")

    # 获取媒体网格图片或视频的数量
    def get_media_items_count(self) -> int:
        """获取媒体网格图片或视频的数量"""
        logger.info("🔍 [Action-Search] 统计分类下媒体/文件项数量")
        try:
            items = self.find_elements(ChatSearchLocator.IV_PIC, timeout=3, raise_exception=False)
            if not items:
                logger.warning("⚠️ [Action-Search] 未找到任何媒体/文件项")
                return 0
            logger.info(f"✅ [Action-Search] 找到 {len(items)} 个媒体/文件项")
            return len(items)
        except Exception:
            logger.warning("⚠️ [Action-Search] 统计媒体/文件项数量失败")
            return 0

    # 获取文件网格的数量
    def get_file_items_count(self) -> int:
        """获取文件网格的数量"""
        logger.info("🔍 [Action-Search] 统计分类下文件项数量")
        try:
            items = self.find_elements(ChatSearchLocator.FILE_NAME, timeout=3, raise_exception=False)
            if not items:
                logger.warning("⚠️ [Action-Search] 未找到任何文件项")
                return 0
            logger.info(f"✅ [Action-Search] 找到 {len(items)} 个文件项")
            return len(items)
        except Exception:
            logger.warning("⚠️ [Action-Search] 统计文件项数量失败")
            return 0

    # 点击分类列表中的媒体项
    def click_media_item(self, index: int = 0) -> str:
        """点击分类列表中的媒体项"""
        logger.info(f"🖱️ [Action-Search] 点击第 {index + 1} 个媒体缩略图项")
        items = self.find_elements(ChatSearchLocator.IV_PIC, timeout=3)
        if not items:
            logger.error(f"❌ [Action-Search] 未找到任何媒体项")
            return None
        image_hash = ScreenshotUtils.dhash_auto(element=items[index])
        logger.info(f"🖼️ [Action-Search] 第 {index + 1} 个媒体缩略图的 hash 值: {image_hash}")
        items[index].click()
        return image_hash

    # 点击分类列表中的文件项
    def click_file_item(self, index: int = 0) -> str:
        """点击分类列表中的文件项"""
        logger.info(f"🖱️ [Action-Search] 点击第 {index + 1} 个文件项")
        items = self.find_elements(ChatSearchLocator.FILE_NAME, timeout=3)
        if not items:
            logger.error(f"❌ [Action-Search] 未找到任何文件项")
            return None
        file_name = items[index].get_attribute('text')
        logger.info(f"📁 [Action-Search] 第 {index + 1} 个文件项的文件名: {file_name}")
        items[index].click()
        return file_name

    # 点击图片预览页的“定位到聊天位置”
    def click_locate_to_chat(self):
        """点击图片预览页的“定位到聊天位置”"""
        logger.info("🖱️ [Action-Search] 点击预览界面中的“定位到聊天位置”按钮")
        self.click(ChatSearchLocator.PREVIEW_LOCATE_BTN)
        time.sleep(1.0)  # 等待界面跳转与滚动定位


    # 按群成员
    # 获取群成员分类列表中的群成员数量
    def get_group_members_count(self) -> int:
        """获取群成员分类列表中的群成员数量"""
        logger.info("🔍 [Action-Search] 统计群成员分类下群成员数量")
        try:
            items = self.find_elements(ChatSearchLocator.FILE_BY_NAME, timeout=3)
            if not items:
                logger.warning("⚠️ [Action-Search] 未找到任何群成员")
                return 0
            logger.info(f"✅ [Action-Search] 找到 {len(items)} 个群成员")
            return len(items)
        except Exception:
            logger.warning("⚠️ [Action-Search] 统计群成员数量失败")
            return 0
    
    # 点击消息列表中的第一条消息
    def click_message_item(self, index: int = 0):
        """点击消息列表中的第 index 条消息"""
        logger.info(f"🖱️ [Action-Search] 点击第 {index + 1} 条消息")
        items = self.find_elements(ChatSearchLocator.FILE_BY_NAME, timeout=3)
        if len(items) > index:
            items[index].click()
            time.sleep(1.0)
        else:
            raise IndexError(f"❌ 消息列表索引 {index} 超出范围")


    # ======================================================================
    # 逻辑功能相关
    # ======================================================================
    # 日期转换映射
    def get_year_month_from_date(self, date_str: str) -> str:
        """转换日期格式  x年y月"""
        date_list = date_str.split("-")
        year = date_list[0] + "年"
        month = date_list[1].lstrip("0") + "月"
        return year+month

    # 根据条件滚动日期面板查询指定日期（带点击操作）
    def scroll_date_panel(self, target_ym: str, day: str, max_scroll: int = 20) -> bool:
        """
        根据年月和天，滚动日期面板查询指定日期（默认从最底部往上滚动查找）。
        如果找到该日期，并且该日期是非灰色（有消息状态），则执行点击并返回 True；
        如果该日期 is_gray 是灰色（无消息），打印日志并不做点击操作返回 False；
        如果在最大滚动次数内未找到该日期或无法点击，返回 False。
        """
        logger.info(f"🧭 [Action-Search] 开始往上滚动搜索目标月份: {target_ym}, 日期: {day}")

        scroll_count = 0
        last_page_source = None
        while scroll_count < max_scroll:
            day_element = self.get_calendar_day_element(target_ym, day)
            if day_element:
                is_gray = self.is_day_gray(day_element)
                if is_gray:
                    logger.warning(f"⚠️ [Action-Search] 目标日期 '{target_ym} {day}日' 在日历中为灰色(无消息)，不可点击")
                    return False
                else:
                    logger.info(f"🎉 [Action-Search] 找到目标日期 '{target_ym} {day}日' 且为激活状态，执行点击跳转")
                    self.click_calendar_day(day_element)
                    time.sleep(1)
                    return True

            is_changed, last_page_source = self.is_page_source_changed(last_page_source)
            if not is_changed:
                logger.warning(f"⚠️ [Action-Search] 已滚动至日历最顶部，无法继续向上滚动，未找到目标日期: {target_ym} {day}日")
                return None

            logger.info(f"🔄 [Action-Search] 当前屏未找到目标日期，向上滚动 (第 {scroll_count + 1}/{max_scroll} 次滑动)")
            self.swipe_page(slid_type="down", duration=800)
            scroll_count += 1
            time.sleep(0.5)
        logger.error(f"❌ [Action-Search] 滚动 {max_scroll} 次后仍未找到或无法点击目标日期: {target_ym} {day}日")
        return None

    # 通过 ocr 进行识别获取消息定位后的日期
    def get_date_from_ocr(self) -> list[str]:
        """通过OCR识别消息定位后的日期"""
        from utils.cv_recognition.ocr_utils import OcrUtils
        ocr_utils = OcrUtils(self.driver)
        texts = ocr_utils.get_all_text(image_name="search_date_locate.png")
        logger.info(f"✅ [Action-Search] 识别到的日期: {texts}")
        return texts






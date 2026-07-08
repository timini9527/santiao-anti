import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from common.base_page import BasePage
from core.logger_utils import logger
from locators.common.common_locator import CommonLocator
from locators.moments.moments_locator import MomentsLocator


class MomentsPage(BasePage):
    """动态页面的所有操作"""

    # ============================================================================
    # 朋友圈页面-基础功能
    # ============================================================================
    # 动态 - 等待朋友圈页面加载完成
    def wait_for_moments_page_load(self, timeout: int = 10, raise_exception: bool = True) -> bool:
        """ 动态 - 等待朋友圈页面加载完成"""
        logger.info(f"⏳ [Wait-moments] 等待朋友圈页面加载完成，超时时间 {timeout} 秒")
        try:
            is_visible = self.get_attribute(MomentsLocator.TV_MOMENTS, 'text') == '动态'
            logger.info(f"✅ [Wait-moments] 朋友圈页面加载完成, 标题是否显示: {is_visible}")
            return bool(is_visible)
        except Exception:
            logger.warning("⚠️ [Wait-moments] 朋友圈页面加载超时")
            return False

    # 动态 - 点击返回按钮
    def click_iv_back(self):
        """ 动态 - 点击返回按钮"""
        self.click(MomentsLocator.IV_BACK)
        logger.info("🚀 [Action-moments] 点击返回按钮")

    # 动态 - 点击发布朋友圈按钮
    def click_post_moments(self):
        """ 动态 - 点击发布朋友圈按钮"""
        self.click(MomentsLocator.IV_CAMERA)
        logger.info("🚀 [Action-moments]点击发布朋友圈按钮")

    # 动态 - 输入朋友圈文字内容
    def input_moments_content(self, text: str):
        """ 动态 - 输入朋友圈文字内容"""
        self.send_keys(MomentsLocator.ET_TEXT, text)
        logger.info(f"🚀 [Action-moments]输入朋友圈内容: {text}")

    # 动态 - 点击发表按钮
    def click_publish(self):
        """ 动态 - 点击发表按钮"""
        self.click(MomentsLocator.TV_SEND)
        logger.info("🚀 [Action-moments]点击发表按钮")

    # 动态 - 快速发布一条纯文字动态
    def post_text_moment(self, text: str):
        """ 动态 - 快速发布一条纯文字动态"""
        self.click_post_moments()
        self.input_moments_content(text)
        self.click_publish()

    # 动态 - 判断朋友圈发布编辑页是否展示
    def is_publish_editor_displayed(self) -> bool:
        """ 动态 - 判断朋友圈发布编辑页是否展示"""
        is_displayed = self.is_element_exist(MomentsLocator.ET_TEXT, timeout=2, raise_exception=False)
        logger.info(f"🔍 [Check-moments] 朋友圈发布编辑页是否展示: {is_displayed}")
        return is_displayed

    # 动态 - 尝试发布空内容，返回是否仍停留在发布编辑页
    def try_publish_empty_moment(self) -> bool:
        """ 动态 - 尝试发布空内容，返回是否仍停留在发布编辑页"""
        self.click_post_moments()
        if self.is_element_exist(MomentsLocator.TV_SEND, timeout=1, raise_exception=False):
            self.click(MomentsLocator.TV_SEND)
            time.sleep(1)
        is_still_editing = self.is_publish_editor_displayed()
        logger.info(f"🔍 [Check-moments] 空内容发表后是否仍停留编辑页: {is_still_editing}")
        return is_still_editing

    # 动态 - 获取第一条动态的正文内容
    def get_first_moment_content(self) -> str:
        """ 动态 - 获取朋友圈第一条动态的正文内容"""
        content = self.get_attribute(MomentsLocator.TV_CONTENT, 'text')
        if content == "":
            logger.warning(f"⚠️ [Check-moments] 朋友圈第一条内容为空")
        else:
            logger.info(f"🔍 [Check-moments] 朋友圈第一条内容: {content}")
        return content

    # 动态 - 获取当前页面可见的朋友圈正文内容-Item
    def get_visible_moment_contents_item(self, timeout: int=2, raise_exception: bool=True) -> list[WebElement]:
        """ 动态 - 获取当前页面可见的朋友圈正文内容-Item"""
        content_elems = self.find_elements(MomentsLocator.TV_CONTENT, timeout=timeout, raise_exception=raise_exception)
        if content_elems == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈正文内容-Item")
        else:
            logger.info(f"🔍 [Check-moments] 当前可见朋友圈正文内容-Item个数: {len(content_elems)}")
        return content_elems
    
    # 动态 - 获取当前页面可见的朋友圈正文内容-Text
    def get_visible_moment_contents_text(self) -> list[str]:
        """ 动态 - 获取当前页面可见的朋友圈正文内容-Text"""
        content_texts = self.get_visible_moment_contents_item()
        if content_texts == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈正文内容-Text")
            return []
        content_texts = [item.get_attribute('text') for item in content_texts]
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈正文内容-Text: {content_texts}")
        return content_texts

    # 动态 - 删除动态
    def delete_moment(self):
        """ 动态 - 删除动态"""
        self.click(MomentsLocator.TV_DELETE)
        logger.info("🚀 [Action-moments]点击了朋友圈动态的删除按钮")
        time.sleep(0.5)
    
    # 动态 - 确认删除动态
    def confirm_delete_moment(self):
        """ 动态 - 确认删除动态"""
        self.click(MomentsLocator.DIALOG_CONFIRM_BTN)
        logger.info("🚀 [Action-moments]点击了删除确认对话框的确定按钮")
        time.sleep(0.5)

    # 动态 - 取消删除动态
    def cancel_delete_moment(self):
        """ 动态 - 取消删除动态"""
        self.click(MomentsLocator.BTN_CANCEL)
        logger.info("🚀 [Action-moments]点击了删除取消对话框的取消按钮")
        time.sleep(0.5)

    # 动态 - 删除自己发布的第一条朋友圈动态并二次确认
    def delete_first_moment(self):
        """ 动态 - 删除自己发布的第一条朋友圈动态并二次确认"""
        self.delete_moment()
        self.confirm_delete_moment()
        logger.info("🚀 [Action-moments]点击了朋友圈动态的删除按钮")


    # ============================================================================
    # 刷新
    # ============================================================================
    # 动态 - 下拉刷新朋友圈列表
    def refresh_moments(self):
        """ 动态 - 下拉刷新朋友圈列表"""
        self.swipe_page(slid_type="down", duration=300, times=1)
        logger.info("🚀 [Action-moments]下拉刷新朋友圈列表")
        time.sleep(0.5)

    # 动态 - 上滑加载更多朋友圈列表
    def load_more_moments(self):
        """ 动态 - 上滑加载更多朋友圈列表"""
        self.swipe_page(slid_type="up", duration=300, times=1)
        logger.info("🚀 [Action-moments]上滑加载更多朋友圈列表")
        time.sleep(0.5)
    
    # ============================================================================
    # 点赞和评论
    # ============================================================================
    # 动态 - 获取朋友圈点赞按钮
    def get_like_button_elems(self, timeout: int=2, raise_exception: bool=False) -> list[WebElement]:
        """ 动态 - 获取朋友圈点赞按钮"""
        like_buttons = self.find_elements(MomentsLocator.TV_LIKE, timeout=timeout, raise_exception=raise_exception)
        if like_buttons == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈点赞按钮")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈点赞按钮个数: {len(like_buttons)}")
        return like_buttons

    # 动态 - 为第n条动态点赞，n从0开始，不传默认为0
    def click_like_nth_moment(self, n: int=0):
        """ 动态 - 为第n条动态点赞，n从0开始，不传默认为0"""
        like_buttons = self.get_like_button_elems()
        if len(like_buttons) <= n:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见第{n+1}条动态的点赞按钮")
            return
        self.click(like_buttons[n])
        logger.info(f"🚀 [Action-moments]为第{n+1}条动态点赞")
    
    # 动态 - 输入评论内容
    def send_comment_text(self, comment_text: str):
        """ 动态 - 输入评论内容"""
        self.send_keys(MomentsLocator.ET_COMMENT, comment_text)
        logger.info(f"🚀 [Action-moments]输入评论内容: {comment_text}")
    
    # 动态 - 发送评论
    def send_comment(self):
        """ 动态 - 发送评论"""
        self.click(MomentsLocator.TV_SEND)
        logger.info("🚀 [Action-moments]发送评论")
    
    # 动态 - 输入内容并发送评论
    def post_comment(self, comment_text: str):
        """ 动态 - 输入内容并发送评论"""
        self.send_comment_text(comment_text)
        self.send_comment()
        logger.info(f"🚀 [Action-moments]输入内容并发送评论: {comment_text}")

    # 动态 - 获取第n条动态的评论按钮
    def get_comment_button_elems(self, timeout: int=2, raise_exception: bool=True) -> list[WebElement]:
        """ 动态 - 获取第n条动态的评论按钮"""
        comment_buttons = self.find_elements(MomentsLocator.TV_COMMENT, timeout=timeout, raise_exception=raise_exception)
        if comment_buttons == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈评论按钮")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈评论按钮个数: {len(comment_buttons)}")
        return comment_buttons

    # 动态 - 为第n条动态发表评论，n从0开始，不传默认为0
    def click_comment_on_nth_moment(self, n: int=0):
        """ 动态 - 为第n条动态发表评论，n从0开始，不传默认为0"""
        comment_buttons = self.get_comment_button_elems()
        if len(comment_buttons) <= n:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见第{n+1}条动态的评论按钮")
            return
        self.click(comment_buttons[n])
        logger.info(f"🚀 [Action-moments] 点击评论第{n+1}条动态")
    
    # 动态 - 获取可见评论内容Item
    def get_comment_item_elems(self, timeout: int=2, raise_exception: bool=True) -> list[WebElement]:
        """ 动态 - 获取可见评论内容Item"""
        comment_elems = self.find_elements(MomentsLocator.RV_COMMENT_DETAIL, timeout=timeout, raise_exception=raise_exception)
        if comment_elems == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈评论内容Item")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈评论内容Item个数: {len(comment_elems)}")
        return comment_elems

    # 动态 - 获取当前可见评论内容列表
    def get_comment_texts(self, timeout: int=2, raise_exception: bool=True) -> list[str]:
        """ 动态 - 获取当前可见评论内容列表"""
        comment_elems = self.get_comment_item_elems(timeout, raise_exception)
        if comment_elems == []:
            return []
        comments = [elem.get_attribute('text') for elem in comment_elems]
        logger.info(f"🔍 [Check-moments] 当前可见评论内容: {comments}")
        return comments

    # 动态 - 获取自己发送的评论Item
    def get_own_comment_item(self, comment_text: str, nickname: str = "") -> WebElement | None:
        """
        根据评论内容和发送者昵称，精准获取自己发送的评论Item元素。
        若指定了 nickname，则匹配包含 nickname 和 comment_text 的评论；
        若有多条完全相同的评论，可通过遍历点击并探测是否有“删除”菜单来定位。
        """
        comment_elems = self.get_comment_item_elems()
        for elem in comment_elems:
            text = elem.get_attribute('text') or ""
            if nickname:
                if nickname in text and comment_text in text:
                    logger.info(f"🔍 [Check-moments] 通过昵称组合定位到特定评论: {text}")
                    return elem
            else:
                if comment_text in text:
                    logger.info(f"🔍 [Check-moments] 模糊匹配定位到评论: {text}")
                    return elem
        logger.warning(f"⚠️ [Check-moments] 未在当前页面定位到匹配 [{comment_text}] 的评论")
        return None

    # 动态 - 根据评论内容点击该评论以触发删除菜单（支持昵称组合和防重探测）
    def click_comment_by_text(self, comment_text: str, nickname: str = ""):
        """ 动态 - 根据评论内容点击该评论以触发删除菜单（支持昵称组合和防重探测）"""
        elem = self.get_own_comment_item(comment_text, nickname)
        if elem:
            self.click(elem)
            logger.info(f"🚀 [Action-moments] 点击指定评论: [{comment_text}]")
            time.sleep(0.5)
        else:
            comment_elems = self.get_comment_item_elems()
            for item in comment_elems:
                text = item.get_attribute('text') or ""
                if comment_text in text:
                    self.click(item)
                    time.sleep(0.5)
                    delete_btn = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("删除")')
                    if self.is_element_exist(delete_btn, timeout=1.5, raise_exception=False):
                        logger.info(f"🔍 [Check-moments] 探测到此项为自己发布的评论，保持点击状态")
                        return
                    else:
                        logger.info("🔍 [Check-moments] 探测到此项非自己发送的评论，正在返回重试下一条")
                        self.driver.back()
                        time.sleep(0.5)
            logger.warning(f"⚠️ [Action-moments] 未能成功探测到属于自己的评论")

    # 动态 - 删除自己发布的评论
    def delete_own_comment(self, comment_text: str, nickname: str = ""):
        """ 动态 - 删除自己发布的评论"""
        self.click_comment_by_text(comment_text, nickname)
        logger.info(f"🚀 [Action-moments] 点击评论: [{comment_text}] 后进行删除操作")
        time.sleep(0.5)
    
    # 动态 - 确认删除评论
    def confirm_delete_comment(self):
        """ 动态 - 确认删除评论"""
        self.click(MomentsLocator.DIALOG_CONFIRM_BTN)
        logger.info("🚀 [Action-moments] 点击评论的确定按钮")
        time.sleep(0.5)

    # 动态 - 取消删除评论
    def cancel_delete_comment(self):
        """ 动态 - 取消删除评论"""
        self.click(MomentsLocator.DIALOG_CANCEL_BTN)
        logger.info("🚀 [Action-moments] 点击评论的取消按钮")
        time.sleep(0.5)

    # 动态 - 删除自己发布的评论并二次确认
    def delete_own_comment_with_confirm(self,comment_text: str, nickname: str = ""):
        """ 动态 - 删除自己发布的评论并二次确认"""
        self.delete_own_comment(comment_text,nickname)
        self.confirm_delete_comment()
        logger.info(f"🚀 [Action-moments] 成功删除自己发布的评论: [{comment_text}]")



    # ============================================================================
    # 检查
    # ============================================================================
    # 动态 - 检查当前朋友圈首屏可见列表中是否包含指定文字内容的动态
    def has_moment_with_text(self, text: str) -> bool:
        """ 动态 - 检查当前朋友圈首屏可见列表中是否包含指定文字内容的动态"""
        contents = self.get_visible_moment_contents()
        found = any(text in content for content in contents)
        logger.info(f"🔍 [Check-moments] 朋友圈信息流中是否存在包含 [{text}] 的动态: {found}")
        return found

    def get_visible_moment_contents(self) -> list[str]:
        """ 向前兼容：获取当前页面可见的朋友圈正文内容 """
        return self.get_visible_moment_contents_text()


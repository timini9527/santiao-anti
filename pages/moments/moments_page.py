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
    def wait_for_moments_page_load(self, timeout: int = 10) -> bool:
        """ 动态 - 等待朋友圈页面加载完成"""
        try:
            is_visible = self.is_element_exist(MomentsLocator.TV_MOMENTS_XPATH, timeout=timeout)
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
    
    # 动态 - 长按发布朋友圈按钮
    def long_press_post_moments(self, hold_time: int = 1000):
        """ 动态 - 长按发布朋友圈按钮"""
        elem = self.find_element(MomentsLocator.IV_CAMERA, timeout=2)
        self.long_press_action(found_ele=elem, hold_time=hold_time)
        logger.info(f"🚀 [Action-moments]长按朋友圈按钮，耗时{hold_time}毫秒")
    
    # 动态 - 点击拍摄
    def click_camera(self):
        """ 动态 - 点击拍摄"""
        self.click(MomentsLocator.CL_SHOOTING)
        logger.info("🚀 [Action-moments]点击拍摄")
    
    # 动态 - 点击从相册选择
    def click_album(self):
        """ 动态 - 点击从相册选择"""
        self.click(MomentsLocator.TV_GALLERY)
        logger.info("🚀 [Action-moments]点击从相册选择")
    
    # 动态 - 点击取消
    def click_cancel(self):
        """ 动态 - 点击取消"""
        self.click(MomentsLocator.FB_CANCEL)
        logger.info("🚀 [Action-moments]点击取消")

    # 动态 - 输入朋友圈文字内容
    def input_moments_content(self, text: str):
        """ 动态 - 输入朋友圈文字内容"""
        self.send_keys(MomentsLocator.ET_TEXT, text)
        logger.info(f"🚀 [Action-moments]输入朋友圈内容: {text}")

    # 动态 - 点击发表按钮
    def click_publish(self):
        """ 动态 - 点击发表按钮"""
        self.click(MomentsLocator.FB_ACTION)
        logger.info("🚀 [Action-moments]点击发表按钮")
    

    # ============================================================================
    # 朋友圈 - 朋友圈列表
    # ============================================================================
    # 动态 - 获取朋友圈列表的Item
    def get_visible_moment_items(self, timeout: int=2) -> list[WebElement]:
        """ 动态 - 获取朋友圈列表的Item"""
        moment_list = self.find_elements(MomentsLocator.RV_LIST_MOMENT_CONTENT, timeout=timeout)
        if moment_list:
            logger.info(f"🚀 [Action-moments]获取朋友圈列表的Item, 共{len(moment_list)}个")
        else:
            logger.info(f"⚠️ [Action-moments]获取朋友圈列表的Item为空")
        return moment_list

    # 动态 - 朋友圈列表的第n个item，默认为第一个
    def get_moment_item(self, index: int = 0, timeout: int = 2) -> WebElement:
        """ 动态 - 朋友圈列表的第n个item，默认为第一个(由0开始索引)"""
        moment_list = self.get_visible_moment_items(timeout=timeout)
        if moment_list:
            if index < len(moment_list):
                logger.info(f"🚀 [Action-moments]获取朋友圈列表的第 {index} 个Item")
                return moment_list[index]
            else:
                logger.warning(f"⚠️ [Action-moments]获取朋友圈列表请求索引 {index} 越界，列表共有 {len(moment_list)} 个Item")
        else:
            logger.info(f"⚠️ [Action-moments]获取朋友圈列表的第 {index} 个Item为空")
        return None

    # 动态 - 判断朋友圈列表是否包含图片/视频
    def is_moment_contains_media(self, motype: int = 1, index: int = 0) -> bool:
        """动态 - 判断指定朋友圈列表项是否包含图片/视频。

        motype: 1=图片, 2=视频
        """
        locator_map = {
            1: MomentsLocator.IV_MEDIA,
            2: MomentsLocator.IV_SINGLE_PIC,
        }
        locator = locator_map.get(motype)
        if locator is None:
            raise ValueError(f"不支持的朋友圈媒体类型: {motype}")

        moment_item = self.get_moment_item(index=index)
        if moment_item is None:
            logger.warning(f"⚠️ [Check-moments] 未找到第 {index} 条朋友圈，无法校验媒体类型 {motype}")
            return False

        media_elements = moment_item.find_elements(*locator)
        has_media = len(media_elements) > 0
        media_name = "图片" if motype == 1 else "视频"
        if has_media:
            logger.info(f"🔍 [Check-moments] 第 {index} 条朋友圈包含{media_name}")
        else:
            logger.warning(f"⚠️ [Check-moments] 第 {index} 条朋友圈不包含{media_name}")
        return has_media



    # 动态 - 点击全文展开或收起
    def click_expand_or_shrink_moment(self, is_expand: bool = True, index: int = 0):
        """ 动态 - 点击全文展开或收起"""
        moment_item = self.get_moment_item(index=index)
        if moment_item is None:
            logger.warning(f"⚠️ [Check-moments] 未找到第 {index} 个朋友圈Item，无法执行展开或收起")
            return

        expand_btns = moment_item.find_elements(*MomentsLocator.TV_EXPAND)
        if expand_btns:
            expand_btn = expand_btns[0]
            btn_text = expand_btn.text
            logger.info(f"🔍 [Check-moments] 找到展开或收起按钮，当前状态文本为: '{btn_text}'，期望 is_expand={is_expand}")
            
            if (is_expand and btn_text == "全文") or (not is_expand and btn_text == "收起"):
                expand_btn.click()
                logger.info(f"🚀 [Action-moments] 成功点击了第 {index} 个Item的展开/收起按钮")
            else:
                logger.info(f"ℹ️ [Check-moments] 按钮状态与期望一致，无需重复点击")
        else:
            logger.warning(f"⚠️ [Check-moments] 当前页面第 {index} 个Item没有找到展开或收起按钮")
    

    # ============================================================================
    # 朋友圈 - 快速发布动态
    # ============================================================================
    # 动态 - 快速发布一条纯文字动态
    def post_text_moment(self, text: str):
        """ 动态 - 快速发布一条纯文字动态"""
        self.long_press_post_moments(1000)
        self.input_moments_content(text)
        self.click_publish()
    
    # 动态 - 快速发布一条图片动态
    def post_image_moment(self, image_path: str):
        """ 动态 - 快速发布一条图片动态"""
        self.click_post_moments()
        self.click_album()
        self.select_image_from_album(image_path)
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
    def get_first_moment_content(self, except_int: int=1) -> str:
        """ 动态 - 获取朋友圈第一条动态的正文内容"""
        raise_exception = True if except_int == 1 else False
        content = self.get_attribute(MomentsLocator.TV_CONTENT, 'text', raise_exception=raise_exception)
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
    
    # 动态 - 获取当前页面可见的朋友圈正文内容列表-Text
    def get_visible_moment_contents(self) -> list[str]:
        """ 动态 - 获取当前页面可见的朋友圈正文内容列表-Text"""
        content_elems = self.get_visible_moment_contents_item()
        if not content_elems:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈正文内容")
            return []
        content_texts = [item.get_attribute('text') for item in content_elems]
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈正文内容: {content_texts}")
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
        self.click(MomentsLocator.DIALOG_CANCEL_BTN)
        logger.info("🚀 [Action-moments]点击了删除取消对话框的取消按钮")
        time.sleep(0.5)

    # 动态 - 删除自己发布的第一条朋友圈动态并二次确认
    def delete_first_moment(self):
        """ 动态 - 删除自己发布的第一条朋友圈动态并二次确认"""
        self.delete_moment()
        self.confirm_delete_moment()
        logger.info("🚀 [Action-moments]点击了朋友圈动态的删除按钮")

    # 动态 - 确认对话框的确认按钮
    def click_ok_dialog(self):
        """ 动态 - 确认对话框的确认按钮"""
        self.click(MomentsLocator.DIALOG_OK_BTN)
        logger.info("🚀 [Action-moments]点击了确认对话框的确认按钮")


    # ============================================================================
    # 图片动态 - 发送图片相关
    # ============================================================================
    # 图片动态 - 获取图片element
    def get_photo_elements(self) -> list[WebElement]:
        """ 图片动态 - 获取图片element"""
        photo_elements = self.find_elements(MomentsLocator.IV_MEDIA, timeout=2)
        if not photo_elements:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见图片")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见图片数量: {len(photo_elements)}")
        return photo_elements
    
    # 图片动态 - 获取第 n 个 element
    def get_photo_element(self, index: int = 0) -> WebElement:
        """ 图片动态 - 获取第 n 个 element"""
        photo_element = self.get_photo_elements()[index]
        logger.info(f"🔍 [Check-moments] 第 {index} 个 element: { '存在' if photo_element else '不存在'}")
        return photo_element
    
    # 图片动态 - 判断最后一个 element是否存在
    def is_last_photo_element(self) -> bool:
        """ 图片动态 - 判断最后一个 element是否存在"""
        is_last_photo_element = self.is_element_exist(MomentsLocator.RV_PIC_LAST_VIDEO_GROUP, timeout=3)
        if is_last_photo_element:
            logger.info(f"🔍 [Check-moments] 最后一个 element: 存在")
        else:
            logger.warning(f"⚠️ [Check-moments] 最后一个 element: 不存在")
        return is_last_photo_element
    
    # 图片动态 - 点击最后一个 element 进行添加图片或视频
    def click_last_photo_element(self):
        """ 图片动态 - 点击最后一个 element 进行添加图片或视频"""
        self.click(MomentsLocator.RV_PIC_LAST_VIDEO_GROUP)
        logger.info("🚀 [Action-moments]点击了最后一个 element 进行添加图片或视频")
    
    # 图片动态 - 获取已选择图片的数量
    def get_selected_photo_count(self):
        """ 图片动态 - 获取已选择图片的数量"""
        count = len(self.get_photo_elements())
        logger.info(f"🔍 [Check-moments] 已选择图片数量: {count}")
        return count


    # ============================================================================
    # 刷新与加载
    # ============================================================================
    # 动态刷新 - 下拉刷新朋友圈列表
    def refresh_moments(self):
        """ 动态刷新 - 下拉刷新朋友圈列表"""
        self.swipe_page(slid_type="down", duration=300)
        logger.info("🚀 [Action-moments]下拉刷新朋友圈列表")
        time.sleep(0.5)

    # 动态加载 - 上滑加载更多朋友圈列表
    def load_more_moments(self):
        """ 动态加载 - 上滑加载更多朋友圈列表"""
        self.swipe_page(slid_type="up", duration=300)
        logger.info("🚀 [Action-moments]上滑加载更多朋友圈列表")
        time.sleep(0.5)
    
    # 动态加载 - 快速上滑加载最后一条朋友圈动态
    def fast_load_more_moments(self, max_swipes: int = 200) -> bool:
        """ 动态加载 - 快速上滑加载最后一条朋友圈动态 (使用高性能稀疏 DOM 边界检测)"""
        swipe_times = 0
        last_source = ""
        
        while max_swipes > 0:
            if swipe_times > 0 and swipe_times % 10 == 0:
                is_changed, last_source = self.is_page_source_changed(last_source)
                if not is_changed:
                    logger.info(f"✅ [Action-moments] 检测到页面 DOM 无变化，物理边界触底（滑动 {swipe_times} 次），安全终止。")
                    return True
                    
            self.swipe_page(slid_type="up", duration=200, x_ratio=0.8)
            swipe_times += 1
            logger.info(f"🚀 [Action-moments]快速上滑加载最后一条朋友圈动态第{swipe_times}次")
            time.sleep(0.8)
            max_swipes -= 1
        return False
    
    
    # ============================================================================
    # 点赞和评论相关功能
    # ============================================================================
    # 动态点赞 - 获取朋友圈点赞按钮
    def get_like_button_elems(self, timeout: int=2, raise_exception: bool=False) -> list[WebElement]:
        """ 动态点赞 - 获取朋友圈点赞按钮"""
        like_buttons = self.find_elements(MomentsLocator.TV_LIKE, timeout=timeout, raise_exception=raise_exception)
        if like_buttons == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈点赞按钮")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈点赞按钮个数: {len(like_buttons)}")
        return like_buttons

    # 动态点赞 - 为第n条动态点赞，n从0开始，不传默认为0
    def click_like_nth_moment(self, n: int=0):
        """ 动态点赞 - 为第n条动态点赞，n从0开始，不传默认为0"""
        like_buttons = self.get_like_button_elems()
        if len(like_buttons) <= n:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见第{n+1}条动态的点赞按钮")
            return
        like_buttons[n].click()
        logger.info(f"🚀 [Action-moments]为第{n+1}条动态点赞")

    # 动态点赞 - 获取第n条朋友圈的点赞用户名文本并转化为用户列表
    def get_nth_moment_like_users(self, n: int = 0) -> list[str]:
        """ 动态点赞 - 获取第n条朋友圈的点赞用户名文本并转化为用户列表 """
        moment_item = self.get_moment_item(n)
        if moment_item is None:
            logger.warning(f"⚠️ [Check-moments] 未找到第 {n+1} 个朋友圈Item，无法获取点赞人列表")
            return []

        like_users_elems = moment_item.find_elements(*MomentsLocator.TV_LIKE_USERNAME)
        if like_users_elems:
            raw_text = "".join([elem.text for elem in like_users_elems if elem.text])
            if not raw_text.strip():
                logger.info(f"🔍 [Check-moments] 第 {n+1} 条动态点赞人节点文本为空")
                return []
            users = raw_text.split("，")
            logger.info(f"🔍 [Check-moments] 成功获取第 {n+1} 条动态的点赞用户列表: {users}")
            return users
            
        logger.info(f"🔍 [Check-moments] 第 {n+1} 条动态当前无点赞用户")
        return []
    

    # 动态评论 - 输入评论内容
    def send_comment_text(self, comment_text: str):
        """ 动态评论 - 输入评论内容"""
        self.send_keys(MomentsLocator.ET_COMMENT, comment_text)
        logger.info(f"🚀 [Action-moments]输入评论内容: {comment_text}")
    
    # 动态评论 - 发送评论
    def send_comment(self):
        """ 动态评论 - 发送评论"""
        self.click(MomentsLocator.TV_SEND)
        logger.info("🚀 [Action-moments]发送评论")
    
    # 动态评论 - 输入内容并发送评论
    def post_comment(self, comment_text: str):
        """ 动态评论 - 输入内容并发送评论"""
        self.send_comment_text(comment_text)
        self.send_comment()
        logger.info(f"🚀 [Action-moments]输入内容并发送评论: {comment_text}")

    # 动态评论 - 获取第n条动态的评论按钮
    def get_comment_button_elems(self, timeout: int=2) -> list[WebElement]:
        """ 动态评论 - 获取第n条动态的评论按钮"""
        comment_buttons = self.find_elements(MomentsLocator.TV_COMMENT, timeout=timeout)
        if comment_buttons == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈评论按钮")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈评论按钮个数: {len(comment_buttons)}")
        return comment_buttons

    # 动态评论 - 为第n条动态发表评论，n从0开始，不传默认为0
    def click_comment_on_nth_moment(self, n: int=0):
        """ 动态评论 - 为第n条动态发表评论，n从0开始，不传默认为0"""
        comment_buttons = self.get_comment_button_elems()
        if len(comment_buttons) <= n:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见第{n+1}条动态的评论按钮")
            return
        comment_buttons[n].click()
        logger.info(f"🚀 [Action-moments] 点击评论第{n+1}条动态")
    
    # 动态评论 - 获取可见评论内容Item
    def get_comment_item_elems(self, timeout: int=2, raise_exception: bool=True) -> list[WebElement]:
        """ 动态评论 - 获取可见评论内容Item"""
        comment_elems = self.find_elements(MomentsLocator.RV_COMMENT_DETAIL, timeout=timeout, raise_exception=raise_exception)
        if comment_elems == []:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见朋友圈评论内容Item")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈评论内容Item个数: {len(comment_elems)}")
        return comment_elems

    # 动态评论 - 获取当前可见评论内容列表
    def get_comment_texts(self, timeout: int=2, raise_exception: bool=True) -> list[str]:
        """ 动态评论 - 获取当前可见评论内容列表"""
        comment_elems = self.get_comment_item_elems(timeout, raise_exception)
        if comment_elems == []:
            return []
        comments = [elem.get_attribute('text') for elem in comment_elems]
        logger.info(f"🔍 [Check-moments] 当前可见评论内容: {comments}")
        return comments

    # 动态评论 - 获取自己发送的评论Item
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

    # 动态评论 - 根据评论内容点击该评论以触发删除菜单（支持昵称组合和防重探测）
    def click_comment_by_text(self, comment_text: str, nickname: str = ""):
        """ 动态评论 - 根据评论内容点击该评论以触发删除菜单（支持昵称组合和防重探测）"""
        elem = self.get_own_comment_item(comment_text, nickname)
        if elem:
            elem.click()
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

    # 动态评论 - 删除自己发布的评论
    def delete_own_comment(self, comment_text: str, nickname: str = ""):
        """ 动态评论 - 删除自己发布的评论"""
        self.click_comment_by_text(comment_text, nickname)
        logger.info(f"🚀 [Action-moments] 点击评论: [{comment_text}] 后进行删除操作")
        time.sleep(0.5)
    
    # 动态评论 - 确认删除评论
    def confirm_delete_comment(self):
        """ 动态评论 - 确认删除评论"""
        self.click(MomentsLocator.DIALOG_CONFIRM_BTN)
        logger.info("🚀 [Action-moments] 点击评论的确定按钮")
        time.sleep(0.5)

    # 动态评论 - 取消删除评论
    def cancel_delete_comment(self):
        """ 动态评论 - 取消删除评论"""
        self.click(MomentsLocator.DIALOG_CANCEL_BTN)
        logger.info("🚀 [Action-moments] 点击评论的取消按钮")
        time.sleep(0.5)

    # 动态评论 - 删除自己发布的评论并二次确认
    def delete_own_comment_with_confirm(self, comment_text: str, nickname: str = ""):
        """ 动态评论 - 删除自己发布的评论并二次确认"""
        self.delete_own_comment(comment_text, nickname)
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

    def click_add_more_photos(self):
        """ 动态 - 在发布朋友圈编辑页面，点击加号按钮继续添加图片 """
        package_id = MomentsLocator.PACKAGE_ID
        locators = [
            (AppiumBy.XPATH, f"//android.widget.ImageView[contains(@resource-id, 'iv_add') or contains(@resource-id, 'add')]"),
            (AppiumBy.XPATH, f"//*[@resource-id='{package_id}/rv_pic']//android.widget.ImageView[last()]"),
            (AppiumBy.XPATH, f"//android.widget.GridView//android.widget.ImageView[last()]"),
            (AppiumBy.XPATH, f"//*[@resource-id='{package_id}/rv_pic']/*[last()]")
        ]
        for loc in locators:
            if self.is_element_exist(loc, timeout=2, raise_exception=False):
                self.click(loc)
                logger.info(f"🚀 [Action-moments] 成功通过定位器 {loc} 点击了‘继续添加图片’加号按钮")
                time.sleep(1)
                return True
        raise RuntimeError("❌ [Action-moments] 未能定位到发布编辑页面上的‘继续添加图片’加号按钮")

    def get_published_photo_count(self) -> int:
        """ 动态 - 获取朋友圈发布编辑页面已选中的图片数量 """
        package_id = MomentsLocator.PACKAGE_ID
        elems = self.find_elements((AppiumBy.XPATH, f"//*[@resource-id='{package_id}/rv_pic']//android.widget.ImageView"), timeout=2, expect_missing=True)
        if not elems:
            elems = self.find_elements((AppiumBy.XPATH, f"//android.widget.GridView//android.widget.ImageView"), timeout=2, expect_missing=True)
        
        count = len(elems) if elems else 0
        if 0 < count < 9:
            count -= 1
        logger.info(f"🔍 [Check-moments] 发布编辑页已选图片数量为: {count}")
        return count




import time
from typing import Optional, List, Tuple
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
        """ 动态 - 等待朋友圈页面加载完成 """
        logger.info(f"⏳ [Wait-moments] 等待朋友圈页面加载完成 (超时: {timeout}s)")
        try:
            is_visible = self.is_element_exist(MomentsLocator.TV_MOMENTS_XPATH, timeout=timeout)
            logger.info(f"✅ [Wait-moments] 朋友圈页面加载完成, 标题是否显示: {is_visible}")
            return bool(is_visible)
        except Exception:
            logger.warning("⚠️ [Wait-moments] 朋友圈页面加载超时")
            return False

    # 动态 - 点击返回按钮
    def click_iv_back(self) -> None:
        """ 动态 - 点击返回按钮 """
        logger.info("🚀 [Action-moments] 点击返回按钮")
        self.click(MomentsLocator.IV_BACK)

    # 动态 - 点击发布朋友圈按钮
    def click_post_moments(self) -> None:
        """ 动态 - 点击发布朋友圈按钮 """
        logger.info("🚀 [Action-moments] 点击发布朋友圈按钮")
        self.click(MomentsLocator.IV_CAMERA)
    
    # 动态 - 校验发布朋友圈按钮是否可见
    def is_camera_displayed(self, timeout: int = 3) -> bool:
        """ 动态 - 校验发布朋友圈按钮(相机图标)是否正常可见 """
        logger.info(f"🔍 [Check-moments] 正在校验朋友圈发布相机图标是否可见(超时: {timeout}s)...")
        return bool(self.is_element_exist(MomentsLocator.IV_CAMERA, timeout=timeout))

    # 动态 - 长按发布朋友圈按钮
    def long_press_post_moments(self, hold_time: int = 1000) -> None:
        """ 动态 - 长按发布朋友圈按钮 """
        logger.info(f"🚀 [Action-moments] 长按朋友圈按钮，耗时 {hold_time} 毫秒")
        elem = self.find_element(MomentsLocator.IV_CAMERA, timeout=2)
        self.long_press_action(found_ele=elem, hold_time=hold_time)
    
    # 动态 - 点击拍摄
    def click_camera(self) -> None:
        """ 动态 - 点击拍摄 """
        logger.info("🚀 [Action-moments] 点击拍摄")
        self.click(MomentsLocator.CL_SHOOTING)
    
    # 动态 - 点击从相册选择
    def click_album(self) -> None:
        """ 动态 - 点击从相册选择 """
        logger.info("🚀 [Action-moments] 点击从相册选择")
        self.click(MomentsLocator.TV_GALLERY)
    
    # 动态 - 点击取消
    def click_cancel(self) -> None:
        """ 动态 - 点击取消 """
        logger.info("🚀 [Action-moments] 点击取消")
        self.click(MomentsLocator.FB_CANCEL)

    # 动态 - 输入朋友圈文字内容
    def input_moments_content(self, text: str) -> None:
        """ 动态 - 输入朋友圈文字内容 """
        logger.info(f"🚀 [Action-moments] 输入朋友圈内容: {text}")
        self.send_keys(MomentsLocator.ET_TEXT, text)

    # 动态 - 点击发表按钮
    def click_publish(self) -> None:
        """ 动态 - 点击发表按钮 """
        logger.info("🚀 [Action-moments] 点击发表按钮")
        self.click(MomentsLocator.FB_ACTION)

    # ============================================================================
    # 朋友圈 - 朋友圈列表
    # ============================================================================
    # 动态 - 获取朋友圈列表的Item
    def get_visible_moment_items(self, timeout: int = 2) -> list[WebElement]:
        """ 动态 - 获取朋友圈列表的Item """
        moment_list = self.find_elements(MomentsLocator.RV_LIST_MOMENT_CONTENT, timeout=timeout)
        if moment_list:
            logger.info(f"🚀 [Action-moments] 获取朋友圈列表的Item, 共 {len(moment_list)} 个")
        else:
            logger.info("⚠️ [Action-moments] 获取朋友圈列表的Item为空")
        return moment_list

    # 动态 - 朋友圈列表的第n个item，默认为第一个
    def get_moment_item(self, index: int = 0, timeout: int = 2) -> Optional[WebElement]:
        """ 动态 - 朋友圈列表的第n个item，默认为第一个(由0开始索引) """
        moment_list = self.get_visible_moment_items(timeout=timeout)
        if moment_list:
            if index < len(moment_list):
                logger.info(f"🚀 [Action-moments] 获取朋友圈列表的第 {index} 个Item")
                return moment_list[index]
            else:
                logger.warning(f"⚠️ [Action-moments] 获取朋友圈列表请求索引 {index} 越界，列表共有 {len(moment_list)} 个Item")
        else:
            logger.info(f"⚠️ [Action-moments] 获取朋友圈列表的第 {index} 个Item为空")
        return None

    # 动态 - 判断朋友圈列表是否包含图片/视频
    def is_moment_contains_media(self, motype: int = 1, index: int = 0) -> bool:
        """
        动态 - 判断指定朋友圈列表项是否包含图片/视频。
        :param motype: 1=图片 (单图与单个视频公用 IV_SINGLE_PIC，多图使用 IV_MEDIA), 2=视频 (单个视频只有 IV_SINGLE_PIC 单独定位元素)
        :param index: 朋友圈Item项的索引序号，默认为 0 (首条)
        :return: bool 是否包含指定媒体资源
        """
        moment_item = self.get_moment_item(index=index)
        if moment_item is None:
            logger.warning(f"⚠️ [Check-moments] 未找到第 {index} 条朋友圈，无法校验媒体类型 {motype}")
            return False

        single_pic_elems = moment_item.find_elements(*MomentsLocator.IV_SINGLE_PIC)
        multi_pic_elems = moment_item.find_elements(*MomentsLocator.IV_MEDIA)
        has_single_media = len(single_pic_elems) > 0
        has_multi_media = len(multi_pic_elems) > 0

        if motype == 1:
            has_media = has_single_media or has_multi_media
            media_name = "图片"
        elif motype == 2:
            has_media = has_single_media
            media_name = "视频"
        else:
            raise ValueError(f"不支持的朋友圈媒体类型: {motype}")

        if has_media:
            logger.info(f"🔍 [Check-moments] 第 {index} 条朋友圈包含{media_name} (single_pic={has_single_media}, multi_media={has_multi_media})")
        else:
            logger.warning(f"⚠️ [Check-moments] 第 {index} 条朋友圈不包含{media_name} (single_pic={has_single_media}, multi_media={has_multi_media})")
        return has_media

    # 动态 - 点击全文展开或收起
    def click_expand_or_shrink_moment(self, is_expand: bool = True, index: int = 0) -> None:
        """ 动态 - 点击全文展开或收起 """
        logger.info(f"⚙️ [Action-moments] 准备点击第 {index} 个Item展开或收起 (期望 is_expand={is_expand})")
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
                logger.info(f"🚀 [Action-moments] 成功点击了第 {index} 个Item的展开/收起按钮")
                expand_btn.click()
            else:
                logger.info("ℹ️ [Check-moments] 按钮状态与期望一致，无需重复点击")
        else:
            logger.warning(f"⚠️ [Check-moments] 当前页面第 {index} 个Item没有找到展开或收起按钮")

    # 动态 - 获取新消息提醒
    def get_new_message_tips(self, raise_exception: bool = True) -> str:
        """ 动态 - 获取新消息提醒 """
        new_message = self.get_attribute(MomentsLocator.TV_NEW_MESSAGE_TEXT, "text", raise_exception=raise_exception)
        if new_message:
            logger.info(f"🚀 [Action-moments] 获取新消息提醒: {new_message}")
        else:
            logger.warning("⚠️ [Action-moments] 获取新消息提醒为空")
        return new_message

    # 动态 - 点击新消息提醒
    def click_new_message(self, raise_exception: bool = True) -> None:
        """ 动态 - 点击新消息提醒 """
        logger.info("⚙️ [Action-moments] 准备点击新消息提醒")
        if self.is_element_exist(MomentsLocator.TV_NEW_MESSAGE_TEXT, raise_exception=raise_exception):
            logger.info("🚀 [Action-moments] 点击新消息提醒")
            self.click(MomentsLocator.TV_NEW_MESSAGE_TEXT)
        else:
            logger.warning("⚠️ [Action-moments] 未找到新消息提醒")

    # ============================================================================
    # 朋友圈 - 快速发布动态
    # ============================================================================
    # 动态 - 快速发布一条纯文字动态
    def post_text_moment(self, text: str) -> None:
        """ 动态 - 快速发布一条纯文字动态 """
        logger.info(f"⚙️ [Action-moments] 快速发布一条纯文字动态: {text}")
        self.long_press_post_moments(1000)
        self.input_moments_content(text)
        self.click_publish()
    
    # 动态 - 判断朋友圈发布编辑页是否展示
    def is_publish_editor_displayed(self) -> bool:
        """ 动态 - 判断朋友圈发布编辑页是否展示 """
        is_displayed = self.is_element_exist(MomentsLocator.ET_TEXT, timeout=2, raise_exception=False)
        logger.info(f"🔍 [Check-moments] 朋友圈发布编辑页是否展示: {is_displayed}")
        return is_displayed

    # 动态 - 尝试发布空内容，返回是否仍停留在发布编辑页
    def try_publish_empty_moment(self) -> bool:
        """ 动态 - 尝试发布空内容，返回是否仍停留在发布编辑页 """
        logger.info("⚙️ [Action-moments] 尝试发布空内容")
        self.click_post_moments()
        if self.is_element_exist(MomentsLocator.TV_SEND, timeout=1, raise_exception=False):
            logger.info("⚙️ [Action-moments] 点击发送空内容按钮")
            self.click(MomentsLocator.TV_SEND)
            time.sleep(1)
        is_still_editing = self.is_publish_editor_displayed()
        logger.info(f"🔍 [Check-moments] 空内容发表后是否仍停留编辑页: {is_still_editing}")
        return is_still_editing

    # 动态 - 获取第一条动态的正文内容
    def get_first_moment_content(self, except_int: int = 1) -> str:
        """ 动态 - 获取朋友圈第一条动态的正文内容 """
        raise_exception = True if except_int == 1 else False
        content = self.get_attribute(MomentsLocator.TV_CONTENT, 'text', raise_exception=raise_exception)
        if content == "":
            logger.warning("⚠️ [Check-moments] 朋友圈第一条内容为空")
        else:
            logger.info(f"🔍 [Check-moments] 朋友圈第一条内容: {content}")
        return content

    # 动态 - 获取当前页面可见的朋友圈正文内容-Item
    def get_visible_moment_contents_item(self, timeout: int = 2, raise_exception: bool = True) -> list[WebElement]:
        """ 动态 - 获取当前页面可见的朋友圈正文内容-Item """
        content_elems = self.find_elements(MomentsLocator.TV_CONTENT, timeout=timeout, raise_exception=raise_exception)
        if not content_elems:
            logger.warning("⚠️ [Check-moments] 当前页面不可见朋友圈正文内容-Item")
        else:
            logger.info(f"🔍 [Check-moments] 当前可见朋友圈正文内容-Item个数: {len(content_elems)}")
        return content_elems
    
    # 动态 - 获取当前页面可见的朋友圈正文内容列表-Text
    def get_visible_moment_contents(self) -> list[str]:
        """ 动态 - 获取当前页面可见的朋友圈正文内容列表-Text """
        content_elems = self.get_visible_moment_contents_item()
        if not content_elems:
            logger.warning("⚠️ [Check-moments] 当前页面不可见朋友圈正文内容")
            return []
        content_texts = [item.get_attribute('text') for item in content_elems if item]
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈正文内容: {content_texts}")
        return content_texts

    # 动态 - 删除动态
    def delete_moment(self) -> None:
        """ 动态 - 删除动态 """
        logger.info("🚀 [Action-moments] 点击了朋友圈动态的删除按钮")
        self.click(MomentsLocator.TV_DELETE)
        time.sleep(0.5)
    
    # 动态 - 确认删除动态
    def confirm_delete_moment(self) -> None:
        """ 动态 - 确认删除动态 """
        logger.info("🚀 [Action-moments] 点击了删除确认对话框的确定按钮")
        self.click(MomentsLocator.DIALOG_CONFIRM_BTN)
        time.sleep(0.5)

    # 动态 - 取消删除动态
    def cancel_delete_moment(self) -> None:
        """ 动态 - 取消删除动态 """
        logger.info("🚀 [Action-moments] 点击了删除取消对话框的取消按钮")
        self.click(MomentsLocator.DIALOG_CANCEL_BTN)
        time.sleep(0.5)

    # 动态 - 删除自己发布的第一条朋友圈动态并二次确认
    def delete_first_moment(self) -> None:
        """ 动态 - 删除自己发布的第一条朋友圈动态并二次确认 """
        logger.info("🚀 [Action-moments] 准备删除第一条朋友圈动态并二次确认")
        self.delete_moment()
        self.confirm_delete_moment()

    # 动态 - 确认对话框的确认按钮
    def click_ok_dialog(self) -> None:
        """ 动态 - 确认对话框的确认按钮 """
        logger.info("🚀 [Action-moments] 点击了确认对话框的确认按钮")
        self.click(MomentsLocator.DIALOG_OK_BTN)

    # ============================================================================
    # 图片动态 - 发送图片相关
    # ============================================================================
    # 图片动态 - 获取图片element
    def get_photo_elements(self) -> list[WebElement]:
        """ 图片动态 - 获取图片element """
        photo_elements = self.find_elements(MomentsLocator.IV_MEDIA, timeout=2)
        if not photo_elements:
            logger.warning("⚠️ [Check-moments] 当前页面不可见图片")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见图片数量: {len(photo_elements)}")
        return photo_elements
    
    # 图片动态 - 获取第 n 个 element
    def get_photo_element(self, index: int = 0) -> Optional[WebElement]:
        """ 图片动态 - 获取第 n 个 element """
        elements = self.get_photo_elements()
        if index < len(elements):
            photo_element = elements[index]
            logger.info(f"🔍 [Check-moments] 第 {index} 个 element: 存在")
            return photo_element
        logger.warning(f"⚠️ [Check-moments] 第 {index} 个 element: 不存在")
        return None
    
    # 图片动态 - 判断最后一个 element是否存在
    def is_last_photo_element(self) -> bool:
        """ 图片动态 - 判断最后一个 element是否存在 """
        is_last_photo_element = self.is_element_exist(MomentsLocator.RV_PIC_LAST_VIDEO_GROUP, timeout=3)
        if is_last_photo_element:
            logger.info("🔍 [Check-moments] 最后一个 element: 存在")
        else:
            logger.warning("⚠️ [Check-moments] 最后一个 element: 不存在")
        return is_last_photo_element
    
    # 图片动态 - 点击最后一个 element 进行添加图片或视频
    def click_last_photo_element(self) -> None:
        """ 图片动态 - 点击最后一个 element 进行添加图片或视频 """
        logger.info("🚀 [Action-moments] 点击了最后一个 element 进行添加图片或视频")
        self.click(MomentsLocator.RV_PIC_LAST_VIDEO_GROUP)
    
    # 图片动态 - 获取已选择图片的数量
    def get_selected_photo_count(self) -> int:
        """ 图片动态 - 获取已选择图片的数量 """
        count = len(self.get_photo_elements())
        logger.info(f"🔍 [Check-moments] 已选择图片数量: {count}")
        return count

    # ============================================================================
    # 刷新与加载
    # ============================================================================
    # 动态刷新 - 下拉刷新朋友圈列表
    def refresh_moments(self) -> None:
        """ 动态刷新 - 下拉刷新朋友圈列表 """
        logger.info("🚀 [Action-moments] 下拉刷新朋友圈列表")
        self.swipe_page(slid_type="down", duration=300)
        time.sleep(0.5)

    # 动态加载 - 上滑加载更多朋友圈列表
    def load_more_moments(self) -> None:
        """ 动态加载 - 上滑加载更多朋友圈列表 """
        logger.info("🚀 [Action-moments] 上滑加载更多朋友圈列表")
        self.swipe_page(slid_type="up", duration=300)
        time.sleep(0.5)
    
    # 动态加载 - 快速上滑加载最后一条朋友圈动态
    def fast_load_more_moments(self, max_swipes: int = 200) -> bool:
        """ 动态加载 - 快速上滑加载最后一条朋友圈动态 (使用高性能稀疏 DOM 边界检测) """
        logger.info(f"🚀 [Action-moments] 快速上滑加载最后一条朋友圈动态 (最大滑动: {max_swipes})")
        swipe_times = 0
        last_source = ""
        
        while max_swipes > 0:
            if swipe_times > 0 and swipe_times % 10 == 0:
                is_changed, last_source = self.is_page_source_changed(last_source)
                if not is_changed:
                    logger.info(f"✅ [Action-moments] 检测到页面 DOM 无变化，物理边界触底（滑动 {swipe_times} 次），安全终止。")
                    return True
                    
            logger.info(f"🚀 [Action-moments] 快速上滑第 {swipe_times + 1} 次")
            self.swipe_page(slid_type="up", duration=200, x_ratio=0.8)
            swipe_times += 1
            time.sleep(0.8)
            max_swipes -= 1
        return False
    
    # ============================================================================
    # 点赞和评论相关功能
    # ============================================================================
    # 动态点赞 - 获取朋友圈点赞按钮
    def get_like_button_elems(self, timeout: int = 2, raise_exception: bool = False) -> list[WebElement]:
        """ 动态点赞 - 获取朋友圈点赞按钮 """
        like_buttons = self.find_elements(MomentsLocator.TV_LIKE, timeout=timeout, raise_exception=raise_exception)
        if not like_buttons:
            logger.warning("⚠️ [Check-moments] 当前页面不可见朋友圈点赞按钮")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈点赞按钮个数: {len(like_buttons)}")
        return like_buttons

    # 动态点赞 - 为第n条动态点赞，n从0开始，不传默认为0
    def click_like_nth_moment(self, n: int = 0) -> None:
        """ 动态点赞 - 为第n条动态点赞，n从0开始，不传默认为0 """
        logger.info(f"⚙️ [Action-moments] 准备为第 {n + 1} 条动态点赞")
        like_buttons = self.get_like_button_elems()
        if len(like_buttons) <= n:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见第 {n + 1} 条动态的点赞按钮")
            return
        logger.info(f"🚀 [Action-moments] 执行为第 {n + 1} 条动态点赞")
        like_buttons[n].click()

    # 动态点赞 - 获取第n条朋友圈的点赞用户名文本并转化为用户列表
    def get_nth_moment_like_users(self, n: int = 0) -> list[str]:
        """ 动态点赞 - 获取第n条朋友圈的点赞用户名文本并转化为用户列表 """
        moment_item = self.get_moment_item(n)
        if moment_item is None:
            logger.warning(f"⚠️ [Check-moments] 未找到第 {n + 1} 个朋友圈Item，无法获取点赞人列表")
            return []

        like_users_elems = moment_item.find_elements(*MomentsLocator.TV_LIKE_USERNAME)
        if like_users_elems:
            raw_text = "".join([elem.text for elem in like_users_elems if elem.text])
            if not raw_text.strip():
                logger.info(f"🔍 [Check-moments] 第 {n + 1} 条动态点赞人节点文本为空")
                return []
            users = raw_text.split("，")
            logger.info(f"🔍 [Check-moments] 成功获取第 {n + 1} 条动态的点赞用户列表: {users}")
            return users
            
        logger.info(f"🔍 [Check-moments] 第 {n + 1} 条动态当前无点赞用户")
        return []

    # 动态评论 - 输入评论内容
    def send_comment_text(self, comment_text: str) -> None:
        """ 动态评论 - 输入评论内容 """
        logger.info(f"🚀 [Action-moments] 输入评论内容: {comment_text}")
        self.send_keys(MomentsLocator.ET_COMMENT, comment_text)
    
    # 动态评论 - 发送评论
    def send_comment(self) -> None:
        """ 动态评论 - 发送评论 """
        logger.info("🚀 [Action-moments] 发送评论")
        self.click(MomentsLocator.TV_SEND)
    
    # 动态评论 - 输入内容并发送评论
    def post_comment(self, comment_text: str) -> None:
        """ 动态评论 - 输入内容并发送评论 """
        logger.info(f"🚀 [Action-moments] 准备输入内容并发送评论: {comment_text}")
        self.send_comment_text(comment_text)
        self.send_comment()

    # 动态评论 - 获取第n条动态的评论按钮
    def get_comment_button_elems(self, timeout: int = 2) -> list[WebElement]:
        """ 动态评论 - 获取第n条动态的评论按钮 """
        comment_buttons = self.find_elements(MomentsLocator.TV_COMMENT, timeout=timeout)
        if not comment_buttons:
            logger.warning("⚠️ [Check-moments] 当前页面不可见朋友圈评论按钮")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈评论按钮个数: {len(comment_buttons)}")
        return comment_buttons

    # 动态评论 - 为第n条动态发表评论，n从0开始，不传默认为0
    def click_comment_on_nth_moment(self, n: int = 0) -> None:
        """ 动态评论 - 为第n条动态发表评论，n从0开始，不传默认为0 """
        logger.info(f"⚙️ [Action-moments] 准备评论第 {n + 1} 条动态")
        comment_buttons = self.get_comment_button_elems()
        if len(comment_buttons) <= n:
            logger.warning(f"⚠️ [Check-moments] 当前页面不可见第 {n + 1} 条动态的评论按钮")
            return
        logger.info(f"🚀 [Action-moments] 点击评论第 {n + 1} 条动态")
        comment_buttons[n].click()
    
    # 动态评论 - 获取可见评论内容Item
    def get_comment_item_elems(self, timeout: int = 2, raise_exception: bool = True) -> list[WebElement]:
        """ 动态评论 - 获取可见评论内容Item """
        comment_elems = self.find_elements(MomentsLocator.RV_COMMENT_DETAIL, timeout=timeout, raise_exception=raise_exception)
        if not comment_elems:
            logger.warning("⚠️ [Check-moments] 当前页面不可见朋友圈评论内容Item")
            return []
        logger.info(f"🔍 [Check-moments] 当前可见朋友圈评论内容Item个数: {len(comment_elems)}")
        return comment_elems

    # 动态评论 - 获取当前可见评论内容列表
    def get_comment_texts(self, timeout: int = 2, raise_exception: bool = True) -> list[str]:
        """ 动态评论 - 获取当前可见评论内容列表 """
        comment_elems = self.get_comment_item_elems(timeout, raise_exception)
        if not comment_elems:
            return []
        comments = [elem.get_attribute('text') for elem in comment_elems if elem]
        logger.info(f"🔍 [Check-moments] 当前可见评论内容: {comments}")
        return comments

    # 动态评论 - 获取自己发送的评论Item
    def get_own_comment_item(self, comment_text: str, nickname: str = "") -> Optional[WebElement]:
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
    def click_comment_by_text(self, comment_text: str, nickname: str = "") -> None:
        """ 动态评论 - 根据评论内容点击该评论以触发删除菜单（支持昵称组合和防重探测） """
        logger.info(f"⚙️ [Action-moments] 准备根据评论内容点击评论: [{comment_text}]")
        elem = self.get_own_comment_item(comment_text, nickname)
        if elem:
            logger.info(f"🚀 [Action-moments] 点击指定评论: [{comment_text}]")
            elem.click()
            time.sleep(0.5)
        else:
            comment_elems = self.get_comment_item_elems()
            for item in comment_elems:
                text = item.get_attribute('text') or ""
                if comment_text in text:
                    logger.info("⚙️ [Action-moments] 点击候选评论项以探测删除权限")
                    self.click(item)
                    time.sleep(0.5)
                    delete_btn = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("删除")')
                    if self.is_element_exist(delete_btn, timeout=2, raise_exception=False):
                        logger.info("🔍 [Check-moments] 探测到此项为自己发布的评论，保持点击状态")
                        return
                    else:
                        logger.info("🔍 [Check-moments] 探测到此项非自己发送的评论，正在返回重试下一条")
                        self.driver.back()
                        time.sleep(0.5)
            logger.warning("⚠️ [Action-moments] 未能成功探测到属于自己的评论")

    # 动态评论 - 删除自己发布的评论
    def delete_own_comment(self, comment_text: str, nickname: str = "") -> None:
        """ 动态评论 - 删除自己发布的评论 """
        logger.info(f"⚙️ [Action-moments] 准备删除自己发布的评论: [{comment_text}]")
        self.click_comment_by_text(comment_text, nickname)
        time.sleep(0.5)
    
    # 动态评论 - 确认删除评论
    def confirm_delete_comment(self) -> None:
        """ 动态评论 - 确认删除评论 """
        logger.info("🚀 [Action-moments] 点击评论的确定删除按钮")
        self.click(MomentsLocator.DIALOG_CONFIRM_BTN)
        time.sleep(0.5)

    # 动态评论 - 取消删除评论
    def cancel_delete_comment(self) -> None:
        """ 动态评论 - 取消删除评论 """
        logger.info("🚀 [Action-moments] 点击评论的取消删除按钮")
        self.click(MomentsLocator.DIALOG_CANCEL_BTN)
        time.sleep(0.5)

    # 动态评论 - 删除自己发布的评论并二次确认
    def delete_own_comment_with_confirm(self, comment_text: str, nickname: str = "") -> None:
        """ 动态评论 - 删除自己发布的评论并二次确认 """
        logger.info(f"⚙️ [Action-moments] 准备删除自己发布的评论并二次确认: [{comment_text}]")
        self.delete_own_comment(comment_text, nickname)
        self.confirm_delete_comment()
        logger.info(f"🚀 [Action-moments] 成功删除自己发布的评论: [{comment_text}]")

    # ============================================================================
    # 检查
    # ============================================================================
    # 动态 - 检查当前朋友圈首屏可见列表中是否包含指定文字内容的动态
    def has_moment_with_text(self, text: str) -> bool:
        """ 动态 - 检查当前朋友圈首屏可见列表中是否包含指定文字内容的动态 """
        contents = self.get_visible_moment_contents()
        found = any(text in content for content in contents)
        logger.info(f"🔍 [Check-moments] 朋友圈信息流中是否存在包含 [{text}] 的动态: {found}")
        return found

    # ============================================================================
    # 隐私设置-多端校验相关功能
    # ============================================================================
    # 动态 - 设置朋友圈发布时的可见范围
    def set_moment_visibility(self, visibility: str = "public", target_friend: Optional[str] = None, target_tag: Optional[str] = None, is_ex: bool = True) -> None:
        """
        动态 - 设置朋友圈发布时的可见范围
        :param visibility: 可见范围类型: public/公开, private/私密, partial/部分可见, exclude/不给谁看
        :param target_friend: 好友昵称（当选择部分可见或排除可见时需要）
        :param target_tag: 标签名称（当选择部分可见或排除可见，且想按标签选择时需要）
        :param is_ex: 是否为排除可见
        """
        logger.info(f"⚙️ [Action-moments] 设置可见范围: {visibility}, 好友: {target_friend}, 标签: {target_tag}")
        if visibility in ["public", "公开"]:
            logger.info("ℹ️ [Action-moments] 默认公开可见性，跳过隐私设置")
            return

        from pages.common.contact_select_page import ContactSelectPage
        
        # 1. 点击可见范围进入选择页
        logger.info("⚙️ [Action-moments] 点击可见范围入口")
        self.click(MomentsLocator.CL_VISIBLE_USER)
        
        # 2. 根据类型选择
        if visibility in ["private", "私密"]:
            logger.info("🚀 [Action-moments] 设置可见性为：私密")
            self.click(MomentsLocator.CL_PRIVATE)
        elif visibility in ["partial", "部分可见", "exclude", "不给谁看"]:
            is_partial = visibility in ["partial", "部分可见"]
            container = MomentsLocator.LL_PARTIAL_CONTAINER if is_partial else MomentsLocator.LL_EXCLUDE_CONTAINER
            
            logger.info(f"🚀 [Action-moments] 点击{'部分可见' if is_partial else '不给谁看'}")
            self.click(container)
            
            # 选择标签
            if target_tag:
                if is_partial:
                    self.click_partial_select_tag()
                else:
                    self.click_exclude_select_tag()
                logger.info(f"🚀 [Action-moments] 已选择标签: {target_tag}")
            # 选择朋友
            elif target_friend:
                select_btn = MomentsLocator.CL_PARTIAL_SELECT_FRIEND if is_partial else MomentsLocator.CL_EXCLUDE_SELECT_FRIEND
                logger.info("⚙️ [Action-moments] 点击选择朋友按钮")
                self.click(select_btn)
                contact_select = ContactSelectPage(self.driver)
                contact_select.wait_for_contact_select_page_load()
                contact_select.click_contact_by_name(target_friend)
                contact_select.click_fb_action()
                contact_select.click_confirm()
                logger.info(f"🚀 [Action-moments] 已选择好友: {target_friend}")
                
        if is_ex:
            self.click_publish()

    # 动态 - 发布指定可见性的纯文字朋友圈
    def post_moment_with_visibility(self, text: str, visibility: str = "public", target_friend: Optional[str] = None, target_tag: Optional[str] = None, is_ex: bool = True) -> None:
        """ 动态 - 快速发布一条纯文字动态，并指定可见范围 """
        logger.info(f"⚙️ [Action-moments] 发布指定可见性的纯文字动态: {text}")
        self.long_press_post_moments(1000)
        self.input_moments_content(text)
        self.set_moment_visibility(visibility, target_friend, target_tag, is_ex=is_ex)
        if is_ex:
            self.click_publish()
    
    # 动态选项 - 点击部分可见的标签选项
    def click_partial_select_tag(self) -> None:
        """ 动态选项 - 点击部分可见的标签选项 """
        logger.info("🚀 [Action-moments] 点击部分可见的选项")
        self.click(MomentsLocator.CL_PARTIAL_SELECT_TAG)
    
    # 动态选项 - 点击谁不可见的选项
    def click_exclude_select_tag(self) -> None:
        """ 动态选项 - 点击谁不可见的选项 """
        logger.info("🚀 [Action-moments] 点击谁不可见的选项")
        self.click(MomentsLocator.CL_EXCLUDE_SELECT_TAG)

    # 动态选项 - 获取可见范围选项的好友副标题文本
    def get_partial_friend_subtitle(self) -> str:
        """ 动态选项 - 获取可见范围选项的好友副标题文本 """
        subtitle = self.get_attribute(MomentsLocator.TV_PARTIAL_FRIEND_SUBTITLE, "text")
        if subtitle:
            logger.info(f"🔍 [Check-moments] 获取可见范围选项的好友副标题文本: {subtitle}")
        else:
            logger.warning("⚠️ [Check-moments] 未获取可见范围选项的好友副标题文本，请检查是否已选择朋友")
        return subtitle
    
    # 动态选项 - 获取谁不可见的选项的好友副标题文本
    def get_exclude_friend_subtitle(self) -> str:
        """ 动态选项 - 获取谁不可见的选项的好友副标题文本 """
        subtitle = self.get_attribute(MomentsLocator.TV_EXCLUDE_FRIEND_SUBTITLE, "text")
        if subtitle:
            logger.info(f"🔍 [Check-moments] 获取谁不可见的选项的好友副标题文本: {subtitle}")
        else:
            logger.warning("⚠️ [Check-moments] 未获取可见范围选项的好友副标题文本，请检查是否已选择朋友")
        return subtitle

    # 动态选项 - 获取可见范围选项的标题文本
    def get_visible_title_and_friends(self) -> tuple[str, str]:
        """ 动态选项 - 获取可见范围选项的标题和副标题文本 """
        title = self.get_attribute(MomentsLocator.TV_VISIBLE_TITLE, "text")
        subtitle = self.get_attribute(MomentsLocator.TV_VISIBLE_FRIENDS, "text")
        if title and subtitle:
            logger.info(f"🔍 [Check-moments] 获取可见范围选项的标题文本: {title}")
            logger.info(f"🔍 [Check-moments] 获取可见范围选项的副标题文本: {subtitle}")
        else:
            logger.warning("⚠️ [Check-moments] 未获取可见范围选项的标题文本，请检查是否已选择朋友")
        return title, subtitle
    
    # 动态选项 - 获取部分可见范围选项的标题文本
    def get_partial_custom_title_and_subtitle(self) -> tuple[str, str]:
        """ 动态选项 - 获取部分可见范围选项的标题和副标题文本 """
        title = self.get_attribute(MomentsLocator.TV_PARTIAL_TAG_TITLE, "text")
        subtitle = self.get_attribute(MomentsLocator.TV_PARTIAL_TAG_SUBTITLE, "text")
        if title and subtitle:
            logger.info(f"🔍 [Check-moments] 获取部分可见范围选项的标题文本: {title}")
            logger.info(f"🔍 [Check-moments] 获取部分可见范围选项的副标题文本: {subtitle}")
        else:
            logger.warning("⚠️ [Check-moments] 未获取部分可见范围选项的标题文本，请检查是否已选择朋友")
        return title, subtitle

    # 动态选项 - 获取不给谁看（排除可见）选项的标题文本
    def get_exclude_custom_title_and_subtitle(self) -> tuple[str, str]:
        """ 动态选项 - 获取不给谁看（排除可见）选项的标题和副标题文本 """
        title = self.get_attribute(MomentsLocator.TV_EXCLUDE_TAG_TITLE, "text")
        subtitle = self.get_attribute(MomentsLocator.TV_EXCLUDE_TAG_SUBTITLE, "text")
        if title and subtitle:
            logger.info(f"🔍 [Check-moments] 获取不给谁看（排除可见）选项的标题文本: {title}")
            logger.info(f"🔍 [Check-moments] 获取不给谁看（排除可见）选项的副标题文本: {subtitle}")
        else:
            logger.warning("⚠️ [Check-moments] 未获取排除可见选项的标题文本，请检查是否已选择标签")
        return title, subtitle

    # 动态标签页 - 输入搜索框内容
    def input_search_content(self, content: str) -> None:
        """ 动态标签页 - 输入搜索框内容 """
        logger.info(f"🚀 [Action-moments] 输入搜索框内容: {content}")
        self.send_keys(MomentsLocator.ET_SEARCH, content)

    # 动态标签页 - 私有方法 - 确保目标元素可见，若不直接可见则通过搜索过滤使其可见
    def _search_and_filter_tag(self, tag_name: str, target_locator: tuple[str, str], timeout: int = 2) -> bool:
        """ 动态标签页 - 私有方法 - 确保目标元素可见，若不直接可见则通过搜索过滤使其可见 """
        if self.is_element_exist(target_locator, timeout=timeout):
            return True
        logger.info(f"🔍 [Action-moments] 未直接找到标签 {tag_name} 对应元素，尝试输入搜索过滤")
        self.input_search_content(tag_name)
        return self.is_element_exist(target_locator, timeout=3)

    # 动态标签页 - 通过标签名内部的成员数量
    def get_tag_member_count_by_tag_name(self, tag_name: str) -> int:
        """ 动态标签页 - 通过标签名内部的成员数量 """
        import re
        locator = MomentsLocator.get_tag_name_text_by_name(tag_name)
        if self._search_and_filter_tag(tag_name, locator):
            tag_text = self.get_attribute(locator, "text")
            match = re.search(rf"{re.escape(tag_name)}\s*[（(](\d+)[）)]", tag_text)
            if match:
                count = int(match.group(1))
                logger.info(f"🔍 [Check-moments] 获取标签: {tag_text} 的成员数量: {count}")
                return count
        logger.warning(f"⚠️ [Check-moments] 未获取到标签 {tag_name} 的成员数量")
        return 0
    
    # 动态标签页 - 通过标签名称进行点击
    def click_tag_by_name(self, tag_name: str) -> None:
        """ 动态标签页 - 通过标签名称进行点击 """
        logger.info(f"🚀 [Action-moments] 准备点击标签: {tag_name}")
        locator = MomentsLocator.get_tag_name_text_by_name(tag_name)
        if self._search_and_filter_tag(tag_name, locator):
            logger.info(f"🚀 [Action-moments] 执行点击标签: {tag_name}")
            self.click(locator)
        else:
            logger.warning(f"⚠️ [Action-moments] 未找到标签: {tag_name}，无法点击")
    
    # 动态标签页 - 通过标签名称进行点击箭头
    def click_tag_arrow_by_name(self, tag_name: str) -> None:
        """ 动态标签页 - 通过标签名称进行点击箭头 """
        logger.info(f"🚀 [Action-moments] 准备点击标签 {tag_name} 的箭头")
        locator = MomentsLocator.get_tag_more_btn_by_name(tag_name)
        if self._search_and_filter_tag(tag_name, locator):
            logger.info(f"🚀 [Action-moments] 执行点击标签 {tag_name} 的箭头")
            self.click(locator)
        else:
            logger.warning(f"⚠️ [Action-moments] 未找到标签 {tag_name} 的箭头，无法点击")
    
    # 动态标签页 - 获取标签可见的名称列表
    def get_visible_tag_names(self, tag_name: str) -> list[str]:
        """ 动态标签页 - 获取标签可见的朋友名称列表 """
        locator = MomentsLocator.get_tag_friends_by_name(tag_name)
        if self._search_and_filter_tag(tag_name, locator):
            tag_name_text = self.get_attribute(locator, "text")
            if tag_name_text:
                tag_name_list = [name.strip() for name in tag_name_text.split(", ") if name.strip()]
                logger.info(f"🔍 [Check-moments] 获取标签 {tag_name} 的朋友名称列表: {tag_name_list}")
                return tag_name_list
        logger.warning(f"⚠️ [Check-moments] 未获取到标签 {tag_name} 的朋友名称列表")
        return []    
    
    # 动态标签页 - 点击添加按钮
    def click_tag_add_button(self) -> None:
        """ 动态标签页 - 点击添加按钮 """
        logger.info("🚀 [Action-moments] 点击添加按钮")
        self.click(MomentsLocator.TV_ADD)

    # 动态标签页 - 点击删除按钮
    def click_tag_delete_button(self) -> None:
        """ 动态标签页 - 点击删除按钮 """
        logger.info("🚀 [Action-moments] 点击删除按钮")
        self.click(MomentsLocator.TV_REMOVE)
    
    # 动态标签页 - 添加标签好友
    def click_tag_add_friend_button(self, target_friend: Optional[str] = None) -> None:
        """ 动态标签页 - 添加标签好友 """
        logger.info(f"🚀 [Action-moments] 准备添加标签好友: {target_friend}")
        from pages.common.contact_select_page import ContactSelectPage
        contact_select = ContactSelectPage(self.driver)
        contact_select.click_contact_by_name(target_friend)
        contact_select.click_fb_action()
        logger.info(f"🚀 [Action-moments] 已选择好友: {target_friend}")

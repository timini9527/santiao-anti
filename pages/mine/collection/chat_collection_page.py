import time
import datetime
from common.base_page import BasePage
from appium.webdriver.webelement import WebElement
from locators.mine.collection.collection_locator import CollectionLocator
from core.logger_utils import logger, LogIcon
from pages.chat.core.chat_page import ChatPage
from utils.cv_recognition.screenshot_utils import ScreenshotUtils, ImageComparator
from dateutil import parser



class ChatCollectionPage(ChatPage):
    
    # 我的收藏-等待收藏选择页面加载
    def wait_for_collection_page_load(self, timeout: int = 10) -> bool:
        """
        我的收藏-等待收藏选择页加载完成
        Args:
            timeout: 超时时间
        Returns:
            bool: True 表示加载成功，False 表示超时
        """
        logger.info(f"{LogIcon.WAIT} 等待收藏选择页加载完成，超时时间 {timeout} 秒")
        try:
            is_visible = self.is_element_exist(CollectionLocator.TV_COLLECTION_XPATH, timeout=timeout)
            logger.info(f"{LogIcon.SUCCESS} 收藏选择页加载完成, 标题是否显示: {is_visible}")
            return bool(is_visible)
        except Exception as e:
            logger.warning(f"{LogIcon.WARN} 收藏选择页加载超时: {e}")
            return False
 
    # 我的收藏-打开面板进入收藏页面
    def open_panel_enter_collection_page(self) -> None:
        """ 我的收藏-打开面板进入收藏页面 """
        logger.info(f"{LogIcon.ACTION} 点击加号面板并进入我的收藏页面")
        self.click_add_button()
        self.click(CollectionLocator.CHAT_COLLECTION_BUTTON)
        self.wait_for_collection_page_load()
 
    # 我的收藏-获取收藏列表容器
    def get_collection_list_container(self) -> WebElement:
        """ 我的收藏-获取收藏列表容器 """
        list_elem = self.find_element(CollectionLocator.COLL_RECYCLER_VIEW)
        if not list_elem:
            logger.warning(f"{LogIcon.WARN} 未找到收藏列表容器元素")
            return None
        logger.info(f"{LogIcon.SUCCESS} 成功定位到收藏列表容器元素")
        return list_elem
 
    # 我的收藏-获取收藏Item
    def get_collection_items(self, timeout: int = 2, expect_missing: bool = False) -> list[WebElement]:
        """ 我的收藏-获取收藏Item """
        items = self.find_elements(CollectionLocator.COLL_CONTENT_CONTAINER, timeout=timeout, expect_missing=expect_missing)
        if not items and len(items) == 0:
            logger.warning(f"{LogIcon.WARN} 未找到收藏Item元素 (expect_missing={expect_missing})")
            return []
        logger.info(f"{LogIcon.SUCCESS} 成功获取到 {len(items)} 个收藏Item")
        return items
 
    # 我的收藏-获取收藏的文本列表
    def get_collection_texts(self, timeout: int = 2, expect_missing: bool = False) -> list[WebElement]:
        """ 我的收藏-获取收藏的文本列表 """
        texts = self.find_elements(CollectionLocator.COLL_CONTENT_TEXT, timeout=timeout, expect_missing=expect_missing)
        if not texts:
            logger.warning(f"{LogIcon.WARN} 未找到收藏文本元素 (expect_missing={expect_missing})")
            return []
        logger.info(f"{LogIcon.SUCCESS} 成功获取到 {len(texts)} 个收藏的文本")
        return texts 
 
    # 我的收藏-根据索引获取收藏的文本 Element
    def get_collection_text_element(self, index: int = 0) -> WebElement | None:
        """ 我的收藏-根据索引获取收藏的文本 Element """
        text_list = self.get_collection_texts()
        if not text_list:
            return None
        if index >= len(text_list):
            logger.warning(f"{LogIcon.WARN} {index} 越界，当前仅有 {len(text_list)} 条文本")
            return None
        text_elem = text_list[index]
        logger.info(f"{LogIcon.SUCCESS} {index} 条文本 Element")
        return text_elem
    
    # 我的收藏-获取收藏的第 {index} 条文本内容
    def get_collection_text_content(self, index: int = 0) -> str:
        """ 我的收藏-获取收藏的第 {index} 条文本内容 """
        text_elem = self.get_collection_text_element(index)
        if not text_elem:
            logger.warning(f"{LogIcon.WARN} {index} 条文本内容，Element 为 None")
            return ""
        return text_elem.get_attribute('text')
    
    # 我的收藏-点击收藏的第 {index} 条文本
    def get_collection_text_and_click(self, index: int = 0) -> None:
        """ 我的收藏-点击收藏的第 {index} 条文本 """
        logger.info(f"{LogIcon.SETUP} 准备获取并点击第 {index + 1} 条收藏文本")
        text_elem = self.get_collection_text_element(index)
        if not text_elem:
            logger.warning(f"{LogIcon.WARN} 未找到第 {index + 1} 条收藏文本元素")
            return
        logger.info(f"{LogIcon.SUCCESS} 成功定位第 {index + 1} 条收藏文本，执行点击")
        text_elem.click()
 
    # 我的收藏-获取收藏图片列表
    def get_collection_images(self, timeout: int = 2, expect_missing: bool = False) -> list[WebElement]:
        """ 我的收藏-获取收藏图片列表 """
        images = self.find_elements(CollectionLocator.COLL_CONTENT_IMAGE, timeout=timeout, expect_missing=expect_missing)
        if not images:
            logger.warning(f"{LogIcon.WARN} 未找到任何收藏图片元素 (timeout={timeout}s)")
            return []
        logger.info(f"{LogIcon.SUCCESS} 成功获取到 {len(images)} 个收藏图片元素")
        return images 
    
    # 我的收藏-根据索引获取收藏的图片 Element
    def get_collection_image_element(self, index: int = 0) -> WebElement | None:
        """ 我的收藏-根据索引获取收藏的图片 Element """
        images = self.get_collection_images()
        if not images:
            return None
        if index >= len(images):
            logger.warning(f"{LogIcon.WARN} {index} 越界，当前仅有 {len(images)} 张图片")
            return None
        image = images[index]
        logger.info(f"{LogIcon.SUCCESS} {index} 张图片 Element")
        return image
    
    # 我的收藏-点击收藏的第 {index} 张图片
    def get_collection_image_and_click(self, index: int = 0) -> None:
        """ 我的收藏-点击收藏的第 {index} 张图片 """
        logger.info(f"{LogIcon.SETUP} {index} 张图片")
        image = self.get_collection_image_element(index)
        if not image:
            logger.warning(f"{LogIcon.WARN} {index} 张图片，Element 为 None")
            return
        logger.info(f"{LogIcon.SUCCESS} {index} 张图片")
        image.click()
 
    
    # 聊天收藏-获取收藏的用户昵称
    def get_collection_user_nicknames(self) -> list[WebElement]:
        """ 聊天收藏-获取收藏的用户昵称 """
        nicknames = self.find_elements(CollectionLocator.COLL_USER_NICKNAME)
        if not nicknames and len(nicknames) == 0:
            logger.warning(f"{LogIcon.WARN} 未找到收藏的用户昵称列表")
            return []
        logger.info(f"{LogIcon.SUCCESS} 成功获取到 {len(nicknames)} 个收藏的用户昵称")
        return nicknames 
    
    # 聊天收藏-获取收藏的时间
    def get_collection_times(self) -> list[WebElement]:
        """ 聊天收藏-获取收藏的时间 """
        times = self.find_elements(CollectionLocator.COLL_TIME)
        if not times and len(times) == 0:
            logger.warning(f"{LogIcon.WARN} 未找到收藏的时间列表")
            return []
        logger.info(f"{LogIcon.SUCCESS} 成功获取到 {len(times)} 个收藏的时间")
        return times 
    
 
    # 聊天收藏-获取发送收藏面板
    def get_send_collection_panel(self) -> WebElement:
        """ 聊天收藏-获取发送收藏面板 """
        panel = self.find_element(CollectionLocator.CONTENT)
        if not panel:
            logger.warning(f"{LogIcon.WARN} 未找到发送收藏面板容器")
            return None
        logger.info(f"{LogIcon.SUCCESS} 成功获取发送收藏面板容器")
        return panel 
    
    # 聊天收藏-等待确认发送面板
    def wait_for_send_collection_panel(self, timeout: int = 10) -> bool:
        """ 聊天收藏-等待确认发送面板 """
        panel = self.find_element(CollectionLocator.CONTENT_SEND, timeout=timeout)
        if not panel:
            logger.warning(f"{LogIcon.WARN} 等待确认发送收藏面板超时 (timeout={timeout}s)")
            return False
        logger.info(f"{LogIcon.SUCCESS} 确认发送收藏面板已成功出现 (timeout={timeout}s)")
        return True
    
    # 聊天收藏-获取面板头像
    def get_send_collection_panel_avatar(self) -> WebElement:
        """ 聊天收藏-获取面板头像 """
        ava = self.find_element(CollectionLocator.CONTENT_AVATAR)
        if not ava:
            logger.warning(f"{LogIcon.WARN} 未找到发送收藏面板头像元素")
            return None
        logger.info(f"{LogIcon.SUCCESS} 成功获取发送收藏面板头像")
        return ava 
    
    # 聊天收藏-获取面板昵称
    def get_send_collection_panel_nickname(self) -> WebElement:
        """ 聊天收藏-获取面板昵称 """
        nickname = self.find_element(CollectionLocator.CONTENT_NICKNAME_ITEM)
        if not nickname:
            logger.warning(f"{LogIcon.WARN} 未找到发送收藏面板昵称元素")
            return None
        logger.info(f"{LogIcon.SUCCESS} 成功获取发送收藏面板昵称")
        return nickname 
    
    # 聊天收藏-获取面板气泡内容
    def get_send_collection_panel_content(self, col_type: str = "text") -> WebElement:
        """ 聊天收藏-获取面板气泡内容 """
        if col_type == "text":
            locator = CollectionLocator.CONTENT_TEXT_BUBBLE
        elif col_type == "image":
            locator = CollectionLocator.CONTENT_IMAGE_BUBBLE
        else:
            logger.warning(f"{LogIcon.WARN} 不支持的收藏内容类型 col_type: {col_type}")
            return None
        
        content_bubble = self.find_element(locator)

        if not content_bubble:
            logger.warning(f"{LogIcon.WARN} 未找到类型为【{col_type}】的面板气泡内容元素")
            return None
        logger.info(f"{LogIcon.SUCCESS} 成功获取类型为【{col_type}】的面板气泡内容元素")
        return content_bubble 

    # 聊天收藏-获取面板输入框并输入内容
    def send_collection_panel_input(self, text: str) -> None:
        """ 聊天收藏-获取面板输入框并输入内容 """
        logger.info(f"{LogIcon.SUCCESS} 收藏发送面板输入内容: {text}")
        self.send_keys(CollectionLocator.CONTENT_INPUT, text)
    
    # 聊天收藏-点击面板表情按钮
    def click_send_collection_panel_emoji(self) -> None:
        """ 聊天收藏-点击面板表情按钮 """
        logger.info(f"{LogIcon.ACTION} 点击发送收藏面板表情按钮")
        self.click(CollectionLocator.CONTENT_EMOJI, force_wait=True)
    
    # 聊天收藏-点击面板发送按钮
    def click_send_collection_panel_send(self) -> None:
        """ 聊天收藏-点击面板发送按钮 """
        logger.info(f"{LogIcon.ACTION} 点击发送收藏面板发送按钮")
        self.click(CollectionLocator.CONTENT_SEND, force_wait=True)

    # 聊天收藏-点击面板关闭按钮
    def click_send_collection_panel_close(self, force_wait: bool = True) -> None:
        """ 聊天收藏-点击发送面板关闭/取消按钮 """
        logger.info(f"{LogIcon.ACTION} 点击发送收藏面板关闭按钮 (force_wait={force_wait})")
        self.click(CollectionLocator.IV_CLOSE, force_wait=force_wait)
    
    # 聊天收藏-获取面板标题
    def get_send_collection_panel_title(self) -> str:
        """ 聊天收藏-获取面板标题 """
        title = self.get_attribute(CollectionLocator.TV_TITLE, 'text')
        logger.info(f"{LogIcon.FIND} 获取发送收藏面板标题: {title}")
        return title

 
    # 我的收藏-获取收藏页面空状态
    def get_empty_layout(self) -> WebElement:
        """ 我的收藏-获取收藏页面空状态 """
        empty_layout = self.find_element(CollectionLocator.EMPTY_LAYOUT)
        if not empty_layout:
            logger.warning(f"{LogIcon.WARN} 未找到我的收藏页面空状态布局元素")
            return None
        logger.info(f"{LogIcon.SUCCESS} 成功获取我的收藏页面空状态布局元素")
        return empty_layout
 
    # 我的收藏-获取收藏页面空状态文字
    def get_empty_layout_text(self) -> str:
        """ 我的收藏-获取收藏页面空状态文字 """
        empty_layout_text = self.get_attribute(CollectionLocator.EMPTY_LAYOUT_TEXT, 'text')
        if not empty_layout_text:
            logger.warning(f"{LogIcon.WARN} 未获取到我的收藏页面空状态文本内容")
            return ""
        logger.info(f"{LogIcon.SUCCESS} 成功获取我的收藏页面空状态文本: {empty_layout_text}")
        return empty_layout_text
 
    

    # ==================================================================================================
    # 逻辑相关
    # ==================================================================================================
    # 我的收藏-获取收藏图片->Hash
    def get_collection_image_hash(self, index: int = 0) -> str:
        """ 我的收藏-获取收藏图片->Hash """
        image_eles = self.find_elements(CollectionLocator.COLL_CONTENT_IMAGE)
        if index >= len(image_eles) or index < 0:
            logger.warning(f"{LogIcon.WARN} 未找到索引为 {index} 的收藏图片 (当前图片数量: {len(image_eles)})")
            return None
 
        image_ele = image_eles[index]
        logger.info(f"{LogIcon.SUCCESS} 成功定位索引为 {index} 的收藏图片，准备进行 hash 计算")
        return ScreenshotUtils.dhash_auto(element=image_ele)
 
    # 聊天收藏-根据传入的index来选择并点击收藏项
    def select_and_click_collection_item(self, col_type: str = "text", index: int = 0, max_swipes: int = 10) -> str:
        """
        根据类型选择并点击收藏项，支持滑动查找（增强版：支持负数索引、滑动查找、去重、索引兜底）
        :param col_type: 收藏类型 ('text', 'image')
        :param index: 目标索引（0代表第1个，-1代表最后一个）
        :param max_swipes: 最大滑动次数
        :return: 选中项的内容（文本或哈希）
        """
        logger.info(f"{LogIcon.ACTION} 开始查找并点击索引为 {index} 的【{col_type}】类型收藏项 (最大滑动次数: {max_swipes})")
        
        found_items_data = []  
        seen_keys = set()  
        swipes = 0
        last_source = ""
        is_negative_index = index < 0
        
        while swipes <= max_swipes:
            # 1. 检查页面源码是否发生变化（触底判定）
            is_changed, last_source = self.is_page_source_changed(last_source)
            if not is_changed:
                logger.info(f"{LogIcon.SUCCESS} 页面 DOM 已无变化，认定已至边界！")
                break
 
            current_items = self.get_collection_items()
            current_screen_keys = []
 
            for item in current_items:
                nickname = ""
                ctime = ""
                try:
                    nick_el = item.find_elements(*CollectionLocator.COLL_META)
                    time_el = item.find_elements(*CollectionLocator.COLL_TIME)
                    nickname = nick_el[0].get_attribute("text") if nick_el else ""
                    ctime = time_el[0].get_attribute("text") if time_el else ""
                except: pass
                
                target_content = None
                if col_type == "text":
                    res = item.find_elements(*CollectionLocator.COLL_CONTENT_TEXT)
                    if res:
                        target_content = res[0].get_attribute("text")
                elif col_type == "image":
                    res = item.find_elements(*CollectionLocator.COLL_CONTENT_IMAGE)
                    if res:
                        target_content = ScreenshotUtils.dhash_auto(element=res[0])
                
                if target_content is not None:
                    item_key = f"{target_content}_{nickname}_{ctime}"
                    current_screen_keys.append(item_key)
                    
                    if item_key not in seen_keys:
                        seen_keys.add(item_key)
                        found_items_data.append((item, target_content))
                        
                        if not is_negative_index and len(found_items_data) > index:
                            break
            
            if not is_negative_index and len(found_items_data) > index:
                break
                
            logger.info(f"{LogIcon.ACTION} 向下翻页中... (当前累计找到: {len(found_items_data)})")
 
            self.swipe_page(slid_type="up", duration=800)
            swipes += 1
            time.sleep(0.5)
 
        if not found_items_data:
            logger.warning(f"{LogIcon.WARN} 滑动查找结束，未能找到任何类型为【{col_type}】的收藏项")
            return None
        
        if is_negative_index:
            if abs(index) > len(found_items_data):
                logger.warning(f"{LogIcon.WARN} 负数索引 {index} 超出范围，选取第一个条目")
                final_idx = 0
            else:
                final_idx = index
        else:
            if index >= len(found_items_data):
                logger.warning(f"{LogIcon.WARN} 索引 {index} 超出范围，选取最后一个条目(Index {len(found_items_data)-1})")
                final_idx = -1
            else:
                final_idx = index
 
        target_item, result_content = found_items_data[final_idx]
        logger.info(f"{LogIcon.FIND} [Final] 成功定位并点击目标项 (实际列表位置: {final_idx if final_idx >=0 else len(found_items_data)+final_idx})")
        
        target_item.click()
        time.sleep(0.5)
        if self.wait_for_send_collection_panel(timeout=3):
            logger.info(f"{LogIcon.SUCCESS} 点击收藏项后成功等待并打开确认发送面板")
        else:
            logger.warning(f"{LogIcon.WARN} 点击收藏项后未能在超时时间内打开确认发送面板")
            
        return result_content
    
    # 聊天收藏-获取打开 item 后，其面板的内容
    def get_selected_item_panel_content(self, col_type: str = "text") -> str:
        """
        获取打开面板的内容
        :param col_type: 收藏类型，'text', 'image', 'file', 'voice', 'video', 'link'
        :return: 包含面板内容信息的字典
        """
        content = self.get_send_collection_panel_content(col_type=col_type)
        if not content:
            logger.warning(f"{LogIcon.WARN} 获取选中的【{col_type}】类型面板气泡内容失败或为空")
            return None
 
        if col_type == "text":
            content_text = content.get_attribute("text")
            logger.info(f"{LogIcon.SUCCESS} 成功获取选中文本面板内容: {content_text}")
            return content_text
        elif col_type == "image":
            content_image = ScreenshotUtils.dhash_auto(element=content)
            logger.info(f"{LogIcon.SUCCESS} 成功获取选中图片面板计算 Hash: {content_image}")
            return content_image
 
    # 聊天收藏-选择并发送收藏项
    def select_and_send_collection_item(self, index: int = 0, comment: str = None) -> bool:
        """
        选择并发送一个收藏项
        :param index: 收藏项的索引（从0开始）
        :param comment: 留言内容 (可选)
        :return: 是否成功触发发送
        """
        logger.info(f"{LogIcon.ACTION} 准备选择并发送第 {index + 1} 个收藏项 (index={index}, comment={comment})")
        
        # 1. 获取并点击收藏项
        items = self.get_collection_items()
        if not items or len(items) <= index:
            logger.warning(f"{LogIcon.WARN} 收藏列表项不足，无法选择索引为 {index} 的条目 (当前列表项数量: {len(items) if items else 0})")
            return False
        
        logger.info(f"{LogIcon.SETUP} 成功定位并准备点击第 {index + 1} 个收藏项")
        items[index].click()
        
        if comment:
            self.send_collection_panel_input(comment)
        
        self.click_send_collection_panel_send()
        logger.info(f"{LogIcon.SUCCESS} 成功触发第 {index + 1} 个收藏项的确认发送")
        return True
 
    # 聊天收藏-验证图片相似度
    def verify_image_similarity(self, hash1: str, hash2: str, threshold: int = 10) -> bool:
        """
        聊天收藏-验证两个图片的相似度
        :param hash1: 图片1的哈希值
        :param hash2: 图片2的哈希值
        :param threshold: 相似度阈值
        :return: True 表示相似，False 表示不相似
        """
        return ImageComparator.is_hash_similar(hash1, hash2, threshold)

    
    
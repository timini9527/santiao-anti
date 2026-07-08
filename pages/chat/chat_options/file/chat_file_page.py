import allure
import time
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from pages.chat.core.chat_page import ChatPage
from core.logger_utils import logger
from locators.chat.chat_options.file.chat_file_locator import ChatFileLocator
from locators.chat.core.chat_locator import ChatLocator

class ChatFilePage(ChatPage):
    """聊天-文件功能页面对象"""

    # 等待文件选择页面加载
    def wait_for_file_page_load(self, timeout: int = 10) -> bool:
        """
        等待文件选择页加载完成
        Args:
            timeout: 超时时间
        Returns:
            bool: True 表示加载成功，False 表示超时
        """
        logger.info(f"⏳ [Wait] 等待文件选择页加载完成，超时时间 {timeout} 秒")
        try:
            file_page_is_visible = len(self.find_elements(ChatFileLocator.SEARCH_BTN, timeout=timeout))
            logger.info(f"✅ [Wait] 文件选择页加载完成, 元素个数为 {file_page_is_visible}")
            return bool(file_page_is_visible)
        except Exception:
            logger.error(f"❌ [Wait] 文件选择页加载超时")
            return False
    
    # 文件-寻找文件入口并点击
    def enter_file_page(self):
        """寻找文件入口并点击，如当前页未找到则向左滑动面板后点击"""
        if not self.is_element_exist(ChatFileLocator.FILE_ROOT, timeout=2):
            logger.info("🔍 [Action] 当前面板未找到文件按钮，尝试向左滑动快捷面板...")
            self.swip_input_more_page('left')
        self.click(ChatFileLocator.FILE_ROOT, timeout=2)
        logger.info("🚀 [Action] 进入系统文件选择页面")


    # 打开加号面板并点击文件按钮
    def open_panel_enter_file_page(self):
        """打开加号面板并进入文件选择页面"""
        self.click_add_button()
        self.enter_file_page()


    # 点击文件左上角菜单按钮
    def click_file_menu_button(self):
        """
        点击文件左上角菜单按钮
        """
        self.click(ChatFileLocator.DRAWER_MENU_BTN)
        logger.info("🚀 [Action] 点击文件左上角菜单按钮")
        time.sleep(0.5)

    # 获取子菜单、子目录标题
    def get_menu_dir_titles(self) -> list[WebElement]:
        """ 获取菜单子目录标题元素列表 """
        dir_type_list = self.find_elements(ChatFileLocator.FOLDER_NAME, timeout=2, expect_missing=True)
        if not dir_type_list:
            logger.error("❌ [Action] 未获取到菜单子目录标题")
            return []
        logger.info(f"📋 [Action] 获取到菜单子目录标题: {len(dir_type_list)}")
        return dir_type_list
    
    # ==================== 多选状态 ====================
    # 获取多选状态时的关闭按钮
    def get_action_mode_close_button(self) -> WebElement:
        """ 获取多选状态时的关闭按钮 """
        close_button = self.find_element(ChatFileLocator.ACTION_MODE_CLOSE_BUTTON, timeout=2)
        if not close_button:
            logger.error("❌ [Action] 未获取到多选状态时的关闭按钮")
            return None
        logger.info("✅ [Action] 获取到多选状态时的关闭按钮")
        return close_button

    # 点击关闭多选模式的按钮
    def click_action_mode_close_button(self):
        """ 点击关闭多选模式的按钮 """
        self.click(ChatFileLocator.ACTION_MODE_CLOSE_BUTTON)
        logger.info("🚀 [Action] 点击关闭多选模式的按钮")
    
    # 获取多选状态标题
    def get_action_bar_title(self) -> str:
        """ 获取多选状态标题 """
        title = self.get_attribute(ChatFileLocator.ACTION_BAR_TITLE, 'text')
        logger.info(f"🚀 [Action] 获取多选状态标题: {title}")
        return title
    
    # 点击确认/完成按钮
    def click_action_menu_select(self):
        """ 点击确认/完成按钮 """
        self.click(ChatFileLocator.ACTION_MENU_SELECT)
        logger.info("🚀 [Action] 点击确认/完成按钮")

    # 获取多选状态顶部的选择按钮
    def get_top_check_button(self) -> WebElement:
        """ 获取多选状态顶部的选择按钮 """
        select_elem = self.find_element(ChatFileLocator.ACTION_MENU_SELECT, timeout=2)
        if not select_elem:
            logger.error("❌ [Action] 未获取到多选状态顶部的选择按钮")
            return None
        logger.info("✅ [Action] 获取到多选状态顶部的选择按钮")
        return select_elem
    
    # 获取多选状态选择文件左边的勾选按钮
    def get_check_icon(self) -> WebElement:
        """ 获取多选状态选择文件左边的勾选按钮 """
        select_elem = self.find_element(ChatFileLocator.ICON_CHECK, timeout=2)
        if not select_elem:
            logger.error("❌ [Action] 未获取到多选状态选择文件左边的勾选按钮")
            return None
        logger.info("✅ [Action] 获取到多选状态选择文件左边的勾选按钮")
        return select_elem

    
    # ====================  ====================
    # 业务方法
    # ====================  ====================

    # 点击子菜单Item（最近、图片、视频、文档、下载）默认-图片
    def click_sub_menu_item(self, item_name: str = "图片"):
        """
        点击子菜单Item（最近、图片、视频、文档、下载）默认-图片
        Args:
            item_name: 子菜单Item名称
        """
        # 获取菜单子目录标题
        dir_type_list = self.get_menu_dir_titles()
        if dir_type_list:
            for dir_type in dir_type_list:
                if dir_type.text == item_name:
                    dir_type.click()
                    logger.info(f"🚀 [Action] 点击子菜单Item: {item_name}")
                    return
            logger.error(f"❌ [Action] 未找到菜单子目录标题: {item_name}")
            return

    # ==================== 私有通用方法 ====================
    # 在当前目录中查找文件，没有则返回上一级继续查找，默认目录：santiaoTalk
    def _scroll_find_and_click(self, target_name: str, loop_max: int = 10, ignore_case: bool = True) -> bool:
        """
        在当前目录列表中滑动查找并点击目标名称的文件/文件夹（通用私有方法）。
        :param target_name: 目标文件或文件夹名称
        :param loop_max: 最大滑动次数
        :param ignore_case: 是否不区分大小写
        :return: 是否成功找到并点击
        """
        last_source = ""
        target = target_name.lower() if ignore_case else target_name
        for i in range(loop_max):
            elements = self.find_elements(ChatFileLocator.DIR_NAME, timeout=2, expect_missing=True)
            if elements:
                for elem in elements:
                    text = elem.text.lower() if ignore_case else elem.text
                    if target in text:
                        elem.click()
                        logger.info(f"✅ [Action] 文件选择页 - 成功点击: {text}")
                        return True

            # 优化：如果当前页面的元素数量较少（如少于 8 个），或者为空，说明不需要/无法滑动
            if not elements or len(elements) < 8:
                logger.warning(f"🛑 [Action] 文件选择页 - 目录数量较少({len(elements) if elements else 0}个)，无需滑动，未找到: {target_name}")
                break

            # 正常滑动前，先判断页面源码是否变化（防死循环）
            is_changed, last_source = self.is_page_source_changed(last_source)
            if i > 0 and not is_changed:
                logger.warning(f"🛑 [Action] 文件选择页 - 已滑动到底部，仍未找到: {target_name}")
                self.swipe_page_quickly(slid_type='down', duration=300)
                break

            logger.info(f"⏳ [Action] 文件选择页 - 第 {i + 1} 次向下滑动寻找 [{target_name}]...")
            self.swipe_page(slid_type='up', duration=500)
        return False

    # 在当前目录中滑动查找第一个匹配指定后缀名的文件，并返回该元素。
    def find_file_by_suffix(self, suffixes: list[str], loop_max: int = 10) -> list[WebElement]:
        """
        在当前目录中滑动查找第一个匹配指定后缀名的文件，并返回该元素。
        :param suffixes: 文件后缀名列表，如 ['.jpg', '.png', '.webp', '.gif', '.bmp', '.mp3', '.mp4', '.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.rar', '.zip']（不区分大小写，可带点可不带）
        :param loop_max: 最大滑动次数
        :return: 匹配的 WebElement，未找到返回 None
        """
        # 统一格式：后缀以 '.' 开头，并转为小写
        normalized = [s.lower() if s.startswith('.') else f'.{s.lower()}' for s in suffixes]
        logger.info(f"🔍 [Action] 文件选择页 - 按后缀查找文件，目标后缀: {normalized}")

        last_source = ""
        for i in range(loop_max):
            new_elems = []
            elements = self.find_elements(ChatFileLocator.DIR_NAME, timeout=2, expect_missing=True)
            
            if elements:
                for elem in elements:
                    file_text = elem.text.strip().lower()
                    for suffix in normalized:
                        if file_text.endswith(suffix):
                            logger.info(f"✅ [Action] 文件选择页 - 找到匹配文件: {elem.text} (后缀: {suffix})")
                            new_elems.append(elem)
                if new_elems:
                    return new_elems

            # 页面的元素数量较少（如少于 8 个），或者为空，说明不需要/无法滑动
            if not elements or len(elements) < 8:
                logger.warning(f"🛑 [Action] 文件选择页 - 当前数量较少({len(elements) if elements else 0}个)，无需滑动")
                break

            is_changed, last_source = self.is_page_source_changed(last_source)
            if i > 0 and not is_changed:
                logger.warning(f"🛑 [Action] 文件选择页 - 已滑动到底部，仍未找到匹配后缀 {normalized} 的文件")
                break

            logger.info(f"⏳ [Action] 文件选择页 - 第 {i + 1} 次向下滑动寻找后缀 {normalized}...")
            self.swipe_page(slid_type='up', duration=800)

        logger.error(f"❌ [Action] 文件选择页 - 未找到匹配后缀 {normalized} 的文件")
        return None

    # 根据指定的模式从文件列表中选择并点击文件
    def _click_file_by_mode(self, file_elems: list[WebElement], mode: str = "first", index: int = 0) -> bool:
        """根据指定的模式从文件列表中选择并点击文件"""
        if not file_elems:
            return False
            
        target_elem = None
        if mode == "first":
            target_elem = file_elems[0]
        elif mode == "last":
            target_elem = file_elems[-1]
        elif mode == "absolute_last":
            logger.info("⏳ [Action] 模式 absolute_last: 开始滑动到底部获取最后一个文件...")
            
            self.swipe_page_quickly(slid_type='up', duration=500)

            close_elem = self.get_action_mode_close_button()
            if close_elem:
                logger.info(f"✅ [Action] 点击关闭多选模式的按钮: {close_elem.text}")
                close_elem.click()

            bottom_elems = self.find_elements(ChatFileLocator.DIR_NAME, timeout=2, expect_missing=True)
            if bottom_elems:
                logger.info(f"📂 [Action] bottom_elems: 过滤带有 '.' 的文本作为文件特征，避免选到纯文件夹")
                candidate_files = [e for e in bottom_elems if "." in e.text]
                if candidate_files:
                    target_elem = candidate_files[-1]
                    logger.info(f"✅ [Action] 成功选择文件 (模式: {mode}): {target_elem.text}")
                else:
                    logger.error(f"❌ [Action] 未找到带 '.' 的文件")
                    return False
            else:
                logger.error(f"❌ [Action] 未找到文件")
                return False
        elif mode == "index":
            if 0 <= index < len(file_elems):
                target_elem = file_elems[index]
            else:
                logger.warning(f"⚠️ [Action] 索引 {index} 超出范围 (0-{len(file_elems)-1})，默认使用第一个")
                target_elem = file_elems[0]
        else:
            target_elem = file_elems[0]

        logger.info(f"✅ [Action] 成功选择文件 (模式: {mode}): {target_elem.text}")
        target_elem.click()
        return True

    # 递归在当前及深层子目录中寻找并选择文件
    def _search_file_recursively(self, common_suffixes: list[str], loop_max: int, select_mode: str, target_index: int, 
                                    current_depth: int = 1, max_depth: int = 4, ignore_dirs: set = None) -> bool:
        """
        [递归搜索器] 在当前层级及深层嵌套子目录中进行深度优先搜索 (DFS) 以寻找目标文件。

        深度策略说明 (max_depth 限制):
        1. 探测层 1 (如 santiaoTalk/): 检查当前列表是否有匹配后缀的文件。
        2. 探测层 2 (如 子目录/): 若层 1 无文件，则进入第一个未访问子目录继续查找。
        3. 探测层 3 (如 孙目录/): 依此类推，深度递归下钻。
        4. 探测层 4 (如 曾孙目录/): 达到最大深度 max_depth 后停止下钻。
        5. 回溯 (Backtracking): 若某路径搜索失败，自动 back() 返回父目录，尝试搜索下一个兄弟目录。

        注意点:
        - 剪枝逻辑：一旦在某一目录中成功选择文件，递归立即终止并返回 True。
        - 状态恢复：在子目录查找失败后，必须执行 self.back() 以保持页面状态可追溯。

        :param common_suffixes: 允许的文件后缀名列表 (如 ['.jpg', '.pdf'])
        :param loop_max: 每个目录页面的滑动探测最大次数
        :param select_mode: 文件选中模式 ('first', 'last', 'index', 'absolute_last')
        :param target_index: 索引选中模式下的目标索引 (从 0 开始)
        :param current_depth: 当前递归深度 (内部参数，默认 1)
        :param max_depth: 允许递归的最大层级深度 (默认 4)
        :param ignore_dirs: 需要跳过的目录名称集合 (不区分大小写)
        :return: 是否成功在当前及其子树下选中并发送文件
        """
        if current_depth > max_depth:
            return False
            
        if ignore_dirs is None:
            ignore_dirs = set()

        # 1. 尝试在当前目录查找文件
        file_elems = self.find_file_by_suffix(common_suffixes, loop_max=loop_max)
        if file_elems and self._click_file_by_mode(file_elems, select_mode, target_index):
            return True

        # 2. 如果当前目录没有文件，遍历当前可见的目录，递归进入子目录查找
        logger.info(f"🔍 [Action] 当前层级未找到可用文件，尝试进入子目录 (深度: {current_depth})")
        visited_dirs = set(ignore_dirs)
        
        while True:
            elements = self.find_elements(ChatFileLocator.DIR_NAME, timeout=3, expect_missing=True)
            if not elements:
                break

            found_new_dir = False
            for elem in elements:
                dir_text = elem.text
                if not dir_text:
                    continue
                    
                if dir_text.lower() in visited_dirs:
                    continue
                    
                visited_dirs.add(dir_text.lower())
                found_new_dir = True

                # 双重保险：如果是带后缀的文件（说明可能没有被 find_file_by_suffix 匹配到），直接处理
                if any(dir_text.lower().endswith(s) for s in common_suffixes):
                    logger.info(f"✅ [Action] 在当前列表发现文件: {dir_text}，尝试选择")
                    if self._click_file_by_mode([elem], select_mode, target_index):
                        return True
                    continue

                logger.info(f"📂 [Action] 尝试进入深层嵌套目录: [{dir_text}] (深度: {current_depth+1})")
                elem.click()
                time.sleep(0.5)

                # 递归调用进入子目录，深度+1，进入新目录后不需要 ignore_dirs
                if self._search_file_recursively(common_suffixes, loop_max, select_mode, target_index, current_depth + 1, max_depth):
                    return True

                logger.warning(f"⚠️ [Action] 嵌套目录 [{dir_text}] 内未找到，返回上一层")
                self.back()
                break  

            if not found_new_dir:
                break
        return False

    # 在目录中查找并选择任意可用文件：优先进入 santiaoTalk 目录，未找到则回退搜索其他目录
    def select_any_file_in_dir(self, file_type: str = 'image', primary_dir: str = "santiaoTalk", select_mode: str = "first", target_index: int = 0, loop_max: int = 10) -> bool:
        """
        [主入口] 在文件列表中查找并选择任意文件，支持优先目录探测与全量递归扫描。
        业务流程:
        1. 类型过滤：根据 file_type (image/video/audio/document/download) 自动匹配后缀集合。
        2. 优先策略：首先尝试进入 primary_dir 目录，并递归查找其中的文件。
        3. 回退扫描：若优先目录查找失败，则回退至根目录，对所有可见目录进行全局 DFS 探测。
        4. 执行发送：找到文件后，根据 select_mode 策略进行点击，并处理可能的确认对话框。

        :param file_type: 业务文件类型，决定匹配哪些后缀 (image, video, audio, document, download)
        :param primary_dir: 优先查找的目录名称 (默认 "santiaoTalk"，不区分大小写)
        :param select_mode: 文件选中模式 ('first', 'last', 'index', 'absolute_last')
        :param target_index: 针对 'index' 模式的目标索引位置
        :param loop_max: 每一个目录视图内的滑动探测上限
        :return: 最终是否成功完成文件发送
        """
        logger.info(f"🔍 [Action] 文件选择页 - 开始寻找文件，优先目录: [{primary_dir}]，模式: [{select_mode}]")
        
        # 1. 根据文件类型确定后缀
        suffix_map = {
            'image': ['.jpg', '.png', '.webp', '.gif', '.bmp'],
            'video': ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.aac', '.flac', '.m4a'],
            'document': ['.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.xml', '.xmls', '.ppt', '.pptx'],
            'download': ['.apk', '.dmg', '.exe', '.ipa', '.rar', '.zip']
        }
        common_suffixes = suffix_map.get(file_type.lower()) or None
        if common_suffixes is None:
            logger.error(f"❌ 文件类型 [{file_type}] 不支持")
            return False

        # -------- 阶段 1：优先进入 primary_dir 目录查找 --------
        if self._scroll_find_and_click(primary_dir, loop_max=loop_max, ignore_case=True):
            logger.info(f"📂 [Action] 已进入优先目录: {primary_dir}，开始查找文件...")
            # 优先目录内也进行递归查找，防止里面套了层层文件夹
            if self._search_file_recursively(common_suffixes, loop_max, select_mode, target_index, 
                                            current_depth=1, max_depth=3):
                return True

            logger.warning(f"⚠️ [Action] 在 [{primary_dir}] 及其子目录中未找到任何文件，返回上级目录")
            self.back()
        else:
            logger.warning(f"⚠️ [Action] 优先目录 [{primary_dir}] 不存在，跳过")

        # -------- 阶段 2：遍历当前可见的其他目录递归查找 --------
        logger.info("🔍 [Action] 开始在其他目录中进行深度递归寻找文件...")
        # 传入 ignore_dirs={primary_dir.lower()} 以跳过已经找过的优先目录
        if self._search_file_recursively(common_suffixes, loop_max, select_mode, target_index, 
                                            current_depth=1, max_depth=4, ignore_dirs={primary_dir.lower()}):
            return True

        logger.error("❌ [Action] 文件选择页 - 遍历了所有可用目录均未找到可用文件")
        return False

    # 获取最新一条文件气泡的文件名
    def get_last_file_name_in_chat(self) -> str:
        """获取聊天列表最新的一条文件消息的名称"""
        elements = self.find_elements(ChatLocator.FILE_NAME_ITEM, timeout=3, expect_missing=True)
        if elements:
            name = elements[-1].text
            logger.info(f"📋 [Action] 获取到最新发送的文件名: {name}")
            return name
        return ""

    # 点击发送文件按钮（系统文件管理器确认选择后自动返回聊天页）
    def click_send_file(self):
        """
        确认发送文件。
        在系统文件管理器中点击文件后，通常会自动返回聊天页并触发发送。
        此方法用于兼容部分设备需要额外确认的场景。
        """
        logger.info("🚀 [Action] 文件选择完成，等待返回聊天页")
        time.sleep(1)


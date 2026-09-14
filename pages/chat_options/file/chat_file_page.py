import allure
import time
from typing import Optional, Literal
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from pages.chat.core.chat_page import ChatPage
from core.logger_utils import logger
from locators.chat_options.file.chat_file_locator import ChatFileLocator
from locators.chat.core.chat_locator import ChatLocator


class ChatFilePage(ChatPage):
    """聊天-文件功能页面对象"""

    # =======================================================================
    # 1. 页面加载与进入导航 (Page Load & Entry)
    # =======================================================================

    # 等载文件选择页面加载
    def wait_for_file_page_load(self, timeout: int = 10) -> bool:
        """ 等待文件选择页加载完成 """
        logger.info(f"⏳ [Wait] 等待文件选择页加载完成，超时时间 {timeout} 秒")
        try:
            file_page_is_visible = len(self.find_elements(ChatFileLocator.SEARCH_BTN, timeout=timeout))
            logger.info(f"✅ [Wait] 文件选择页加载完成, 元素个数为 {file_page_is_visible}")
            return bool(file_page_is_visible)
        except Exception:
            logger.error("❌ [Wait] 文件选择页加载超时")
            return False

    # 文件-寻找文件入口并点击
    def enter_file_page(self) -> None:
        """寻找文件入口并点击，如当前页未找到则向左滑动面板后点击"""
        logger.info("🔍 [Action] 寻找文件入口...")
        if not self.is_element_exist(ChatFileLocator.FILE_ROOT, timeout=2, raise_exception=False):
            logger.info("🔍 [Action] 当前面板未找到文件按钮，尝试向左滑动快捷面板...")
            self.swip_input_more_page('left', duration=400)
        logger.info("🚀 [Action] 准备点击文件按钮进入系统文件选择页面...")
        self.click(ChatFileLocator.FILE_ROOT, timeout=2)
        logger.info("🚀 [Action] 进入系统文件选择页面完成")

    # 打开加号面板并点击文件按钮
    def open_panel_enter_file_page(self) -> None:
        """打开加号面板并进入文件选择页面"""
        logger.info("🚀 打开加号面板并准备进入文件页面...")
        self.click_add_button()
        self.enter_file_page()


    # =======================================================================
    # 2. 核心业务主入口与调度 (Public Business APIs & Dispatchers)
    # =======================================================================

    # 文件 - 智能切换分类/目录（AOSP 默认【最近】目录，OPPO 默认【文件】导航Tab）
    def switch_to_file_category(self, category_name: str = "最近") -> bool:
        """
        [自适应智能导航] 智能切换至目标文件分类/目录：
        1. OPPO (ColorOS) 模式：直接选择顶部【文件】导航 Tab，若指定了分类卡片则进入对应卡片；
        2. AOSP 原生模式：默认选择【最近】目录文件夹：
           - 实时检测顶部当前目录（get_toolbar_dir_name）；
           - 若当前已处于【最近】（或目标目录），直接复用，免去多余的侧边栏展开与点击；
           - 若当前不在目标目录，则先打开左侧抽屉侧边栏，并点击【最近】（或指定分类目录）。
        """
        logger.info(f"🧭 [Action] 智能切换文件分类/目录: {category_name}...")
        if self.is_oppo_file_manager():
            logger.info("📱 [OPPO ColorOS] 模式：直接选择顶部【文件】导航 Tab")
            file_tab = self.find_element(ChatFileLocator.TAB_FILE, timeout=1)
            if file_tab:
                logger.info("📱 [OPPO ColorOS] 准备点击顶部【文件】导航 Tab...")
                file_tab.click()
                time.sleep(0.2)
            if category_name and category_name not in ("文件", "最近"):
                return self.click_sub_menu_item(category_name)
            return True

        # AOSP 原生模式：默认导航目标为【最近】目录文件夹
        target_nav = "最近" if (category_name in ("最近", "文件") or not category_name) else category_name
        current_dir = self.get_toolbar_dir_name()

        # 如果当前已经处于【最近】或目标目录，直接复用无需多余打开侧边栏
        if current_dir and target_nav in current_dir:
            logger.info(f"📂 [AOSP 原生] 当前已处于目标目录【{current_dir}】，无需打开侧边栏")
            return True

        logger.info(f"🤖 [AOSP 原生] 当前目录为【{current_dir}】，需切换至【{target_nav}】，打开侧边栏")
        return self.click_file_menu_button() and self.click_sub_menu_item(target_nav)

    # 最近页面 / 分类入口：自适应分发
    def get_recently_page_files(self, file_type: str = 'image', sub_menu_item: str = "图片", primary_dir: str = "santiaoTalk", select_mode: str = "first",
                                target_index: int = 0, loop_max: int = 10, timeout: int = 2) -> bool:
        """
        [自适应分发入口] 自动识别当前环境是 OPPO (ColorOS) 还是 AOSP 原生，并调度对应厂商专用函数。
        """
        logger.info(f"🎯 [Dispatcher] 分发获取最近文件: 类型=[{file_type}], 子菜单=[{sub_menu_item}]...")
        if self.is_aosp_file_manager():
            logger.info("🎯 [Dispatcher] 检测到当前为 AOSP / 原生文件管理器，调度 select_file_aosp_by_category")
            return self.select_file_aosp_by_category(
                sub_menu_item=sub_menu_item,
                file_type=file_type,
                select_mode=select_mode,
                target_index=target_index,
                loop_max=loop_max,
                timeout=timeout
            )

        logger.info("🎯 [Dispatcher] 检测到当前为 OPPO (ColorOS) 文件管理器，调度 select_file_oppo_by_category")
        return self.select_file_oppo_by_category(
            sub_menu_item=sub_menu_item,
            file_type=file_type,
            primary_dir=primary_dir,
            select_mode=select_mode,
            target_index=target_index,
            loop_max=loop_max
        )

    # 在文件目录中查找并选择文件
    def select_any_file_in_dir(self, file_type: str = 'image', primary_dir: str = "santiaoTalk", select_mode: str = "first", target_index: int = 0, loop_max: int = 10) -> bool:
        """
        [主入口] 在文件目录中查找并选择文件。自动适配 OPPO【全部文件】与 AOSP 抽屉【内部存储】。
        """
        logger.info(f"🔍 准备在文件目录中查找并选择文件: 类型={file_type}, 目录={primary_dir}...")
        if self.is_oppo_file_manager():
            logger.info("🎯 [Dispatcher] OPPO 环境分发至 select_file_oppo_from_storage")
            return self.select_file_oppo_from_storage(primary_dir=primary_dir, file_type=file_type, select_mode=select_mode, target_index=target_index, loop_max=loop_max)

        logger.info(f"🔍 [AOSP 原生] 开始在目录寻找文件，优先目录: [{primary_dir}]，模式: [{select_mode}]")
        return self._select_file_in_opened_dir(file_type=file_type, primary_dir=primary_dir, select_mode=select_mode, target_index=target_index, loop_max=loop_max)

    # 核心业务方法：通过固定完整文件名搜索并点击发送
    def search_and_select_file_by_name(self, exact_file_name: str, search_timeout: int = 3, select_timeout: int = 3) -> bool:
        """
        [固定文件名搜索模式] 通过顶部搜索栏精准搜索固定文件名并点击选择。
        业务流程:
        1. 点击文件选择页顶部搜索按钮。
        2. 在搜索输入框中输入完整文件名（如 'test_doc.pdf', 'IMG_20260817_142457.jpg'）。
        3. 等待搜索结果列表渲染，并通过完整文件名精确匹配目标条目。
        4. 点击匹配条目，系统自动完成选择并返回聊天页。
        :param exact_file_name: 完整固定文件名（包含扩展名）
        :param search_timeout: 搜索框等待超时时间
        :param select_timeout: 搜索结果条目等待超时时间
        :return: bool: 是否成功精准选中文件
        """
        logger.info(f"🔍 [Action] 开始通过固定文件名精准搜索选择: [{exact_file_name}]")
        # 1. 点击搜索按钮
        if not self.click_file_search_button(timeout=search_timeout):
            return False
        time.sleep(0.5)

        # 2. 输入固定文件名
        if not self.input_search_file_name(exact_file_name, timeout=search_timeout):
            return False
        time.sleep(0.5)

        # 3. 在搜索结果列表中精准查找目标文件
        file_locator = ChatFileLocator.get_file_by_name(exact_file_name)
        target_file = self.find_element(file_locator, timeout=select_timeout)
        if not target_file:
            logger.error(f"❌ [Action] 搜索结果中未找到目标文件: {exact_file_name}")
            return False
        logger.info(f"✅ [Action] 成功精准定位到固定文件: {target_file.text}，准备执行选择...")
        target_file.click()
        return True


    # =======================================================================
    # 3. 跨厂商环境感知与厂商专属实现 (OEM Detection & Implementations)
    # =======================================================================

    # 文件 - 判定当前设备文件管理器系统类型 (AOSP原生 / OPPO / 华为鸿蒙 / 小米 / vivo / 其他)
    def get_file_system_type(self) -> str:
        """
        [跨厂商环境判定] 综合当前 Package 包名与关键特征 DOM 元素，精准识别文件系统厂商类型。
        Returns:
            str: 
                - 'oppo': OPPO / 一加 / Realme (ColorOS / OPlus) 文件管理器
                - 'aosp': Google / AOSP 原生 (DocumentsUI) 文件管理器
                - 'harmonyos': 华为 / 鸿蒙 (HarmonyOS / EMUI) 文件管理器
                - 'xiaomi': 小米 (MIUI / HyperOS) 文件管理器
                - 'vivo': vivo (OriginOS / FuntouchOS) 文件管理器
                - 'other': 其他未知或通用兜底
        """
        logger.info("🔍 判定当前设备文件管理器系统类型...")
        # 1. 优先通过当前 activity/package 包名进行精准判定
        try:
            current_pkg = (getattr(self.driver, "current_package", "") or "").lower()
            if any(k in current_pkg for k in ["documentsui", "android.documentsui", "google.documentsui"]):
                return "aosp"
            if any(k in current_pkg for k in ["coloros", "oplus"]):
                return "oppo"
            if any(k in current_pkg for k in ["huawei.hidisk", "huawei.filemanager", "harmony"]):
                return "harmonyos"
            if any(k in current_pkg for k in ["fileexplorer", "miui"]):
                return "xiaomi"
            if "vivo.filemanager" in current_pkg:
                return "vivo"
        except Exception:
            pass

        # 2. 依据特征 DOM 元素进行二次兜底判定
        if self.is_element_exist(ChatFileLocator.DRAWER_MENU_BTN, timeout=1, raise_exception=False) or \
           self.is_element_exist(ChatFileLocator.TOOLBAR_DIR_NAME, timeout=1, raise_exception=False):
            return "aosp"
        if self.is_element_exist(ChatFileLocator.TAB_FILE, timeout=1, raise_exception=False) or \
           self.is_element_exist(ChatFileLocator.ALL_FILES_ENTRY, timeout=1, raise_exception=False):
            return "oppo"
        return "other"

    # 判断是否为 OPPO 系统文件管理器
    def is_oppo_file_manager(self) -> bool:
        """
        判断当前是否处于 OPPO (ColorOS) 系统文件管理器界面。
        """
        return self.get_file_system_type() == "oppo"

    # 判断是否为 AOSP 原生系统文件管理器
    def is_aosp_file_manager(self) -> bool:
        """
        判断当前是否处于 AOSP 原生 / Google DocumentsUI 系统文件管理器界面。
        """
        return self.get_file_system_type() == "aosp"

    # ------------------- OPPO / ColorOS -------------------
    # OPPO 专属通过分类选择文件
    def select_file_oppo_by_category(self, sub_menu_item: str = "图片", file_type: str = "image", primary_dir: str = "santiaoTalk", select_mode: str = "first", target_index: int = 0, loop_max: int = 10) -> bool:
        """
        [OPPO 专属] 通过主界面分类卡片（图片、视频、音频、文档、下载等）或顶部 Tab 选中文件。
        """
        logger.info(f"📱 [OPPO ColorOS] 开始通过分类选择文件: 分类=[{sub_menu_item}], 类型=[{file_type}], 优先相册/目录=[{primary_dir}], 模式=[{select_mode}]")
        
        # 1. 针对【最近】分类特殊处理
        if sub_menu_item == "最近":
            return self.select_file_oppo_by_recent(file_type, select_mode, target_index, loop_max)
            
        file_tab = self.find_element(ChatFileLocator.TAB_FILE, timeout=1)
        if file_tab:
            logger.info("📱 [OPPO ColorOS] 准备点击顶部【文件】Tab...")
            file_tab.click()

        # 2. 点击对应分类卡片（如 '图片'、'视频'、'音频'、'文档'、'下载'）
        cat_locator = ChatFileLocator.get_recently_page_top_nav_bar(sub_menu_item)
        cat_elem = self.find_element(cat_locator, timeout=2)
        if not cat_elem:
            logger.error(f"❌ [OPPO ColorOS] 未找到分类卡片: {sub_menu_item}")
            return False
        logger.info(f"📱 [OPPO ColorOS] 准备点击进入分类卡片: 【{sub_menu_item}】...")
        cat_elem.click()

        # 3. 复用通用目录探测逻辑
        return self._select_file_in_opened_dir(file_type=file_type, primary_dir=primary_dir, select_mode=select_mode, target_index=target_index, loop_max=loop_max)

    # OPPO 专属在最近列表中选择文件
    def select_file_oppo_by_recent(self, file_type: str = "image", select_mode: str = "first", target_index: int = 0, loop_max: int = 10) -> bool:
        """
        [OPPO 专属] 切换至顶部【最近】Tab 并在最近列表中选择文件。
        """
        logger.info(f"📱 [OPPO ColorOS] 切换至【最近】Tab 选择文件，类型: [{file_type}], 模式: [{select_mode}]")
        recent_tab = self.find_element(ChatFileLocator.TAB_RECENT, timeout=2)
        if recent_tab:
            logger.info("📱 [OPPO ColorOS] 准备点击切换至【最近】Tab...")
            recent_tab.click()
            time.sleep(0.5)

        suffix_map = {
            'image': ['.jpg', '.png', '.webp', '.gif', '.bmp'],
            'video': ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg'],
            'document': ['.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.xml', '.xmls', '.ppt', '.pptx'],
            'download': ['.apk', '.dmg', '.exe', '.ipa', '.rar', '.zip']
        }
        common_suffixes = suffix_map.get(file_type.lower(), ['.jpg', '.png'])

        file_elems = self.find_file_by_suffix(common_suffixes, loop_max=loop_max)
        if file_elems and self._click_file_by_mode(file_elems, select_mode, target_index):
            logger.info("✅ [OPPO ColorOS] 在【最近】Tab 下成功按后缀选中文件")
            return True

        logger.error(f"❌ [OPPO ColorOS] 在【最近】Tab 下未找到匹配后缀的文件: {common_suffixes}")
        return False

    # OPPO 专属从存储目录寻找并选择文件
    def select_file_oppo_from_storage(self, primary_dir: str = "santiaoTalk", file_type: str = "image", select_mode: str = "first", target_index: int = 0, loop_max: int = 10) -> bool:
        """
        [OPPO 专属] 点击【全部文件】进入内部存储树，并进入指定文件夹选择文件。
        """
        logger.info(f"📱 [OPPO ColorOS] 从【全部文件】存储目录寻找: [{primary_dir}]")
        # 1. 确保在【文件】Tab
        file_tab = self.find_element(ChatFileLocator.TAB_FILE, timeout=1)
        if file_tab:
            logger.info("📱 [OPPO ColorOS] 准备点击切换至【文件】Tab...")
            file_tab.click()
            time.sleep(0.3)

        # 2. 点击【全部文件】
        all_files_btn = self.find_element(ChatFileLocator.ALL_FILES_ENTRY, timeout=2)
        if not all_files_btn:
            logger.error("❌ [OPPO ColorOS] 未找到【全部文件】入口")
            return False
        logger.info("📱 [OPPO ColorOS] 准备点击【全部文件】入口...")
        all_files_btn.click()
        time.sleep(1)

        # 3. 复用通用目录探测逻辑
        return self._select_file_in_opened_dir(file_type=file_type, primary_dir=primary_dir, select_mode=select_mode, target_index=target_index, loop_max=loop_max)

    # ------------------- AOSP 原生 -------------------
    # AOSP 原生通过分类选择文件
    def select_file_aosp_by_category(self, sub_menu_item: str = "图片", file_type: str = "image", select_mode: str = "first", 
                                    target_index: int = 0, loop_max: int = 10, timeout: int = 2) -> bool:
        """
        [AOSP 原生专属] 通过智能导航切换至对应分类/目录并在视图中选取发送文件。
        """
        type_nav_map = {
            'image': '图片',
            'video': '视频',
            'audio': '音频',
            'document': '文档',
            'download': '下载',
            'big_file': '大型文件',
            'week': '本周'
        }
        nav_title = sub_menu_item or type_nav_map.get(file_type.lower(), '图片')
        logger.info(f"🤖 [AOSP 原生] 开始通过分类/目录选择文件: 目标=[{nav_title}], 类型=[{file_type}], 模式=[{select_mode}]")

        suffix_map = {
            'image': ['.jpg', '.png', '.webp', '.gif', '.bmp'],
            'video': ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg'],
            'document': ['.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.xml', '.xmls', '.ppt', '.pptx'],
            'download': ['.apk', '.dmg', '.exe', '.ipa', '.rar', '.zip']
        }
        common_suffixes = suffix_map.get(file_type.lower(), ['.jpg', '.png'])

        self.click_recently_page_top_nav_bar(nav_title, timeout=timeout)
        time.sleep(1)

        # 2. 在对应列表中按后缀查找并选中文件
        file_elems = self.find_file_by_suffix(common_suffixes, loop_max=loop_max)
        if file_elems and self._click_file_by_mode(file_elems, select_mode, target_index):
            logger.info(f"✅ [AOSP 原生] 成功通过导航 [{nav_title}] 选中并发送文件")
            return True

        logger.error(f"❌ [AOSP 原生] 在导航 [{nav_title}] 下未找到匹配文件")
        return False


    # =======================================================================
    # 4. 基础 UI 交互原子动作 (Basic UI & Search Actions)
    # =======================================================================

    # 文件 - 获取顶部标题栏上的当前目录/面包屑文本
    def get_toolbar_dir_name(self) -> str:
        """ 获取顶部标题栏上的当前目录/面包屑文本 """
        logger.info("🔍 获取顶部标题栏目录/面包屑文本...")
        dir_name = self.get_attribute(ChatFileLocator.TOOLBAR_DIR_NAME, 'text')
        logger.info(f"🚀 [Action] 获取顶部标题栏上的当前目录/面包屑文本: {dir_name}")
        return dir_name

    # 文件 - 点击文件左上角菜单按钮
    def click_file_menu_button(self) -> bool:
        """ 点击文件左上角抽屉菜单按钮（自适应 AOSP 抽屉模式与 OPPO/ColorOS 卡片平铺模式） """
        logger.info("🔍 准备检测并点击文件左上角抽屉菜单按钮...")
        if self.is_oppo_file_manager():
            logger.info("📱 [Action] 当前设备为 OPPO/ColorOS 卡片模式文件管理器，无需抽屉展开，直接使用界面分类入口")
            return False

        if self.is_element_exist(ChatFileLocator.DRAWER_MENU_BTN, timeout=1, raise_exception=False):
            logger.info("🚀 [Action] 准备点击文件左上角抽屉菜单按钮...")
            self.click(ChatFileLocator.DRAWER_MENU_BTN)
            logger.info("🚀 [Action] 点击文件左上角抽屉菜单按钮完成")
            return True
        return False

    # 文件 - 获取子菜单、子目录标题
    def get_menu_dir_titles(self) -> list[WebElement]:
        """ 获取菜单子目录标题元素列表 """
        logger.info("🔍 获取菜单子目录标题元素列表...")
        dir_type_list = self.find_elements(ChatFileLocator.FOLDER_NAME, timeout=2, expect_missing=True)
        if not dir_type_list:
            logger.error("❌ [Action] 未获取到菜单子目录标题")
            return []
        logger.info(f"📋 [Action] 获取到菜单子目录标题: {len(dir_type_list)}")
        return dir_type_list

    # 文件 - 点击子菜单/分类Item（最近、图片、视频、文档、下载、全部文件）默认-图片
    def click_sub_menu_item(self, item_name: str = "图片") -> bool:
        """ 点击子菜单/分类 Item（自适应 OPPO 卡片直达与 AOSP 抽屉子菜单）"""
        logger.info(f"🔍 准备点击子菜单/分类 Item: {item_name}...")
        # 1. 优先尝试直接在当前页面点击对应名称的卡片/Tab（OPPO ColorOS 模式）
        target_locator = ChatFileLocator.get_recently_page_top_nav_bar(item_name)
        if self.is_element_exist(target_locator, timeout=1, raise_exception=False):
            logger.info(f"🚀 [Action] 准备点击分类卡片/Tab: {item_name}...")
            self.click(target_locator)
            logger.info(f"🚀 [Action] 成功直达点击分类卡片/Tab: {item_name}")
            time.sleep(0.2)
            return True

        # 2. AOSP 抽屉展开后的目录列表查找
        dir_type_list = self.get_menu_dir_titles()
        if dir_type_list:
            for dir_type in dir_type_list:
                if dir_type.text == item_name:
                    logger.info(f"🚀 [Action] 准备在抽屉菜单中点击子菜单Item: {item_name}...")
                    dir_type.click()
                    logger.info(f"🚀 [Action] 抽屉菜单中点击子菜单Item完成: {item_name}")
                    time.sleep(0.2)
                    return True
            logger.error(f"❌ [Action] 抽屉菜单中未找到子目录标题: {item_name}")
            return False
        logger.error(f"❌ [Action] 未找到分类入口: {item_name}")
        return False

    # 点击最近页面顶部导航栏
    def click_recently_page_top_nav_bar(self, item_name: str = "图片", timeout: int = 2) -> bool:
        """ 点击最近页面顶部导航栏 """
        logger.info(f"🔍 检索最近页面顶部导航栏: {item_name}...")
        locator = ChatFileLocator.get_recently_page_top_nav_bar(item_name)
        nav_bar = self.find_element(locator, timeout=timeout)
        if not nav_bar:
            logger.error(f"❌ [Action] 未获取到最近页面顶部导航栏: {item_name}")
            return False
        logger.info(f"🚀 [Action] 准备点击最近页面顶部导航栏: {item_name}...")
        nav_bar.click()
        logger.info(f"🚀 [Action] 点击最近页面顶部导航栏完成: {item_name}")
        return True

    # 点击文件选择页搜索按钮
    def click_file_search_button(self, timeout: int = 2) -> bool:
        """ 点击文件选择页搜索按钮 """
        logger.info("🔍 检索文件选择页搜索按钮...")
        if not self.is_element_exist(ChatFileLocator.SEARCH_BTN, timeout=timeout):
            logger.error("❌ [Action] 未找到搜索按钮")
            return False
        logger.info("🚀 [Action] 准备点击文件选择页搜索按钮...")
        self.click(ChatFileLocator.SEARCH_BTN)
        logger.info("🚀 [Action] 点击文件选择页搜索按钮完成")
        return True

    # 搜索框输入文件名
    def input_search_file_name(self, file_name: str, timeout: int = 2) -> bool:
        """ 在搜索框中输入文件名 """
        logger.info(f"🔍 检索搜索输入框并输入: {file_name}...")
        search_input = self.find_element(ChatFileLocator.SEARCH_INPUT, timeout=timeout)
        if not search_input:
            logger.error("❌ [Action] 未找到搜索输入框")
            return False
        logger.info(f"✍️ [Action] 准备在搜索框中输入文件名: {file_name}...")
        search_input.clear()
        search_input.send_keys(file_name)
        logger.info(f"✍️ [Action] 搜索框输入文件名完成: {file_name}")
        return True


    # =======================================================================
    # 5. 多选模式状态交互 (Action Mode / Multi-select)
    # =======================================================================

    # 文件 - 获取多选状态时的关闭按钮
    def get_action_mode_close_button(self) -> Optional[WebElement]:
        """ 获取多选状态时的关闭按钮 """
        logger.info("🔍 获取多选状态时的关闭按钮...")
        close_button = self.find_element(ChatFileLocator.ACTION_MODE_CLOSE_BUTTON, timeout=2)
        if not close_button:
            logger.error("❌ [Action] 未获取到多选状态时的关闭按钮")
            return None
        logger.info("✅ [Action] 获取到多选状态时的关闭按钮")
        return close_button

    # 文件 - 点击关闭多选模式的按钮
    def click_action_mode_close_button(self) -> None:
        """ 点击关闭多选模式的按钮 """
        logger.info("🚀 [Action] 准备点击关闭多选模式的按钮...")
        self.click(ChatFileLocator.ACTION_MODE_CLOSE_BUTTON)
        logger.info("🚀 [Action] 点击关闭多选模式的按钮完成")

    # 文件 - 获取多选状态标题
    def get_action_bar_title(self) -> str:
        """ 获取多选状态标题 """
        logger.info("🔍 获取多选状态标题...")
        title = self.get_attribute(ChatFileLocator.ACTION_BAR_TITLE, 'text')
        logger.info(f"🚀 [Action] 获取多选状态标题: {title}")
        return title

    # 文件 - 点击确认/完成按钮
    def click_action_menu_select(self) -> None:
        """ 点击确认/完成按钮 """
        logger.info("🚀 [Action] 准备点击确认/完成按钮...")
        self.click(ChatFileLocator.ACTION_MENU_SELECT)
        logger.info("🚀 [Action] 点击确认/完成按钮完成")

    # 文件 - 获取多选状态顶部的选择按钮
    def get_top_check_button(self) -> Optional[WebElement]:
        """ 获取多选状态顶部的选择按钮 """
        logger.info("🔍 获取多选状态顶部的选择按钮...")
        select_elem = self.find_element(ChatFileLocator.ACTION_MENU_SELECT, timeout=2)
        if not select_elem:
            logger.error("❌ [Action] 未获取到多选状态顶部的选择按钮")
            return None
        logger.info("✅ [Action] 获取到多选状态顶部的选择按钮")
        return select_elem

    # 文件 - 获取多选状态选择文件左边的勾选按钮
    def get_check_icon(self) -> Optional[WebElement]:
        """ 获取多选状态选择文件左边的勾选按钮 """
        logger.info("🔍 获取多选状态选择文件左边的勾选按钮...")
        select_elem = self.find_element(ChatFileLocator.ICON_CHECK, timeout=2)
        if not select_elem:
            logger.error("❌ [Action] 未获取到多选状态选择文件左边的勾选按钮")
            return None
        logger.info("✅ [Action] 获取到多选状态选择文件左边的勾选按钮")
        return select_elem


    # =======================================================================
    # 6. 底层私有探测算法与滑动算法 (Private Algorithms & Helpers)
    # =======================================================================

    # 通用当前目录探测方法 (Opened Directory Explorer)
    def _select_file_in_opened_dir(self, file_type: str = "image", primary_dir: str = "santiaoTalk", select_mode: str = "first", target_index: int = 0, loop_max: int = 10) -> bool:
        """
        在当前已打开的目录/分类视图中探测并选择文件：
        1. 若当前视图有匹配后缀文件，直接选择；
        2. 若当前视图是相册/子目录列表，优先尝试进入 primary_dir 目录查找；
        3. 若优先目录未找到，回溯并对其他子目录进行 DFS 深度探测。
        """
        logger.info(f"🔍 [Action] 在打开的目录中探测文件: 类型={file_type}, 目录={primary_dir}...")
        suffix_map = {
            'image': ['.jpg', '.png', '.webp', '.gif', '.bmp', '.jpeg'],
            'video': ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg'],
            'document': ['.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.xml', '.xmls', '.ppt', '.pptx'],
            'download': ['.apk', '.dmg', '.exe', '.ipa', '.rar', '.zip']
        }
        common_suffixes = suffix_map.get(file_type.lower())
        if not common_suffixes:
            logger.error(f"❌ 文件类型 [{file_type}] 不支持")
            return False

        # 1. 尝试直接在当前平铺视图中找文件
        file_elems = self.find_file_by_suffix(common_suffixes, loop_max=loop_max)
        if file_elems and self._click_file_by_mode(file_elems, select_mode, target_index):
            logger.info("✅ [Action] 在当前视图列表中成功按后缀选中文件")
            return True

        # 2. 优先进入 primary_dir 目录探测
        if primary_dir and self._scroll_find_and_click(primary_dir, loop_max=loop_max, ignore_case=True):
            logger.info(f"📂 [Action] 已进入优先目录/相册: {primary_dir}，查找文件...")
            if self._search_file_recursively(common_suffixes, loop_max, select_mode, target_index, current_depth=1, max_depth=3):
                return True
            logger.warning(f"⚠️ [Action] 优先目录 [{primary_dir}] 内未找到可用文件，返回上一层")
            self.back()

        # 3. 回溯并在其他可见目录进行 DFS 递归扫描
        logger.info("🔍 [Action] 开始在其他相册/目录中递归寻找文件...")
        ignore_set = {primary_dir.lower()} if primary_dir else set()
        return self._search_file_recursively(common_suffixes, loop_max, select_mode, target_index, current_depth=1, max_depth=4, ignore_dirs=ignore_set)

    # 递归在当前及深层子目录中寻找并选择文件
    def _search_file_recursively(self, common_suffixes: list[str], loop_max: int, select_mode: str, target_index: int, 
                                 current_depth: int = 1, max_depth: int = 4, ignore_dirs: Optional[set] = None) -> bool:
        """
        [递归搜索器] 在当前层级及深层嵌套子目录中进行深度优先搜索 (DFS) 以寻找目标文件。
        :param common_suffixes: 允许的文件后缀名列表 (如 ['.jpg', '.pdf'])
        :param loop_max: 每个目录页面的滑动探测最大次数
        :param select_mode: 文件选中模式 ('first', 'last', 'index', 'absolute_last')
        :param target_index: 索引选中模式下的目标索引 (从 0 开始)
        :param current_depth: 当前递归深度 (内部参数，默认 1)
        :param max_depth: 允许递归的最大层级深度 (默认 4)
        :param ignore_dirs: 需要跳过的目录名称集合 (不区分大小写)
        :return: 是否成功在当前及其子树下选中并发送文件
        """
        logger.info(f"🔍 [Action] 递归寻找文件 (深度 {current_depth}/{max_depth})...")
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

                logger.info(f"📂 [Action] 准备点击进入深层嵌套目录: [{dir_text}] (深度: {current_depth+1})...")
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

    # 在当前目录中滑动查找第一个匹配指定后缀名的文件，并返回该元素。
    def find_file_by_suffix(self, suffixes: list[str], loop_max: int = 10) -> Optional[list[WebElement]]:
        """
        在当前目录中滑动查找第一个匹配指定后缀名的文件，并返回该元素。
        :param suffixes: 文件后缀名列表，如 ['.jpg', '.png', '.webp', '.gif', '.bmp', '.mp3', '.mp4', '.doc', '.docx', '.xls', '.xlsx', '.pdf', '.txt', '.rar', '.zip']（不区分大小写，可带点可不带）
        :param loop_max: 最大滑动次数
        :return: 匹配的 WebElement 列表，未找到返回 None
        """
        # 统一格式：后缀以 '.' 开头，并转为小写
        normalized = [s.lower() if s.startswith('.') else f'.{s.lower()}' for s in suffixes]
        logger.info(f"🔍 [Action] 文件选择页 - 按后缀查找文件，目标后缀: {normalized}")

        last_source = ""
        for i in range(loop_max):
            new_elems = []
            elements = self.find_elements(ChatFileLocator.DIR_NAME, timeout=3)
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

    # 在当前目录中查找文件，没有则返回上一级继续查找，默认目录：santiaoTalk
    def _scroll_find_and_click(self, target_name: str, loop_max: int = 10, ignore_case: bool = True) -> bool:
        """
        在当前目录列表中滑动查找并点击目标名称的文件/文件夹（通用私有方法）。
        :param target_name: 目标文件或文件夹名称
        :param loop_max: 最大滑动次数
        :param ignore_case: 是否不区分大小写
        :return: 是否成功找到并点击
        """
        logger.info(f"🔍 [Action] 在目录列表中查找并点击: [{target_name}]...")
        last_source = ""
        target = target_name.lower() if ignore_case else target_name
        for i in range(loop_max):
            elements = self.find_elements(ChatFileLocator.DIR_NAME, timeout=2, expect_missing=True)
            if elements:
                for elem in elements:
                    text = elem.text.lower() if ignore_case else elem.text
                    if target in text:
                        logger.info(f"✅ [Action] 找到目标项，准备点击: {text}...")
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

    # 根据指定的模式从文件列表中选择并点击文件
    def _click_file_by_mode(self, file_elems: list[WebElement], mode: str = "first", index: int = 0) -> bool:
        """根据指定的模式从文件列表中选择并点击文件"""
        logger.info(f"🔍 [Action] 根据模式选择文件: 模式={mode}, 索引={index}...")
        if not file_elems:
            return False
            
        target_elem = None
        if mode == "first":
            target_elem = file_elems[0]
        elif mode == "last":
            target_elem = file_elems[-1]
        elif mode == "absolute_last":
            if len(file_elems) <= 6:
                target_elem = file_elems[-1]
                logger.info(f"✅ [Action] 当前文件数量较少({len(file_elems)}个)，无需额外滑动，直接选中最后一个: {target_elem.text}")
            else:
                logger.info("⏳ [Action] 模式 absolute_last: 文件数量较多，开始滑动到底部获取最后一个文件...")
                self.swipe_page_quickly(slid_type='up', duration=300, item_locator=ChatFileLocator.DIR_NAME)

                close_elem = self.get_action_mode_close_button()
                if close_elem:
                    logger.info(f"✅ [Action] 准备点击关闭多选模式的按钮: {close_elem.text}...")
                    close_elem.click()

                bottom_elems = self.find_elements(ChatFileLocator.DIR_NAME, timeout=2, expect_missing=True)
                if bottom_elems:
                    candidate_files = [e for e in bottom_elems if "." in e.text]
                    target_elem = candidate_files[-1] if candidate_files else bottom_elems[-1]
                    logger.info(f"✅ [Action] 成功定位文件 (模式: {mode}): {target_elem.text}")
                else:
                    target_elem = file_elems[-1]
        elif mode == "index":
            if 0 <= index < len(file_elems):
                target_elem = file_elems[index]
            else:
                logger.warning(f"⚠️ [Action] 索引 {index} 超出范围 (0-{len(file_elems)-1})，默认使用第一个")
                target_elem = file_elems[0]
        else:
            target_elem = file_elems[0]

        logger.info(f"✅ [Action] 准备点击选中文件 (模式: {mode}): {target_elem.text}...")
        target_elem.click()
        logger.info(f"✅ [Action] 成功选择文件 (模式: {mode}): {target_elem.text}")
        return True


    # =======================================================================
    # 7. 聊天页面断言与状态获取 (Chat Page Verification Helpers)
    # =======================================================================

    # 获取最新一条文件气泡的文件名
    def get_last_file_name_in_chat(self) -> str:
        """获取聊天列表最新的一条文件消息的名称"""
        logger.info("🔍 获取聊天列表最新一条文件消息的名称...")
        elements = self.find_elements(ChatLocator.FILE_NAME_ITEM, timeout=2, expect_missing=True)
        if elements:
            name = elements[-1].text
            logger.info(f"📋 [Action] 获取到最新发送的文件名: {name}")
            return name
        return ""

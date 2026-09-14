from core.logger_utils import logger
from locators.chat.setting.chat_setting_locator import ChatSettingLocator
from locators.common.common_locator import CommonLocator
from pages.chat.core.chat_page import ChatPage


class ChatSettingPage(ChatPage):
    """单聊设置（聊天信息）页面操作类"""

    # 等待单聊设置页面加载，适用于需要先判断是否存在再进行操作的场景
    def wait_for_setting_page_load(self, timeout: int = 10) -> bool:
        """等待单聊设置页面加载"""
        logger.info("⏳ [Action] ChatSettingPage - 正在等待单聊设置页面加载...")
        res = self.get_attribute(CommonLocator.TOP_TV_TITLE, "text") == "聊天信息"
        logger.info(f"⏳ [Action] ChatSettingPage - 页面加载{'成功' if res else '超时'}")
        return res

    # 获取聊天设置页面标题
    def get_chat_setting_title(self) -> str:
        """获取聊天设置页面标题"""
        logger.info("📖 [Action] ChatSettingPage - 正在获取聊天设置页面标题...")
        title = self.get_attribute(CommonLocator.TOP_TV_TITLE, "text")
        logger.info(f"📖 [Action] ChatSettingPage - 获取聊天设置页面标题: {title}")
        return title

    # 点击返回按钮
    def click_iv_back_button(self) -> None:
        """点击返回按钮"""
        logger.info("🔙 [Action] ChatSettingPage - 准备点击返回按钮...")
        self.click(CommonLocator.TOP_IV_BACK_BTN)
        logger.info("🔙 [Action] ChatSettingPage - 点击返回已完成")

    # ==========================
    # 顶部好友信息区
    # ==========================
    # 点击好友头像
    def click_friend_avatar(self) -> None:
        """点击好友头像"""
        logger.info("⚙️ [Action] ChatSettingPage - 准备点击【好友头像】...")
        self.click(ChatSettingLocator.SETTING_FRIEND_AVATAR)
        logger.info("⚙️ [Action] ChatSettingPage - 点击【好友头像】已完成")

    # 获取聊天对象昵称
    def get_friend_name(self) -> str:
        """获取聊天对象昵称"""
        logger.info("⚙️ [Action] ChatSettingPage - 正在获取聊天对象昵称...")
        nickname = self.get_attribute(ChatSettingLocator.SETTING_FRIEND_NAME, 'text')
        logger.info(f"⚙️ [Action] ChatSettingPage - 获取聊天对象昵称: {nickname}")
        return nickname

    # 点击添加更多朋友(+)以建群
    def click_add_friend(self) -> None:
        """点击添加更多朋友(+)以建群"""
        logger.info("⚙️ [Action] ChatSettingPage - 准备点击【添加更多朋友】...")
        self.click(ChatSettingLocator.SETTING_ADD_FRIEND)
        logger.info("⚙️ [Action] ChatSettingPage - 点击【添加更多朋友】已完成")

    # ==========================
    # 查找与记录操作
    # ==========================
    # 点击查找聊天记录
    def click_search_chat_record(self) -> None:
        """点击查找聊天记录（自适应：群聊快捷【搜索记录】与私聊【查找聊天记录】）"""
        logger.info("🔍 [Action] ChatSettingPage - 准备点击查找聊天记录...")
        if self.is_element_exist(ChatSettingLocator.GROUP_QUICK_SEARCH, timeout=1, raise_exception=False):
            logger.info("🔍 [Action] ChatSettingPage - 准备点击群聊快捷【搜索记录】...")
            self.click(ChatSettingLocator.GROUP_QUICK_SEARCH)
            logger.info("🔍 [Action] ChatSettingPage - 点击群聊快捷【搜索记录】已完成")
        else:
            logger.info("🔍 [Action] ChatSettingPage - 准备点击私聊【查找聊天记录】...")
            self.click(ChatSettingLocator.SEARCH_CHAT_RECORD)
            logger.info("🔍 [Action] ChatSettingPage - 点击私聊【查找聊天记录】已完成")

    # 点击清空聊天记录
    def click_clear_chat_record(self) -> None:
        """点击清空聊天记录"""
        logger.info("🗑️ [Action] ChatSettingPage - 准备滑动并点击【清空聊天记录】...")
        self.swipe_page_quickly(slid_type='up') # 向下滑动到底部
        logger.info("🗑️ [Action] ChatSettingPage - 准备点击清空聊天记录按钮...")
        self.click(ChatSettingLocator.SETTING_CHAT_CLEAR)
        logger.info("🗑️ [Action] ChatSettingPage - 点击【清空聊天记录】已完成")

    # ==========================
    # 开关控制项
    # ==========================
    # 点击置顶聊天
    def click_switch_top(self) -> None:
        """点击置顶聊天（自适应：群聊快捷置顶块 quick_pin 与私聊 CheckBox）"""
        logger.info("🎚️ [Action] ChatSettingPage - 准备点击置顶聊天...")
        if self.is_element_exist(ChatSettingLocator.GROUP_QUICK_PIN, timeout=1, raise_exception=False):
            logger.info("🎚️ [Action] ChatSettingPage - 点击群聊快捷【置顶聊天/取消置顶】")
            self.click(ChatSettingLocator.GROUP_QUICK_PIN)
        else:
            logger.info("🎚️ [Action] ChatSettingPage - 切换私聊【置顶聊天】")
            self.click(ChatSettingLocator.SETTING_TOP_CHAT_BTN, timeout=1)

    # 获取置顶聊天状态
    def get_switch_top_status(self, max_retry: int = 5) -> str:
        """
        获取置顶聊天状态：
        - 群聊快捷置顶块（quick_pin_text）：
          - 文本为 "取消置顶" 时表示已置顶，返回 'true'
          - 文本为 "置顶聊天" 时表示未置顶，返回 'false'
        - 私聊 CheckBox 开关：
          - checked 为 'true' 表示已置顶，'false' 表示未置顶
        """
        logger.info("🚀 [Action] ChatSettingPage - 正在获取置顶聊天状态...")
        status = ''
        while max_retry > 0:
            # 1. 优先检测是否处于群聊设置页快捷置顶区域
            pin_text_elem = self.find_element(ChatSettingLocator.GROUP_QUICK_PIN_TEXT, timeout=1, raise_exception=False)
            if pin_text_elem:
                text = pin_text_elem.text.strip()
                if text == "取消置顶":
                    status = 'true'
                    logger.info(f"🚀[Action] ChatSettingPage - 群聊置顶文本为【{text}】，状态为: true")
                    break
                elif text == "置顶聊天":
                    status = 'false'
                    logger.info(f"🚀[Action] ChatSettingPage - 群聊置顶文本为【{text}】，状态为: false")
                    break

            # 2. 私聊设置页 CheckBox 状态检测
            status = self.get_attribute(ChatSettingLocator.SETTING_TOP_CHAT_BTN, 'checked', raise_exception=False)
            if status in ('true', 'false'):
                logger.info(f"🚀[Action] ChatSettingPage - 私聊获取置顶聊天状态: {status}")
                break

            max_retry -= 1
            if max_retry > 0:
                logger.warning("没有找到 置顶聊天 状态，尝试下滑操作")
                self.swipe_page('up', duration=400)

        logger.info(f"🚀[Action] ChatSettingPage - 最终获取置顶聊天状态: {status}")
        return status

    # 点击消息免打扰
    def click_switch_remind(self) -> None:
        """点击消息免打扰"""
        logger.info("🎚️ [Action] ChatSettingPage - 准备切换【消息免打扰】...")
        self.click(ChatSettingLocator.SETTING_CHAT_REMIND_BTN)
        logger.info("🎚️ [Action] ChatSettingPage - 切换【消息免打扰】已完成")

    # 获取消息免打扰状态
    def get_switch_remind_status(self, max_retry: int = 5) -> str:
        """获取消息免打扰状态"""
        logger.info("🚀 [Action] ChatSettingPage - 正在获取免打扰状态...")
        status = ''
        while max_retry > 0:
            status = self.get_attribute(ChatSettingLocator.SETTING_CHAT_REMIND_BTN, 'checked')
            max_retry -= 1
            if status == '':
                logger.warning("没有找到 免打扰 状态， 尝试下滑操作")
                self.swipe_page('up', duration=400)
            else:
                break
        logger.info(f"🚀[Action] ChatSettingPage - 获取免打扰状态: {status}")
        return status

    # 点击聊天密码
    def click_switch_chat_pwd(self) -> None:
        """点击聊天密码"""
        logger.info("🎚️ [Action] ChatSettingPage - 准备滑动并切换【聊天密码】...")
        self.swipe_page_quickly(slid_type='up')
        logger.info("🎚️ [Action] ChatSettingPage - 准备点击密码开关...")
        self.click(ChatSettingLocator.SETTING_CHAT_PWD_BTN)
        logger.info("🎚️ [Action] ChatSettingPage - 切换【聊天密码】已完成")

    # 获取聊天密码状态
    def get_switch_chat_pwd_status(self, max_retry: int = 5) -> str:
        """获取聊天密码状态"""
        logger.info("🚀 [Action] ChatSettingPage - 正在获取聊天密码状态...")
        status = ''
        while max_retry > 0:
            status = self.get_attribute(ChatSettingLocator.SETTING_CHAT_PWD_BTN, 'checked', raise_exception=False)
            max_retry -= 1
            if status == '':
                logger.warning("没有找到 聊天密码 状态， 尝试下滑操作")
                self.swipe_page('up', duration=400)
            else:
                break
        logger.info(f"🚀[Action] ChatSettingPage - 获取聊天密码状态: {status}")
        return status

    # 点击截屏通知
    def click_switch_screenshot(self) -> None:
        """点击截屏通知"""
        logger.info("🎚️ [Action] ChatSettingPage - 准备滑动并切换【截屏通知】...")
        self.swipe_page_quickly(slid_type='up')
        logger.info("🎚️ [Action] ChatSettingPage - 准备点击截屏通知开关...")
        self.click(ChatSettingLocator.SETTING_CHAT_SCREEN_SHOT_BTN)
        logger.info("🎚️ [Action] ChatSettingPage - 切换【截屏通知】已完成")

    # 获取截屏通知状态
    def get_switch_screenshot_status(self, max_retry: int = 5) -> str:
        """获取截屏通知状态"""
        logger.info("🚀 [Action] ChatSettingPage - 正在获取截屏通知状态...")
        status = ''
        while max_retry > 0:
            status = self.get_attribute(ChatSettingLocator.SETTING_CHAT_SCREEN_SHOT_BTN, 'checked', raise_exception=False)
            max_retry -= 1
            if status == '':
                logger.warning("没有找到 截屏通知 状态， 尝试下滑操作")
                self.swipe_page('up', duration=400)
            else:
                break
        logger.info(f"🚀[Action] ChatSettingPage - 获取截屏通知状态: {status}")
        return status

    # 点击撤回通知
    def click_switch_recall(self) -> None:
        """点击撤回通知"""
        logger.info("🎚️ [Action] ChatSettingPage - 准备滑动并切换【撤回通知】...")
        self.swipe_page_quickly(slid_type='up')
        logger.info("🎚️ [Action] ChatSettingPage - 准备点击撤回通知开关...")
        self.click(ChatSettingLocator.SETTING_CHAT_REVOKE_BTN)
        logger.info("🎚️ [Action] ChatSettingPage - 切换【撤回通知】已完成")

    # 获取撤回通知状态
    def get_switch_recall_status(self, max_retry: int = 5) -> str:
        """获取撤回通知状态"""
        logger.info("🚀 [Action] ChatSettingPage - 正在获取撤回通知状态...")
        status = ''
        while max_retry > 0:
            status = self.get_attribute(ChatSettingLocator.SETTING_CHAT_REVOKE_BTN, 'checked', raise_exception=False)
            max_retry -= 1
            if status == '':
                logger.warning("没有找到 撤回通知 状态， 尝试下滑操作")
                self.swipe_page('up', duration=400)
            else:
                break
        logger.info(f"🚀[Action] ChatSettingPage - 获取撤回通知状态: {status}")
        return status

    # ==========================
    # 其他功能
    # ==========================
    # 点击投诉
    def click_report(self) -> None:
        """点击投诉"""
        logger.info("⚠️ [Action] ChatSettingPage - 准备滑动并点击【投诉】...")
        self.swipe_page_quickly(slid_type='up')
        logger.info("⚠️ [Action] ChatSettingPage - 准备点击投诉按钮...")
        self.click(ChatSettingLocator.SETTING_CHAT_REPORT)
        logger.info("⚠️ [Action] ChatSettingPage - 点击【投诉】已完成")

    # ==========================
    # 二次确认弹窗操作
    # ==========================
    # 点击【确认】按钮
    def click_two_confirm(self) -> None:
        """点击【确认】按钮"""
        logger.info("✅ [Action] ChatSettingPage - 准备点击【确认】...")
        self.click(ChatSettingLocator.TWO_CONFIRM)
        logger.info("✅ [Action] ChatSettingPage - 点击【确认】已完成")

    # 点击【取消】按钮
    def click_two_cancel(self) -> None:
        """点击【取消】按钮"""
        logger.info("❌ [Action] ChatSettingPage - 准备点击【取消】...")
        self.click(ChatSettingLocator.TWO_CANCEL)
        logger.info("❌ [Action] ChatSettingPage - 点击【取消】已完成")

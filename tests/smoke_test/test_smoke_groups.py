import pytest
import allure
import pytest_check as check
import time
from core.logger_utils import logger

from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat.list.chat_list_page import ChatListPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.setting.chat_setting_page import ChatSettingPage
from pages.groups.create.group_create_page import GroupCreatePage
from pages.groups.setting.general.group_setting_page import GroupSettingPage
from pages.groups.setting.qrcode.group_qrcode_page import GroupQrCodePage
from pages.groups.setting.notice.group_notice_page import GroupNoticePage
from pages.groups.setting.manager.group_manager_page import GroupManagerPage
from pages.groups.setting.general.group_avatar_page import GroupAvatarPage
from pages.common.contact_select_page import ContactSelectPage
from pages.common.session_select_page import SessionSelectPage
from pages.chat.core.chat_panel_page import ChatPanelPage
from pages.chat.core.chat_long_press_page import ChatLongPressPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY
from utils.cv_recognition.screenshot_utils import ImageComparator


class BaseSmokeGroupSingle:
    """群聊单端测试基类，收敛 Page 实例化及常用辅助方法"""

    @pytest.fixture(autouse=True)
    def setup_single(self, driver_sender):
        self.mainPage = MainPage(driver_sender)
        self.homePage = HomePage(driver_sender)
        self.groupCreatePage = GroupCreatePage(driver_sender)
        self.groupSettingPage = GroupSettingPage(driver_sender)
        self.groupQrCodePage = GroupQrCodePage(driver_sender)
        self.groupManagerPage = GroupManagerPage(driver_sender)
        self.groupAvatarPage = GroupAvatarPage(driver_sender)
        self.chatPage = ChatPage(driver_sender)
        self.chatListPage = ChatListPage(driver_sender)
        self.contactSelectPage = ContactSelectPage(driver_sender)
        self.chatSettingPage = ChatSettingPage(driver_sender)
        self.groupNoticePage = GroupNoticePage(driver_sender)
        self.selectPage = SessionSelectPage(driver_sender)
        yield
        self.mainPage.go_to_main_page()

    def _open_start_group_chat(self):
        """在首页点击加号并进入发起群聊页面"""
        self.homePage.click_add_button()
        self.homePage.click_start_group_chat()

    def _enter_group_setting(self):
        """进入群详情设置页"""
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)
        self.chatPage.wait_for_chat_page_load(timeout=1, raise_exception=False)
        self.chatPage.click_more_button()
        self.groupSettingPage.wait_for_setting_page_load()


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-群聊模块-创建与公告")
class TestSmokeGroupCreate(BaseSmokeGroupSingle):
    """群聊创建与群公告发布冒烟用例"""

    @allure.story("群聊创建")
    @allure.title("通过首页右上角发起群聊 (小群:2人) - 正常建群流程-状态：已完成")
    def test_group_create_success(self):
        friend_list = [PRIVATE_USER1.name, PRIVATE_USER2.name]
        
        with allure.step("1. 进入发起群聊页面"):
            self._open_start_group_chat()
            
        with allure.step("2. 在通讯录列表中勾选多个好友并完成"):
            self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            for contact in friend_list:
                self.contactSelectPage.click_contact_by_name(contact)
            self.contactSelectPage.click_action_button()
            
        with allure.step("3. 验证是否成功进入了群聊天页面"):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 建群后未能成功进入聊天页面")
        
        with allure.step("4. 验证群聊标题是否包含：(3)"):
            title = self.chatPage.get_top_name()
            check.is_in("(3)", title, f"❌ 群聊标题不包含：(3)")

    @allure.story("群聊创建")
    @allure.title("通过好友发起群聊 - 取消建群流程-状态：已完成")
    def test_create_group_cancel(self):
        with allure.step("1. 进入好友聊天界面"):
            self.chatListPage.enter_session(PRIVATE_USER1.name, match_type="exact")
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 未能成功进入聊天页面")

        with allure.step("2. 在聊天界面点击右上角'...' -> 添加成员"):
            self.chatPage.click_more_button()
            self.chatSettingPage.click_add_friend()

        with allure.step("3. 进入好友选择页后直接返回取消建群"):
            is_select_page = self.contactSelectPage.wait_for_contact_and_group_select_page_load()
            check.is_true(is_select_page, "❌ 未能进入好友选择页")
            self.contactSelectPage.click_back()
            self.contactSelectPage.click_back()

        with allure.step("4. 验证仍停留在原好友单聊页面"):
            is_in_chat = self.chatPage.wait_for_chat_page_load()
            check.is_true(is_in_chat, "❌ 取消建群后未能返回聊天页面")

            title = self.chatPage.get_top_name()
            check.is_in(PRIVATE_USER1.name, title, f"❌ 取消建群后聊天标题不正确，实际标题: {title}")
            check.is_false(self.groupCreatePage.is_chat_group(title), f"❌ 取消建群后不应进入群聊，实际标题: {title}")

    @allure.story("发布群公告")
    @allure.title("发布新群公告 - 取消发布流程-状态：已完成")
    def test_group_publish_notice_cancel(self):
        with allure.step("1. 进入群聊并打开群公告页面"):
            self._enter_group_setting()
            desc = self.groupNoticePage.get_notice_content()

        with allure.step("2. 进入群公告并开启编辑"):
            self.groupSettingPage.click_group_notice()
            self.groupNoticePage.wait_for_notice_page_load()
            if desc != "":
                self.groupNoticePage.click_publish_btn()
                time.sleep(0.5)

        with allure.step("3. 输入待测的群公告内容并点击返回"):
            notice_content = "取消发布公告测试"
            self.groupNoticePage.input_notice_content(notice_content)
            self.groupNoticePage.click_back_button()

        with allure.step("4. 验证公告内容未发生改变并返回主页"):
            current_notice = self.groupNoticePage.get_notice_content()
            check.equal(current_notice, desc, f"❌ 取消保存后，公告内容不应改变，实际为: {current_notice}")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-群聊模块-群管理设置")
class TestSmokeGroupManage(BaseSmokeGroupSingle):
    """群名称、头像、二维码以及成员搜索等日常管理冒烟用例"""

    def _enter_group(self):
        self.chatListPage.enter_chat(GROUP_STRATEGY.name)

    def _open_avatar_select_panel(self):
        self.groupAvatarPage.click_confirm_change_group_avatar()
        self.groupAvatarPage.wait_for_album_dialog()

    @allure.story("保存二维码")
    @allure.title("保存与分享群二维码功能-状态：已完成")
    def test_save_qrcode_success(self):
        with allure.step("1. 进入群聊并记录群名"):
            self._enter_group()
            group_name = self.chatPage.get_group_name()

        with allure.step("2. 进入群设置，并点击群二维码"):
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_qr_code()
            self.groupQrCodePage.wait_for_qrcode_page_load()

        with allure.step("3. 校验群二维码页面基础元素"):
            check.is_true(self.groupQrCodePage.is_qr_card_layout_visible(), "❌ 二维码卡片布局不可见")
            check.is_true(self.groupQrCodePage.is_group_header_visible(), "❌ 群头像未显示")
            check.is_true(self.groupQrCodePage.is_group_code_visible(), "❌ 二维码图片未渲染")
            group_name_on_card = self.groupQrCodePage.get_group_name()
            check.equal(group_name_on_card, group_name, "❌ 二维码卡片上显示的群名称与当前群聊不一致")

        with allure.step("4. 测试保存群二维码到本地"):
            self.groupQrCodePage.click_save_qrcode()
            toast = self.groupQrCodePage.get_toast()
            check.is_in("已保存到相册", toast, "❌ 保存二维码的提示信息有误")

    @allure.story("修改群名称")
    @allure.title("群聊名称修改校验-状态：已完成")
    def test_change_group_name_success(self):
        with allure.step("1. 进入群设置"):
            self._enter_group_setting()
            original_name = self.groupSettingPage.get_group_name_val()

        with allure.step("2. 点击群名并输入新群名"):
            self.groupSettingPage.click_group_name_item()
            new_name = "NewGroupName_" + str(int(time.time()))
            self.groupSettingPage.input_group_name(new_name)
            self.groupSettingPage.click_confirm_button()
            time.sleep(1)

        with allure.step("3. 校验修改后的群名称"):
            current_name = self.groupSettingPage.get_group_name_val()
            check.equal(current_name, new_name, f"❌ 修改群名不一致，预期: {new_name}, 实际: {current_name}")

        with allure.step("4. 环境重置为原始群名"):
            self.groupSettingPage.click_group_name_item()
            self.groupSettingPage.input_group_name(original_name)
            self.groupSettingPage.click_confirm_button()

    @allure.story("修改群头像")
    @allure.title("从相册修改群聊头像成功-状态：已完成")
    def test_modify_group_avatar_success(self):
        with allure.step("1. 进入群详情，并点击群头像进入大图预览"):
            self._enter_group_setting()
            self.groupAvatarPage.click_group_avatar()
            self.groupAvatarPage.wait_group_avatar_page_load()
            old_hash = self.groupAvatarPage.get_group_avatar_hash()

        with allure.step("2. 进入相册选择新头像"):
            self._open_avatar_select_panel()
            self.groupAvatarPage.click_group_avatar_pick_gallery()
            self.groupAvatarPage.wait_album_panel_load()
            self.groupAvatarPage.click_album_image_by_index(index=0)
            toast_text = self.groupAvatarPage.get_toast()
            check.equal("头像更新成功", toast_text, f"❌ 未弹出【头像更新成功】提示,实际:【{toast_text}】")
            self.groupAvatarPage.wait_group_avatar_page_load()

        with allure.step("3. 验证头像是否变更"):
            new_hash = self.groupAvatarPage.get_group_avatar_hash()
            is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
            check.is_false(is_similar, f"❌ 修改前后的群头像哈希相似度过高，群头像可能更新失败。")

        with allure.step("4. 环境重置原头像"):
            self._open_avatar_select_panel()
            self.groupAvatarPage.click_group_avatar_pick_gallery()
            self.groupAvatarPage.wait_album_panel_load()
            self.groupAvatarPage.click_album_image_by_index(index=-1)
            self.groupAvatarPage.wait_group_avatar_page_load()


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-群聊模块-双端协同权限")
class TestSmokeGroupAdminDouble(BaseSmokeGroupSingle):
    """群聊日常管理（禁言、互相加好友、群管理员增删等）冒烟用例"""

    # 重写自有的 setup_method_fixture 保证其在管理页
    @pytest.fixture(autouse=True)
    def setup_method_fixture(self, driver_sender):
        with allure.step("前置准备：进入目标群聊并进入群管理"):
            self.chatListPage.enter_chat(GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupSettingPage.wait_for_setting_page_load()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_page_load()

    def _enter_group_setting_back(self):
        self.chatPage.click_more_button()
        self.groupSettingPage.wait_for_setting_page_load()

    @allure.story("群管理员增删")
    @allure.title("【群管理员】功能正常使用校验-状态：已完成")
    def test_group_manager_functionality(self):
        with allure.step("1. 点击群管理员，并添加管理员"):
            self.groupManagerPage.click_administrators()
            self.groupManagerPage.click_add_admin()

        with allure.step("2. 准备群管理员数据"):
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)

        with allure.step("3. 点击新增群管理员并确认"):
            self.groupManagerPage.click_all_switch(checked_str="false")
            self.groupManagerPage.click_confirm_button()
            self.chatPage.wait_banner_message_disappear()
        
        with allure.step("4. 返回管理员列表，并校验管理员状态"):
            member_names = self.groupManagerPage.get_member_names()
            check.is_in(PRIVATE_USER1.name, member_names, "❌ [Action-groupManagerPage] 添加管理员失败")

        with allure.step("5. 移除管理员"):
            self.groupManagerPage.click_member_by_name(name=PRIVATE_USER1.name)
            self.groupManagerPage.click_sure_button()
            self.groupManagerPage.click_sure_content_button()
            self.chatPage.wait_banner_message_disappear()
            member_names = self.groupManagerPage.get_member_names()
            check.is_not_in(PRIVATE_USER1.name, member_names, "❌ [Action-groupManagerPage] 移除管理员失败")

    @allure.story("禁言开关切换")
    @allure.title("切换【全员禁言】开关状态校验-状态：已完成")
    def test_all_member_mute_toggle(self):
        with allure.step("1. 开启全员禁言"):
            self.groupManagerPage.click_all_member_mute_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()

        with allure.step("2. 回到聊天页面中，并校验全员禁言开启状态"):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('开启全员禁言', cmd_texts, "❌ [Action-groupManagerPage] 全员禁言开关未开启")

        with allure.step("3. 再次点击开关恢复至初始状态"):
            self._enter_group_setting_back()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_page_load()
            self.groupManagerPage.click_all_member_mute_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()

        with allure.step("4. 回到聊天页面中，并校验全员禁言关闭后Banner消息"):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in("关闭全员禁言", cmd_texts, "❌ [Action-groupManagerPage] 全员禁言开关未关闭")

    @allure.story("群成员限制互加好友")
    @allure.title("切换【禁止群成员互相加好友】开关状态校验-状态：已完成")
    def test_un_add_friend_each_other_toggle(self):
        with allure.step("1. 开启禁止群成员互相加好友"):
            self.groupManagerPage.click_un_add_friend_each_other_switch(checked_str='true')
            self.chatPage.wait_banner_message_disappear()

        with allure.step("2. 回到聊天页面中，并校验禁止互相加好友开启状态"):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('开启群内禁止添加好友', cmd_texts, "❌ [Action-groupManagerPage] 禁止群成员互相加好友开关未开启")

        with allure.step("3. 再次点击开关恢复至初始状态"):
            self._enter_group_setting_back()
            self.groupSettingPage.click_group_manager()
            self.groupManagerPage.wait_for_page_load()
            self.groupManagerPage.click_un_add_friend_each_other_switch(checked_str='false')
            self.chatPage.wait_banner_message_disappear()

        with allure.step("4. 回到聊天页面中，并校验关闭后的Banner消息"):
            self.chatPage.back_to_chat_page()
            cmd_texts = self.chatPage.get_cmd_notification_texts(index=-1)
            check.is_in('关闭群内禁止添加好友', cmd_texts, "❌ [Action-groupManagerPage] 禁止群成员互相加好友开关未关闭")


@allure.epic("IM核心功能测试")
@allure.feature("冒烟测试-群聊模块-群机器人")
class TestSmokeGroupBot:
    """群聊机器人状态控制与交互冒烟用例"""

    @pytest.fixture(autouse=True)
    def setup_double(self, driver_sender, driver_receiver):
        from pages.groups.bot.group_bot_page import GroupBotPage
        
        self.mainS = MainPage(driver_sender)
        self.chatListS = ChatListPage(driver_sender)
        self.chatS = ChatPage(driver_sender)
        self.settingS = GroupSettingPage(driver_sender)
        self.botS = GroupBotPage(driver_sender)

        self.mainR = MainPage(driver_receiver)
        self.chatListR = ChatListPage(driver_receiver)
        self.chatR = ChatPage(driver_receiver)
        self.panelR = ChatPanelPage(driver_receiver)
        self.longPressPageR = ChatLongPressPage(driver_receiver)
        
        # 类前置：发送方进入群发言管理
        self.mainS.go_to_main_page()
        self.chatListS.enter_chat(GROUP_STRATEGY.name)
        self.chatS.wait_for_chat_page_load()
        self.chatS.click_more_button()
        self.settingS.wait_for_setting_page_load()
        time.sleep(1)
        self.settingS.click_friend_header()
        self.botS.enter_speech_manage()
        
        # 接收方进入目标聊天
        self.mainR.go_to_main_page()
        self.chatListR.enter_chat(GROUP_STRATEGY.name)
        self.chatR.wait_for_chat_page_load()
        yield
        
        # 后置清理：双端回归主页
        try:
            self.mainS.go_to_main_page()
            self.mainR.go_to_main_page()
        except Exception:
            pass

    @allure.story("关闭机器人发言限制")
    @allure.title("关闭群机器人发言管理总开关后，普通文本功能不再受限-状态：已完成")
    def test_group_bot_disable_speech(self):
        with allure.step("1. 发送方关闭发言管理总开关"):
            self.botS.toggle_speech_manage_switch(enable=False)
            self.botS.click_save()

        with allure.step("2. 接收方发送普通消息成功并上屏"):
            test_msg = "机器人发言总开关关闭测试"
            self.chatR.send_message(test_msg)
            time.sleep(1)
            last_text = self.chatR.get_last_message_text()
            check.equal(last_text, test_msg, "❌ 发言管理关闭后，消息未能发送成功或内容不符")

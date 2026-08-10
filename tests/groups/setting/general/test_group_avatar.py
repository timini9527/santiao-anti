import time
import pytest
import allure
import pytest_check as check
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.groups.setting.general.group_avatar_page import GroupAvatarPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER2, GROUP_STRATEGY
from utils.cv_recognition.screenshot_utils import ImageComparator

@allure.epic('IM核心功能测试')
@allure.feature('群聊模块-通用设置')
class TestGroupAvatar:
    """群头像管理相关测试用例"""
    mainPage: MainPage
    chatPage: ChatPage
    chatListPage: ChatListPage
    groupAvatarPage: GroupAvatarPage

    @pytest.fixture(scope='class', autouse=True)
    def class_setup(self, request, driver_sender):
        """类级别前置：在整个类的所有测试用例运行前，只执行一次"""
        request.cls.mainPage = MainPage(driver_sender)
        request.cls.chatPage = ChatPage(driver_sender)
        request.cls.chatListPage = ChatListPage(driver_sender)
        request.cls.groupAvatarPage = GroupAvatarPage(driver_sender)
        with allure.step('-> [类级前置准备] 进入群详情，并点击群头像进入大图预览 (仅跑一次)'):
            self.chatListPage.enter_chat(session_name=GROUP_STRATEGY.name)
            self.chatPage.click_more_button()
            self.groupAvatarPage.click_group_avatar()
            self.groupAvatarPage.wait_group_avatar_page_load()
        yield
        with allure.step('-> [类级后置清理] 返回主页面 (仅跑一次)'):
            self.mainPage.go_to_main_page()

    def _open_select_panel(self):
        """内部辅助方法：从大图页打开底部选择弹窗，并进入相册"""
        self.groupAvatarPage.click_confirm_change_group_avatar()
        self.groupAvatarPage.wait_for_album_dialog()

    @allure.story('群聊头像设置')
    @allure.title('从相册修改群聊头像成功-状态：已完成')
    @pytest.mark.parametrize('album_image_index', [pytest.param(1, id='选择照片'), pytest.param(0, id='取消选择')])
    def test_change_group_avatar_success(self, album_image_index):
        """验证群主/群成员可以成功从系统相册选取并修改群聊头像"""
        with allure.step('1. 获取修改群头像之前的图像哈希值'):
            old_hash = self.groupAvatarPage.get_group_avatar_hash()
        with allure.step('2. 进入相册'):
            self._open_select_panel()
            self.groupAvatarPage.click_group_avatar_pick_gallery()
            self.groupAvatarPage.wait_album_panel_load()
            if album_image_index == 0:
                self.groupAvatarPage.click_back_to_group_avatar_page()
                time.sleep(0.5)
                new_hash = self.groupAvatarPage.get_group_avatar_hash()
                is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
                check.is_true(is_similar, f'❌ 取消修改群头像后，头像未恢复。old: {old_hash}, new: {new_hash}')
                return
        with allure.step('3. 从系统相册选择第一张照片并等待返回大图页'):
            self.groupAvatarPage.click_album_image_by_index(index=0)
            toast_text = self.groupAvatarPage.get_toast()
            check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示,实际:【{toast_text}】')
            self.groupAvatarPage.wait_group_avatar_page_load()
        with allure.step('4. 获取修改群头像之后的图像哈希值，校验头像是否发生变更'):
            new_hash = self.groupAvatarPage.get_group_avatar_hash()
            is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
            check.is_false(is_similar, f'❌ 修改前后的群头像哈希相似度过高（判定相似），群头像可能更新失败。old: {old_hash}, new: {new_hash}')
        with allure.step('5. 重置环境 (把头像改回最后一张)'):
            self._open_select_panel()
            self.groupAvatarPage.click_group_avatar_pick_gallery()
            self.groupAvatarPage.wait_album_panel_load()
            self.groupAvatarPage.click_album_image_by_index(index=-1)
            toast_text = self.groupAvatarPage.get_toast()
            check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示,实际:【{toast_text}】')
            self.groupAvatarPage.wait_group_avatar_page_load()
            time.sleep(0.5)
            reset_hash = self.groupAvatarPage.get_group_avatar_hash()
            is_similar = ImageComparator.is_hash_similar(old_hash, reset_hash, threshold=10)
            check.is_true(is_similar, f'❌ 重置环境失败，群头像未变回原始状态。old: {old_hash}, reset: {reset_hash}')

    @allure.story('群聊头像设置')
    @allure.title('修改群头像-拍照上传-状态：已完成')
    @pytest.mark.parametrize('photo_index', [pytest.param(1, id='拍照'), pytest.param(2, id='拍照+切换摄像头'), pytest.param(0, id='拍照+取消')])
    def test_change_group_avatar_by_taking_photo(self, photo_index):
        """验证群主/群成员可以成功通过拍照并修改群聊头像"""
        with allure.step('1. 获取修改群头像之前的图像哈希值'):
            old_hash = self.groupAvatarPage.get_group_avatar_hash()
        with allure.step('2. 打开底部选择弹窗，并点击拍照'):
            self._open_select_panel()
            self.groupAvatarPage.click_group_avatar_take_photo()
        with allure.step('3. 拍照并等待返回大图页'):
            self.groupAvatarPage.wait_capture_page_load()
            if photo_index == 1:
                self.groupAvatarPage.click_capture_photo()
            elif photo_index == 2:
                self.groupAvatarPage.click_camera_switch()
                self.groupAvatarPage.click_capture_photo()
            elif photo_index == 0:
                self.groupAvatarPage.click_capture_photo()
                self.groupAvatarPage.click_cancel()
                self.groupAvatarPage.click_capture_back()
            if photo_index != 0:
                self.groupAvatarPage.click_confirm()
                toast_text = self.groupAvatarPage.get_toast()
                check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示,实际:【{toast_text}】')
                self.groupAvatarPage.wait_group_avatar_page_load()
        with allure.step('4. 获取修改群头像之后的图像哈希值，校验头像是否发生变更'):
            new_hash = self.groupAvatarPage.get_group_avatar_hash()
            is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
            if photo_index == 0:
                check.is_true(is_similar, f'❌ 取消修改后头像发生了变化。old: {old_hash}, new: {new_hash}')
            else:
                check.is_false(is_similar, f'❌ 修改前后的群头像哈希非常相似（判定未更新），群头像未能成功更新。old: {old_hash}, new: {new_hash}')
        with allure.step('5. 重置环境 (把头像改回最后一张)'):
            if photo_index == 0:
                pass
            else:
                self._open_select_panel()
                self.groupAvatarPage.click_group_avatar_pick_gallery()
                self.groupAvatarPage.wait_album_panel_load()
                self.groupAvatarPage.click_album_image_by_index(index=-1)
                toast_text = self.groupAvatarPage.get_toast()
                check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示,实际:【{toast_text}】')
                self.groupAvatarPage.wait_group_avatar_page_load()
                reset_hash = self.groupAvatarPage.get_group_avatar_hash()
                is_similar = ImageComparator.is_hash_similar(old_hash, reset_hash, threshold=10)
                check.is_true(is_similar, f'❌ 重置环境失败，群头像未变回原始状态。old: {old_hash}, reset: {reset_hash}')

    @allure.story('群聊头像设置')
    @allure.title('保存群头像到本地相册成功-状态：已完成')
    def test_save_group_avatar_to_album(self):
        """验证用户可以将群聊头像大图成功保存至本地相册"""
        with allure.step('1. 打开底部修改面板，并点击【保存图片】'):
            self._open_select_panel()
            self.groupAvatarPage.click_group_avatar_save_image()
        with allure.step('2. 获取保存成功后的 Toast 提示并做断言'):
            toast_text = self.groupAvatarPage.get_toast()
            check.is_in('已保存到相册', toast_text, f'❌ 未能监听到【已保存到相册】提示, 实际 Toast 为: 【{toast_text}】')
import time
import pytest
import allure
import pytest_check as check
from pages.main.main_page import MainPage
from pages.chat.core.chat_page import ChatPage
from pages.chat.list.chat_list_page import ChatListPage
from pages.groups.setting.general.group_avatar_page import GroupAvatarPage
from strategy.chat.chat_strategy import GROUP_STRATEGY
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
        """内部辅助方法：从大图页打开底部选择弹窗"""
        self.groupAvatarPage.click_confirm_change_group_avatar()
        self.groupAvatarPage.wait_for_album_dialog()

    @allure.story('群聊头像设置')
    @allure.title('从相册修改群聊头像-状态：已完成')
    @pytest.mark.parametrize('action_type, desc', [
        pytest.param('confirm', '从相册选择照片并修改', id='从相册选择照片并修改'),
        pytest.param('cancel', '从相册选择页面取消修改', id='从相册选择页面取消修改')
    ])
    def test_change_group_avatar_success(self, action_type, desc):
        """验证群主/群成员可以从相册选择并修改群头像，或在相册中取消选择"""
        allure.dynamic.title(f'群聊头像设置 - {desc}')
        with allure.step('1. 获取修改群头像之前的图像哈希值'):
            old_hash = self.groupAvatarPage.get_group_avatar_hash()

        with allure.step('2. 进入系统相册'):
            self._open_select_panel()
            self.groupAvatarPage.click_group_avatar_pick_gallery()
            self.groupAvatarPage.wait_album_panel_load()

        if action_type == 'cancel':
            with allure.step('3. 点击相册返回按钮取消选择'):
                self.groupAvatarPage.click_back_to_group_avatar_page()
                self.groupAvatarPage.wait_group_avatar_page_load()
            with allure.step('4. 校验取消修改后群头像未发生改变'):
                new_hash = self.groupAvatarPage.get_group_avatar_hash()
                is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=5)
                check.is_true(is_similar, f'❌ 取消修改群头像后，头像未恢复原样。old: {old_hash}, new: {new_hash}')
            return

        with allure.step('3. 从系统相册选择第一张照片并等待返回大图页'):
            self.groupAvatarPage.click_album_image_by_index(index=0)
            toast_text = self.groupAvatarPage.get_toast()
            check.equal('头像更新成功', toast_text, f'❌ 未弹出【头像更新成功】提示, 实际:【{toast_text}】')
            self.groupAvatarPage.wait_group_avatar_page_load()
        with allure.step('4. 获取修改群头像之后的图像哈希值，校验头像已发生变更'):
            new_hash = self.groupAvatarPage.get_group_avatar_hash()
            is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=5)
            check.is_false(is_similar, f'❌ 修改前后的群头像哈希相似度过高，群头像未能成功更新。old: {old_hash}, new: {new_hash}')


    @allure.story('群聊头像设置')
    @allure.title('修改群头像-拍照上传-状态：已完成')
    @pytest.mark.parametrize('photo_mode, desc', [
        pytest.param('capture', '直接拍照修改头像', id='直接拍照修改头像'),
        pytest.param('switch_camera', '切换摄像头后拍照修改头像', id='切换摄像头后拍照修改头像'),
        pytest.param('cancel', '拍照后取消修改', id='拍照后取消修改')
    ])
    def test_change_group_avatar_by_taking_photo(self, photo_mode, desc):
        """验证群主/群成员可以通过拍照修改群聊头像，或在拍照后放弃修改"""
        allure.dynamic.title(f'群聊头像设置 - {desc}')
        with allure.step('1. 获取修改群头像之前的图像哈希值'):
            old_hash = self.groupAvatarPage.get_group_avatar_hash()

        with allure.step('2. 打开底部选择弹窗，并点击拍照'):
            self._open_select_panel()
            self.groupAvatarPage.click_group_avatar_take_photo()
            self.groupAvatarPage.wait_capture_page_load()

        if photo_mode == 'cancel':
            with allure.step('3. 拍照并点击取消，退出拍照页面'):
                self.groupAvatarPage.click_capture_photo()
                self.groupAvatarPage.click_cancel()
                self.groupAvatarPage.click_capture_back()
                self.groupAvatarPage.wait_group_avatar_page_load()
            with allure.step('4. 校验取消修改后头像未发生改变'):
                new_hash = self.groupAvatarPage.get_group_avatar_hash()
                is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=10)
                check.is_true(is_similar, f'❌ 取消拍照修改后头像发生异常变化。old: {old_hash}, new: {new_hash}')
            return

        with allure.step(f'3. 执行拍照流程【{desc}】并确认修改'):
            if photo_mode == 'switch_camera':
                self.groupAvatarPage.click_camera_switch()
            self.groupAvatarPage.click_capture_photo()
            self.groupAvatarPage.click_confirm()
            toast_state = self.groupAvatarPage.get_toast('头像更新成功', timeout=5)
            check.is_true(toast_state, f'❌ 未弹出【头像更新成功】提示')
            self.groupAvatarPage.wait_group_avatar_page_load()
        with allure.step('4. 获取修改后的图像哈希值，校验头像已成功发生物理变更'):
            new_hash = self.groupAvatarPage.get_group_avatar_hash()
            is_similar = ImageComparator.is_hash_similar(old_hash, new_hash, threshold=5)
            check.is_false(is_similar, f'❌ 修改前后的群头像哈希相似度过高，群头像未能成功更新。old: {old_hash}, new: {new_hash}')


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
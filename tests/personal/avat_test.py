import time
import pytest
import allure
from pytest_check import check
from core.logger_utils import logger
from pages.personal.avat_page import AvatarPage

@pytest.mark.usefixtures('enter_personal_info')
@allure.epic('IM核心功能测试')
@allure.feature('个人信息模块-头像')
@allure.story('上传头像断言')
class TestAvatar:

    @pytest.fixture(autouse=True)
    def setup_test(self, driver_sender):
        """
        每个测试类开始前，自动获取 avatarPage 实例并绑定到 self
        这样下面的方法就不需要反复传参了
        """
        self.avatarPage = AvatarPage(driver_sender)
        self.pre_avatar = self.avatarPage.get_avatar_data()
        self.avatarPage.click_avatar()
        self.avatarPage.click_right_top_button()

    def _photo1_4(self):
        self.avatarPage.take_photos_1()
        self.avatarPage.photo_img_center()

    def _photo5_8(self):
        self.avatarPage.take_photos_1()
        self.avatarPage.photo_img_right1()
        self.avatarPage.photo_img_center()

    def _select_image(self):
        self.avatarPage.take_select_photo()
        elems_imgs_nums, nums = self.avatarPage.count_photos()
        self.avatarPage.sj_select_image(elems_imgs_nums, nums)
        return (elems_imgs_nums, nums)

    def upload_assert(self):
        """ 上传头像断言 """
        aIdAfter = self.avatarPage.wait_for_avatar_update(self.aIdPre)
        assert self.aIdPre != aIdAfter, f'更新头像失败, 上传前为: {self.aIdPre}, 上传后为: {aIdAfter}'

    @pytest.mark.skip(reason='跳过')
    @allure.story('头像后置拍照')
    def test_photo_1(self):
        self._photo1_4()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_photo_2(self):
        self._photo1_4()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_back()
        self.avatarPage.take_photos_1_retry()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_photo_3(self):
        self._photo1_4()
        self.avatarPage.photo_img_cancel()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_photo_4(self):
        self._photo1_4()
        self.avatarPage.photo_img_cancel()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_back()
        self.avatarPage.take_photos_1_retry()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    @allure.story('头像前置拍照')
    def test_photo_5(self):
        self._photo5_8()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_photo_6(self):
        self._photo5_8()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_back()
        self.avatarPage.take_photos_1_retry()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_photo_7(self):
        self._photo5_8()
        self.avatarPage.photo_img_cancel()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_photo_8(self):
        self._photo5_8()
        self.avatarPage.photo_img_cancel()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_back()
        self.avatarPage.take_photos_1_retry()
        self.avatarPage.photo_img_center()
        self.avatarPage.photo_img_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @allure.story('正向流：从相册成功更换头像')
    @pytest.mark.parametrize('strategy, desc', [pytest.param('first', '选择第 1 张图片', id='第1张'), pytest.param('second', '选择第 2 张图片', id='第2张'), pytest.param('random', '选择随机 1 张图片', id='随机1张'), pytest.param('current_last', '选择当前屏幕可见的最后 1 张', id='当前最后1张'), pytest.param('absolute_last', '滑动到底部，选择相册绝对最后 1 张', id='底端最后1张')])
    def test_update_avatar_success_strategies(self, strategy, desc):
        allure.dynamic.title(f'更换头像策略测试: {desc}')

        def enter_page():
            self.avatarPage.click_avatar()
            self.avatarPage.click_right_top_button()

        def update_avatar(stray):
            self.avatarPage.click_select_images()
            self.avatarPage.select_image_by_strategy(stray)
            self.avatarPage.click_selected_crop()
            self.avatarPage.back_to_personal_info()
            return self.avatarPage.get_avatar_data()
        aft_avatar = update_avatar(strategy)
        if self.pre_avatar == aft_avatar:
            with allure.step('🔧 触发防呆重置机制：更换为备用图片后重新验证'):
                backup_strategy = 'second' if strategy == 'first' else 'first'
                logger.info(f"--> [重置状态] 使用备用策略 '{backup_strategy}' 垫底...")
                enter_page()
                new_pre_avatar = update_avatar(backup_strategy)
                logger.info(f"--> [重新验证] 再次执行目标策略 '{strategy}'...")
                enter_page()
                final_avatar = update_avatar(strategy)
                print(f'备用更换前: {new_pre_avatar}, 备用更换后: {final_avatar}')
                check.not_equal(final_avatar, new_pre_avatar, f'❌ 【{desc}】终极防呆重试后头像仍未更新！核心功能可能存在 Bug。')
        else:
            with allure.step('✅ 验证头像更新成功'):
                logger.info(f'更换前: {self.pre_avatar}, 更换后: {aft_avatar}')
                check.not_equal(aft_avatar, self.pre_avatar, f'【{desc}】头像更新失败！前后数据一致: {aft_avatar}')

    @allure.story('逆向流：取消更换动作')
    @allure.title('在相册选择页点击取消，头像未改变')
    def test_cancel_in_album_page(self):
        self.avatarPage.click_select_images()
        self.avatarPage.click_cancel_album()
        self.avatarPage.click_back_avatar()
        aft_avatar = self.avatarPage.get_avatar_data()
        check.equal(aft_avatar, self.pre_avatar, '在相册页取消后，头像被意外篡改！')

    @allure.story('逆向流：取消更换动作')
    @allure.title('进入剪裁页面后点击取消，退回相册，头像未改变')
    def test_cancel_in_crop_page(self):
        with allure.step('1. 选定图片进入剪裁页，然后取消'):
            self.avatarPage.click_select_images()
            self.avatarPage.select_image_by_strategy('first')
            self.avatarPage.click_selected_album_back()
        with allure.step('2. 验证退回到了相册页 (可选)'):
            assert self.avatarPage.get_album_title(), '取消剪裁后未能退回到相册页'
        with allure.step('3. 退出相册，验证头像未变'):
            self.avatarPage.click_cancel_album()
            self.avatarPage.back_to_personal_info()
            aft_avatar = self.avatarPage.get_avatar_data()
            check.equal(aft_avatar, self.pre_avatar, '在剪裁页取消后，头像被意外篡改！')

    @allure.story('业务流转：剪裁页取消后重新选图')
    @allure.title('在剪裁页取消后，重新选择图片并成功更换')
    def test_cancel_crop_then_reselect_success(self):
        with allure.step('1. 第一次选图进入剪裁页后取消'):
            self.avatarPage.click_select_images()
            self.avatarPage.select_image_by_strategy('first')
            self.avatarPage.click_selected_album_back()
        with allure.step('2. 在相册重新选图并确认'):
            self.avatarPage.select_image_by_strategy('random')
            self.avatarPage.click_selected_crop()
        with allure.step('3. 验证头像更新成功'):
            aft_avatar = self.avatarPage.get_avatar_data()
            check.not_equal(aft_avatar, self.pre_avatar, '重新选图后头像未能更新！')

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_2(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_3(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_4(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_5(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_back()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_6(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_back()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(False, 0)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_7(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_back()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_8(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_back()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_9(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_back()
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_10(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_back()
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_11(self):
        self._select_image()
        self.avatarPage.click_back()
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_12(self):
        self._select_image()
        self.avatarPage.click_back()
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_13(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(False, 0)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_14(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(True, 1)
        self.avatarPage.click_back()
        self.avatarPage.sj_select_image_retry(elems_imgs_nums)
        self.avatarPage.sj_select_image(elems_imgs_nums, nums)
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_image_done()
        self.avatarPage.click_done()
        self.upload_assert()

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_15(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.sj_select_image(elems_imgs_nums, nums)
        toast_text = self.avatarPage.get_toast_message(self.avatarPage.TOASE_IMAGE)
        self.avatarPage.back_person_avatar()
        assert '最多只能显示1张' in toast_text, f'期望收到超限提示，但实际收到: {toast_text}'

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_16(self):
        self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.cancel_checkbox()
        check_s = self.avatarPage.is_checkbox_checked()
        self.avatarPage.back_person_avatar()
        assert check_s is None, f'没有勾选图片，完成按钮应该不能点击'

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_17(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_preview_image()
        self.avatarPage.click_origin_image_in(False, 0)
        self.avatarPage.click_image_done()
        self.avatarPage.click_back()
        status = self.avatarPage.is_person_image(self.avatarPage.PRO_PIC_TEXT)
        self.avatarPage.back_person_avatar()
        assert status is not False, f'回到个人头像页面失败： {status}'

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_18(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_preview_image()
        self.avatarPage.click_image_done()
        self.avatarPage.click_back()
        status = self.avatarPage.is_person_image(self.avatarPage.PRO_PIC_TEXT)
        self.avatarPage.back_person_avatar()
        assert status is not False, f'回到个人头像页面失败： {status}'

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_19(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_origin_image_out(elems_imgs_nums, nums, True, 1)
        self.avatarPage.click_preview_image()
        self.avatarPage.click_back()
        status = self.avatarPage.is_person_image(self.avatarPage.IMG_TEXT)
        self.avatarPage.back_person_avatar()
        assert status is not False, f'回到选择图片页面失败： {status}'

    @pytest.mark.skip(reason='跳过')
    def test_select_photo_20(self):
        elems_imgs_nums, nums = self._select_image()
        self.avatarPage.click_preview_image()
        self.avatarPage.click_back()
        status = self.avatarPage.is_person_image(self.avatarPage.IMG_TEXT)
        self.avatarPage.back_person_avatar()
        assert status is not False, f'回到选择图片页面失败： {status}'

    @allure.story('头像大图浏览')
    @allure.title('保存当前头像到本地相册')
    def test_save_image(self):
        with allure.step('1. 点击保存图片按钮'):
            self.avatarPage.click_save_image()
        with allure.step('2. 获取并验证 Toast 提示信息'):
            toast_msg = self.avatarPage.get_toast(expected_toast='已保存到相册')
            assert toast_msg, "保存图片失败！未显示 '已保存到相册' 提示"

    @allure.story('逆向流：取消更换动作')
    @allure.title('在头像操作页点击取消，验证页面回退且头像未变')
    def test_cancel_avatar(self):
        with allure.step('1. 获取取消操作前的原始头像数据'):
            logger.info(f'取消更换头像前的原始头像数据: {self.pre_avatar}')
        with allure.step('2. 执行取消并回退操作'):
            self.avatarPage.click_cancel_button()
            self.avatarPage.click_back_avatar()
        with allure.step('3. 验证是否成功返回上一级页面'):
            is_back_success = self.avatarPage.back_to_personal_info()
            assert is_back_success is True, '回退失败，未能成功返回个人信息主页'
        with allure.step('4. 核心业务断言：验证头像未被意外修改'):
            current_avatar = self.avatarPage.get_avatar_data()
            check.equal(current_avatar, self.pre_avatar, f'严重Bug：取消更换后，头像数据被意外篡改！预期:{self.pre_avatar}, 实际:{current_avatar}')
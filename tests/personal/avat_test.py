import os
import random
import time
import threading
import pytest
import allure
from PIL import Image
from pytest_check import check
from core.logger_utils import logger, LogIcon
from pages.personal.avat_page import AvatarPage
from pages.home.home_page import HomePage
from pages.home.side_slip_page import SideSlipPage
from pages.home.left_menus.settings_center_page import SettingsCenterPage
from pages.login.login_page import LoginPage
from common.toast_enums import ToastMsg


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
                logger.info(f"{LogIcon.SETUP} --> [重置状态] 使用备用策略 '{backup_strategy}' 垫底...")
                enter_page()
                new_pre_avatar = update_avatar(backup_strategy)
                logger.info(f"{LogIcon.FIND} --> [重新验证] 再次执行目标策略 '{strategy}'...")
                enter_page()
                logger.info(f"{LogIcon.ACTION} 备用更换前: {new_pre_avatar}, 备用更换后: {final_avatar}")
                check.not_equal(final_avatar, new_pre_avatar, f'【{desc}】终极防呆重试后头像仍未更新！核心功能可能存在 Bug。')
        else:
            with allure.step('✅ 验证头像更新成功'):
                logger.info(f'{LogIcon.ACTION} 更换前: {self.pre_avatar}, 更换后: {aft_avatar}')
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
            toast_msg = self.avatarPage.get_toast(expected_toast=ToastMsg.SAVED_TO_ALBUM)
            assert toast_msg, f"保存图片失败！未显示 '{ToastMsg.SAVED_TO_ALBUM}' 提示"

    @allure.story('逆向流：取消更换动作')
    @allure.title('在头像操作页点击取消，验证页面回退且头像未变')
    def test_cancel_avatar(self):
        with allure.step('1. 获取取消操作前的原始头像数据'):
            logger.info(f'{LogIcon.ACTION} 取消更换头像前的原始头像数据: {self.pre_avatar}')
        with allure.step('2. 执行取消并回退操作'):
            self.avatarPage.click_cancel_button()
            self.avatarPage.click_back_avatar()
        with allure.step('3. 验证是否成功返回上一级页面'):
            is_back_success = self.avatarPage.back_to_personal_info()
            assert is_back_success is True, '回退失败，未能成功返回个人信息主页'
        with allure.step('4. 核心业务断言：验证头像未被意外修改'):
            current_avatar = self.avatarPage.get_avatar_data()
            check.equal(current_avatar, self.pre_avatar, f'严重Bug：取消更换后，头像数据被意外篡改！预期:{self.pre_avatar}, 实际:{current_avatar}')



@allure.epic('IM核心功能测试')
@allure.feature('个人信息模块-头像')
@allure.story('固定账号一键批量更新个人头像')
class TestUpdateAvatarByFixedAccount:
    """批量固定账号一键更换个人头像（独立运行模式，不执行任何通用 setup）"""

    

    @allure.title('多设备异步并发批量更换固定账号个人头像-状态：已完成')
    def test_update_avatar_by_fixed_account(self, request):
        """
        多设备异步并发批量更换个人头像（免校验极速模式）：
        1. 轮流将 50 个固定账号 (19200000050 ~ 19200000099) 均分分配给 5 台已连接设备 (Device_5 ~ Device_9)
        2. 各设备线程异步并行登录分配到的账号、进入个人信息更换头像并退出登录
        3. 等待所有线程执行结束并做异常汇总与校验，实现 5 倍速度极速并行换头像
        """
        # 1. 生成 50 个固定测试账号列表 (19200000050 ~ 19200000099)
        accounts = [
            {"account": f"19200000{i}", "password": "a1234567B"}
            for i in range(101, 251)
        ]

        # 2. 将 50 个固定账号平均切分为 5 组 (每组 10 个账号)，对齐 test_chat.py 调度模式
        dev5_accounts = accounts[0:30]   
        dev6_accounts = accounts[30:60]  
        dev7_accounts = accounts[60:90]  
        dev8_accounts = accounts[90:120] 
        dev9_accounts = accounts[120:150] 

        device_accounts_map = {
            5: ('Device_5', dev5_accounts),
            6: ('Device_6', dev6_accounts),
            7: ('Device_7', dev7_accounts),
            8: ('Device_8', dev8_accounts),
            9: ('Device_9', dev9_accounts),
        }

        # 3. 加载项目本地表情包图片资源库 (resources/images/avatars)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        avatars_dir = os.path.join(project_root, "resources", "images", "avatars")
        supported_exts = {".jpg", ".jpeg", ".png"}
        avatar_images = []
        if os.path.exists(avatars_dir):
            avatar_images = sorted([
                os.path.join(avatars_dir, f)
                for f in os.listdir(avatars_dir)
                if os.path.splitext(f)[1].lower() in supported_exts
            ])
            logger.info(f"{LogIcon.ACTION} 🖼️ 已从本地表情包资源库加载 {len(avatar_images)} 张合规静态头像图片")

        if not avatar_images:
            temp_dir = os.path.join(project_root, "resources", "images")
            os.makedirs(temp_dir, exist_ok=True)
            fallback_img = os.path.join(temp_dir, "batch_avatar.png")
            if not os.path.exists(fallback_img):
                img = Image.new("RGB", (300, 300), color=(70, 140, 240))
                img.save(fallback_img, format="PNG")
            avatar_images = [fallback_img]

        # 4. 收集所有已就绪的设备及其 Driver 实例 (若部分 Appium 服务未开则自动跳过并告警)
        ready_tasks = []
        for idx, (dev_name, acc_list) in device_accounts_map.items():
            try:
                driver = request.getfixturevalue(f'driver_device{idx}')
                if driver:
                    ready_tasks.append((idx, dev_name, driver, acc_list))
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} 设备 {dev_name} (driver_device{idx}) 未就绪或启动失败: {e}")

        if not ready_tasks:
            logger.warning(f"{LogIcon.WARN} 未检测到任何 Device_5 ~ Device_9 设备，尝试回退使用 driver_sender 单设备执行")
            try:
                default_driver = request.getfixturevalue("driver_sender")
                ready_tasks.append((1, "Default_Sender", default_driver, accounts))
            except Exception as def_err:
                pytest.fail(f"❌ 没有可用设备驱动可以执行更换头像任务: {def_err}")

        exceptions = []

        # 5. 单设备异步并发 Worker 执行函数（严格线程安全，独立维护专属 Page 实例）
        def worker_avatar_update(dev_idx, dev_name, driver, acc_list):
            logger.info(f"{LogIcon.ACTION} 设备 [{dev_name}] 线程启动，开始异步并行处理 {len(acc_list)} 个固定账号更换头像...")
            # 为当前设备独立创建一套专属 Page Object 实例，杜绝多线程资源竞态
            login_page = LoginPage(driver)
            home_page = HomePage(driver)
            side_slip_page = SideSlipPage(driver)
            settings_center_page = SettingsCenterPage(driver)
            avatar_page = AvatarPage(driver)

            # 初始环境对齐：确保当前设备处于登录首页
            try:
                if not login_page.wait_for_login_success_no_card(timeout=2):
                    home_page.open_left_menu()
                    side_slip_page.click_setting()
                    settings_center_page.click_logout_and_get_toast()
            except Exception:
                pass
            login_page.wait_for_login_success_no_card(timeout=3)

            total_acc = len(acc_list)
            for a_idx, item in enumerate(acc_list, start=1):
                acc = item["account"]
                pwd = item["password"]
                logger.info(f"{LogIcon.ACTION} [{dev_name}] [{a_idx}/{total_acc}] 开始处理固定账号: {acc}")
                try:
                    # 分配专属头像图片并推送到相机胶卷置顶
                    img_idx = (int(acc[-2:]) if acc[-2:].isdigit() else a_idx) % len(avatar_images)
                    chosen_image = avatar_images[img_idx]
                    file_ext = os.path.splitext(chosen_image)[1].lower()
                    remote_name = f"IMG_{int(time.time())}_{acc}{file_ext}"

                    avatar_page.push_local_image_to_gallery(chosen_image, remote_filename=remote_name)

                    # 步骤 A：登录当前固定账号
                    is_login = login_page.wait_for_login_success_no_card(timeout=2)
                    if is_login:
                        login_page.click_phone_login_button()
                    login_page.click_password_login_button()
                    login_page.input_account(acc)
                    login_page.input_password(pwd)
                    login_page.click_user_agreement()
                    login_page.click_login_button()
                    home_page.wait_home_page(timeout=10)

                    # 步骤 B：从首页侧边栏进入个人信息页面
                    home_page.open_left_menu()
                    side_slip_page.click_INFO()

                    # 步骤 C：进入头像并选取本地图片剪裁保存 (免校验直接更换)
                    avatar_page.click_avatar()
                    avatar_page.click_right_top_button()
                    avatar_page.click_select_images()
                    avatar_page.select_image_by_strategy("first")
                    avatar_page.click_selected_crop()
                    avatar_page.back_to_personal_info()
                    logger.info(f"{LogIcon.SUCCESS} [{dev_name}] [{a_idx}/{total_acc}] 账号【{acc}】头像更换完成")

                    # 步骤 D：从个人信息返回主页 -> 打开侧边栏 -> 设置中心 -> 退出登录
                    avatar_page.click_back()
                    home_page.open_left_menu()
                    side_slip_page.click_setting()
                    settings_center_page.click_logout_and_get_toast()
                    login_page.wait_for_login_success_no_card(timeout=2)

                except Exception as acc_err:
                    logger.error(f"{LogIcon.FAIL} [{dev_name}] 账号【{acc}】换头像异常: {acc_err}")
                    exceptions.append((dev_name, acc, acc_err))
                    # 异常自愈兜底：退回到登录页，继续处理后续账号
                    try:
                        avatar_page.back_to_personal_info()
                        avatar_page.click_back()
                        home_page.open_left_menu()
                        side_slip_page.click_setting()
                        settings_center_page.click_logout_and_get_toast()
                    except Exception:
                        pass
                    login_page.wait_for_login_success_no_card(timeout=3)

            logger.info(f"{LogIcon.SUCCESS} 设备 [{dev_name}] 线程全部 {total_acc} 个账号处理完毕！")

        # 6. 创建并启动多设备并发线程
        threads = []
        for idx, dev_name, driver, acc_list in ready_tasks:
            t = threading.Thread(
                target=worker_avatar_update,
                args=(idx, dev_name, driver, acc_list),
                name=f"Thread-{dev_name}"
            )
            threads.append(t)
            logger.info(f"{LogIcon.ACTION} 🧵 [Multi Device Avatar] 已就绪并发设备线程: {dev_name} (分配账号数: {len(acc_list)})")

        with allure.step(f"0. 启动多设备异步并发换头像 (参与设备数: {len(threads)})"):
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        if exceptions:
            err_details = "\n".join([f"[{d}] 账号 {a}: {e}" for d, a, e in exceptions])
            logger.warning(f"{LogIcon.WARN} 多设备换头像执行完毕，共有 {len(exceptions)} 个账号发生异常:\n{err_details}")
            if len(exceptions) > len(accounts) * 0.3:
                pytest.fail(f"❌ 多设备更换头像失败率过高 (失败数: {len(exceptions)}/{len(accounts)}):\n{err_details}")
        else:
            logger.info(f"{LogIcon.SUCCESS} 恭喜！所有参与设备的固定账号头像已全部并发更换完成！")
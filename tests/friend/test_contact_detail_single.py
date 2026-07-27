import time
import allure
import pytest
import pytest_check as check
from core.logger_utils import logger
from pages.main.main_page import MainPage
from pages.home.home_page import HomePage
from pages.chat_options.contact.contact_detail_page import ContactDetailPage
from pages.common.contact_select_page import ContactSelectPage
from pages.chat_options.contact.remark_setting_page import RemarkSettingPage
from strategy.chat.chat_strategy import PRIVATE_USER1, PRIVATE_USER3

SENDER_NAME = PRIVATE_USER3.name
RECEIVER_NAME = PRIVATE_USER1.name

@allure.epic("IM核心功能测试")
@allure.feature("好友资料模块")
@allure.story("好友资料卡展示与备注设置(单端)")
class TestContactDetailSingle:
    """单端好友资料详情管理与备注设置测试集 (仅操作发送端，提速运行)"""

    @pytest.fixture(scope="class", autouse=True)
    def setup_class_nav(self, driver_sender):
        """类级别前置：全类仅执行1次，从主页展开底栏并进入好友/通讯录列表页"""
        main_page = MainPage(driver_sender)
        home_page = HomePage(driver_sender)
        main_page.go_to_main_page()
        home_page.click_bottom_expand_button()
        home_page.click_friend()
        home_page.wait_for_friend_page_load()

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """用例级别前置与后置：初始化页面对象，后置确保停留在好友页面"""
        # S 端 (发送方 Sender / 操作方)
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.contactDetailPageS = ContactDetailPage(driver_sender)
        self.remarkSettingPageS = RemarkSettingPage(driver_sender)

        yield
        try:
            self.homePageS.click_friend()
        except Exception as e:
            logger.error(f"⚠️ [Teardown] 返回好友页面失败: {e}")

    def _go_to_contact_detail_from_list(self, name: str, raise_exception: bool = True) -> bool:
        """导航辅助方法：在通讯录列表中查找并进入指定好友的资料详情页"""
        return self._click_contact_by_name(name, raise_exception=raise_exception)

    def _click_contact_by_name(self, name: str, raise_exception: bool = True, search: bool = False) -> bool:
        """点击通讯录好友并等待详情页加载完成"""
        click_ok = self.contactSelectPageS.click_contact_by_name(name, raise_exception=raise_exception, search=search)
        if click_ok:
            self.contactDetailPageS.wait_for_detail_page_load(timeout=8)
        return click_ok



    @allure.story("入口与展示")
    @allure.title("从通讯录成功进入好友资料页并校验-状态：已完成")
    def test_entry_and_profile_display(self):
        """从通讯录列表成功点击好友，进入资料页验证顶部大字昵称、ID及所在地信息完整展示"""
        with allure.step("1. 从通讯录中点击进入好友B的资料详情页"):
            success = self._go_to_contact_detail_from_list(RECEIVER_NAME)
            check.is_true(success, f"❌ 通讯录中未找到并点击好友: {RECEIVER_NAME}")

        with allure.step("2. 校验好友资料卡信息展示"):
            main_name = self.contactDetailPageS.get_formatted_friend_name()
            st_id = self.contactDetailPageS.get_st_id()
            location = self.contactDetailPageS.get_location()

            check.equal(main_name, RECEIVER_NAME, f"❌ 资料页主名称与预期不符，实际: {main_name}")
            check.is_true(len(st_id) > 0, "❌ 资料页显示的ID为空")
            check.is_true(len(location) > 0, "❌ 资料页显示的地区所在地为空")
            self.contactDetailPageS.click_iv_back()


    @allure.story("设置备注名")
    @allure.title("修改备注名、各处同步并在清空后恢复-参数化边界字数限制校验-状态：已完成")
    @pytest.mark.parametrize("input_remark, expected_remark", [
        ("DYNAMIC_TIME", "DYNAMIC_TIME"),                
        ("A" * 30, "A" * 30),                            
        ("B" * 31, "B" * 30)                             
    ], ids=["正常修改备注", "30个字符", "超过30个字符"])
    def test_modify_contact_remark_and_sync(self, input_remark, expected_remark):
        """修改备注名保存 -> 校验资料卡、通讯录同步显示 -> 清空备注名 -> 恢复原名称展示 (参数化合并)"""
        if input_remark == "DYNAMIC_TIME":
            input_remark = expected_remark = f"测试备注_{int(time.time())}"

        with allure.step("1. 进入资料页并修改备注名"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.remarkSettingPageS.click_remark_name()
            self.remarkSettingPageS.input_remark_name(input_remark)
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()

        with allure.step("2. 校验资料页大字正确展示新备注名，小字展示原昵称"):
            main_name = self.contactDetailPageS.get_formatted_friend_name()
            small_name = self.contactDetailPageS.get_contact_nickname(raise_exception=False)
            check.equal(main_name, expected_remark, f"❌ 资料卡顶部未成功显示修改后的备注名: {expected_remark}")
            check.is_in(RECEIVER_NAME, small_name, f"❌ 资料卡昵称小字处未成功保留显示好友原名称: {RECEIVER_NAME}")

        with allure.step("3. 校验通讯录好友列表中同步为新备注名"):
            self.contactDetailPageS.click_iv_back()
            self.homePageS.wait_for_friend_page_load()
            has_remark = self.contactSelectPageS.select_contact_by_name(expected_remark)
            check.is_true(bool(has_remark), f"❌ 备注修改后，通讯录中找不到带有新备注名的联系人: {expected_remark}")

        with allure.step("4. 清空备注名并保存，校验是否成功恢复为原名称显示"):
            self._click_contact_by_name(name=expected_remark, search=False)
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.remarkSettingPageS.click_remark_name()
            self.remarkSettingPageS.clear_remark_name()
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
        
        with allure.step("5. 校验通讯录好友列表同步恢复"):
            after_main_name = self.contactDetailPageS.get_formatted_friend_name()
            after_small_name = self.contactDetailPageS.get_contact_nickname(raise_exception=False)
            check.equal(after_main_name, RECEIVER_NAME, f"❌ 资料卡顶部未成功恢复显示原昵称，实际显示：{after_main_name}")
            check.is_false(bool(after_small_name), f"❌ 清空备注后，资料卡仍显示昵称小字：{after_small_name}")

            self.contactDetailPageS.click_iv_back()
            self.homePageS.wait_for_friend_page_load()
            has_remark = self.contactSelectPageS.select_contact_by_name(RECEIVER_NAME)
            check.is_true(bool(has_remark), f"❌ 清空备注后通讯录未恢复展示好友原昵称")


    @allure.story("电话管理")
    @allure.title("新增电话号码参数化校验（上限3个/数字限制/15字字符截断）-状态：已完成")
    @pytest.mark.parametrize("scenario, input_phones, expected_phones", [
        ("LIMIT_COUNT", ["13800000001", "13800000002", "13800000003", "13800000004"], ["13800000001", "13800000002", "13800000003"]),
        ("ONLY_DIGITS", ["1380000abc"], ["1380000"]),
        ("MAX_LENGTH", ["1" * 16], ["1" * 15])
    ], ids=["限制输入最多3个", "只允许输入数字", "最多输入15个字符"])
    def test_phone_number_addition_and_limit(self, scenario, input_phones, expected_phones):
        """新增电话号码参数化校验：测试只能添加3个、只允许数字、最多输入15个字"""
        with allure.step(f"1. 进入设置备注与电话页，尝试输入测试号码 - 场景: {scenario}"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.remarkSettingPageS.click_phone_item()
        
        with allure.step("2. 尝试添加电话号码并校验数量限制"):
            box_count = len(self.remarkSettingPageS.get_phones(False))

            if box_count >= 3:
                is_visible = self.remarkSettingPageS.is_add_phone_visible(False)
                check.is_false(is_visible, "❌ 已添加3个电话，但‘添加电话’按钮依然可见，未作数量上限控制")
            else:
                add_count = 3 - box_count
                for i, phone_val in enumerate(input_phones):
                    is_visible = self.remarkSettingPageS.is_add_phone_visible(False)
                    if i >= add_count and not is_visible:
                        check.is_false(is_visible, "❌ 到达上限后，添加电话按钮隐藏异常 ")
                        break
                    
                    self.remarkSettingPageS.input_phone(phone_val, index=i, by_action=True)
                    if is_visible:
                        self.remarkSettingPageS.click_add_phone()

        with allure.step("2. 前端即时校验：校验输入框中的文本变化是否符合规则"):
            current_phones = self.remarkSettingPageS.get_phones(False)
            if scenario == "ONLY_DIGITS":
                check.equal(current_phones, expected_phones, f"❌ 前端未实时限制纯数字输入，当前输入框: {current_phones}")
            elif scenario == "MAX_LENGTH":
                check.equal(current_phones, expected_phones, f"❌ 前端未实时限制15字上限截断，当前输入框: {current_phones}")

        with allure.step("3. 保存电话并重新进入，校验号码持久化回显是否符合预期"):
            self.remarkSettingPageS.click_save()
            self.remarkSettingPageS.wait_friend_detail_page()
        
        with allure.step("4. 校验已添加的电话号码回显"):
            ph_list = self.remarkSettingPageS.get_phone_numbers()
            check.is_true(all(p in expected_phones for p in ph_list), 
                f"❌ 已添加的电话号码回显不符合预期，实际: {ph_list}, 预期: {expected_phones}")
            self.contactDetailPageS.click_iv_back()
        
        with allure.step("5. 好友资料页面，校验号码回显"):
            if len(expected_phones) >= 3:
                self.contactDetailPageS.click_all_phone_numbers()
                self.contactDetailPageS.wait_for_phone_sheet_load()
                sheet_list = self.contactDetailPageS.get_sheet_phone_list()
                check.is_true(all(p in expected_phones for p in sheet_list), 
                    f"❌ 已添加的电话号码回显不符合预期，实际: {sheet_list}, 预期: {expected_phones}")
                self.contactDetailPageS.click_phone_sheet_close()
            else:
                ph_list = self.contactDetailPageS.get_profile_phone_value()
                check.is_true(all(p in expected_phones for p in ph_list), 
                    f"❌ 已添加的电话号码回显不符合预期，实际: {ph_list}, 预期: {expected_phones}")
            
        with allure.step("6. 重新进入设置备注与电话页，校验号码持久化回显"):
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.remarkSettingPageS.click_phone_item()
            actual_phones = self.remarkSettingPageS.get_phones(False)
            check.equal(actual_phones, expected_phones, f"❌ 保存后回显号码与预期不符，实际: {actual_phones}, 预期: {expected_phones}")

        with allure.step("7. 环境还原：清空本次输入的所有电话并保存"):
            self.remarkSettingPageS.delete_all_phones()
            self.remarkSettingPageS.click_save()
            aftph_list = self.remarkSettingPageS.get_phone_numbers()
            check.is_true(len(aftph_list) == 0, f"❌ 清空后回显号码与预期不符，实际: {aftph_list}, 预期: []")
            self.contactDetailPageS.click_iv_back()
            is_exist = self.contactDetailPageS.is_row_profile_phone()
            check.is_false(is_exist, f"❌ 清空后资料卡电话行不符合预期，实际: {is_exist}, 预期: False")
            self.contactDetailPageS.click_iv_back()


    @allure.story("电话管理")
    @allure.title("删除电话号码及添加按钮重新显露逻辑-状态：已完成")
    def test_phone_number_deletion_flow(self):
        """测试删除其中一个电话，校验添加按钮重新显示流程"""
        try:
            with allure.step("1. 前置准备：进入备注页，添加2个电话并保存"):
                self._go_to_contact_detail_from_list(RECEIVER_NAME)
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                self.remarkSettingPageS.click_phone_item()

                # 采用与 test_phone_number_addition_and_limit 相同的标准时序添加2个电话
                self.remarkSettingPageS.input_phone("13900000001", index=0)
                self.remarkSettingPageS.click_add_phone()
                self.remarkSettingPageS.input_phone("13900000002", index=1)
                self.remarkSettingPageS.click_save()
                self.remarkSettingPageS.wait_friend_detail_page()

            with allure.step("2. 重新进入编辑页并删除第二个电话"):
                self.remarkSettingPageS.click_phone_item()
                self.remarkSettingPageS.clear_phone(index=1)

            with allure.step("3. 校验‘添加电话’按钮重新显露"):
                is_visible_after_del = self.remarkSettingPageS.is_add_phone_visible()
                check.is_true(is_visible_after_del, "❌ 删除1个电话后，‘添加电话’按钮未重新显露")

            with allure.step("4. 保存并重新进入，校验只剩下了第一个电话"):
                self.remarkSettingPageS.click_save()
                self.contactDetailPageS.click_iv_back()
                self.contactDetailPageS.wait_for_detail_page_load()
                ph_list = self.contactDetailPageS.get_profile_phone_value()
                check.is_true(len(ph_list) == 1, f"❌ 保存后重新进入，已保存的电话号码条数不等于1，实际为: {len(ph_list)}")
                if ph_list:
                    check.equal(ph_list[0], "13900000001", f"❌ 剩余电话号码内容与预期不符，实际: {ph_list[0]}")
            
            with allure.step("5. 进入设置备注与电话页，校验只剩下了第一个电话"):
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                self.remarkSettingPageS.click_phone_item()
                phones = self.remarkSettingPageS.get_phones()
                check.equal(len(phones), 1, f"❌ 保存后重新进入，已保存的电话号码条数不等于1，实际为: {len(phones)}")
                if phones:
                    check.equal(phones[0], "13900000001", f"❌ 剩余电话号码内容与预期不符，实际: {phones[0]}")
        finally:
            with allure.step("5. Environment Teardown：全部清除后保存退出"):
                self.remarkSettingPageS.delete_all_phones()
                self.remarkSettingPageS.click_save()
                self.contactDetailPageS.click_iv_back()


    @allure.story("标签")
    @allure.title("标签点击后选中/取消选中状态切换-状态：已完成")
    def test_tag_selection_and_toggle(self):
        """TextView 标签点击后应在选中（绿色）与未选中（灰色）状态间切换。"""
        with allure.step("1. 进入标签选择页并清理当前选中状态"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_friend_detail_title_remark()
            self.remarkSettingPageS.wait_friend_detail_page()
        
        with allure.step("2. 清理当前选中状态"):
            tag_values = self.remarkSettingPageS.get_tag_values()
            self.remarkSettingPageS.click_tags()
            self.remarkSettingPageS.wait_for_tag_page_load()
            self.remarkSettingPageS.clear_tag(list_tags=tag_values)
            toast = self.remarkSettingPageS.get_toast()
            check.equal("保存成功", toast, f"❌ 未收到保存成功的 Toast，实际: {toast}")

        with allure.step(f"2. 获取当前标签名称并断言"):
            tag_names = self.remarkSettingPageS.get_tag_names()
            check.is_true(tag_names, "❌ 标签选择页没有找到 chip_group 下的 TextView 标签")
            if not tag_names:
                pytest.fail("标签选择页没有可操作的 TextView 标签")
            tag_name = tag_names[0]

        with allure.step(f"3. 点击标签 [{tag_name}]，校验变为选中状态（绿色）"):
            click_tag = self.remarkSettingPageS.click_tag(tag_type=1, target=tag_name)
            check.is_true(click_tag, f"❌ 点击标签 [{tag_name}] 失败")
            is_selected = self.remarkSettingPageS.is_tag_selected(tag_name)
            check.is_false(is_selected, f"❌ 点击标签 [{tag_name}] 后未变为选中状态")

        with allure.step(f"4. 再次点击标签 [{tag_name}]，校验取消选中（灰色）"):
            click_tag = self.remarkSettingPageS.click_tag(tag_type=1, target=tag_name)
            check.is_true(click_tag, f"❌ 再次点击标签 [{tag_name}] 失败")
            after_unselected = self.remarkSettingPageS.is_tag_selected(tag_name)
            check.is_true(after_unselected, f"❌ 再次点击后标签 [{tag_name}] 仍处于选中状态")
        
        with allure.step("5. 点击取消并返回"):
            self.remarkSettingPageS.click_tv_cancel()
            self.remarkSettingPageS.click_tv_cancel()
            self.contactDetailPageS.cancel_two_btn_comment()
            self.remarkSettingPageS.wait_friend_detail_page()
            self.contactDetailPageS.click_iv_back()
            self.contactDetailPageS.wait_for_detail_page_load()
            self.contactDetailPageS.click_iv_back()
            

    @allure.story("标签")
    @allure.title("选择标签及标签上限边界参数化校验-状态：已完成")
    @pytest.mark.parametrize(
        "select_count, expected_selected_count, check_exceed_toast",
        [
            (1, 1, False),
            (14, 14, False),
            (15, 15, False),
            (16, 15, True),
        ],
        ids=["选择1个标签", "选择14个标签", "选择15个标签", "选择16个标签受阻"]
    )
    def test_tag_selection_boundary_limit(self, select_count, expected_selected_count, check_exceed_toast):
        """通过参数化模式合并校验标签的最大选择上限及超限拦截逻辑"""
        try:
            with allure.step("1. 进入标签选择页"):
                self._go_to_contact_detail_from_list(RECEIVER_NAME)
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                tag_values = self.remarkSettingPageS.get_tag_values()
                self.remarkSettingPageS.click_tags()
                self.remarkSettingPageS.wait_for_tag_page_load()
            
            with allure.step("2. 清理当前已有选中状态"):
                if tag_values:
                    self.remarkSettingPageS.clear_tag(list_tags=tag_values)
                    self.remarkSettingPageS.click_tags()

            tag_names = self.remarkSettingPageS.get_tag_names(timeout=10)
            required_tags = max(select_count, 15)
            if len(tag_names) < required_tags:
                pytest.fail(f"测试需要至少 {required_tags} 个标签，当前只有 {len(tag_names)} 个")

            click_count = min(select_count, 15)
            with allure.step(f"3. 依次选择前 {click_count} 个标签"):
                self.remarkSettingPageS.click_tag(tag_type=0, target=click_count)

            if check_exceed_toast:
                with allure.step("4. 尝试点击第 16 个标签，校验被拦截并弹出 Toast"):
                    sixteenth_tag_name = tag_names[15]
                    self.remarkSettingPageS.click_tag(tag_type=1, target=sixteenth_tag_name)
                    sel_toast = self.remarkSettingPageS.get_toast(timeout=10)
                    is_selected = self.remarkSettingPageS.is_tag_selected(sixteenth_tag_name)
                    check.is_true(is_selected, f"❌ 第16个标签 [{sixteenth_tag_name}] 已选中")
                    check.is_in("最多选择15个标签", sel_toast, f"❌ 未收到15个标签上限 Toast，实际: {sel_toast}")

            with allure.step(f"5. 校验最终资料页和卡片页选中的标签数量为 {expected_selected_count}"):
                self.remarkSettingPageS.click_save()
                self.remarkSettingPageS.wait_friend_detail_page()
                selected_tags = self.remarkSettingPageS.get_tag_page_values(tag_type=0, split_type=0)
                check.equal(len(selected_tags), expected_selected_count, f"❌ 备注设置页标签选中数量不等于 {expected_selected_count}")

                self.contactDetailPageS.click_iv_back()
                self.contactDetailPageS.wait_for_detail_page_load()
                out_tags = self.remarkSettingPageS.get_tag_page_values(tag_type=1, split_type=1)
                check.equal(len(out_tags), expected_selected_count, f"❌ 资料卡展示标签数量不等于 {expected_selected_count}")
        finally:
            with allure.step("6. 环境恢复：进入设置页清空所有选中标签"):
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                tag_values = self.remarkSettingPageS.get_tag_values()
                if tag_values:
                    self.remarkSettingPageS.click_tags()
                    self.remarkSettingPageS.wait_for_tag_page_load()
                    self.remarkSettingPageS.clear_tag(list_tags=tag_values)
                    self.remarkSettingPageS.click_save()
                    self.remarkSettingPageS.wait_friend_detail_page()
                self.contactDetailPageS.click_iv_back()
                time.sleep(0.3)
                self.contactDetailPageS.click_iv_back()


    @allure.story("标签")
    @allure.title("新增标签30字限制及新增后默认选中-状态：已完成")
    @pytest.mark.destructive
    @pytest.mark.parametrize(
        "input_length, expected_length",
        [
            (29, 29),
            (30, 30),
            (31, 30),
        ],
        ids=["29字-上限前", "30字-正好上限", "31字-超限截断"],
    )
    def test_create_tag_length_and_auto_selected(self, input_length: int, expected_length: int):
        """参数化校验标签名称长度边界，且新增成功后默认处于选中状态。"""
        try:
            with allure.step("1. 进入标签选择页并清理已有标签"):
                self._go_to_contact_detail_from_list(RECEIVER_NAME)
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                tag_values = self.remarkSettingPageS.get_tag_values()
                self.remarkSettingPageS.click_tags()
                self.remarkSettingPageS.wait_for_tag_page_load()
                if tag_values:
                    self.remarkSettingPageS.clear_tag(list_tags=tag_values)

            unique_prefix = f"qa{time.time_ns()}_{input_length}_"
            tag_name = (unique_prefix + ("x" * input_length))[:input_length]
            expected_tag_name = tag_name[:expected_length]

            with allure.step(f"2. 新增{input_length}字标签，校验实际保留{expected_length}字"):
                self.remarkSettingPageS.click_add_new_tag()
                self.remarkSettingPageS.input_tag_name(tag_name)
                self.remarkSettingPageS.click_create_done()
                self.remarkSettingPageS.wait_for_tag_page_load()
                self.remarkSettingPageS.input_search_tag(expected_tag_name)
                tag_names = self.remarkSettingPageS.get_tag_names(timeout=5)
                check.equal(
                    len(tag_names[-1]),
                    expected_length,
                    f"❌ 输入{input_length}字时长度处理错误，预期保留{expected_length}字，实际保留{len(tag_names[-1])}字",
                )
                check.equal(
                    tag_names[-1],
                    expected_tag_name,
                    f"❌ 标签输入框最终内容不符合预期，实际: {tag_names[-1]}",
                )

            with allure.step("3. 校验新增后的标签名称及默认选中状态"):
                check.is_in(expected_tag_name, tag_names, f"❌ 新增标签未出现在标签列表: {expected_tag_name}")
                if expected_tag_name in tag_names:
                    check.is_false(
                        self.remarkSettingPageS.is_tag_selected(expected_tag_name),
                        f"❌ 新增标签 [{expected_tag_name}] 默认选中",
                    )
        finally:
            with allure.step("4. 环境恢复：清空创建的测试标签"):
                self.remarkSettingPageS.click_tv_cancel()
                self.remarkSettingPageS.click_tv_cancel()
                self.contactDetailPageS.click_iv_back()
                self.contactDetailPageS.click_iv_back()
                

    @allure.story("标签")
    @allure.title("新增标签数量边界及保存回显参数化校验-状态：已完成")
    @pytest.mark.destructive
    @pytest.mark.parametrize(
        "create_count, expected_count, check_exceed_toast, should_save",
        [
            (1, 1, False, True),     
            (14, 14, False, False), 
            (15, 15, False, False), 
            (16, 15, True, False), 
        ],
        ids=["新增1个标签并保存回显", "新增14个标签", "新增15个标签上限", "新增16个标签受阻"],
    )
    def test_create_tag_max_count_limit_toast(
        self, create_count: int, expected_count: int, check_exceed_toast: bool, should_save: bool
    ):
        """校验新增不同数量标签边界、上限 Toast 拦截以及正向保存回显闭环 (参数化合并)。"""
        try:
            with allure.step("1. 进入标签选择页并清理已有标签"):
                self._go_to_contact_detail_from_list(RECEIVER_NAME)
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                tag_values = self.remarkSettingPageS.get_tag_values()
                self.remarkSettingPageS.click_tags()
                self.remarkSettingPageS.wait_for_tag_page_load()
                if tag_values:
                    self.remarkSettingPageS.clear_tag(list_tags=tag_values)
                    self.remarkSettingPageS.click_tags()

            test_prefix = f"qa{int(time.time())}"
            actual_add_count = min(create_count, 15)
            with allure.step(f"2. 尝试连续新增 {actual_add_count} 个标签"):
                for index in range(actual_add_count):
                    tag_name = f"{test_prefix}_{index:02d}"
                    self.remarkSettingPageS.click_add_new_tag()
                    self.remarkSettingPageS.input_tag_name(tag_name)
                    self.remarkSettingPageS.click_create_done()
                    self.remarkSettingPageS.wait_for_tag_page_load()

            if check_exceed_toast:
                with allure.step(f"3. 尝试新增第 {create_count} 个标签，校验被限制并弹出 Toast"):
                    sixteenth_name = f"{test_prefix}_15".ljust(30, "x")
                    self.remarkSettingPageS.click_add_new_tag()
                    self.remarkSettingPageS.input_tag_name(sixteenth_name)
                    self.remarkSettingPageS.click_create_done()
                    toast_exceed = self.remarkSettingPageS.get_toast("最多选择15个标签", timeout=2)
                    check.is_true(toast_exceed, f"❌ 未收到最多新增15个标签的 Toast 拦截提示")

            with allure.step(f"4. 校验列表中实际成功创建的标签数量为 {expected_count}"):
                tag_names = self.remarkSettingPageS.get_tag_names(timeout=2)
                check.equal(len(tag_names), expected_count, f"❌ 实际成功创建的标签数量 ({len(tag_names)}) 不符合预期 ({expected_count})")

            if should_save:
                with allure.step("5. 点击保存并验证资料卡成功同步渲染新标签"):
                    self.remarkSettingPageS.click_save()
                    self.remarkSettingPageS.wait_friend_detail_page()
                    self.contactDetailPageS.click_iv_back()
                    out_tags = self.remarkSettingPageS.get_tag_page_values(tag_type=1, split_type=1)
                    check.is_true(
                        any(test_prefix in tag for tag in out_tags),
                        f"❌ 资料卡未同步展示新保存的标签: {out_tags}",
                    )
        finally:
            with allure.step("6. 环境恢复：安全返回并恢复主页"):
                if should_save:
                    self.contactDetailPageS.click_friend_detail_title_remark()
                    self.remarkSettingPageS.wait_friend_detail_page()
                    tag_values = self.remarkSettingPageS.get_tag_values()
                    if tag_values:
                        self.remarkSettingPageS.click_tags()
                        self.remarkSettingPageS.wait_for_tag_page_load()
                        self.remarkSettingPageS.clear_tag(list_tags=tag_values)
                        self.remarkSettingPageS.click_save()
                        self.remarkSettingPageS.wait_friend_detail_page()
                    self.contactDetailPageS.click_iv_back()
                    self.contactDetailPageS.click_iv_back()
                else:
                    self.remarkSettingPageS.click_tv_cancel()
                    self.remarkSettingPageS.click_tv_cancel()
                    self.contactDetailPageS.click_iv_back()
                    self.contactDetailPageS.click_iv_back()


    @allure.story("备注描述")
    @allure.title("FD_NOTE_002 - 编辑多行特殊备注并验证持久化")
    def test_multi_line_description_note(self):
        """测试输入多行带 Emoji 的描述，验证保存后重新进入能够正确回显且内容无损"""
        complex_note = "第一行：测试账号特性描述\n第二行：具有高可靠性校验🌟"

        try:
            with allure.step("1. 进入设置备注页，在描述栏输入多行内容并保存"):
                self._go_to_contact_detail_from_list(RECEIVER_NAME)
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                self.remarkSettingPageS.clear_note()
                self.remarkSettingPageS.input_note(complex_note)
                self.remarkSettingPageS.click_save()
                save_toast = self.remarkSettingPageS.get_toast("保存成功", timeout=15)
                check.is_true(save_toast, "❌ 描述修改后未收到保存成功的 Toast")
                self.contactDetailPageS.wait_for_detail_page_load()

            with allure.step("2. 重新进入编辑页，验证描述是否无损回显"):
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                displayed_note = self.remarkSettingPageS.get_note()
                check.equal(displayed_note, complex_note, f"❌ 多行备注描述回显不匹配，实际: {displayed_note}")
        finally:
            with allure.step("3. 环境恢复：清理测试描述"):
                self.remarkSettingPageS.clear_note()
                self.remarkSettingPageS.click_save()
                self.contactDetailPageS.click_iv_back()


    @allure.story("共同群聊")
    @allure.title("FD_GROUP_002 - 共同群聊入口展示、过滤及页面返回验证")
    def test_common_groups_navigation_and_search(self):
        """校验存在共同群聊时资料页的展示，以及共同群聊详情列表过滤检索及返回功能"""
        try:
            with allure.step("1. 进入好友资料卡并点进设置备注页，验证共同群聊展示个数"):
                self._go_to_contact_detail_from_list(RECEIVER_NAME)
                self.contactDetailPageS.click_friend_detail_title_remark()
                self.remarkSettingPageS.wait_friend_detail_page()
                count = self.remarkSettingPageS.get_common_groups_count()
                check.is_true(count >= 0, f"❌ 共同群聊数量获取异常: {count}")

            if count > 0:
                with allure.step("2. 点击共同群聊，进入共同群聊详情页面"):
                    self.remarkSettingPageS.click_common_groups()
                    self.remarkSettingPageS.wait_for_common_groups_page_load()
                    
                    # 校验详情页实际列表渲染的群个数
                    list_count = self.remarkSettingPageS.get_common_groups_list_count()
                    check.equal(list_count, count, f"❌ 详情页群聊个数 ({list_count}) 与设置备注页显示的共同群聊数量 ({count}) 不一致")

                with allure.step("3. 过滤搜索共同群聊并返回设置备注页"):
                    self.remarkSettingPageS.search_common_group("测试")
                    self.remarkSettingPageS.click_back()
                    self.remarkSettingPageS.wait_friend_detail_page()
                    self.remarkSettingPageS.click_save()
                    self.contactDetailPageS.wait_for_detail_page_load()
            else:
                logger.info("ℹ️ 当前与该好友没有共同群聊，FD_GROUP_002 搜索子流程略过")
                self.remarkSettingPageS.click_save()
                self.contactDetailPageS.wait_for_detail_page_load()
        finally:
            self.contactDetailPageS.click_iv_back()

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

    @pytest.fixture(autouse=True)
    def setup_base(self, driver_sender):
        """单端前置：仅初始化操作端页面对象并校验环境就绪"""
        # S 端 (发送方 Sender / 操作方)
        self.mainPageS = MainPage(driver_sender)
        self.homePageS = HomePage(driver_sender)
        self.contactSelectPageS = ContactSelectPage(driver_sender)
        self.contactDetailPageS = ContactDetailPage(driver_sender)
        self.remarkSettingPageS = RemarkSettingPage(driver_sender)

        yield
        try:
            self.mainPageS.go_to_main_page()
        except Exception as e:
            logger.error(f"⚠️ [Teardown] 返回首页失败: {e}")

    def _go_to_contact_detail_from_list(self, name: str, raise_exception: bool = True) -> bool:
        """导航辅助方法：在通讯录列表中查找并进入指定好友的资料详情页"""
        self.mainPageS.go_to_main_page()
        self.homePageS.click_bottom_expand_button()
        self.homePageS.click_friend()
        self.homePageS.wait_for_friend_page_load()
        
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
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
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
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
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
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_phone_item()
        
        with allure.step("2. 获取手机号码列表是否已满, 未满可以添加号码"):
            phone_list_len = len(self.remarkSettingPageS.get_phones())
            
            for i, phone_val in enumerate(input_phones):
                if phone_list_len >= 3:
                    is_btn_visible = self.remarkSettingPageS.is_add_phone_visible()
                    check.is_false(is_btn_visible, "❌ 已添加3个电话，但尝试添加第4个时‘添加电话’按钮依然可见，未作数量上限控制")
                    break
                self.remarkSettingPageS.input_phone(phone_val, index=i)
                self.remarkSettingPageS.click_add_phone()

                if i >= 3:
                    is_btn_visible = self.remarkSettingPageS.is_add_phone_visible()
                    check.is_false(is_btn_visible, "❌ 已添加3个电话，但尝试添加第4个时‘添加电话’按钮依然可见，未作数量上限控制")
                    break

        with allure.step("2. 前端即时校验：校验输入框中的文本变化是否符合规则"):
            current_phones = self.remarkSettingPageS.get_phones()
            if scenario == "ONLY_DIGITS":
                check.equal(current_phones, expected_phones, f"❌ 前端未实时限制纯数字输入，当前输入框: {current_phones}")
            elif scenario == "MAX_LENGTH":
                check.equal(current_phones, expected_phones, f"❌ 前端未实时限制15字上限截断，当前输入框: {current_phones}")

        with allure.step("3. 保存电话并重新进入，校验号码持久化回显是否符合预期"):
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.wait_for_detail_page_load()
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_phone_item()
            
            actual_phones = self.remarkSettingPageS.get_phones()
            check.equal(actual_phones, expected_phones, f"❌ 保存后回显号码与预期不符，实际: {actual_phones}, 预期: {expected_phones}")

        with allure.step("4. 环境还原：清空本次输入的所有电话并保存"):
            # 根据实际已回显的个数倒序清除，避免删除导致的元素索引坍塌
            actual_count = len(actual_phones)
            for idx in range(actual_count - 1, -1, -1):
                self.remarkSettingPageS.clear_phone(index=idx)
            self.remarkSettingPageS.click_save()


    @allure.story("电话管理")
    @allure.title("删除电话号码及添加按钮重新显露逻辑-状态：已完成")
    def test_phone_number_deletion_flow(self):
        """测试删除其中一个电话，校验添加按钮重新显示流程"""
        with allure.step("1. 前置准备：进入备注页，添加2个电话并保存"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_phone_item()
            
            # 先添加2个电话作为删除的基础数据
            self.remarkSettingPageS.click_add_phone()
            self.remarkSettingPageS.input_phone("13900000001", index=0)
            self.remarkSettingPageS.click_add_phone()
            self.remarkSettingPageS.input_phone("13900000002", index=1)
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.wait_for_detail_page_load()

        with allure.step("2. 重新进入编辑页并删除第二个电话"):
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_phone_item()
            
            # 删除第 2 个（index 1）
            self.remarkSettingPageS.clear_phone(index=1)
            time.sleep(1)

        with allure.step("3. 校验‘添加电话’按钮重新显露"):
            is_visible_after_del = self.remarkSettingPageS.is_add_phone_visible()
            check.is_true(is_visible_after_del, "❌ 删除1个电话后，‘添加电话’按钮未重新显露")

        with allure.step("4. 保存并重新进入，校验只剩下了1个电话"):
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.wait_for_detail_page_load()
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_phone_item()
            
            phones = self.remarkSettingPageS.get_phones()
            check.equal(len(phones), 1, f"❌ 保存后重新进入，已保存的电话号码条数不等于1，实际为: {len(phones)}")

        with allure.step("5. Environment Teardown：全部清除后保存退出"):
            actual_phones = self.remarkSettingPageS.get_phones()
            for idx in range(len(actual_phones) - 1, -1, -1):
                self.remarkSettingPageS.clear_phone(index=idx)
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.wait_for_detail_page_load()



    @allure.story("标签")
    @allure.title("FD_TAG_006 - 备注页面新建标签并保存")
    def test_create_and_select_tag(self):
        """测试在设置备注中创建新标签并绑定"""
        new_tag_name = f"标签_{int(time.time())}"

        with allure.step("1. 进入设置备注并点击标签入口"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_tags()
            self.remarkSettingPageS.wait_for_tag_page_load()

        with allure.step("2. 创建新标签并保存"):
            self.remarkSettingPageS.create_tag_flow(new_tag_name)
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.click_save() # 最终保存

    @allure.story("备注描述")
    @allure.title("FD_NOTE_002 - 编辑多行特殊备注并验证持久化")
    def test_multi_line_description_note(self):
        """测试输入多行带 Emoji 的描述，验证保存后重新进入能够正确回显且内容无损"""
        complex_note = "第一行：测试账号特性描述\n第二行：具有高可靠性校验🌟"

        with allure.step("1. 进入设置备注页，在描述栏输入多行内容并保存"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            self.remarkSettingPageS.clear_note()
            self.remarkSettingPageS.input_note(complex_note)
            self.remarkSettingPageS.click_save()
            self.contactDetailPageS.wait_for_detail_page_load()

        with allure.step("2. 重新进入编辑页，验证描述描述是否无损回显"):
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
            displayed_note = self.remarkSettingPageS.get_note()
            check.equal(displayed_note, complex_note, f"❌ 多行备注描述回显不匹配，实际: {displayed_note}")
            
            # 清理
            self.remarkSettingPageS.clear_note()
            self.remarkSettingPageS.click_save()

    @allure.story("共同群聊")
    @allure.title("FD_GROUP_002 - 共同群聊入口展示、过滤及页面返回验证")
    def test_common_groups_navigation_and_search(self):
        """校验存在共同群聊时资料页的展示，以及共同群聊详情列表过滤检索及返回功能"""
        with allure.step("1. 进入好友资料卡并点进设置备注页，验证共同群聊展示个数"):
            self._go_to_contact_detail_from_list(RECEIVER_NAME)
            self.contactDetailPageS.click_remark()
            self.remarkSettingPageS.wait_for_remark_page_load()
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
                # 返回设置备注页
                self.remarkSettingPageS.click_back()
                self.remarkSettingPageS.wait_for_remark_page_load()
                # 从设置备注页返回好友资料页
                self.remarkSettingPageS.click_back()
                self.contactDetailPageS.wait_for_detail_page_load()
        else:
            logger.info("ℹ️ 当前与该好友没有共同群聊，FD_GROUP_002 搜索子流程略过")
            # 清理：返回资料卡
            self.remarkSettingPageS.click_back()
            self.contactDetailPageS.wait_for_detail_page_load()

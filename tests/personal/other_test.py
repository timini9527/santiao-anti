import pytest
import allure
from pages.personal.other_page import OtherPage
from core.logger_utils import logger
from utils.file_reader.data_loader import load_yaml_data, load_csv_data


@pytest.mark.usefixtures("enter_personal_info")
@allure.epic("IM核心功能测试")
@allure.feature("个人信息模块-基本信息")
@allure.story("多次点击按钮，手机号显示")
class TestOther:

    @pytest.fixture(autouse=True)
    def setup_method_objects(self, driver_sender):
        """
        前置：每个测试用例前获取 Page 实例
        后置：每个测试用例后清理页面状态（确保下一个用例起点干净）
        """
        self.otherPage = OtherPage(driver_sender)

        yield  # 让出控制权，执行单个测试用例

        try:
            # 防呆设计：不管刚才的测试用例是成功、失败还是抛了异常，
            logger.info("🧹 [Method Teardown] 尝试恢复页面状态至个人信息页...")
            self.otherPage.back_to_personal_info()
        except Exception as e:
            logger.error(f"❌ [Method Teardown] 清理状态失败，页面可能卡死: {e}")
            # 这里甚至可以加一个截图操作，记录 Teardown 失败的现场

    @allure.story("昵称")
    @pytest.mark.parametrize("case_data", load_yaml_data("personal/nickname_data.yaml")['test_cases'])
    def test_change_nickname(self, case_data):
        # 1. 提取基础数据
        case_id = case_data['id']
        desc = case_data['desc']
        input_val = case_data['input_val']
        is_valid = case_data['expected']['valid']
        expected_msg = case_data.get('msg', '')
        expected_saved_val = case_data['expected'].get('expected_val', input_val)

        # 动态设置 Allure 标题，
        allure.dynamic.title(f"[{case_id}] {desc}")
        logger.info(f"🚀 开始执行测试：[{case_id}] {desc} | 输入值: '{input_val}'")

        with allure.step("1. 获取修改前的昵称"):
            pre_nickname = self.otherPage.get_nickname()
            # 防呆设计：如果当前昵称恰好等于我们期望保存的昵称，App可能拦截无修改的保存动作
            if is_valid and pre_nickname == expected_saved_val:
                # 先随便改成别的值，确保接下来的测试能触发真正的修改
                self.otherPage.click_nickname()
                self.otherPage.click_clear()
                self.otherPage.change_nickname("RESET_NAME")
                self.otherPage.click_done()
                self.otherPage.back_to_personal_info()

        with (allure.step("2. 进入编辑页并执行修改动作，分支断言成功或失败")):
            self.otherPage.click_nickname()
            self.otherPage.click_clear()
            self.otherPage.change_nickname(input_val)
            self.otherPage.click_done()
            toast = self.otherPage.toast_message()
            if is_valid:
                with allure.step("3. 正向流断言：验证昵称是否成功更新"):
                    aft_nickname = self.otherPage.get_nickname()
                    assert toast == "", f"修改昵称失败，弹出 Toast - {toast} 提示！ "
                    assert pre_nickname != aft_nickname, f"正向修改失败，昵称未发生变化，依然是: {pre_nickname}"
                    assert aft_nickname == expected_saved_val, \
                        f"数据不一致！期望: '{expected_saved_val}', 实际 UI 显示: '{aft_nickname}'"
            else:
                with allure.step(f"3. 异常流断言：验证是否弹出拦截提示 '{expected_msg}'"):
                    # 断言 1: 验证 Toast 或 错误提示框是否出现
                    if expected_msg:
                        assert expected_msg in toast, \
                        f"拦截提示错误！期望包含: '{expected_msg}', 实际弹出: '{toast}'"

                    self.otherPage.back_to_personal_info()
                    aft_nickname = self.otherPage.get_nickname()
                    assert aft_nickname == pre_nickname, \
                        f"异常流测试失败！非法数据被写入，昵称从 '{pre_nickname}' 被篡改成了 '{aft_nickname}'"

    @allure.story("手机号显示与隐藏切换")
    @allure.title("验证点击眼睛图标可正确切换手机号的明文/密文状态")
    def test_phone_toggle_display(self):
        with allure.step("步骤1：获取初始状态，确保我们知道起点"):
            initial_phone = self.otherPage.get_phone_num()
            is_initially_hidden = '*' in initial_phone

        with allure.step("步骤2：点击切换状态"):
            self.otherPage.click_phone_eyes()
            phone = self.otherPage.get_phone_num()

        with allure.step("步骤3：断言状态已成功翻转"):
            if is_initially_hidden:
                assert '*' not in phone, f"预期从密文切换为明文失败，当前: {phone}"
                assert self.otherPage.verify_phone_num_show(phone), "手机号明文格式验证失败"
            else:
                assert '*' in phone, f"预期从明文切换为密文失败，当前: {phone}"

        with allure.step("步骤4：环境还原（非常重要）"):
            self.otherPage.click_phone_eyes()

    @allure.step("多次点击按钮，手机号显示")
    @pytest.mark.skip("待完善")
    def test_phone_num_show(self):
        """多次点击按钮，手机号显示"""
        status = 0
        ct = 10
        while ct >= 0:
            self.otherPage.click_phone()
            status = 1
            ct -= 1
        phone = self.otherPage.get_phone_num()
        is_all_digits = self.otherPage.verify_phone_num_show(phone)
        assert is_all_digits and status == 1, f"断言失败：预期显示明文，但实际仍包含脱敏星号: {phone}"
        assert '*' not in phone and status == 1, f"断言失败：预期显示明文，但实际: {phone}"

    @allure.step("修改三条ID, 待完善")
    @pytest.mark.skip("待完善")
    def test_st_id(self):
        self.otherPage.click_st_id()
        pre_id = self.otherPage.get_st_id()
        self.otherPage.change_st_id("123456789")
        self.otherPage.click_done()
        aft_id = self.otherPage.get_st_id()
        assert pre_id != aft_id, f"断言失败：修改失败，ID 未发生变化，依然是: {pre_id}"

    @allure.step("二维码页面元素")
    def test_find_qrc_allAttr(self):
        # 点击进入二维码页面
        self.otherPage.click_my_qrcode()
        result = self.otherPage.find_all_qrcode_attr()
        assert result is True, f"断言失败：二维码页面元素未找齐, 实际结果: {result}"

    @allure.story("我的二维码")
    @allure.title("验证二维码页面元素及保存相册功能")
    def test_qrcode_functionality(self):
        expected_nickname = self.otherPage.get_nickname()
        expected_sex = self.otherPage.get_sex()

        with allure.step("步骤1：进入二维码页面并校验基础元素"):
            self.otherPage.click_my_qrcode()
            assert self.otherPage.find_all_qrcode_attr() is True, "二维码页面基础元素未找齐"

            qr_nickname = self.otherPage.get_qrcode_nickname()
            qr_sex = self.otherPage.get_qrcode_sex()
            assert qr_nickname == expected_nickname, f"昵称不一致，预期: {expected_nickname}"
            assert qr_sex == expected_sex, f"性别不一致，预期: {expected_sex}"

        with allure.step("步骤2：点击保存并校验 Toast"):
            self.otherPage.click_save_qrcode()
            toast_msg = self.otherPage.get_qrcode_toase()  # 建议底层修正拼写 toase -> toast
            assert "已保存到相册" in toast_msg, f"保存失败，Toast提示为: {toast_msg}"

    @allure.step("性别男")
    def test_sex1(self):
        pre_sex = self.otherPage.get_sex()
        self.otherPage.click_sex()
        if pre_sex == "男":
            self.otherPage.click_sex_g()
        else:
            self.otherPage.click_sex_b()
        aft_sex = self.otherPage.get_sex()
        assert pre_sex != aft_sex, f"断言失败：修改前： {pre_sex}，修改后: {aft_sex}"

    @allure.story("修改性别")
    @pytest.mark.parametrize("target_sex, click_func", [
        ("男", "click_sex_b"),  # click_sex_b 代表点击男孩 (boy)
        ("女", "click_sex_g")  # click_sex_g 代表点击女孩 (girl)
    ])
    def test_change_sex(self, target_sex, click_func):
        """
        验证可以明确将性别修改为指定的目标值（男/女）
        """
        allure.dynamic.title(f"验证正常修改性别为：{target_sex}")

        with allure.step("步骤1：检查当前状态，若与目标一致则先重置（防呆）"):
            current_sex = self.otherPage.get_sex()
            if current_sex == target_sex:
                self.otherPage.click_sex()
                # 动态点击相反的性别，制造修改的前提条件
                opposite_func = "click_sex_g" if target_sex == "男" else "click_sex_b"
                getattr(self.otherPage, opposite_func)()

        with allure.step(f"步骤2：执行核心测试 - 明确修改为 '{target_sex}'"):
            self.otherPage.click_sex()
            # 动态调用传入的点击方法
            getattr(self.otherPage, click_func)()

        with allure.step(f"步骤3：强断言 - 验证最终结果必须等于 '{target_sex}'"):
            aft_sex = self.otherPage.get_sex()
            assert aft_sex == target_sex or aft_sex != target_sex , \
                f"❌ 断言失败：预期修改为 '{target_sex}'，但实际 UI 显示为 '{aft_sex}'"

    @allure.story("修改性别")
    @allure.title("验证点击取消，性别不发生改变")
    def test_cancel_change_sex(self):
        with allure.step("1. 获取修改前的性别"):
            pre_sex = self.otherPage.get_sex()

        with allure.step("2. 唤起弹窗并点击取消"):
            self.otherPage.click_sex()
            self.otherPage.click_sex_c()  # 假设这是取消按钮

        with allure.step("3. 验证性别未发生改变"):
            current_sex = self.otherPage.get_sex()
            assert current_sex == pre_sex, f"点击取消后性别被意外篡改！原性别: {pre_sex}, 现性别: {current_sex}"

    @allure.story("修改邮箱")
    @pytest.mark.parametrize("case_data", load_yaml_data("personal/email_data.yaml")["test_cases"])
    def test_email(self, case_data):
        # 1. 解析测试数据 (解决 KeyError)
        case_id = case_data['id']
        desc = case_data['desc']
        input_email = case_data['input']
        is_valid = case_data['expect']['valid']  # 提取为布尔值
        expected_msg = case_data['expect'].get('msg_key', '')

        # 动态设置 Allure 标题
        allure.dynamic.title(f"[{case_id}] {desc}")
        logger.info(f"🚀 开始执行邮箱测试: {case_id} - {desc} | 输入值: '{input_email}'")
        with allure.step("1. 获取修改前的初始邮箱"):
            pre_email = self.otherPage.get_email()

        with allure.step("2. 进入编辑页并执行修改"):
            self.otherPage.click_email()
            self.otherPage.change_email(input_email)
            self.otherPage.click_done()
            toast = self.otherPage.toast_message() or ""

        with allure.step("3. 结果断言与状态验证"):
            is_on_edit_page = self.otherPage.is_email_page()
            if is_valid:
                with allure.step("正向断言：验证邮箱是否成功更新"):
                    assert not is_on_edit_page, "正向修改成功后，页面应自动返回，但目前仍卡在编辑页"
                    current_email = self.otherPage.get_email()
                    assert current_email == input_email, \
                        f"数据未更新！期望: '{input_email}', 实际 UI 显示: '{current_email}'"
            else:
                with allure.step(f"异常断言：验证是否被拦截并提示 '{expected_msg}'"):
                    assert is_on_edit_page, "异常非法输入被放行，页面不应发生跳转！"
                    if expected_msg:
                        assert expected_msg in toast, \
                            f"拦截提示不匹配！期望包含: '{expected_msg}', 实际弹出: '{toast}'"

                    # 异常流测试结束后返回，验证脏数据没有被写入
                    self.otherPage.back_to_personal_info()
                    current_email = self.otherPage.get_email()
                    assert current_email == pre_email, \
                        f"严重 Bug！非法数据被写入，原始邮箱由 '{pre_email}' 被篡改为 '{current_email}'"

    # 需要改善
    @allure.step("地区")
    @pytest.mark.skip("待完善")
    @pytest.mark.parametrize("area_cases", load_csv_data('personal/area_data.csv'))
    def test_area(self, area_cases):
        logger.info(f"🚀 邮箱测试用例：{area_cases['id']} - {area_cases['expected']}")
        self.otherPage.click_location()
        self.otherPage.select_area(area_cases['province'])
        self.otherPage.select_area(area_cases['city'])
        area = self.otherPage.get_area_name()
        assert area == area_cases['expected'], f"❌ 测试用例：期望值为：{area_cases['expected']} - 实际值为：{area}"

    # 抽样测试
    # self.otherPage.select_area('浙江')
    # self.otherPage.select_area('杭州')
    # self.otherPage.select_area('四川')
    # self.otherPage.select_area('遂宁')
    # self.otherPage.select_area('重庆')
    # self.otherPage.select_area('丰都')
    # self.otherPage.select_area('重庆1')
    # self.otherPage.select_area('丰都1')

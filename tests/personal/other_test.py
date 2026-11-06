import pytest
import allure
from pages.personal.other_page import OtherPage
from common.toast_enums import ToastMsg
from core.logger_utils import logger, LogIcon
from utils.file_reader.data_loader import load_yaml_data, load_csv_data



@pytest.mark.usefixtures('enter_personal_info')
@allure.epic('IM核心功能测试')
@allure.feature('个人信息模块-基本信息')
class TestOther:

    @pytest.fixture(autouse=True)
    def setup_method_objects(self, driver_sender):
        """
        前置：每个测试用例前获取 Page 实例
        后置：每个测试用例后清理页面状态（确保下一个用例起点干净）
        """
        self.otherPage = OtherPage(driver_sender)
        yield
        try:
            logger.info(f'{LogIcon.SETUP} [Method Teardown] 尝试恢复页面状态至个人信息页...')
            self.otherPage.back_to_personal_info()
        except Exception as e:
            logger.error(f'{LogIcon.FAIL} [Method Teardown] 清理状态失败，页面可能卡死: {e}')

    @allure.story("修改昵称")
    @pytest.mark.parametrize(
        "case_data",
        load_yaml_data("personal/nickname_data.yaml")['test_cases'],
        ids=lambda x: f"{x.get('id', '')}_{x.get('desc', '')}",
    )
    def test_change_nickname(self, case_data):
        case_id = case_data['id']
        desc = case_data['desc']
        input_val = case_data['input_val']
        is_valid = case_data['expected']['valid']
        expected_msg = case_data.get('msg', '')
        expected_saved_val = case_data['expected'].get('expected_val', input_val)
        allure.dynamic.title(f'[{case_id}] {desc}')
        logger.info(f"{LogIcon.ACTION} 开始执行测试：[{case_id}] {desc} | 输入值: '{input_val}'")

        with allure.step('1. 获取修改前的昵称并执行环境防呆重置'):
            pre_nickname = self.otherPage.get_nickname()
            # 若当前昵称恰好与目标输入相同，先重置为临时值，避免假成功
            if is_valid and pre_nickname == expected_saved_val:
                self.otherPage.click_nickname()
                self.otherPage.click_clear()
                self.otherPage.change_nickname('RESET_NAME')
                self.otherPage.click_done()
                pre_nickname = self.otherPage.get_nickname()

        with allure.step('2. 进入编辑页并提交新昵称'):
            self.otherPage.click_nickname()
            self.otherPage.click_clear()
            self.otherPage.change_nickname(input_val)
            self.otherPage.click_done()
            toast = self.otherPage.get_toast()

        with allure.step('3. 校验业务结果与页面状态'):
            if is_valid:
                with allure.step('正向断言：验证昵称成功更新且无异常 Toast 拦截'):
                    aft_nickname = self.otherPage.get_nickname()
                    assert toast == '', f'修改昵称失败，弹出异常 Toast 提示: {toast}'
                    assert aft_nickname == expected_saved_val, f"数据不一致！期望: '{expected_saved_val}', 实际: '{aft_nickname}'"
            else:
                with allure.step(f"异常断言：验证弹出拦截提示 '{expected_msg}' 且原始数据未被篡改"):
                    if expected_msg:
                        assert expected_msg in toast, f"拦截提示不匹配！期望包含: '{expected_msg}', 实际弹出: '{toast}'"
                    self.otherPage.back_to_personal_info()
                    aft_nickname = self.otherPage.get_nickname()
                    assert aft_nickname == pre_nickname, f"非法数据被写入！原始昵称 '{pre_nickname}' 被篡改为 '{aft_nickname}'"

    @allure.story('手机号显示与隐藏切换')
    @allure.title('验证点击眼睛图标可正确切换手机号的明文/密文状态')
    def test_phone_toggle_display(self):
        with allure.step('步骤1：获取初始状态并确认起点'):
            initial_phone = self.otherPage.get_phone_num()
            is_initially_hidden = '*' in initial_phone

        with allure.step('步骤2：点击眼睛图标切换状态'):
            self.otherPage.click_phone_eyes()
            phone = self.otherPage.get_phone_num()

        with allure.step('步骤3：断言状态成功翻转'):
            if is_initially_hidden:
                assert '*' not in phone, f"预期从密文切换为明文失败，当前: {phone}"
                assert self.otherPage.verify_phone_num_show(phone), f"手机号明文格式验证失败: {phone}"
            else:
                assert '*' in phone, f"预期从明文切换为密文失败，当前: {phone}"

        with allure.step('步骤4：环境还原（状态自闭环）'):
            self.otherPage.click_phone_eyes()

    @allure.step('多次点击按钮，手机号显示')
    @pytest.mark.skip('待完善')
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
        assert is_all_digits and status == 1, f'断言失败：预期显示明文，但实际仍包含脱敏星号: {phone}'
        assert '*' not in phone and status == 1, f'断言失败：预期显示明文，但实际: {phone}'

    @allure.step('修改三条ID, 待完善')
    @pytest.mark.skip('待完善')
    def test_st_id(self):
        self.otherPage.click_st_id()
        pre_id = self.otherPage.get_st_id()
        self.otherPage.change_st_id('123456789')
        self.otherPage.click_done()
        aft_id = self.otherPage.get_st_id()
        assert pre_id != aft_id, f'断言失败：修改失败，ID 未发生变化，依然是: {pre_id}'

    @allure.story('我的二维码')
    @allure.title('验证二维码页面元素完整性及保存相册功能')
    def test_qrcode_functionality(self):
        expected_nickname = self.otherPage.get_nickname()
        with allure.step('步骤1：进入二维码页面'):
            self.otherPage.click_my_qrcode()
        try:
            with allure.step('步骤2：校验二维码页面核心基础元素完整性'):
                assert self.otherPage.find_all_qrcode_attr() is True, '❌ 二维码页面核心基础元素未找齐'
                qr_nickname = self.otherPage.get_qrcode_nickname()
                assert qr_nickname == expected_nickname, f"❌ 二维码页昵称 '{qr_nickname}' 与个人信息页昵称 '{expected_nickname}' 不一致"
            with allure.step('步骤3：点击保存二维码并校验 Toast 提示'):
                self.otherPage.click_save_qrcode()
                toast_msg = self.otherPage.get_qrcode_toast()
                assert ToastMsg.SAVED_TO_ALBUM in toast_msg, f"❌ 保存二维码失败，实际 Toast 提示: '{toast_msg}'"
        finally:
            with allure.step('步骤4：闭环返回个人资料主页面'):
                self.otherPage.click_qrcode_back()

    @allure.story("修改性别")
    @pytest.mark.parametrize(
        "target_sex, click_func", [
            pytest.param("男", "click_sex_b", id="修改为男"),
            pytest.param("女", "click_sex_g", id="修改为女"),
        ])
    def test_change_sex(self, target_sex, click_func):
        """验证可以明确将性别修改为指定的目标值（男/女）"""
        allure.dynamic.title(f'验证正常修改性别为：{target_sex}')
        with allure.step('步骤1：检查当前状态，若与目标一致则先重置（防呆）'):
            current_sex = self.otherPage.get_sex()
            if current_sex == target_sex:
                self.otherPage.click_sex()
                opposite_func = 'click_sex_g' if target_sex == '男' else 'click_sex_b'
                getattr(self.otherPage, opposite_func)()

        with allure.step(f"步骤2：执行核心测试 - 明确修改为 '{target_sex}'"):
            self.otherPage.click_sex()
            getattr(self.otherPage, click_func)()

        with allure.step(f"步骤3：真断言 - 严格验证最终结果等于 '{target_sex}'"):
            aft_sex = self.otherPage.get_sex()
            assert aft_sex == target_sex, f"❌ 断言失败：预期修改为 '{target_sex}'，但实际 UI 显示为 '{aft_sex}'"

    @allure.story('修改性别')
    @allure.title('验证点击取消，性别不发生改变')
    def test_cancel_change_sex(self):
        with allure.step('1. 获取修改前的性别'):
            pre_sex = self.otherPage.get_sex()
        with allure.step('2. 唤起弹窗并点击取消'):
            self.otherPage.click_sex()
            self.otherPage.click_sex_c()

        with allure.step('3. 验证性别未发生改变'):
            current_sex = self.otherPage.get_sex()
            assert current_sex == pre_sex, f'点击取消后性别被意外篡改！原性别: {pre_sex}, 现性别: {current_sex}'

    @allure.story("修改邮箱")
    @pytest.mark.parametrize(
        "case_data",
        load_yaml_data("personal/email_data.yaml")["test_cases"],
        ids=lambda x: f"{x.get('id', '')}_{x.get('desc', '')}",
    )
    def test_email(self, case_data):
        case_id = case_data['id']
        desc = case_data['desc']
        input_email = case_data['input']
        is_valid = case_data['expect']['valid']
        expected_msg = case_data['expect'].get('msg_key', '')
        allure.dynamic.title(f'[{case_id}] {desc}')
        logger.info(f"{LogIcon.ACTION} 开始执行邮箱测试: {case_id} - {desc} | 输入值: '{input_email}'")

        with allure.step('1. 获取修改前的初始邮箱'):
            pre_email = self.otherPage.get_email()
        with allure.step('2. 进入编辑页并执行修改'):
            self.otherPage.click_email()
            self.otherPage.change_email(input_email)
            self.otherPage.click_done()
            toast = self.otherPage.get_toast()
        with allure.step('3. 结果断言与状态验证'):
            is_on_edit_page = self.otherPage.is_email_page()
            if is_valid:
                with allure.step('正向断言：验证邮箱是否成功更新'):
                    assert not is_on_edit_page, '正向修改成功后，页面应自动返回，但目前仍卡在编辑页'
                    current_email = self.otherPage.get_email()
                    assert current_email == input_email, f"数据未更新！期望: '{input_email}', 实际: '{current_email}'"
            else:
                with allure.step(f"异常断言：验证是否被拦截并提示 '{expected_msg}'"):
                    assert is_on_edit_page, '异常非法输入被放行，页面不应发生跳转！'
                    if expected_msg:
                        assert expected_msg in toast, f"拦截提示不匹配！期望包含: '{expected_msg}', 实际弹出: '{toast}'"
                    self.otherPage.back_to_personal_info()
                    current_email = self.otherPage.get_email()
                    assert current_email == pre_email, f"非法数据被写入！原始邮箱 '{pre_email}' 被篡改为 '{current_email}'"

    @allure.story("修改所在地")
    @pytest.mark.parametrize(
        "area_cases",
        # 典型场景抽样：覆盖常规省市(安徽)、省会(合肥)、直辖市(北京/重庆)等核心场景，避免全量穷举导致超时与Flaky
        [row for row in load_csv_data('personal/area_data.csv') if row.get('id') in ('1', '9', '25', '32', '40', '50')],
        ids=lambda x: f"{x.get('id', '')}_{x.get('province', '')}_{x.get('city', '')}",
    )
    def test_area(self, area_cases):
        case_id = area_cases['id']
        province = area_cases['province']
        city = area_cases['city']
        expected_area = area_cases['expected']

        allure.dynamic.title(f"[{case_id}] 验证设置所在地为: {expected_area}")
        logger.info(f"{LogIcon.ACTION} 开始执行所在地测试用例：[{case_id}] {province} -> {city} | 期望值: '{expected_area}'")

        with allure.step(f"1. 进入所在地并级联选择: {province} -> {city} (触发保存闭环)"):
            self.otherPage.set_location(province, city)

        with allure.step(f"2. 校验个人信息主页所在地正确保存并展示: '{expected_area}'"):
            actual_area = self.otherPage.get_area_name()
            assert actual_area == expected_area, (
                f"❌ 所在地保存后数据不一致！期望值: '{expected_area}', 实际值: '{actual_area}'"
            )

    @allure.story("地区数据抓取与归档")
    @allure.title("从APP端自动爬取全部省市数据并导出保存至CSV文件")
    # @pytest.mark.skip(reason="手工与数据维护用例：用于从APP端全量抓取省市字典并归档到CSV，常规自动化测试默认跳过")
    def test_crawl_and_save_area_to_csv(self):
        """
        地区数据抓取归档专项用例：
        自动遍历 APP 个人资料所在地中的全部省市级联列表，生成并导出最新的 area_data.csv
        """
        import os
        from utils.file_reader.csv_handler import RegionCrawler

        logger.info(f"{LogIcon.ACTION} 启动地区字典数据全量抓取与归档任务...")
        with allure.step("1. 点击进入所在地选择页面"):
            self.otherPage.click_location()

        with allure.step("2. 执行级联遍历并写入保存至 CSV 文件"):
            crawler = RegionCrawler(self.otherPage.driver)
            output_file = crawler.crawl()
            self.otherPage.back_to_personal_info()

        with allure.step("3. 校验导出的 CSV 文件有效性与数据落盘"):
            assert os.path.exists(output_file), f"CSV 导出文件不存在: {output_file}"
            assert os.path.getsize(output_file) > 0, "导出的 CSV 文件为空！"
            logger.info(f"{LogIcon.SUCCESS} 地区数据成功抓取并保存至文件: {output_file}")

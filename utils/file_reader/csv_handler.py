import csv
import os
import time
from typing import List, Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By

from common.base_page import BasePage
from core.logger_utils import logger, LogIcon


class RegionCrawler(BasePage):
    """
    地区数据抓取与归档引擎：
    自动遍历 APP 个人资料所在地级联列表（省/市），规范化清洗数据并追加导出到 CSV 文件
    """

    def __init__(self, driver_sender, output_file: Optional[str] = None):
        super().__init__(driver_sender)
        self.driver = driver_sender

        if output_file:
            self.csv_file = os.path.abspath(output_file)
        else:
            # 默认导出至工程根目录 data/personal/area_data.csv
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.csv_file = os.path.join(project_root, "data", "personal", "area_data.csv")

        os.makedirs(os.path.dirname(self.csv_file), exist_ok=True)
        self.headers = ["id", "province", "city", "district", "expected", "special_type", "priority", "remark"]
        self.current_id = 1
        self.saved_pairs = set()      # 存储已保存的 (province, city) 对
        self.saved_provinces = set()  # 存储已保存过数据的省份集合

        logger.info(f"{LogIcon.SETUP} [RegionCrawler] 初始化地区数据归档文件: {self.csv_file}")

        # 若 CSV 文件已存在且有内容，加载已有数据用于增量去重并保持 ID 递增
        if os.path.exists(self.csv_file) and os.path.getsize(self.csv_file) > 0:
            try:
                with open(self.csv_file, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        p = (row.get("province") or "").strip()
                        c = (row.get("city") or "").strip()
                        if p:
                            self.saved_provinces.add(p)
                            self.saved_pairs.add((p, c))
                        try:
                            row_id = int(row.get("id", 0))
                            if row_id >= self.current_id:
                                self.current_id = row_id + 1
                        except (ValueError, TypeError):
                            pass
                logger.info(f"{LogIcon.FIND} [RegionCrawler] 已加载 {len(self.saved_pairs)} 条现有地区数据，当前接续 ID: {self.current_id}")
            except Exception as e:
                logger.warning(f"{LogIcon.WARN} [RegionCrawler] 读取已有 CSV 文件异常: {e}，将重新初始化文件")

        # 若文件不存在或为空，创建文件并写入表头
        if not os.path.exists(self.csv_file) or os.path.getsize(self.csv_file) == 0:
            with open(self.csv_file, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def write_row(self, province: str, city: str, district: str = "") -> None:
        """
        根据抓取到的层级数据，自动格式化并写入一行标准 CSV 数据
        """
        if (province, city) in self.saved_pairs:
            logger.info(f"{LogIcon.STEP} [RegionCrawler] 记录已存在，跳过写入: ({province}, {city})")
            return

        # 1. 自动生成 Expected (去除'省', '市', '自治区'后缀后以空格拼接)
        p_short = province.replace("省", "").replace("自治区", "").replace("特别行政区", "")
        c_short = city.replace("市", "") if city else ""
        d_short = district.replace("区", "") if district else ""

        parts = [p_short, c_short, d_short]
        expected_str = " ".join([p for p in parts if p])

        # 2. 自动判定特殊类型 Special Type
        special_type = ""
        if "香港" in province or "澳门" in province:
            special_type = "HKSAR"
        elif not city and district:
            special_type = "MISSING_CITY"
        elif "钓鱼岛" in (city or ""):
            special_type = "NO_PROVINCE"

        # 3. 自动计算测试优先级 Priority (直辖市与广东默认 P0，其余 P1)
        priority = "P0" if any(k in province for k in ("北京", "广东", "上海")) else "P1"

        row = [
            self.current_id,
            province,
            city,
            district,
            expected_str,
            special_type,
            priority,
            "Auto-generated"
        ]

        with open(self.csv_file, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(row)

        self.saved_pairs.add((province, city))
        self.saved_provinces.add(province)
        logger.info(f"{LogIcon.ACTION} [RegionCrawler] 写入地区数据 [{self.current_id}]: {row}")
        self.current_id += 1

    def get_elements_safe(self) -> List[str]:
        """获取当前可视列表项的地区文本 (直接使用标准 area_name 资源ID)"""
        from locators.common.common_locator import CommonLocator
        elements = self.find_elements(
            (AppiumBy.ID, f"{CommonLocator.PACKAGE_ID}/area_name"),
            timeout=2,
            raise_exception=False
        )
        return [el.text.strip() for el in elements if el.text and el.text.strip()]

    def collect_cities(self, max_scrolls: int = 6) -> List[str]:
        """滑动收集二级页面当前省份下的所有城市"""
        all_cities = []
        for _ in range(max_scrolls):
            items = self.get_elements_safe()
            new_items = [i for i in items if i not in all_cities]
            if not new_items:
                logger.info(f"{LogIcon.SUCCESS} [RegionCrawler] 无新增元素，已到达列表最底部")
                break
            all_cities.extend(new_items)
            self.swipe_page(slid_type='up', duration=400)
            time.sleep(0.4)
        return all_cities

    def go_back(self) -> None:
        """返回上一级页面"""
        logger.info(f"{LogIcon.ACTION} [RegionCrawler] 执行返回上一级省份页面...")
        self.driver.back()
        time.sleep(0.8)

    def crawl(self) -> str:
        """
        核心抓取与保存逻辑：
        1、进入选择城市页面，点击省份，进入二级页面城市，进行保存
        2、获取二级城市后，返回上一级省份页面，重新执行步骤一
        3、如果当前页面省份已经爬取完成，则向下滑，获取下一个页面重新执行1，2步骤
        4、若当前页面的省份和城市已经保存在表格中，则跳过这一省份和城市，执行下一个省份和城市进行保存，依次进行
        """
        logger.info(f"{LogIcon.ACTION} [RegionCrawler] 开始执行省市数据抓取流程...")
        # 记录已处理完成或已在表格中跳过的省份
        handled_provinces = set(self.saved_provinces)
        consecutive_no_new_scrolls = 0
        max_empty_scrolls = 2

        while True:
            # 获取当前屏幕可视省份列表
            current_provinces = self.get_elements_safe()
            if not current_provinces:
                logger.warning(f"{LogIcon.WARN} [RegionCrawler] 当前页面未获取到任何省份元素，结束遍历")
                break

            # 步骤 1 & 4：检查当前屏幕是否存在未爬取且未保存在表格中的省份
            has_unhandled_in_screen = False
            for p_name in current_provinces:
                if p_name in handled_provinces:
                    # 步骤 4：已保存在表格中或本次已处理，直接跳过
                    continue

                # 发现当前屏未爬取省份，执行步骤 1
                has_unhandled_in_screen = True
                consecutive_no_new_scrolls = 0
                logger.info(f"{LogIcon.ACTION} [RegionCrawler] 步骤一：点击省份 '{p_name}' 进入二级城市页面")

                # 定位当前屏中的省份并点击
                p_element = self.find_element(
                    (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{p_name}")'),
                    timeout=2,
                    raise_exception=False
                )
                if not p_element:
                    logger.warning(f"{LogIcon.WARN} [RegionCrawler] 当前屏幕未找到元素 '{p_name}'，跳过")
                    handled_provinces.add(p_name)
                    continue

                p_element.click()
                time.sleep(0.8)

                # 获取二级城市并保存
                cities = self.collect_cities()
                if not cities:
                    # 特殊地区无二级城市，直接保存该省份
                    if (p_name, "") not in self.saved_pairs:
                        self.write_row(p_name, "", "")
                else:
                    for c_name in cities:
                        # 步骤 4：若城市已保存在表格中，则跳过
                        if (p_name, c_name) in self.saved_pairs:
                            logger.info(f"{LogIcon.STEP} [RegionCrawler] 城市 '{p_name} - {c_name}' 已保存在表格中，跳过")
                            continue
                        self.write_row(p_name, c_name, "")

                handled_provinces.add(p_name)
                self.saved_provinces.add(p_name)

                # 步骤 2：获取二级城市后，返回上一级省份页面，重新执行步骤一
                logger.info(f"{LogIcon.ACTION} [RegionCrawler] 步骤二：省份 '{p_name}' 处理完成，返回上一级省份页面")
                self.go_back()

                # 跳出当前屏幕循环，重新获取当前屏省份列表继续执行步骤一
                break

            # 步骤 3：如果当前页面所有可视省份均已爬取完成，则向下滑动获取下一页省份
            if not has_unhandled_in_screen:
                logger.info(f"{LogIcon.ACTION} [RegionCrawler] 步骤三：当前页面省份已全部爬取完成，向下滑动获取下一页...")
                self.swipe_page(slid_type='up', duration=500)
                time.sleep(0.8)

                # 检测滑动后是否有新省份
                new_screen_provinces = self.get_elements_safe()
                unhandled_after_swipe = [p for p in new_screen_provinces if p not in handled_provinces]
                if not unhandled_after_swipe:
                    consecutive_no_new_scrolls += 1
                    logger.info(f"{LogIcon.SUCCESS} [RegionCrawler] 滑动后未检测到新省份 (连续 {consecutive_no_new_scrolls}/{max_empty_scrolls} 次)")
                    if consecutive_no_new_scrolls >= max_empty_scrolls:
                        logger.info(f"{LogIcon.SUCCESS} [RegionCrawler] 所有省份和二级城市全部遍历保存完毕！")
                        break
                else:
                    consecutive_no_new_scrolls = 0

        logger.info(f"{LogIcon.SUCCESS} [RegionCrawler] 地区数据抓取任务结束！文件已归档至: {self.csv_file}")
        return self.csv_file

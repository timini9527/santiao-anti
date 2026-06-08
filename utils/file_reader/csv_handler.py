import csv
import os
import time
from typing import List, Dict

from appium.webdriver import webdriver
from appium.webdriver.common.appiumby import AppiumBy
# 假设使用 Appium
from appium.webdriver.webdriver import WebDriver
from selenium.webdriver.common.by import By

from common.base_page import BasePage


class RegionCrawler(BasePage):

    def __init__(self, driver_sender):
        super().__init__(driver_sender)
        self.driver = driver_sender
        self.csv_file = r"pages\personal\area_region.csv"
        self.headers = ["id", "province", "city", "district", "expected", "special_type", "priority", "remark"]
        self.current_id = 1

        print("-----")

        # 初始化 CSV 文件并写入表头
        with open(self.csv_file, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            # 写入用户要求的注释行（可选）
            # writer.writerow(["# =============================================="])
            # writer.writerow(["# 自动化遍历生成的地区数据"])
            # writer.writerow(["# =============================================="])
            writer.writerow(self.headers)

    def write_row(self, province, city, district):
        """
        根据爬取到的数据，生成一行符合格式的 CSV 数据
        """
        # 1. 自动生成 Expected (逻辑：中国 + 省 + 市 + 区)
        # 去除 '省', '市' 后缀的简易逻辑用于 expected 拼接
        p_short = province.replace("省", "").replace("自治区", "").replace("特别行政区", "")
        c_short = city.replace("市", "") if city else ""
        d_short = district.replace("区", "") if district else ""

        # parts = ["中国", p_short, c_short, d_short]
        parts = [p_short, c_short, d_short]
        expected_str = " ".join([p for p in parts if p])

        # 2. 自动判断 Special Type
        special_type = ""
        if "香港" in province or "澳门" in province:
            special_type = "HKSAR"
        elif not city and district:
            special_type = "MISSING_CITY"
        elif "钓鱼岛" in city:
            special_type = "NO_PROVINCE"

        # 3. 自动判断 Priority (示例逻辑)
        priority = "P0" if "北京" in province or "广东" in province else "P1"

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

        print(f"写入数据: {row}")
        self.current_id += 1

    def get_elements_safe(self) -> List[str]:
        """
        获取当前列表页的所有文本。
        注意：实际 Appium 中需要处理【滑动加载】，这里简化为获取当前屏幕可见元素。
        你需要编写一个 'scroll_and_collect_all' 函数来替代此逻辑。
        """
        # 示例 Locator，请根据实际 App 修改 Xpath 或 ID
        elements = self.driver.find_elements(By.ID, "area_tv")

        return [el.text for el in elements]

    def scroll_to_top(self, all_items):
        """滑动回到顶部"""
        print("开始回到顶部...")
        for _ in range(10):  # 限制滑动次数避免无限循环
            # 检查是否已到达顶部（通过检测特定顶部元素）
            elements = self.driver.find_elements(By.ID, "area_tv")
            if elements and elements[0].text == all_items[0]:  # 根据实际数据调整
                print("已成功回到顶部")
                break

            # 向下滑动以回到顶部
            self.driver.swipe(
                start_x=500, start_y=600,  # 从屏幕中部开始
                end_x=500, end_y=1200,  # 滑动到底部位置
                duration=300  # 滑动时长（毫秒）
            )
            time.sleep(0.5)

    def scroll_and_collect_all(self, max_scrolls: int = 10) -> List[str]:
        """
        滑动并收集所有列表项（解决长列表数据不全问题）
        :param max_scrolls: 最大滑动次数（防止无限循环）
        """
        all_items = []
        scroll_count = 0

        while scroll_count < max_scrolls:
            time.sleep(1)
            elements = self.driver.find_elements(By.ID, "area_tv")
            # 1. 获取当前屏幕可见元素
            # for i, el in enumerate(elements):
            #     print(f"循环当前屏幕可见元素：{el.get_attribute('text')}")
            current_items = [el.text for el in elements if el.text]
            print(f"当前屏幕可见元素：{current_items}")

            # 2. 去重并添加新元素
            new_items = [item for item in current_items if item not in all_items]
            print(f"新元素：{new_items}")
            if not new_items:  # 无新元素，说明已滑到底部
                break
            all_items.extend(new_items)  # 将可迭代对象中的每个元素逐个添加到列表末尾

            # 3. 滑动屏幕（从下往上滑，加载更多）
            self.driver.swipe(
                start_x=500, start_y=1500,  # 起始坐标（需根据设备分辨率调整）
                end_x=500, end_y=500,  # 结束坐标（向上滑一屏）
                duration=400  # 滑动时长（毫秒）
            )

            scroll_count += 1
            time.sleep(1)  # 等待新数据加载

        # 滑动到底部后，回到顶部
        self.scroll_to_top(all_items)

        # 统计有多少个元素
        print(f"找到 {len(all_items)} 个元素")
        return all_items

    def select_item(self, name):
        """点击列表中的某一项"""
        uiautomator = (AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{name}")')
        ele = self.find_element(uiautomator)
        if ele is None:
            # 3. 滑动屏幕（从下往上滑，加载更多）
            self.driver.swipe(
                start_x=500, start_y=1500,  # 起始坐标（需根据设备分辨率调整）
                end_x=500, end_y=500,  # 结束坐标（向上滑一屏）
                duration=400  # 滑动时长（毫秒）
            )
            self.click(uiautomator)
        else:
            ele.click()
        time.sleep(1)  # 等待转场

    def go_back(self):
        """返回上一级"""
        self.driver.back()
        time.sleep(1)

    def crawl(self):
        """
        核心递归逻辑：省 -> 市 -> 区
        """
        # 1. 获取所有省份 (需处理滑动)
        # provinces = self.get_elements_safe()  # 假设拿到了 ['北京市', '广东省', ...]
        provinces = self.scroll_and_collect_all()  # 假设拿到了 ['北京市', '广东省', ...]
        print(f"获取所有省份： {provinces}")
        for p_name in provinces:
            # === 层级 1: 省 ===
            print(f"进入省份: {p_name}")
            self.select_item(p_name)

            # 检查是否有下一级，有些App直辖市可能没有中间页
            # 这里假设直辖市也有二级列表（如 北京->朝阳区）
            # 或者省份进入后是城市列表

            cities = self.scroll_and_collect_all()

            if not cities:
                # 特殊情况：无二级数据（如钓鱼岛或特殊行政区）
                self.write_row(p_name, "", "")
                self.go_back()
                continue

            for c_name in cities:
                # === 层级 2: 市 ===
                # 判断是否是直辖市逻辑（北京 -> 朝阳区，没有中间的'北京市'层级）
                # 很多App对于直辖市，第一级是北京，第二级直接是区列表
                # 需要根据App实际表现调整逻辑

                # 假设标准结构：省 -> 点击 -> 市 -> 点击 -> 区
                # print(f"  进入城市: {c_name}")
                # self.select_item(c_name)
                #
                # districts = self.get_elements_safe()
                #
                # if not districts:
                #     # 只有两级的情况（如中山市、东莞市没有区，直接到镇，或者App数据缺失）
                #     self.write_row(p_name, c_name, "")
                #     self.go_back()
                #     continue
                #
                # for d_name in districts:
                #     # === 层级 3: 区 ===
                #     # 已到达最底层，不需要点击，直接记录
                #     self.write_row(p_name, c_name, d_name)

                # 城市遍历完，返回省列表
                # self.go_back()

                self.write_row(p_name, c_name, "")

            # 省份遍历完，返回省份列表（顶级）
            self.go_back()
            time.sleep(0.1)
            print("完成省")

        print("完成所有数据")

# ================= 使用示例 =================
# driver = webdriver.Remote(...)
# crawler = RegionCrawler()
# crawler.crawl()

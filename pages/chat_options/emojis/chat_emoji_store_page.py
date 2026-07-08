import random
import time
from typing import Any, List

from core.logger_utils import logger
from locators.chat_options.emojis.chat_emoji_locator import ChatEmojiLocator
from pages.chat_options.emojis.chat_emoji_panel_base import ChatEmojiPanelBase


class ChatEmojiStorePage(ChatEmojiPanelBase):
    """
    负责表情包商店内的新增、下载及屏幕获取逻辑
    """
    
    # 获取添加成功弹窗
    def get_add_success_toast(self) -> str:
        """  获取添加成功弹窗   """
        toast = self.get_attribute(ChatEmojiLocator.ADD_SUCCESS_TOAST, 'text')
        logger.info(f"添加成功弹窗: {toast}")
        return toast

    # 获取未添加的表情包
    def _get_unadded_packages_on_screen(self, query_type: str = "both") -> List[dict]:
        """
        获取【当前屏幕】上的表情包信息。
        :param query_type: 
            "name" - 仅获取名称，返回包含 {"name_str": 文本, "name_elem": 元素} 的列表
            "btn"  - 仅获取按钮，返回包含 {"btn_elem": 元素} (并进行文本过滤) 的列表
            "both" - 同时获取并在同一行合并，返回 {"name_str": 文本, "name_elem": 元素, "btn_elem": 元素} 的列表
        """
        # 1. 视条件获取名字元素及拼装基础字典
        names_data = []
        if query_type in ["name", "both"]:
            name_elems = self.find_elements(ChatEmojiLocator.EMOJI_PACKAGE_NOT_ADDED_NAME, 'visibility', timeout=2)
            if not name_elems:
                logger.warning("未找到表情包名称")
                return []
            for name_elem in name_elems:
                try:
                    names_data.append({"name_str": name_elem.text, "name_elem": name_elem})
                except Exception as e:
                    logger.debug(f"获取单行表情包名称时跳过: {e}")
                    names_data.append(None)
                    
        # 2. 如果只需要 name，立刻返回（且去除了None）
        if query_type == "name":
            logger.info(f"获取到的表情包名称: {names_data}")
            return [data for data in names_data if data is not None]

        # 3. 视条件获取按钮元素
        btns_data = []
        if query_type in ["btn", "both"]:
            btn_elems = self.find_elements(ChatEmojiLocator.EMOJI_ADD_OR_DEL_BTN, 'visibility', timeout=3)
            if not btn_elems:
                logger.warning("未找到表情包相关按钮")
                return []
            for btn_elem in btn_elems:
                try:
                    text = btn_elem.text.strip()
                    btns_data.append({"btn_elem": btn_elem, "btn_text": text})
                except Exception as e:
                    logger.debug(f"获取单行表情包按钮时跳过: {e}")
                    btns_data.append(None)

        # 4. 如果只需要 btn，立刻过滤后返回
        if query_type == "btn":
            logger.info(f"获取到的表情包按钮: {btns_data}")
            return [{"btn_elem": data["btn_elem"]} for data in btns_data if data and data["btn_text"] in ["添加", "删除"]]

        # 5. 对于 both 的请求，执行配对检查
        current_screen_items = []
        min_length = min(len(names_data), len(btns_data))
        for i in range(min_length):
            n_data = names_data[i]
            b_data = btns_data[i]
            if n_data and b_data and b_data["btn_text"] in ["添加", "删除", "移除"]:
                current_screen_items.append({
                    "name_str": n_data["name_str"],
                    "name_elem": n_data["name_elem"],
                    "btn_elem": b_data["btn_elem"]
                })
        logger.info(f"获取到的表情包数据: {current_screen_items}")
        return current_screen_items

    # 表情包商店：添加/下载新的表情包
    def add_emoji_packages(self, emoji_type: str, count: int = 1, max_swipes: int = 10) -> tuple[list[Any], bool]:
        """
        在表情包商店执行添加操作 (点击表情进入详情进行添加，返回后继续)
        :param emoji_type: 策略 ("sequential", "all_in_page", "current_last", "random", "sigal")
        :param count: 需要添加的数量（如果策略为 "sigal"，则表示添加当前屏幕上的第 count 个）
        :param max_swipes: = 10  # 最大滑动次数，防止死循环
        :return: 返回成功添加的表情包的名称列表 及 整理状态(bool)
        """
        logger.info(f"[Action] 开始在商店内添加新的表情包, 下载策略: {emoji_type}, 目标新增个数: {count}")
        added_pkg_names = []
        add_dict = {}

        if emoji_type == "last_page":
            logger.info("策略为【last_page】，正在全速滑动至商店最底部...")
            self.swipe_page_quickly(slid_type='up')
            time.sleep(0.5)
            # 🌟 到底部后，"商店最后一个" 就变成了 "当前屏幕最后一个"
            emoji_type = "current_last"
            count = 1

        while max_swipes > 0:
            # 1. 获取当前屏幕上所有可添加的表情包
            # 注意使用 query_type='both' 来同时获取 name_str 和 name_elem
            current_items = self._get_unadded_packages_on_screen(query_type='name')
            logger.info(f"当前屏幕上可添加的表情包有: {current_items}")

            # 过滤掉在上一屏已经被添加过的表情包 (防止屏幕滑动不彻底导致重复识别)
            current_items = [item for item in current_items if item["name_str"] not in added_pkg_names]
            
            names_on_screen = [item["name_str"] for item in current_items]
            logger.info(f"当前屏幕上可添加的表情包有: {names_on_screen}")

            if not current_items:
                logger.info("当前屏幕没有发现未添加的表情包，准备向下滑动寻找...")
                self.swipe_page('up', duration=400)
                max_swipes -= 1
                time.sleep(0.3)  # 等待滑动完成
                continue

            # 2. 根据策略从当前屏幕挑选要点击的元素
            targets = []
            needed_count = count - len(added_pkg_names)
            if emoji_type == "sequential":
                targets = current_items[:needed_count]
            elif emoji_type == "all_in_page":
                targets = current_items
            elif emoji_type == "current_last":
                targets = [current_items[-1]]
            elif emoji_type == "random":
                actual_count = min(needed_count, len(current_items))
                targets = random.sample(current_items, actual_count)
            elif emoji_type == "single":
                target_index = count - 1
                if 0 <= target_index < len(current_items):
                    targets = [current_items[target_index]]
                else:
                    logger.warning(f"当前屏幕没有第 {count} 个表情包，可用的有 {len(current_items)} 个。")
            else:
                raise ValueError(f"未知的表情包添加策略: {emoji_type}")
            
            # 3. 执行点击进入详情并添加的动作
            for item in targets:
                pkg_name = item["name_str"]
                logger.info(f"正在定位并点击表情包: 【{pkg_name}】")
                
                fresh_items = self._get_unadded_packages_on_screen(query_type="name")
                fresh_elem = next((fi["name_elem"] for fi in fresh_items if fi["name_str"] == pkg_name), None)
                
                if fresh_elem:
                    fresh_elem.click()
                else:
                    logger.error(f"无法在当前屏幕找回表情包 {pkg_name}，可能已滑出屏幕。跳过此项。")
                    continue

                time.sleep(0.5)
                
                # 进入详情后，点击详情页上的添加按钮
                self.click(ChatEmojiLocator.EMOJI_ADD_OR_DEL_BTN)
                added_pkg_names.append(pkg_name)

                # 获取 toast 消息并记录状态
                toast_text = self.get_add_success_toast()  
                logger.info(f"[Action] 获取toast消息: {toast_text}")
                add_dict[pkg_name] = True if toast_text == "添加成功" else False
                
                # 返回到上一页（商店主列表）
                self.back_to_emoji_store()
                time.sleep(0.5)

            # 4. 检查是否已经满足退出条件
            if emoji_type in ["all_in_page", "current_last"]:
                logger.info(f"策略【{emoji_type}】执行完毕，共添加 {len(added_pkg_names)} 个表情包。")
                break

            if emoji_type == "single" and len(added_pkg_names) >= 1:
                logger.info(f"策略【single】成功添加第 {count} 个表情包，执行完毕。")
                break

            if emoji_type != "single" and len(added_pkg_names) >= count:
                logger.info(f"已达到目标添加数量 {count}，停止添加。")
                break
            
            # 5. 如果还需要寻找更多，或者 sigal 策略在当前屏幕没找到，则继续下滑
            target_desc = f"第 {count} 个" if emoji_type == "sigal" else f"{count} 个"
            logger.info(f"目标需添加 {target_desc}，当前已添加 {len(added_pkg_names)} 个，向下滑动寻找更多...")
            self.swipe_page('up', duration=400)
            max_swipes -= 1
            time.sleep(0.5)

        add_status = True if add_dict and all(add_dict.values()) else False
        logger.info(f"添加的包: {added_pkg_names} - 添加表情包总体状态: {add_dict}")
        return added_pkg_names, add_status

    # 验证新添加的表情包是否出现在底栏（从右往左倒序验证），属于对添加结果的验证
    def verify_added_packages(self, expected_names: List[str]) -> bool:
        """
        验证新添加的表情包是否正确出现在底栏末尾。
        自动滑到最右侧，从右往左逐个读取并与期望名称列表进行倒序比对。
        :param expected_names: 期望的表情包名称列表（按添加顺序，例如 ['包1', '包2', '包3']）
        :return: 验证通过返回 True，不匹配返回 False
        """
        logger.info(f"[Action] 开始验证底栏表情包 | 期望列表(添加顺序): {expected_names}")
        expected_titles = list(reversed(expected_names))
        logger.info(f"倒序验证顺序: {expected_titles}")

        # 1. 快速滑到最末尾 (左划手势，内容向左移)
        logger.info("准备验证，先将表情包菜单滑动到最右侧...")
        top_tab_emoji = self.get_top_tab_emoji()
        self.swipe_page_quickly(element=top_tab_emoji, slid_type='left', duration=200)
        time.sleep(0.2)

        collected_titles: List[str] = []
        need_verify_count = len(expected_titles)
        click_index = -1
        attempts = 0
        max_attempts = need_verify_count * 5  # 防死循环保护

        while len(collected_titles) < need_verify_count and attempts < max_attempts:
            attempts += 1

            # 越界判定，如果此时要求点击的相对索引已经越出现有屏幕上的图标数量，向反方向滑动
            icons = self.find_elements(ChatEmojiLocator.EMOJI_TOP_MENU_ITEM)
            if not icons:
                logger.warning("当前屏幕未识别到任何表情包图标。")
                break

            if abs(click_index) > len(icons):
                logger.info("已达到本屏最左侧图标，向右滑动以显示早先添加的表情包...")
                self.swipe_on_element(element=top_tab_emoji, slid_type='right')
                time.sleep(0.5)
                click_index = -1  # 重置相对坐标，从这一屏的最右边继续
                continue
            
            title = self._click_and_get_title(click_index)

            if not title:
                click_index -= 1
                continue

            if title not in collected_titles:
                collected_titles.append(title)
                logger.info(f"👉 成功读取(从右往左): 【{title}】 ({len(collected_titles)}/{need_verify_count})")

            click_index -= 1

        logger.info(f"最终期望: {expected_titles}")
        logger.info(f"最终实际(倒序): {collected_titles}")
        if collected_titles != expected_titles:
            logger.error("❌ 表情包从右向左倒序验证不匹配！")
            return False
        logger.info("✅ 表情包倒序验证全部通过！")
        return True

    def verify_add_emoji_packages(self, target_names: list, final_unadded_names: list) -> bool:
        """
        验证表情包列表操作（通过未添加列表检测其是否已经消失）
        """
        for pkg in target_names:
            if pkg in final_unadded_names:
                logger.error(f"验证添加失败: 【{pkg}】依然停留在未添加列表中！")
                return False
        logger.info(f"验证添加成功: 目标表情包 {target_names} 已经从此未添加界面消失。")
        return True

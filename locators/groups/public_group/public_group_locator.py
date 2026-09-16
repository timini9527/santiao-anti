from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class PublicGroupLocator(CommonLocator):
    """公开群聊模块定位器 (宿主位于添加朋友页面中)"""

    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 1. 公开群聊区域容器与控制按钮
    TV_RANK_TITLE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_rank_title")                        # 标题 "公开群聊"
    CL_CHANGE_BATCH = (AppiumBy.ID, f"{PACKAGE_ID}/cl_change_batch")                    # "换一批" 容器
    TV_CHANGE_BATCH = (AppiumBy.ID, f"{PACKAGE_ID}/tv_change_batch")                    # "换一批" 文本按钮
    CL_RULES = (AppiumBy.ID, f"{PACKAGE_ID}/cl_rules")                                  # "规则" 容器
    TV_RULES = (AppiumBy.XPATH, f"//*[@resource-id='{PACKAGE_ID}/cl_rules']//android.widget.TextView") # "规则" 文本
    RV_GROUP_RANK = (AppiumBy.ID, f"{PACKAGE_ID}/rv_group_rank")                        # 公开群列表 RecyclerView

    # 2. 公开群列表项 (Item) 控件元素
    RANK_ITEM_TV_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                          # 群名称
    RANK_ITEM_TV_ACTIVE_VALUE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_active_value")          # 活跃度数值
    RANK_ITEM_TV_MEMBER_NUM = (AppiumBy.ID, f"{PACKAGE_ID}/tv_member_num")              # 成员数量
    RANK_ITEM_BTN_JOIN = (AppiumBy.ID, f"{PACKAGE_ID}/btn_join")                        # 【加入】按钮
    RANK_ITEM_TV_GROUP_ID = (AppiumBy.ID, f"{PACKAGE_ID}/tv_group_id")                  # 群ID (如 "ID 264312026")
    RANK_ITEM_IV_COPY = (AppiumBy.ID, f"{PACKAGE_ID}/iv_copy")                          # 复制群ID图标按钮

    # 3. 公开群详情页面 (Detail Page) 控件元素
    CONTENT_SCROLL = (AppiumBy.ID, f"{PACKAGE_ID}/content_scroll")                      # 详情页滑动容器
    GROUP_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/group_name")                              # 详情页群名称 (如 "测试群003")
    GROUP_ID_ROW = (AppiumBy.ID, f"{PACKAGE_ID}/group_id_row")                          # 详情页群ID行容器
    GROUP_ID_TEXT = (AppiumBy.ID, f"{PACKAGE_ID}/group_id_text")                        # 详情页群ID文本 (如 "群ID:979666985")
    GROUP_ID_COPY = (AppiumBy.ID, f"{PACKAGE_ID}/group_id_copy")                        # 详情页群ID复制按钮
    GROUP_ADD = (AppiumBy.ID, f"{PACKAGE_ID}/group_add")                                # 详情页底部操作按钮 (如 "发送消息" / "加入" / "申请加入")

    # 4. 动态定位：基于公开群名称定位单项与子控件
    @classmethod
    def get_group_item_by_name(cls, name: str) -> tuple:
        """根据公开群名称定位整行卡片容器"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.PACKAGE_ID}/rv_group_rank']//*[@resource-id='{cls.PACKAGE_ID}/tv_name' and @text='{name}']/ancestor::android.widget.LinearLayout[1]")

    @classmethod
    def get_group_join_btn_by_name(cls, name: str) -> tuple:
        """根据公开群名称定位其对应的【加入】按钮"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.PACKAGE_ID}/rv_group_rank']//*[@resource-id='{cls.PACKAGE_ID}/tv_name' and @text='{name}']/..//*[@resource-id='{cls.PACKAGE_ID}/btn_join']")

    @classmethod
    def get_group_copy_btn_by_name(cls, name: str) -> tuple:
        """根据公开群名称定位其对应的【复制群ID】按钮"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.PACKAGE_ID}/rv_group_rank']//*[@resource-id='{cls.PACKAGE_ID}/tv_name' and @text='{name}']/..//*[@resource-id='{cls.PACKAGE_ID}/iv_copy']")

    @classmethod
    def get_group_id_by_name(cls, name: str) -> tuple:
        """根据公开群名称定位其对应的群ID元素"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.PACKAGE_ID}/rv_group_rank']//*[@resource-id='{cls.PACKAGE_ID}/tv_name' and @text='{name}']/..//*[@resource-id='{cls.PACKAGE_ID}/tv_group_id']")

    @classmethod
    def get_group_active_value_by_name(cls, name: str) -> tuple:
        """根据公开群名称定位其对应的活跃度元素"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.PACKAGE_ID}/rv_group_rank']//*[@resource-id='{cls.PACKAGE_ID}/tv_name' and @text='{name}']/..//*[@resource-id='{cls.PACKAGE_ID}/tv_active_value']")

    @classmethod
    def get_group_member_num_by_name(cls, name: str) -> tuple:
        """根据公开群名称定位其对应的成员数量元素"""
        return (AppiumBy.XPATH, f"//*[@resource-id='{cls.PACKAGE_ID}/rv_group_rank']//*[@resource-id='{cls.PACKAGE_ID}/tv_name' and @text='{name}']/..//*[@resource-id='{cls.PACKAGE_ID}/tv_member_num']")

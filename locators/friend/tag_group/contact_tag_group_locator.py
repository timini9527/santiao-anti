from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class ContactTagGroupLocator:
    """通讯录好友分组/标签页面定位器"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 1. 顶部导航栏
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                                 # 返回按钮
    TV_TITLE = CommonLocator.TOP_TV_TITLE                                   # 页面标题 ("标签" / "通讯录分组")
    TV_ACTION_SAVE = CommonLocator.TOP_BAR_EDIT_TO_BTN                      # 右上角保存/完成按钮

    # 首页
    ADD_SUBGROUP = (AppiumBy.ID, f"{PACKAGE_ID}/add_subGroup")              # 添加分组
    GROUP_ITEM_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/group_item_header")    # 分组列表Item
    GROUP_ITEM_TV_ID = f"{PACKAGE_ID}/group_item_tv"
    GROUP_ITEM_TV = (AppiumBy.ID, GROUP_ITEM_TV_ID)                         # 分组/标签名称
    GROUP_ITEM_EDIT_ID = f"{PACKAGE_ID}/group_item_edit"
    GROUP_ITEM_EDIT = (AppiumBy.ID, GROUP_ITEM_EDIT_ID)                     # 分组/标签编辑按钮

    # 根据分组名称动态定位其右侧的【编辑】图标
    @classmethod
    def get_group_item_edit_by_name(cls, group_name: str) -> tuple:
        """根据分组名称动态定位对应的编辑按钮 (following-sibling 兄弟节点定位)"""
        xpath = (
            f"//*[@resource-id='{cls.GROUP_ITEM_TV_ID}' and contains(@text, '{group_name}')]"
            f"/following-sibling::*[@resource-id='{cls.GROUP_ITEM_EDIT_ID}']"
        )
        return (AppiumBy.XPATH, xpath)
    
    # 根据分组名称动态定位分组
    @classmethod
    def get_group_item_by_name(cls, group_name: str) -> tuple:
        """根据分组名称动态定位分组 (following-sibling 兄弟节点定位)"""
        xpath = (
            f"//*[@resource-id='{cls.GROUP_ITEM_TV_ID}' and contains(@text, '{group_name}')]"
        )
        return (AppiumBy.XPATH, xpath)

        
    # 管理分组页面
    CREATE_SUBGROUP_EDIT = (AppiumBy.ID, f"{PACKAGE_ID}/create_subGroup_edit")
    CREATE_SUBGROUP_ADD_MEMBER_ID = f"{PACKAGE_ID}/create_subGroup_add_member"
    IV_DELETE = (AppiumBy.ID, f"{PACKAGE_ID}/iv_delete")                    # 删除/清空分组名字
    # 添加成员按钮
    CREATE_SUBGROUP_ADD_MEMBER = (AppiumBy.XPATH,                           
                                  f"//*[@resource-id='{CREATE_SUBGROUP_ADD_MEMBER_ID}']/android.widget.ImageView")
    CREATE_SUBGROUP_RV = (AppiumBy.ID, f"{PACKAGE_ID}/create_subGroup_rv")  # 好友列表
    FRIEND_HEADER = (AppiumBy.ID, f"{PACKAGE_ID}/friend_header")            # 好友头像
    FRIEND_NAME = f"{PACKAGE_ID}/friend_name"                               # 好友名称
    FRIEND_NAME_XPATH = (AppiumBy.XPATH, f"//*[@resource-id='{FRIEND_NAME}']/android.widget.TextView")
    FB_DELETE = (AppiumBy.ID, f"{PACKAGE_ID}/fb_delete")                    # 删除好友按钮

    # 5. 确认弹窗
    DIALOG_CONFIRM_BTN = CommonLocator.DIALOG_CONFIRM_BTN                   # 弹窗确认按钮
    DIALOG_CANCEL_BTN = CommonLocator.DIALOG_CANCEL_BTN                     # 弹窗取消按钮

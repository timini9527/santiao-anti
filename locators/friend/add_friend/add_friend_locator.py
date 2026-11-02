from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator

class AddFriendLocator:
    """添加朋友页面定位器 (基于最新 XML 布局树重构)"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 1. 顶部导航栏元素
    TOP_IV_BACK_BTN = CommonLocator.TOP_IV_BACK_BTN                             # 返回按钮
    TOP_TV_TITLE = CommonLocator.TOP_TV_TITLE                                   # 页面标题 "添加朋友"
    TOP_IV_ACTION_BTN = CommonLocator.TOP_IV_ACTION_BTN                         # 右上角动作按钮
    IV_TITLE_QRCODE = (AppiumBy.ID, f"{PACKAGE_ID}/iv_title_qrcode")            # 顶部二维码图标
    IV_TITLE_SCAN = (AppiumBy.ID, f"{PACKAGE_ID}/iv_title_scan")                # 顶部扫一扫图标

    # 2. 搜索框
    # SEARCH_ENTRY_ID = f"{PACKAGE_ID}/fb_search"
    # SEARCH_ENTRY = (AppiumBy.ID, SEARCH_ENTRY_ID)
    # SEARCH_ENTRY_XPATH = (AppiumBy.XPATH, f"//*[@resource-id='{SEARCH_ENTRY_ID}']//android.widget.TextView")
    # 2. 搜索框 - new
    SEARCH_ENTRY_ID = f"{PACKAGE_ID}/cl_search"
    SEARCH_ENTRY = (AppiumBy.ID, SEARCH_ENTRY_ID)
    SEARCH_ENTRY_XPATH = (AppiumBy.ID, f"{PACKAGE_ID}/tv_search_hint")

    ET_SEARCH = (AppiumBy.ID, f"{PACKAGE_ID}/et_search")                        # 搜索框输入
    TV_CANCEL = CommonLocator.TV_CANCEL_BTN                                     # 取消按钮
    RV_SEARCH_RESULTS = (AppiumBy.ID, f"{PACKAGE_ID}/rv_search_results")        # 搜索结果列表
    TV_SEARCH_KEY_MARK = (AppiumBy.ID, f"{PACKAGE_ID}/tv_search_key_mark")      # 确认搜索容器
    CL_ITEM = (AppiumBy.ID, f"{PACKAGE_ID}/cl_item")                            # 搜索结果item
    # 搜索结果item中的昵称 搜索结果中唯一
    RESULT_ITEM_TV_NAME = (AppiumBy.XPATH, f"//*[@resource-id='{PACKAGE_ID}/tv_name']")

    RESULT_ITEM_TV_MESSAGE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_message")


    # 3. 扫一扫容器
    SCAN_CL = (AppiumBy.ID, f"{PACKAGE_ID}/cl_scan")                    # 扫一扫容器
    IV_SCAN = (AppiumBy.ID, f"{PACKAGE_ID}/iv_scan")                    # 扫一扫图标
    TV_SCAN = (AppiumBy.ID, f"{PACKAGE_ID}/tv_scan")                    # 扫一扫文字
    TV_SCAN_FRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_scan_friend")      # 扫一扫加朋友

    # 4. 我的二维码容器
    QRCODE_CL = (AppiumBy.ID, f"{PACKAGE_ID}/cl_qrcode")                # 我的二维码容器
    IV_QRCODE_ICON = (AppiumBy.ID, f"{PACKAGE_ID}/iv_qrcode_icon")      # 我的二维码图标
    TV_QRCODE = (AppiumBy.ID, f"{PACKAGE_ID}/tv_qrcode")                # 我的二维码文字
    TV_QRCODE_FRIEND = (AppiumBy.ID, f"{PACKAGE_ID}/tv_qrcode_friend")  # 我的二维码加朋友

    # 5. 底部个人名片展示信息
    MY_QRCODE_LAYOUT = (AppiumBy.ID, f"{PACKAGE_ID}/cl_my_qrcode")      # 我的名片区域
    IV_QRCODE = (AppiumBy.ID, f"{PACKAGE_ID}/iv_qrcode")                # 我的二维码
    MY_NAME = (AppiumBy.ID, f"{PACKAGE_ID}/tv_name")                    # 个人昵称 (如 "1234567890")
    MY_ID = (AppiumBy.ID, f"{PACKAGE_ID}/tv_id")                        # 个人ID (如 "ID: imid_xxx")


    # 6. 申请页面
    # 输入备注
    INPUT_REMARK = (AppiumBy.ID, f"{PACKAGE_ID}/input_remark")

    




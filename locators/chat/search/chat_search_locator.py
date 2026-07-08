from appium.webdriver.common.appiumby import AppiumBy
from locators.system.common.common_locator import CommonLocator


class ChatSearchLocator(CommonLocator):
    """聊天记录搜索页面 Object"""
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 查找页面标志元素

    # 顶部搜索输入框
    SEARCH_INPUT = (AppiumBy.ID, f'{PACKAGE_ID}/search_edit_text')
    
    # 右侧取消按钮

    # 快速搜索分类选项
    OPTION_DATE = (AppiumBy.ID, f'{PACKAGE_ID}/search_date')                    # 按日期
    OPTION_IMAGE = (AppiumBy.ID, f'{PACKAGE_ID}/search_picture')                # 按图片
    OPTION_VIDEO = (AppiumBy.ID, f'{PACKAGE_ID}/search_video')                  # 按视频
    OPTION_FILE = (AppiumBy.ID, f'{PACKAGE_ID}/search_file')                    # 按文件
    OPTION_GROUP_MEMBER = (AppiumBy.ID, f'{PACKAGE_ID}/search_group_member')    # 按群成员

    # 搜索结果容器
    # 搜索结果-头像
    # 搜索结果-名称
    # 搜索结果-时间
    # 搜索结果-消息内容
    TV_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_content')


    # 按日期查找相关元素

    MONTH_TITLE_ID = f'{PACKAGE_ID}/month_title'        # 月份标题
    DAY_GRID_ID = f'{PACKAGE_ID}/day_grid'              # 日历网格  
    DAY_GRID = (AppiumBy.ID, DAY_GRID_ID) 

    # 动态获取日历面板中特定天的选项
    @classmethod
    def get_calendar_day_locator(cls, year_month: str, day: str) -> tuple:
        """根据日期数字动态生成定位器"""
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.MONTH_TITLE_ID}" and @text="{year_month}"]/following-sibling::*[@resource-id="{cls.DAY_GRID_ID}"]//*[@text="{day}"]')

    # 动态获取年月日期
    @classmethod
    def get_month_title_locator(cls, year_month: str) -> tuple:
        """根据年月动态生成定位器"""
        return (AppiumBy.XPATH, f'//*[@resource-id="{cls.MONTH_TITLE_ID}" and @text="{year_month}"]')
    

    # 按相册和视频容器
    PICTURE_RV = (AppiumBy.ID, f'{PACKAGE_ID}/picture_rv')
    IV_PIC = (AppiumBy.ID, f'{PACKAGE_ID}/iv_pic')      # 相册列表项
    
    
    # 按文件容器
    BY_FILE_RV = (AppiumBy.ID, f'{PACKAGE_ID}/byFile_rv')               # 文件列表项
    FILE_BY_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/file_by_name')          # 文件发送者昵称
    FILE_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/file_name')                # 文件名称

    # 按群成员容器

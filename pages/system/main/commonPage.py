from common.base_page import BasePage

from selenium.webdriver.common.by import By




class CommonPage(BasePage):

    # 顶部菜单
    # BACK = (By.ID, 'back_layout')    # 左上角返回
    BACK = (By.ID, 'back_imageView')  # 左上角返回
    SGD = (By.ID, 'title_right_iv')  # 右上角三个点
    DONE = (By.ID, 'title_right_tv')
    CLEAR = (By.ID, 'iv_clear')
    # 底部菜单
    CANCEL_TV = (By.ID, 'cancel_tv') # 取消


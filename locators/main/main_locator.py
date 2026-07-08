from appium.webdriver.common.appiumby import AppiumBy

class MainLocator:
    """主页面底部菜单等通用导航元素定位器"""
    
    PACKAGE_ID = 'com.santiaotalk.im:id'
    
    # 底部菜单：消息/主页
    MENU_MAIN = (AppiumBy.ID, f'{PACKAGE_ID}/rl_menu_main')
    
    # 底部菜单：好友/联系人
    MENU_CONTACT = (AppiumBy.ID, f'{PACKAGE_ID}/lottie_contact')
    
    # 底部菜单：通话
    MENU_CALL = (AppiumBy.ID, f'{PACKAGE_ID}/lottie_call')
    
    # 底部菜单：我的
    MENU_MINE = (AppiumBy.ID, f'{PACKAGE_ID}/rl_menu_mine')
    
    # 用于判断登录成功的一个通用标志 (比如消息列表容器)
    CONVERSATION_LIST = (AppiumBy.ID, f'{PACKAGE_ID}/rv_conversation')

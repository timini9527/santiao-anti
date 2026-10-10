from appium.webdriver.common.appiumby import AppiumBy
from locators.common.common_locator import CommonLocator


class MomentsLocator:
    PACKAGE_ID = CommonLocator.PACKAGE_ID

    # 顶部元素
    IV_BACK = CommonLocator.TOP_IV_BACK_BTN                     # 返回图标
    TV_MOMENTS = CommonLocator.TOP_TV_TITLE                     # 动态标题
    TV_MOMENTS_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{CommonLocator.TOP_TV_TITLE_ID}" and @text="朋友圈"]')
    IV_CAMERA = (AppiumBy.ID, f'{PACKAGE_ID}/iv_camera')        # 发布朋友圈按钮 (相机图标)

    IV_BG = (AppiumBy.ID, f'{PACKAGE_ID}/iv_bg')                # 背景图片
    TV_NOT_BG = (AppiumBy.ID, f'{PACKAGE_ID}/tv_not_bg')        # 轻触更换封面按钮
    IV_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_avatar')        # 头像图片


    # ===========================================
    # 朋友圈列表及内容
    # ===========================================
    RV_LIST = (AppiumBy.ID, f'{PACKAGE_ID}/rv_list')            # 朋友圈列表
    # 朋友圈列表最新一条内容 (发布成功后需要下拉刷新才能看到最新发布)
    RV_LIST_MOMENT_CONTENT = (AppiumBy.XPATH, f'//*[@resource-id="{PACKAGE_ID}/rv_list"]/android.view.ViewGroup')

    # 朋友圈昵称
    TV_NAME_ID = f'{PACKAGE_ID}/tv_name'
    TV_NAME = (AppiumBy.ID, TV_NAME_ID)            
    TV_NAME_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TV_NAME_ID}"]/android.widget.TextView') 
    
    TV_CONTENT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_content')              # 动态正文内容
    CL_PIC = (AppiumBy.ID, f'{PACKAGE_ID}/cl_pic')                      # 朋友圈多图区域
    RV_PIC = (AppiumBy.ID, f'{PACKAGE_ID}/rv_pic')                      # 朋友圈内容图片区域          
    IV_MEDIA = (AppiumBy.ID, f'{PACKAGE_ID}/iv_media')                  # 朋友圈多个图片
    IV_SINGLE_PIC = (AppiumBy.ID, f'{PACKAGE_ID}/iv_single_pic')        # 朋友圈单个视频/图片
    TV_TIME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_time')                    # 朋友圈时间
    TV_DELETE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_delete')                # 删除
    DIALOG_CONFIRM_BTN = CommonLocator.DIALOG_CONFIRM_BTN               # 确认按钮
    DIALOG_CANCEL_BTN = CommonLocator.DIALOG_CANCEL_BTN                 # 取消按钮
    BOTTOM_TEXT = (AppiumBy.XPATH, '//*[contains(@text, "没有更多") or contains(@text, "到底了") or contains(@text, "已加载全部")]')
    
    # 图片和视频区域
    RV_MEDIA_ID = f'{PACKAGE_ID}/rv_media'                              # 图片和视频列表
    RV_MEDIA = (AppiumBy.ID, RV_MEDIA_ID)                  
    # 最后一个元素添加按钮
    RV_PIC_LAST_VIDEO_GROUP = (AppiumBy.XPATH, f'//*[@resource-id="{RV_MEDIA_ID}"]/android.view.ViewGroup[last()]')

    IV_VIDEO = (AppiumBy.ID, f'{PACKAGE_ID}/iv_video')                  # 朋友圈视频
    IV_PLAY = (AppiumBy.ID, f'{PACKAGE_ID}/iv_play')                    # 朋友圈播放按钮



    # 弹窗确认按钮
    DIALOG_OK_BTN = (AppiumBy.ID, f'{PACKAGE_ID}/btnOk')               # 弹窗确认按钮

    TV_EXPEND_ID = f'{PACKAGE_ID}/tv_expand'
    TV_EXPAND = (AppiumBy.ID, TV_EXPEND_ID)                             # 全文展开按钮
    TV_EXPAND_TEXT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TV_EXPEND_ID}" and @text="全文"]')  # 全文展开按钮
    TV_SHRINK_TEXT_XPATH = (AppiumBy.XPATH, f'//*[@resource-id="{TV_EXPEND_ID}" and @text="收起"]')  # 收起

    TV_LIKE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_like')                    # 朋友圈点赞按钮
    TV_COMMENT_ID = f'{PACKAGE_ID}/tv_comment'
    TV_COMMENT = (AppiumBy.ID, TV_COMMENT_ID)                           # 朋友圈评论按钮
    
    # 朋友圈评论区元素
    FB_LIKE_USER = (AppiumBy.ID, f'{PACKAGE_ID}/fb_like_user')          # 点赞区域父容器
    CL_LIKE_USER = (AppiumBy.ID, f'{PACKAGE_ID}/cl_like_user')          # 点赞用户节点容器
    IV_LIKE_USER = (AppiumBy.ID, f'{PACKAGE_ID}/iv_like_user')          # 点赞图标
    TV_LIKE_USERNAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_like_user')      # 点赞用户名

    FB_COMMENT_USER = (AppiumBy.ID, f'{PACKAGE_ID}/fb_comment_user')    # 评论区域父容器
    CL_COMMENT_USER = (AppiumBy.ID, f'{PACKAGE_ID}/cl_comment_user')    # 评论节点容器
    IV_COMMENT_USER = (AppiumBy.ID, f'{PACKAGE_ID}/iv_comment_user')    # 评论图标
    RV_COMMENT_USER_ID = f'{PACKAGE_ID}/rv_comment_user'
    RV_COMMENT_USER = (AppiumBy.ID, RV_COMMENT_USER_ID)                 # 评论列表
    # 评论内容
    RV_COMMENT_DETAIL = (AppiumBy.XPATH, f'//*[@resource-id="{RV_COMMENT_USER_ID}"]//*[@resource-id="{TV_COMMENT_ID}"]')  

    # 发送评论元素
    ET_COMMENT = (AppiumBy.ID, f'{PACKAGE_ID}/et_comment')              # 评论输入框
    TV_SEND = (AppiumBy.ID, f'{PACKAGE_ID}/tv_send')                    # 评论发送按钮

    # 收到点赞或评论的提醒Tip
    FB_NEW_MESSAGE = (AppiumBy.ID, f'{PACKAGE_ID}/fb_new_message')                  # 收到点赞或评论的提醒Tip
    IV_NEW_MESSAGE_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_new_message_avatar')    # 提醒Tip的头像
    TV_NEW_MESSAGE_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/tv_new_message_text')        # 提醒Tip的文本
    
    

    
    # 发布页面元素
    # 弹窗选择
    CL_SHOOTING = (AppiumBy.ID, f'{PACKAGE_ID}/cl_shooting')            # 拍照选项
    TV_GALLERY = (AppiumBy.ID, f'{PACKAGE_ID}/tv_gallery')              # 从相册选择选项
    FB_CANCEL = (AppiumBy.ID, f'{PACKAGE_ID}/fb_cancel')                # 取消按钮
    FB_ACTION = CommonLocator.TOP_FB_ACTION_BTN                         # 发布按钮

    # 朋友圈发布
    ET_TEXT = (AppiumBy.ID, f'{PACKAGE_ID}/et_text')                    # 文字输入框

    # 可见范围
    CL_VISIBLE_USER = (AppiumBy.ID, f'{PACKAGE_ID}/cl_visible_user')                # 可见范围容器
    CL_PUBLIC = (AppiumBy.ID, f'{PACKAGE_ID}/cl_public')                            # 公开选项
    IV_PUBLIC_CHECK = (AppiumBy.ID, f'{PACKAGE_ID}/iv_public_check')                # 公开选项对勾
    TV_PUBLIC_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_public_title')                # 公开选项标题
    TV_PUBLIC_SUBTITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_public_subtitle')          # 公开选项副标题

    CL_PRIVATE = (AppiumBy.ID, f'{PACKAGE_ID}/cl_private')                          # 私密选项
    IV_PRIVATE_CHECK = (AppiumBy.ID, f'{PACKAGE_ID}/iv_private_check')              # 私密选项对勾
    TV_PRIVATE_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_private_title')              # 私密选项标题
    TV_PRIVATE_SUBTITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_private_subtitle')        # 私密选项副标题
    
    LL_PARTIAL_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/ll_partial_container')      # 部分可见容器
    IV_PARTIAL_CHECK = (AppiumBy.ID, f'{PACKAGE_ID}/iv_partial_check')              # 部分可见选项对勾
    TV_PARTIAL_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_partial_title')              # 部分可见选项标题
    CL_PARTIAL_SELECT_TAG = (AppiumBy.ID, f'{PACKAGE_ID}/cl_partial_select_tag')    # 部分可见选项标签
    TV_PARTIAL_TAG_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_partial_tag_title')      # 部分可见选项标签标题
    TV_PARTIAL_TAG_SUBTITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_partial_tag_subtitle')        # 部分可见选项标签副标题
    CL_PARTIAL_SELECT_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/cl_partial_select_friend')      # 部分可见选项好友
    TV_PARTIAL_FRIEND_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_partial_friend_title')        # 部分可见选项好友标题
    TV_PARTIAL_FRIEND_SUBTITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_partial_friend_subtitle')  # 部分可见选项好友副标题

    LL_EXCLUDE_CONTAINER = (AppiumBy.ID, f'{PACKAGE_ID}/ll_exclude_container')      # 排除可见容器
    IV_EXCLUDE_CHECK = (AppiumBy.ID, f'{PACKAGE_ID}/iv_exclude_check')              # 排除可见选项对勾
    TV_EXCLUDE_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_exclude_title')              # 排除可见选项标题
    CL_EXCLUDE_SELECT_TAG = (AppiumBy.ID, f'{PACKAGE_ID}/cl_exclude_select_tag')    # 排除可见选项标签
    TV_EXCLUDE_TAG_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_exclude_tag_title')      # 排除可见选项标签标题
    TV_EXCLUDE_TAG_SUBTITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_exclude_tag_subtitle')        # 排除可见选项标签副标题
    CL_EXCLUDE_SELECT_FRIEND = (AppiumBy.ID, f'{PACKAGE_ID}/cl_exclude_select_friend')      # 排除可见选项好友
    TV_EXCLUDE_FRIEND_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_exclude_friend_title')        # 排除可见选项好友标题
    TV_EXCLUDE_FRIEND_SUBTITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_exclude_friend_subtitle')  # 排除可见选项好友副标题


    # 标签选择页面
    ET_SEARCH = (AppiumBy.ID, f'{PACKAGE_ID}/et_search')                    # 搜索框
    RV_TAGS = (AppiumBy.ID, f'{PACKAGE_ID}/rv_tags')                        # 标签列表
    CB_SELECT = (AppiumBy.ID, f'{PACKAGE_ID}/cb_select')                    # 标签选择框
    TV_TAG_NAME = (AppiumBy.ID, f'{PACKAGE_ID}/tv_tag_name')                # 标签名称
    TV_TAG_FRIENDS = (AppiumBy.ID, f'{PACKAGE_ID}/tv_tag_friends')          # 标签好友数量
    IV_MORE = (AppiumBy.ID, f'{PACKAGE_ID}/iv_more')                        # 更多按钮

    # TV_TAG_ITEM = (AppiumBy.XPATH, f'//android.widget.TextView[contains(@text, "测试标签")]/..')
    
    TV_ADD = (AppiumBy.ID, f'{PACKAGE_ID}/tv_add')                          # 添加好友
    TV_REMOVE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_remove')                    # 删除好友    

    # 二次标签选择或朋友标签元素
    TV_VISIBLE_TITLE = (AppiumBy.ID, f'{PACKAGE_ID}/tv_visible_title')      # 标签可见标题
    TV_VISIBLE_FRIENDS = (AppiumBy.ID, f'{PACKAGE_ID}/tv_visible_friends')  # 标签可见好友

    # 删除底部展开页面
    CL_REMOVE = (AppiumBy.ID, f'{PACKAGE_ID}/cl_remove')                    # 删除选项
    IV_ARROW_UP = (AppiumBy.ID, f'{PACKAGE_ID}/iv_arrow_up')                # 删除按钮上的向上箭头
    IV_SELECT_AVATAR = (AppiumBy.ID, f'{PACKAGE_ID}/iv_select_avatar')      # 删除好友列表中的头像
    FB_REMOVE = (AppiumBy.ID, f'{PACKAGE_ID}/fb_remove')                    # 删除按钮
    CB_SELECT = (AppiumBy.ID, f'{PACKAGE_ID}/cb_select')                    # 删除好友列表中的选择框
    CB_ALL_SELECT = (AppiumBy.ID, f'{PACKAGE_ID}/cb_all_select')            # 全选
    

    @classmethod
    def get_tag_item_by_text(cls, tag_name: str) -> tuple[str, str]:
        """获取标签名称的通用定位器，支持动态传入标签名称"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[contains(@text, "{tag_name}")]/..')

    @classmethod
    def get_tag_friends_by_name(cls, tag_name: str) -> tuple[str, str]:
        """获取指定标签名称底下的好友名字文本定位器"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[contains(@text, "{tag_name}")]/../*[@resource-id="{cls.PACKAGE_ID}/tv_tag_friends"]')

    @classmethod
    def get_tag_name_text_by_name(cls, tag_name: str) -> tuple[str, str]:
        """获取指定标签名称所在的TextView文本定位器"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@resource-id="{cls.PACKAGE_ID}/tv_tag_name" and contains(@text, "{tag_name}")]')

    @classmethod
    def get_tag_more_btn_by_name(cls, tag_name: str) -> tuple[str, str]:
        """获取指定标签名称右侧的更多/编辑箭头按钮定位器"""
        return (AppiumBy.XPATH, f'//android.widget.TextView[contains(@text, "{tag_name}")]/../*[@resource-id="{cls.PACKAGE_ID}/iv_more"]')



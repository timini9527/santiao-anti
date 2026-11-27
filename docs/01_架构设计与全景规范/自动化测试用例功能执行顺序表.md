# 📋 三条 IM 自动化测试用例功能执行顺序表

> 本文档按类微信 IM 的核心业务闭环逻辑（**冒烟与登录认证 $\rightarrow$ 会话列表与单聊核心 $\rightarrow$ 聊天多媒体附件 $\rightarrow$ 通讯录好友关系链 $\rightarrow$ 群聊体系与群助手 $\rightarrow$ 动态社交与收藏 $\rightarrow$ 风控举报与多端演练**），对项目中全部 67 个测试用例文件进行了体系化编排。

---

## 一、冒烟测试基类套件 (`tests/smoke_test/`)
负责各核心模块 Page 对象的实例化调度、公共状态自愈与前后置夹具清理，保障主流程探活。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 1 | [test_smoke_login.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_login.py) | 登录认证模块冒烟基类与快速验证 | P0 |
| 2 | [test_smoke_contacts.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_contacts.py) | 通讯录与联系人列表冒烟基类 | P0 |
| 3 | [test_smoke_contact_detail.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_contact_detail.py) | 好友资料卡与备注设置冒烟基类 | P0 |
| 4 | [test_smoke_chat.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_chat.py) | 单聊核心收发、长按菜单与搜索冒烟基类 | P0 |
| 5 | [test_smoke_chat_options.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_chat_options.py) | 单聊加号面板多媒体与附件扩展冒烟基类 | P0 |
| 6 | [test_smoke_groups.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_groups.py) | 群聊创建、群设置与群管理冒烟基类 | P0 |
| 7 | [test_smoke_moments.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_moments.py) | 朋友圈/动态列表与发布冒烟基类 | P0 |
| 8 | [test_smoke_collection.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_collection.py) | 个人中心收藏夹管理冒烟基类 | P0 |
| 9 | [test_smoke_personal.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_personal.py) | 个人资料与隐私设置冒烟基类 | P0 |
| 10 | [test_smoke_report.py](file:///d:/projects/santiao-anti/tests/smoke_test/test_smoke_report.py) | 投诉举报与反垃圾流程冒烟基类 | P0 |

---

## 二、账号与登录认证 (`tests/login/`)
涵盖标准账号密码、短信验证码、运营商一键免密及用户协议合规校验。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 11 | [test_login.py](file:///d:/projects/santiao-anti/tests/login/test_login.py) | 账号密码标准登录、异常账号拦截与表单校验 | P0 |
| 12 | [test_verification_login.py](file:///d:/projects/santiao-anti/tests/login/test_verification_login.py) | 手机短信验证码登录、频控限制与倒计时 | P0 |
| 13 | [test_one_login.py](file:///d:/projects/santiao-anti/tests/login/test_one_login.py) | 运营商一键免密登录与无卡兜底流程 | P1 |
| 14 | [test_login_agreement.py](file:///d:/projects/santiao-anti/tests/login/test_login_agreement.py) | 用户服务协议、隐私政策勾选与拦截提示 | P1 |

---

## 三、主页会话与列表交互 (`tests/chat/list/`)
涵盖会话置顶、多项置顶折叠收起、侧滑菜单（静音/删除）及双端未读消息同步。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 15 | [test_chat_list.py](file:///d:/projects/santiao-anti/tests/chat/list/test_chat_list.py) | 会话列表展示、置顶多项折叠入口、侧滑静音与删除 | P0 |
| 16 | [test_chat_list_double.py](file:///d:/projects/santiao-anti/tests/chat/list/test_chat_list_double.py) | 会话列表双端协同：新消息红点提示、排序动态置顶与多端未读同步 | P0 |

---

## 四、单聊核心通信 (`tests/chat/`)
覆盖单聊文本消息收发、长文本、CSV 批量集、多端收发协同、长按菜单、聊天搜索与聊天设置。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 17 | [test_chat.py](file:///d:/projects/santiao-anti/tests/chat/core/test_chat.py) | 单聊/群聊普通文本消息发送、超长文本、CSV 数据集批量发送 | P0 |
| 18 | [test_chat_double.py](file:///d:/projects/santiao-anti/tests/chat/core/test_chat_double.py) | 单聊双端双向实时收发、消息送达与接收回执 | P0 |
| 19 | [test_chat_multi_device.py](file:///d:/projects/santiao-anti/tests/chat/core/test_chat_multi_device.py) | 多设备（Device 5~9）并发消息总线异步吞吐压测 | P1 |
| 20 | [test_chat_long_press.py](file:///d:/projects/santiao-anti/tests/chat/long_press/test_chat_long_press.py) | 消息气泡长按菜单：复制、转发、撤回、删除、多选批量操作 | P0 |
| 21 | [test_chat_search.py](file:///d:/projects/santiao-anti/tests/chat/search/test_chat_search.py) | 聊天记录全文检索、按日期日历查找、定位高亮原消息 | P1 |
| 22 | [test_chat_setting.py](file:///d:/projects/santiao-anti/tests/chat/setting/test_chat_setting.py) | 聊天设置：修改聊天备注、聊天密码锁开关、截屏通知开关 | P1 |

---

## 五、聊天扩展与多媒体附件 (`tests/chat_options/`)
包含输入框加号扩展面板中的图片、视频、语音、文件、表情包、地理位置及个人名片发送。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 23 | [test_images.py](file:///d:/projects/santiao-anti/tests/chat_options/images/test_images.py) | 图片发送：相机即拍、相册多选、原图/压缩图、预览与取消反悔 | P0 |
| 24 | [test_videos.py](file:///d:/projects/santiao-anti/tests/chat_options/videos/test_videos.py) | 视频发送：相册选择、超大视频体积校验、视频播放与发送反悔分支 | P0 |
| 25 | [test_voice.py](file:///d:/projects/santiao-anti/tests/chat_options/voice/test_voice.py) | 语音消息：按住录音、滑动手势取消、录音试听预览与发送 | P0 |
| 26 | [test_file.py](file:///d:/projects/santiao-anti/tests/chat_options/file/test_file.py) | 文件消息：手机本地文件浏览、分片上传与进度条校验 | P1 |
| 27 | [test_chat_basic_emoji.py](file:///d:/projects/santiao-anti/tests/chat_options/emojis/test_chat_basic_emoji.py) | 系统默认 Emoji 基础表情单发与连续表情混排 | P1 |
| 28 | [test_chat_emoji_collection.py](file:///d:/projects/santiao-anti/tests/chat_options/emojis/test_chat_emoji_collection.py) | 自定义表情包收藏、管理与移除 | P1 |
| 29 | [test_chat_emoji_store.py](file:///d:/projects/santiao-anti/tests/chat_options/emojis/test_chat_emoji_store.py) | 表情商城浏览、整套表情包下载与商用表情发送 | P2 |
| 30 | [test_position.py](file:///d:/projects/santiao-anti/tests/chat_options/location/test_position.py) | 位置发送：地图定位检索、POI 列表选择、无结果兜底与发送 | P1 |
| 31 | [test_contact_card.py](file:///d:/projects/santiao-anti/tests/chat_options/contact/test_contact_card.py) | 个人名片推荐：好友列表选取、名片气泡渲染与取消选择 | P1 |

---

## 六、联系人与好友关系链 (`tests/friend/`)
涵盖通讯录导航、添加好友、申请审批、好友资料卡、黑名单/删除及标签分组。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 32 | [test_friend_list.py](file:///d:/projects/santiao-anti/tests/friend/test_friend_list.py) | 通讯录字母索引导航、好友列表渲染与快速查找 | P0 |
| 33 | [test_add_friend.py](file:///d:/projects/santiao-anti/tests/friend/add_friend/test_add_friend.py) | 搜索手机号/三条号添加好友、验证信息输入与防重申请 | P0 |
| 34 | [test_new_friend.py](file:///d:/projects/santiao-anti/tests/friend/add_friend/test_new_friend.py) | “新的朋友”申请通知列表、同意/拒绝申请、一键清空列表 | P0 |
| 35 | [test_contact_detail_single.py](file:///d:/projects/santiao-anti/tests/friend/profile/test_contact_detail_single.py) | 好友资料页：修改备注、标签、手机号、设置为星标朋友 | P1 |
| 36 | [test_contact_detail_double.py](file:///d:/projects/santiao-anti/tests/friend/profile/test_contact_detail_double.py) | 好友资料双端验证：端 A 更改备注，端 B 观察名片与会话头联动 | P1 |
| 37 | [test_friend_relationship.py](file:///d:/projects/santiao-anti/tests/friend/relationship/test_friend_relationship.py) | 关系链状态机：加入黑名单、移出黑名单、双向/单向删除好友 | P0 |
| 38 | [test_contact_tag_group.py](file:///d:/projects/santiao-anti/tests/friend/tag_group/test_contact_tag_group.py) | 好友标签分组创建、批量成员打标与标签解绑 | P1 |

---

## 七、群聊体系与群管理 (`tests/groups/`)

### 1. 群聊创建与公开群发现
| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 39 | [test_group_create.py](file:///d:/projects/santiao-anti/tests/groups/create/test_group_create.py) | 单端勾选多联系人建群、默认群名生成与空选拦截 | P0 |
| 40 | [test_group_create_double.py](file:///d:/projects/santiao-anti/tests/groups/create/test_group_create_double.py) | 双端建群协同：发起建群、被邀请人自动进群并收到首条广播 | P0 |
| 41 | [test_public_group.py](file:///d:/projects/santiao-anti/tests/groups/public_group/test_public_group.py) | 公开群聊广场：公开群检索、浏览与申请加入公开群 | P1 |

### 2. 群资料与基础设置
| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 42 | [test_group_avatar.py](file:///d:/projects/santiao-anti/tests/groups/setting/general/test_group_avatar.py) | 群头像更换（拍照/相册）与群成员头像展示 | P1 |
| 43 | [test_group_setting.py](file:///d:/projects/santiao-anti/tests/groups/setting/general/test_group_setting.py) | 群信息设置：群名称修改、我在本群昵称、消息免打扰、群置顶 | P0 |
| 44 | [test_group_notice.py](file:///d:/projects/santiao-anti/tests/groups/setting/notice/test_group_notice.py) | 群公告编辑、发布推送、弹窗确认与历史公告查看 | P1 |
| 45 | [test_group_qrcode.py](file:///d:/projects/santiao-anti/tests/groups/setting/qrcode/test_group_qrcode.py) | 群二维码展示、保存到相册、分享与有效期时效规则 | P1 |

### 3. 群管理员权限与成员控制
| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 46 | [test_group_manager.py](file:///d:/projects/santiao-anti/tests/groups/setting/manager/test_group_manager.py) | 群管理子菜单：设置/取消管理员、仅群主可改群名等权限开关 | P0 |
| 47 | [test_group_manager_double.py](file:///d:/projects/santiao-anti/tests/groups/setting/manager/test_group_manager_double.py) | 双端群管理验证：群主转移群主身份、被提升管理员实时权限生效 | P0 |
| 48 | [test_admin_permissions_double.py](file:///d:/projects/santiao-anti/tests/groups/setting/manager/test_admin_permissions_double.py) | 管理员跨端踢人、邀请审核与群成员权限边界约束 | P0 |
| 49 | [test_speech_management_double.py](file:///d:/projects/santiao-anti/tests/groups/setting/manager/test_speech_management_double.py) | 全员禁言与单人禁言控制，成员端输入框置灰与违禁拦截提示 | P0 |

### 4. 群助手 / 智能机器人自动化
| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 50 | [test_group_bot_join_verify.py](file:///d:/projects/santiao-anti/tests/groups/bot/join_verify/test_group_bot_join_verify.py) | 群助手进群问答与验证机制配置 | P1 |
| 51 | [test_group_bot_welcome.py](file:///d:/projects/santiao-anti/tests/groups/bot/welcome/test_group_bot_welcome.py) | 新成员进群自定义欢迎语自动触发与占位符替换 | P1 |
| 52 | [test_group_bot_timed_msg.py](file:///d:/projects/santiao-anti/tests/groups/bot/timed_msg/test_group_bot_timed_msg.py) | 群定时消息发布配置、生命周期管理与定时触发 | P1 |
| 53 | [test_group_bot_keyword.py](file:///d:/projects/santiao-anti/tests/groups/bot/keyword/test_group_bot_keyword.py) | 敏感/违规关键词拦截、自动撤回或警告规则配置 | P1 |
| 54 | [test_group_bot_interaction.py](file:///d:/projects/santiao-anti/tests/groups/bot/keyword/test_group_bot_interaction.py) | 关键词多端交互：触发关键词自动回复特定图文消息 | P1 |
| 55 | [test_group_bot_auto_clean.py](file:///d:/projects/santiao-anti/tests/groups/bot/auto_clean/test_group_bot_auto_clean.py) | 僵尸成员/潜水成员基于周期的自动清理踢出 | P2 |
| 56 | [test_group_special_multi_device.py](file:///d:/projects/santiao-anti/tests/groups/special/test_group_special_multi_device.py) | 群聊多设备（5 设备并行）复杂入群、高频刷屏与抢发专项 | P1 |

---

## 八、朋友圈与社交动态 (`tests/moments/`)
涵盖图文动态发布、时间轴刷新、双端权限可见性与点赞/评论社交互动。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 57 | [test_moments.py](file:///d:/projects/santiao-anti/tests/moments/test_moments.py) | 朋友圈动态发布（纯文本、九宫格图片）、列表下拉刷新 | P0 |
| 58 | [test_moments_double.py](file:///d:/projects/santiao-anti/tests/moments/test_moments_double.py) | 动态双端可见性验证：权限控制（公开/私密）、好友时间轴即时流转 | P0 |
| 59 | [test_moments_interaction.py](file:///d:/projects/santiao-anti/tests/moments/test_moments_interaction.py) | 社交互动：点赞与取消点赞、评论与回复评论、空评论提交拦截 | P1 |

---

## 九、个人中心与收藏夹 (`tests/mine/collection/`)
支持聊天气泡、朋友圈图文的收藏沉淀、分类筛选与双端协同转发。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 60 | [test_collection.py](file:///d:/projects/santiao-anti/tests/mine/collection/single/test_collection.py) | 收藏夹列表展示、条目筛选（图片/链接/文件）、一键清空与单项删除 | P1 |
| 61 | [test_chat_collection.py](file:///d:/projects/santiao-anti/tests/mine/collection/single/test_chat_collection.py) | 聊天会话长按添加至收藏夹，以及在聊天中从收藏夹选定发送 | P1 |
| 62 | [test_moments_collection.py](file:///d:/projects/santiao-anti/tests/mine/collection/single/test_moments_collection.py) | 朋友圈图文动态收藏与条目溯源 | P1 |
| 63 | [test_collection_double.py](file:///d:/projects/santiao-anti/tests/mine/collection/double/test_collection_double.py) | 收藏夹双端协同：端 A 收藏并转发给端 B，端 B 接收并打开原内容 | P1 |

---

## 十、安全风控与投诉举报 (`tests/report/`)
涵盖聊天会话与群聊违规内容投诉举报流转及举报分类树自动化导出。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 64 | [test_chat_report.py](file:///d:/projects/santiao-anti/tests/report/test_chat_report.py) | 聊天违规举报（色情/诈骗/涉政）、证据截图上传与提交成功弹窗 | P1 |
| 65 | [test_extract_report_tree.py](file:///d:/projects/santiao-anti/tests/report/test_extract_report_tree.py) | 自动递归抓取 App 端全量投诉举报分类树并导出为标准配置 | P2 |

---

## 十一、跨端运行与自愈演练 Demo (`tests/`)
提供多端全流程状态机与鸿蒙 NEXT 纯血驱动自愈演练。

| 序号 | 测试用例文件 | 核心覆盖功能与场景 | 建议优先级 |
| :---: | :--- | :--- | :---: |
| 66 | [test_demo_android.py](file:///d:/projects/santiao-anti/tests/test_demo_android.py) | Android 端典型业务全流程状态机演练 Demo | P2 |
| 67 | [test_demo_harmony.py](file:///d:/projects/santiao-anti/tests/test_demo_harmony.py) | 鸿蒙 HarmonyOS NEXT 原生 UI 渲染、抽屉侧滑与驱动自愈演练 Demo | P1 |


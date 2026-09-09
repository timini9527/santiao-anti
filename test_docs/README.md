# 📖 IM 即时通讯软件 - 业务测试用例全景总览手册

> [!IMPORTANT]
> **面向对象**：产品经理、项目经理、测试工程师及业务主管。  
> **设计核心原则**：**100% 零代码黑话、纯人话业务解释、直观两级扁平目录**。无需懂代码，即可清晰了解每一项测试的**业务目的、操作流程、场景矩阵及验收通过标准**。

## 🧭 业务大类快速导航目录 (按核心业务分为 9 大板块)

### 📂 00_综合功能测试 `[共 1 个功能模块 / 1 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **功能_demo** | `test_demo.py` | [功能_demo](00_综合功能测试/【功能_demo】test_demo.md) | `1` |

### 📂 01_核心冒烟测试(smoke_test) `[共 10 个功能模块 / 67 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **冒烟测试-单聊-基础与设置** | `test_smoke_chat.py` | [冒烟测试-单聊-基础与设置](01_核心冒烟测试(smoke_test)/【冒烟测试-单聊-基础与设置】test_smoke_chat.md) | `13` |
| 2 | **冒烟测试-单聊-多媒体与附件** | `test_smoke_chat_options.py` | [冒烟测试-单聊-多媒体与附件](01_核心冒烟测试(smoke_test)/【冒烟测试-单聊-多媒体与附件】test_smoke_chat_options.md) | `8` |
| 3 | **冒烟测试-我的收藏-管理** | `test_smoke_collection.py` | [冒烟测试-我的收藏-管理](01_核心冒烟测试(smoke_test)/【冒烟测试-我的收藏-管理】test_smoke_collection.md) | `6` |
| 4 | **冒烟测试-好友资料与备注设置** | `test_smoke_contact_detail.py` | [冒烟测试-好友资料与备注设置](01_核心冒烟测试(smoke_test)/【冒烟测试-好友资料与备注设置】test_smoke_contact_detail.md) | `6` |
| 5 | **冒烟测试-联系人与好友** | `test_smoke_contacts.py` | [冒烟测试-联系人与好友](01_核心冒烟测试(smoke_test)/【冒烟测试-联系人与好友】test_smoke_contacts.md) | `2` |
| 6 | **冒烟测试-群聊模块-创建与公告** | `test_smoke_groups.py` | [冒烟测试-群聊模块-创建与公告](01_核心冒烟测试(smoke_test)/【冒烟测试-群聊模块-创建与公告】test_smoke_groups.md) | `14` |
| 7 | **冒烟测试-登录注册-协议校验** | `test_smoke_login.py` | [冒烟测试-登录注册-协议校验](01_核心冒烟测试(smoke_test)/【冒烟测试-登录注册-协议校验】test_smoke_login.md) | `5` |
| 8 | **冒烟测试-朋友圈与动态** | `test_smoke_moments.py` | [冒烟测试-朋友圈与动态](01_核心冒烟测试(smoke_test)/【冒烟测试-朋友圈与动态】test_smoke_moments.md) | `8` |
| 9 | **冒烟测试-个人资料与设置** | `test_smoke_personal.py` | [冒烟测试-个人资料与设置](01_核心冒烟测试(smoke_test)/【冒烟测试-个人资料与设置】test_smoke_personal.md) | `3` |
| 10 | **冒烟测试-举报模块-聊天举报** | `test_smoke_report.py` | [冒烟测试-举报模块-聊天举报](01_核心冒烟测试(smoke_test)/【冒烟测试-举报模块-聊天举报】test_smoke_report.md) | `2` |

### 📂 02_单聊与会话消息(chat) `[共 5 个功能模块 / 41 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **聊天模块-单聊基础：已完成** | `test_chat.py` | [聊天模块-单聊基础：已完成](02_单聊与会话消息(chat)/【聊天模块-单聊基础：已完成】test_chat.md) | `7` |
| 2 | **聊天模块-会话列表** | `test_chat_list.py` | [聊天模块-会话列表](02_单聊与会话消息(chat)/【聊天模块-会话列表】test_chat_list.md) | `14` |
| 3 | **聊天模块-长按菜单** | `test_chat_long_press.py` | [聊天模块-长按菜单](02_单聊与会话消息(chat)/【聊天模块-长按菜单】test_chat_long_press.md) | `8` |
| 4 | **聊天设置** | `test_chat_search.py` | [聊天设置](02_单聊与会话消息(chat)/【聊天设置】test_chat_search.md) | `7` |
| 5 | **聊天模块-单聊设置** | `test_chat_setting.py` | [聊天模块-单聊设置](02_单聊与会话消息(chat)/【聊天模块-单聊设置】test_chat_setting.md) | `5` |

### 📂 03_聊天多媒体附件(chat_options) `[共 9 个功能模块 / 50 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **聊天面板-名片** | `test_contact_card.py` | [聊天面板-名片](03_聊天多媒体附件(chat_options)/【聊天面板-名片】test_contact_card.md) | `5` |
| 2 | **聊天面板-表情** | `test_chat_basic_emoji.py` | [聊天面板-表情](03_聊天多媒体附件(chat_options)/【聊天面板-表情】test_chat_basic_emoji.md) | `3` |
| 3 | **聊天面板-表情包** | `test_chat_emoji_collection.py` | [聊天面板-表情包](03_聊天多媒体附件(chat_options)/【聊天面板-表情包】test_chat_emoji_collection.md) | `2` |
| 4 | **聊天面板-表情包** | `test_chat_emoji_store.py` | [聊天面板-表情包](03_聊天多媒体附件(chat_options)/【聊天面板-表情包】test_chat_emoji_store.md) | `3` |
| 5 | **聊天面板-文件** | `test_file.py` | [聊天面板-文件](03_聊天多媒体附件(chat_options)/【聊天面板-文件】test_file.md) | `9` |
| 6 | **聊天面板-图片** | `test_images.py` | [聊天面板-图片](03_聊天多媒体附件(chat_options)/【聊天面板-图片】test_images.md) | `6` |
| 7 | **聊天面板-位置** | `test_position.py` | [聊天面板-位置](03_聊天多媒体附件(chat_options)/【聊天面板-位置】test_position.md) | `10` |
| 8 | **聊天面板-视频** | `test_videos.py` | [聊天面板-视频](03_聊天多媒体附件(chat_options)/【聊天面板-视频】test_videos.md) | `6` |
| 9 | **聊天面板-语音** | `test_voice.py` | [聊天面板-语音](03_聊天多媒体附件(chat_options)/【聊天面板-语音】test_voice.md) | `6` |

### 📂 04_群聊体系与群助手(groups) `[共 16 个功能模块 / 65 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **群助手-自动清理成员** | `test_group_bot_auto_clean.py` | [群助手-自动清理成员](04_群聊体系与群助手(groups)/【群助手-自动清理成员】test_group_bot_auto_clean.md) | `2` |
| 2 | **群助手-入群验证** | `test_group_bot_join_verify.py` | [群助手-入群验证](04_群聊体系与群助手(groups)/【群助手-入群验证】test_group_bot_join_verify.md) | `1` |
| 3 | **群助手-禁言发送关键词-双端交互与拦截** | `test_group_bot_interaction.py` | [群助手-禁言发送关键词-双端交互与拦截](04_群聊体系与群助手(groups)/【群助手-禁言发送关键词-双端交互与拦截】test_group_bot_interaction.md) | `4` |
| 4 | **群助手-禁止发送关键词** | `test_group_bot_keyword.py` | [群助手-禁止发送关键词](04_群聊体系与群助手(groups)/【群助手-禁止发送关键词】test_group_bot_keyword.md) | `6` |
| 5 | **群助手-发言管理-两端验证** | `test_group_bot_speech_manage.py` | [群助手-发言管理-两端验证](04_群聊体系与群助手(groups)/【群助手-发言管理-两端验证】test_group_bot_speech_manage.md) | `2` |
| 6 | **群助手-定时消息** | `test_group_bot_timed_msg.py` | [群助手-定时消息](04_群聊体系与群助手(groups)/【群助手-定时消息】test_group_bot_timed_msg.md) | `1` |
| 7 | **群助手-进群欢迎语** | `test_group_bot_welcome.py` | [群助手-进群欢迎语](04_群聊体系与群助手(groups)/【群助手-进群欢迎语】test_group_bot_welcome.md) | `1` |
| 8 | **群聊模块-发起群聊** | `test_group_create.py` | [群聊模块-发起群聊](04_群聊体系与群助手(groups)/【群聊模块-发起群聊】test_group_create.md) | `8` |
| 9 | **群聊模块-发起群聊** | `test_group_create_double.py` | [群聊模块-发起群聊](04_群聊体系与群助手(groups)/【群聊模块-发起群聊】test_group_create_double.md) | `2` |
| 10 | **群聊模块-通用设置** | `test_group_avatar.py` | [群聊模块-通用设置](04_群聊体系与群助手(groups)/【群聊模块-通用设置】test_group_avatar.md) | `3` |
| 11 | **群聊模块-群管理** | `test_group_setting.py` | [群聊模块-群管理](04_群聊体系与群助手(groups)/【群聊模块-群管理】test_group_setting.md) | `11` |
| 12 | **群聊模块-群管理员-分配管理员单独权限校验** | `test_admin_permissions_double.py` | [群聊模块-群管理员-分配管理员单独权限校验](04_群聊体系与群助手(groups)/【群聊模块-群管理员-分配管理员单独权限校验】test_admin_permissions_double.md) | `1` |
| 13 | **群聊模块-群管理** | `test_group_manager.py` | [群聊模块-群管理](04_群聊体系与群助手(groups)/【群聊模块-群管理】test_group_manager.md) | `8` |
| 14 | **群聊模块-群管理双端验证** | `test_group_manager_double.py` | [群聊模块-群管理双端验证](04_群聊体系与群助手(groups)/【群聊模块-群管理双端验证】test_group_manager_double.md) | `10` |
| 15 | **群聊模块-群公告** | `test_group_notice.py` | [群聊模块-群公告](04_群聊体系与群助手(groups)/【群聊模块-群公告】test_group_notice.md) | `2` |
| 16 | **群聊模块-群二维码** | `test_group_qrcode.py` | [群聊模块-群二维码](04_群聊体系与群助手(groups)/【群聊模块-群二维码】test_group_qrcode.md) | `3` |

### 📂 05_通讯录与好友管理(friend) `[共 6 个功能模块 / 33 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **通讯录与好友管理** | `test_add_friend.py` | [通讯录与好友管理](05_通讯录与好友管理(friend)/【通讯录与好友管理】test_add_friend.md) | `8` |
| 2 | **通讯录与好友管理** | `test_new_friend.py` | [通讯录与好友管理](05_通讯录与好友管理(friend)/【通讯录与好友管理】test_new_friend.md) | `4` |
| 3 | **好友资料模块** | `test_contact_detail_single.py` | [好友资料模块](05_通讯录与好友管理(friend)/【好友资料模块】test_contact_detail_single.md) | `10` |
| 4 | **好友关系管理** | `test_friend_relationship.py` | [好友关系管理](05_通讯录与好友管理(friend)/【好友关系管理】test_friend_relationship.md) | `5` |
| 5 | **好友分组与标签管理** | `test_contact_tag_group.py` | [好友分组与标签管理](05_通讯录与好友管理(friend)/【好友分组与标签管理】test_contact_tag_group.md) | `4` |
| 6 | **通讯录与好友管理** | `test_friend_list.py` | [通讯录与好友管理](05_通讯录与好友管理(friend)/【通讯录与好友管理】test_friend_list.md) | `2` |

### 📂 06_朋友圈社交动态(moments) `[共 3 个功能模块 / 24 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **朋友圈模块-发布与互动** | `test_moments.py` | [朋友圈模块-发布与互动](06_朋友圈社交动态(moments)/【朋友圈模块-发布与互动】test_moments.md) | `9` |
| 2 | **朋友圈模块-多端与社交互动** | `test_moments_double.py` | [朋友圈模块-多端与社交互动](06_朋友圈社交动态(moments)/【朋友圈模块-多端与社交互动】test_moments_double.md) | `9` |
| 3 | **朋友圈模块-互动** | `test_moments_interaction.py` | [朋友圈模块-互动](06_朋友圈社交动态(moments)/【朋友圈模块-互动】test_moments_interaction.md) | `6` |

### 📂 07_我的收藏管理(mine_collection) `[共 4 个功能模块 / 13 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **我的收藏-收藏夹双端验证** | `test_collection_double.py` | [我的收藏-收藏夹双端验证](07_我的收藏管理(mine_collection)/【我的收藏-收藏夹双端验证】test_collection_double.md) | `2` |
| 2 | **我的收藏-聊天页面收藏** | `test_chat_collection.py` | [我的收藏-聊天页面收藏](07_我的收藏管理(mine_collection)/【我的收藏-聊天页面收藏】test_chat_collection.md) | `4` |
| 3 | **我的收藏-收藏夹** | `test_collection.py` | [我的收藏-收藏夹](07_我的收藏管理(mine_collection)/【我的收藏-收藏夹】test_collection.md) | `5` |
| 4 | **我的收藏-朋友圈收藏** | `test_moments_collection.py` | [我的收藏-朋友圈收藏](07_我的收藏管理(mine_collection)/【我的收藏-朋友圈收藏】test_moments_collection.md) | `2` |

### 📂 08_登录注册与鉴权(login) `[共 4 个功能模块 / 7 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **登录注册模块-账号密码登录** | `test_login.py` | [登录注册模块-账号密码登录](08_登录注册与鉴权(login)/【登录注册模块-账号密码登录】test_login.md) | `3` |
| 2 | **登录注册模块-协议校验** | `test_login_agreement.py` | [登录注册模块-协议校验](08_登录注册与鉴权(login)/【登录注册模块-协议校验】test_login_agreement.md) | `2` |
| 3 | **登录注册模块-一键登录** | `test_one_login.py` | [登录注册模块-一键登录](08_登录注册与鉴权(login)/【登录注册模块-一键登录】test_one_login.md) | `1` |
| 4 | **登录注册模块-验证码登录** | `test_verification_login.py` | [登录注册模块-验证码登录](08_登录注册与鉴权(login)/【登录注册模块-验证码登录】test_verification_login.md) | `1` |

### 📂 09_个人中心与违规举报(personal_report) `[共 4 个功能模块 / 47 个测试用例]`

| 序号 | 业务功能模块 (Feature) | 原始代码脚本 | 业务用例文档 (点击直达) | 核心用例数 |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **个人信息模块-头像** | `avat_test.py` | [个人信息模块-头像](09_个人中心与违规举报(personal_report)/【个人信息模块-头像】avat_test.md) | `33` |
| 2 | **个人信息模块-基本信息** | `other_test.py` | [个人信息模块-基本信息](09_个人中心与违规举报(personal_report)/【个人信息模块-基本信息】other_test.md) | `11` |
| 3 | **聊天设置** | `test_chat_report.py` | [聊天设置](09_个人中心与违规举报(personal_report)/【聊天设置】test_chat_report.md) | `2` |
| 4 | **投诉模块提取** | `test_extract_report_tree.py` | [投诉模块提取](09_个人中心与违规举报(personal_report)/【投诉模块提取】test_extract_report_tree.md) | `1` |

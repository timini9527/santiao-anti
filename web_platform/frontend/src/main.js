import { createApp } from 'vue'
import App from './App.vue'

// 引入 Element Plus 框架及样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// 引入 Element Plus 的官方暗黑主题样式变量
import 'element-plus/theme-chalk/dark/css-vars.css'
// 引入所有常用图标组件
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import './style.css'

const app = createApp(App)

// 全局注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus)
app.mount('#app')

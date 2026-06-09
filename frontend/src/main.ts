/**
 * Vue 应用入口
 *
 * 初始化 Vue 3 应用，注册 Pinia 状态管理、Vue Router 路由、
 * Element Plus UI 组件库及图标组件。
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/vitepress.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// 创建 Vue 应用实例
const app = createApp(App)

// 注册全局插件
app.use(createPinia())     // Pinia 状态管理
app.use(router)            // 路由
app.use(ElementPlus)       // Element Plus UI 组件库

// 全局注册 Element Plus 图标组件，模板中可直接使用图标名
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 挂载到 DOM
app.mount('#app')

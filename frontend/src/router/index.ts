/**
 * Vue Router 路由配置
 *
 * 定义应用的三个页面路由，使用懒加载减少首屏加载体积。
 */
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),  // 使用 HTML5 History 模式（无 # 号）
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),  // 首页 - 调研任务列表
    },
    {
      path: '/research/:id',
      name: 'research',
      component: () => import('../views/ResearchView.vue'),  // 调研进度页 - 实时展示 Agent 执行过程
    },
    {
      path: '/report/:id',
      name: 'report',
      component: () => import('../views/ReportView.vue'),  // 报告页 - 展示最终调研报告
    },
  ],
})

export default router

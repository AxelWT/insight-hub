<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'

// 路由实例，用于编程式导航
const router = useRouter()
// 任务状态管理实例，提供任务列表数据和加载状态
const taskStore = useTaskStore()

// 组件挂载时获取任务列表，确保首页展示最新数据
onMounted(() => {
  taskStore.fetchTasks()
})

// 调研深度枚举到中文标签的映射，用于前端展示
const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

// 任务状态到对应标签样式的映射，不同状态用不同颜色区分
const statusTagClass: Record<string, string> = {
  pending: 'vp-tag-gray',
  planning: 'vp-tag-yellow',
  searching: 'vp-tag-brand',
  crawling: 'vp-tag-brand',
  evaluating: 'vp-tag-yellow',
  writing: 'vp-tag-brand',
  completed: 'vp-tag-green',
  failed: 'vp-tag-red',
}

// 任务状态到中文标签的映射，用于前端展示
const statusLabels: Record<string, string> = {
  pending: '等待中',
  planning: '规划中',
  searching: '搜索中',
  crawling: '爬取中',
  evaluating: '评估中',
  writing: '撰写中',
  completed: '已完成',
  failed: '失败',
}

// 点击任务卡片时的导航逻辑：已完成跳转报告页，否则跳转调研详情页
function goToTask(task: { id: number; status: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}

// 将 ISO 日期字符串格式化为中文简短格式（如 "6月1日 14:30"）
function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div>
    <!-- 顶部英雄区域：展示平台标题和功能简介 -->
    <div class="hero-section">
      <h1>AI 调研平台</h1>
      <p class="hero-desc">
        输入调研主题或指定网站，AI Agent 将自动搜索、分析、整理，生成结构化调研报告。
      </p>
    </div>

    <!-- 最近调研任务列表区域 -->
    <div class="section">
      <h2>最近调研</h2>

      <!-- 加载状态提示 -->
      <div v-if="taskStore.loading" style="padding: 40px; text-align: center; color: var(--vp-c-text-3)">
        加载中...
      </div>

      <!-- 空状态提示：引导用户创建新调研 -->
      <div v-else-if="taskStore.tasks.length === 0" class="empty-state">
        <div class="empty-icon">📋</div>
        <p>暂无调研记录</p>
        <p class="text-muted" style="font-size: 13px">在左侧点击「主题调研」或「网站调研」开始</p>
      </div>

      <!-- 任务卡片网格，最多展示最近 12 条记录 -->
      <div v-else class="task-grid">
        <div
          v-for="task in taskStore.tasks.slice(0, 12)"
          :key="task.id"
          class="vp-card clickable task-card"
          @click="goToTask(task)"
        >
          <!-- 卡片头部：标题 + 状态标签 -->
          <div class="task-card-header">
            <h3 class="task-card-title">{{ task.topic }}</h3>
            <span :class="['vp-tag', statusTagClass[task.status] || 'vp-tag-gray']">
              {{ statusLabels[task.status] || task.status }}
            </span>
          </div>

          <!-- 任务描述，超过 80 字符截断显示 -->
          <div v-if="task.description" class="task-card-desc">
            {{ task.description.slice(0, 80) }}{{ task.description.length > 80 ? '...' : '' }}
          </div>

          <!-- 卡片底部：类型标签 + 深度/层数 + 创建时间 -->
          <div class="task-card-footer">
            <div class="task-card-tags">
              <span :class="['type-badge', task.task_type === 'website' ? 'type-website' : 'type-search']">
                {{ task.task_type === 'website' ? '🌐 网站调研' : '🔍 主题调研' }}
              </span>
              <span v-if="task.task_type === 'search'" class="text-muted">{{ depthLabels[task.depth] || task.depth }}调研</span>
              <span v-if="task.task_type === 'website'" class="text-muted">{{ task.crawl_depth }}层深度</span>
            </div>
            <span class="text-muted">{{ formatDate(task.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 顶部英雄区域的外边距，与下方内容拉开间距 */
.hero-section {
  margin-bottom: 40px;
}

/* 标题使用品牌色渐变文字效果，增强视觉冲击力 */
.hero-section h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px;
  background: linear-gradient(135deg, var(--vp-c-brand) 0%, var(--vp-c-brand-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* 功能简介文字样式，使用次要文字颜色降低视觉层级 */
.hero-desc {
  color: var(--vp-c-text-2);
  font-size: 16px;
  margin: 0;
  line-height: 1.7;
}

/* 分区标题样式 */
.section h2 {
  font-size: 20px;
  margin: 0 0 20px;
}

/* 空状态居中布局，留足呼吸空间 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

/* 空状态图标尺寸 */
.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

/* 空状态提示文字 */
.empty-state p {
  margin: 4px 0;
  color: var(--vp-c-text-2);
}

/* 任务卡片网格：自适应列数，最小宽度 300px，保证卡片不会过窄 */
.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

/* 任务卡片内边距 */
.task-card {
  padding: 20px;
}

/* 卡片头部：标题与状态标签水平排列，两端对齐 */
.task-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

/* 卡片标题：最多显示两行，超出部分省略，防止长标题撑开布局 */
.task-card-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  line-height: 1.5;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 卡片描述文字，使用最弱文字颜色降低视觉层级 */
.task-card-desc {
  font-size: 13px;
  color: var(--vp-c-text-3);
  line-height: 1.6;
  margin-bottom: 12px;
}

/* 卡片底部：标签和时间左右分布 */
.task-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

/* 底部标签区域水平排列 */
.task-card-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 任务类型徽章基础样式 */
.type-badge {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  line-height: 18px;
}

/* 主题调研类型：蓝色调 */
.type-search {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

/* 网站调研类型：绿色调，与主题调研做视觉区分 */
.type-website {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}
</style>

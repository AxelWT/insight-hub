<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'

const router = useRouter()
const taskStore = useTaskStore()

onMounted(() => {
  taskStore.fetchTasks()
})

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

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

function goToTask(task: { id: number; status: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}

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
    <div class="hero-section">
      <div class="hero-badge">AI Research</div>
      <h1>AI 调研平台</h1>
      <p class="hero-desc">
        输入调研主题或指定网站，AI Agent 将自动搜索、分析、整理，生成结构化调研报告。
      </p>
    </div>

    <div class="section">
      <h2>最近调研</h2>

      <div v-if="taskStore.loading" style="padding: 40px; text-align: center; color: var(--vp-c-text-3)">
        加载中...
      </div>

      <div v-else-if="taskStore.tasks.length === 0" class="empty-state">
        <p>暂无调研记录</p>
        <p class="text-muted" style="font-size: 13px">在左侧点击「主题调研」或「网站调研」开始</p>
      </div>

      <div v-else class="task-grid">
        <div
          v-for="task in taskStore.tasks.slice(0, 12)"
          :key="task.id"
          class="vp-card clickable task-card"
          @click="goToTask(task)"
        >
          <div class="task-card-header">
            <h3 class="task-card-title">{{ task.topic }}</h3>
            <span :class="['vp-tag', statusTagClass[task.status] || 'vp-tag-gray']">
              {{ statusLabels[task.status] || task.status }}
            </span>
          </div>

          <div v-if="task.description" class="task-card-desc">
            {{ task.description.slice(0, 80) }}{{ task.description.length > 80 ? '...' : '' }}
          </div>

          <div class="task-card-footer">
            <div class="task-card-tags">
              <span :class="['type-badge', task.task_type === 'website' ? 'type-website' : 'type-search']">
                {{ task.task_type === 'website' ? '网站调研' : '主题调研' }}
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
.hero-section {
  margin-bottom: 40px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 100px;
  font-family: var(--vp-font-family-mono);
  font-size: 11px;
  color: var(--vp-c-brand);
  margin-bottom: 16px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.hero-badge::before {
  content: '';
  width: 6px;
  height: 6px;
  background: var(--vp-c-brand);
  border-radius: 50%;
  animation: hero-pulse 2s ease-in-out infinite;
}

@keyframes hero-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.hero-section h1 {
  font-size: 36px;
  font-weight: 700;
  margin: 0 0 10px;
  background: var(--gradient-1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  color: var(--vp-c-text-2);
  font-size: 16px;
  margin: 0;
  line-height: 1.7;
  max-width: 600px;
  white-space: nowrap;
}

.section h2 {
  font-size: 20px;
  margin: 0 0 20px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-state p {
  margin: 4px 0;
  color: var(--vp-c-text-2);
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.task-card {
  padding: 20px;
}

.task-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

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

.task-card-desc {
  font-size: 13px;
  color: var(--vp-c-text-3);
  line-height: 1.6;
  margin-bottom: 12px;
}

.task-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.task-card-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-badge {
  display: inline-block;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
  line-height: 18px;
}

.type-search {
  background: var(--vp-c-brand-bg);
  color: var(--vp-c-brand);
}

.type-website {
  background: var(--vp-c-brand-bg);
  color: var(--vp-c-brand-light);
}
</style>

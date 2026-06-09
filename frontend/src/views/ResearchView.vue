<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTask, type Task } from '../api/task'
import { useWebSocketStore } from '../stores/websocket'
import AgentTimeline, { type LogEntry } from '../components/AgentTimeline.vue'

const route = useRoute()
const router = useRouter()
const wsStore = useWebSocketStore()

// 当前任务数据，初始为 null 表示尚未加载
const task = ref<Task | null>(null)
// 页面加载状态，用于控制加载中提示的显示
const loading = ref(true)

// 将 WebSocket store 中的 agentLogs 转换为 AgentTimeline 组件所需的 LogEntry 类型
const typedAgentLogs = computed(() => wsStore.agentLogs as unknown as LogEntry[])

// 调研深度对应的中文标签映射
const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

// 任务类型对应的中文标签映射，包含图标前缀
const typeLabels: Record<string, string> = {
  search: '🔍 主题调研',
  website: '🌐 网站调研',
}

// 根据路由参数中的任务 ID 拉取任务详情，失败时跳转首页
async function fetchTask() {
  const id = Number(route.params.id)
  try {
    task.value = await getTask(id)
  } catch {
    router.push('/')
  } finally {
    loading.value = false
  }
}

// 建立 WebSocket 连接，订阅指定任务的实时消息推送
function connectWs() {
  const id = Number(route.params.id)
  wsStore.connect(id)
}

// 初始化任务页面：重置加载状态、拉取数据、建立 WebSocket 连接
function initTask() {
  loading.value = true
  fetchTask()
  connectWs()
}

// 组件挂载时初始化任务数据
onMounted(() => {
  initTask()
})

// 组件卸载时断开 WebSocket 连接并清除轮询定时器，避免内存泄漏
onUnmounted(() => {
  wsStore.disconnect()
  if (pollTimer) clearInterval(pollTimer)
})

// 监听路由参数变化，重新加载数据
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    wsStore.disconnect()
    initTask()
  }
})

// 监听 WebSocket 推送消息，实时更新任务状态和进度
watch(() => wsStore.lastMessage, (msg) => {
  if (!msg) return
  // 状态更新：同步任务状态，完成时自动跳转报告页
  if (msg.type === 'status_update' && task.value) {
    task.value.status = msg.data.status as string
    task.value.current_step = msg.data.current_step as string || task.value.current_step
    if (msg.data.status === 'completed') {
      router.push(`/report/${task.value.id}`)
    }
  }
  // 进度更新：同步任务进度百分比
  if (msg.type === 'progress_update' && task.value) {
    task.value.progress = msg.data.progress as number
  }
})

// 轮询定时器，作为 WebSocket 的兜底机制，确保数据最终一致
let pollTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  pollTimer = setInterval(fetchTask, 5000)
})
</script>

<template>
  <!-- 加载中状态 -->
  <div v-if="loading" style="padding: 60px; text-align: center; color: var(--vp-c-text-3)">
    加载中...
  </div>

  <div v-else-if="task">
    <!-- 头部区域：返回按钮、任务标题、元信息标签 -->
    <div class="research-header">
      <button class="vp-btn vp-btn-text" @click="router.push('/')">&larr; 返回</button>
      <h1>{{ task.topic }}</h1>
      <div class="research-meta">
        <span
          :class="['type-badge', task.task_type === 'website' ? 'type-website' : 'type-search']"
        >
          {{ typeLabels[task.task_type] || '调研' }}
        </span>
        <span v-if="task.task_type === 'search'" class="vp-tag vp-tag-brand">{{ depthLabels[task.depth] || task.depth }}调研</span>
        <!-- 网站调研类型专属标签：爬取深度和最大页数 -->
        <span v-if="task.task_type === 'website'" class="vp-tag vp-tag-green">
          爬取深度: {{ task.crawl_depth }} 层
        </span>
        <span v-if="task.task_type === 'website'" class="vp-tag vp-tag-green">
          最大 {{ task.max_pages }} 页
        </span>
        <span class="text-muted" style="font-size: 13px">模型: {{ task.model }}</span>
        <span class="text-muted" style="font-size: 13px">{{ new Date(task.created_at).toLocaleTimeString('zh-CN') }}</span>
      </div>
    </div>

    <!-- 进度条区域：显示调研百分比进度和当前步骤描述 -->
    <div class="vp-card" style="margin-bottom: 24px">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px">
        <span style="font-size: 14px; font-weight: 600; color: var(--vp-c-text-1)">调研进度</span>
        <span style="font-size: 14px; font-weight: 700; color: var(--vp-c-brand)">{{ task.progress }}%</span>
      </div>
      <div class="vp-progress">
        <div class="vp-progress-bar" :style="{ width: task.progress + '%' }" />
      </div>
      <div v-if="task.current_step" style="margin-top: 8px; font-size: 13px; color: var(--vp-c-text-3)">
        {{ task.current_step }}
      </div>
    </div>

    <!-- 完成状态：提供跳转报告页的入口 -->
    <div v-if="task.status === 'completed'" class="vp-card" style="text-align: center; padding: 48px">
      <div style="font-size: 48px; margin-bottom: 16px">✅</div>
      <h2 style="margin: 0 0 8px">调研完成</h2>
      <p class="text-muted" style="margin-bottom: 24px">报告已生成，点击查看详细内容</p>
      <button class="vp-btn vp-btn-primary" @click="router.push(`/report/${task.id}`)">查看报告</button>
    </div>

    <!-- 失败状态：显示错误信息，引导用户返回首页 -->
    <div v-else-if="task.status === 'failed'" class="vp-card" style="text-align: center; padding: 48px">
      <div style="font-size: 48px; margin-bottom: 16px">❌</div>
      <h2 style="margin: 0 0 8px; color: var(--vp-c-red)">调研失败</h2>
      <p class="text-muted" style="margin-bottom: 24px">{{ task.error_message || '发生未知错误' }}</p>
      <button class="vp-btn vp-btn-ghost" @click="router.push('/')">返回首页</button>
    </div>

    <!-- 进行中状态：展示 Agent 实时执行时间线 -->
    <div v-else>
      <AgentTimeline :logs="typedAgentLogs" :current-step="task.current_step" :task-type="task.task_type" />
    </div>
  </div>
</template>

<style scoped>
/* 头部区域容器：控制底部间距 */
.research-header {
  margin-bottom: 24px;
}

/* 任务标题：较大字号，与返回按钮和元信息保持合理间距 */
.research-header h1 {
  font-size: 24px;
  margin: 8px 0 12px;
}

/* 元信息行：标签水平排列，等间距分布 */
.research-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 任务类型徽章基础样式：圆角小标签 */
.type-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 500;
  line-height: 20px;
}

/* 主题调研类型的蓝色徽章 */
.type-search {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

/* 网站调研类型的绿色徽章 */
.type-website {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}
</style>

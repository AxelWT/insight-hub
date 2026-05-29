<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTask, type Task } from '../api/task'
import { useWebSocketStore } from '../stores/websocket'
import AgentTimeline, { type LogEntry } from '../components/AgentTimeline.vue'

const route = useRoute()
const router = useRouter()
const wsStore = useWebSocketStore()

const task = ref<Task | null>(null)
const loading = ref(true)

const typedAgentLogs = computed(() => wsStore.agentLogs as unknown as LogEntry[])

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

const typeLabels: Record<string, string> = {
  search: '🔍 主题调研',
  website: '🌐 网站调研',
}

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

function connectWs() {
  const id = Number(route.params.id)
  wsStore.connect(id)
}

function initTask() {
  loading.value = true
  fetchTask()
  connectWs()
}

onMounted(() => {
  initTask()
})

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

watch(() => wsStore.lastMessage, (msg) => {
  if (!msg) return
  if (msg.type === 'status_update' && task.value) {
    task.value.status = msg.data.status as string
    task.value.current_step = msg.data.current_step as string || task.value.current_step
    if (msg.data.status === 'completed') {
      router.push(`/report/${task.value.id}`)
    }
  }
  if (msg.type === 'progress_update' && task.value) {
    task.value.progress = msg.data.progress as number
  }
})

let pollTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  pollTimer = setInterval(fetchTask, 5000)
})
</script>

<template>
  <div v-if="loading" style="padding: 60px; text-align: center; color: var(--vp-c-text-3)">
    加载中...
  </div>

  <div v-else-if="task">
    <!-- Header -->
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

    <!-- Progress -->
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

    <!-- Completed State -->
    <div v-if="task.status === 'completed'" class="vp-card" style="text-align: center; padding: 48px">
      <div style="font-size: 48px; margin-bottom: 16px">✅</div>
      <h2 style="margin: 0 0 8px">调研完成</h2>
      <p class="text-muted" style="margin-bottom: 24px">报告已生成，点击查看详细内容</p>
      <button class="vp-btn vp-btn-primary" @click="router.push(`/report/${task.id}`)">查看报告</button>
    </div>

    <!-- Failed State -->
    <div v-else-if="task.status === 'failed'" class="vp-card" style="text-align: center; padding: 48px">
      <div style="font-size: 48px; margin-bottom: 16px">❌</div>
      <h2 style="margin: 0 0 8px; color: var(--vp-c-red)">调研失败</h2>
      <p class="text-muted" style="margin-bottom: 24px">{{ task.error_message || '发生未知错误' }}</p>
      <button class="vp-btn vp-btn-ghost" @click="router.push('/')">返回首页</button>
    </div>

    <!-- Agent Timeline -->
    <div v-else>
      <AgentTimeline :logs="typedAgentLogs" :current-step="task.current_step" :task-type="task.task_type" />
    </div>
  </div>
</template>

<style scoped>
.research-header {
  margin-bottom: 24px;
}

.research-header h1 {
  font-size: 24px;
  margin: 8px 0 12px;
}

.research-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 4px;
  font-weight: 500;
  line-height: 20px;
}

.type-search {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.type-website {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}
</style>

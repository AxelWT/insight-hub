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

onMounted(() => {
  fetchTask()
  connectWs()
})

onUnmounted(() => {
  wsStore.disconnect()
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
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div v-loading="loading">
    <div v-if="task">
      <h1>🔍 调研进行中</h1>
      <h2>{{ task.topic }}</h2>
      <p style="color: var(--el-text-color-secondary)">
        模型: {{ task.model }} |
        深度: {{ depthLabels[task.depth] || task.depth }} |
        创建时间: {{ new Date(task.created_at).toLocaleTimeString('zh-CN') }}
      </p>

      <el-progress :percentage="task.progress" :stroke-width="20" striped striped-flow style="margin: 16px 0" />

      <div v-if="task.status === 'completed'" style="text-align: center; margin-top: 32px">
        <el-result icon="success" title="调研完成！">
          <template #extra>
            <el-button type="primary" @click="router.push(`/report/${task.id}`)">📄 查看报告</el-button>
          </template>
        </el-result>
      </div>

      <div v-else-if="task.status === 'failed'">
        <el-result icon="error" :title="`调研失败: ${task.error_message || '未知错误'}`">
          <template #extra>
            <el-button @click="router.push('/')">← 返回首页</el-button>
          </template>
        </el-result>
      </div>

      <div v-else>
        <AgentTimeline :logs="typedAgentLogs" :current-step="task.current_step" />
      </div>
    </div>
  </div>
</template>

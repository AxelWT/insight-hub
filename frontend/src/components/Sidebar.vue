<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'
import { getModels } from '../api/report'
import type { TaskCreateParams } from '../api/task'

const router = useRouter()
const taskStore = useTaskStore()

const form = ref<TaskCreateParams>({
  topic: '',
  description: '',
  model: 'deepseek',
  depth: 'standard',
})

const models = ref<{ id: string; name: string }[]>([])
const submitting = ref(false)
const showForm = ref(false)

const depthOptions = [
  { value: 'quick', label: '快速（1轮搜索）' },
  { value: 'standard', label: '标准（2-3轮搜索）' },
  { value: 'deep', label: '深度（3-5轮搜索）' },
]

onMounted(async () => {
  await taskStore.fetchTasks()
  try {
    const res = await getModels()
    models.value = res.models
  } catch {
    models.value = [{ id: 'deepseek', name: 'DeepSeek' }]
  }
})

async function handleSubmit() {
  if (!form.value.topic.trim()) return
  submitting.value = true
  try {
    const task = await taskStore.addTask(form.value)
    form.value.topic = ''
    form.value.description = ''
    showForm.value = false
    router.push(`/research/${task.id}`)
  } finally {
    submitting.value = false
  }
}

function goToTask(task: { id: number; status: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}

const statusIcons: Record<string, string> = {
  pending: '⏳',
  planning: '🤔',
  searching: '🔍',
  evaluating: '📊',
  writing: '✍️',
  completed: '✅',
  failed: '❌',
}

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

function truncate(text: string, len: number) {
  return text.length > len ? text.slice(0, len) + '...' : text
}
</script>

<template>
  <div class="sidebar-inner">
    <!-- Brand -->
    <div class="sidebar-brand">
      <span class="sidebar-brand-icon">🔬</span>
      <span>AI 调研平台</span>
    </div>

    <div class="sidebar-divider" />

    <!-- New Research Button / Form -->
    <div class="sidebar-section">
      <button
        v-if="!showForm"
        class="vp-btn vp-btn-primary"
        style="width: 100%"
        @click="showForm = true"
      >
        + 新建调研
      </button>

      <div v-else class="new-research-form">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
          <span style="font-size: 14px; font-weight: 600; color: var(--vp-c-text-1)">新建调研</span>
          <button class="vp-btn vp-btn-text" style="padding: 4px 8px; font-size: 18px" @click="showForm = false">&times;</button>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">调研主题</label>
          <input v-model="form.topic" class="vp-input" placeholder="例如：2024年中国新能源汽车市场分析" @keyup.enter="handleSubmit" />
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">补充说明（可选）</label>
          <textarea v-model="form.description" class="vp-input" rows="2" placeholder="重点关注比亚迪、特斯拉的市占率变化" />
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">AI 模型</label>
          <select v-model="form.model" class="vp-select">
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">调研深度</label>
          <select v-model="form.depth" class="vp-select">
            <option v-for="d in depthOptions" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>

        <button
          class="vp-btn vp-btn-primary"
          style="width: 100%"
          :disabled="submitting || !form.topic.trim()"
          @click="handleSubmit"
        >
          {{ submitting ? '提交中...' : '开始调研' }}
        </button>
      </div>
    </div>

    <div class="sidebar-divider" />

    <!-- History List -->
    <div class="sidebar-section" style="flex: 1; overflow-y: auto; padding-bottom: 20px">
      <div class="sidebar-section-title">历史调研</div>

      <div v-if="taskStore.loading" style="padding: 16px; text-align: center; color: var(--vp-c-text-3); font-size: 13px">
        加载中...
      </div>

      <div v-else-if="taskStore.tasks.length === 0" style="padding: 16px; text-align: center; color: var(--vp-c-text-3); font-size: 13px">
        暂无历史记录
      </div>

      <div v-else>
        <div
          v-for="task in taskStore.tasks"
          :key="task.id"
          class="sidebar-task-item"
          :data-status="task.status"
          @click="goToTask(task)"
        >
          <div class="task-title">
            {{ statusIcons[task.status] || '' }} {{ truncate(task.topic, 28) }}
          </div>
          <div class="task-meta">
            {{ depthLabels[task.depth] || task.depth }}
            &middot;
            {{ new Date(task.created_at).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.new-research-form {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: var(--vp-radius);
  padding: 16px;
}
</style>

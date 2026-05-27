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
</script>

<template>
  <div style="padding: 16px; height: 100%; overflow-y: auto">
    <h2 style="margin: 0 0 16px">🔍 AI 调研平台</h2>

    <el-collapse model-value="form">
      <el-collapse-item title="📝 新建调研" name="form">
        <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
          <el-form-item label="调研主题">
            <el-input v-model="form.topic" placeholder="例如：2024年中国新能源汽车市场分析" />
          </el-form-item>
          <el-form-item label="补充说明（可选）">
            <el-input v-model="form.description" type="textarea" :rows="2" placeholder="重点关注比亚迪、特斯拉的市占率变化" />
          </el-form-item>
          <el-form-item label="AI 模型">
            <el-select v-model="form.model" style="width: 100%">
              <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="调研深度">
            <el-select v-model="form.depth" style="width: 100%">
              <el-option v-for="d in depthOptions" :key="d.value" :label="d.label" :value="d.value" />
            </el-select>
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit" style="width: 100%">
            开始调研
          </el-button>
        </el-form>
      </el-collapse-item>
    </el-collapse>

    <el-divider />

    <h4>历史调研</h4>
    <div v-if="taskStore.loading" v-loading="true" style="height: 100px" />
    <div v-else-if="taskStore.tasks.length === 0" style="color: var(--el-text-color-secondary)">
      暂无历史调研记录
    </div>
    <div v-else>
      <div
        v-for="task in taskStore.tasks"
        :key="task.id"
        class="task-item"
        @click="goToTask(task)"
      >
        <div class="task-title">
          {{ statusIcons[task.status] || '❓' }}
          {{ task.topic.length > 30 ? task.topic.slice(0, 30) + '...' : task.topic }}
        </div>
        <div class="task-meta">
          {{ depthLabels[task.depth] || task.depth }} |
          {{ new Date(task.created_at).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  margin-bottom: 4px;
}
.task-item:hover {
  background: var(--el-fill-color-light);
}
.task-title {
  font-size: 14px;
  line-height: 1.4;
}
.task-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}
</style>

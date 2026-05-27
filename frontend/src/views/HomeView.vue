<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'

const router = useRouter()
const taskStore = useTaskStore()

onMounted(() => {
  taskStore.fetchTasks()
})

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

function goToTask(task: { id: number; status: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}
</script>

<template>
  <div>
    <h1>🔍 AI 调研平台</h1>
    <p>输入调研主题，AI Agent 将自动搜索、分析、整理，生成结构化调研报告。</p>

    <el-divider />

    <h3>最近调研</h3>
    <div v-if="taskStore.loading" v-loading="true" style="height: 200px" />
    <el-empty v-else-if="taskStore.tasks.length === 0" description="暂无历史调研记录，请在左侧创建新的调研" />
    <el-table v-else :data="taskStore.tasks.slice(0, 10)" @row-click="goToTask" style="cursor: pointer">
      <el-table-column label="状态" width="60">
        <template #default="{ row }">
          {{ statusIcons[row.status] || '❓' }}
        </template>
      </el-table-column>
      <el-table-column prop="topic" label="调研主题" />
      <el-table-column label="深度" width="80">
        <template #default="{ row }">
          {{ depthLabels[row.depth] || row.depth }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="140">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

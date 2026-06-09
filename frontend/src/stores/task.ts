/**
 * 任务状态管理 Store
 *
 * 使用 Pinia 管理调研任务列表，提供获取、创建、删除、更新等操作。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTasks, createTask, deleteTask, type Task, type TaskCreateParams } from '../api/task'

export const useTaskStore = defineStore('task', () => {
  /** 任务列表 */
  const tasks = ref<Task[]>([])
  /** 加载状态 */
  const loading = ref(false)

  /** 从后端获取任务列表 */
  async function fetchTasks() {
    loading.value = true
    try {
      const res = await getTasks()
      tasks.value = res.tasks
    } finally {
      loading.value = false
    }
  }

  /** 创建新任务并添加到列表头部 */
  async function addTask(params: TaskCreateParams): Promise<Task> {
    const task = await createTask(params)
    tasks.value.unshift(task)  // 新任务插到最前面
    return task
  }

  /** 删除指定任务 */
  async function removeTask(id: number) {
    await deleteTask(id)
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  /** 本地更新任务属性（用于 WebSocket 推送的增量更新） */
  function updateTask(id: number, updates: Partial<Task>) {
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      tasks.value[idx] = { ...tasks.value[idx], ...updates }
    }
  }

  return { tasks, loading, fetchTasks, addTask, removeTask, updateTask }
})

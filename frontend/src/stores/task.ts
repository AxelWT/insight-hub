import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTasks, createTask, deleteTask, type Task, type TaskCreateParams } from '../api/task'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const res = await getTasks()
      tasks.value = res.tasks
    } finally {
      loading.value = false
    }
  }

  async function addTask(params: TaskCreateParams): Promise<Task> {
    const task = await createTask(params)
    tasks.value.unshift(task)
    return task
  }

  async function removeTask(id: number) {
    await deleteTask(id)
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  function updateTask(id: number, updates: Partial<Task>) {
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      tasks.value[idx] = { ...tasks.value[idx], ...updates }
    }
  }

  return { tasks, loading, fetchTasks, addTask, removeTask, updateTask }
})

/**
 * 任务 API 接口
 *
 * 封装任务相关的 HTTP 请求，包括类型定义和 CRUD 操作。
 */
import request from './request'

/** 任务数据类型 */
export interface Task {
  id: number
  topic: string
  description: string
  model: string
  depth: string
  task_type: 'search' | 'website'
  urls: string[]
  questions: string
  crawl_depth: number
  max_pages: number
  status: string
  progress: number
  current_step: string
  search_rounds: number
  created_at: string
  completed_at: string | null
  error_message: string | null
}

/** 创建任务请求参数 */
export interface TaskCreateParams {
  topic: string
  description?: string
  model: string
  depth?: string
  task_type?: 'search' | 'website'
  urls?: string[]
  questions?: string
  crawl_depth?: number
  max_pages?: number
}

/** 获取任务列表 */
export function getTasks(): Promise<{ tasks: Task[] }> {
  return request.get('/tasks')
}

/** 创建新任务 */
export function createTask(data: TaskCreateParams): Promise<Task> {
  return request.post('/tasks', data)
}

/** 获取单个任务详情 */
export function getTask(id: number): Promise<Task> {
  return request.get(`/tasks/${id}`)
}

/** 删除任务 */
export function deleteTask(id: number): Promise<{ ok: boolean }> {
  return request.delete(`/tasks/${id}`)
}

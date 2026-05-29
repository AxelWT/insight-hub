import request from './request'

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

export function getTasks(): Promise<{ tasks: Task[] }> {
  return request.get('/tasks')
}

export function createTask(data: TaskCreateParams): Promise<Task> {
  return request.post('/tasks', data)
}

export function getTask(id: number): Promise<Task> {
  return request.get(`/tasks/${id}`)
}

export function deleteTask(id: number): Promise<{ ok: boolean }> {
  return request.delete(`/tasks/${id}`)
}

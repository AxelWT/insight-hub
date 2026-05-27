import request from './request'

export interface Report {
  id: number
  task_id: number
  content: string
  word_count: number
  source_count: number
  file_path: string | null
}

export interface Source {
  id: number
  url: string
  title: string
  snippet: string
  content: string
  relevance_score: number | null
  search_round: number
  crawled_at: string
}

export interface AgentLog {
  id: number
  agent_name: string
  step: string
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  decision: string
  timestamp: string
}

export function getReport(taskId: number): Promise<Report> {
  return request.get(`/tasks/${taskId}/report`)
}

export function getSources(taskId: number): Promise<Source[]> {
  return request.get(`/tasks/${taskId}/sources`)
}

export function getAgentLogs(taskId: number): Promise<AgentLog[]> {
  return request.get(`/tasks/${taskId}/logs`)
}

export function getModels(): Promise<{ models: { id: string; name: string }[] }> {
  return request.get('/config/models')
}

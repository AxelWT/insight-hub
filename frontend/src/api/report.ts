/**
 * 报告 API 接口
 *
 * 封装报告、来源、Agent 日志和模型配置相关的 HTTP 请求。
 */
import request from './request'

/** 报告数据类型 */
export interface Report {
  id: number
  task_id: number
  content: string          // Markdown 正文
  word_count: number
  source_count: number
  file_path: string | null
}

/** 信息来源数据类型 */
export interface Source {
  id: number
  url: string
  title: string
  snippet: string          // 搜索摘要
  content: string          // 爬取正文
  relevance_score: number | null  // 相关性评分
  search_round: number     // 搜索轮次
  crawled_at: string
}

/** Agent 日志数据类型 */
export interface AgentLog {
  id: number
  agent_name: string
  step: string
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  decision: string         // Agent 决策说明
  timestamp: string
}

/** 获取指定任务的调研报告 */
export function getReport(taskId: number): Promise<Report> {
  return request.get(`/tasks/${taskId}/report`)
}

/** 获取指定任务的信息来源列表 */
export function getSources(taskId: number): Promise<Source[]> {
  return request.get(`/tasks/${taskId}/sources`)
}

/** 获取指定任务的 Agent 执行日志 */
export function getAgentLogs(taskId: number): Promise<AgentLog[]> {
  return request.get(`/tasks/${taskId}/logs`)
}

/** 获取当前可用的 AI 模型列表 */
export function getModels(): Promise<{ models: { id: string; name: string }[] }> {
  return request.get('/config/models')
}

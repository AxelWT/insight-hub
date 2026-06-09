/**
 * WebSocket 连接管理 Store
 *
 * 管理与后端的 WebSocket 连接，接收实时推送的任务状态更新和 Agent 日志。
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

/** WebSocket 消息类型定义 */
export interface WsMessage {
  type: 'status_update' | 'progress_update' | 'agent_log' | 'error'
  data: Record<string, unknown>
}

export const useWebSocketStore = defineStore('websocket', () => {
  /** WebSocket 连接实例 */
  const ws = ref<WebSocket | null>(null)
  /** 连接状态 */
  const connected = ref(false)
  /** 最近一条消息 */
  const lastMessage = ref<WsMessage | null>(null)
  /** Agent 日志列表（通过 WebSocket 推送逐步累积） */
  const agentLogs = ref<Record<string, unknown>[]>([])

  /** 建立与指定任务的 WebSocket 连接 */
  function connect(taskId: number) {
    // 先断开已有连接
    disconnect()
    agentLogs.value = []

    // 根据当前页面协议选择 ws/wss
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/api/ws/tasks/${taskId}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data)
      lastMessage.value = msg

      // 累积 Agent 日志
      if (msg.type === 'agent_log') {
        agentLogs.value.push(msg.data)
      }
    }

    ws.value.onclose = () => {
      connected.value = false
    }

    ws.value.onerror = () => {
      connected.value = false
    }
  }

  /** 断开 WebSocket 连接并重置状态 */
  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      connected.value = false
    }
  }

  return { ws, connected, lastMessage, agentLogs, connect, disconnect }
})

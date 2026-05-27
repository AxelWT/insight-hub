import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface WsMessage {
  type: 'status_update' | 'progress_update' | 'agent_log' | 'error'
  data: Record<string, unknown>
}

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const lastMessage = ref<WsMessage | null>(null)
  const agentLogs = ref<Record<string, unknown>[]>([])

  function connect(taskId: number) {
    disconnect()
    agentLogs.value = []

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/api/ws/tasks/${taskId}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data)
      lastMessage.value = msg

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

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      connected.value = false
    }
  }

  return { ws, connected, lastMessage, agentLogs, connect, disconnect }
})

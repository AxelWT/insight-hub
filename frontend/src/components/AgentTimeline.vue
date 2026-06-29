<script setup lang="ts">
import { computed } from 'vue'

export interface LogEntry {
  agent: string
  step: string
  decision?: string
  output?: unknown
}

const props = defineProps<{
  logs: LogEntry[]
  currentStep?: string
  taskType?: string
}>()

const agentDotClass: Record<string, string> = {
  supervisor: 'agent-dot-supervisor',
  searcher: 'agent-dot-searcher',
  crawler: 'agent-dot-crawler',
  evaluator: 'agent-dot-evaluator',
  writer: 'agent-dot-writer',
  website_crawler: 'agent-dot-website_crawler',
  website_writer: 'agent-dot-website_writer',
}

const stepLabels: Record<string, string> = {
  supervisor: '规划搜索策略',
  searcher: '搜索相关信息',
  crawler: '爬取网页内容',
  evaluator: '评估信息充分性',
  writer: '撰写调研报告',
  website_crawler: '爬取网站内容',
  website_writer: '分析内容并撰写报告',
}

const allAgents = ['supervisor', 'searcher', 'crawler', 'evaluator', 'writer']
const websiteAgents = ['website_crawler', 'website_writer']

const completedAgents = computed(() => {
  return new Set(props.logs.map((l) => l.agent))
})

const agentList = computed(() => {
  return props.taskType === 'website' ? websiteAgents : allAgents
})

const remainingAgents = computed(() => {
  return agentList.value.filter((a) => !completedAgents.value.has(a))
})

const statusInfo = computed(() => {
  const step = props.currentStep || ''
  const map: Record<string, { title: string; desc: string; color: string }> = {
    规划: { title: '规划中', desc: 'Agent 正在制定搜索策略...', color: '#e2a32d' },
    搜索: { title: '搜索中', desc: 'Agent 正在搜索相关信息...', color: '#3b82f6' },
    爬取: { title: '爬取中', desc: 'Agent 正在爬取网页内容...', color: '#8b5cf6' },
    评估: { title: '评估中', desc: 'Agent 正在评估信息充分性...', color: '#00d4aa' },
    撰写: { title: '撰写中', desc: 'Agent 正在撰写调研报告...', color: '#f472b6' },
    完成: { title: '已完成', desc: '调研报告已生成！', color: '#00d4aa' },
  }
  for (const [key, val] of Object.entries(map)) {
    if (step.includes(key)) return val
  }
  return { title: '进行中', desc: step, color: '#00a8e8' }
})

function formatOutput(output: unknown): string {
  if (!output) return ''
  if (typeof output === 'string') return output.slice(0, 500)
  if (Array.isArray(output)) return output.map((i) => `- ${i}`).join('\n')
  return JSON.stringify(output, null, 2).slice(0, 500)
}
</script>

<template>
  <div v-if="!logs.length && !currentStep" class="vp-card" style="text-align: center; padding: 48px">
    <p class="text-muted">Agent 准备中...</p>
  </div>

  <div v-else>
    <div class="status-card vp-card" style="margin-bottom: 24px">
      <div style="display: flex; align-items: center; gap: 12px">
        <div class="status-indicator" :style="{ background: statusInfo.color }" />
        <div>
          <div style="font-size: 16px; font-weight: 600; color: var(--vp-c-text-1)">{{ statusInfo.title }}</div>
          <div style="font-size: 13px; color: var(--vp-c-text-3)">{{ statusInfo.desc }}</div>
        </div>
      </div>
    </div>

    <h3 style="font-size: 16px; margin: 0 0 16px">执行时间线</h3>
    <div class="vp-timeline">
      <div
        v-for="(log, i) in logs"
        :key="i"
        class="vp-timeline-item done"
      >
        <div class="vp-timeline-dot" />
        <div class="vp-timeline-card">
          <div class="vp-timeline-card-header">
            <span :class="['agent-dot', agentDotClass[log.agent] || 'agent-dot-default']" />
            {{ log.step }}
          </div>
          <div v-if="log.decision" class="vp-timeline-card-body">
            {{ log.decision }}
          </div>
          <div v-if="log.output" style="margin-top: 8px">
            <pre style="white-space: pre-wrap; font-family: var(--vp-font-family-mono); font-size: 12px; color: var(--vp-c-text-3); max-height: 200px; overflow: auto; margin: 0">{{ formatOutput(log.output) }}</pre>
          </div>
        </div>
      </div>

      <div
        v-for="agent in remainingAgents"
        :key="agent"
        class="vp-timeline-item pending"
      >
        <div class="vp-timeline-dot" />
        <div style="font-size: 13px; color: var(--vp-c-text-3); padding: 4px 0">
          <span :class="['agent-dot', agentDotClass[agent] || 'agent-dot-default']" />
          {{ stepLabels[agent] || agent }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 currentColor; }
  50% { opacity: 0.7; box-shadow: 0 0 12px 2px currentColor; }
}
</style>

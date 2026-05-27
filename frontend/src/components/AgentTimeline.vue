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
}>()

const stepIcons: Record<string, string> = {
  supervisor: '🧠',
  searcher: '🔍',
  crawler: '🕷️',
  evaluator: '📊',
  writer: '✍️',
}

const stepLabels: Record<string, string> = {
  supervisor: '规划搜索策略',
  searcher: '搜索相关信息',
  crawler: '爬取网页内容',
  evaluator: '评估信息充分性',
  writer: '撰写调研报告',
}

const allAgents = ['supervisor', 'searcher', 'crawler', 'evaluator', 'writer']

const completedAgents = computed(() => {
  return new Set(props.logs.map((l) => l.agent))
})

const remainingAgents = computed(() => {
  return allAgents.filter((a) => !completedAgents.value.has(a))
})

const statusInfo = computed(() => {
  const step = props.currentStep || ''
  const map: Record<string, { title: string; desc: string }> = {
    规划: { title: '🤔 规划中', desc: 'Agent 正在制定搜索策略...' },
    搜索: { title: '🔍 搜索中', desc: 'Agent 正在搜索相关信息...' },
    爬取: { title: '🕷️ 爬取中', desc: 'Agent 正在爬取网页内容...' },
    评估: { title: '📊 评估中', desc: 'Agent 正在评估信息充分性...' },
    撰写: { title: '✍️ 撰写中', desc: 'Agent 正在撰写调研报告...' },
    完成: { title: '✅ 已完成', desc: '调研报告已生成！' },
  }
  for (const [key, val] of Object.entries(map)) {
    if (step.includes(key)) return val
  }
  return { title: '🔄 进行中', desc: step }
})

function formatOutput(output: unknown): string {
  if (!output) return ''
  if (typeof output === 'string') return output.slice(0, 500)
  if (Array.isArray(output)) return output.map((i) => `- ${i}`).join('\n')
  return JSON.stringify(output, null, 2).slice(0, 500)
}
</script>

<template>
  <div v-if="!logs.length && !currentStep">
    <el-empty description="Agent 尚未开始工作..." :image-size="60" />
  </div>

  <div v-else>
    <h3>{{ statusInfo.title }}</h3>
    <p style="color: var(--el-text-color-secondary)">{{ statusInfo.desc }}</p>

    <el-divider />

    <h4>📋 执行时间线</h4>
    <el-timeline>
      <el-timeline-item
        v-for="(log, i) in logs"
        :key="i"
        :timestamp="log.step"
        placement="top"
        :hollow="i < logs.length - 1"
      >
        <el-card shadow="never">
          <template #header>
            <span>{{ stepIcons[log.agent] || '⚙️' }} {{ log.step }}</span>
          </template>
          <div v-if="log.decision">
            <strong>决策：</strong>{{ log.decision }}
          </div>
          <div v-if="log.output" style="margin-top: 8px">
            <strong>输出：</strong>
            <pre style="white-space: pre-wrap; font-size: 12px; max-height: 200px; overflow: auto">{{ formatOutput(log.output) }}</pre>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>

    <div v-if="remainingAgents.length && currentStep !== '报告撰写完成'">
      <div v-for="agent in remainingAgents" :key="agent" style="padding: 4px 0; color: var(--el-text-color-secondary)">
        {{ stepIcons[agent] || '⚙️' }} ⏳ {{ stepLabels[agent] || agent }}
      </div>
    </div>
  </div>
</template>

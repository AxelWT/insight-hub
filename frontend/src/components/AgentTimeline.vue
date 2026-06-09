<script setup lang="ts">
import { computed } from 'vue'

// 日志条目类型定义，描述每个 Agent 执行步骤的记录
export interface LogEntry {
  agent: string       // 执行该步骤的 Agent 名称
  step: string        // 步骤描述
  decision?: string   // Agent 做出的决策（可选）
  output?: unknown    // 步骤的输出结果（可选，类型不固定）
}

const props = defineProps<{
  logs: LogEntry[]      // 已完成的日志条目列表
  currentStep?: string  // 当前正在执行的步骤描述
  taskType?: string     // 任务类型，用于区分不同 Agent 流程（如 "website"）
}>()

// 每个 Agent 对应的图标映射，用于时间线中的视觉标识
const stepIcons: Record<string, string> = {
  supervisor: '🧠',
  searcher: '🔍',
  crawler: '🕷️',
  evaluator: '📊',
  writer: '✍️',
  website_crawler: '🕷️',
  website_writer: '✍️',
}

// 每个 Agent 对应的中文标签，用于待执行步骤的展示
const stepLabels: Record<string, string> = {
  supervisor: '规划搜索策略',
  searcher: '搜索相关信息',
  crawler: '爬取网页内容',
  evaluator: '评估信息充分性',
  writer: '撰写调研报告',
  website_crawler: '爬取网站内容',
  website_writer: '分析内容并撰写报告',
}

// 默认调研任务的完整 Agent 执行顺序
const allAgents = ['supervisor', 'searcher', 'crawler', 'evaluator', 'writer']
// 网站分析任务使用精简的 Agent 流程
const websiteAgents = ['website_crawler', 'website_writer']

// 已完成的 Agent 集合，通过日志中出现的 agent 字段去重得到
const completedAgents = computed(() => {
  return new Set(props.logs.map((l) => l.agent))
})

// 根据任务类型返回对应的 Agent 列表，决定时间线展示哪些步骤
const agentList = computed(() => {
  return props.taskType === 'website' ? websiteAgents : allAgents
})

// 尚未执行的 Agent 列表，用于展示待执行的灰色步骤
const remainingAgents = computed(() => {
  return agentList.value.filter((a) => !completedAgents.value.has(a))
})

// 根据当前步骤关键词匹配状态信息，包含标题、描述和图标
// 用于顶部状态卡片的实时展示
const statusInfo = computed(() => {
  const step = props.currentStep || ''
  // 关键词到状态信息的映射，按步骤阶段划分
  const map: Record<string, { title: string; desc: string; icon: string }> = {
    规划: { title: '规划中', desc: 'Agent 正在制定搜索策略...', icon: '🤔' },
    搜索: { title: '搜索中', desc: 'Agent 正在搜索相关信息...', icon: '🔍' },
    爬取: { title: '爬取中', desc: 'Agent 正在爬取网页内容...', icon: '🕷️' },
    评估: { title: '评估中', desc: 'Agent 正在评估信息充分性...', icon: '📊' },
    撰写: { title: '撰写中', desc: 'Agent 正在撰写调研报告...', icon: '✍️' },
    完成: { title: '已完成', desc: '调研报告已生成！', icon: '✅' },
  }
  // 遍历关键词映射，匹配当前步骤包含的关键词
  for (const [key, val] of Object.entries(map)) {
    if (step.includes(key)) return val
  }
  // 未匹配到任何关键词时的默认状态
  return { title: '进行中', desc: step, icon: '🔄' }
})

// 格式化 Agent 输出内容，根据不同类型做截断或结构化处理
// 避免输出过长影响页面展示
function formatOutput(output: unknown): string {
  if (!output) return ''
  // 字符串类型直接截断到 500 字符
  if (typeof output === 'string') return output.slice(0, 500)
  // 数组类型将每项转为列表项形式
  if (Array.isArray(output)) return output.map((i) => `- ${i}`).join('\n')
  // 其他类型序列化为 JSON 并截断
  return JSON.stringify(output, null, 2).slice(0, 500)
}
</script>

<template>
  <!-- 空状态：尚无日志且无当前步骤时，显示准备中提示 -->
  <div v-if="!logs.length && !currentStep" class="vp-card" style="text-align: center; padding: 48px">
    <div style="font-size: 48px; margin-bottom: 12px">⏳</div>
    <p class="text-muted">Agent 准备中...</p>
  </div>

  <div v-else>
    <!-- 当前状态卡片：实时展示 Agent 正在执行的阶段 -->
    <div class="vp-card" style="margin-bottom: 24px">
      <div style="display: flex; align-items: center; gap: 12px">
        <span style="font-size: 28px">{{ statusInfo.icon }}</span>
        <div>
          <div style="font-size: 16px; font-weight: 600; color: var(--vp-c-text-1)">{{ statusInfo.title }}</div>
          <div style="font-size: 13px; color: var(--vp-c-text-3)">{{ statusInfo.desc }}</div>
        </div>
      </div>
    </div>

    <!-- 执行时间线：展示已完成和待执行的 Agent 步骤 -->
    <h3 style="font-size: 16px; margin: 0 0 16px">执行时间线</h3>
    <div class="vp-timeline">
      <!-- 已完成的步骤：展示步骤名称、决策和输出 -->
      <div
        v-for="(log, i) in logs"
        :key="i"
        class="vp-timeline-item done"
      >
        <div class="vp-timeline-dot" />
        <div class="vp-timeline-card">
          <div class="vp-timeline-card-header">
            {{ stepIcons[log.agent] || '⚙️' }} {{ log.step }}
          </div>
          <!-- 决策内容：Agent 在该步骤做出的判断或选择 -->
          <div v-if="log.decision" class="vp-timeline-card-body">
            {{ log.decision }}
          </div>
          <!-- 输出内容：以预格式化文本展示，限制最大高度避免过长 -->
          <div v-if="log.output" style="margin-top: 8px">
            <pre style="white-space: pre-wrap; font-size: 12px; color: var(--vp-c-text-3); max-height: 200px; overflow: auto; margin: 0">{{ formatOutput(log.output) }}</pre>
          </div>
        </div>
      </div>

      <!-- 待执行步骤：灰显展示尚未开始的 Agent 流程 -->
      <div
        v-for="agent in remainingAgents"
        :key="agent"
        class="vp-timeline-item pending"
      >
        <div class="vp-timeline-dot" />
        <div style="font-size: 13px; color: var(--vp-c-text-3); padding: 4px 0">
          {{ stepIcons[agent] || '⚙️' }} {{ stepLabels[agent] || agent }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { getTask, type Task } from '../api/task'
import { getReport, getSources, getAgentLogs, type Report, type Source, type AgentLog } from '../api/report'

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt()

const task = ref<Task | null>(null)
const report = ref<Report | null>(null)
const sources = ref<Source[]>([])
const logs = ref<AgentLog[]>([])
const loading = ref(true)
const activeTab = ref('report')

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

const agentIcons: Record<string, string> = {
  supervisor: '🧠',
  searcher: '🔍',
  crawler: '🕷️',
  evaluator: '📊',
  writer: '✍️',
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    task.value = await getTask(id)
    report.value = await getReport(id)
    sources.value = await getSources(id)
    logs.value = await getAgentLogs(id)
  } catch {
    router.push('/')
  } finally {
    loading.value = false
  }
})

function extractToc(content: string): { title: string; level: number }[] {
  const toc: { title: string; level: number }[] = []
  for (const line of content.split('\n')) {
    if (line.startsWith('#')) {
      const level = line.split(' ')[0].length
      if (level <= 4) {
        toc.push({ title: line.replace(/^#+\s*/, ''), level })
      }
    }
  }
  return toc
}

const sourcesByRound = computed(() => {
  const grouped: Record<number, Source[]> = {}
  for (const s of sources.value) {
    grouped[s.search_round] = grouped[s.search_round] || []
    grouped[s.search_round].push(s)
  }
  return grouped
})

function downloadMarkdown() {
  if (!report.value || !task.value) return
  const blob = new Blob([report.value.content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report_${task.value.id}.md`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyToClipboard() {
  if (!report.value) return
  await navigator.clipboard.writeText(report.value.content)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <div v-loading="loading">
    <div v-if="task">
      <el-row align="middle" style="margin-bottom: 16px">
        <el-col :span="1">
          <el-button @click="router.push('/')" text>←</el-button>
        </el-col>
        <el-col :span="23">
          <h1 style="margin: 0">{{ task.topic }}</h1>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-bottom: 24px">
        <el-col :span="6">
          <el-statistic title="字数" :value="report?.word_count || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="来源数" :value="report?.source_count || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="搜索轮次" :value="task.search_rounds" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="深度" :value="depthLabels[task.depth] || task.depth" />
        </el-col>
      </el-row>

      <el-empty v-if="!report" description="报告尚未生成" />

      <template v-else>
        <el-tabs v-model="activeTab">
          <el-tab-pane label="📄 报告" name="report">
            <el-row :gutter="24">
              <el-col :span="6">
                <h3>目录</h3>
                <div v-for="(item, i) in extractToc(report.content)" :key="i"
                     :style="{ paddingLeft: (item.level - 1) * 16 + 'px', fontSize: '14px', lineHeight: '2' }">
                  {{ item.title }}
                </div>
              </el-col>
              <el-col :span="18">
                <div v-html="md.render(report.content)" class="report-content" />
              </el-col>
            </el-row>

            <el-divider />
            <el-row :gutter="16">
              <el-col :span="8">
                <el-button @click="downloadMarkdown" style="width: 100%">📥 下载 Markdown</el-button>
              </el-col>
              <el-col :span="8">
                <el-button @click="copyToClipboard" style="width: 100%">📋 复制到剪贴板</el-button>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="📚 来源" name="sources">
            <div v-if="!sources.length">
              <el-empty description="无来源信息" />
            </div>
            <template v-for="(roundSources, round) in sourcesByRound" :key="round">
              <h4>第 {{ round }} 轮搜索</h4>
              <el-collapse>
                <el-collapse-item
                  v-for="(source, i) in roundSources"
                  :key="source.id"
                  :title="`[${i + 1}] ${source.title || source.url.slice(0, 60)}`"
                >
                  <p><strong>URL：</strong><a :href="source.url" target="_blank">{{ source.url }}</a></p>
                  <p v-if="source.snippet"><strong>摘要：</strong>{{ source.snippet.slice(0, 500) }}</p>
                  <p v-if="source.relevance_score"><strong>相关性：</strong>{{ source.relevance_score.toFixed(2) }}</p>
                </el-collapse-item>
              </el-collapse>
            </template>
          </el-tab-pane>

          <el-tab-pane label="🤖 Agent 日志" name="logs">
            <div v-if="!logs.length">
              <el-empty description="无 Agent 日志" />
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="log in logs"
                :key="log.id"
                :timestamp="new Date(log.timestamp).toLocaleTimeString('zh-CN')"
                placement="top"
              >
                <el-card shadow="never">
                  <template #header>
                    {{ agentIcons[log.agent_name] || '⚙️' }} [{{ log.agent_name }}] {{ log.step }}
                  </template>
                  <p v-if="log.decision"><strong>决策：</strong>{{ log.decision }}</p>
                  <pre v-if="log.output_data" style="white-space: pre-wrap; font-size: 12px">{{ JSON.stringify(log.output_data, null, 2) }}</pre>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-tab-pane>
        </el-tabs>
      </template>
    </div>
  </div>
</template>

<style scoped>
.report-content {
  line-height: 1.8;
  font-size: 15px;
}
.report-content h1, .report-content h2, .report-content h3 {
  margin-top: 24px;
  margin-bottom: 12px;
}
.report-content p {
  margin-bottom: 12px;
}
.report-content code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.report-content pre {
  background: var(--el-fill-color-darker);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}
</style>

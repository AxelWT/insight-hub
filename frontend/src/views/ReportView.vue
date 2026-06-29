<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
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

const agentColors: Record<string, string> = {
  supervisor: 'agent-dot-supervisor',
  searcher: 'agent-dot-searcher',
  crawler: 'agent-dot-crawler',
  evaluator: 'agent-dot-evaluator',
  writer: 'agent-dot-writer',
  website_crawler: 'agent-dot-website_crawler',
  website_writer: 'agent-dot-website_writer',
}

const agentLabels: Record<string, string> = {
  supervisor: 'Supervisor',
  searcher: 'Searcher',
  crawler: 'Crawler',
  evaluator: 'Evaluator',
  writer: 'Writer',
  website_crawler: 'Website Crawler',
  website_writer: 'Website Writer',
}

async function fetchData() {
  const id = Number(route.params.id)
  loading.value = true
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
  await nextTick()
  setupScrollSpy()
}

onMounted(() => {
  fetchData()
})

watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    activeTab.value = 'report'
    fetchData()
  }
})

function slugify(text: string): string {
  return text
    .replace(/\s+/g, '-')
    .replace(/[^\w一-鿿-]/g, '')
    .toLowerCase()
}

function extractToc(content: string): { title: string; level: number; slug: string }[] {
  const toc: { title: string; level: number; slug: string }[] = []
  for (const line of content.split('\n')) {
    if (line.startsWith('#')) {
      const level = line.split(' ')[0].length
      if (level <= 4) {
        const title = line.replace(/^#+\s*/, '')
        toc.push({ title, level, slug: slugify(title) })
      }
    }
  }
  return toc
}

function addHeadingIds(html: string): string {
  html = html.replace(
    /(\[来源\d+\]\s*.*?\s*-\s*)(https?:\/\/[^\s<]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener">$2</a>'
  )
  return html.replace(/<h([1-4])([^>]*)>([\s\S]*?)<\/h\1>/g, (match, level, attrs, content) => {
    if (/id=/.test(attrs)) return match
    const text = content.replace(/<[^>]+>/g, '')
    const id = slugify(text)
    return `<h${level}${attrs} id="${id}">${content}</h${level}>`
  })
}

const activeTocIndex = ref(-1)
let observer: IntersectionObserver | null = null

function setupScrollSpy() {
  observer?.disconnect()
  const headings = document.querySelectorAll('.vp-doc h1, .vp-doc h2, .vp-doc h3, .vp-doc h4')
  if (!headings.length) return
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const slug = entry.target.id
          const idx = extractToc(report.value?.content || '').findIndex(t => t.slug === slug)
          if (idx >= 0) activeTocIndex.value = idx
        }
      }
    },
    { rootMargin: '-10% 0px -80% 0px' }
  )
  headings.forEach(h => observer!.observe(h))
}

function scrollToHeading(slug: string) {
  const el = document.getElementById(slug)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

watch(activeTab, (tab) => {
  if (tab === 'report') {
    nextTick(setupScrollSpy)
  } else {
    observer?.disconnect()
    activeTocIndex.value = -1
  }
})

const sourcesByRound = computed(() => {
  const grouped: Record<number, Source[]> = {}
  for (const s of sources.value) {
    grouped[s.search_round] = grouped[s.search_round] || []
    grouped[s.search_round].push(s)
  }
  return grouped
})

onUnmounted(() => {
  observer?.disconnect()
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
  <div v-if="loading" style="padding: 60px; text-align: center; color: var(--vp-c-text-3)">
    加载中...
  </div>

  <div v-else-if="task">
    <div class="report-header">
      <div class="report-breadcrumb">
        <span class="breadcrumb-item" @click="router.push('/')">首页</span>
        <span class="breadcrumb-separator">/</span>
        <span class="breadcrumb-item current">{{ task.topic }}</span>
      </div>

      <h1>{{ task.topic }}</h1>

      <div class="vp-stat-row">
        <div class="vp-stat">
          <span class="vp-stat-value">{{ report?.word_count || 0 }}</span>
          <span class="vp-stat-label">字数</span>
        </div>
        <div class="vp-stat">
          <span class="vp-stat-value">{{ report?.source_count || 0 }}</span>
          <span class="vp-stat-label">来源</span>
        </div>
        <div class="vp-stat">
          <span class="vp-stat-value">{{ task.search_rounds }}</span>
          <span class="vp-stat-label">搜索轮次</span>
        </div>
        <div class="vp-stat">
          <span class="vp-stat-value">{{ depthLabels[task.depth] || task.depth }}</span>
          <span class="vp-stat-label">深度</span>
        </div>
      </div>
    </div>

    <div v-if="!report" class="vp-card" style="text-align: center; padding: 48px">
      <p class="text-muted">报告尚未生成</p>
    </div>

    <template v-else>
      <div class="vp-tabs">
        <button
          :class="['vp-tab', { active: activeTab === 'report' }]"
          @click="activeTab = 'report'"
        >报告</button>
        <button
          :class="['vp-tab', { active: activeTab === 'sources' }]"
          @click="activeTab = 'sources'"
        >来源 ({{ sources.length }})</button>
        <button
          :class="['vp-tab', { active: activeTab === 'logs' }]"
          @click="activeTab = 'logs'"
        >Agent 日志</button>
      </div>

      <div v-if="activeTab === 'report'" class="report-layout">
        <div class="report-body">
          <div v-html="addHeadingIds(md.render(report.content))" class="vp-doc" />

          <div class="report-actions">
            <button class="vp-btn vp-btn-ghost" @click="downloadMarkdown">下载 Markdown</button>
            <button class="vp-btn vp-btn-ghost" @click="copyToClipboard">复制内容</button>
          </div>
        </div>

        <div class="report-toc">
          <div class="toc-title">目录</div>
          <div
            v-for="(item, i) in extractToc(report.content)"
            :key="i"
            class="toc-item"
            :class="{ active: activeTocIndex === i }"
            :style="{ paddingLeft: (item.level - 1) * 16 + 'px' }"
            @click="scrollToHeading(item.slug)"
          >
            {{ item.title }}
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'sources'">
        <div v-if="!sources.length" class="vp-card" style="text-align: center; padding: 48px">
          <p class="text-muted">无来源信息</p>
        </div>

        <template v-for="(roundSources, round) in sourcesByRound" :key="round">
          <h3 style="margin: 24px 0 12px; font-size: 15px">第 {{ round }} 轮搜索</h3>
          <div
            v-for="(source, i) in roundSources"
            :key="source.id"
            class="vp-card source-card"
          >
            <div class="source-header">
              <span class="source-index">[{{ i + 1 }}]</span>
              <a :href="source.url" target="_blank" class="source-title">{{ source.title || source.url.slice(0, 60) }}</a>
            </div>
            <div v-if="source.snippet" class="source-snippet">{{ source.snippet.slice(0, 300) }}</div>
            <div class="source-footer">
              <a :href="source.url" target="_blank" class="source-url">{{ source.url }}</a>
              <span v-if="source.relevance_score" class="vp-tag vp-tag-gray">相关性 {{ source.relevance_score.toFixed(2) }}</span>
            </div>
          </div>
        </template>
      </div>

      <div v-if="activeTab === 'logs'">
        <div v-if="!logs.length" class="vp-card" style="text-align: center; padding: 48px">
          <p class="text-muted">无 Agent 日志</p>
        </div>

        <div v-else class="vp-timeline">
          <div v-for="log in logs" :key="log.id" class="vp-timeline-item done">
            <div class="vp-timeline-dot" />
            <div class="vp-timeline-timestamp">
              {{ new Date(log.timestamp).toLocaleTimeString('zh-CN') }}
            </div>
            <div class="vp-timeline-card">
              <div class="vp-timeline-card-header">
                <span :class="['agent-dot', agentColors[log.agent_name] || 'agent-dot-default']" />
                {{ agentLabels[log.agent_name] || log.agent_name }} &mdash; {{ log.step }}
              </div>
              <div v-if="log.decision" class="vp-timeline-card-body">
                {{ log.decision }}
              </div>
              <pre
                v-if="log.output_data"
                style="margin: 8px 0 0; white-space: pre-wrap; font-family: var(--vp-font-family-mono); font-size: 12px; color: var(--vp-c-text-3); max-height: 200px; overflow: auto"
              >{{ JSON.stringify(log.output_data, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.report-header {
  margin-bottom: 8px;
}

.report-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--vp-c-text-3);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--vp-c-divider);
  margin-bottom: 16px;
}

.breadcrumb-item {
  cursor: pointer;
  transition: color var(--vp-transition);
}

.breadcrumb-item:hover {
  color: var(--vp-c-brand);
}

.breadcrumb-item.current {
  color: var(--vp-c-text-2);
  cursor: default;
}

.breadcrumb-item.current:hover {
  color: var(--vp-c-text-2);
}

.breadcrumb-separator {
  color: var(--vp-c-text-3);
  opacity: 0.4;
}

.report-header h1 {
  font-size: 22px;
  margin: 0 0 16px;
}

.report-header .vp-stat-row {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--vp-c-divider);
  margin-bottom: 24px;
}

.report-layout {
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 32px;
}

.report-body {
  min-width: 0;
  overflow: hidden;
}

.report-toc {
  position: sticky;
  top: 32px;
  align-self: start;
}

.toc-title {
  font-family: var(--vp-font-family-mono);
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--vp-c-text-3);
  margin-bottom: 12px;
}

.toc-item {
  font-size: 13px;
  color: var(--vp-c-text-3);
  line-height: 2;
  cursor: pointer;
  transition: color var(--vp-transition);
}

.toc-item:hover {
  color: var(--vp-c-text-1);
}

.toc-item.active {
  color: var(--vp-c-brand);
  font-weight: 600;
}

.report-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--vp-c-divider);
}

.source-card {
  margin-bottom: 12px;
  padding: 16px 20px;
  overflow: hidden;
}

.source-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.source-index {
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  font-weight: 500;
  color: var(--vp-c-brand);
  flex-shrink: 0;
}

.source-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.source-title:hover {
  color: var(--vp-c-brand);
}

.source-snippet {
  font-size: 13px;
  color: var(--vp-c-text-3);
  line-height: 1.6;
  margin-bottom: 8px;
}

.source-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.source-url {
  font-family: var(--vp-font-family-mono);
  font-size: 12px;
  color: var(--vp-c-text-3);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 70%;
  cursor: pointer;
}

.source-url:hover {
  color: var(--vp-c-brand);
  text-decoration: underline;
}
</style>

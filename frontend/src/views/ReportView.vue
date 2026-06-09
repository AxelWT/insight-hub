<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { getTask, type Task } from '../api/task'
import { getReport, getSources, getAgentLogs, type Report, type Source, type AgentLog } from '../api/report'

const route = useRoute()
const router = useRouter()
// 初始化 Markdown 渲染器，用于将报告内容渲染为 HTML
const md = new MarkdownIt()

// 页面核心数据：任务、报告、来源、Agent 日志
const task = ref<Task | null>(null)
const report = ref<Report | null>(null)
const sources = ref<Source[]>([])
const logs = ref<AgentLog[]>([])
const loading = ref(true)
const activeTab = ref('report')

// 搜索深度对应的中文标签映射
const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

// Agent 类型对应的图标映射，用于日志展示时快速识别角色
const agentIcons: Record<string, string> = {
  supervisor: '🧠',
  searcher: '🔍',
  crawler: '🕷️',
  evaluator: '📊',
  writer: '✍️',
  website_crawler: '🕷️',
  website_writer: '✍️',
}

// 根据 URL 中的任务 ID 请求所有数据
async function fetchData() {
  const id = Number(route.params.id)
  loading.value = true
  try {
    // 并行请求四类数据：任务详情、报告内容、来源列表、Agent 日志
    task.value = await getTask(id)
    report.value = await getReport(id)
    sources.value = await getSources(id)
    logs.value = await getAgentLogs(id)
  } catch {
    // 请求失败时跳转回首页，避免停留在无效页面
    router.push('/')
  } finally {
    loading.value = false
  }
  // 等待 DOM 更新后再设置滚动监听，确保标题元素已渲染
  await nextTick()
  setupScrollSpy()
}

onMounted(() => {
  fetchData()
})

// 监听路由参数变化，重新加载数据
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    // 切换任务时重置到报告标签页
    activeTab.value = 'report'
    fetchData()
  }
})

// 将标题文本转为 URL 安全的 slug，用于目录锚点定位
function slugify(text: string): string {
  return text
    .replace(/\s+/g, '-')
    .replace(/[^\w一-鿿-]/g, '')
    .toLowerCase()
}

// 从 Markdown 原文提取标题结构，生成目录数据
function extractToc(content: string): { title: string; level: number; slug: string }[] {
  const toc: { title: string; level: number; slug: string }[] = []
  for (const line of content.split('\n')) {
    if (line.startsWith('#')) {
      const level = line.split(' ')[0].length
      // 只提取 h1~h4 级别标题，避免目录过于细碎
      if (level <= 4) {
        const title = line.replace(/^#+\s*/, '')
        toc.push({ title, level, slug: slugify(title) })
      }
    }
  }
  return toc
}

// 对渲染后的 HTML 进行后处理：给标题添加 id 锚点，并将来源引用转为可点击链接
function addHeadingIds(html: string): string {
  // 将来源引用中的裸 URL 转换为可点击的超链接
  html = html.replace(
    /(\[来源\d+\]\s*.*?\s*-\s*)(https?:\/\/[^\s<]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener">$2</a>'
  )
  // 为 h1~h4 标题添加 id 属性，用于目录锚点定位；已有 id 的标题跳过
  return html.replace(/<h([1-4])([^>]*)>([\s\S]*?)<\/h\1>/g, (match, level, attrs, content) => {
    if (/id=/.test(attrs)) return match
    // 去除 HTML 标签，取纯文本作为 id
    const text = content.replace(/<[^>]+>/g, '')
    const id = slugify(text)
    return `<h${level}${attrs} id="${id}">${content}</h${level}>`
  })
}

// 当前目录中高亮的标题索引，-1 表示无高亮
const activeTocIndex = ref(-1)
// IntersectionObserver 实例，用于监听标题元素进入视口
let observer: IntersectionObserver | null = null

// 设置滚动监听：当标题元素进入视口时，自动高亮对应目录项
function setupScrollSpy() {
  // 先断开之前的监听，避免重复注册
  observer?.disconnect()
  const headings = document.querySelectorAll('.vp-doc h1, .vp-doc h2, .vp-doc h3, .vp-doc h4')
  if (!headings.length) return
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          // 根据标题的 id 匹配目录项索引
          const slug = entry.target.id
          const idx = extractToc(report.value?.content || '').findIndex(t => t.slug === slug)
          if (idx >= 0) activeTocIndex.value = idx
        }
      }
    },
    // 仅当标题位于视口顶部 10%~20% 区域时触发，避免底部标题误判
    { rootMargin: '-10% 0px -80% 0px' }
  )
  headings.forEach(h => observer!.observe(h))
}

// 点击目录项时平滑滚动到对应标题位置
function scrollToHeading(slug: string) {
  const el = document.getElementById(slug)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

// 切换标签页时管理滚动监听：报告页启用，其他页禁用
watch(activeTab, (tab) => {
  if (tab === 'report') {
    nextTick(setupScrollSpy)
  } else {
    observer?.disconnect()
    activeTocIndex.value = -1
  }
})

// 将来源数据按搜索轮次分组，方便在来源标签页中按轮次展示
const sourcesByRound = computed(() => {
  const grouped: Record<number, Source[]> = {}
  for (const s of sources.value) {
    grouped[s.search_round] = grouped[s.search_round] || []
    grouped[s.search_round].push(s)
  }
  return grouped
})

// 组件卸载时清理 IntersectionObserver，防止内存泄漏
onUnmounted(() => {
  observer?.disconnect()
})

// 下载报告为 Markdown 文件
function downloadMarkdown() {
  if (!report.value || !task.value) return
  const blob = new Blob([report.value.content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report_${task.value.id}.md`
  a.click()
  // 释放临时 URL，避免内存泄漏
  URL.revokeObjectURL(url)
}

// 复制报告内容到剪贴板
async function copyToClipboard() {
  if (!report.value) return
  await navigator.clipboard.writeText(report.value.content)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <!-- 全屏加载提示 -->
  <div v-if="loading" style="padding: 60px; text-align: center; color: var(--vp-c-text-3)">
    加载中...
  </div>

  <div v-else-if="task">
    <!-- 页面头部：面包屑导航、标题、统计信息 -->
    <div class="report-header">
      <!-- 面包屑：首页 / 当前任务主题 -->
      <div class="report-breadcrumb">
        <span class="breadcrumb-item" @click="router.push('/')">首页</span>
        <span class="breadcrumb-separator">/</span>
        <span class="breadcrumb-item current">{{ task.topic }}</span>
      </div>

      <h1>{{ task.topic }}</h1>

      <!-- 报告统计：字数、来源数、搜索轮次、深度 -->
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

    <!-- 报告尚未生成时的空状态提示 -->
    <div v-if="!report" class="vp-card" style="text-align: center; padding: 48px">
      <div style="font-size: 48px; margin-bottom: 12px">📄</div>
      <p class="text-muted">报告尚未生成</p>
    </div>

    <template v-else>
      <!-- 标签页切换栏 -->
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

      <!-- 报告标签页：正文 + 侧边目录 -->
      <div v-if="activeTab === 'report'" class="report-layout">
        <div class="report-body">
          <!-- 渲染 Markdown 内容为 HTML，并添加标题锚点和来源链接 -->
          <div v-html="addHeadingIds(md.render(report.content))" class="vp-doc" />

          <!-- 报告底部操作栏：下载和复制 -->
          <div class="report-actions">
            <button class="vp-btn vp-btn-ghost" @click="downloadMarkdown">下载 Markdown</button>
            <button class="vp-btn vp-btn-ghost" @click="copyToClipboard">复制内容</button>
          </div>
        </div>

        <!-- 侧边目录：根据标题层级缩进，当前高亮项跟随滚动 -->
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

      <!-- 来源标签页：按搜索轮次分组展示来源卡片 -->
      <div v-if="activeTab === 'sources'">
        <!-- 无来源时的空状态 -->
        <div v-if="!sources.length" class="vp-card" style="text-align: center; padding: 48px">
          <p class="text-muted">无来源信息</p>
        </div>

        <!-- 按轮次分组展示来源列表 -->
        <template v-for="(roundSources, round) in sourcesByRound" :key="round">
          <h3 style="margin: 24px 0 12px; font-size: 15px">第 {{ round }} 轮搜索</h3>
          <div
            v-for="(source, i) in roundSources"
            :key="source.id"
            class="vp-card source-card"
          >
            <!-- 来源标题和序号 -->
            <div class="source-header">
              <span class="source-index">[{{ i + 1 }}]</span>
              <a :href="source.url" target="_blank" class="source-title">{{ source.title || source.url.slice(0, 60) }}</a>
            </div>
            <!-- 来源摘要，截取前 300 字符 -->
            <div v-if="source.snippet" class="source-snippet">{{ source.snippet.slice(0, 300) }}</div>
            <!-- 来源 URL 和相关性评分 -->
            <div class="source-footer">
              <a :href="source.url" target="_blank" class="source-url">{{ source.url }}</a>
              <span v-if="source.relevance_score" class="vp-tag vp-tag-gray">相关性 {{ source.relevance_score.toFixed(2) }}</span>
            </div>
          </div>
        </template>
      </div>

      <!-- Agent 日志标签页：按时间线展示各 Agent 的执行记录 -->
      <div v-if="activeTab === 'logs'">
        <!-- 无日志时的空状态 -->
        <div v-if="!logs.length" class="vp-card" style="text-align: center; padding: 48px">
          <p class="text-muted">无 Agent 日志</p>
        </div>

        <!-- 时间线形式的日志列表 -->
        <div v-else class="vp-timeline">
          <div v-for="log in logs" :key="log.id" class="vp-timeline-item done">
            <div class="vp-timeline-dot" />
            <!-- 时间戳，使用中文本地化格式 -->
            <div class="vp-timeline-timestamp">
              {{ new Date(log.timestamp).toLocaleTimeString('zh-CN') }}
            </div>
            <div class="vp-timeline-card">
              <!-- Agent 名称和步骤 -->
              <div class="vp-timeline-card-header">
                {{ agentIcons[log.agent_name] || '⚙️' }} {{ log.agent_name }} &mdash; {{ log.step }}
              </div>
              <!-- Agent 的决策说明 -->
              <div v-if="log.decision" class="vp-timeline-card-body">
                {{ log.decision }}
              </div>
              <!-- Agent 输出的结构化数据，以 JSON 格式展示 -->
              <pre
                v-if="log.output_data"
                style="margin: 8px 0 0; white-space: pre-wrap; font-size: 12px; color: var(--vp-c-text-3); max-height: 200px; overflow: auto"
              >{{ JSON.stringify(log.output_data, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
/* 报告页面头部区域 */
.report-header {
  margin-bottom: 8px;
}

/* 面包屑导航栏 */
.report-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--vp-c-text-3);
  padding-bottom: 16px;
  border-bottom: 1px solid var(--vp-c-divider-light);
  margin-bottom: 16px;
}

/* 面包屑项：可点击，带悬停变色效果 */
.breadcrumb-item {
  cursor: pointer;
  transition: color var(--vp-transition);
}

.breadcrumb-item:hover {
  color: var(--vp-c-brand);
}

/* 当前页面包屑：使用较深文字色，禁用悬停效果 */
.breadcrumb-item.current {
  color: var(--vp-c-text-2);
  cursor: default;
}

.breadcrumb-item.current:hover {
  color: var(--vp-c-text-2);
}

/* 面包屑分隔符 */
.breadcrumb-separator {
  color: var(--vp-c-divider);
}

/* 报告标题样式 */
.report-header h1 {
  font-size: 22px;
  margin: 0 0 16px;
}

/* 统计行底部间距和分隔线 */
.report-header .vp-stat-row {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--vp-c-divider-light);
  margin-bottom: 24px;
}

/* 报告主体布局：左侧内容 + 右侧目录，使用 grid 实现 */
.report-layout {
  display: grid;
  grid-template-columns: 1fr 200px;
  gap: 32px;
}

/* 报告正文区域：防止长内容溢出 */
.report-body {
  min-width: 0;
  overflow: hidden;
}

/* 侧边目录：固定在视口顶部，跟随页面滚动 */
.report-toc {
  position: sticky;
  top: 32px;
  align-self: start;
}

/* 目录标题样式 */
.toc-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--vp-c-text-3);
  margin-bottom: 12px;
}

/* 目录项：点击可跳转，悬停变色 */
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

/* 当前高亮的目录项：使用品牌色强调 */
.toc-item.active {
  color: var(--vp-c-brand);
  font-weight: 600;
}

/* 报告底部操作栏：下载和复制按钮 */
.report-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--vp-c-divider-light);
}

/* 来源卡片样式 */
.source-card {
  margin-bottom: 12px;
  padding: 16px 20px;
  overflow: hidden;
}

/* 来源卡片头部：序号 + 标题 */
.source-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

/* 来源序号标签 */
.source-index {
  font-size: 12px;
  font-weight: 700;
  color: var(--vp-c-brand);
  flex-shrink: 0;
}

/* 来源标题链接 */
.source-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  text-decoration: none;
}

.source-title:hover {
  color: var(--vp-c-brand);
}

/* 来源摘要文字 */
.source-snippet {
  font-size: 13px;
  color: var(--vp-c-text-3);
  line-height: 1.6;
  margin-bottom: 8px;
}

/* 来源卡片底部：URL + 相关性评分 */
.source-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

/* 来源 URL 链接：超长时省略显示 */
.source-url {
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

/* 来源标题可点击 */
.source-title {
  cursor: pointer;
}
</style>

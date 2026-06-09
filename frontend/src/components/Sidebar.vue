<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'
import { getModels } from '../api/report'
import type { TaskCreateParams } from '../api/task'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const taskStore = useTaskStore()

// 主题搜索调研的表单数据
const searchForm = ref<TaskCreateParams>({
  topic: '',
  description: '',
  model: 'deepseek',
  depth: 'standard',
})

// 网站调研的表单数据，task_type 固定为 website
const websiteForm = ref<TaskCreateParams>({
  topic: '',
  questions: '',
  model: 'deepseek',
  task_type: 'website',
  urls: [],
  crawl_depth: 0,
  max_pages: 20,
})

// 当前正在输入的新 URL，用于逐个添加到 urls 列表
const newUrl = ref('')
// 可选的 AI 模型列表，从后端接口动态获取
const models = ref<{ id: string; name: string }[]>([])
// 防止重复提交的加载标志
const submitting = ref(false)
// 控制当前展示的表单类型：search / website / null（显示按钮组）
const formType = ref<'search' | 'website' | null>(null)

// 调研深度选项，决定 AI 搜索的轮数
const depthOptions = [
  { value: 'quick', label: '快速（1轮搜索）' },
  { value: 'standard', label: '标准（2-3轮搜索）' },
  { value: 'deep', label: '深度（3-5轮搜索）' },
]

// 页面挂载时加载任务列表和可用模型
async function loadData() {
  await taskStore.fetchTasks()
  try {
    const res = await getModels()
    models.value = res.models
  } catch {
    // 接口失败时使用默认模型，保证表单可用
    models.value = [{ id: 'deepseek', name: 'DeepSeek' }]
  }
}

onMounted(() => {
  loadData()
})

// 校验 URL 格式，要求以 http:// 或 https:// 开头并包含域名
function isValidUrl(url: string): boolean {
  return /^https?:\/\/.+\..+/.test(url.trim())
}

// 将输入框中的 URL 添加到网站列表，自动去重并校验格式
function addUrl() {
  const url = newUrl.value.trim()
  if (!url) return
  if (!isValidUrl(url)) return
  // 防止重复添加同一个 URL
  if (websiteForm.value.urls!.includes(url)) {
    newUrl.value = ''
    return
  }
  websiteForm.value.urls!.push(url)
  newUrl.value = ''
}

// 从网站列表中移除指定索引的 URL
function removeUrl(index: number) {
  websiteForm.value.urls!.splice(index, 1)
}

// 提交主题搜索调研：校验主题非空后创建任务，成功后跳转到调研详情页
async function handleSearchSubmit() {
  if (!searchForm.value.topic.trim()) return
  submitting.value = true
  try {
    const task = await taskStore.addTask(searchForm.value)
    // 重置表单并关闭表单面板
    searchForm.value.topic = ''
    searchForm.value.description = ''
    formType.value = null
    router.push(`/research/${task.id}`)
  } finally {
    submitting.value = false
  }
}

// 提交网站调研：校验 URL 列表非空后创建任务，主题由系统自动生成
async function handleWebsiteSubmit() {
  if (!websiteForm.value.urls?.length) return
  submitting.value = true
  try {
    // 自动生成调研主题：取前 3 个 URL 的域名
    const domains = websiteForm.value.urls.slice(0, 3).map(url => {
      try {
        return new URL(url).hostname
      } catch {
        return url.slice(0, 30)
      }
    })
    const autoTopic = domains.length > 2
      ? `${domains[0]}、${domains[1]} 等网站调研`
      : `${domains.join('、')} 网站调研`

    // 如果调研问题为空，使用默认值
    if (!websiteForm.value.questions?.trim()) {
      websiteForm.value.questions = '汇总这些页面，生成简报'
    }

    const task = await taskStore.addTask({
      ...websiteForm.value,
      topic: autoTopic,
      task_type: 'website',
    })
    // 重置网站调研表单到初始状态
    websiteForm.value.topic = ''
    websiteForm.value.questions = ''
    websiteForm.value.urls = []
    websiteForm.value.crawl_depth = 0
    websiteForm.value.max_pages = 20
    newUrl.value = ''
    formType.value = null
    router.push(`/research/${task.id}`)
  } finally {
    submitting.value = false
  }
}

// 根据任务状态跳转：已完成跳报告页，否则跳调研进度页
function goToTask(task: { id: number; status: string; task_type: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}

// 任务状态对应的图标，用于在历史列表中直观显示当前阶段
const statusIcons: Record<string, string> = {
  pending: '⏳',
  planning: '🤔',
  searching: '🔍',
  crawling: '🕷️',
  evaluating: '📊',
  writing: '✍️',
  completed: '✅',
  failed: '❌',
}

// 调研深度的中文标签，用于历史列表的元信息展示
const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

// 截断过长文本，用于在空间有限的列表项中显示
function truncate(text: string, len: number) {
  return text.length > len ? text.slice(0, len) + '...' : text
}

// 删除任务前弹出确认框，防止误操作
async function handleDelete(task: { id: number; topic: string }, event: Event) {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm(
      `确定删除「${truncate(task.topic, 20)}」？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await taskStore.removeTask(task.id)
  } catch {
    // 用户取消删除，无需处理
  }
}
</script>

<template>
  <div class="sidebar-inner">
    <!-- 顶部品牌标识 -->
    <div class="sidebar-brand">
      <span>AI 调研平台</span>
    </div>

    <div class="sidebar-divider" />

    <!-- 新建调研区域：按钮组 / 搜索表单 / 网站表单 -->
    <div class="sidebar-section">
      <!-- 未选择表单类型时显示两个入口按钮 -->
      <div v-if="!formType" class="btn-group">
        <button
          class="vp-btn vp-btn-primary"
          style="flex: 1"
          @click="formType = 'search'"
        >
          + 主题调研
        </button>
        <button
          class="vp-btn vp-btn-brand"
          style="flex: 1"
          @click="formType = 'website'"
        >
          + 网站调研
        </button>
      </div>

      <!-- 主题搜索调研表单 -->
      <div v-else-if="formType === 'search'" class="new-research-form">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
          <span style="font-size: 14px; font-weight: 600; color: var(--vp-c-text-1)">🔍 主题调研</span>
          <!-- 关闭表单回到按钮组 -->
          <button class="vp-btn vp-btn-text" style="padding: 4px 8px; font-size: 18px" @click="formType = null">&times;</button>
        </div>

        <!-- 调研主题输入，回车可直接提交 -->
        <div class="vp-form-item">
          <label class="vp-form-label">调研主题</label>
          <input v-model="searchForm.topic" class="vp-input" placeholder="例如：2024年中国新能源汽车市场分析" @keyup.enter="handleSearchSubmit" />
        </div>

        <!-- 补充说明，帮助 AI 更精准地聚焦调研方向 -->
        <div class="vp-form-item">
          <label class="vp-form-label">补充说明（可选）</label>
          <textarea v-model="searchForm.description" class="vp-input" rows="2" placeholder="重点关注比亚迪、特斯拉的市占率变化" />
        </div>

        <!-- 选择用于生成报告的 AI 模型 -->
        <div class="vp-form-item">
          <label class="vp-form-label">AI 模型</label>
          <select v-model="searchForm.model" class="vp-select">
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>

        <!-- 调研深度决定搜索轮数，深度越大结果越全面但耗时越长 -->
        <div class="vp-form-item">
          <label class="vp-form-label">调研深度</label>
          <select v-model="searchForm.depth" class="vp-select">
            <option v-for="d in depthOptions" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>

        <!-- 提交按钮，主题为空或正在提交时禁用 -->
        <button
          class="vp-btn vp-btn-primary"
          style="width: 100%"
          :disabled="submitting || !searchForm.topic.trim()"
          @click="handleSearchSubmit"
        >
          {{ submitting ? '提交中...' : '开始调研' }}
        </button>
      </div>

      <!-- 网站调研表单 -->
      <div v-else-if="formType === 'website'" class="new-research-form">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
          <span style="font-size: 14px; font-weight: 600; color: var(--vp-c-text-1)">🌐 网站调研</span>
          <!-- 关闭表单回到按钮组 -->
          <button class="vp-btn vp-btn-text" style="padding: 4px 8px; font-size: 18px" @click="formType = null">&times;</button>
        </div>

        <!-- URL 列表管理：展示已添加的 URL，支持逐个删除 -->
        <div class="vp-form-item">
          <label class="vp-form-label">网站列表</label>
          <div v-if="websiteForm.urls!.length" class="url-list">
            <div v-for="(url, i) in websiteForm.urls" :key="i" class="url-item">
              <span class="url-text" :title="url">{{ url }}</span>
              <button class="url-remove" @click="removeUrl(i)">&times;</button>
            </div>
          </div>
          <!-- URL 输入区：输入框 + 添加按钮，回车也可添加 -->
          <div style="display: flex; gap: 8px">
            <input
              v-model="newUrl"
              class="vp-input"
              style="flex: 1"
              placeholder="输入网站 URL，回车添加"
              @keyup.enter="addUrl"
            />
            <button
              class="vp-btn vp-btn-ghost"
              style="flex-shrink: 0; padding: 0 12px"
              :disabled="!newUrl.trim() || !isValidUrl(newUrl)"
              @click="addUrl"
            >
              添加
            </button>
          </div>
          <!-- URL 格式校验提示 -->
          <div v-if="newUrl.trim() && !isValidUrl(newUrl)" style="font-size: 12px; color: var(--vp-c-red); margin-top: 4px">
            请输入有效的 URL（以 http:// 或 https:// 开头）
          </div>
        </div>

        <!-- 调研问题：引导 AI 针对网站内容进行定向分析 -->
        <div class="vp-form-item">
          <label class="vp-form-label">调研问题</label>
          <textarea v-model="websiteForm.questions" class="vp-input" rows="3" placeholder="汇总这些页面，生成简报" />
        </div>

        <!-- 爬取深度：控制是否自动发现并爬取子页面 -->
        <div class="vp-form-item">
          <label class="vp-form-label">爬取深度</label>
          <select v-model="websiteForm.crawl_depth" class="vp-select">
            <option :value="0">仅输入的 URLs</option>
            <option :value="1">包含子页面（1 层）</option>
            <option :value="2">包含子页面（2 层）</option>
            <option :value="3">包含子页面（3 层）</option>
          </select>
          <div style="font-size: 12px; color: var(--vp-c-text-3); margin-top: 4px">
            {{ websiteForm.crawl_depth === 0 ? '只爬取输入的 URLs' : `自动发现并爬取同域名下的 ${websiteForm.crawl_depth} 层子页面` }}
          </div>
        </div>

        <!-- 最大页面数：仅当爬取深度 > 0 时显示，防止爬取过多页面 -->
        <div v-if="websiteForm.crawl_depth && websiteForm.crawl_depth > 0" class="vp-form-item">
          <label class="vp-form-label">最大页面数</label>
          <select v-model="websiteForm.max_pages" class="vp-select">
            <option :value="10">10 页</option>
            <option :value="20">20 页</option>
            <option :value="50">50 页</option>
            <option :value="100">100 页</option>
          </select>
          <div style="font-size: 12px; color: var(--vp-c-text-3); margin-top: 4px">
            限制爬取的总页面数，避免爬取过多
          </div>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">AI 模型</label>
          <select v-model="websiteForm.model" class="vp-select">
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>

        <!-- 提交按钮，URL 列表为空时禁用 -->
        <button
          class="vp-btn vp-btn-brand"
          style="width: 100%"
          :disabled="submitting || !websiteForm.urls?.length"
          @click="handleWebsiteSubmit"
        >
          {{ submitting ? '提交中...' : '开始调研' }}
        </button>
      </div>
    </div>

    <div class="sidebar-divider" />

    <!-- 历史调研列表区域，支持滚动 -->
    <div class="sidebar-section" style="flex: 1; overflow-y: auto; padding-bottom: 20px">
      <div class="sidebar-section-title">历史调研</div>

      <!-- 加载中状态 -->
      <div v-if="taskStore.loading" style="padding: 16px; text-align: center; color: var(--vp-c-text-3); font-size: 13px">
        加载中...
      </div>

      <!-- 空状态提示 -->
      <div v-else-if="taskStore.tasks.length === 0" style="padding: 16px; text-align: center; color: var(--vp-c-text-3); font-size: 13px">
        暂无历史记录
      </div>

      <!-- 任务列表 -->
      <div v-else>
        <div
          v-for="task in taskStore.tasks"
          :key="task.id"
          class="sidebar-task-item"
          :data-status="task.status"
          @click="goToTask(task)"
        >
          <div class="task-content">
            <!-- 任务标题：状态图标 + 截断后的主题 -->
            <div class="task-title">
              {{ statusIcons[task.status] || '' }} {{ truncate(task.topic, 28) }}
            </div>
            <!-- 任务元信息：类型标签、深度/层数、创建时间 -->
            <div class="task-meta">
              <span :class="['type-badge', task.task_type === 'website' ? 'type-website' : 'type-search']">
                {{ task.task_type === 'website' ? '网站' : '主题' }}
              </span>
              <span v-if="task.task_type === 'search'">{{ depthLabels[task.depth] || task.depth }}</span>
              <span v-if="task.task_type === 'website'">{{ task.crawl_depth }}层深度</span>
              <span>&middot;</span>
              <span>{{ new Date(task.created_at).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}</span>
            </div>
          </div>
          <!-- 删除按钮，hover 时才显示，点击触发确认弹窗 -->
          <button
            class="task-delete-btn"
            title="删除"
            @click="handleDelete(task, $event)"
          >
            &times;
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 侧边栏整体布局：纵向排列，撑满父容器高度 */
.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 新建调研的两个入口按钮组 */
.btn-group {
  display: flex;
  gap: 8px;
}

/* 调研表单卡片：独立背景和边框，与侧边栏区分层次 */
.new-research-form {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: var(--vp-radius);
  padding: 16px;
}

/* 已添加的 URL 列表容器 */
.url-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

/* 单个 URL 条目：圆角卡片样式 */
.url-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 12px;
}

/* URL 文本：超长时省略号截断 */
.url-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--vp-c-text-2);
}

/* URL 删除小按钮：紧凑尺寸，默认不占多余空间 */
.url-remove {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: none;
  background: transparent;
  color: var(--vp-c-text-3);
  font-size: 14px;
  cursor: pointer;
  border-radius: 3px;
  padding: 0;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* URL 删除按钮悬停：红色提示可删除 */
.url-remove:hover {
  color: var(--vp-c-red);
  background: var(--vp-c-bg-mute);
}

/* 历史任务列表项：水平排列，内容区与删除按钮 */
.sidebar-task-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 任务内容区：占据剩余空间，标题超长可截断 */
.task-content {
  flex: 1;
  min-width: 0;
}

/* 任务删除按钮：默认隐藏，悬停任务项时才显示 */
.task-delete-btn {
  display: none;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border: none;
  background: transparent;
  color: var(--vp-c-text-3);
  font-size: 16px;
  cursor: pointer;
  border-radius: 4px;
  padding: 0;
  line-height: 1;
}

/* 删除按钮悬停：红色警示 */
.task-delete-btn:hover {
  color: var(--vp-c-red);
  background: var(--vp-c-bg-mute);
}

/* 悬停任务项时显示删除按钮 */
.sidebar-task-item:hover .task-delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 任务元信息行：类型、深度、时间等辅助信息 */
.task-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--vp-c-text-3);
}

/* 调研类型徽章基础样式 */
.type-badge {
  display: inline-block;
  font-size: 10px;
  padding: 0 5px;
  border-radius: 3px;
  line-height: 18px;
  font-weight: 500;
}

/* 主题调研类型徽章：蓝色系 */
.type-search {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

/* 网站调研类型徽章：绿色系 */
.type-website {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}
</style>

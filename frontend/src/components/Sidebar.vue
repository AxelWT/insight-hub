<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'
import { getModels } from '../api/report'
import type { TaskCreateParams } from '../api/task'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const taskStore = useTaskStore()

const searchForm = ref<TaskCreateParams>({
  topic: '',
  description: '',
  model: 'deepseek',
  depth: 'standard',
})

const websiteForm = ref<TaskCreateParams>({
  topic: '',
  questions: '',
  model: 'deepseek',
  task_type: 'website',
  urls: [],
  crawl_depth: 1,
  max_pages: 20,
})

const newUrl = ref('')
const models = ref<{ id: string; name: string }[]>([])
const submitting = ref(false)
const formType = ref<'search' | 'website' | null>(null)

const depthOptions = [
  { value: 'quick', label: '快速（1轮搜索）' },
  { value: 'standard', label: '标准（2-3轮搜索）' },
  { value: 'deep', label: '深度（3-5轮搜索）' },
]

async function loadData() {
  await taskStore.fetchTasks()
  try {
    const res = await getModels()
    models.value = res.models
  } catch {
    models.value = [{ id: 'deepseek', name: 'DeepSeek' }]
  }
}

onMounted(() => {
  loadData()
})

function isValidUrl(url: string): boolean {
  return /^https?:\/\/.+\..+/.test(url.trim())
}

function addUrl() {
  const url = newUrl.value.trim()
  if (!url) return
  if (!isValidUrl(url)) return
  if (websiteForm.value.urls!.includes(url)) {
    newUrl.value = ''
    return
  }
  websiteForm.value.urls!.push(url)
  newUrl.value = ''
}

function removeUrl(index: number) {
  websiteForm.value.urls!.splice(index, 1)
}

async function handleSearchSubmit() {
  if (!searchForm.value.topic.trim()) return
  submitting.value = true
  try {
    const task = await taskStore.addTask(searchForm.value)
    searchForm.value.topic = ''
    searchForm.value.description = ''
    formType.value = null
    router.push(`/research/${task.id}`)
  } finally {
    submitting.value = false
  }
}

async function handleWebsiteSubmit() {
  if (!websiteForm.value.topic.trim()) return
  if (!websiteForm.value.urls?.length) return
  submitting.value = true
  try {
    const task = await taskStore.addTask({
      ...websiteForm.value,
      task_type: 'website',
    })
    websiteForm.value.topic = ''
    websiteForm.value.questions = ''
    websiteForm.value.urls = []
    websiteForm.value.crawl_depth = 1
    websiteForm.value.max_pages = 20
    newUrl.value = ''
    formType.value = null
    router.push(`/research/${task.id}`)
  } finally {
    submitting.value = false
  }
}

function goToTask(task: { id: number; status: string; task_type: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}

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

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

function truncate(text: string, len: number) {
  return text.length > len ? text.slice(0, len) + '...' : text
}

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
    // 用户取消
  }
}
</script>

<template>
  <div class="sidebar-inner">
    <!-- Brand -->
    <div class="sidebar-brand">
      <span>AI 调研平台</span>
    </div>

    <div class="sidebar-divider" />

    <!-- New Research Buttons -->
    <div class="sidebar-section">
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

      <!-- Search Research Form -->
      <div v-else-if="formType === 'search'" class="new-research-form">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
          <span style="font-size: 14px; font-weight: 600; color: var(--vp-c-text-1)">🔍 主题调研</span>
          <button class="vp-btn vp-btn-text" style="padding: 4px 8px; font-size: 18px" @click="formType = null">&times;</button>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">调研主题</label>
          <input v-model="searchForm.topic" class="vp-input" placeholder="例如：2024年中国新能源汽车市场分析" @keyup.enter="handleSearchSubmit" />
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">补充说明（可选）</label>
          <textarea v-model="searchForm.description" class="vp-input" rows="2" placeholder="重点关注比亚迪、特斯拉的市占率变化" />
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">AI 模型</label>
          <select v-model="searchForm.model" class="vp-select">
            <option v-for="m in models" :key="m.id" :value="m.id">{{ m.name }}</option>
          </select>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">调研深度</label>
          <select v-model="searchForm.depth" class="vp-select">
            <option v-for="d in depthOptions" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>

        <button
          class="vp-btn vp-btn-primary"
          style="width: 100%"
          :disabled="submitting || !searchForm.topic.trim()"
          @click="handleSearchSubmit"
        >
          {{ submitting ? '提交中...' : '开始调研' }}
        </button>
      </div>

      <!-- Website Research Form -->
      <div v-else-if="formType === 'website'" class="new-research-form">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px">
          <span style="font-size: 14px; font-weight: 600; color: var(--vp-c-text-1)">🌐 网站调研</span>
          <button class="vp-btn vp-btn-text" style="padding: 4px 8px; font-size: 18px" @click="formType = null">&times;</button>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">调研主题</label>
          <input v-model="websiteForm.topic" class="vp-input" placeholder="例如：竞品官网功能对比分析" />
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">网站列表</label>
          <div v-if="websiteForm.urls!.length" class="url-list">
            <div v-for="(url, i) in websiteForm.urls" :key="i" class="url-item">
              <span class="url-text" :title="url">{{ url }}</span>
              <button class="url-remove" @click="removeUrl(i)">&times;</button>
            </div>
          </div>
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
          <div v-if="newUrl.trim() && !isValidUrl(newUrl)" style="font-size: 12px; color: var(--vp-c-red); margin-top: 4px">
            请输入有效的 URL（以 http:// 或 https:// 开头）
          </div>
        </div>

        <div class="vp-form-item">
          <label class="vp-form-label">调研问题</label>
          <textarea v-model="websiteForm.questions" class="vp-input" rows="3" placeholder="输入你希望 AI 分析的问题&#10;每行一个问题，例如：&#10;这些网站的核心功能有哪些差异？&#10;定价策略有什么不同？" />
        </div>

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

        <button
          class="vp-btn vp-btn-brand"
          style="width: 100%"
          :disabled="submitting || !websiteForm.topic.trim() || !websiteForm.urls?.length"
          @click="handleWebsiteSubmit"
        >
          {{ submitting ? '提交中...' : '开始调研' }}
        </button>
      </div>
    </div>

    <div class="sidebar-divider" />

    <!-- History List -->
    <div class="sidebar-section" style="flex: 1; overflow-y: auto; padding-bottom: 20px">
      <div class="sidebar-section-title">历史调研</div>

      <div v-if="taskStore.loading" style="padding: 16px; text-align: center; color: var(--vp-c-text-3); font-size: 13px">
        加载中...
      </div>

      <div v-else-if="taskStore.tasks.length === 0" style="padding: 16px; text-align: center; color: var(--vp-c-text-3); font-size: 13px">
        暂无历史记录
      </div>

      <div v-else>
        <div
          v-for="task in taskStore.tasks"
          :key="task.id"
          class="sidebar-task-item"
          :data-status="task.status"
          @click="goToTask(task)"
        >
          <div class="task-content">
            <div class="task-title">
              {{ statusIcons[task.status] || '' }} {{ truncate(task.topic, 28) }}
            </div>
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
.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.btn-group {
  display: flex;
  gap: 8px;
}

.new-research-form {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: var(--vp-radius);
  padding: 16px;
}

.url-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
}

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

.url-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--vp-c-text-2);
}

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

.url-remove:hover {
  color: var(--vp-c-red);
  background: var(--vp-c-bg-mute);
}

.sidebar-task-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-content {
  flex: 1;
  min-width: 0;
}

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

.task-delete-btn:hover {
  color: var(--vp-c-red);
  background: var(--vp-c-bg-mute);
}

.sidebar-task-item:hover .task-delete-btn {
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--vp-c-text-3);
}

.type-badge {
  display: inline-block;
  font-size: 10px;
  padding: 0 5px;
  border-radius: 3px;
  line-height: 18px;
  font-weight: 500;
}

.type-search {
  background: rgba(59, 130, 246, 0.12);
  color: #3b82f6;
}

.type-website {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}
</style>

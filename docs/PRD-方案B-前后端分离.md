# PRD：AI 调研平台 - 方案 B（前后端分离）

## 1. 产品概述

### 1.1 产品定位
个人使用的 AI 驱动调研工具，采用前后端分离架构，提供流畅的单页应用体验。后端提供 REST API + WebSocket 实时推送，前端为 Vue 3 SPA。

### 1.2 目标用户
个人用户 / 小团队，追求更好的 UI 交互体验和实时反馈。

### 1.3 核心价值
- 同方案 A 的核心价值
- 额外优势：实时 WebSocket 进度推送、更流畅的 SPA 交互体验

---

## 2. 功能需求

### 2.1 调研任务管理

#### 创建调研
- 输入调研主题（必填）
- 可选补充说明
- 选择 AI 模型（下拉选择）
- 高级选项（可选）：
  - 搜索结果数量（默认 15）
  - 最大爬取页面数（默认 10）
  - 目标网站限制（可选，如只搜索特定域名）
- 点击"开始调研"

#### 任务状态（实时更新）
- **搜索中**：WebSocket 实时推送搜索到的每条结果
- **爬取中**：显示爬取进度和每页状态
- **分析中**：显示 AI 正在处理的阶段
- **已完成**：自动跳转到报告页

#### 任务管理面板
- 左侧边栏：历史任务列表（可搜索、筛选）
- 支持按状态筛选（全部 / 进行中 / 已完成 / 失败）
- 任务卡片显示：标题、状态徽章、创建时间、模型标签

### 2.2 信息搜索与爬取

#### 搜索策略
- 使用 Tavily Search API
- 支持指定搜索范围：
  - 全网搜索（默认）
  - 指定网站列表（如只搜索 techcrunch.com, 36kr.com）
- 搜索结果实时推送到前端

#### 网页爬取
- Tavily Extract API 提取正文
- httpx + BeautifulSoup4 作为回退
- 爬取状态实时显示（每个 URL 的状态：等待中 / 爬取中 / 成功 / 失败）
- 自动去重、超时控制

### 2.3 AI 报告生成

#### 报告结构
同方案 A，额外增加：
- AI 生成过程中的"思考步骤"展示
- 每个章节标注信息来源

#### 多模型支持
- 使用 litellm 统一接口
- 模型选择下拉框，显示模型名称 + 预估成本
- 支持 OpenAI GPT-4o / GPT-4o-mini
- 支持 Anthropic Claude Sonnet 4 / Haiku 4.5
- 模型列表可通过配置文件扩展

### 2.4 报告展示

#### 页面展示
- 三栏布局：左侧目录 → 中间报告 → 右侧信息面板
- 目录导航跟随滚动高亮
- Markdown 渲染支持：表格、代码块、数学公式、流程图
- 参考来源卡片（可展开查看原文摘要）
- 阅读进度条

#### 报告操作
- 复制 Markdown 原文
- 导出 .md 文件
- 导出 PDF（前端生成）
- 删除报告
- 基于当前报告"继续深入调研"（追加搜索）

---

## 3. 技术架构

### 3.1 整体架构
```
┌────────────────────────┐     ┌─────────────────────────┐
│     Vue 3 SPA           │     │      FastAPI 后端         │
│  ┌──────────────────┐  │     │  ┌──────────────────┐   │
│  │ Vue Router        │  │     │  │ REST API Router   │   │
│  │ Pinia Store       │◄─┼─HTTP┼─►│ (research/report) │   │
│  │ Element Plus UI   │  │     │  └──────────────────┘   │
│  └──────────────────┘  │     │  ┌──────────────────┐   │
│  ┌──────────────────┐  │     │  │ WebSocket Server  │   │
│  │ WebSocket Client  │◄─┼─WS──►│ (进度推送)         │   │
│  └──────────────────┘  │     │  └──────────────────┘   │
│  ┌──────────────────┐  │     │  ┌──────────────────┐   │
│  │ Markdown 渲染     │  │     │  │ 服务层            │   │
│  │ markdown-it       │  │     │  │ search/crawl/ai   │   │
│  └──────────────────┘  │     │  └──────────────────┘   │
└────────────────────────┘     │  ┌──────────────────┐   │
                               │  │ SQLite + ORM      │   │
                               │  └──────────────────┘   │
                               └─────────────────────────┘
```

### 3.2 技术栈

**后端：**
| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | FastAPI | 高性能异步框架 |
| ASGI 服务器 | Uvicorn | - |
| ORM | SQLAlchemy 2.0 | 异步 ORM |
| 数据验证 | Pydantic v2 | 请求/响应模型 |
| WebSocket | FastAPI 内置 | 实时进度推送 |
| 搜索 API | Tavily | 搜索 + 提取 |
| 爬虫 | httpx + BeautifulSoup4 | - |
| AI 代理 | litellm | 多模型支持 |
| 数据库 | SQLite | - |
| CORS | fastapi.middleware | 跨域支持 |

**前端：**
| 组件 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3 + TypeScript | SPA |
| 构建 | Vite | 快速开发构建 |
| UI 库 | Element Plus | Vue 3 组件库 |
| 状态管理 | Pinia | Vue 3 状态管理 |
| 路由 | Vue Router 4 | SPA 路由 |
| HTTP | Axios | API 请求 |
| Markdown | markdown-it + highlight.js | 报告渲染 |
| 目录 | markdown-it-toc | 自动生成 TOC |
| PDF | html2pdf.js | 前端 PDF 导出 |

### 3.3 项目结构
```
my-project-2/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 入口 + CORS + WebSocket
│   │   ├── config.py               # 配置管理
│   │   ├── database.py             # 数据库连接
│   │   ├── models.py               # SQLAlchemy 模型
│   │   ├── schemas.py              # Pydantic Schema
│   │   ├── routers/
│   │   │   ├── research.py         # 调研任务 REST API
│   │   │   ├── report.py           # 报告 REST API
│   │   │   └── ws.py               # WebSocket 端点
│   │   └── services/
│   │       ├── search.py           # 搜索服务
│   │       ├── crawler.py          # 爬虫服务
│   │       ├── ai.py               # AI 服务
│   │       └── orchestrator.py     # 工作流编排
│   ├── reports/                    # 生成的报告文件
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.vue                 # 根组件
│   │   ├── main.ts                 # 入口
│   │   ├── router/
│   │   │   └── index.ts            # Vue Router 配置
│   │   ├── stores/
│   │   │   ├── research.ts         # 调研状态
│   │   │   └── websocket.ts        # WebSocket 连接管理
│   │   ├── api/
│   │   │   └── index.ts            # Axios API 封装
│   │   ├── views/
│   │   │   ├── HomeView.vue        # 首页
│   │   │   ├── ResearchView.vue    # 调研进度页
│   │   │   └── ReportView.vue      # 报告展示页
│   │   ├── components/
│   │   │   ├── ResearchForm.vue    # 调研输入表单
│   │   │   ├── TaskList.vue        # 任务列表
│   │   │   ├── TaskCard.vue        # 任务卡片
│   │   │   ├── ProgressPanel.vue   # 进度面板
│   │   │   ├── MarkdownViewer.vue  # Markdown 渲染
│   │   │   ├── TocNav.vue          # 目录导航
│   │   │   └── SourceCard.vue      # 来源卡片
│   │   ├── composables/
│   │   │   ├── useWebSocket.ts     # WebSocket Hook
│   │   │   └── useMarkdown.ts      # Markdown 渲染 Hook
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript 类型定义
│   │   └── utils/
│   │       └── format.ts           # 格式化工具
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
└── docs/
```

---

## 4. API 设计

### 4.1 REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/research | 创建调研任务 |
| GET | /api/research | 获取任务列表 |
| GET | /api/research/{id} | 获取任务详情 |
| DELETE | /api/research/{id} | 删除任务 |
| GET | /api/research/{id}/sources | 获取任务的信息来源 |
| GET | /api/report/{task_id} | 获取报告内容 |
| GET | /api/report/{task_id}/export | 导出报告文件 |
| GET | /api/models | 获取可用模型列表 |

### 4.2 WebSocket

```
ws://localhost:8000/ws/research/{task_id}

# 服务端推送消息格式
{
  "type": "status_update",
  "data": {
    "status": "searching",
    "progress": 30,
    "message": "正在搜索第 5/15 条结果..."
  }
}

{
  "type": "source_found",
  "data": {
    "url": "https://...",
    "title": "...",
    "snippet": "..."
  }
}

{
  "type": "crawl_progress",
  "data": {
    "current": 3,
    "total": 10,
    "url": "https://...",
    "status": "success"
  }
}

{
  "type": "completed",
  "data": {
    "report_id": 1
  }
}
```

---

## 5. 数据模型

同方案 A，额外字段：

### ResearchTask 扩展
| 字段 | 类型 | 说明 |
|------|------|------|
| ... | ... | 同方案 A |
| max_results | Integer | 最大搜索结果数（默认 15） |
| max_pages | Integer | 最大爬取页数（默认 10） |
| target_sites | JSON | 指定搜索网站列表（可空） |

---

## 6. 页面设计

### 6.1 首页 (HomeView)
- 顶部导航栏：Logo + 历史记录入口
- 中央大卡片：调研输入表单
  - 主题输入（大文本框）
  - 高级选项折叠面板
- 底部：最近调研记录卡片

### 6.2 调研进度页 (ResearchView)
- 顶部：任务标题 + 状态标签
- 左侧：进度时间线
  - 搜索阶段：已找到 X 条结果
  - 爬取阶段：进度条 + URL 列表
  - 分析阶段：AI 处理中动画
- 右侧：实时搜索结果预览卡片

### 6.3 报告展示页 (ReportView)
- 三栏布局
- 左栏：目录导航（TOC），跟随滚动高亮
- 中间栏：Markdown 渲染的报告正文
- 右栏：元信息面板（模型、来源数、字数）
- 顶部工具栏：复制、下载 MD、导出 PDF、继续调研

---

## 7. 核心流程

### 7.1 调研流程
```
1. 用户提交 → POST /api/research → 创建任务
2. 后端异步启动调研流程
3. 通过 WebSocket 推送实时进度：
   a. searching → 推送每条搜索结果
   b. crawling → 推送每个页面爬取状态
   c. analyzing → 推送 AI 处理阶段
   d. completed → 推送报告 ID
4. 前端接收 WebSocket 消息更新 UI
5. 完成后 Vue Router 自动跳转报告页
```

### 7.2 WebSocket 生命周期
```
前端                          后端
  │                            │
  ├── CONNECT ─────────────────►│
  │                            │
  │◄── status_update ──────────┤  (搜索开始)
  │◄── source_found ───────────┤  (每条搜索结果)
  │◄── source_found ───────────┤
  │◄── status_update ──────────┤  (爬取开始)
  │◄── crawl_progress ─────────┤  (每个页面)
  │◄── crawl_progress ─────────┤
  │◄── status_update ──────────┤  (分析开始)
  │◄── completed ──────────────┤  (完成)
  │                            │
  ├── CLOSE ───────────────────►│
```

---

## 8. 配置管理

### 环境变量
```env
# 后端
TAVILY_API_KEY=tvly-xxxxx
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx
DEFAULT_MODEL=openai/gpt-4o
MAX_SEARCH_RESULTS=15
MAX_CRAWL_PAGES=10
CRAWL_TIMEOUT=10
REPORT_OUTPUT_DIR=./reports
DATABASE_URL=sqlite:///./research.db
CORS_ORIGINS=http://localhost:5173

# 前端（.env）
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

---

## 9. 错误处理

| 场景 | 后端处理 | 前端展示 |
|------|---------|---------|
| 搜索 API 超时 | 重试 2 次 | WebSocket 推送警告 |
| 网页爬取失败 | 跳过，记录错误 | 进度条标红该条目 |
| AI 生成失败 | 重试 1 次 | 显示错误提示 |
| WebSocket 断开 | - | 自动重连 + 轮询降级 |
| 无搜索结果 | 返回空结果 | 显示空状态插画 |

---

## 10. 部署

### 10.1 开发环境
```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev  # 默认 5173 端口
```

### 10.2 生产部署
```bash
# 前端构建
cd frontend && npm run build

# 后端服务静态文件
# FastAPI 挂载 frontend/dist 为静态目录
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 10.3 Docker Compose
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./reports:/app/reports
```

---

## 11. 开发计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| P0 | 项目搭建（前后端脚手架 + 配置） | 0.5 天 |
| P1 | 后端 API + WebSocket + 服务层 | 1.5 天 |
| P2 | 前端 SPA 页面 + 组件 | 2 天 |
| P3 | 前后端联调 + WebSocket 集成 | 1 天 |
| P4 | 测试 + 修复 + 打磨 | 1 天 |
| **总计** | | **6 天** |

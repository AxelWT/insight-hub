# Vue 3 前端迁移设计文档

## Context

当前项目 "AI 调研平台" 使用 Streamlit 作为前端框架。Streamlit 存在以下限制：
- UI 定制能力有限，难以实现专业级交互体验
- 前后端耦合，无法独立部署和开发
- 实时状态更新依赖轮询，体验不佳
- 团队技术栈偏向 Vue 生态

本设计将前端完全替换为 Vue 3 + FastAPI 架构，实现前后端分离、WebSocket 实时推送、以及更好的用户体验。

## 技术选型

| 层 | 技术 | 说明 |
|---|---|---|
| 前端框架 | Vue 3 + TypeScript | Composition API |
| 构建工具 | Vite | 快速 HMR，开发体验好 |
| 状态管理 | Pinia | Vue 3 官方推荐 |
| 路由 | Vue Router | SPA 路由 |
| UI 组件库 | Element Plus | 成熟稳定，组件丰富 |
| HTTP 客户端 | axios | 请求拦截、错误处理 |
| 后端框架 | FastAPI | 异步、自带 OpenAPI 文档 |
| 实时通信 | WebSocket | 全双工，实时推送 Agent 状态 |
| 数据库 | SQLite + SQLAlchemy | 保持不变 |

## 项目结构

```
insight-hub/
├── frontend/                  # Vue 3 SPA
│   ├── src/
│   │   ├── api/               # API 请求封装
│   │   │   ├── request.ts     # axios 实例（baseURL、拦截器）
│   │   │   ├── task.ts        # 任务 API：list、create、get、delete
│   │   │   └── report.ts      # 报告 API：get、sources、logs
│   │   ├── stores/            # Pinia 状态管理
│   │   │   ├── task.ts        # 任务状态：列表、当前任务、CRUD 操作
│   │   │   └── websocket.ts   # WebSocket 连接管理、消息分发
│   │   ├── views/             # 页面组件
│   │   │   ├── HomeView.vue   # 首页：任务列表 + 侧边栏
│   │   │   ├── ResearchView.vue  # 调研进度：实时 Agent 时间线
│   │   │   └── ReportView.vue    # 报告详情：内容/来源/日志 Tab
│   │   ├── components/        # 通用组件
│   │   │   ├── Sidebar.vue    # 侧边栏：新建调研表单 + 历史列表
│   │   │   ├── AgentTimeline.vue  # Agent 时间线（el-timeline）
│   │   │   └── ReportToc.vue  # 报告目录
│   │   ├── router/
│   │   │   └── index.ts       # 路由：/ /research/:id /report/:id
│   │   ├── App.vue            # 根组件：el-container 布局
│   │   └── main.ts            # 入口：注册 Element Plus、Pinia、Router
│   ├── index.html
│   ├── vite.config.ts         # 代理配置：/api → localhost:8000
│   ├── tsconfig.json
│   └── package.json
├── backend/                   # FastAPI 后端
│   ├── api/                   # API 路由
│   │   ├── __init__.py
│   │   ├── tasks.py           # 任务 CRUD：GET/POST/DELETE /api/tasks
│   │   ├── reports.py         # 报告接口：GET /api/tasks/{id}/report
│   │   └── websocket.py       # WebSocket：WS /api/ws/tasks/{id}
│   ├── core/                  # 核心业务（从 app/ 迁移，代码不变）
│   │   ├── agents/            # Agent 定义
│   │   ├── graph/             # LangGraph 工作流
│   │   ├── services/          # 外部服务（AI、搜索、爬虫、报告）
│   │   ├── models.py          # SQLAlchemy 数据模型
│   │   ├── database.py        # 数据库配置
│   │   └── config.py          # 应用配置
│   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── task.py            # TaskCreate、TaskResponse、TaskListResponse
│   │   └── report.py          # ReportResponse、SourceResponse、AgentLogResponse
│   ├── main.py                # FastAPI 入口：CORS、路由注册、启动事件
│   └── requirements.txt       # Python 依赖（移除 streamlit，新增 fastapi/uvicorn/websockets）
├── .env
├── .env.example
└── README.md
```

## API 设计

### REST 接口

#### `GET /api/tasks`
返回任务列表，按创建时间倒序。

响应：
```json
{
  "tasks": [
    {
      "id": 1,
      "topic": "2024年中国新能源汽车市场分析",
      "status": "completed",
      "progress": 100,
      "depth": "standard",
      "model": "deepseek",
      "created_at": "2026-05-27T20:00:00",
      "completed_at": "2026-05-27T20:05:00"
    }
  ]
}
```

#### `POST /api/tasks`
创建调研任务并启动后台执行。

请求体：
```json
{
  "topic": "调研主题",
  "description": "补充说明（可选）",
  "model": "deepseek",
  "depth": "standard"
}
```

响应：返回创建的任务对象（status 为 "pending"）。

#### `GET /api/tasks/{id}`
返回任务详情，包含报告摘要（如有）。

#### `DELETE /api/tasks/{id}`
删除任务及其关联数据（来源、日志、报告）。

#### `GET /api/tasks/{id}/report`
返回报告内容、来源列表、Agent 日志。

#### `GET /api/config/models`
返回可用模型列表（从 Settings.available_models 读取）。

### WebSocket 协议

`WS /api/ws/tasks/{id}`

服务端推送消息格式：
```json
{
  "type": "status_update" | "progress_update" | "agent_log" | "error",
  "data": { ... }
}
```

消息类型：
- `status_update`: 任务状态变更（planning, searching, evaluating, writing, completed, failed）
- `progress_update`: 进度百分比更新
- `agent_log`: 新 Agent 日志（agent_name, step, decision, output）
- `error`: 错误信息

## 前端页面设计

### 首页 (`/`)
- 左侧 `el-aside` 侧边栏：
  - 新建调研表单（`el-form`）：主题输入、补充说明、模型下拉、深度选择
  - 历史任务列表（`el-menu` 或卡片）
- 右侧主区域：
  - 标题 + 使用说明
  - 最近调研列表（`el-table` 或 `el-card`），点击跳转到对应页面

### 调研进度页 (`/research/:id`)
- 任务信息栏：主题、模型、深度、创建时间
- `el-progress` 进度条
- `el-timeline` Agent 执行时间线（实时更新）
  - 每个节点：图标 + 步骤描述 + 决策 + 输出
  - 已完成节点展开显示详情
  - 未完成节点显示等待状态
- WebSocket 连接：进入页面时连接，离开时断开

### 报告详情页 (`/report/:id`)
- 统计指标行：`el-statistic`（字数、来源数、搜索轮次、深度）
- `el-tabs` 三个标签页：
  - 报告内容：左侧目录 + 右侧 Markdown 渲染
  - 来源列表：按搜索轮次分组，`el-collapse` 展开详情
  - Agent 日志：`el-timeline` 展示完整决策过程
- 操作按钮：下载 Markdown、复制到剪贴板、继续深入调研

## 实施步骤

### 第一阶段：后端 API 层（5 步）

1. **创建 FastAPI 入口** — `backend/main.py`，配置 CORS、路由注册
2. **定义 Pydantic 模型** — `backend/schemas/`，请求/响应数据结构
3. **实现 REST 路由** — `backend/api/tasks.py`、`backend/api/reports.py`
4. **实现 WebSocket** — `backend/api/websocket.py`，连接管理和消息广播
5. **重构任务执行** — 将 `_run_research_stream` 提取到 `backend/core/`，用 asyncio 包装，执行中推送 WebSocket 消息

### 第二阶段：前端 Vue 3 项目（7 步）

6. **初始化项目** — Vite + Vue 3 + TypeScript，安装依赖
7. **配置 Vite** — API 代理、WebSocket 代理
8. **实现 API 层** — axios 实例、任务 API、报告 API
9. **实现 Pinia Store** — 任务状态、WebSocket 连接管理
10. **实现页面组件** — HomeView、ResearchView、ReportView
11. **实现通用组件** — Sidebar、AgentTimeline、ReportToc
12. **路由和布局** — Vue Router 配置、App.vue 布局

### 第三阶段：清理整合（3 步）

13. **删除 Streamlit 代码** — 移除 `app/ui/`、`app/main.py`
14. **重组目录** — `app/` 业务逻辑迁移到 `backend/core/`
15. **更新文档** — README.md、.env.example、requirements.txt

## 验证方案

1. **后端 API**：启动 FastAPI，访问 `/docs` Swagger 文档，测试所有接口
2. **前端功能**：启动 Vite dev server，测试创建任务、实时进度、报告查看
3. **端到端**：创建"快速"深度任务，验证 WebSocket 实时推送、报告生成、历史列表

## 风险和注意事项

- **LangGraph 同步执行**：LangGraph 的 `stream()` 是同步的，需要用 `asyncio.to_thread()` 包装以避免阻塞 FastAPI 事件循环
- **WebSocket 连接管理**：需要处理客户端断开重连、多客户端同时连接的场景
- **数据库并发**：SQLite 在并发写入时有限制，后台任务和 API 请求可能竞争，需使用 WAL 模式或连接池
- **静态文件部署**：生产环境需要配置 nginx 或 FastAPI 的 `StaticFiles` 来 serve Vue 构建产物

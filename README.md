# AI 调研平台 (Insight Hub)

一个基于多 Agent 协作的自动化调研系统，能够自动搜索、分析、整理信息并生成结构化调研报告。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus + TypeScript
- **后端**: FastAPI + WebSocket
- **工作流引擎**: LangGraph
- **LLM 框架**: LangChain + LiteLLM
- **搜索 API**: Tavily
- **网页爬取**: Crawl4AI + Playwright
- **数据库**: SQLite + SQLAlchemy + Alembic

## 🚀 快速开始

### 方式一：Docker 启动（推荐）

#### 前置要求
- Docker Desktop 4.0+
- Docker Compose v2

#### 启动步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd insight-hub

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 API Key

# 3. 一键启动
./docker-start.sh
```

#### Docker 常用命令

```bash
./docker-start.sh           # 启动服务
./docker-start.sh stop      # 停止服务
./docker-start.sh restart   # 重启服务
./docker-start.sh logs      # 查看日志
./docker-start.sh status    # 查看状态
./docker-start.sh build     # 重新构建镜像
```

---

### 方式二：终端启动

#### 前置要求
- Python 3.10+
- Node.js 18+
- npm 或 pnpm

#### 启动步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd insight-hub

# 2. 一键启动（自动检测并安装依赖）
./start.sh
```

首次运行会自动：
- 创建 `.env` 配置文件
- 安装后端 Python 依赖
- 安装 Playwright 浏览器
- 安装前端 npm 依赖

#### 手动启动（分开启动）

```bash
# 启动后端
cd backend
python -m uvicorn main:app --reload --port 8000

# 新终端，启动前端
cd frontend
npm run dev
```

---

## 🔧 环境配置

复制项目根目录的 `.env.example` 为 `.env`，填写以下配置：

```bash
cp .env.example .env
vim .env  # 编辑配置文件
```

需要配置的内容：

```bash
# 必需配置
TAVILY_API_KEY=tvly-xxx           # Tavily 搜索 API Key
DEEPSEEK_API_KEY=sk-xxx           # DeepSeek API Key

# 可选配置（使用自定义模型）
CUSTOM_BASE_URL=https://xxx       # 自定义模型 API 地址
CUSTOM_API_KEY=sk-xxx             # 自定义模型 API Key
CUSTOM_MODEL_NAME=gpt-4           # 自定义模型名称
```

#### 获取 API Key

| 服务 | 获取地址 | 说明 |
|------|----------|------|
| Tavily | https://tavily.com | 搜索 API，有免费额度 |
| DeepSeek | https://platform.deepseek.com | 国产大模型，性价比高 |

---

## 📁 项目结构

```
insight-hub/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API 请求封装
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面组件
│   │   └── components/    # 通用组件
│   ├── Dockerfile         # 前端 Docker 镜像
│   └── nginx.conf         # Nginx 配置
│
├── backend/               # FastAPI 后端
│   ├── api/               # REST + WebSocket 路由
│   ├── core/              # 业务逻辑
│   │   ├── agents/        # AI Agent 定义
│   │   ├── graph/         # LangGraph 工作流
│   │   └── services/      # 外部服务封装
│   ├── schemas/           # Pydantic 数据模型
│   ├── alembic/           # 数据库迁移
│   ├── data/              # SQLite 数据库
│   ├── logs/              # 应用日志
│   ├── main.py            # FastAPI 入口
│   └── Dockerfile         # 后端 Docker 镜像
│
├── docker-compose.yml     # Docker 编排配置
├── start.sh               # 终端启动脚本（自动安装依赖）
└── docker-start.sh        # Docker 启动脚本
```

---

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:5173 (终端) / http://localhost:80 (Docker) | Vue 前端 |
| 后端 API | http://localhost:8000 | FastAPI 后端 |
| API 文档 | http://localhost:8000/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 服务状态 |

---

## 📊 核心功能

### 调研模式

#### 1. 主题调研
采用 LangGraph 构建有向无环图 (DAG) 工作流：

```
START → Supervisor → Searcher → Crawler → Evaluator
                                          ↓
                              (条件路由) ──→ Searcher (补充搜索)
                                          ↓
                                        Writer → END
```

#### 2. 网站调研
针对指定网站进行深度爬取和分析：

```
START → Website Crawler → Website Writer → END
```

### Agent 职责

| Agent | 职责 |
|-------|------|
| **Supervisor** | 调研主管，分析主题，制定搜索策略 |
| **Searcher** | 搜索执行者，调用 Tavily API |
| **Crawler** | 网页爬取者，抓取完整网页内容 |
| **Evaluator** | 信息评估者，决定是否需要补充搜索 |
| **Writer** | 报告撰写者，生成结构化报告 |

---

## 🗄️ 数据库管理

使用 Alembic 管理数据库迁移：

```bash
cd backend

# 生成新迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history
```

---

## 📝 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tasks` | 任务列表 |
| `POST` | `/api/tasks` | 创建任务 |
| `GET` | `/api/tasks/{id}` | 任务详情 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 |
| `GET` | `/api/tasks/{id}/report` | 获取报告 |
| `GET` | `/api/tasks/{id}/sources` | 获取来源列表 |
| `GET` | `/api/config/models` | 获取可用模型 |
| `WS` | `/api/ws/tasks/{id}` | 实时状态推送 |

---

## ❓ 常见问题

### Q: Playwright 安装失败？
```bash
# macOS
brew install chromium

# 或手动安装
playwright install chromium --with-deps
```

### Q: 数据库在哪里？
- 本地启动: `backend/data/insight_hub.db`
- Docker: 挂载在 `backend/data/` 目录

### Q: 如何查看日志？
- 本地启动: `backend/logs/app.log`
- Docker: `./docker-start.sh logs`

### Q: 如何重置数据库？
```bash
# 删除数据库文件
rm backend/data/insight_hub.db

# 重新运行迁移
cd backend && alembic upgrade head
```

---

## 📄 License

MIT License

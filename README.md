# AI 调研平台

一个基于多 Agent 协作的自动化调研系统，能够自动搜索、分析、整理信息并生成结构化调研报告。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus + TypeScript
- **后端**: FastAPI + WebSocket
- **工作流引擎**: LangGraph
- **LLM 框架**: LangChain + LiteLLM
- **搜索 API**: Tavily
- **数据库**: MySQL + SQLAlchemy

## 项目结构

```
insight-hub/
├── frontend/              # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API 请求封装
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   └── router/        # Vue Router
│   └── vite.config.ts
├── backend/               # FastAPI 后端
│   ├── api/               # REST + WebSocket 路由
│   ├── core/              # 业务逻辑（Agent、工作流、服务）
│   │   ├── agents/        # AI Agent 定义
│   │   ├── graph/         # LangGraph 工作流
│   │   └── services/      # 外部服务封装
│   ├── schemas/           # Pydantic 数据模型
│   └── main.py            # FastAPI 入口
├── app/                   # (已废弃，业务代码已迁移到 backend/)
├── docs/                  # 文档
└── .env
```

## 快速开始

### 1. 安装 MySQL 数据库

**macOS（使用 Homebrew）**:
```bash
# 安装 MySQL
brew install mysql

# 启动 MySQL 服务
brew services start mysql

# 安全设置（设置 root 密码等）
mysql_secure_installation
```

**创建数据库**:
```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE insight_hub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（可选，也可以使用 root）
CREATE USER 'insight_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON insight_hub.* TO 'insight_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

需要配置的 Key：
- `TAVILY_API_KEY` - Tavily 搜索 API (必需)
- `DEEPSEEK_API_KEY` / `CUSTOM_API_KEY` - 至少一个 LLM API Key
- `DATABASE_URL` - MySQL 连接字符串（格式：`mysql+pymysql://user:password@localhost:3306/insight_hub`）

### 4. 启动后端

```bash
uvicorn backend.main:app --reload --port 8000
```

API 文档访问 http://localhost:8000/docs

### 5. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端访问 http://localhost:5173

## 核心原理

### 多 Agent 协作流程

系统采用 **LangGraph** 构建有向无环图 (DAG) 工作流，包含 5 个协作 Agent：

```
START → Supervisor → Searcher → Crawler → Evaluator
                                          ↓
                              (条件路由) ──→ Searcher (补充搜索)
                                          ↓
                                        Writer → END
```

### Agent 职责

| Agent | 职责 | 核心能力 |
|-------|------|----------|
| **Supervisor** | 调研主管 | 分析主题，拆解为多个搜索关键词，制定搜索策略 |
| **Searcher** | 搜索执行者 | 调用 Tavily API 执行搜索，收集搜索结果 |
| **Crawler** | 网页爬取者 | 抓取搜索结果的完整网页内容 |
| **Evaluator** | 信息评估者 | 评估信息覆盖度、深度、多样性，决定是否需要补充搜索 |
| **Writer** | 报告撰写者 | 基于收集的材料生成结构化调研报告 |

### 调研深度

| 深度 | 最大搜索轮次 | 预期来源数 | 适用场景 |
|------|-------------|-----------|----------|
| 快速 (quick) | 1 轮 | 5-8 个 | 快速了解概览 |
| 标准 (standard) | 3 轮 | 10-15 个 | 常规调研 |
| 深度 (deep) | 5 轮 | 15-25 个 | 深入研究 |

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/tasks` | 任务列表 |
| `POST` | `/api/tasks` | 创建任务（自动启动调研） |
| `GET` | `/api/tasks/{id}` | 任务详情 |
| `DELETE` | `/api/tasks/{id}` | 删除任务 |
| `GET` | `/api/tasks/{id}/report` | 获取报告 |
| `GET` | `/api/tasks/{id}/sources` | 获取来源列表 |
| `GET` | `/api/tasks/{id}/logs` | 获取 Agent 日志 |
| `GET` | `/api/config/models` | 获取可用模型列表 |
| `WS`  | `/api/ws/tasks/{id}` | 实时状态推送 |

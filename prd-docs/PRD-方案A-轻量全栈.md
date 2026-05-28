# PRD：AI 调研平台 - 方案 A（轻量全栈）

## 1. 产品概述

### 1.1 产品定位
个人使用的 AI 驱动调研工具，用户输入一个调研主题，系统自动搜索互联网、爬取网页内容、AI 整理汇总，最终生成结构化的 Markdown 调研报告并在 Web 页面展示。

### 1.2 目标用户
个人用户 / 小团队，需要快速了解某个领域的全貌。

### 1.3 核心价值
- 从"手动搜索数十个网页 + 整理笔记"到"输入主题 → 获取报告"，节省 80% 的调研时间
- AI 自动提炼关键信息、交叉验证、结构化输出

---

## 2. 功能需求

### 2.1 调研任务管理

#### 创建调研
- 输入调研主题（必填，如 "2024 年中国新能源汽车市场分析"）
- 可选补充说明（如 "重点关注比亚迪、特斯拉的市占率变化"）
- 选择 AI 模型（OpenAI GPT-4o / Claude Sonnet / 其他）
- 点击"开始调研"

#### 任务状态
- **搜索中**：正在通过 Tavily API 搜索相关网页
- **爬取中**：正在爬取和解析网页正文（显示进度 x/10）
- **分析中**：AI 正在分析材料并生成报告
- **已完成**：报告已生成，可查看

#### 任务列表
- 显示所有历史调研任务
- 按时间倒序排列
- 显示标题、创建时间、状态、所用模型

### 2.2 信息搜索与爬取

#### 搜索策略
- 默认搜索 10-20 条相关结果
- 使用 Tavily Search API 获取搜索结果摘要
- 对每条结果评估相关性，筛选 top 10 进行深度爬取

#### 网页爬取
- 使用 Tavily Extract API 提取网页正文
- 回退方案：httpx + BeautifulSoup4 自行提取
- 提取标题、正文、发布时间、来源 URL
- 自动去重（基于 URL 去重）
- 超时控制（单页 10 秒）

### 2.3 AI 报告生成

#### 报告结构
```markdown
# {调研主题}

## 摘要
一段话概述核心发现

## 一、背景介绍
主题的背景和上下文

## 二、核心发现
### 2.1 发现一
### 2.2 发现二
...

## 三、数据与趋势
关键数据和趋势分析

## 四、不同观点
各方的不同看法和立场

## 五、总结与展望
总结性观点和未来趋势

## 参考来源
- [来源标题](URL)
- [来源标题](URL)
...
```

#### 多模型支持
- 使用 litellm 统一接口
- 支持的模型列表可配置
- 用户创建任务时选择模型
- 报告中标注所使用的模型

### 2.4 报告展示

#### 页面展示
- Markdown 渲染为格式化的 HTML 页面
- 目录导航（自动提取标题生成 TOC）
- 代码块语法高亮
- 表格样式化
- 参考来源可点击跳转

#### 报告操作
- 复制 Markdown 原文
- 导出为 .md 文件下载
- 删除报告

---

## 3. 技术架构

### 3.1 整体架构
```
┌──────────────────────────────────────┐
│           用户浏览器                    │
│     (Jinja2 渲染 + htmx 交互)          │
└──────────────┬───────────────────────┘
               │ HTTP
┌──────────────▼───────────────────────┐
│            FastAPI                     │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ │
│  │ 路由层   │ │ 模板渲染  │ │ 静态文件│ │
│  └─────────┘ └──────────┘ └────────┘ │
│  ┌─────────────────────────────────┐  │
│  │         服务层                    │  │
│  │  搜索服务 → 爬虫服务 → AI 服务   │  │
│  │         ↕                         │  │
│  │     工作流编排器                   │  │
│  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐  │
│  │   SQLite (SQLAlchemy ORM)        │  │
│  └─────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### 3.2 技术栈
| 组件 | 技术 | 版本 |
|------|------|------|
| Web 框架 | FastAPI | 0.110+ |
| ASGI 服务器 | Uvicorn | 0.29+ |
| 模板引擎 | Jinja2 | 3.1+ |
| 前端交互 | htmx | 2.0+ |
| CSS 框架 | TailwindCSS (CDN) | 3.4+ |
| 搜索 API | Tavily Python SDK | 0.5+ |
| HTTP 客户端 | httpx | 0.27+ |
| HTML 解析 | BeautifulSoup4 | 4.12+ |
| AI 代理 | litellm | 1.40+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库 | SQLite | 内置 |
| 数据验证 | Pydantic | 2.0+ |
| 异步任务 | asyncio (内置) | - |
| Markdown 前端 | marked.js + highlight.js | CDN |

### 3.3 项目结构
```
my-project-2/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI 应用入口
│   ├── config.py                   # Pydantic Settings 配置
│   ├── database.py                 # 数据库连接和会话管理
│   ├── models.py                   # SQLAlchemy 模型
│   ├── schemas.py                  # Pydantic 请求/响应 Schema
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py                # 页面路由（返回 HTML）
│   │   ├── research.py             # 调研任务 API（htmx 调用）
│   │   └── report.py               # 报告 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search.py               # Tavily 搜索服务
│   │   ├── crawler.py              # 网页爬取服务
│   │   ├── ai.py                   # litellm AI 服务
│   │   └── orchestrator.py         # 工作流编排
│   ├── templates/
│   │   ├── base.html               # 基础布局（TailwindCSS + htmx）
│   │   ├── index.html              # 首页
│   │   ├── research.html           # 调研进度页
│   │   ├── report.html             # 报告展示页
│   │   └── partials/
│   │       ├── task_card.html      # 任务卡片
│   │       ├── progress.html       # 进度条
│   │       └── report_list.html    # 报告列表
│   └── static/
│       └── custom.js               # 自定义 JS
├── reports/                         # 生成的 Markdown 报告文件
├── docs/
├── .env                             # API Keys 配置
├── .env.example                     # API Keys 模板
├── requirements.txt
└── README.md
```

---

## 4. 数据模型

### 4.1 ResearchTask（调研任务）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| topic | String(500) | 调研主题 |
| description | Text | 补充说明（可选） |
| model | String(50) | 使用的 AI 模型 |
| status | Enum | pending / searching / crawling / analyzing / completed / failed |
| progress | Integer | 进度百分比 0-100 |
| created_at | DateTime | 创建时间 |
| completed_at | DateTime | 完成时间（可空） |
| error_message | Text | 错误信息（可空） |

### 4.2 Source（信息来源）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| task_id | Integer (FK) | 关联调研任务 |
| url | String(2000) | 网页 URL |
| title | String(500) | 网页标题 |
| snippet | Text | 搜索摘要 |
| content | Text | 爬取正文 |
| relevance_score | Float | 相关性评分 |
| crawled_at | DateTime | 爬取时间 |

### 4.3 Report（调研报告）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| task_id | Integer (FK, Unique) | 关联调研任务 |
| content | Text | Markdown 格式报告内容 |
| word_count | Integer | 字数统计 |
| source_count | Integer | 参考来源数量 |
| file_path | String(500) | .md 文件存储路径 |

---

## 5. 核心流程

### 5.1 调研流程（异步执行）

```
1. 创建任务 → status: pending
2. 调用 Tavily Search API
   - 搜索关键词 = 调研主题 + 补充说明
   - 获取 10-20 条结果
   → status: searching, progress: 20%

3. 筛选 & 爬取
   - 按相关性排序，取 top 10
   - 使用 Tavily Extract 提取正文
   - 回退：httpx + BeautifulSoup4
   → status: crawling, progress: 20-60%

4. AI 分析
   - 将所有来源材料拼接为 prompt
   - 调用 litellm 生成结构化报告
   - Prompt 包含：报告模板 + 所有来源材料
   → status: analyzing, progress: 60-90%

5. 保存报告
   - Markdown 内容存入数据库
   - 同时保存为 .md 文件
   → status: completed, progress: 100%
```

### 5.2 进度查询（htmx 轮询）
- 前端每 2 秒通过 htmx 请求进度
- 返回当前状态和进度条
- 完成后自动跳转报告页

---

## 6. 页面设计

### 6.1 首页
- 顶部：项目名称 + 简介
- 中部：调研输入区域
  - 主题输入框（大文本框）
  - 补充说明（可选）
  - 模型选择下拉框
  - "开始调研"按钮
- 底部：历史调研任务列表

### 6.2 调研进度页
- 显示当前任务主题
- 进度条 + 当前阶段文字
- 已搜索到的来源列表（实时更新）

### 6.3 报告展示页
- 左侧：目录导航（TOC）
- 右侧：Markdown 渲染的报告内容
- 顶部：操作按钮（复制、下载、删除）
- 底部：参考来源列表

---

## 7. 配置管理

### 7.1 环境变量（.env）
```env
# Tavily
TAVILY_API_KEY=tvly-xxxxx

# AI Models
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# App Settings
DEFAULT_MODEL=openai/gpt-4o
MAX_SEARCH_RESULTS=15
MAX_CRAWL_PAGES=10
CRAWL_TIMEOUT=10
REPORT_OUTPUT_DIR=./reports
DATABASE_URL=sqlite:///./research.db
```

### 7.2 可选模型配置
```python
AVAILABLE_MODELS = [
    {"id": "openai/gpt-4o", "name": "GPT-4o"},
    {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini"},
    {"id": "anthropic/claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
    {"id": "anthropic/claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
]
```

---

## 8. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 搜索 API 超时 | 重试 2 次，仍失败则标记任务为 failed |
| 网页爬取失败 | 跳过该网页，继续爬取其他 |
| AI 生成失败 | 重试 1 次，仍失败则标记 failed |
| 无搜索结果 | 返回提示"未找到相关信息，请调整主题" |
| API Key 缺失 | 启动时检查，缺失则提示配置 |

---

## 9. 部署

### 9.1 本地运行
```bash
pip install -r requirements.txt
cp .env.example .env  # 填入 API Keys
uvicorn app.main:app --reload
# 访问 http://localhost:8000
```

### 9.2 Docker 部署（可选）
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 10. 开发计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| P0 | 项目搭建 + 配置 + 数据模型 | 0.5 天 |
| P1 | 搜索服务 + 爬虫服务 | 0.5 天 |
| P2 | AI 服务 + 工作流编排 | 0.5 天 |
| P3 | 页面路由 + 模板 + htmx 交互 | 1 天 |
| P4 | 测试 + 修复 + 打磨 | 0.5 天 |
| **总计** | | **3 天** |

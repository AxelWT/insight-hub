# AI 调研平台

一个基于多 Agent 协作的自动化调研系统，能够自动搜索、分析、整理信息并生成结构化调研报告。

## 项目架构

```
my-project-2/
├── app/
│   ├── agents/           # AI Agent 定义
│   │   ├── supervisor.py # 主管 Agent - 制定搜索策略
│   │   ├── searcher.py   # 搜索 Agent - 执行搜索
│   │   ├── crawler.py    # 爬虫 Agent - 抓取网页内容
│   │   ├── evaluator.py  # 评估 Agent - 评估信息充分性
│   │   └── writer.py     # 撰写 Agent - 生成调研报告
│   ├── graph/
│   │   ├── state.py      # 状态定义 (ResearchState)
│   │   └── research_graph.py  # LangGraph 工作流定义
│   ├── services/         # 外部服务封装
│   │   ├── ai.py         # LLM 调用服务
│   │   ├── search.py     # Tavily 搜索服务
│   │   └── crawler.py    # 网页爬取服务
│   ├── ui/               # Streamlit 前端
│   │   ├── sidebar.py    # 侧边栏
│   │   ├── research_page.py  # 调研页面
│   │   ├── report_page.py    # 报告页面
│   │   └── agent_visual.py   # Agent 可视化
│   ├── models.py         # SQLAlchemy 数据模型
│   ├── database.py       # 数据库配置
│   ├── config.py         # 应用配置
│   └── main.py           # Streamlit 入口
├── docs/                 # PRD 文档
├── .env.example          # 环境变量示例
└── requirements.txt      # Python 依赖
```

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

### 条件路由逻辑

Evaluator 评估后会进行条件路由：
- **信息充分** → 进入 Writer 生成报告
- **信息不充分且未达最大轮次** → 返回 Searcher 补充搜索
- **已达最大轮次** → 强制进入 Writer 生成报告

### 调研深度

系统支持三种调研深度：

| 深度 | 最大搜索轮次 | 预期来源数 | 适用场景 |
|------|-------------|-----------|----------|
| 快速 (quick) | 1 轮 | 5-8 个 | 快速了解概览 |
| 标准 (standard) | 3 轮 | 10-15 个 | 常规调研 |
| 深度 (deep) | 5 轮 | 15-25 个 | 深入研究 |

## 技术栈

- **前端**: Streamlit
- **工作流引擎**: LangGraph
- **LLM 框架**: LangChain + LiteLLM
- **搜索 API**: Tavily
- **数据库**: SQLite + SQLAlchemy
- **支持的 LLM**: OpenAI GPT-4o、Anthropic Claude、DeepSeek

## 运行命令

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入 API Key：

```bash
cp .env.example .env
```

需要配置的 Key：
- `TAVILY_API_KEY` - Tavily 搜索 API (必需)
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `DEEPSEEK_API_KEY` - 至少一个 LLM API Key

### 3. 启动应用

```bash
streamlit run app/main.py
```

应用默认运行在 `http://localhost:8501`

## 使用流程

1. 在左侧边栏输入调研主题
2. 选择 AI 模型和调研深度
3. 点击"开始调研"
4. 实时查看 Agent 的思考和决策过程
5. 调研完成后查看结构化报告

## 数据模型

- **ResearchTask**: 调研任务（主题、状态、进度）
- **Source**: 信息来源（URL、标题、内容）
- **AgentLog**: Agent 操作日志（决策过程）
- **Report**: 生成的调研报告

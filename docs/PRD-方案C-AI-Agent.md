# PRD：AI 调研平台 - 方案 C（AI Agent 架构）

## 1. 产品概述

### 1.1 产品定位
基于 AI Agent 架构的智能调研平台。AI Agent 自主规划搜索策略、多轮迭代搜索、评估信息充分性，最终生成高质量结构化调研报告。

### 1.2 目标用户
对报告质量有较高要求的个人用户，愿意为更好的报告质量付出更多时间和 Token 成本。

### 1.3 核心价值
- 同方案 A/B 的基础价值
- **核心差异**：AI 自主决策搜索策略，自动判断信息是否充分，不够则调整关键词补充搜索
- 报告质量显著高于固定流程方案

---

## 2. 功能需求

### 2.1 调研任务管理

#### 创建调研
- 输入调研主题（必填）
- 可选补充说明
- 选择 AI 模型
- 选择调研深度：
  - **快速**：1 轮搜索，5-8 个来源（低成本）
  - **标准**：2-3 轮搜索，10-15 个来源（推荐）
  - **深度**：3-5 轮搜索，15-25 个来源（高质量）
- 点击"开始调研"

#### Agent 可视化
- 实时展示 Agent 的思考和决策过程
- 显示 Agent 状态图（LangGraph 可视化）
- 每一步的输入/输出可展开查看

#### 任务状态
- **规划中**：Agent 正在制定搜索策略
- **搜索中（第 N 轮）**：正在搜索第 N 轮
- **评估中**：Agent 正在评估信息充分性
- **补充搜索**：信息不够充分，调整策略继续搜索
- **撰写中**：Agent 正在撰写报告
- **已完成**：报告已生成

### 2.2 Agent 搜索策略

#### Supervisor Agent（主管）
- 分析调研主题，拆解为多个搜索子任务
- 为每个子任务生成搜索关键词
- 评估搜索结果的覆盖度和充分性
- 决定是否需要补充搜索

#### Searcher Agent（搜索员）
- 根据 Supervisor 的指令执行搜索
- 使用 Tavily Search API
- 对搜索结果进行初步相关性评估
- 返回候选网页列表

#### Crawler Agent（爬虫）
- 爬取候选网页的正文
- 提取关键信息和数据
- 标注信息来源和质量

#### Writer Agent（撰写者）
- 分析所有收集的材料
- 生成结构化的调研报告
- 标注每个论点的信息来源
- 生成摘要和结论

### 2.3 多轮搜索示例

以"2024 年中国新能源汽车市场分析"为例：

```
第 1 轮搜索：
  关键词："2024 中国新能源汽车 市场分析"
  结果：10 条，覆盖面较广但缺乏数据

评估：信息不够充分，缺少具体销量数据

第 2 轮搜索：
  关键词："2024 新能源汽车 销量数据 比亚迪 特斯拉"
  结果：8 条，获得具体销量数据

评估：销量数据充分，但缺少政策分析

第 3 轮搜索：
  关键词："2024 新能源汽车政策 补贴 产业政策"
  结果：6 条，获得政策信息

评估：信息充分，开始撰写报告
```

### 2.4 AI 报告生成

#### 报告结构
```markdown
# {调研主题}

## 摘要
## 一、背景与概述
## 二、核心发现
### 2.1 ...
### 2.2 ...
## 三、数据分析
## 四、趋势与预测
## 五、不同观点与争议
## 六、总结与建议
## 附录
### A. 搜索策略说明
### B. 信息来源评估
## 参考来源
```

#### 报告特色
- 每个论点标注来源（[1] [2] 引用标记）
- 末尾附搜索策略说明（展示 Agent 的思考过程）
- 信息来源评估（标注每个来源的可信度）

### 2.5 报告展示

#### 页面展示
- Agent 思考过程时间线（可展开/折叠）
- 三栏布局：目录 → 报告 → 来源面板
- 引用标注可悬浮查看来源详情
- Markdown 渲染 + 目录导航

#### 报告操作
- 复制 / 下载 Markdown
- 查看原始搜索材料
- "继续深入调研"（基于当前报告，Agent 继续补充搜索）

---

## 3. 技术架构

### 3.1 整体架构
```
┌──────────────────────────────────┐
│        Streamlit / Gradio UI      │
└──────────────┬───────────────────┘
               │
┌──────────────▼───────────────────┐
│           FastAPI 后端             │
│  ┌─────────────────────────────┐  │
│  │    LangGraph Agent 状态图    │  │
│  │                             │  │
│  │  ┌─────────┐  ┌──────────┐ │  │
│  │  │Supervisor│─►│ Searcher │ │  │
│  │  └────┬────┘  └──────────┘ │  │
│  │       │       ┌──────────┐ │  │
│  │       ├──────►│ Crawler  │ │  │
│  │       │       └──────────┘ │  │
│  │       │       ┌──────────┐ │  │
│  │       ├──────►│ Evaluator│ │  │
│  │       │       └──────────┘ │  │
│  │       │       ┌──────────┐ │  │
│  │       └──────►│ Writer   │ │  │
│  │               └──────────┘ │  │
│  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │
│  │   Tools                      │  │
│  │   tavily_search | crawl | llm│  │
│  └─────────────────────────────┘  │
│  ┌─────────────────────────────┐  │
│  │   SQLite + litellm          │  │
│  └─────────────────────────────┘  │
└──────────────────────────────────┘
```

### 3.2 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Agent 框架 | LangGraph | 状态机驱动的多 Agent 编排 |
| LLM 框架 | LangChain + litellm | 工具调用 + 多模型 |
| 展示框架 | Streamlit | 快速搭建 AI 应用 UI |
| Web 框架 | FastAPI | 后端 API |
| 搜索 | Tavily | 搜索 + 提取 |
| 爬虫 | httpx + BeautifulSoup4 | 网页爬取 |
| AI | litellm | 多模型代理 |
| 数据库 | SQLite | 数据存储 |
| 向量存储 | ChromaDB（可选） | 报告检索 |
| 缓存 | Redis（可选） | Agent 状态缓存 |

### 3.3 项目结构
```
my-project-2/
├── app/
│   ├── __init__.py
│   ├── main.py                     # Streamlit 入口
│   ├── config.py                   # 配置管理
│   ├── database.py                 # 数据库连接
│   ├── models.py                   # 数据模型
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── supervisor.py           # Supervisor Agent
│   │   ├── searcher.py             # Searcher Agent
│   │   ├── crawler.py              # Crawler Agent
│   │   ├── evaluator.py            # Evaluator Agent
│   │   └── writer.py               # Writer Agent
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── research_graph.py       # LangGraph 状态图定义
│   │   └── state.py                # Graph State 定义
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_tool.py          # Tavily 搜索工具
│   │   ├── crawl_tool.py           # 网页爬取工具
│   │   └── analyze_tool.py         # 内容分析工具
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai.py                   # litellm 模型调用
│   │   └── report.py               # 报告管理服务
│   │
│   └── ui/
│       ├── __init__.py
│       ├── sidebar.py              # 侧边栏（任务列表）
│       ├── research_page.py        # 调研页面
│       ├── agent_visual.py         # Agent 可视化组件
│       └── report_page.py          # 报告展示页面
│
├── reports/                         # 报告文件
├── requirements.txt
├── .env
└── docs/
```

---

## 4. LangGraph 状态图设计

### 4.1 状态定义
```python
class ResearchState(TypedDict):
    topic: str                    # 调研主题
    description: str              # 补充说明
    depth: str                    # 调研深度
    search_rounds: int            # 当前搜索轮次
    max_rounds: int               # 最大搜索轮次
    search_queries: list[str]     # 搜索关键词列表
    search_results: list[dict]    # 搜索结果
    crawled_content: list[dict]   # 爬取内容
    evaluation: dict              # 充分性评估结果
    report: str                   # 生成的报告
    agent_logs: list[dict]        # Agent 决策日志
    current_step: str             # 当前步骤
```

### 4.2 状态图
```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Supervisor│ ← 规划搜索策略
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Searcher  │ ← 执行搜索
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  Crawler  │ ← 爬取网页
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │ Evaluator │ ← 评估充分性
                    └────┬─────┘
                         │
                  ┌──────┴──────┐
                  │             │
           信息不够充分    信息充分
                  │             │
           ┌──────▼──────┐ ┌───▼────┐
           │ 搜索轮次 < max?│ │ Writer │ ← 生成报告
           └──────┬──────┘ └───┬────┘
                  │             │
           ┌──────┴──────┐ ┌───▼────┐
           │ Yes         │ No │  END   │
           ▼             ▼   └────────┘
      回到 Searcher   进入 Writer
```

### 4.3 Agent 决策逻辑

#### Supervisor
```
输入：主题 + 补充说明
输出：搜索关键词列表 + 搜索策略

Prompt 示例：
"你是一个调研主管。用户想调研'{topic}'。
请制定搜索策略：
1. 拆解为 3-5 个子主题
2. 为每个子主题生成 2-3 个搜索关键词
3. 按优先级排序"
```

#### Evaluator
```
输入：已收集的所有信息
输出：充分性评估 + 缺口分析

Prompt 示例：
"评估以下信息是否足以撰写一份关于'{topic}'的调研报告。
已有信息：{summary_of_collected_info}
请评估：
1. 覆盖度（1-10 分）
2. 信息缺口是什么
3. 是否需要补充搜索
4. 如需补充，建议新的搜索关键词"
```

---

## 5. 数据模型

### 5.1 ResearchTask
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| topic | String(500) | 调研主题 |
| description | Text | 补充说明 |
| model | String(50) | AI 模型 |
| depth | Enum | quick / standard / deep |
| status | Enum | planning / searching / evaluating / writing / completed / failed |
| search_rounds | Integer | 实际搜索轮次 |
| current_step | String | 当前步骤描述 |
| created_at | DateTime | 创建时间 |
| completed_at | DateTime | 完成时间 |

### 5.2 AgentLog
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer (PK) | 自增主键 |
| task_id | Integer (FK) | 关联任务 |
| agent_name | String | Agent 名称 |
| step | String | 步骤名 |
| input_data | JSON | 输入数据 |
| output_data | JSON | 输出数据 |
| decision | Text | 决策说明 |
| timestamp | DateTime | 时间戳 |

### 5.3 Source / Report
同方案 A。

---

## 6. 页面设计

### 6.1 Streamlit 页面布局

#### 首页（sidebar + main）
- 侧边栏：
  - 调研输入表单
  - 模型和深度选择
  - 历史任务列表
- 主区域：
  - Agent 实时可视化面板
  - 思考过程时间线
  - 当前状态大字展示

#### 报告展示页
- 顶部：报告标题 + 元信息
- 左侧：目录导航（st.sidebar）
- 中间：Markdown 渲染（st.markdown）
- 底部：参考来源 + Agent 决策日志

### 6.2 Agent 可视化
```
调研进度面板
┌─────────────────────────────────────────┐
│  🔄 第 2 轮搜索中                        │
│                                          │
│  ✅ 规划搜索策略                          │
│  ├── 关键词："中国新能源汽车" "市场分析"   │
│  └── 策略：分 3 个子主题搜索              │
│                                          │
│  ✅ 第 1 轮搜索（已完成）                  │
│  ├── 搜索到 10 条结果                     │
│  └── 评估：覆盖度 6/10，缺少销量数据      │
│                                          │
│  🔄 第 2 轮搜索（进行中）                  │
│  ├── 关键词："新能源车 销量 2024"          │
│  └── 已搜索到 5/8 条结果...               │
│                                          │
│  ⏳ 爬取网页                              │
│  ⏳ 评估充分性                            │
│  ⏳ 撰写报告                              │
└─────────────────────────────────────────┘
```

---

## 7. 配置管理

### 环境变量
```env
# Tavily
TAVILY_API_KEY=tvly-xxxxx

# AI Models
OPENAI_API_KEY=sk-xxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Agent Settings
DEFAULT_MODEL=openai/gpt-4o
EVALUATOR_MODEL=openai/gpt-4o-mini
QUICK_MAX_ROUNDS=1
STANDARD_MAX_ROUNDS=3
DEEP_MAX_ROUNDS=5
RESULTS_PER_ROUND=8

# App
DATABASE_URL=sqlite:///./research.db
REPORT_OUTPUT_DIR=./reports
```

---

## 8. 错误处理

| 场景 | 处理方式 |
|------|---------|
| Agent 陷入循环 | 最大轮次限制 + 强制结束 |
| 搜索 API 超时 | 单轮重试 2 次，失败则跳过 |
| AI 生成失败 | 重试 1 次，仍失败则降级为简单报告 |
| Token 超限 | 截断输入内容，优先保留最新信息 |
| Agent 决策异常 | 日志记录 + 降级为固定流程 |

---

## 9. 成本估算

### Token 消耗（标准深度，约 15 个来源）

| Agent | 每轮 Token | 轮次 | 小计 |
|-------|-----------|------|------|
| Supervisor | ~2,000 | 1 | 2,000 |
| Searcher | ~1,000 × 3 搜索 | 3 | 9,000 |
| Evaluator | ~3,000 | 3 | 9,000 |
| Writer | ~15,000 | 1 | 15,000 |
| **总计** | | | **~35,000 tokens** |

使用 GPT-4o 约 $0.35/次，使用 Claude Sonnet 约 $0.21/次。

---

## 10. 部署

### 本地运行
```bash
pip install -r requirements.txt
cp .env.example .env
streamlit run app/main.py --server.port 8501
```

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app/main.py", "--server.address", "0.0.0.0"]
```

---

## 11. 开发计划

| 阶段 | 内容 | 时间 |
|------|------|------|
| P0 | 项目搭建 + LangGraph 环境配置 | 0.5 天 |
| P1 | Agent 定义（Supervisor + Searcher + Crawler） | 1.5 天 |
| P2 | Evaluator + Writer + 状态图串联 | 1.5 天 |
| P3 | Streamlit UI + Agent 可视化 | 1.5 天 |
| P4 | Agent 调优 + 测试 + 修复 | 1.5 天 |
| **总计** | | **6.5 天** |

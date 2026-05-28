# Vue 3 前端迁移实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AI 调研平台的前端从 Streamlit 完全替换为 Vue 3 + FastAPI 架构，实现前后端分离和 WebSocket 实时推送。

**Architecture:** 后端用 FastAPI 暴露 REST API 和 WebSocket 端点，前端用 Vue 3 SPA 消费 API。LangGraph Agent 业务逻辑保持不变，仅将 UI 层从 Streamlit 迁移到 Vue。任务执行在后台线程中运行，通过 WebSocket 推送实时状态。

**Tech Stack:** Vue 3, Vite, TypeScript, Pinia, Vue Router, Element Plus, axios, FastAPI, WebSocket, SQLAlchemy, LangGraph

---

## File Structure

### Backend (新建)
| 文件 | 职责 |
|------|------|
| `backend/__init__.py` | 包标记 |
| `backend/main.py` | FastAPI 入口，CORS，路由注册，启动事件 |
| `backend/api/__init__.py` | 包标记 |
| `backend/api/tasks.py` | 任务 CRUD：GET/POST/DELETE /api/tasks |
| `backend/api/reports.py` | 报告接口：GET /api/tasks/{id}/report, sources, logs |
| `backend/api/config.py` | 配置接口：GET /api/config/models |
| `backend/api/websocket.py` | WebSocket 端点：WS /api/ws/tasks/{id} |
| `backend/schemas/__init__.py` | 包标记 |
| `backend/schemas/task.py` | 任务 Pydantic 模型 |
| `backend/schemas/report.py` | 报告/来源/日志 Pydantic 模型 |
| `backend/core/__init__.py` | 包标记 |
| `backend/core/runner.py` | 任务执行器：异步包装 LangGraph，WebSocket 推送 |

### Backend (从 app/ 迁移，代码不变)
| 原路径 | 新路径 |
|--------|--------|
| `app/config.py` | `backend/core/config.py` |
| `app/database.py` | `backend/core/database.py` |
| `app/models.py` | `backend/core/models.py` |
| `app/agents/*` | `backend/core/agents/*` |
| `app/graph/*` | `backend/core/graph/*` |
| `app/services/*` | `backend/core/services/*` |

### Frontend (全新)
| 文件 | 职责 |
|------|------|
| `frontend/package.json` | 依赖管理 |
| `frontend/vite.config.ts` | Vite 配置 + API/WebSocket 代理 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/index.html` | HTML 入口 |
| `frontend/src/main.ts` | Vue 入口：注册 Element Plus、Pinia、Router |
| `frontend/src/App.vue` | 根组件：el-container 布局 |
| `frontend/src/router/index.ts` | 路由配置 |
| `frontend/src/api/request.ts` | axios 实例 |
| `frontend/src/api/task.ts` | 任务 API |
| `frontend/src/api/report.ts` | 报告 API |
| `frontend/src/stores/task.ts` | 任务 Pinia store |
| `frontend/src/stores/websocket.ts` | WebSocket store |
| `frontend/src/views/HomeView.vue` | 首页 |
| `frontend/src/views/ResearchView.vue` | 调研进度页 |
| `frontend/src/views/ReportView.vue` | 报告详情页 |
| `frontend/src/components/Sidebar.vue` | 侧边栏 |
| `frontend/src/components/AgentTimeline.vue` | Agent 时间线 |

---

## Task 1: 创建后端目录结构并迁移业务代码

**Files:**
- Create: `backend/__init__.py`, `backend/core/__init__.py`, `backend/api/__init__.py`, `backend/schemas/__init__.py`
- Copy: `app/config.py` → `backend/core/config.py`
- Copy: `app/database.py` → `backend/core/database.py`
- Copy: `app/models.py` → `backend/core/models.py`
- Copy: `app/agents/` → `backend/core/agents/`
- Copy: `app/graph/` → `backend/core/graph/`
- Copy: `app/services/` → `backend/core/services/`

- [ ] **Step 1: 创建 backend 目录结构**

```bash
mkdir -p backend/core backend/api backend/schemas
touch backend/__init__.py backend/core/__init__.py backend/api/__init__.py backend/schemas/__init__.py
```

- [ ] **Step 2: 复制业务代码到 backend/core/**

```bash
cp app/config.py backend/core/config.py
cp app/database.py backend/core/database.py
cp app/models.py backend/core/models.py
cp -r app/agents backend/core/agents
cp -r app/graph backend/core/graph
cp -r app/services backend/core/services
```

- [ ] **Step 3: 修改 backend/core/ 中的 import 路径**

将所有 `from app.` 改为 `from backend.core.`。

`backend/core/config.py` — 无需修改（无内部 import）

`backend/core/database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.core.config import settings

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
```

`backend/core/models.py` — 将 `from app.database import Base` 改为 `from backend.core.database import Base`

`backend/core/services/report.py` — 将 `from app.config import settings` 和 `from app.models import ...` 改为 `from backend.core.config import settings` 和 `from backend.core.models import ...`

`backend/core/services/ai.py` — 将 `from app.config import settings` 改为 `from backend.core.config import settings`

`backend/core/services/search.py` — 同上

`backend/core/services/crawler.py` — 同上

`backend/core/graph/research_graph.py` — 将所有 `from app.` 改为 `from backend.core.`

`backend/core/agents/*.py` — 将所有 `from app.` 改为 `from backend.core.`

- [ ] **Step 4: 验证 import 正确**

```bash
cd /Users/allen/IdeaProjects/explore/insight-hub
python -c "from backend.core.config import settings; print('config OK')"
python -c "from backend.core.database import Base; print('database OK')"
python -c "from backend.core.models import ResearchTask; print('models OK')"
```

Expected: 每行输出对应 OK

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: create backend directory and migrate business code from app/"
```

---

## Task 2: 定义 Pydantic 请求/响应模型

**Files:**
- Create: `backend/schemas/task.py`
- Create: `backend/schemas/report.py`

- [ ] **Step 1: 创建任务 schema**

`backend/schemas/task.py`:
```python
from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    topic: str
    description: str = ""
    model: str = "deepseek"
    depth: str = "standard"


class TaskResponse(BaseModel):
    id: int
    topic: str
    description: str
    model: str
    depth: str
    status: str
    progress: int
    current_step: str
    search_rounds: int
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
```

- [ ] **Step 2: 创建报告 schema**

`backend/schemas/report.py`:
```python
from datetime import datetime
from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: int
    url: str
    title: str
    snippet: str
    content: str
    relevance_score: float | None = None
    search_round: int
    crawled_at: datetime

    model_config = {"from_attributes": True}


class AgentLogResponse(BaseModel):
    id: int
    agent_name: str
    step: str
    input_data: dict | None = None
    output_data: dict | None = None
    decision: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: int
    task_id: int
    content: str
    word_count: int
    source_count: int
    file_path: str | None = None

    model_config = {"from_attributes": True}


class TaskDetailResponse(BaseModel):
    task: "TaskResponse"
    report: ReportResponse | None = None
    sources: list[SourceResponse] = []
    logs: list[AgentLogResponse] = []


from backend.schemas.task import TaskResponse

TaskDetailResponse.model_rebuild()
```

- [ ] **Step 3: 验证 schema 可导入**

```bash
python -c "from backend.schemas.task import TaskCreate, TaskResponse, TaskListResponse; print('task schemas OK')"
python -c "from backend.schemas.report import ReportResponse, SourceResponse, AgentLogResponse; print('report schemas OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/schemas/
git commit -m "feat: add Pydantic request/response schemas"
```

---

## Task 3: 实现配置和任务 API 路由

**Files:**
- Create: `backend/api/config.py`
- Create: `backend/api/tasks.py`

- [ ] **Step 1: 创建配置 API**

`backend/api/config.py`:
```python
from fastapi import APIRouter
from backend.core.config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/models")
def get_models():
    return {"models": settings.available_models}
```

- [ ] **Step 2: 创建任务 API**

`backend/api/tasks.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import ResearchTask
from backend.schemas.task import TaskCreate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(db: Session = Depends(get_db)):
    tasks = (
        db.query(ResearchTask)
        .order_by(ResearchTask.created_at.desc())
        .limit(50)
        .all()
    )
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.post("", response_model=TaskResponse)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = ResearchTask(
        topic=body.topic,
        description=body.description,
        model=body.model,
        depth=body.depth,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/config.py backend/api/tasks.py
git commit -m "feat: add config and task API routes"
```

---

## Task 4: 实现报告 API 路由

**Files:**
- Create: `backend/api/reports.py`

- [ ] **Step 1: 创建报告 API**

`backend/api/reports.py`:
```python
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import ResearchTask, Report, Source, AgentLog
from backend.schemas.report import (
    ReportResponse,
    SourceResponse,
    AgentLogResponse,
)

router = APIRouter(prefix="/api/tasks", tags=["reports"])


@router.get("/{task_id}/report", response_model=ReportResponse | None)
def get_report(task_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return ReportResponse.model_validate(report)


@router.get("/{task_id}/sources", response_model=list[SourceResponse])
def get_sources(task_id: int, db: Session = Depends(get_db)):
    sources = (
        db.query(Source)
        .filter(Source.task_id == task_id)
        .order_by(Source.search_round, Source.id)
        .all()
    )
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/{task_id}/logs", response_model=list[AgentLogResponse])
def get_agent_logs(task_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(AgentLog)
        .filter(AgentLog.task_id == task_id)
        .order_by(AgentLog.timestamp)
        .all()
    )
    return [AgentLogResponse.model_validate(l) for l in logs]
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/reports.py
git commit -m "feat: add report, sources, and agent logs API routes"
```

---

## Task 5: 实现 WebSocket 端点和任务执行器

**Files:**
- Create: `backend/api/websocket.py`
- Create: `backend/core/runner.py`

- [ ] **Step 1: 创建 WebSocket 连接管理器**

`backend/api/websocket.py`:
```python
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# task_id -> set of connected websockets
_connections: dict[int, set[WebSocket]] = {}


async def connect(task_id: int, ws: WebSocket):
    await ws.accept()
    _connections.setdefault(task_id, set()).add(ws)


def disconnect(task_id: int, ws: WebSocket):
    conns = _connections.get(task_id)
    if conns:
        conns.discard(ws)
        if not conns:
            del _connections[task_id]


async def broadcast(task_id: int, message: dict):
    conns = _connections.get(task_id, set())
    dead = []
    for ws in conns:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.discard(ws)


@router.websocket("/api/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: int):
    await connect(task_id, websocket)
    try:
        while True:
            # Keep connection alive; client may send pings
            await websocket.receive_text()
    except WebSocketDisconnect:
        disconnect(task_id, websocket)
```

- [ ] **Step 2: 创建任务执行器**

`backend/core/runner.py`:
```python
import asyncio
import logging
from datetime import datetime

from backend.core.database import SessionLocal
from backend.core.models import ResearchTask
from backend.core.config import settings
from backend.core.services.report import save_report, save_sources, save_agent_log, update_task_status

logger = logging.getLogger(__name__)

# Import broadcast lazily to avoid circular imports
_broadcast = None


def set_broadcaster(broadcast_fn):
    global _broadcast
    _broadcast = broadcast_fn


async def _ws_broadcast(task_id: int, message: dict):
    if _broadcast:
        await _broadcast(task_id, message)


def run_research(task_id: int):
    """Run research in a background thread. Called via asyncio.to_thread()."""
    from backend.core.graph.research_graph import research_graph

    db = SessionLocal()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            return
        topic = task.topic
        description = task.description
        model = task.model
        depth = task.depth
    finally:
        db.close()

    # Update status to planning
    db = SessionLocal()
    try:
        update_task_status(db, task_id, "planning", "正在规划搜索策略...", 5)
    finally:
        db.close()

    # Run the graph
    try:
        initial_state = {
            "topic": topic,
            "description": description,
            "model": model,
            "evaluator_model": settings.evaluator_model,
            "depth": depth,
            "max_rounds": settings.get_max_rounds(depth),
            "search_rounds": 0,
            "search_results": [],
            "crawled_content": [],
            "agent_logs": [],
            "progress": 0,
            "sources_saved": False,
        }

        status_map = {
            "supervisor": ("planning", "正在规划搜索策略..."),
            "searcher": ("searching", "正在搜索相关信息..."),
            "crawler": ("searching", "正在爬取网页内容..."),
            "evaluator": ("evaluating", "正在评估信息充分性..."),
            "writer": ("writing", "正在撰写调研报告..."),
        }

        final_state = {}
        for event in research_graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = node_output
                db = SessionLocal()
                try:
                    if node_name in status_map:
                        status, step_desc = status_map[node_name]
                        progress = node_output.get("progress", 0)
                        search_rounds = node_output.get("search_rounds")
                        update_task_status(
                            db, task_id, status, step_desc, progress, search_rounds
                        )

                    logs = node_output.get("agent_logs", [])
                    if logs:
                        latest_log = logs[-1]
                        save_agent_log(db, task_id, latest_log)

                    if node_name in ("searcher", "crawler") and node_output.get(
                        "search_results"
                    ):
                        save_sources(
                            db,
                            task_id,
                            node_output.get("search_results", []),
                            node_output.get("crawled_content", []),
                        )
                finally:
                    db.close()

        db = SessionLocal()
        try:
            report_content = final_state.get("report", "未能生成报告")
            save_report(db, task_id, report_content)
        finally:
            db.close()

    except Exception as e:
        logger.exception(f"Research task {task_id} failed")
        db = SessionLocal()
        try:
            task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
        finally:
            db.close()


async def start_research(task_id: int):
    """Start research task in background and broadcast status via WebSocket."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_research, task_id)
```

- [ ] **Step 3: 验证模块可导入**

```bash
python -c "from backend.api.websocket import router; print('websocket OK')"
python -c "from backend.core.runner import run_research, start_research; print('runner OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/api/websocket.py backend/core/runner.py
git commit -m "feat: add WebSocket endpoint and async task runner"
```

---

## Task 6: 创建 FastAPI 入口

**Files:**
- Create: `backend/main.py`
- Create: `backend/requirements.txt`

- [ ] **Step 1: 创建 FastAPI 主入口**

`backend/main.py`:
```python
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.core.runner import set_broadcaster, start_research
from backend.api.tasks import router as tasks_router
from backend.api.reports import router as reports_router
from backend.api.config import router as config_router
from backend.api.websocket import router as ws_router, broadcast


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    set_broadcaster(broadcast)
    yield


app = FastAPI(title="AI 调研平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(reports_router)
app.include_router(config_router)
app.include_router(ws_router)


@app.post("/api/tasks/{task_id}/start")
async def start_task(task_id: int):
    """Start a pending research task."""
    asyncio.create_task(start_research(task_id))
    return {"ok": True, "message": "任务已启动"}
```

- [ ] **Step 2: 创建 backend requirements.txt**

`backend/requirements.txt`:
```
fastapi>=0.115
uvicorn[standard]>=0.30
websockets>=12.0
langgraph>=0.2
langchain>=0.3
langchain-core>=0.3
openai>=1.0
tavily-python>=0.5
httpx>=0.27
beautifulsoup4>=4.12
sqlalchemy>=2.0
pydantic>=2.0
pydantic-settings>=2.0
python-dotenv>=1.0
```

- [ ] **Step 3: 验证 FastAPI 可启动**

```bash
cd /Users/allen/IdeaProjects/explore/insight-hub
pip install fastapi uvicorn websockets
python -c "from backend.main import app; print('FastAPI app OK')"
```

- [ ] **Step 4: Commit**

```bash
git add backend/main.py backend/requirements.txt
git commit -m "feat: add FastAPI entry point with CORS and route registration"
```

---

## Task 7: 修改任务创建 API 以自动启动执行

**Files:**
- Modify: `backend/api/tasks.py`

- [ ] **Step 1: 更新 create_task 端点，创建后自动启动**

在 `backend/api/tasks.py` 的 `create_task` 函数末尾，添加启动逻辑。修改后的完整文件：

`backend/api/tasks.py`:
```python
import asyncio

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import ResearchTask
from backend.core.runner import start_research
from backend.schemas.task import TaskCreate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(db: Session = Depends(get_db)):
    tasks = (
        db.query(ResearchTask)
        .order_by(ResearchTask.created_at.desc())
        .limit(50)
        .all()
    )
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.post("", response_model=TaskResponse)
async def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = ResearchTask(
        topic=body.topic,
        description=body.description,
        model=body.model,
        depth=body.depth,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Start research in background
    asyncio.create_task(start_research(task.id))

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: 从 main.py 移除多余的 /start 端点**

从 `backend/main.py` 中删除 `@app.post("/api/tasks/{task_id}/start")` 函数，因为创建任务时已自动启动。

- [ ] **Step 3: Commit**

```bash
git add backend/api/tasks.py backend/main.py
git commit -m "feat: auto-start research on task creation"
```

---

## Task 8: 初始化 Vue 3 前端项目

**Files:**
- Create: `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/index.html`, `frontend/src/main.ts`, `frontend/src/App.vue`, `frontend/src/env.d.ts`

- [ ] **Step 1: 创建 Vue 3 项目**

```bash
cd /Users/allen/IdeaProjects/explore/insight-hub
npm create vite@latest frontend -- --template vue-ts
cd frontend
npm install
npm install vue-router@4 pinia element-plus @element-plus/icons-vue axios markdown-it
npm install -D @types/markdown-it
```

- [ ] **Step 2: 配置 Vite 代理**

`frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
```

- [ ] **Step 3: 配置 main.ts**

`frontend/src/main.ts`:
```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
```

- [ ] **Step 4: 配置 App.vue**

`frontend/src/App.vue`:
```vue
<script setup lang="ts">
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="320px" style="border-right: 1px solid var(--el-border-color)">
      <Sidebar />
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
```

- [ ] **Step 5: 验证前端可启动**

```bash
cd /Users/allen/IdeaProjects/explore/insight-hub/frontend
npm run dev
```

Expected: Vite dev server 启动在 http://localhost:5173

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Vue 3 project with Vite, Pinia, Element Plus"
```

---

## Task 9: 实现 API 请求层和路由

**Files:**
- Create: `frontend/src/api/request.ts`, `frontend/src/api/task.ts`, `frontend/src/api/report.ts`
- Create: `frontend/src/router/index.ts`

- [ ] **Step 1: 创建 axios 实例**

`frontend/src/api/request.ts`:
```typescript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
```

- [ ] **Step 2: 创建任务 API**

`frontend/src/api/task.ts`:
```typescript
import request from './request'

export interface Task {
  id: number
  topic: string
  description: string
  model: string
  depth: string
  status: string
  progress: number
  current_step: string
  search_rounds: number
  created_at: string
  completed_at: string | null
  error_message: string | null
}

export interface TaskCreateParams {
  topic: string
  description?: string
  model: string
  depth: string
}

export function getTasks(): Promise<{ tasks: Task[] }> {
  return request.get('/tasks')
}

export function createTask(data: TaskCreateParams): Promise<Task> {
  return request.post('/tasks', data)
}

export function getTask(id: number): Promise<Task> {
  return request.get(`/tasks/${id}`)
}

export function deleteTask(id: number): Promise<{ ok: boolean }> {
  return request.delete(`/tasks/${id}`)
}
```

- [ ] **Step 3: 创建报告 API**

`frontend/src/api/report.ts`:
```typescript
import request from './request'

export interface Report {
  id: number
  task_id: number
  content: string
  word_count: number
  source_count: number
  file_path: string | null
}

export interface Source {
  id: number
  url: string
  title: string
  snippet: string
  content: string
  relevance_score: number | null
  search_round: number
  crawled_at: string
}

export interface AgentLog {
  id: number
  agent_name: string
  step: string
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  decision: string
  timestamp: string
}

export function getReport(taskId: number): Promise<Report> {
  return request.get(`/tasks/${taskId}/report`)
}

export function getSources(taskId: number): Promise<Source[]> {
  return request.get(`/tasks/${taskId}/sources`)
}

export function getAgentLogs(taskId: number): Promise<AgentLog[]> {
  return request.get(`/tasks/${taskId}/logs`)
}

export function getModels(): Promise<{ models: { id: string; name: string }[] }> {
  return request.get('/config/models')
}
```

- [ ] **Step 4: 创建路由**

`frontend/src/router/index.ts`:
```typescript
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
    },
    {
      path: '/research/:id',
      name: 'research',
      component: () => import('../views/ResearchView.vue'),
    },
    {
      path: '/report/:id',
      name: 'report',
      component: () => import('../views/ReportView.vue'),
    },
  ],
})

export default router
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/ frontend/src/router/
git commit -m "feat: add API request layer and Vue Router config"
```

---

## Task 10: 实现 Pinia Store

**Files:**
- Create: `frontend/src/stores/task.ts`, `frontend/src/stores/websocket.ts`

- [ ] **Step 1: 创建任务 store**

`frontend/src/stores/task.ts`:
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getTasks, createTask, deleteTask, type Task, type TaskCreateParams } from '../api/task'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const res = await getTasks()
      tasks.value = res.tasks
    } finally {
      loading.value = false
    }
  }

  async function addTask(params: TaskCreateParams): Promise<Task> {
    const task = await createTask(params)
    tasks.value.unshift(task)
    return task
  }

  async function removeTask(id: number) {
    await deleteTask(id)
    tasks.value = tasks.value.filter((t) => t.id !== id)
  }

  function updateTask(id: number, updates: Partial<Task>) {
    const idx = tasks.value.findIndex((t) => t.id === id)
    if (idx !== -1) {
      tasks.value[idx] = { ...tasks.value[idx], ...updates }
    }
  }

  return { tasks, loading, fetchTasks, addTask, removeTask, updateTask }
})
```

- [ ] **Step 2: 创建 WebSocket store**

`frontend/src/stores/websocket.ts`:
```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface WsMessage {
  type: 'status_update' | 'progress_update' | 'agent_log' | 'error'
  data: Record<string, unknown>
}

export const useWebSocketStore = defineStore('websocket', () => {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const lastMessage = ref<WsMessage | null>(null)
  const agentLogs = ref<Record<string, unknown>[]>([])

  function connect(taskId: number) {
    disconnect()
    agentLogs.value = []

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/api/ws/tasks/${taskId}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      connected.value = true
    }

    ws.value.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data)
      lastMessage.value = msg

      if (msg.type === 'agent_log') {
        agentLogs.value.push(msg.data)
      }
    }

    ws.value.onclose = () => {
      connected.value = false
    }

    ws.value.onerror = () => {
      connected.value = false
    }
  }

  function disconnect() {
    if (ws.value) {
      ws.value.close()
      ws.value = null
      connected.value = false
    }
  }

  return { ws, connected, lastMessage, agentLogs, connect, disconnect }
})
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/
git commit -m "feat: add Pinia stores for tasks and WebSocket"
```

---

## Task 11: 实现 Sidebar 组件

**Files:**
- Create: `frontend/src/components/Sidebar.vue`

- [ ] **Step 1: 创建 Sidebar 组件**

`frontend/src/components/Sidebar.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'
import { getModels } from '../api/report'
import type { TaskCreateParams } from '../api/task'

const router = useRouter()
const taskStore = useTaskStore()

const form = ref<TaskCreateParams>({
  topic: '',
  description: '',
  model: 'deepseek',
  depth: 'standard',
})

const models = ref<{ id: string; name: string }[]>([])
const submitting = ref(false)

const depthOptions = [
  { value: 'quick', label: '快速（1轮搜索）' },
  { value: 'standard', label: '标准（2-3轮搜索）' },
  { value: 'deep', label: '深度（3-5轮搜索）' },
]

onMounted(async () => {
  await taskStore.fetchTasks()
  try {
    const res = await getModels()
    models.value = res.models
  } catch {
    models.value = [{ id: 'deepseek', name: 'DeepSeek' }]
  }
})

async function handleSubmit() {
  if (!form.value.topic.trim()) return
  submitting.value = true
  try {
    const task = await taskStore.addTask(form.value)
    form.value.topic = ''
    form.value.description = ''
    router.push(`/research/${task.id}`)
  } finally {
    submitting.value = false
  }
}

function goToTask(task: { id: number; status: string }) {
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
</script>

<template>
  <div style="padding: 16px; height: 100%; overflow-y: auto">
    <h2 style="margin: 0 0 16px">🔍 AI 调研平台</h2>

    <el-collapse model-value="form">
      <el-collapse-item title="📝 新建调研" name="form">
        <el-form :model="form" label-position="top" @submit.prevent="handleSubmit">
          <el-form-item label="调研主题">
            <el-input v-model="form.topic" placeholder="例如：2024年中国新能源汽车市场分析" />
          </el-form-item>
          <el-form-item label="补充说明（可选）">
            <el-input v-model="form.description" type="textarea" :rows="2" placeholder="重点关注比亚迪、特斯拉的市占率变化" />
          </el-form-item>
          <el-form-item label="AI 模型">
            <el-select v-model="form.model" style="width: 100%">
              <el-option v-for="m in models" :key="m.id" :label="m.name" :value="m.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="调研深度">
            <el-select v-model="form.depth" style="width: 100%">
              <el-option v-for="d in depthOptions" :key="d.value" :label="d.label" :value="d.value" />
            </el-select>
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit" style="width: 100%">
            开始调研
          </el-button>
        </el-form>
      </el-collapse-item>
    </el-collapse>

    <el-divider />

    <h4>历史调研</h4>
    <div v-if="taskStore.loading" v-loading="true" style="height: 100px" />
    <div v-else-if="taskStore.tasks.length === 0" style="color: var(--el-text-color-secondary)">
      暂无历史调研记录
    </div>
    <div v-else>
      <div
        v-for="task in taskStore.tasks"
        :key="task.id"
        class="task-item"
        @click="goToTask(task)"
      >
        <div class="task-title">
          {{ statusIcons[task.status] || '❓' }}
          {{ task.topic.length > 30 ? task.topic.slice(0, 30) + '...' : task.topic }}
        </div>
        <div class="task-meta">
          {{ depthLabels[task.depth] || task.depth }} |
          {{ new Date(task.created_at).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  margin-bottom: 4px;
}
.task-item:hover {
  background: var(--el-fill-color-light);
}
.task-title {
  font-size: 14px;
  line-height: 1.4;
}
.task-meta {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Sidebar.vue
git commit -m "feat: add Sidebar component with task creation form"
```

---

## Task 12: 实现 AgentTimeline 组件

**Files:**
- Create: `frontend/src/components/AgentTimeline.vue`

- [ ] **Step 1: 创建 AgentTimeline 组件**

`frontend/src/components/AgentTimeline.vue`:
```vue
<script setup lang="ts">
import { computed } from 'vue'

interface LogEntry {
  agent: string
  step: string
  decision?: string
  output?: unknown
}

const props = defineProps<{
  logs: LogEntry[]
  currentStep?: string
}>()

const stepIcons: Record<string, string> = {
  supervisor: '🧠',
  searcher: '🔍',
  crawler: '🕷️',
  evaluator: '📊',
  writer: '✍️',
}

const stepLabels: Record<string, string> = {
  supervisor: '规划搜索策略',
  searcher: '搜索相关信息',
  crawler: '爬取网页内容',
  evaluator: '评估信息充分性',
  writer: '撰写调研报告',
}

const allAgents = ['supervisor', 'searcher', 'crawler', 'evaluator', 'writer']

const completedAgents = computed(() => {
  return new Set(props.logs.map((l) => l.agent))
})

const remainingAgents = computed(() => {
  return allAgents.filter((a) => !completedAgents.value.has(a))
})

const statusInfo = computed(() => {
  const step = props.currentStep || ''
  const map: Record<string, { title: string; desc: string }> = {
    规划: { title: '🤔 规划中', desc: 'Agent 正在制定搜索策略...' },
    搜索: { title: '🔍 搜索中', desc: 'Agent 正在搜索相关信息...' },
    爬取: { title: '🕷️ 爬取中', desc: 'Agent 正在爬取网页内容...' },
    评估: { title: '📊 评估中', desc: 'Agent 正在评估信息充分性...' },
    撰写: { title: '✍️ 撰写中', desc: 'Agent 正在撰写调研报告...' },
    完成: { title: '✅ 已完成', desc: '调研报告已生成！' },
  }
  for (const [key, val] of Object.entries(map)) {
    if (step.includes(key)) return val
  }
  return { title: '🔄 进行中', desc: step }
})

function formatOutput(output: unknown): string {
  if (!output) return ''
  if (typeof output === 'string') return output.slice(0, 500)
  if (Array.isArray(output)) return output.map((i) => `- ${i}`).join('\n')
  return JSON.stringify(output, null, 2).slice(0, 500)
}
</script>

<template>
  <div v-if="!logs.length && !currentStep">
    <el-empty description="Agent 尚未开始工作..." :image-size="60" />
  </div>

  <div v-else>
    <h3>{{ statusInfo.title }}</h3>
    <p style="color: var(--el-text-color-secondary)">{{ statusInfo.desc }}</p>

    <el-divider />

    <h4>📋 执行时间线</h4>
    <el-timeline>
      <el-timeline-item
        v-for="(log, i) in logs"
        :key="i"
        :timestamp="log.step"
        placement="top"
        :hollow="i < logs.length - 1"
      >
        <el-card shadow="never">
          <template #header>
            <span>{{ stepIcons[log.agent] || '⚙️' }} {{ log.step }}</span>
          </template>
          <div v-if="log.decision">
            <strong>决策：</strong>{{ log.decision }}
          </div>
          <div v-if="log.output" style="margin-top: 8px">
            <strong>输出：</strong>
            <pre style="white-space: pre-wrap; font-size: 12px; max-height: 200px; overflow: auto">{{ formatOutput(log.output) }}</pre>
          </div>
        </el-card>
      </el-timeline-item>
    </el-timeline>

    <div v-if="remainingAgents.length && currentStep !== '报告撰写完成'">
      <div v-for="agent in remainingAgents" :key="agent" style="padding: 4px 0; color: var(--el-text-color-secondary)">
        {{ stepIcons[agent] || '⚙️' }} ⏳ {{ stepLabels[agent] || agent }}
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AgentTimeline.vue
git commit -m "feat: add AgentTimeline component with real-time timeline"
```

---

## Task 13: 实现 HomeView 页面

**Files:**
- Create: `frontend/src/views/HomeView.vue`

- [ ] **Step 1: 创建 HomeView**

`frontend/src/views/HomeView.vue`:
```vue
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTaskStore } from '../stores/task'

const router = useRouter()
const taskStore = useTaskStore()

onMounted(() => {
  taskStore.fetchTasks()
})

const statusIcons: Record<string, string> = {
  pending: '⏳',
  planning: '🤔',
  searching: '🔍',
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

function goToTask(task: { id: number; status: string }) {
  if (task.status === 'completed') {
    router.push(`/report/${task.id}`)
  } else {
    router.push(`/research/${task.id}`)
  }
}
</script>

<template>
  <div>
    <h1>🔍 AI 调研平台</h1>
    <p>输入调研主题，AI Agent 将自动搜索、分析、整理，生成结构化调研报告。</p>

    <el-divider />

    <h3>最近调研</h3>
    <div v-if="taskStore.loading" v-loading="true" style="height: 200px" />
    <el-empty v-else-if="taskStore.tasks.length === 0" description="暂无历史调研记录，请在左侧创建新的调研" />
    <el-table v-else :data="taskStore.tasks.slice(0, 10)" @row-click="goToTask" style="cursor: pointer">
      <el-table-column label="状态" width="60">
        <template #default="{ row }">
          {{ statusIcons[row.status] || '❓' }}
        </template>
      </el-table-column>
      <el-table-column prop="topic" label="调研主题" />
      <el-table-column label="深度" width="80">
        <template #default="{ row }">
          {{ depthLabels[row.depth] || row.depth }}
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="140">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/HomeView.vue
git commit -m "feat: add HomeView with task list"
```

---

## Task 14: 实现 ResearchView 页面

**Files:**
- Create: `frontend/src/views/ResearchView.vue`

- [ ] **Step 1: 创建 ResearchView**

`frontend/src/views/ResearchView.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTask, type Task } from '../api/task'
import { useTaskStore } from '../stores/task'
import { useWebSocketStore } from '../stores/websocket'
import AgentTimeline from '../components/AgentTimeline.vue'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()
const wsStore = useWebSocketStore()

const task = ref<Task | null>(null)
const loading = ref(true)

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

async function fetchTask() {
  const id = Number(route.params.id)
  try {
    task.value = await getTask(id)
  } catch {
    router.push('/')
  } finally {
    loading.value = false
  }
}

function connectWs() {
  const id = Number(route.params.id)
  wsStore.connect(id)
}

onMounted(() => {
  fetchTask()
  connectWs()
})

onUnmounted(() => {
  wsStore.disconnect()
})

// Watch for status changes from WebSocket
watch(() => wsStore.lastMessage, (msg) => {
  if (!msg) return
  if (msg.type === 'status_update' && task.value) {
    task.value.status = msg.data.status as string
    task.value.current_step = msg.data.current_step as string || task.value.current_step
    if (msg.data.status === 'completed') {
      router.push(`/report/${task.value.id}`)
    }
  }
  if (msg.type === 'progress_update' && task.value) {
    task.value.progress = msg.data.progress as number
  }
})

// Poll for updates as fallback
let pollTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  pollTimer = setInterval(fetchTask, 5000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div v-loading="loading">
    <div v-if="task">
      <h1>🔍 调研进行中</h1>
      <h2>{{ task.topic }}</h2>
      <p style="color: var(--el-text-color-secondary)">
        模型: {{ task.model }} |
        深度: {{ depthLabels[task.depth] || task.depth }} |
        创建时间: {{ new Date(task.created_at).toLocaleTimeString('zh-CN') }}
      </p>

      <el-progress :percentage="task.progress" :stroke-width="20" striped striped-flow style="margin: 16px 0" />

      <div v-if="task.status === 'completed'" style="text-align: center; margin-top: 32px">
        <el-result icon="success" title="调研完成！">
          <template #extra>
            <el-button type="primary" @click="router.push(`/report/${task.id}`)">📄 查看报告</el-button>
          </template>
        </el-result>
      </div>

      <div v-else-if="task.status === 'failed'">
        <el-result icon="error" :title="`调研失败: ${task.error_message || '未知错误'}`">
          <template #extra>
            <el-button @click="router.push('/')">← 返回首页</el-button>
          </template>
        </el-result>
      </div>

      <div v-else>
        <AgentTimeline :logs="wsStore.agentLogs" :current-step="task.current_step" />
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/ResearchView.vue
git commit -m "feat: add ResearchView with WebSocket real-time updates"
```

---

## Task 15: 实现 ReportView 页面

**Files:**
- Create: `frontend/src/views/ReportView.vue`

- [ ] **Step 1: 创建 ReportView**

`frontend/src/views/ReportView.vue`:
```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { getTask, type Task } from '../api/task'
import { getReport, getSources, getAgentLogs, type Report, type Source, type AgentLog } from '../api/report'

const route = useRoute()
const router = useRouter()
const md = new MarkdownIt()

const task = ref<Task | null>(null)
const report = ref<Report | null>(null)
const sources = ref<Source[]>([])
const logs = ref<AgentLog[]>([])
const loading = ref(true)
const activeTab = ref('report')

const depthLabels: Record<string, string> = {
  quick: '快速',
  standard: '标准',
  deep: '深度',
}

const agentIcons: Record<string, string> = {
  supervisor: '🧠',
  searcher: '🔍',
  crawler: '🕷️',
  evaluator: '📊',
  writer: '✍️',
}

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    task.value = await getTask(id)
    report.value = await getReport(id)
    sources.value = await getSources(id)
    logs.value = await getAgentLogs(id)
  } catch {
    router.push('/')
  } finally {
    loading.value = false
  }
})

function extractToc(content: string): { title: string; level: number }[] {
  const toc: { title: string; level: number }[] = []
  for (const line of content.split('\n')) {
    if (line.startsWith('#')) {
      const level = line.split(' ')[0].length
      if (level <= 4) {
        toc.push({ title: line.replace(/^#+\s*/, ''), level })
      }
    }
  }
  return toc
}

function downloadMarkdown() {
  if (!report.value || !task.value) return
  const blob = new Blob([report.value.content], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `report_${task.value.id}.md`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyToClipboard() {
  if (!report.value) return
  await navigator.clipboard.writeText(report.value.content)
  ElMessage.success('已复制到剪贴板')
}

const sourcesByRound = ref<Record<number, Source[]>>({})
onMounted(() => {
  const grouped: Record<number, Source[]> = {}
  for (const s of sources.value) {
    grouped[s.search_round] = grouped[s.search_round] || []
    grouped[s.search_round].push(s)
  }
  sourcesByRound.value = grouped
})
</script>

<template>
  <div v-loading="loading">
    <div v-if="task">
      <el-row align="middle" style="margin-bottom: 16px">
        <el-col :span="1">
          <el-button @click="router.push('/')" text>←</el-button>
        </el-col>
        <el-col :span="23">
          <h1 style="margin: 0">{{ task.topic }}</h1>
        </el-col>
      </el-row>

      <el-row :gutter="16" style="margin-bottom: 24px">
        <el-col :span="6">
          <el-statistic title="字数" :value="report?.word_count || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="来源数" :value="report?.source_count || 0" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="搜索轮次" :value="task.search_rounds" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="深度" :value="depthLabels[task.depth] || task.depth" />
        </el-col>
      </el-row>

      <el-empty v-if="!report" description="报告尚未生成" />

      <template v-else>
        <el-tabs v-model="activeTab">
          <el-tab-pane label="📄 报告" name="report">
            <el-row :gutter="24">
              <el-col :span="6">
                <h3>目录</h3>
                <div v-for="(item, i) in extractToc(report.content)" :key="i"
                     :style="{ paddingLeft: (item.level - 1) * 16 + 'px', fontSize: '14px', lineHeight: '2' }">
                  {{ item.title }}
                </div>
              </el-col>
              <el-col :span="18">
                <div v-html="md.render(report.content)" class="report-content" />
              </el-col>
            </el-row>

            <el-divider />
            <el-row :gutter="16">
              <el-col :span="8">
                <el-button @click="downloadMarkdown" style="width: 100%">📥 下载 Markdown</el-button>
              </el-col>
              <el-col :span="8">
                <el-button @click="copyToClipboard" style="width: 100%">📋 复制到剪贴板</el-button>
              </el-col>
            </el-row>
          </el-tab-pane>

          <el-tab-pane label="📚 来源" name="sources">
            <div v-if="!sources.length">
              <el-empty description="无来源信息" />
            </div>
            <template v-for="(roundSources, round) in sourcesByRound" :key="round">
              <h4>第 {{ round }} 轮搜索</h4>
              <el-collapse>
                <el-collapse-item
                  v-for="(source, i) in roundSources"
                  :key="source.id"
                  :title="`[${i + 1}] ${source.title || source.url.slice(0, 60)}`"
                >
                  <p><strong>URL：</strong><a :href="source.url" target="_blank">{{ source.url }}</a></p>
                  <p v-if="source.snippet"><strong>摘要：</strong>{{ source.snippet.slice(0, 500) }}</p>
                  <p v-if="source.relevance_score"><strong>相关性：</strong>{{ source.relevance_score.toFixed(2) }}</p>
                </el-collapse-item>
              </el-collapse>
            </template>
          </el-tab-pane>

          <el-tab-pane label="🤖 Agent 日志" name="logs">
            <div v-if="!logs.length">
              <el-empty description="无 Agent 日志" />
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="log in logs"
                :key="log.id"
                :timestamp="new Date(log.timestamp).toLocaleTimeString('zh-CN')"
                placement="top"
              >
                <el-card shadow="never">
                  <template #header>
                    {{ agentIcons[log.agent_name] || '⚙️' }} [{{ log.agent_name }}] {{ log.step }}
                  </template>
                  <p v-if="log.decision"><strong>决策：</strong>{{ log.decision }}</p>
                  <pre v-if="log.output_data" style="white-space: pre-wrap; font-size: 12px">{{ JSON.stringify(log.output_data, null, 2) }}</pre>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </el-tab-pane>
        </el-tabs>
      </template>
    </div>
  </div>
</template>

<style scoped>
.report-content {
  line-height: 1.8;
  font-size: 15px;
}
.report-content h1, .report-content h2, .report-content h3 {
  margin-top: 24px;
  margin-bottom: 12px;
}
.report-content p {
  margin-bottom: 12px;
}
.report-content code {
  background: var(--el-fill-color-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.report-content pre {
  background: var(--el-fill-color-darker);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/ReportView.vue
git commit -m "feat: add ReportView with report content, sources, and logs tabs"
```

---

## Task 16: 删除 Streamlit 代码并清理

**Files:**
- Delete: `app/ui/sidebar.py`, `app/ui/research_page.py`, `app/ui/report_page.py`, `app/ui/agent_visual.py`, `app/ui/__init__.py`, `app/main.py`
- Modify: `requirements.txt`

- [ ] **Step 1: 删除 Streamlit UI 文件**

```bash
rm app/ui/sidebar.py app/ui/research_page.py app/ui/report_page.py app/ui/agent_visual.py app/ui/__init__.py
rm app/main.py
```

- [ ] **Step 2: 更新根目录 requirements.txt**

将 `requirements.txt` 中的 `streamlit>=1.38` 替换为 FastAPI 相关依赖：

```
fastapi>=0.115
uvicorn[standard]>=0.30
websockets>=12.0
langgraph>=0.2
langchain>=0.3
langchain-core>=0.3
openai>=1.0
tavily-python>=0.5
httpx>=0.27
beautifulsoup4>=4.12
sqlalchemy>=2.0
pydantic>=2.0
pydantic-settings>=2.0
python-dotenv>=1.0
```

- [ ] **Step 3: 验证后端可启动**

```bash
cd /Users/allen/IdeaProjects/explore/insight-hub
pip install -r requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Expected: FastAPI 启动成功，访问 http://localhost:8000/docs 可看到 Swagger 文档

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: remove Streamlit code, update dependencies to FastAPI"
```

---

## Task 17: 更新项目文档

**Files:**
- Modify: `README.md`, `.env.example`

- [ ] **Step 1: 更新 README.md**

替换 `README.md` 中的启动命令和架构说明：

```markdown
# AI 调研平台

一个基于多 Agent 协作的自动化调研系统，能够自动搜索、分析、整理信息并生成结构化调研报告。

## 技术栈

- **前端**: Vue 3 + Vite + Element Plus + TypeScript
- **后端**: FastAPI + WebSocket
- **工作流引擎**: LangGraph
- **LLM 框架**: LangChain + LiteLLM
- **搜索 API**: Tavily
- **数据库**: SQLite + SQLAlchemy

## 快速开始

### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

### 3. 启动后端

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端访问 http://localhost:5173，API 文档访问 http://localhost:8000/docs

## 项目结构

```
insight-hub/
├── frontend/          # Vue 3 前端
├── backend/           # FastAPI 后端
│   ├── api/           # REST + WebSocket 路由
│   ├── core/          # 业务逻辑（Agent、工作流、服务）
│   └── schemas/       # Pydantic 数据模型
├── app/               # (已废弃，业务代码已迁移到 backend/)
└── .env
```
```

- [ ] **Step 2: 更新 .env.example**

确认 `.env.example` 包含所有需要的环境变量（当前已包含，无需修改）。

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: update README for Vue 3 + FastAPI architecture"
```

---

## 验证清单

完成后按以下步骤验证：

1. **后端启动**：`uvicorn backend.main:app --reload --port 8000`，访问 http://localhost:8000/docs
2. **前端启动**：`cd frontend && npm run dev`，访问 http://localhost:5173
3. **创建任务**：在左侧表单输入主题，点击"开始调研"
4. **实时进度**：调研页面应显示 Agent 时间线（WebSocket 推送）
5. **查看报告**：完成后自动跳转到报告页，验证 Markdown 渲染、来源列表、日志
6. **历史列表**：首页和侧边栏显示历史任务

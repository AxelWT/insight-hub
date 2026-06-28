# ========== 阶段 1: 构建前端 ==========
# 使用 Node.js 20 Alpine 镜像构建 Vue 前端项目
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

# 先复制依赖声明文件，利用 Docker 缓存层加速构建
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci    # 严格按 lock 文件安装 确保依赖版本一致

# 复制前端源码并构建
COPY frontend/ .
RUN npm run build

# ========== 阶段 2: Python 后端 + 托管前端 ==========
# 使用 Python 3.10 slim 镜像运行 FastAPI 后端
FROM python:3.10-slim

WORKDIR /app

# 安装系统级依赖（build-essential 用于编译 C 扩展，curl 用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*   # 清理 apt 缓存减小镜像体积

# 安装 Playwright 浏览器引擎（Crawl4AI 依赖，用于 JS 渲染页面爬取）
RUN pip install playwright && playwright install --with-deps chromium

# 复制后端依赖声明并安装 Python 包
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制后端源代码
COPY backend/ backend/

# 从前端构建阶段复制构建产物（dist 目录）
COPY --from=frontend-builder /app/frontend/dist frontend/dist

# 创建必要的数据目录
RUN mkdir -p backend/data backend/reports backend/logs

# 设置工作目录为后端代码目录
WORKDIR /app/backend

# 暴露 FastAPI 服务端口
EXPOSE 8003

# 启动命令：先执行数据库迁移，再启动 Web 服务
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8003"]

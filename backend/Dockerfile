# 阶段 1: 构建前端
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# 阶段 2: Python 后端 + 托管前端
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Playwright 依赖
RUN pip install playwright && playwright install --with-deps chromium

# 复制后端依赖并安装
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 复制后端代码
COPY backend/ backend/

# 从构建阶段复制前端产物
COPY --from=frontend-builder /app/frontend/dist frontend/dist

# 复制环境配置
COPY .env* ./

# 创建数据目录
RUN mkdir -p backend/data backend/reports backend/logs

# 设置工作目录
WORKDIR /app/backend

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]

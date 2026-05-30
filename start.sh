#!/bin/bash
# Insight Hub 终端快速启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║         🧠 Insight Hub 启动脚本          ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 检查依赖是否安装
check_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        exit 1
    fi

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js 未安装${NC}"
        exit 1
    fi

    # 检查后端依赖
    if [ ! -d "backend/venv" ] && [ ! -d "backend/__pycache__" ]; then
        echo -e "${YELLOW}⚠️  后端依赖未安装，请先运行 ./setup.sh${NC}"
        exit 1
    fi

    # 检查前端依赖
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "${YELLOW}⚠️  前端依赖未安装，请先运行 ./setup.sh${NC}"
        exit 1
    fi

    # 检查环境配置
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env 配置文件${NC}"
        echo -e "${YELLOW}   请复制 .env.example 并填写 API Key${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ 依赖检查通过${NC}"
}

# 停止已运行的服务
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ 服务已停止${NC}"
    exit 0
}

# 注册清理函数
trap cleanup SIGINT SIGTERM

# 检查依赖
check_dependencies

# 启动后端
echo ""
echo -e "${BLUE}🚀 启动后端服务...${NC}"
cd backend
python -m uvicorn main:app --reload --port 8000 --host 0.0.0.0 &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo -e "${YELLOW}等待后端服务启动...${NC}"
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务已启动${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败，请检查日志${NC}"
    cleanup
fi

# 启动前端
echo ""
echo -e "${BLUE}🚀 启动前端服务...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待前端启动
sleep 3

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✅ 启动成功！                  ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  后端 API:  http://localhost:8000        ║${NC}"
echo -e "${GREEN}║  API 文档:  http://localhost:8000/docs   ║${NC}"
echo -e "${GREEN}║  前端界面:  http://localhost:5173        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 保持脚本运行
wait

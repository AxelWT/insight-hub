#!/bin/bash
# Insight Hub 一键启动脚本（自动检测并安装依赖）
# 使用方法: ./start.sh

set -e

# ========== 颜色定义 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color（重置颜色）

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║         🧠 Insight Hub 启动脚本          ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ========== 检查系统依赖 ==========
check_system_deps() {
    echo -e "${CYAN}📋 检查系统依赖...${NC}"

    # 检查 Python3 是否安装，版本需 3.10+
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        echo "请先安装 Python 3.10+"
        exit 1
    fi
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "  ${GREEN}✓${NC} Python $python_version"

    # 检查 Node.js 是否安装，版本需 18+
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js 未安装${NC}"
        echo "请先安装 Node.js 18+"
        exit 1
    fi
    node_version=$(node --version)
    echo -e "  ${GREEN}✓${NC} Node.js $node_version"

    # 检查 npm 是否安装
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm 未安装${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} npm $(npm --version)"

    echo ""
}

# ========== 检查并创建环境配置 ==========
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env 配置文件${NC}"
        if [ -f ".env.example" ]; then
            # 从示例文件复制创建 .env
            cp .env.example .env
            echo -e "${GREEN}✓ 已从 .env.example 创建 .env${NC}"
            echo -e "${YELLOW}  ⚠️  请编辑 .env 文件填写 API Key 后重新运行${NC}"
            echo ""
            echo "  vim .env"
            exit 0
        else
            echo -e "${RED}❌ 未找到 .env.example 模板文件${NC}"
            exit 1
        fi
    fi
    echo -e "${GREEN}✓ 环境配置文件已存在${NC}"
}

# ========== 安装后端依赖 ==========
install_backend() {
    echo ""
    echo -e "${CYAN}📦 安装后端依赖...${NC}"
    cd backend

    # 安装 Python 依赖包
    echo -e "  安装 Python 包..."
    pip install -r requirements.txt -q

    # 检查并安装 Playwright 浏览器引擎（Crawl4AI 依赖）
    if ! python -c "from playwright.sync_api import sync_playwright; print('ok')" &>/dev/null; then
        echo -e "  安装 Playwright 浏览器..."
        playwright install chromium --with-deps
    else
        echo -e "  ${GREEN}✓${NC} Playwright 已安装"
    fi

    # 创建必要的数据目录
    mkdir -p data reports logs

    cd ..
    echo -e "${GREEN}✓ 后端依赖安装完成${NC}"
}

# ========== 安装前端依赖 ==========
install_frontend() {
    echo ""
    echo -e "${CYAN}📦 安装前端依赖...${NC}"
    cd frontend
    npm install --silent
    cd ..
    echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
}

# ========== 检查并安装依赖 ==========
check_and_install_deps() {
    echo -e "${CYAN}🔍 检查项目依赖...${NC}"

    local need_install=false

    # 检查后端依赖是否已安装（通过 __pycache__ 或 venv 目录判断）
    if [ ! -d "backend/__pycache__" ] && [ ! -d "backend/venv" ]; then
        echo -e "  ${YELLOW}⚠${NC} 后端依赖未安装"
        need_install=true
    else
        echo -e "  ${GREEN}✓${NC} 后端依赖已安装"
    fi

    # 检查前端依赖是否已安装（通过 node_modules 目录判断）
    if [ ! -d "frontend/node_modules" ]; then
        echo -e "  ${YELLOW}⚠${NC} 前端依赖未安装"
        need_install=true
    else
        echo -e "  ${GREEN}✓${NC} 前端依赖已安装"
    fi

    # 交互式确认是否安装
    if [ "$need_install" = true ]; then
        echo ""
        echo -e "${YELLOW}是否自动安装缺失的依赖？(y/n)${NC}"
        read -r answer
        if [[ "$answer" =~ ^[Yy]$ ]] || [[ -z "$answer" ]]; then
            install_backend
            install_frontend
        else
            echo -e "${RED}❌ 依赖未安装，无法启动${NC}"
            exit 1
        fi
    fi

    echo ""
}

# ========== 停止已运行的服务 ==========
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    # 终止后端进程
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    # 终止前端进程
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ 服务已停止${NC}"
    exit 0
}

# 注册清理函数，在 Ctrl+C 时自动停止服务
trap cleanup SIGINT SIGTERM

# ========== 主流程 ==========

# 1. 检查系统依赖（Python、Node.js、npm）
check_system_deps

# 2. 检查环境配置（.env 文件）
check_env

# 3. 检查并安装项目依赖
check_and_install_deps

# 4. 启动后端服务（uvicorn 热重载模式）
echo -e "${BLUE}🚀 启动后端服务...${NC}"
cd backend
python -m uvicorn main:app --reload --port 8003 --host 0.0.0.0 &
BACKEND_PID=$!
cd ..

# 等待后端服务启动
echo -e "${YELLOW}等待后端服务启动...${NC}"
sleep 3

# 健康检查：确认后端是否启动成功
if curl -s http://localhost:8003/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 后端服务已启动${NC}"
else
    echo -e "${RED}❌ 后端服务启动失败，请检查日志${NC}"
    cleanup
fi

# 5. 启动前端开发服务器（Vite 热重载模式）
echo ""
echo -e "${BLUE}🚀 启动前端服务...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# 等待前端服务启动
sleep 3

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✅ 启动成功！                  ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  后端 API:  http://localhost:8003        ║${NC}"
echo -e "${GREEN}║  API 文档:  http://localhost:8003/docs   ║${NC}"
echo -e "${GREEN}║  前端界面:  http://localhost:5173        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 阻塞等待子进程，保持脚本运行
wait

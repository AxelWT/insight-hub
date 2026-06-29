#!/bin/bash
# Insight Hub Docker 快速启动脚本
# 使用方法: ./docker-start.sh [命令]
# 支持命令: up/start(默认), stop, restart, logs, status, build

set -e

# ========== 颜色定义 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║       🐳 Insight Hub Docker 启动         ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ========== 检查 Docker 环境 ==========
check_docker() {
    echo -e "${YELLOW}检查 Docker 环境...${NC}"

    # 检查 Docker 命令是否存在
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker 未安装${NC}"
        echo "请先安装 Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # 检查 Docker Compose 是否可用（支持 v1 和 v2 命令格式）
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose 未安装${NC}"
        exit 1
    fi

    # 检查 Docker 守护进程是否运行
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker 未运行，请启动 Docker Desktop${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Docker 环境检查通过${NC}"
}

# ========== 检查环境配置文件 ==========
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  未找到 .env 配置文件${NC}"
        echo -e "${YELLOW}   请复制 .env.example 并填写 API Key${NC}"
        echo ""
        echo "   cp .env.example .env"
        echo "   vim .env"
        exit 1
    fi
    echo -e "${GREEN}✓ 环境配置检查通过${NC}"
}

# ========== 停止服务 ==========
stop_services() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    # 兼容 v1 (docker-compose) 和 v2 (docker compose) 命令格式
    docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
    echo -e "${GREEN}✓ 服务已停止${NC}"
    exit 0
}

# 注册信号处理，Ctrl+C 时优雅停止
trap stop_services SIGINT SIGTERM

# ========== 前置检查 ==========
check_docker
check_env

# ========== 解析命令行参数 ==========
ACTION=${1:-"up"}  # 默认执行 up（启动服务）

case $ACTION in
    "up"|"start")
        # 启动服务：构建镜像并在后台运行
        echo ""
        echo -e "${BLUE}🚀 启动服务...${NC}"
        docker compose up -d --build 2>/dev/null || docker-compose up -d --build

        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║           ✅ 启动成功！                  ║${NC}"
        echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
        echo -e "${GREEN}║  应用地址:  http://localhost:8003        ║${NC}"
        echo -e "${GREEN}║  API 文档:  http://localhost:8003/docs   ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}常用命令:${NC}"
        echo "  查看日志: docker compose logs -f"
        echo "  停止服务: ./docker-start.sh stop"
        echo "  重启服务: ./docker-start.sh restart"
        ;;

    "stop")
        # 停止所有容器
        stop_services
        ;;

    "restart")
        # 重启：先停止再启动
        echo ""
        echo -e "${BLUE}🔄 重启服务...${NC}"
        docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
        docker compose up -d --build 2>/dev/null || docker-compose up -d --build
        echo -e "${GREEN}✓ 服务已重启${NC}"
        ;;

    "logs")
        # 实时查看容器日志
        docker compose logs -f 2>/dev/null || docker-compose logs -f
        ;;

    "status")
        # 查看容器运行状态
        docker compose ps 2>/dev/null || docker-compose ps
        ;;

    "build")
        # 重新构建镜像（不使用缓存）
        echo ""
        echo -e "${BLUE}🔨 重新构建镜像...${NC}"
        docker compose build --no-cache 2>/dev/null || docker-compose build --no-cache
        echo -e "${GREEN}✓ 构建完成${NC}"
        ;;

    *)
        # 未知命令，显示帮助信息
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  up/start  启动服务（默认）"
        echo "  stop      停止服务"
        echo "  restart   重启服务"
        echo "  logs      查看日志"
        echo "  status    查看状态"
        echo "  build     重新构建镜像"
        exit 1
        ;;
esac

#!/bin/bash
# Insight Hub 手动部署脚本
# 使用方法: ./scripts/deploy.sh

set -e

echo "🚀 Insight Hub 部署脚本"
echo "======================"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 请在项目根目录运行此脚本${NC}"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行${NC}"
    exit 1
fi

# 拉取最新代码
echo -e "${YELLOW}📥 拉取最新代码...${NC}"
git pull origin main

# 停止旧容器
echo -e "${YELLOW}⏹️  停止旧容器...${NC}"
docker compose down

# 重新构建并启动
echo -e "${YELLOW}🔨 构建并启动服务...${NC}"
docker compose up -d --build

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 15

# 检查服务状态
echo -e "${YELLOW}📊 检查服务状态...${NC}"
docker compose ps

# 检查健康状态
echo ""
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务正常${NC}"
else
    echo -e "${RED}⚠️  后端服务可能还在启动中${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           ✅ 部署完成！                  ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  前端: http://your-server-ip             ║${NC}"
echo -e "${GREEN}║  后端: http://your-server-ip:8000        ║${NC}"
echo -e "${GREEN}║  文档: http://your-server-ip:8000/docs   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"

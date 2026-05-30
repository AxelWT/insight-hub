#!/bin/bash
# Insight Hub 服务器初始化脚本
# 使用方法: curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/insight-hub/main/scripts/server-init.sh | bash

set -e

echo "🚀 Insight Hub 服务器初始化"
echo "=========================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 安装 Docker
echo -e "${YELLOW}📦 安装 Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✓ Docker 安装完成${NC}"
else
    echo -e "${GREEN}✓ Docker 已安装${NC}"
fi

# 2. 安装 Docker Compose
echo -e "${YELLOW}📦 安装 Docker Compose...${NC}"
if ! docker compose version &> /dev/null; then
    apt-get update
    apt-get install -y docker-compose-plugin
    echo -e "${GREEN}✓ Docker Compose 安装完成${NC}"
else
    echo -e "${GREEN}✓ Docker Compose 已安装${NC}"
fi

# 3. 安装 Git
echo -e "${YELLOW}📦 安装 Git...${NC}"
if ! command -v git &> /dev/null; then
    apt-get update
    apt-get install -y git
    echo -e "${GREEN}✓ Git 安装完成${NC}"
else
    echo -e "${GREEN}✓ Git 已安装${NC}"
fi

# 4. 创建项目目录
echo -e "${YELLOW}📁 创建项目目录...${NC}"
mkdir -p /opt/insight-hub
cd /opt/insight-hub

# 5. 克隆项目（如果还没有）
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📥 克隆项目...${NC}"
    echo "请输入 Git 仓库地址 (例如: https://github.com/username/insight-hub.git):"
    read -r REPO_URL
    git clone "$REPO_URL" .
    echo -e "${GREEN}✓ 项目克隆完成${NC}"
else
    echo -e "${GREEN}✓ 项目已存在${NC}"
fi

# 6. 配置环境变量
echo -e "${YELLOW}⚙️  配置环境变量...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}请编辑 .env 文件填写 API Key:${NC}"
    echo "vim /opt/insight-hub/.env"
    echo ""
    echo "填写完成后运行: docker compose up -d --build"
else
    echo -e "${GREEN}✓ .env 已存在${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        ✅ 服务器初始化完成！             ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  下一步:                                 ║${NC}"
echo -e "${GREEN}║  1. vim /opt/insight-hub/.env            ║${NC}"
echo -e "${GREEN}║  2. 填写 API Key                         ║${NC}"
echo -e "${GREEN}║  3. docker compose up -d --build         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"

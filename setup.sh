#!/bin/bash
# Insight Hub 项目安装脚本

set -e

echo "🚀 Insight Hub 安装脚本"
echo "========================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"

# 复制环境配置（在根目录）
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ 已创建 .env 配置文件，请填写 API Key"
fi

# 安装后端依赖
echo ""
echo "📦 安装后端依赖..."
cd backend
pip install -r requirements.txt -q

# 安装 Playwright 浏览器
echo "🌐 安装 Playwright 浏览器..."
playwright install chromium --with-deps

# 创建必要目录
echo "📁 创建数据目录..."
mkdir -p data reports logs

cd ..

# 安装前端依赖
echo ""
echo "📦 安装前端依赖..."
cd frontend
npm install
cd ..

echo ""
echo "✅ 安装完成！"
echo ""
echo "================================================"
echo "  启动方式："
echo "  1. 终端启动: ./start.sh"
echo "  2. Docker 启动: ./docker-start.sh"
echo "================================================"

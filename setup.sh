#!/bin/bash
# Insight Hub 项目安装脚本

echo "📦 安装 Python 依赖..."
pip install -r requirements.txt

echo "🌐 安装 Playwright 浏览器..."
playwright install chromium

echo "✅ 安装完成！"
echo ""
echo "启动命令："
echo "  cd backend && python -m uvicorn main:app --reload --port 8000"

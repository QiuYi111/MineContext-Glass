#!/bin/bash
# 测试 Electron 应用启动的简单脚本

echo "🧪 测试 Electron 应用启动..."

# 设置环境变量
export NODE_ENV=development

# 启动 Electron 应用（5秒后自动退出）
timeout 5s npm run electron || echo "Electron 测试完成"
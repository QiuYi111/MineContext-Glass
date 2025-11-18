#!/bin/bash
# 完整的应用测试脚本

echo "🧪 开始测试 MineContext Glass 完整应用..."
echo "📋 测试步骤:"
echo "  1. 启动 Electron 应用"
echo "  2. 检查后端启动"
echo "  3. 检查前端连接"
echo "  4. 验证功能正常"
echo ""

# 设置环境变量
export NODE_ENV=development

# 启动应用（后台运行，10秒后自动检查）
echo "🚀 启动 Electron 应用..."
npm run electron-dev > test-output.log 2>&1 &
APP_PID=$!

# 等待应用启动
echo "⏳ 等待应用启动 (15秒)..."
sleep 15

# 检查输出日志
echo "📊 检查启动日志..."
if grep -q "后端已启动，端口:" test-output.log; then
    echo "✅ 后端启动成功"
    BACKEND_PORT=$(grep "后端已启动，端口:" test-output.log | head -1 | sed 's/.*端口: \([0-9]*\).*/\1/')
    echo "   📍 后端端口: $BACKEND_PORT"
else
    echo "❌ 后端启动失败"
fi

if grep -q "成功连接到前端端口" test-output.log; then
    echo "✅ 前端连接成功"
    FRONTEND_PORT=$(grep "成功连接到前端端口" test-output.log | sed 's/.*端口 \([0-9]*\).*/\1/')
    echo "   📍 前端端口: $FRONTEND_PORT"
else
    echo "❌ 前端连接失败"
fi

# 检查是否有错误
if grep -q "Error\|error\|ERROR" test-output.log | grep -v "Backend:" | head -3; then
    echo "⚠️  发现一些错误，请检查完整日志"
else
    echo "✅ 没有发现明显错误"
fi

echo ""
echo "📄 完整日志保存在: test-output.log"
echo "🛑 停止测试应用..."
kill $APP_PID 2>/dev/null
wait $APP_PID 2>/dev/null

echo "✅ 测试完成！如需手动测试，请运行: npm run electron-dev"
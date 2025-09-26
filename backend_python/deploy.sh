#!/bin/bash

# MoziBang 激活码系统部署脚本

echo "🚀 开始部署 MoziBang 激活码系统..."

# 检查必要文件
echo "📋 检查部署文件..."
required_files=("requirements.txt" "sqlite_activation_api.py" "sqlite_admin_app.py" "runtime.txt")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done

# 检查环境变量
echo "🔧 检查环境变量..."
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  警告: SECRET_KEY 环境变量未设置"
fi

if [ -z "$API_SECRET_KEY" ]; then
    echo "⚠️  警告: API_SECRET_KEY 环境变量未设置"
fi

# 初始化数据库
echo "🗄️  初始化数据库..."
python sqlite_init_database.py

# 检查数据库是否创建成功
if [ ! -f "mozibang_activation.db" ]; then
    echo "❌ 数据库创建失败"
    exit 1
fi

echo "✅ 数据库初始化完成"

# 安装依赖（如果在本地运行）
if [ "$1" = "local" ]; then
    echo "📦 安装Python依赖..."
    pip install -r requirements.txt
    
    echo "🌐 启动本地服务..."
    echo "激活API服务将在端口 5001 启动"
    echo "管理后台将在端口 5000 启动"
    
    # 启动服务
    python sqlite_activation_api.py &
    API_PID=$!
    
    python sqlite_admin_app.py &
    ADMIN_PID=$!
    
    echo "✅ 服务已启动"
    echo "激活API: http://localhost:5001/api"
    echo "管理后台: http://localhost:5000"
    echo ""
    echo "按 Ctrl+C 停止服务"
    
    # 等待中断信号
    trap "echo '🛑 停止服务...'; kill $API_PID $ADMIN_PID; exit" INT
    wait
else
    echo "✅ 部署准备完成"
    echo ""
    echo "📋 部署检查清单:"
    echo "  ✅ 部署文件已准备"
    echo "  ✅ 数据库已初始化"
    echo "  ⚠️  请设置环境变量"
    echo "  ⚠️  请更新Chrome扩展配置"
    echo ""
    echo "🌐 支持的部署平台:"
    echo "  - Railway: railway.toml 已配置"
    echo "  - Vercel: vercel.json 已配置"
    echo "  - Heroku: Procfile 已配置"
    echo ""
    echo "📖 详细部署指南请查看 DEPLOYMENT_GUIDE.md"
fi
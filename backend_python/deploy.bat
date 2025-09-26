@echo off
chcp 65001 >nul

echo 🚀 开始部署 MoziBang 激活码系统...

REM 检查必要文件
echo 📋 检查部署文件...
if not exist "requirements.txt" (
    echo ❌ 缺少必要文件: requirements.txt
    pause
    exit /b 1
)

if not exist "sqlite_activation_api.py" (
    echo ❌ 缺少必要文件: sqlite_activation_api.py
    pause
    exit /b 1
)

if not exist "sqlite_admin_app.py" (
    echo ❌ 缺少必要文件: sqlite_admin_app.py
    pause
    exit /b 1
)

REM 检查环境变量
echo 🔧 检查环境变量...
if "%SECRET_KEY%"=="" (
    echo ⚠️  警告: SECRET_KEY 环境变量未设置
)

if "%API_SECRET_KEY%"=="" (
    echo ⚠️  警告: API_SECRET_KEY 环境变量未设置
)

REM 初始化数据库
echo 🗄️  初始化数据库...
python sqlite_init_database.py

REM 检查数据库是否创建成功
if not exist "mozibang_activation.db" (
    echo ❌ 数据库创建失败
    pause
    exit /b 1
)

echo ✅ 数据库初始化完成

REM 检查是否为本地部署
if "%1"=="local" (
    echo 📦 安装Python依赖...
    pip install -r requirements.txt
    
    echo 🌐 启动本地服务...
    echo 激活API服务将在端口 5001 启动
    echo 管理后台将在端口 5000 启动
    
    REM 启动服务
    start "MoziBang API" python sqlite_activation_api.py
    start "MoziBang Admin" python sqlite_admin_app.py
    
    echo ✅ 服务已启动
    echo 激活API: http://localhost:5001/api
    echo 管理后台: http://localhost:5000
    echo.
    echo 按任意键关闭此窗口...
    pause >nul
) else (
    echo ✅ 部署准备完成
    echo.
    echo 📋 部署检查清单:
    echo   ✅ 部署文件已准备
    echo   ✅ 数据库已初始化
    echo   ⚠️  请设置环境变量
    echo   ⚠️  请更新Chrome扩展配置
    echo.
    echo 🌐 支持的部署平台:
    echo   - Railway: railway.toml 已配置
    echo   - Vercel: vercel.json 已配置
    echo   - Heroku: Procfile 已配置
    echo.
    echo 📖 详细部署指南请查看 DEPLOYMENT_GUIDE.md
    echo.
    echo 按任意键继续...
    pause >nul
)
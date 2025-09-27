# 云端API部署信息

## 🚀 当前部署状态

### Render 部署 ✅ 已完成
- **API服务名称**: mozibang-activation-api
- **API部署URL**: https://mozibang-activation-api.onrender.com
- **API基础地址**: https://mozibang-activation-api.onrender.com/api
- **管理后台服务名称**: mozibang-admin-panel
- **管理后台URL**: https://mozibang-admin-panel.onrender.com
- **部署时间**: 2024年9月26日
- **状态**: 🟢 运行中

## 📋 API端点列表

### 激活码相关
- `GET /api/health` - 健康检查 ✅
- `POST /api/activate` - 激活码验证
- `GET /api/codes` - 获取激活码列表
- `POST /api/revoke_pro` - 撤销Pro激活

### 统计相关
- `GET /api/stats` - 获取统计信息

## 🎛️ 管理后台

### 访问信息
- **云端管理后台**: https://mozibang-admin-panel.onrender.com
- **本地管理后台**: http://localhost:5000 (仅开发环境)
- **默认账号**: admin / admin123

### 功能特性
- 激活码生成和管理
- 用户激活记录查看
- 统计数据分析
- 激活码批量操作

## 🔧 配置更新

### Chrome扩展配置
文件: `activation_config.js`
```javascript
production: {
  render: {
    API_BASE_URL: 'https://mozibang-activation-api.onrender.com/api',
    API_KEY: 'mozibang_api_secret_2024'
  }
}
```

### 当前环境
- 生产环境自动使用Render配置
- 开发环境使用localhost:5001

## 🧪 测试命令

### 健康检查 ✅ 正常
```bash
curl https://mozibang-activation-api.onrender.com/api/health
```

### 激活码验证测试
```bash
curl -X POST https://mozibang-activation-api.onrender.com/api/activate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mozibang_api_secret_2024" \
  -d '{"code": "TEST-CODE-123"}'
```

## 🗄️ 数据库配置

### 测试激活码
- `MOZIBANG-PRO-2024` - Pro激活码
- `TEST-CODE-123` - 测试激活码  
- `DEMO-ACTIVATION` - 演示激活码

### 数据库表结构
- `activation_codes` - 激活码表
- `users` - 用户表

### 自动初始化
- 应用启动时自动创建数据库表
- 自动插入测试激活码数据
- 支持SQLite数据库文件存储

## 📝 部署说明

### Render配置
- 使用 `render.yaml` 配置文件
- 支持多服务部署（API + 管理后台）
- 自动从GitHub仓库部署
- 免费计划支持

### 环境变量
- `PYTHON_VERSION`: 3.9.18
- `FLASK_ENV`: production
- `PORT`: 自动生成

## 🔗 相关链接

- **GitHub仓库**: https://github.com/zhoudada668/mozibang-activation-system
- **API文档**: 查看代码中的端点定义
- **部署指南**: 查看 `DEPLOYMENT_GUIDE.md`
# Railway 部署指南 - MoziBang 激活码系统

## 🎯 为什么选择 Railway？

- ✅ **新手友好** - 界面简洁，操作简单
- ✅ **免费额度** - 每月 $5 免费额度，足够小型项目使用
- ✅ **自动部署** - 连接 GitHub 后自动部署
- ✅ **HTTPS 支持** - 自动提供 HTTPS 域名
- ✅ **数据库支持** - 支持 SQLite 和 PostgreSQL

## 📋 部署前准备

### 1. 检查文件完整性
确保以下文件存在：
- [x] `backend_python/requirements.txt`
- [x] `backend_python/railway.toml`
- [x] `backend_python/sqlite_activation_api.py`
- [x] `backend_python/sqlite_admin_app.py`
- [x] `backend_python/sqlite_init_database.py`
- [x] `backend_python/runtime.txt`

### 2. 准备环境变量
```env
SECRET_KEY=your-secret-key-here
API_SECRET_KEY=your-api-secret-key-here
FLASK_ENV=production
```

## 🚀 详细部署步骤

### 步骤 1: 创建 GitHub 仓库

1. **登录 GitHub**
   - 访问 [github.com](https://github.com)
   - 登录您的账号

2. **创建新仓库**
   - 点击右上角 "+" → "New repository"
   - 仓库名：`mozibang-activation-system`
   - 设为 **Private**（保护API密钥）
   - 不要初始化 README、.gitignore 或 license

3. **上传代码**
   ```bash
   # 在项目根目录 (i:\seatra - 副本备份) 执行
   git init
   git add .
   git commit -m "Initial commit: MoziBang activation system"
   git branch -M main
   git remote add origin https://github.com/您的用户名/mozibang-activation-system.git
   git push -u origin main
   ```

### 步骤 2: Railway 部署

1. **注册 Railway 账号**
   - 访问 [railway.app](https://railway.app)
   - 点击 "Login" → "Login with GitHub"
   - 授权 Railway 访问您的 GitHub

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 找到并选择 `mozibang-activation-system` 仓库
   - 点击 "Deploy Now"

3. **配置根目录**
   - 部署后，进入项目设置
   - 在 "Settings" → "General" 中
   - 设置 "Root Directory" 为 `backend_python`

4. **设置环境变量**
   - 进入 "Variables" 标签
   - 添加以下环境变量：
   ```
   SECRET_KEY = mozibang-secret-key-production-2024
   API_SECRET_KEY = mozibang_api_secret_production_2024
   FLASK_ENV = production
   ```

5. **重新部署**
   - 在 "Deployments" 标签中
   - 点击 "Redeploy" 触发重新部署

### 步骤 3: 获取部署域名

部署成功后：
1. 在 Railway 项目页面找到 "Domains" 部分
2. 复制提供的域名，格式类似：
   `https://mozibang-activation-system-production.up.railway.app`

### 步骤 4: 验证部署

访问以下链接验证部署：
- **API健康检查**: `https://your-domain.up.railway.app/api/health`
- **管理后台**: `https://your-domain.up.railway.app/`

## 🔧 部署后配置

### 1. 更新 Chrome 扩展配置

修改 `activation_config.js` 文件：

```javascript
// 更新生产环境配置
production: {
  railway: {
    API_BASE_URL: 'https://your-actual-domain.up.railway.app/api',
    API_KEY: 'mozibang_api_secret_production_2024'
  }
}
```

### 2. 重新打包 Chrome 扩展

更新配置后，需要：
1. 重新加载 Chrome 扩展
2. 或重新打包并安装扩展

## 🧪 测试部署

### 1. 测试 API 连接
```bash
curl https://your-domain.up.railway.app/api/health
```

预期响应：
```json
{
  "status": "healthy",
  "message": "MoziBang 激活码API运行正常",
  "timestamp": "2024-01-XX..."
}
```

### 2. 测试管理后台
- 访问：`https://your-domain.up.railway.app/`
- 使用默认账号登录：`admin` / `admin123`
- 生成测试激活码

### 3. 测试 Chrome 扩展
- 在扩展中输入生成的激活码
- 验证激活是否成功

## 🔒 安全配置

### 1. 更改默认密码
部署后立即更改管理后台默认密码

### 2. 更新 API 密钥
使用强密码生成器生成新的 API 密钥

### 3. 限制访问来源
在生产环境中配置 CORS 限制

## 📊 监控和维护

### 1. Railway 监控
- 查看部署日志
- 监控资源使用情况
- 设置告警通知

### 2. 数据备份
- 定期导出数据库
- 备份激活码数据

## 💰 成本估算

**Railway 免费额度**：
- $5/月 免费额度
- 包含：500小时运行时间
- 1GB RAM, 1GB 存储

**超出免费额度**：
- $0.000463/GB-hour (RAM)
- $0.25/GB-month (存储)

## 🆘 常见问题

### Q: 部署失败怎么办？
A: 检查 Railway 部署日志，常见问题：
- 缺少 `requirements.txt`
- Python 版本不兼容
- 环境变量未设置

### Q: 数据库文件丢失？
A: Railway 重启可能清空临时文件，建议：
- 使用 Railway PostgreSQL 数据库
- 或定期备份 SQLite 文件

### Q: Chrome 扩展无法连接？
A: 检查：
- API 域名是否正确
- HTTPS 证书是否有效
- CORS 配置是否正确

## 📞 获取帮助

如果遇到问题：
1. 查看 Railway 部署日志
2. 检查环境变量配置
3. 验证 GitHub 代码完整性
4. 联系技术支持

---

**下一步**: 完成部署后，记得更新 Chrome 扩展配置并测试激活功能！
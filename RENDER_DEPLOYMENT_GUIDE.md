# Render 部署指南

## 🚀 使用 Render 部署 Mozibang 激活系统

Render 是一个现代化的云平台，提供免费的 Python 应用部署服务。

### 📋 准备工作

1. **GitHub 仓库已准备** ✅
2. **配置文件已创建** ✅
   - `requirements.txt` - Python 依赖
   - `render.yaml` - Render 配置
   - `runtime.txt` - Python 版本

### 🛠️ 部署步骤

#### 第一步：注册 Render 账户
1. 访问 [render.com](https://render.com)
2. 点击 "Get Started for Free"
3. 使用 GitHub 账户登录

#### 第二步：连接 GitHub 仓库
1. 在 Render Dashboard 点击 "New +"
2. 选择 "Web Service"
3. 连接你的 GitHub 账户
4. 选择 `mozibang-activation-system` 仓库

#### 第三步：配置服务
1. **Name**: `mozibang-activation-api`
2. **Environment**: `Python 3`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python sqlite_activation_api.py`
5. **Plan**: 选择 `Free`

#### 第四步：环境变量设置
- `PYTHON_VERSION`: `3.9.18`
- `PORT`: 由 Render 自动生成

#### 第五步：部署
1. 点击 "Create Web Service"
2. 等待构建和部署完成（约 2-5 分钟）
3. 获取部署 URL

### 🔧 配置文件说明

#### `render.yaml`
```yaml
services:
  - type: web
    name: mozibang-activation-api
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python sqlite_activation_api.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.9.18
      - key: PORT
        generateValue: true
```

#### `requirements.txt`
```
Flask==2.3.3
Flask-CORS==4.0.0
gunicorn==21.2.0
```

#### `runtime.txt`
```
python-3.9.18
```

### 📊 部署后验证

部署成功后，你会获得一个 URL，格式如：
```
https://mozibang-activation-api.onrender.com
```

测试 API 端点：
- `GET /health` - 健康检查
- `POST /activate` - 激活码验证
- `GET /codes` - 获取激活码列表

### 🔄 自动部署

配置完成后，每次推送到 GitHub 主分支，Render 会自动重新部署。

### 💡 优势

- ✅ **免费额度**: 每月 750 小时
- ✅ **自动 HTTPS**: 免费 SSL 证书
- ✅ **全球 CDN**: 快速访问
- ✅ **自动部署**: GitHub 集成
- ✅ **监控日志**: 内置监控

### 🚨 注意事项

1. **冷启动**: 免费服务在无活动时会休眠，首次访问可能较慢
2. **数据持久化**: SQLite 文件在重启时会重置，生产环境建议使用 PostgreSQL
3. **资源限制**: 免费计划有 CPU 和内存限制

### 📞 技术支持

如遇问题，可查看：
- Render 部署日志
- GitHub Actions 状态
- 本地测试结果

---

**下一步**: 部署完成后，更新 Chrome 扩展配置指向新的 API 地址。
# MoziBang 激活码系统部署指南

## 概述

MoziBang Chrome扩展的激活码系统需要部署到云端，以便用户可以在任何地方激活和验证Pro状态。本指南提供了多种部署方案。

## 系统架构

```
Chrome扩展 → 云端API服务 → 数据库
```

### 核心组件
1. **激活API服务** (`sqlite_activation_api.py`) - 处理激活码验证和Pro状态管理
2. **管理后台** (`sqlite_admin_app.py`) - 生成和管理激活码
3. **SQLite数据库** (`mozibang_activation.db`) - 存储激活码和用户数据

## 推荐部署方案

### 方案1: Railway (推荐)
**优势**: 简单易用，支持Python，免费额度充足

1. **准备部署文件**
   ```bash
   # requirements.txt
   Flask==2.3.3
   Flask-CORS==4.0.0
   
   # railway.toml
   [build]
   builder = "NIXPACKS"
   
   [deploy]
   startCommand = "python sqlite_activation_api.py"
   ```

2. **环境变量配置**
   ```
   FLASK_ENV=production
   API_SECRET_KEY=your_secure_api_key_here
   ADMIN_PASSWORD=your_secure_admin_password
   ```

3. **部署步骤**
   - 注册 Railway 账号
   - 连接 GitHub 仓库
   - 配置环境变量
   - 自动部署

### 方案2: Vercel
**优势**: 全球CDN，免费额度，适合API服务

1. **配置文件** (`vercel.json`)
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "sqlite_activation_api.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "sqlite_activation_api.py"
       }
     ]
   }
   ```

### 方案3: Heroku
**优势**: 成熟稳定，支持PostgreSQL

1. **配置文件**
   ```
   # Procfile
   web: python sqlite_activation_api.py
   
   # runtime.txt
   python-3.11.0
   ```

### 方案4: 阿里云/腾讯云服务器
**优势**: 国内访问速度快，完全控制

## 数据库选择

### 开发/小规模部署
- **SQLite** - 当前使用，适合小规模用户
- 优势: 零配置，文件存储
- 限制: 并发性能有限

### 生产环境推荐
- **PostgreSQL** (推荐)
- **MySQL**
- 优势: 更好的并发性能和数据完整性

## 部署前准备

### 1. 安全配置
```python
# 生产环境配置
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    API_SECRET_KEY = os.environ.get('API_SECRET_KEY') or 'your-api-secret'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///activation.db'
    DEBUG = False
    CORS_ORIGINS = ['chrome-extension://*']  # 限制CORS来源
```

### 2. 环境变量
```bash
# 必需的环境变量
SECRET_KEY=your_flask_secret_key
API_SECRET_KEY=your_api_secret_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password
DATABASE_URL=your_database_url
```

### 3. 数据库迁移
如果从SQLite迁移到PostgreSQL:
```python
# 数据迁移脚本
import sqlite3
import psycopg2

def migrate_data():
    # 从SQLite导出数据
    # 导入到PostgreSQL
    pass
```

## Chrome扩展配置更新

部署完成后，需要更新扩展中的API配置:

```javascript
// activation.js
window.ActivationManager = {
  // 更新为云端API地址
  API_BASE_URL: 'https://your-domain.com/api',  // 替换localhost
  API_KEY: 'your_production_api_key',
  
  // 其他配置保持不变
};
```

## 监控和维护

### 1. 日志监控
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
```

### 2. 健康检查
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### 3. 备份策略
- 定期备份数据库
- 监控API响应时间
- 设置错误告警

## 成本估算

### Railway (推荐新手)
- 免费额度: $5/月
- 付费计划: $5-20/月

### Vercel
- 免费额度: 充足的API调用
- 付费计划: $20/月起

### 云服务器
- 阿里云ECS: ¥100-300/月
- 腾讯云CVM: ¥100-300/月

## 部署检查清单

- [ ] 准备部署配置文件
- [ ] 设置环境变量
- [ ] 配置数据库
- [ ] 部署API服务
- [ ] 部署管理后台
- [ ] 更新Chrome扩展配置
- [ ] 测试激活流程
- [ ] 设置监控和备份

## 下一步

1. 选择部署平台
2. 准备部署文件
3. 配置环境变量
4. 执行部署
5. 更新扩展配置
6. 全面测试

需要帮助选择具体的部署方案吗？
# 🚀 快速部署指南 - 5分钟上线

## 📋 部署清单

- [x] ✅ 所有部署文件已准备完成
- [x] ✅ Chrome扩展配置已更新
- [ ] ⏳ 创建GitHub仓库
- [ ] ⏳ 部署到Railway
- [ ] ⏳ 测试激活功能

## 🎯 第一步：创建GitHub仓库

### 方法一：通过GitHub网站（推荐）

1. **访问GitHub**：https://github.com
2. **创建仓库**：
   - 点击右上角 "+" → "New repository"
   - 仓库名：`mozibang-activation-system`
   - 设为 **Private**（重要：保护API密钥）
   - 不要勾选任何初始化选项
   - 点击 "Create repository"

3. **上传代码**：
   - 下载并安装 [Git](https://git-scm.com/download/win)
   - 在项目根目录打开命令行
   - 执行以下命令：

```bash
# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交代码
git commit -m "Initial commit: MoziBang activation system"

# 设置主分支
git branch -M main

# 添加远程仓库（替换YOUR_USERNAME为您的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/mozibang-activation-system.git

# 推送代码
git push -u origin main
```

### 方法二：使用GitHub Desktop（简单）

1. 下载 [GitHub Desktop](https://desktop.github.com/)
2. 登录GitHub账号
3. 点击 "File" → "New repository"
4. 选择项目文件夹并发布

## 🚂 第二步：部署到Railway

### 1. 注册Railway账号
- 访问：https://railway.app
- 点击 "Login" → "Login with GitHub"
- 授权Railway访问您的GitHub

### 2. 创建项目
- 点击 "New Project"
- 选择 "Deploy from GitHub repo"
- 选择 `mozibang-activation-system` 仓库
- 点击 "Deploy Now"

### 3. 配置项目
**设置根目录**：
- 进入项目 → "Settings" → "General"
- 设置 "Root Directory" 为 `backend_python`

**添加环境变量**：
- 进入 "Variables" 标签
- 添加以下变量：

```
SECRET_KEY = mozibang-secret-key-production-2024
API_SECRET_KEY = mozibang_api_secret_production_2024
FLASK_ENV = production
```

### 4. 重新部署
- 进入 "Deployments" 标签
- 点击 "Redeploy"

### 5. 获取域名
- 部署成功后，在 "Domains" 部分复制域名
- 格式：`https://your-app-name.up.railway.app`

## 🔧 第三步：更新Chrome扩展

### 1. 修改配置文件
打开 `activation_config.js`，找到第32行：

```javascript
// 将这行：
return this.production.railway; // 默认使用Railway配置

// 修改railway配置中的域名：
railway: {
  API_BASE_URL: 'https://your-actual-domain.up.railway.app/api',
  API_KEY: 'mozibang_api_secret_production_2024'
}
```

### 2. 重新加载扩展
- 打开Chrome → 扩展程序管理
- 找到MoziBang扩展
- 点击刷新按钮

## 🧪 第四步：测试功能

### 1. 测试API连接
在浏览器访问：
```
https://your-domain.up.railway.app/api/health
```

应该看到：
```json
{
  "status": "healthy",
  "message": "MoziBang 激活码API运行正常"
}
```

### 2. 测试管理后台
访问：`https://your-domain.up.railway.app/`
- 用户名：`admin`
- 密码：`admin123`

### 3. 生成激活码
- 登录管理后台
- 进入"生成激活码"页面
- 生成一个终身激活码

### 4. 测试Chrome扩展
- 打开Chrome扩展
- 点击"激活码"按钮
- 输入刚生成的激活码
- 验证激活是否成功

## ✅ 完成！

恭喜！您的MoziBang激活码系统已成功部署到云端。

## 🔒 安全提醒

**立即执行**：
1. 更改管理后台默认密码
2. 备份激活码数据
3. 定期检查系统日志

## 📞 需要帮助？

如果遇到问题：
1. 检查Railway部署日志
2. 验证环境变量设置
3. 确认GitHub代码已正确上传
4. 查看详细部署指南：`RAILWAY_DEPLOYMENT_GUIDE.md`

---

**预计总时间**：5-10分钟
**成本**：免费（Railway免费额度）
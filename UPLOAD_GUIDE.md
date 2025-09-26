# 📋 本地克隆上传详细步骤指南

## 🚨 网络问题解决方案

### 问题：`fatal: unable to access` 或 `Recv failure: Connection was reset`

这是访问GitHub的网络连接问题，常见于中国大陆。以下是解决方案：

#### 方案1：使用GitHub镜像站（推荐）
```bash
# 使用GitHub镜像克隆
git clone https://github.com.cnpmjs.org/zhoudada668/mozibang-activation-system.git

# 或者使用另一个镜像
git clone https://hub.fastgit.xyz/zhoudada668/mozibang-activation-system.git
```

#### 方案2：修改Git配置
```bash
# 取消Git的SSL验证
git config --global http.sslVerify false

# 设置代理（如果您有代理）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy https://127.0.0.1:7890
```

#### 方案3：使用SSH方式（需要配置SSH密钥）
```bash
git clone git@github.com:zhoudada668/mozibang-activation-system.git
```

#### 方案4：直接下载ZIP文件
1. 访问：https://github.com/zhoudada668/mozibang-activation-system
2. 点击绿色的"Code"按钮
3. 选择"Download ZIP"
4. 解压到 `F:\mozibang-activation-system\`

---

## 🎯 方法1：本地克隆上传（修正版）

### 第一步：克隆GitHub仓库到本地

1. **选择目录**
   ```bash
   cd F:\
   ```

2. **尝试克隆**（按优先级尝试）
   ```bash
   # 方案1：使用镜像站
   git clone https://github.com.cnpmjs.org/zhoudada668/mozibang-activation-system.git
   
   # 如果失败，尝试方案2
   git clone https://hub.fastgit.xyz/zhoudada668/mozibang-activation-system.git
   
   # 如果还是失败，使用方案4下载ZIP
   ```

3. **进入文件夹**
   ```bash
   cd mozibang-activation-system
   ```

### 第二步：复制核心文件到克隆文件夹

**需要复制的文件清单：**

#### 🔥 核心必需文件
```
从 i:\seatra - 副本备份\ 复制到 F:\mozibang-activation-system\

✅ backend_python\          # 整个文件夹
✅ manifest.json            # Chrome扩展配置
✅ activation_config.js     # 激活码配置
✅ popup.html              # 扩展弹窗
✅ popup.js                # 扩展弹窗逻辑
✅ background.js           # 扩展后台脚本
✅ content.js              # 内容脚本
✅ images\                 # 图标文件夹
✅ .gitignore              # Git忽略文件
✅ QUICK_DEPLOY.md         # 快速部署指南
✅ RAILWAY_DEPLOYMENT_GUIDE.md  # Railway部署指南
✅ CLOUD_DEPLOYMENT_SUMMARY.md # 部署总结
```

#### 📁 复制操作步骤
1. **打开两个文件管理器窗口**
   - 窗口1：`i:\seatra - 副本备份\`
   - 窗口2：`F:\mozibang-activation-system\`

2. **逐个复制文件**
   - 选中上述文件和文件夹
   - 拖拽或复制粘贴到克隆文件夹

### 第三步：提交并推送到GitHub

1. **在克隆文件夹中打开PowerShell**
   ```bash
   cd F:\mozibang-activation-system
   ```

2. **配置Git用户信息**（如果还没配置）
   ```bash
   git config user.name "zhoudada668"
   git config user.email "13573875365@163.com"
   ```

3. **添加所有文件**
   ```bash
   git add .
   ```

4. **提交更改**
   ```bash
   git commit -m "Add MoziBang activation system files"
   ```

5. **推送到GitHub**（可能需要多次尝试）
   ```bash
   # 如果使用镜像克隆的，需要修改远程地址
   git remote set-url origin https://github.com/zhoudada668/mozibang-activation-system.git
   
   # 推送
   git push origin main
   
   # 如果推送失败，尝试强制推送
   git push -f origin main
   ```

### 第四步：验证上传成功

1. **访问GitHub仓库**
   ```
   https://github.com/zhoudada668/mozibang-activation-system
   ```

2. **检查文件是否都已上传**
   - backend_python 文件夹
   - manifest.json
   - 所有Chrome扩展文件

## 🚨 注意事项

1. **网络问题**：
   - 如果克隆失败，优先使用镜像站
   - 推送时可能需要多次尝试
   - 考虑使用VPN或代理

2. **不要复制的文件**：
   - `backend\` 文件夹（旧版本）
   - `license.js`、`payment.js`、`secure-data.js`
   - `activation.js`（如果有重复功能）

3. **确保文件完整性**：
   - `backend_python\requirements.txt` 必须存在
   - `backend_python\Procfile` 必须存在
   - `backend_python\railway.toml` 必须存在

## 🎉 完成后的下一步

上传成功后，立即进行Railway部署：
1. 访问 railway.app
2. 连接GitHub仓库
3. 配置环境变量
4. 部署完成！

---
**预计完成时间：15-20分钟（包含网络问题处理时间）**
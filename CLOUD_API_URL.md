# 云端API部署信息

## 🚀 当前部署状态

### Render 部署 ✅ 已完成
- **服务名称**: mozibang-activation-api
- **部署URL**: https://mozibang-activation-api.onrender.com
- **API基础地址**: https://mozibang-activation-api.onrender.com/api
- **部署时间**: 2024年9月26日
- **状态**: 🟢 运行中

## 📋 API端点列表

### 激活码相关
- `GET /api/health` - 健康检查
- `POST /api/activate` - 激活码验证
- `GET /api/codes` - 获取激活码列表
- `POST /api/revoke_pro` - 撤销Pro激活

### 统计相关
- `GET /api/stats` - 获取统计信息

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

### 健康检查
```bash
curl https://mozibang-activation-api.onrender.com/api/health
```

### 激活码验证测试
```bash
curl -X POST https://mozibang-activation-api.onrender.com/api/activate \
  -H "Content-Type: application/json" \
  -d '{"code": "TEST-CODE-123"}'
```

## ⚠️ 注意事项

1. **冷启动**: 免费服务在无活动时会休眠，首次访问可能需要30秒启动
2. **数据持久化**: SQLite数据库在服务重启时会重置
3. **API密钥**: 生产环境使用相同的API密钥进行验证

## 📊 监控

- **Render控制台**: https://dashboard.render.com
- **实时日志**: 可在Render控制台查看
- **服务状态**: 24/7监控

---

**更新时间**: 2024年9月26日 20:43
**下一步**: 测试Chrome扩展与云端API的集成
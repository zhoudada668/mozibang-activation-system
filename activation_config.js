// MoziBang 激活码系统 - 云端部署配置
// 部署后需要更新这些配置

window.ActivationConfig = {
  // 开发环境配置
  development: {
    API_BASE_URL: 'http://localhost:5001/api',
    API_KEY: 'mozibang_api_secret_2024'
  },
  
  // 生产环境配置 - 部署后需要更新
  production: {
    // Render 部署 - 当前使用
    render: {
      API_BASE_URL: 'https://mozibang-activation-api.onrender.com/api',
      API_KEY: 'mozibang_api_secret_2024'
    },
    
    // Railway 部署示例
    railway: {
      API_BASE_URL: 'https://your-app-name.up.railway.app/api',
      API_KEY: 'your_production_api_key'
    },
    
    // Vercel 部署示例
    vercel: {
      API_BASE_URL: 'https://your-app-name.vercel.app/api',
      API_KEY: 'your_production_api_key'
    },
    
    // Heroku 部署示例
    heroku: {
      API_BASE_URL: 'https://your-app-name.herokuapp.com/api',
      API_KEY: 'your_production_api_key'
    },
    
    // 自定义域名
    custom: {
      API_BASE_URL: 'https://api.yourdomain.com/api',
      API_KEY: 'your_production_api_key'
    }
  },
  
  // 获取当前环境配置
  getCurrentConfig() {
    // 检测是否为生产环境
    const isProduction = !window.location.href.includes('localhost') && 
                        !window.location.href.includes('127.0.0.1');
    
    if (isProduction) {
      // 生产环境 - 根据需要选择部署平台
      // 部署后请修改这里选择正确的配置
      return this.production.render; // 当前使用Render配置
    } else {
      // 开发环境
      return this.development;
    }
  }
};

// 更新 ActivationManager 的配置
if (window.ActivationManager) {
  const config = window.ActivationConfig.getCurrentConfig();
  window.ActivationManager.API_BASE_URL = config.API_BASE_URL;
  window.ActivationManager.API_KEY = config.API_KEY;
  
  console.log('激活码API配置已更新:', config);
}

console.log('激活码配置管理器已加载');
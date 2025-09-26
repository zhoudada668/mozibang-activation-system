// 支付环境配置
window.paymentConfig = {
  // 🚨 重要：上架前需要修改这些配�?
  
  // 生产环境扩展ID（Chrome Web Store发布后获得）
  productionExtensionIds: [
    'your_production_extension_id_here', // 替换为你的正式扩展ID
    // 如果有多个版本可以添加多个ID
  ],
  
  // 开发环境配�?
  development: {
    // 使用模拟支付
    useRealPayment: false,
    
    // 本地测试服务器（如果需要）
    serverUrl: 'http://localhost:3000/api',
    
    // 模拟支付延迟（毫秒）
    simulatedDelay: 1500,
    
    // 模拟支付成功率（0-1�?
    simulatedSuccessRate: 1.0
  },
  
  // 生产环境配置
  production: {
    // 使用真实支付
    useRealPayment: true,
    
    // 后端服务器地址 - 部署后替换为你的Vercel地址
    serverUrl: 'https://mozibang-backend-你的用户�?vercel.app/api',
    
    // Chrome Web Store内购配置
    chromeWebStore: {
      itemId: 'your_chrome_store_item_id', // 在Chrome Developer Dashboard中配�?
      enabled: true
    },
    
    // 支付宝配�?
    alipay: {
      appId: 'your_alipay_app_id',
      enabled: true,
      sandboxMode: false // 生产环境设为false
    },
    
    // 微信支付配置（可选）
    wechatPay: {
      appId: 'your_wechat_app_id',
      enabled: false
    }
  },
  
  // 通用配置
  common: {
    // Pro版本价格
    proPrice: 9.9,
    proPriceCents: 990, // 以分为单�?
    
    // 货币
    currency: 'CNY',
    
    // 产品信息
    productName: 'SeaTra Pro�?,
    productDescription: '一次付费，终身使用所有高级功�?,
    
    // 支付超时时间（分钟）
    paymentTimeout: 15,
    
    // 自动更新UI延迟（毫秒）
    uiUpdateDelay: 100,
    
    // 成功通知显示时间（毫秒）
    notificationDisplayTime: 3000
  }
};

// 获取当前环境配置
window.getCurrentPaymentConfig = function() {
  const extensionId = chrome.runtime.id;
  const isProduction = window.paymentConfig.productionExtensionIds.includes(extensionId);
  
  if (isProduction) {
    return {
      ...window.paymentConfig.common,
      ...window.paymentConfig.production,
      environment: 'production'
    };
  } else {
    return {
      ...window.paymentConfig.common,
      ...window.paymentConfig.development,
      environment: 'development'
    };
  }
};

// 检查当前环�?
window.checkPaymentEnvironment = function() {
  const config = window.getCurrentPaymentConfig();
  
  console.log(`🔧 当前支付环境: ${config.environment}`);
  console.log(`💳 使用真实支付: ${config.useRealPayment}`);
  console.log(`🏪 Chrome Web Store: ${config.chromeWebStore?.enabled ? '启用' : '禁用'}`);
  console.log(`💰 支付�? ${config.alipay?.enabled ? '启用' : '禁用'}`);
  
  return config;
};

console.log('💳 支付配置已加�?);

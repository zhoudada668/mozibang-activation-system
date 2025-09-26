// MoziBang 激活码管理系统
window.ActivationManager = {
  // API配置
  API_BASE_URL: 'http://localhost:5001/api',
  API_KEY: 'mozibang_api_secret_2024',
  
  // 激活码验证和激活
  async activateCode(activationCode, userEmail, userName = '') {
    try {
      console.log('开始激活码验证:', { activationCode, userEmail });
      
      const response = await fetch(`${this.API_BASE_URL}/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.API_KEY
        },
        body: JSON.stringify({
          activation_code: activationCode.trim(),
          user_email: userEmail,
          user_name: userName
        })
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        // 激活成功，保存Pro状态到本地存储
        const proData = {
          isPro: true,
          plan: result.data.pro_type,
          activatedAt: result.data.activated_at,
          expiresAt: result.data.expires_at,
          isLifetime: result.data.is_lifetime,
          activationCode: activationCode,
          userToken: result.data.user_token
        };
        
        await chrome.storage.local.set({ 
          proStatus: proData,
          activationData: result.data
        });
        
        console.log('激活成功，Pro状态已保存:', proData);
        
        return {
          success: true,
          message: '激活成功！您已升级为Pro用户',
          data: result.data
        };
      } else {
        console.error('激活失败:', result);
        return {
          success: false,
          message: this.getErrorMessage(result.code, result.error),
          code: result.code
        };
      }
    } catch (error) {
      console.error('激活码验证网络错误:', error);
      return {
        success: false,
        message: '网络连接失败，请检查网络后重试',
        code: 'NETWORK_ERROR'
      };
    }
  },
  
  // 验证Pro状态
  async verifyProStatus(userEmail) {
    try {
      const response = await fetch(`${this.API_BASE_URL}/verify-pro`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.API_KEY
        },
        body: JSON.stringify({
          user_email: userEmail
        })
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        // 更新本地Pro状态
        if (result.data.is_pro) {
          const proData = {
            isPro: true,
            plan: result.data.pro_type,
            activatedAt: result.data.activated_at,
            expiresAt: result.data.expires_at,
            isLifetime: result.data.is_lifetime,
            activationCode: result.data.activation_code_used,
            lastLogin: result.data.last_login
          };
          
          await chrome.storage.local.set({ proStatus: proData });
        } else {
          // 清除本地Pro状态
          await chrome.storage.local.remove(['proStatus', 'activationData']);
        }
        
        return {
          success: true,
          data: result.data
        };
      } else {
        console.error('Pro状态验证失败:', result);
        return {
          success: false,
          message: '状态验证失败',
          code: result.code
        };
      }
    } catch (error) {
      console.error('Pro状态验证网络错误:', error);
      return {
        success: false,
        message: '网络连接失败',
        code: 'NETWORK_ERROR'
      };
    }
  },
  
  // 获取本地Pro状态
  async getLocalProStatus() {
    try {
      const result = await chrome.storage.local.get(['proStatus', 'activationData']);
      const proData = result.proStatus;
      
      if (!proData || !proData.isPro) {
        return {
          isPro: false,
          plan: 'free',
          message: '免费版本'
        };
      }
      
      // 检查是否过期（非永久版本）
      if (proData.expiresAt && new Date(proData.expiresAt) < new Date()) {
        // 已过期，清除Pro状态
        await chrome.storage.local.remove(['proStatus', 'activationData']);
        return {
          isPro: false,
          plan: 'free',
          message: 'Pro版本已过期'
        };
      }
      
      return {
        isPro: true,
        plan: proData.plan,
        activatedAt: proData.activatedAt,
        expiresAt: proData.expiresAt,
        isLifetime: proData.isLifetime,
        activationCode: proData.activationCode,
        message: proData.isLifetime ? 'Pro版本 (永久有效)' : `Pro版本 (到期: ${new Date(proData.expiresAt).toLocaleDateString()})`
      };
    } catch (error) {
      console.error('获取本地Pro状态失败:', error);
      return {
        isPro: false,
        plan: 'free',
        message: '免费版本'
      };
    }
  },
  
  // 清除Pro状态
  async clearProStatus() {
    try {
      await chrome.storage.local.remove(['proStatus', 'activationData']);
      console.log('Pro状态已清除');
      return true;
    } catch (error) {
      console.error('清除Pro状态失败:', error);
      return false;
    }
  },
  
  // 获取错误消息
  getErrorMessage(code, defaultMessage) {
    const errorMessages = {
      'INVALID_CODE': '激活码无效或不存在',
      'CODE_ALREADY_USED': '激活码已被使用',
      'CODE_EXPIRED': '激活码已过期',
      'INVALID_CODE_TYPE': '激活码类型无效',
      'MISSING_REQUIRED_FIELDS': '请输入完整的激活码和邮箱',
      'DB_CONNECTION_ERROR': '服务器连接失败，请稍后重试',
      'ACTIVATION_ERROR': '激活过程中发生错误，请重试',
      'NETWORK_ERROR': '网络连接失败，请检查网络后重试',
      'INVALID_API_KEY': 'API密钥无效',
      'INTERNAL_ERROR': '服务器内部错误，请联系技术支持'
    };
    
    return errorMessages[code] || defaultMessage || '未知错误';
  },
  
  // 显示激活码弹窗
  showActivationModal() {
    const modal = document.getElementById('activationModal');
    if (modal) {
      modal.style.display = 'flex';
      
      // 清空之前的输入和状态
      const input = document.getElementById('activationCodeInput');
      const status = document.getElementById('activationStatus');
      if (input) input.value = '';
      if (status) {
        status.className = 'activation-status';
        status.textContent = '';
      }
      
      // 聚焦到输入框
      setTimeout(() => {
        if (input) input.focus();
      }, 100);
    }
  },
  
  // 隐藏激活码弹窗
  hideActivationModal() {
    const modal = document.getElementById('activationModal');
    if (modal) {
      modal.style.display = 'none';
    }
  },
  
  // 显示激活状态
  showActivationStatus(message, type = 'info') {
    const status = document.getElementById('activationStatus');
    if (status) {
      status.className = `activation-status ${type}`;
      status.textContent = message;
    }
  },
  
  // 初始化激活码相关事件
  initActivationEvents() {
    // 激活码按钮点击事件
    const activationBtn = document.getElementById('activationBtn');
    if (activationBtn) {
      activationBtn.addEventListener('click', () => {
        this.showActivationModal();
      });
    }
    
    // 关闭弹窗按钮
    const closeBtn = document.getElementById('closeActivationModal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        this.hideActivationModal();
      });
    }
    
    // 点击弹窗外部关闭
    const modal = document.getElementById('activationModal');
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.hideActivationModal();
        }
      });
    }
    
    // 激活按钮点击事件
    const activateBtn = document.getElementById('activateBtn');
    if (activateBtn) {
      activateBtn.addEventListener('click', async () => {
        await this.handleActivation();
      });
    }
    
    // 输入框回车事件
    const input = document.getElementById('activationCodeInput');
    if (input) {
      input.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
          await this.handleActivation();
        }
      });
      
      // 输入时清除状态消息
      input.addEventListener('input', () => {
        const status = document.getElementById('activationStatus');
        if (status) {
          status.className = 'activation-status';
          status.textContent = '';
        }
      });
    }
  },
  
  // 处理激活
  async handleActivation() {
    const input = document.getElementById('activationCodeInput');
    const activateBtn = document.getElementById('activateBtn');
    
    if (!input || !activateBtn) return;
    
    const activationCode = input.value.trim();
    
    if (!activationCode) {
      this.showActivationStatus('请输入激活码', 'error');
      return;
    }
    
    // 获取用户邮箱
    let userEmail = '';
    let userName = '';
    
    try {
      // 从认证状态获取用户信息
      if (window.userProfile && window.userProfile.email) {
        userEmail = window.userProfile.email;
        userName = window.userProfile.name || '';
      } else {
        // 尝试从存储获取
        const authResult = await chrome.storage.local.get('authToken');
        if (authResult.authToken && authResult.authToken.email) {
          userEmail = authResult.authToken.email;
          userName = authResult.authToken.name || '';
        }
      }
      
      if (!userEmail) {
        this.showActivationStatus('请先登录Google账号', 'error');
        return;
      }
    } catch (error) {
      console.error('获取用户信息失败:', error);
      this.showActivationStatus('获取用户信息失败，请重新登录', 'error');
      return;
    }
    
    // 禁用按钮，显示加载状态
    activateBtn.disabled = true;
    activateBtn.textContent = '激活中...';
    this.showActivationStatus('正在验证激活码，请稍候...', 'loading');
    
    try {
      // 调用激活API
      const result = await this.activateCode(activationCode, userEmail, userName);
      
      if (result.success) {
        this.showActivationStatus(result.message, 'success');
        
        // 延迟关闭弹窗并刷新UI
        setTimeout(() => {
          this.hideActivationModal();
          
          // 刷新UI状态
          if (window.updateUIStatus) {
            window.updateUIStatus();
          }
          
          // 显示成功提示
          if (window.showNotification) {
            window.showNotification('激活成功！您已升级为Pro用户', 'success');
          }
        }, 2000);
      } else {
        this.showActivationStatus(result.message, 'error');
      }
    } catch (error) {
      console.error('激活过程中发生错误:', error);
      this.showActivationStatus('激活失败，请重试', 'error');
    } finally {
      // 恢复按钮状态
      activateBtn.disabled = false;
      activateBtn.textContent = '激活';
    }
  }
};

// 在DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  if (window.ActivationManager) {
    window.ActivationManager.initActivationEvents();
  }
});

console.log('激活码管理器已加载');
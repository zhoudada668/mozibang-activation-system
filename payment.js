// MoziBang 支付管理器
window.PaymentManager = {
  // 获取Pro状态 - 优先使用激活码系统
  async getProStatus() {
    try {
      // 首先尝试从激活码系统获取状态
      if (window.ActivationManager) {
        const activationStatus = await window.ActivationManager.getLocalProStatus();
        if (activationStatus.isPro) {
          return {
            isPro: true,
            plan: activationStatus.plan,
            activatedAt: activationStatus.activatedAt,
            expiresAt: activationStatus.expiresAt,
            isLifetime: activationStatus.isLifetime,
            source: 'activation_code',
            message: activationStatus.message
          };
        }
      }
      
      // 如果激活码系统没有Pro状态，检查旧的支付系统
      const result = await chrome.storage.local.get('proStatus');
      const proData = result.proStatus;
      
      if (proData && proData.isPro) {
        // 检查是否过期
        if (proData.expiresAt && new Date(proData.expiresAt) < new Date()) {
          await chrome.storage.local.remove('proStatus');
          return {
            isPro: false,
            plan: 'free',
            message: 'Pro版本已过期'
          };
        }
        
        return {
          isPro: true,
          plan: proData.plan || 'pro',
          purchasedAt: proData.purchasedAt,
          expiresAt: proData.expiresAt,
          source: 'payment',
          message: proData.expiresAt ? 
            `Pro版本 (到期: ${new Date(proData.expiresAt).toLocaleDateString()})` : 
            'Pro版本'
        };
      }
      
      return {
        isPro: false,
        plan: 'free',
        message: '免费版本'
      };
    } catch (error) {
      console.error('获取Pro状态失败:', error);
      return {
        isPro: false,
        plan: 'free',
        message: '免费版本'
      };
    }
  },

  // 购买Pro版本 (保留原有功能)
  async purchasePro(plan = 'pro') {
    try {
      const proData = {
        isPro: true,
        plan: plan,
        purchasedAt: new Date().toISOString(),
        // 设置1年有效期
        expiresAt: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString()
      };
      
      await chrome.storage.local.set({ proStatus: proData });
      
      console.log('Pro版本购买成功:', proData);
      return {
        success: true,
        message: 'Pro版本购买成功！',
        data: proData
      };
    } catch (error) {
      console.error('购买Pro版本失败:', error);
      return {
        success: false,
        message: '购买失败，请重试'
      };
    }
  },

  // 清除Pro状态
  async clearProStatus() {
    try {
      // 清除激活码Pro状态
      if (window.ActivationManager) {
        await window.ActivationManager.clearProStatus();
      }
      
      // 清除支付Pro状态
      await chrome.storage.local.remove('proStatus');
      
      console.log('Pro状态已清除');
      return true;
    } catch (error) {
      console.error('清除Pro状态失败:', error);
      return false;
    }
  },

  // 显示升级对话框
  showUpgradeDialog() {
    // 优先显示激活码升级选项
    if (window.ActivationManager) {
      window.ActivationManager.showActivationModal();
      return;
    }
    
    // 原有的升级对话框逻辑
    const upgradeModal = document.getElementById('upgradeModal');
    if (upgradeModal) {
      upgradeModal.style.display = 'flex';
    } else {
      // 如果没有升级模态框，显示简单的确认对话框
      if (confirm('升级到Pro版本以解锁无限制功能？')) {
        this.purchasePro().then(result => {
          if (result.success) {
            alert(result.message);
            // 刷新UI
            if (window.updateUIStatus) {
              window.updateUIStatus();
            }
          } else {
            alert(result.message);
          }
        });
      }
    }
  },

  // 验证远程Pro状态 (与激活码系统集成)
  async verifyRemoteProStatus(userEmail) {
    try {
      if (window.ActivationManager && userEmail) {
        const result = await window.ActivationManager.verifyProStatus(userEmail);
        if (result.success) {
          return result.data;
        }
      }
      
      // 如果激活码系统验证失败，返回本地状态
      return await this.getProStatus();
    } catch (error) {
      console.error('远程Pro状态验证失败:', error);
      return await this.getProStatus();
    }
  },

  // 初始化支付相关事件
  initPaymentEvents() {
    // 升级按钮事件
    const upgradeBtn = document.getElementById('upgradeBtn');
    if (upgradeBtn) {
      upgradeBtn.addEventListener('click', () => {
        this.showUpgradeDialog();
      });
    }
    
    // 如果有购买按钮
    const purchaseBtn = document.getElementById('purchaseBtn');
    if (purchaseBtn) {
      purchaseBtn.addEventListener('click', async () => {
        const result = await this.purchasePro();
        if (result.success) {
          alert(result.message);
          if (window.updateUIStatus) {
            window.updateUIStatus();
          }
        } else {
          alert(result.message);
        }
      });
    }
  }

};

// 在DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
  if (window.PaymentManager) {
    window.PaymentManager.initPaymentEvents();
  }
});

console.log('支付管理器已加载');

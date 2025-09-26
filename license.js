// 许可证管理系统
window.licenseManager = {
  FREE_LIMIT: 100, // 免费版限制100条
  
  // 获取用户使用统计
  async getUsage() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['usage'], (result) => {
        const usage = result.usage || { totalExtracted: 0 };
        resolve(usage);
      });
    });
  },
  
  // 检查是否可以提取（免费版提取不限制）
  async checkLimit(count = 1) {
    try {
      console.log('检查提取限制 - 请求数量:', count);
      
      // 检查是否是Pro用户
      if (window.PaymentManager) {
        const proStatus = await window.PaymentManager.getProStatus();
        if (proStatus.isPro) {
          console.log('Pro用户，提取无限制');
          return { allowed: true, message: 'Pro用户无限制' };
        }
      }
      
      // 免费用户提取不限制，只在导出时限制
      console.log('免费用户，提取无限制');
      return { allowed: true, message: '提取无限制' };
    } catch (error) {
      console.error('检查限制失败:', error);
      return { allowed: true, message: '检查限制失败，允许继续' };
    }
  },
  
  // 记录导出使用量（免费版在导出时计数）
  async recordExport(count) {
    try {
      // 检查是否是Pro用户
      if (window.PaymentManager) {
        const proStatus = await window.PaymentManager.getProStatus();
        if (proStatus.isPro) {
          return; // Pro用户无需记录
        }
      }
      
      const usage = await this.getUsage();
      usage.totalExtracted = (usage.totalExtracted || 0) + count;
      
      return new Promise((resolve) => {
        chrome.storage.local.set({ usage }, () => {
          resolve(usage);
        });
      });
    } catch (error) {
      console.error('记录导出失败:', error);
    }
  },

  // 记录提取使用量（Pro版检查）
  async recordExtraction(count) {
    try {
      // 检查是否是Pro用户
      if (window.PaymentManager) {
        const proStatus = await window.PaymentManager.getProStatus();
        if (proStatus.isPro) {
          return; // Pro用户无需记录
        }
      }
      
      const usage = await this.getUsage();
      usage.totalExtracted = (usage.totalExtracted || 0) + count;
      
      return new Promise((resolve) => {
        chrome.storage.local.set({ usage }, () => {
          resolve(usage);
        });
      });
    } catch (error) {
      console.error('记录提取失败:', error);
    }
  },
  
  // 检查导出限制（免费版累计导出限制100条）
  async checkExportLimit(count) {
    try {
      console.log('检查导出限制 - 数据量:', count);
      
      // 检查是否是Pro用户
      if (window.PaymentManager) {
        const proStatus = await window.PaymentManager.getProStatus();
        if (proStatus.isPro) {
          console.log('Pro用户，导出无限制');
          return { allowed: true, allowedCount: count };
        }
      }
      
      // 免费用户检查累计导出限制100条
      const usage = await this.getUsage();
      const remaining = this.FREE_LIMIT - usage.totalExtracted;
      
      console.log('当前累计导出:', usage.totalExtracted, '/', this.FREE_LIMIT, ', 剩余:', remaining);
      
      if (remaining <= 0) {
        return {
          allowed: false,
          message: '已达到免费版导出限制（累计100条），请升级到Pro版本',
          upgradeRequired: true
        };
      }
      
      if (remaining < count) {
        return {
          allowed: true,
          allowedCount: remaining,
          message: `免费版剩余 ${remaining} 条导出额度，本次只能导出 ${remaining} 条`
        };
      }
      
      console.log('导出数量在免费限制内，允许全部导出');
      return { allowed: true, allowedCount: count };
    } catch (error) {
      console.error('检查导出限制失败:', error);
      return { allowed: true, allowedCount: count };
    }
  },
  
  // 重置使用统计（测试用）
  async resetUsage() {
    try {
      const newUsage = {
        totalExtracted: 0,
        lastResetDate: new Date().toISOString(),
        dailyUsage: {}
      };
      await chrome.storage.local.set({ usageStats: newUsage });
      console.log('使用统计已重置');
      return newUsage;
    } catch (error) {
      console.error('重置使用统计失败:', error);
    }
  },

  // 重置到免费会员状态（测试用）
  async resetToFreeUser() {
    try {
      console.log('开始重置到免费会员状态...');
      
      // 清除Pro状态
      if (window.PaymentManager) {
        await window.PaymentManager.clearProStatus();
        console.log('Pro状态已清除');
      }
      
      // 重置使用统计
      await this.resetUsage();
      console.log('使用统计已重置');
      
      console.log('已成功重置到免费会员状态');
      return {
        success: true,
        message: '已重置到免费会员状态，使用量已清零'
      };
    } catch (error) {
      console.error('重置到免费会员失败:', error);
      return {
        success: false,
        message: '重置失败: ' + error.message
      };
    }
  }
};

console.log('许可证管理器已加载，免费限制:', window.licenseManager.FREE_LIMIT);

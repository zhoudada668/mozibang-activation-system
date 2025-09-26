// 安全数据管理系统
window.secureDataManager = {
  // 简单的混淆函数（不是真正的加密，但增加获取难度）
  obfuscateData(data) {
    const jsonStr = JSON.stringify(data);
    const encoded = btoa(jsonStr); // Base64编码
    // 简单字符替换混淆
    return encoded.split('').map(char => {
      const code = char.charCodeAt(0);
      return String.fromCharCode(code + 3); // 简单位移
    }).join('');
  },

  // 反混淆函数
  deobfuscateData(obfuscatedData) {
    try {
      // 反向字符替换
      const decoded = obfuscatedData.split('').map(char => {
        const code = char.charCodeAt(0);
        return String.fromCharCode(code - 3);
      }).join('');
      
      const jsonStr = atob(decoded); // Base64解码
      return JSON.parse(jsonStr);
    } catch (error) {
      console.error('数据反混淆失败:', error);
      return null;
    }
  },

  // 生成访问令牌
  generateAccessToken() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substr(2, 9);
    return `${timestamp}_${random}`;
  },

  // 存储提取的数据（带安全控制）
  async storeExtractedData(data, type = 'bulk') {
    try {
      if (!data || data.length === 0) {
        return { success: false, message: '没有数据需要存储' };
      }

      // 检查是否是Pro用户，免费用户限制存储数据量
      let storageLimit = 200; // 免费用户最多存储200条提取数据
      if (window.PaymentManager) {
        const proStatus = await window.PaymentManager.getProStatus();
        if (proStatus.isPro) {
          storageLimit = 10000; // Pro用户可以存储更多数据
        }
      }

      // 如果超过限制，只保留最新的数据
      let dataToStore = data;
      if (data.length > storageLimit) {
        dataToStore = data.slice(-storageLimit); // 保留最后的N条}

      // 混淆数据
      const obfuscatedData = this.obfuscateData(dataToStore);
      
      // 生成访问令牌
      const accessToken = this.generateAccessToken();
      
      // 存储到Chrome storage（会话级别）
      const storageKey = `extracted_${type}_${accessToken}`;
      const storageData = {
        data: obfuscatedData,
        timestamp: Date.now(),
        count: dataToStore.length,
        accessToken: accessToken,
        type: type
      };

      await chrome.storage.session.set({ [storageKey]: storageData });return {
        success: true,
        accessToken: accessToken,
        count: dataToStore.length,
        storageKey: storageKey
      };

    } catch (error) {
      console.error('存储数据失败:', error);
      return { success: false, message: error.message };
    }
  },

  // 获取存储的数据（需要访问令牌）
  async getStoredData(accessToken, skipLicenseCheck = false) {
    try {
      if (!accessToken) {
        return { success: false, message: '缺少访问令牌' };
      }

      // 查找对应的存储键
      const allStorage = await chrome.storage.session.get(null);
      let targetKey = null;
      let targetData = null;

      for (const [key, value] of Object.entries(allStorage)) {
        if (key.startsWith('extracted_') && value.accessToken === accessToken) {
          targetKey = key;
          targetData = value;
          break;
        }
      }

      if (!targetData) {
        return { success: false, message: '找不到对应的数据或访问令牌已失效' };
      }

      // 检查数据是否过期（1小时）
      const now = Date.now();
      const dataAge = now - targetData.timestamp;
      if (dataAge > 60 * 60 * 1000) { // 1小时
        await chrome.storage.session.remove(targetKey);
        return { success: false, message: '数据已过期，请重新提取' };
      }

      // 反混淆数据
      const originalData = this.deobfuscateData(targetData.data);
      if (!originalData) {
        return { success: false, message: '数据解析失败' };
      }

      return {
        success: true,
        data: originalData,
        count: originalData.length,
        timestamp: targetData.timestamp,
        type: targetData.type
      };

    } catch (error) {
      console.error('获取存储数据失败:', error);
      return { success: false, message: error.message };
    }
  },

  // 更新特定项目的详情
  async updateItemDetail(token, itemHref, detailInfo) {
    try {
      if (!token || !itemHref) return { success: false, newToken: token };
      
      const sessionData = await this.getStoredData(token);
      if (!sessionData || !sessionData.success || !sessionData.data) return { success: false, newToken: token };
      
      // 找到并更新对应的项目
      let itemFound = false;
      const updatedData = sessionData.data.map(item => {
        if (item.href === itemHref) {
          itemFound = true;
          return { ...item, ...detailInfo };
        }
        return item;
      });
      
      if (!itemFound) {
        console.warn('未找到要更新的项目:', itemHref);
        return { success: false, newToken: token };
      }
      
      // 删除旧数据
      await this.deleteStoredData(token);
      
      // 重新存储更新后的数据，保持原有类型
      const storeResult = await this.storeExtractedData(updatedData, sessionData.type || 'bulk');
      
      if (storeResult.success) {}
      
      return { 
        success: storeResult.success, 
        newToken: storeResult.success ? storeResult.accessToken : token 
      };
      
    } catch (error) {
      console.error('更新项目详情失败:', error);
      return { success: false, newToken: token };
    }
  },

  // 获取数据数量（不获取完整数据，只返回计数）
  async getDataCount(token) {
    try {
      if (!token) return 0;
      
      const sessionData = await this.getStoredData(token);
      if (!sessionData || !sessionData.success || !sessionData.data) return 0;
      
      return sessionData.data.length;
    } catch (error) {
      console.warn('获取数据计数失败:', error);
      return 0;
    }
  },

  // 清理过期数据
  async cleanupExpiredData() {
    try {
      const allStorage = await chrome.storage.session.get(null);
      const now = Date.now();
      const keysToRemove = [];

      for (const [key, value] of Object.entries(allStorage)) {
        if (key.startsWith('extracted_') && value.timestamp) {
          const dataAge = now - value.timestamp;
          if (dataAge > 60 * 60 * 1000) { // 1小时过期
            keysToRemove.push(key);
          }
        }
      }

      if (keysToRemove.length > 0) {
        await chrome.storage.session.remove(keysToRemove);}

    } catch (error) {
      console.error('清理过期数据失败:', error);
    }
  },

  // 删除指定数据
  async deleteStoredData(accessToken) {
    try {
      const allStorage = await chrome.storage.session.get(null);
      
      for (const [key, value] of Object.entries(allStorage)) {
        if (key.startsWith('extracted_') && value.accessToken === accessToken) {
          await chrome.storage.session.remove(key);return { success: true };
        }
      }
      
      return { success: false, message: '找不到对应的数据' };
    } catch (error) {
      console.error('删除数据失败:', error);
      return { success: false, message: error.message };
    }
  },

  // 获取当前存储的数据概览
  async getStorageOverview() {
    try {
      const allStorage = await chrome.storage.session.get(null);
      const extractedDataItems = [];

      for (const [key, value] of Object.entries(allStorage)) {
        if (key.startsWith('extracted_') && value.timestamp) {
          extractedDataItems.push({
            key: key,
            count: value.count,
            type: value.type,
            timestamp: value.timestamp,
            age: Date.now() - value.timestamp
          });
        }
      }

      return {
        success: true,
        items: extractedDataItems,
        totalItems: extractedDataItems.length
      };
    } catch (error) {
      console.error('获取存储概览失败:', error);
      return { success: false, message: error.message };
    }
  }
};

// 定期清理过期数据
setInterval(() => {
  window.secureDataManager.cleanupExpiredData();
}, 10 * 60 * 1000); // 每10分钟清理一次
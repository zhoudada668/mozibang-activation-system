// 用户认证状态
let userAuthenticated = false;
let userProfile = null;

// 数据存储变量（简化版本）
let bulkData = [];
let currentDataToken = null;
let cachedDataCount = 0;
let openedTabs = {};

// 等待Chrome API就绪的函数
function waitForChromeAPI() {
  return new Promise((resolve, reject) => {
    const checkAPI = () => {
      if (typeof chrome !== 'undefined' && 
          chrome.storage && 
          chrome.storage.local && 
          chrome.identity && 
          chrome.runtime) {
        console.log('Chrome API 已就绪');
        resolve();
      } else {
        console.log('Chrome API 未就绪，继续等待...');
        setTimeout(checkAPI, 100);
      }
    };
    
    // 设置超时
    setTimeout(() => {
      reject(new Error('Chrome API 初始化超时'));
    }, 10000);
    
    checkAPI();
  });
}

// 检查用户认证状态
async function checkAuthStatus() {
  try {
    console.log('🔍 开始检查认证状态...');
    
    // 等待Chrome API就绪
    await waitForChromeAPI();
    
    console.log('📦 获取存储的token...');
    const result = await new Promise((resolve, reject) => {
      chrome.storage.local.get('authToken', (result) => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          resolve(result);
        }
      });
    });
    
    console.log('💾 存储中的token状态:', result.authToken ? '✅ 存在' : '❌ 不存在');
    
    if (result.authToken) {
      console.log('🔄 验证现有token...');
      const response = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: { Authorization: `Bearer ${result.authToken}` }
      });
      console.log('📡 用户信息请求状态:', response.status);
      
      if (response.ok) {
        userProfile = await response.json();
        window.userProfile = userProfile; // 设置为全局变量
        console.log('👤 获取到用户信息:', userProfile);
        userAuthenticated = true;
        updateUIForAuthenticatedUser();
      } else {
        console.error('❌ 验证失败，状态码:', response.status);
        console.log('🔄 尝试刷新token...');
        await handleAuthError();
      }
    } else {
      console.log('ℹ️ 未找到token，显示未登录状态');
      updateUIForUnauthenticatedUser();
    }
  } catch (error) {
    console.error('❌ 认证状态检查失败:', error);
    await handleAuthError();
  }
}

// 处理认证错误
async function handleAuthError() {
  try {
    await waitForChromeAPI();
    
    await new Promise((resolve, reject) => {
      chrome.storage.local.remove('authToken', () => {
        if (chrome.runtime.lastError) {
          console.log('移除token时出错:', chrome.runtime.lastError);
        }
        resolve();
      });
    });
  } catch (error) {
    console.error('处理认证错误失败:', error);
  }
  
  userAuthenticated = false;
  userProfile = null;
  window.userProfile = null; // 清除全局变量
  updateUIForUnauthenticatedUser();
}

// Google登录
async function authenticateWithGoogle() {
  try {
    console.log('🔐 开始Google登录流程...');
    
    // 等待Chrome API就绪
    await waitForChromeAPI();
    
    // 显示登录状态
    const status = document.getElementById('status');
    if (status) {
      status.textContent = '正在登录...';
    }
    
    console.log('📋 检查manifest中的OAuth配置...');
    const manifest = chrome.runtime.getManifest();
    console.log('OAuth client_id:', manifest.oauth2?.client_id);
    console.log('OAuth scopes:', manifest.oauth2?.scopes);
    
    // 清除现有的token
    try {
      const existingResult = await new Promise((resolve, reject) => {
        chrome.storage.local.get('authToken', (result) => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else {
            resolve(result);
          }
        });
      });
      
      if (existingResult.authToken) {
        console.log('🗑️ 清除现有token...');
        await new Promise((resolve, reject) => {
          chrome.identity.removeCachedAuthToken({ token: existingResult.authToken }, () => {
            if (chrome.runtime.lastError) {
              console.log('⚠️ 清除token时出错（可能已过期）:', chrome.runtime.lastError);
            }
            resolve();
          });
        });
        
        await new Promise((resolve, reject) => {
          chrome.storage.local.remove('authToken', () => {
            if (chrome.runtime.lastError) {
              reject(chrome.runtime.lastError);
            } else {
              resolve();
            }
          });
        });
      }
    } catch (clearError) {
      console.log('⚠️ 清除现有认证时出错:', clearError);
    }

    console.log('🔄 请求新的认证token...');
    
    // 获取新token
    const token = await new Promise((resolve, reject) => {
      chrome.identity.getAuthToken({
        interactive: true
      }, (token) => {
        if (chrome.runtime.lastError) {
          console.error('❌ 获取token失败:', chrome.runtime.lastError);
          reject(chrome.runtime.lastError);
        } else {
          resolve(token);
        }
      });
    });
    
    console.log('🎫 获取到认证token:', token ? '✅ 成功' : '❌ 失败');
    
    if (token) {
      // 保存token
      await new Promise((resolve, reject) => {
        chrome.storage.local.set({ authToken: token }, () => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else {
            resolve();
          }
        });
      });
      
      // 验证token
      console.log('✅ 验证token...');
      const response = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log('📡 Google API响应状态:', response.status);
      
      if (response.ok) {
        const userInfo = await response.json();
        console.log('👤 Token验证成功，用户信息:', userInfo);
        userProfile = userInfo;
        window.userProfile = userProfile; // 设置为全局变量
        userAuthenticated = true;
        updateUIForAuthenticatedUser();
        
        if (status) {
          status.textContent = '登录成功！';
        }
      } else {
        console.error('❌ Token验证失败，状态码:', response.status);
        const errorText = await response.text();
        console.error('❌ 错误详情:', errorText);
        throw new Error(`Token验证失败: ${response.status} - ${errorText}`);
      }
    } else {
      throw new Error('未能获取到有效的认证token');
    }
  } catch (error) {
    console.error('❌ Google登录失败:', error);
    
    // 显示用户友好的错误信息
    let errorMessage = '登录失败';
    if (error.message && error.message.includes('User did not approve')) {
      errorMessage = '用户取消了登录';
    } else if (error.message && error.message.includes('OAuth')) {
      errorMessage = 'OAuth认证失败，请检查网络连接';
    } else if (error.message && error.message.includes('Token')) {
      errorMessage = 'Token获取失败，请重试';
    } else if (error.message && error.message.includes('identity')) {
      errorMessage = '身份认证服务不可用，请检查扩展权限';
    } else {
      errorMessage = `登录失败: ${error.message || '未知错误'}`;
    }
    
    console.log('🔧 建议解决方案:');
    console.log('1. 检查网络连接');
    console.log('2. 重新加载扩展');
    console.log('3. 检查Google账户状态');
    console.log('4. 清除浏览器缓存');
    
    const status = document.getElementById('status');
    if (status) {
      status.textContent = errorMessage;
      status.style.color = '#ea4335';
    }
    
    // 清理状态
    await handleAuthError();
  }
}

// 注销
async function logout() {
  try {
    console.log('开始注销流程...');
    
    // 等待Chrome API就绪
    await waitForChromeAPI();
    
    const result = await new Promise((resolve, reject) => {
      chrome.storage.local.get('authToken', (result) => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          resolve(result);
        }
      });
    });
    
    if (result.authToken) {
      await new Promise((resolve, reject) => {
        chrome.identity.removeCachedAuthToken({ token: result.authToken }, () => {
          if (chrome.runtime.lastError) {
            console.log('移除缓存token时出错:', chrome.runtime.lastError);
          }
          resolve();
        });
      });
    }
    
    await new Promise((resolve, reject) => {
      chrome.storage.local.remove('authToken', () => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          resolve();
        }
      });
    });
   // 清理状态
    userAuthenticated = false;
    userProfile = null;
    window.userProfile = null; // 清除全局变量
    updateUIForUnauthenticatedUser();
    
    const status = document.getElementById('status');
    if (status) {
      status.textContent = '已注销';
    }
  } catch (error) {
    console.error('注销失败:', error);
  }
}

// 更新已登录用户的UI
function updateUIForAuthenticatedUser() {
  document.getElementById('loginSection').style.display = 'none';
  document.getElementById('mainContent').style.display = 'block';
  const userInfo = document.getElementById('userInfo');
  if (userProfile) {
    const userImg = document.createElement('img');
    userImg.className = 'user-avatar';
    userImg.alt = '用户头像';
    userImg.crossOrigin = 'anonymous';
    userImg.src = userProfile.picture;
    
    const userName = document.createElement('span');
    userName.className = 'user-name';
    userName.textContent = userProfile.name || userProfile.email || '用户';
    
    const logoutBtn = document.createElement('button');
    logoutBtn.id = 'logoutBtn';
    logoutBtn.className = 'logout-btn';
    logoutBtn.textContent = '注销';
    
    userInfo.innerHTML = '';
    userInfo.appendChild(userImg);
    userInfo.appendChild(userName);
    userInfo.appendChild(logoutBtn);
    
    logoutBtn.addEventListener('click', logout);
  }
  const status = document.getElementById('status');
  if (status) {
    status.textContent = '已登录，可以开始使用';
  }
}

// 更新未登录用户的UI
function updateUIForUnauthenticatedUser() {
  document.getElementById('loginSection').style.display = 'block';
  document.getElementById('mainContent').style.display = 'none';
  document.getElementById('userInfo').innerHTML = '';
  const status = document.getElementById('status');
  if (status) {
    status.textContent = '请先登录以使用功能';
  }
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', async () => {
  console.log('Popup页面加载完成，开始初始化...');
  
  // 尝试恢复最近的数据会话
  await tryRestoreRecentSession();
  
  // 更新UI状态
  await updateUIStatus();
  
  // 显示当前数据（如果有）
  await displayBulkDataSecurely();
  
  // 根据数据状态更新按钮
  if (bulkData.length > 0) {
    exportBtn.disabled = false;
    extractBulkDetailBtn.disabled = false;
  } else {
    exportBtn.disabled = true;
    extractBulkDetailBtn.disabled = true;
  }
});

// 尝试恢复最近的数据会话
async function tryRestoreRecentSession() {
  // 简化版本：不需要复杂的会话恢复
  console.log('简化版本启动，不需要会话恢复');
}

// 更新UI状态显示
async function updateUIStatus() {
  const usageInfoElement = document.getElementById('usageInfo');
  const proStatusElement = document.getElementById('proStatus');
  const upgradeBtnElement = document.getElementById('upgradeBtn');
  const activationBtnElement = document.getElementById('activationBtn');
  
  if (!usageInfoElement || !window.licenseManager) {
    return;
  }
  
  try {
    const proStatus = window.PaymentManager ? await window.PaymentManager.getProStatus() : { isPro: false };
    
    if (proStatus.isPro) {
      usageInfoElement.textContent = 'Pro版本（永久有效）';
      usageInfoElement.className = 'usage-text';
      
      if (proStatusElement) {
        proStatusElement.style.display = 'inline-block';
        proStatusElement.textContent = 'Pro会员';
      }
      
      if (upgradeBtnElement) {
        upgradeBtnElement.style.display = 'none';
      }
      
      if (activationBtnElement) {
        activationBtnElement.style.display = 'none';
      }
    } else {
      const usage = await window.licenseManager.getUsage();
      const remaining = Math.max(0, window.licenseManager.FREE_LIMIT - usage.totalExtracted);
      
      usageInfoElement.textContent = `免费版 ${usage.totalExtracted}/${window.licenseManager.FREE_LIMIT}`;
      
      if (remaining <= 0) {
        usageInfoElement.className = 'usage-text usage-critical';
      } else if (remaining <= 20) {
        usageInfoElement.className = 'usage-text usage-warning';
      } else {
        usageInfoElement.className = 'usage-text';
      }
      
      if (proStatusElement) {
        proStatusElement.style.display = 'none';
      }
      
      if (upgradeBtnElement) {
        upgradeBtnElement.style.display = 'inline-block';
      }
      
      if (activationBtnElement) {
        activationBtnElement.style.display = 'inline-block';
      }
    }
  } catch (error) {
    console.error('更新UI状态失败:', error);
    usageInfoElement.textContent = '状态获取失败';
    usageInfoElement.className = 'usage-text';
  }
}

// 使函数全局可用
window.updateUIStatus = updateUIStatus;

document.addEventListener('DOMContentLoaded', async () => {
  // 获取DOM元素
  const extractBulkBtn = document.getElementById('extractBulkBtn');
  const extractBulkDetailBtn = document.getElementById('extractBulkDetailBtn');
  const exportBtn = document.getElementById('exportBtn');
  const resetToFreeBtn = document.getElementById('resetToFreeBtn');
  const filterInput = document.getElementById('filterInput');
  const dataContainer = document.getElementById('dataContainer');
  const status = document.getElementById('status');
  const dataCount = document.getElementById('dataCount');
  const pageUrl = document.getElementById('pageUrl');
  
  // 初始化登录按钮
  const loginBtn = document.getElementById('loginBtn');
  if (loginBtn) {
    loginBtn.addEventListener('click', authenticateWithGoogle);
  }
  
  // 检查登录状态
  await checkAuthStatus();
  
  // 初始化许可证状态显示
  await updateUIStatus();
  
  // 升级按钮事件监听器
  const upgradeBtn = document.getElementById('upgradeBtn');
  
  if (upgradeBtn) {
    // 保存当前的显示状态
    const currentDisplayStyle = upgradeBtn.style.display;
    
    // 清除之前可能存在的事件监听器
    upgradeBtn.replaceWith(upgradeBtn.cloneNode(true));
    const newUpgradeBtn = document.getElementById('upgradeBtn');
    
    // 恢复显示状态并设置其他样式
    newUpgradeBtn.style.display = currentDisplayStyle;
    newUpgradeBtn.style.cursor = 'pointer';
    newUpgradeBtn.style.pointerEvents = 'auto';
    newUpgradeBtn.style.opacity = '1';
    newUpgradeBtn.disabled = false;
    
    newUpgradeBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // 立即给用户反馈
      newUpgradeBtn.style.background = '#1a73e8';
      newUpgradeBtn.textContent = '打开中...';
      
      setTimeout(() => {
        newUpgradeBtn.style.background = '';
        newUpgradeBtn.textContent = '升级Pro';
      }, 1000);
      
      if (window.PaymentManager && typeof window.PaymentManager.showUpgradeDialog === 'function') {
        try {
          window.PaymentManager.showUpgradeDialog();
        } catch (error) {
          console.error('升级对话框触发失败:', error);
          alert('升级功能出现问题: ' + error.message);
        }
      } else {
        console.error('Payment Manager 或 showUpgradeDialog 方法不可用');
        alert('支付管理器未加载，请重新打开扩展');
      }
    });
  }
  
  // 激活码按钮事件监听器
  const activationBtn = document.getElementById('activationBtn');
  
  if (activationBtn) {
    activationBtn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      // 显示激活码输入对话框
      const activationCode = prompt('请输入激活码:');
      
      if (activationCode && activationCode.trim()) {
        // 立即给用户反馈
        activationBtn.disabled = true;
        activationBtn.textContent = '验证中...';
        
        // 验证激活码
        if (window.PaymentManager && typeof window.PaymentManager.activateWithCode === 'function') {
          window.PaymentManager.activateWithCode(activationCode.trim())
            .then(result => {
              if (result.success) {
                alert('激活成功！');
                updateUIStatus(); // 更新UI状态
              } else {
                alert('激活失败: ' + (result.message || '无效的激活码'));
              }
            })
            .catch(error => {
              console.error('激活过程出错:', error);
              alert('激活过程出错: ' + error.message);
            })
            .finally(() => {
              activationBtn.disabled = false;
              activationBtn.textContent = '激活码';
            });
        } else {
          console.error('Payment Manager 或 activateWithCode 方法不可用');
          alert('激活功能未加载，请重新打开扩展');
          activationBtn.disabled = false;
          activationBtn.textContent = '激活码';
        }
      }
    });
  }
  
  // 批量提取数据
  extractBulkBtn.addEventListener('click', async () => {
    // 提取阶段不限制，在导出时才计算
    status.textContent = '正在批量提取数据...';
    extractBulkBtn.disabled = true;
    exportBtn.disabled = true;
    dataContainer.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    chrome.runtime.sendMessage({action: 'extractBulkData'}, async (response) => {
      extractBulkBtn.disabled = false;
      
      if (chrome.runtime.lastError) {
        status.textContent = '提取数据时出错：' + chrome.runtime.lastError.message;
        return;
      }
      
      if (response.error) {
        status.textContent = '提取数据时出错：' + response.error;
        return;
      }
      
      const extractedData = response.extractedData || [];
      
      // 简化存储：直接使用全局变量，同时保持安全存储作为备份
      bulkData = extractedData;
      cachedDataCount = extractedData.length;
      
      // 尝试安全存储作为备份
      if (extractedData.length > 0 && window.secureDataManager) {
        try {
          const storeResult = await window.secureDataManager.storeExtractedData(extractedData, 'bulk');
          if (storeResult.success) {
            currentDataToken = storeResult.accessToken;
            console.log(`安全存储备份了 ${cachedDataCount} 条数据`);
          }
        } catch (error) {
          console.log('安全存储失败，使用内存存储:', error);
        }
      }
      
      dataCount.textContent = cachedDataCount;
      pageUrl.textContent = response.url || '-';
      
      // 直接显示数据
      displayBulkData(bulkData.slice(0, 10), cachedDataCount);
      
      // 安全获取当前数据计数
      const currentDataCount = bulkData.length;
      
      if (currentDataCount >= 20) {
        status.textContent = `成功提取 ${currentDataCount} 个数据项`;
        exportBtn.disabled = false;
        extractBulkDetailBtn.disabled = false;
      } else if (currentDataCount > 0) {
        status.textContent = `只找到 ${currentDataCount} 个数据项，不满足批量提取条件（至少20条）`;
        exportBtn.disabled = false;
        extractBulkDetailBtn.disabled = false;
      } else {
        status.textContent = '当前页面未找到符合条件的数据';
        exportBtn.disabled = true;
        extractBulkDetailBtn.disabled = true;
      }
      
      // 更新UI状态
      await updateUIStatus();
    });
  });
  
  // 搜索过滤
  filterInput.addEventListener('input', (e) => {
    const searchText = e.target.value.toLowerCase();
    
    if (bulkData.length > 0) {
      const filteredData = bulkData.filter(item => {
        return Object.values(item).some(value => 
          value && value.toString().toLowerCase().includes(searchText)
        );
      });
      displayBulkData(filteredData, bulkData.length);
    }
  });
  
  // 显示批量数据
  function displayBulkData(data, totalCount = null) {
    dataContainer.innerHTML = '';
    
    // 如果是预览模式，显示安全提示
    const isPreview = totalCount && totalCount > data.length;
    if (isPreview) {
      const previewNotice = document.createElement('div');
      previewNotice.className = 'preview-notice';
      previewNotice.innerHTML = `🔒 <strong>安全预览模式</strong>：显示前 ${data.length} 条，共 ${totalCount} 条数据<br><small>完整数据已安全存储，导出时自动获取</small>`;
      previewNotice.style.cssText = 'background: #e3f2fd; border: 1px solid #2196f3; padding: 10px; margin-bottom: 10px; border-radius: 4px; color: #1976d2;';
      dataContainer.appendChild(previewNotice);
    }
    
    if (data.length === 0) {
      const emptyMessage = document.createElement('div');
      emptyMessage.className = 'empty-message';
      emptyMessage.textContent = '没有找到符合条件的数据';
      dataContainer.appendChild(emptyMessage);
      return;
    }
    
    const table = document.createElement('table');
    table.className = 'data-table';
    
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    const fields = ['title', 'url', 'description'];
    
    fields.forEach(field => {
      const th = document.createElement('th');
      th.textContent = getFieldDisplayName(field);
      headerRow.appendChild(th);
    });
    
    const actionTh = document.createElement('th');
    actionTh.textContent = '操作';
    headerRow.appendChild(actionTh);
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    const tbody = document.createElement('tbody');
    
    data.forEach(item => {
      const row = document.createElement('tr');
      
      fields.forEach(field => {
        const td = document.createElement('td');
        td.textContent = item[field] || '';
        row.appendChild(td);
      });
      
      const actionTd = document.createElement('td');
      
      if (item.href) {
        const openButton = document.createElement('button');
        openButton.className = 'action-button';
        openButton.textContent = '打开';
        openButton.addEventListener('click', () => {
          chrome.tabs.create({url: item.href}, (tab) => {
            openedTabs[item.href] = tab.id;
            console.log('已打开标签页:', tab.id, '链接:', item.href);
          });
        });
        actionTd.appendChild(openButton);
        
        const detailButton = document.createElement('button');
        detailButton.className = 'action-button';
        detailButton.textContent = '提取详情';
        detailButton.addEventListener('click', () => {
          console.log('点击了提取详情按钮');
          detailButton.disabled = true;
          detailButton.textContent = '提取中...';
          
          // 最简单的方式：直接打开页面让用户手动复制
          window.open(item.href, '_blank');
          
          setTimeout(() => {
            detailButton.disabled = false;
            detailButton.textContent = '提取详情';
            status.textContent = '已打开详情页面，请手动查看内容';
          }, 1000);
        });
        actionTd.appendChild(detailButton);
      }
      
      row.appendChild(actionTd);
      tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    dataContainer.appendChild(table);
  }
  
  function getFieldDisplayName(field) {
    const fieldMap = {
      'url': '实际URL',
      'href': '链接URL',
      'title': '标题',
      'description': '描述',
      'image': '图片'
    };
    
    return fieldMap[field] || field;
  }
  
  // 导出CSV功能
  exportBtn.addEventListener('click', async () => {
    try {
      console.log('点击导出按钮，数据长度:', bulkData.length);
      
      if (bulkData.length === 0) {
        console.log('没有数据可导出');
        status.textContent = '没有可导出的数据';
        return;
      }
      
      let dataToExport = bulkData;
      
      // 检查导出限制（免费版累计导出限制100条）
      if (window.licenseManager) {
        console.log('检查导出限制...');
        
        // 检查导出限制
        const exportCheck = await window.licenseManager.checkExportLimit(bulkData.length);
        console.log('导出检查结果:', exportCheck);
        
        if (!exportCheck.allowed) {
          status.textContent = exportCheck.message;
          if (window.PaymentManager) {
            window.PaymentManager.showUpgradeDialog();
          }
          return;
        }
        
        // 如果有限制，只导出允许的数量
        if (exportCheck.allowedCount < bulkData.length) {
          dataToExport = bulkData.slice(0, exportCheck.allowedCount);
          status.textContent = exportCheck.message || `免费版限制：只能导出 ${exportCheck.allowedCount} 条数据`;
        }
        
        // 记录本次导出的使用量（在导出时计数）
        await window.licenseManager.recordExport(dataToExport.length);
        console.log(`已记录导出使用量: ${dataToExport.length} 条`);
        
      } else {
        console.log('许可证管理器未加载，允许全部导出');
      }
      
      console.log('准备导出数据条数:', dataToExport.length);
      
      // 包含详情数据的字段
      const fields = ['title', 'url', 'href', 'description', 'detailText', 'hasDetail'];
      console.log('导出字段:', fields);
      
      // 创建CSV内容
      const csvRows = [];
      csvRows.push(fields.join(','));
      
      dataToExport.forEach(item => {
        const row = fields.map(field => {
          const value = item[field] || '';
          // 简单的CSV转义
          return `"${String(value).replace(/"/g, '""')}"`;
        });
        csvRows.push(row.join(','));
      });
      
      const csvString = csvRows.join('\n');
      console.log('CSV内容生成成功，长度:', csvString.length);
      
      // 创建下载
      const blob = new Blob(['\ufeff' + csvString], {
        type: 'text/csv;charset=utf-8;'
      });
      
      const url = URL.createObjectURL(blob);
      console.log('Blob URL创建成功:', url);
      
      // 使用Chrome下载API
      if (chrome.downloads) {
        chrome.downloads.download({
          url: url,
          filename: `mozibang_data_${new Date().toISOString().slice(0, 10)}.csv`,
          saveAs: true
        }, (downloadId) => {
          console.log('下载请求结果 - ID:', downloadId, 'Error:', chrome.runtime.lastError);
          
          if (chrome.runtime.lastError) {
            console.error('Chrome下载API出错:', chrome.runtime.lastError);
            // 尝试备用方法
            tryAlternativeDownload(url, csvString);
          } else {
            console.log('下载成功启动，ID:', downloadId);
            status.textContent = `已导出 ${dataToExport.length} 条数据`;
          }
          
          // 清理URL
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        });
      } else {
        console.log('Chrome downloads API不可用，使用备用方法');
        tryAlternativeDownload(url, csvString);
      }
      
      // 备用下载方法
      function tryAlternativeDownload(blobUrl, csvData) {
        console.log('尝试备用下载方法');
        
        // 方法1：创建临时链接
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = `mozibang_data_${new Date().toISOString().slice(0, 10)}.csv`;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        status.textContent = `已导出 ${dataToExport.length} 条数据（备用方法）`;
        console.log('备用下载方法执行完成');
      }
      
    } catch (error) {
      console.error('导出过程中出错:', error);
      status.textContent = '导出数据时出错：' + error.message;
    }
  });

  // 重置到免费版按钮
  resetToFreeBtn.addEventListener('click', async () => {
    if (confirm('确定要重置到免费版状态吗？这将清除Pro会员状态和使用统计。')) {
      try {
        resetToFreeBtn.disabled = true;
        resetToFreeBtn.textContent = '重置中...';
        status.textContent = '正在重置到免费版状态...';
        
        if (window.licenseManager) {
          const result = await window.licenseManager.resetToFreeUser();
          if (result.success) {
            status.textContent = result.message;
            // 更新UI状态
            await updateUIStatus();
          } else {
            status.textContent = '重置失败: ' + result.message;
          }
        } else {
          status.textContent = '许可证管理器未加载';
        }
      } catch (error) {
        console.error('重置过程中出错:', error);
        status.textContent = '重置时出错: ' + error.message;
      } finally {
        resetToFreeBtn.disabled = false;
        resetToFreeBtn.textContent = '重置免费版';
      }
    }
  });
  
  // 提取详情数据的函数
  async function extractDetailData(item, button) {
    console.log('=== 开始提取详情 ===', item.href);
    
    if (!item.href) {
      status.textContent = '无法提取详情：链接URL不存在';
      if (button) {
        button.disabled = false;
        button.textContent = '提取详情';
      }
      return;
    }

    try {
      status.textContent = '正在打开详情页面...';
      console.log('创建新标签页:', item.href);
      
      // 使用Promise包装chrome.tabs.create
      const tab = await new Promise((resolve, reject) => {
        chrome.tabs.create({
          url: item.href,
          active: false
        }, (newTab) => {
          if (chrome.runtime.lastError) {
            reject(chrome.runtime.lastError);
          } else {
            resolve(newTab);
          }
        });
      });
      
      console.log('标签页创建成功:', tab.id);
      
      // 等待页面加载并注入content script
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      console.log('开始发送消息到标签页:', tab.id);
      
      // 发送消息提取详情
      const response = await new Promise((resolve, reject) => {
        chrome.tabs.sendMessage(tab.id, {
          action: 'extractDetailData'
        }, (response) => {
          if (chrome.runtime.lastError) {
            console.error('发送消息错误:', chrome.runtime.lastError);
            reject(chrome.runtime.lastError);
          } else {
            console.log('收到响应:', response);
            resolve(response);
          }
        });
      });
      
      // 关闭标签页
      chrome.tabs.remove(tab.id);
      console.log('标签页已关闭');
      
      // 处理响应
      if (response && response.detailData) {
        // 直接更新bulkData数组
        const dataIndex = bulkData.findIndex(data => data.href === item.href);
        if (dataIndex !== -1) {
          bulkData[dataIndex].detailText = response.detailData.text;
          bulkData[dataIndex].hasDetail = true;
          console.log('成功更新详情到bulkData:', item.href);
        }
        
        // 更新显示中的徽章
        const rows = document.querySelectorAll('.data-table tbody tr');
        const rowsArray = Array.from(rows);
        const targetRow = rowsArray.find(row => {
          const linkCell = row.querySelector('td:nth-child(2) a');
          return linkCell && linkCell.href === item.href;
        });
        
        if (targetRow) {
          const titleCell = targetRow.querySelector('td:first-child');
          if (titleCell && !titleCell.querySelector('.detail-badge')) {
            const badge = document.createElement('span');
            badge.className = 'detail-badge';
            badge.textContent = '已提取详情';
            titleCell.appendChild(badge);
          }
        }
        
        status.textContent = `✅ 成功提取详情：${item.title || item.href}`;
      } else {
        status.textContent = '⚠️ 未找到详情数据';
      }
      
    } catch (error) {
      console.error('❌ 提取详情失败:', error);
      status.textContent = '❌ 提取详情失败：' + error.message;
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = '提取详情';
      }
    }
  }
  
  // 显示详情数据
  function displayDetailData(item, detailData) {
    const detailModal = document.createElement('div');
    detailModal.className = 'detail-modal';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    
    const modalTitle = document.createElement('h3');
    modalTitle.textContent = item.title || item.href;
    modalContent.appendChild(modalTitle);
    
    const modalLink = document.createElement('a');
    modalLink.href = item.href;
    modalLink.textContent = item.href;
    modalLink.target = '_blank';
    modalContent.appendChild(modalLink);
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'detail-content';
    
    if (detailData.text) {
      const textContent = document.createElement('div');
      textContent.className = 'detail-text';
      textContent.textContent = detailData.text;
      contentDiv.appendChild(textContent);
    }
    
    modalContent.appendChild(contentDiv);
    
    const closeButton = document.createElement('button');
    closeButton.className = 'button';
    closeButton.textContent = '关闭';
    closeButton.addEventListener('click', () => {
      document.body.removeChild(detailModal);
    });
    modalContent.appendChild(closeButton);
    
    detailModal.appendChild(modalContent);
    document.body.appendChild(detailModal);
  }
  
  // 批量提取详情数据
  extractBulkDetailBtn.addEventListener('click', async () => {
    console.log('开始批量提取详情，bulkData长度:', bulkData.length);
    
    if (bulkData.length === 0) {
      status.textContent = '没有可提取详情的数据';
      return;
    }
    
    const itemsToProcess = bulkData.filter(item => !item.hasDetail && item.href)
      .map((item, index) => ({ 
        href: item.href, 
        title: item.title || '',
        index: index
      }));
    
    console.log('创建详情队列，共', itemsToProcess.length, '项');
    
    if (itemsToProcess.length === 0) {
      status.textContent = '所有数据已提取详情';
      return;
    }
    
    // 详情提取也不限制，在导出时才计算
    extractBulkDetailBtn.disabled = true;
    extractBulkDetailBtn.textContent = '提取中...';
    
    if (itemsToProcess.length === 0) {
      status.textContent = '所有数据已提取详情';
      extractBulkDetailBtn.textContent = '批量提取详情';
      extractBulkDetailBtn.disabled = false;
      return;
    }
    
    const progressContainer = document.getElementById('progressContainer');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    const progressBar = document.getElementById('progressBar');
    
    progressContainer.style.display = 'block';
    progressText.textContent = `0/${itemsToProcess.length}`;
    progressPercent.textContent = '0%';
    progressBar.style.width = '0%';
    
    status.textContent = `开始批量提取详情，共 ${itemsToProcess.length} 项`;
    
    const batchId = Date.now().toString();
    
    const forceCloseAllTabs = () => {
      return new Promise((resolve) => {
        const openTabIds = Object.values(openedTabs);
        if (openTabIds.length > 0) {
          console.log('尝试强制关闭所有已打开的标签页:', openTabIds);
          
          const closePromises = openTabIds.map(tabId => {
            return new Promise(resolveTab => {
              chrome.runtime.sendMessage({
                action: 'forceCloseTab',
                tabId: tabId
              }, (response) => {
                if (chrome.runtime.lastError) {
                  console.error('关闭标签页时出错:', chrome.runtime.lastError);
                } else {
                  console.log('标签页关闭结果:', response);
                }
                resolveTab();
              });
            });
          });
          
          Promise.all(closePromises).then(() => {
            console.log('所有标签页关闭操作已完成');
            openedTabs = {};
            resolve();
          });
        } else {
          console.log('没有需要关闭的标签页');
          resolve();
        }
      });
    };
    
    forceCloseAllTabs().then(() => {
      chrome.runtime.sendMessage({
        action: 'extractBulkDetails',
        items: itemsToProcess,
        batchId: batchId
      }, async (response) => {
        console.log('批量提取详情完成，结果:', response);
        
        progressContainer.style.display = 'none';
        
        if (chrome.runtime.lastError) {
          console.error('批量提取详情时出错：', chrome.runtime.lastError);
          status.textContent = '批量提取详情时出错：' + chrome.runtime.lastError.message;
        } else if (response && response.results) {
          response.results.forEach((result, i) => {
            if (!result || result.error) {
              console.error('提取详情数据时出错：', result ? result.error : '未知错误');
              return;
            }
            
            const originalItem = itemsToProcess[i];
            const dataIndex = bulkData.findIndex(data => data.href === originalItem.href);
            
            if (dataIndex !== -1) {
              bulkData[dataIndex].detailText = result.detailData.text;
              bulkData[dataIndex].hasDetail = true;
              
              const rows = document.querySelectorAll('.data-table tbody tr');
              if (rows[dataIndex]) {
                const titleCell = rows[dataIndex].querySelector('td:first-child');
                if (titleCell && !titleCell.querySelector('.detail-badge')) {
                  const badge = document.createElement('span');
                  badge.className = 'detail-badge';
                  badge.textContent = '已提取详情';
                  titleCell.appendChild(badge);
                }
              }
            }
          });
          
          const successCount = response.results.filter(r => r && !r.error).length;
          
          // 详情提取也不记录使用量，只在导出时记录
          if (successCount > 0) {
            try {
              await updateUIStatus();
            } catch (error) {
              console.error('更新UI状态失败:', error);
            }
          }
          
          status.textContent = `批量提取详情完成，成功提取 ${successCount} 项`;
        } else {
          status.textContent = '批量提取详情完成，但未返回结果';
        }
        
        extractBulkDetailBtn.disabled = false;
        extractBulkDetailBtn.textContent = '批量提取详情';
        
        // 重新显示更新后的数据
        displayBulkData(bulkData.slice(0, 10), bulkData.length);
      });
    });
  });
  
  // 添加详情弹窗样式
  const style = document.createElement('style');
  style.textContent = `
    .detail-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background-color: rgba(0, 0, 0, 0.5);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }
    
    .modal-content {
      background-color: white;
      padding: 20px;
      border-radius: 8px;
      max-width: 80%;
      max-height: 80%;
      overflow: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .detail-content {
      border: 1px solid #e8eaed;
      padding: 12px;
      border-radius: 4px;
      max-height: 300px;
      overflow: auto;
    }
    
    .detail-text {
      white-space: pre-wrap;
      font-size: 14px;
      line-height: 1.5;
    }
    
    .action-button {
      margin-right: 4px;
      padding: 4px 8px;
      background-color: #4285f4;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
    }
    
    .action-button:hover {
      background-color: #3367d6;
    }
    
    .action-button:disabled {
      background-color: #ccc;
      cursor: not-allowed;
    }
    
    .detail-badge {
      display: inline-block;
      margin-left: 8px;
      padding: 2px 6px;
      background-color: #34a853;
      color: white;
      border-radius: 4px;
      font-size: 10px;
      vertical-align: middle;
    }
    
    .bulk-detail-btn {
      background-color: #fbbc05;
    }
    
    .bulk-detail-btn:hover {
      background-color: #f9a825;
    }
    
    .bulk-detail-btn:disabled {
      background-color: #ccc;
      cursor: not-allowed;
    }
  `;
  document.head.appendChild(style);
});

// 监听详情提取进度更新
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'updateDetailProgress' && message.total > 0) {
    const progressContainer = document.getElementById('progressContainer');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    const progressBar = document.getElementById('progressBar');
    
    if (progressContainer) {
      progressContainer.style.display = 'block';
      const percent = Math.round((message.current / message.total) * 100);
      progressText.textContent = `${message.current}/${message.total}`;
      progressPercent.textContent = `${percent}%`;
      progressBar.style.width = `${percent}%`;
      
      const status = document.getElementById('status');
      if (status) {
        status.textContent = `正在提取详情 ${message.current}/${message.total}`;
      }
    }
  }
  return true;
});

// 安全地显示数据（只显示预览）
  async function displayBulkDataSecurely() {
    try {
      let dataToDisplay = [];
      let totalCount = 0;
      
      if (currentDataToken && window.secureDataManager) {
        const result = await window.secureDataManager.getStoredData(currentDataToken);
        if (result.success) {
          // 只显示前10条作为预览
          dataToDisplay = result.data.slice(0, 10);
          totalCount = result.data.length;
        }
      } else if (window.fallbackBulkData && window.fallbackBulkData.length > 0) {
        // 降级到内存数据
        dataToDisplay = window.fallbackBulkData.slice(0, 10);
        totalCount = window.fallbackBulkData.length;
      }
      
      // 确保dataContainer存在
      const dataContainer = document.getElementById('dataContainer');
      if (!dataContainer) {
        console.error('dataContainer元素未找到');
        return;
      }
      
      // 如果没有数据，显示空消息而不是错误
      if (dataToDisplay.length === 0 && totalCount === 0) {
        dataContainer.innerHTML = '<div class="empty-message">当前页面未找到符合条件的数据</div>';
        return;
      }
      
      displayBulkData(dataToDisplay, totalCount);
      
    } catch (error) {
      console.error('安全显示数据失败:', error);
      const dataContainer = document.getElementById('dataContainer');
      if (dataContainer) {
        dataContainer.innerHTML = '<div class="error">数据显示失败: ' + error.message + '</div>';
      }
    }
  }

  // 安全地获取完整数据（用于导出）
  async function getFullDataSecurely() {
    try {
      if (currentDataToken && window.secureDataManager) {
        const result = await window.secureDataManager.getStoredData(currentDataToken);
        if (result.success) {
          return result.data;
        }
      }
      
      // 降级到内存数据
      if (window.fallbackBulkData) {
        return window.fallbackBulkData;
      }
      
      return [];
    } catch (error) {
      console.error('获取完整数据失败:', error);
      return [];
    }
  }

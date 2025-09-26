// 监听扩展程序安装事件
chrome.runtime.onInstalled.addListener(() => {
  console.log('Web Data Extractor installed');
});
// 添加详情提取队列和并发控制变量
let detailExtractionQueue = [];
let isProcessingQueue = false;
const MAX_CONCURRENT_TABS = 2; // 设置最大并发标签页数量
let activeDetailPromises = []; // 存储活跃的提取任务

// 处理队列中的详情提取请求
async function processDetailQueue() {
  if (isProcessingQueue) return;
  isProcessingQueue = true;
  
  let processedCount = 0;
  const totalCount = detailExtractionQueue.length;
  
  // 发送初始进度
  chrome.runtime.sendMessage({
    action: 'updateDetailProgress',
    current: processedCount,
    total: totalCount
  });
  
  try {
    while (detailExtractionQueue.length > 0 || activeDetailPromises.length > 0) {
      // 如果活跃任务数小于限制且队列中还有任务，则启动新任务
      if (activeDetailPromises.length < MAX_CONCURRENT_TABS && detailExtractionQueue.length > 0) {
        const item = detailExtractionQueue.shift();
        console.log('处理队列项:', item.href);
        
        const taskPromise = processDetailItem(item);
        activeDetailPromises.push(taskPromise);
        
        // 任务完成后从活跃列表中移除并更新进度
        taskPromise.finally(() => {
          activeDetailPromises = activeDetailPromises.filter(p => p !== taskPromise);
          processedCount++;
          
          // 发送进度更新
          chrome.runtime.sendMessage({
            action: 'updateDetailProgress',
            current: processedCount,
            total: totalCount
          });
          
          console.log(`详情任务完成。活跃任务: ${activeDetailPromises.length}, 队列大小: ${detailExtractionQueue.length}, 进度: ${processedCount}/${totalCount}`);
        });
      } else if (activeDetailPromises.length > 0) {
        // 等待任意一个活跃任务完成
        await Promise.race(activeDetailPromises);
      } else {
        break;
      }
    }
  } finally {
    isProcessingQueue = false;
    console.log('所有详情提取任务处理完成');
  }
}

// 处理单个详情提取任务
// 处理单个详情提取任务
async function processDetailItem(item) {
  let tab = null;
  
  try {
    // 创建一个新标签页打开链接
    tab = await new Promise((resolve, reject) => {
      chrome.tabs.create({ url: item.href, active: false }, tab => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          console.log('已创建标签页:', tab.id);
          resolve(tab);
        }
      });
    });
    
    // 等待页面加载完成
    await new Promise(resolve => {
      const listener = function(tabId, changeInfo) {
        if (tabId === tab.id && changeInfo.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          console.log('页面加载完成:', tab.id);
          resolve();
        }
      };
      chrome.tabs.onUpdated.addListener(listener);
    });
    
    // 注入content script
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ['content.js']
    });
    console.log('已注入content script到标签页:', tab.id);
    
    // 向content script发送消息，请求提取详情数据
    const results = await new Promise((resolve, reject) => {
      chrome.tabs.sendMessage(tab.id, {
        action: 'extractDetailData'
      }, response => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          console.log('已接收详情数据:', tab.id);
          resolve(response);
        }
      });
    });
    
    // 发送结果回popup
    if (item.sendResponse) {
      item.sendResponse(results);
      console.log('已发送结果回popup');
    }
    
    return results;
  } catch (error) {
    console.error('Error processing detail item:', error);
    if (item.sendResponse) {
      item.sendResponse({ error: error.message || '提取详情时出错' });
    }
    throw error;
  } finally {
    // 确保标签页被关闭，即使发生错误
    if (tab && tab.id) {
      try {
        await forceCloseTab(tab.id);
      } catch (closeError) {
        console.error('关闭标签页时出错:', closeError);
      }
    }
  }
}

// 监听来自popup的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractData' || request.action === 'extractLinks' || 
      request.action === 'extractSpecificData' || request.action === 'extractBulkData') {
    // 获取当前标签页
    chrome.tabs.query({active: true, currentWindow: true}, async ([tab]) => {
      try {
        // 注入content script
        await chrome.scripting.executeScript({
          target: {tabId: tab.id},
          files: ['content.js']
        });
        
        // 向content script发送消息，请求提取数据
        const results = await chrome.tabs.sendMessage(tab.id, {
          action: request.action,
          dataType: request.dataType || 'all'
        });
        
        // 发送结果回popup
        sendResponse(results);
      } catch (error) {
        console.error('Error:', error);
        sendResponse({error: error.message});
      }
    });
    return true; // 保持消息通道开放
  } else if (request.action === 'extractDetailData') {
    console.log('收到提取详情请求:', request.href);
    // 将请求添加到队列
    detailExtractionQueue.push({
      href: request.href,
      title: request.title,
      sendResponse: sendResponse
    });
    
    // 开始处理队列（如果尚未开始）
    processDetailQueue();
    
    return true; // 保持消息通道开放
  } else if (request.action === 'extractBulkDetails') {
    // 新增：批量提取详情的处理
    console.log(`收到批量提取详情请求，共 ${request.items.length} 项`);
    
    // 将所有项添加到队列
    request.items.forEach(item => {
      detailExtractionQueue.push({
        href: item.href,
        title: item.title,
        index: item.index,
        batchId: request.batchId
      });
    });
    
    // 创建一个Map来存储批处理结果
    const batchResults = new Map();
    
    // 为每个项目设置一个Promise
    const resultPromises = request.items.map(item => {
      return new Promise(resolve => {
        const originalSendResponse = detailExtractionQueue.find(
          qItem => qItem.href === item.href && qItem.batchId === request.batchId
        ).sendResponse;
        
        detailExtractionQueue.find(
          qItem => qItem.href === item.href && qItem.batchId === request.batchId
        ).sendResponse = (result) => {
          batchResults.set(item.index, result);
          resolve(result);
          if (originalSendResponse) originalSendResponse(result);
        };
      });
    });
    
    // 开始处理队列
    processDetailQueue();
    
    // 等待所有结果完成并发送回popup
    Promise.all(resultPromises).then(() => {
      const resultsArray = Array.from(batchResults.entries())
        .sort((a, b) => a[0] - b[0])
        .map(entry => entry[1]);
      
      sendResponse({
        batchId: request.batchId,
        results: resultsArray
      });
    });
    
    return true; // 保持消息通道开放
  } else if (request.action === 'forceCloseTab') {
    // 新增：强制关闭指定标签页
    if (request.tabId) {
      forceCloseTab(request.tabId).then(() => {
        sendResponse({success: true});
      }).catch(error => {
        sendResponse({success: false, error: error.message});
      });
      return true; // 保持消息通道开放
    }
  }
});

// 强制关闭标签页的函数
async function forceCloseTab(tabId) {
  return new Promise((resolve) => {
    // 先尝试常规方式关闭
    chrome.tabs.remove(tabId, () => {
      const error = chrome.runtime.lastError;
      if (error) {
        console.warn('常规关闭标签页失败:', error.message);
        
        // 如果常规方式失败，尝试查询标签页是否存在，然后再次尝试关闭
        chrome.tabs.get(tabId, (tab) => {
          if (chrome.runtime.lastError) {
            // 标签页不存在或已关闭
            console.log('标签页已不存在:', tabId);
            resolve();
          } else {
            // 标签页仍然存在，尝试再次关闭
            chrome.tabs.remove(tabId, () => {
              if (chrome.runtime.lastError) {
                console.error('二次关闭标签页失败:', chrome.runtime.lastError.message);
              } else {
                console.log('二次关闭标签页成功:', tabId);
              }
              resolve();
            });
          }
        });
      } else {
        console.log('标签页已成功关闭:', tabId);
        resolve();
      }
    });
  });
}
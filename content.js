// 监听来自popup的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractBulkData') {
    // 根据不同的网站类型选择不同的选择器
    let selector = '';
    let dataItems = [];
    
    // 检测页面类型并选择合适的选择器
    if (document.querySelectorAll('a.sites-body').length >= 1) { // 降低阈值
      // 示例网站类型1 - 网站卡片
      selector = 'a.sites-body';
      dataItems = Array.from(document.querySelectorAll(selector));
    } else if (document.querySelectorAll('a[data-id][data-url]').length >= 1) { // 降低阈值
      // 示例网站类型2 - 带有data-id和data-url属性的链接
      selector = 'a[data-id][data-url]';
      dataItems = Array.from(document.querySelectorAll(selector));
    } else {
      // 尝试其他可能的选择器
      const possibleSelectors = [
        'a.item', 
        '.card a', 
        '.product a', 
        '.site-item a',
        'a[data-id]',
        'a[data-url]'
      ];
      
      for (const sel of possibleSelectors) {
        const elements = document.querySelectorAll(sel);
        if (elements.length >= 1) { // 降低阈值
          selector = sel;
          dataItems = Array.from(elements);
          break;
        }
      }
    }
    
    // 如果没有找到足够的数据项，尝试提取所有链接
    if (dataItems.length < 1) { // 降低阈值，从20改为1
      selector = 'a';
      dataItems = Array.from(document.querySelectorAll('a')).filter(a => {
        // 过滤掉导航链接、空链接等
        const href = a.href || '';
        const text = a.textContent.trim();
        return href && 
               !href.startsWith('javascript:') && 
               !href.startsWith('#') && 
               text !== '' &&
               text.length > 1 && // 确保有实际内容
               !a.classList.contains('nav-link') &&
               !a.classList.contains('menu-item') &&
               !a.classList.contains('header-link') &&
               !a.classList.contains('footer-link') &&
               !href.includes('javascript:void') &&
               !text.match(/^(首页|主页|登录|注册|关于|联系|帮助)$/); // 排除常见导航词
      });
    }
    
    // 提取数据
    const extractedData = dataItems.map(item => {
      // 基本数据
      const data = {
        url: item.getAttribute('data-url') || '',
        href: item.href || '',
        title: item.title || ''
      };
      
      // 提取标题文本 - 尝试多种可能的标题元素
      if (!data.title) {
        const titleElement = 
          item.querySelector('.item-title') || 
          item.querySelector('h3') || 
          item.querySelector('h2') || 
          item.querySelector('strong') || 
          item.querySelector('b');
        
        if (titleElement) {
          data.title = titleElement.textContent.trim();
        } else if (item.textContent.trim()) {
          // 如果没有找到标题元素，使用链接文本
          data.title = item.textContent.trim();
        }
      }
      
      // 提取描述
      const descElement = 
        item.querySelector('.text-muted') || 
        item.querySelector('.description') || 
        item.querySelector('p');
      
      if (descElement) {
        data.description = descElement.textContent.trim();
      }
      
      // 提取图片
      const imgElement = 
        item.querySelector('img.sites-icon') || 
        item.querySelector('img');
      
      if (imgElement) {
        data.image = imgElement.getAttribute('data-src') || imgElement.src || '';
      }
      
      return data;
    });
    
    // 过滤掉不完整的数据
    const validData = extractedData.filter(item => {
      // 至少要有URL和标题
      return (item.url || item.href) && item.title;
    });
    
    sendResponse({
      extractedData: validData,
      count: validData.length,
      selector: selector,
      pageTitle: document.title,
      url: window.location.href
    });
  }
  else if (request.action === 'extractData' || request.action === 'extractLinks' || request.action === 'extractSpecificData') {
    // 保留原有功能的代码
    const dataType = request.dataType || 'all';
    let extractedData = {};
    
    // 提取链接数据
    if (dataType === 'links' || dataType === 'all') {
      const links = Array.from(document.querySelectorAll('a')).map(link => {
        return {
          href: link.href || '',
          dataUrl: link.getAttribute('data-url') || '',
          title: link.title || link.textContent.trim() || '',
          dataBg: link.getAttribute('data-bg') || ''
        };
      });
      
      extractedData.links = links;
    }
    
    // 提取图片数据
    if (dataType === 'images' || dataType === 'all') {
      const images = Array.from(document.querySelectorAll('img')).map(img => {
        return {
          src: img.src || '',
          alt: img.alt || '',
          title: img.title || '',
          width: img.width || '',
          height: img.height || '',
          naturalWidth: img.naturalWidth || '',
          naturalHeight: img.naturalHeight || ''
        };
      });
      
      extractedData.images = images;
    }
    
    // 提取表格数据
    if (dataType === 'tables' || dataType === 'all') {
      const tables = Array.from(document.querySelectorAll('table')).map((table, tableIndex) => {
        const rows = Array.from(table.querySelectorAll('tr'));
        const headers = Array.from(rows[0]?.querySelectorAll('th') || []).map(th => th.textContent.trim());
        
        const tableData = rows.slice(headers.length > 0 ? 1 : 0).map(row => {
          const cells = Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim());
          return cells;
        });
        
        return {
          index: tableIndex,
          headers: headers,
          data: tableData
        };
      });
      
      extractedData.tables = tables;
    }
    
    // 提取元数据
    if (dataType === 'metadata' || dataType === 'all') {
      const metadata = {
        title: document.title,
        url: window.location.href,
        description: document.querySelector('meta[name="description"]')?.getAttribute('content') || '',
        keywords: document.querySelector('meta[name="keywords"]')?.getAttribute('content') || '',
        author: document.querySelector('meta[name="author"]')?.getAttribute('content') || '',
        ogTitle: document.querySelector('meta[property="og:title"]')?.getAttribute('content') || '',
        ogDescription: document.querySelector('meta[property="og:description"]')?.getAttribute('content') || '',
        ogImage: document.querySelector('meta[property="og:image"]')?.getAttribute('content') || ''
      };
      
      extractedData.metadata = metadata;
    }
    
    // 提取文本内容
    if (dataType === 'text' || dataType === 'all') {
      // 获取主要内容区域的文本
      const mainContent = document.querySelector('.content') || 
                          document.querySelector('#content');
      
      const textContent = mainContent ? 
        mainContent.textContent.trim() : 
        document.body.textContent.trim();
      
      // 获取所有段落
      const paragraphs = Array.from(document.querySelectorAll('p')).map(p => p.textContent.trim());
      
      // 获取所有标题
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(h => ({
        level: parseInt(h.tagName.substring(1)),
        text: h.textContent.trim()
      }));
      
      extractedData.text = {
        fullText: textContent,
        paragraphs: paragraphs,
        headings: headings
      };
    }
    
    // 返回提取的数据
    sendResponse({
      extractedData: extractedData,
      pageTitle: document.title,
      url: window.location.href
    });
  }
  else if (request.action === 'extractDetailData') {
    // 定位到指定的div标签
    const specificSelector = 'div.panel-body.single';
    const specificContent = document.querySelector(specificSelector);
    
    let combinedText = '';
    
    if (specificContent) {
      console.log('找到指定的div标签');
      
      // 方法1：获取所有文本内容，包括所有子元素
      combinedText = specificContent.innerText;
      
      // 方法2（备选）：如果想要更精确控制，可以提取特定标签
      // const textElements = Array.from(specificContent.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div:not(:has(*))'));
      // const texts = textElements.map(el => el.textContent.trim()).filter(text => text);
      // combinedText = texts.join('\n\n');
      
      // 如果没有找到任何文本内容，确保返回空字符串
      if (combinedText.trim() === '') {
        combinedText = '';
      }
      
      // 如果内容过长，可以考虑截断
      // const maxLength = 1000000; // 设置一个合理的最大长度
      // if (combinedText.length > maxLength) {
      //   combinedText = combinedText.substring(0, maxLength) + '\n\n[内容过长，已截断]';
      // }
    } else {
      // 如果找不到特定结构，返回空字符串
      console.error('未找到指定的div标签');
      combinedText = '';
    }
    
    // 返回提取的详情数据
    sendResponse({
      detailData: {
        text: combinedText,
        url: window.location.href,
        title: document.title
      }
    });
  }
  return true; // 保持消息通道开放
});
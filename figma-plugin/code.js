// MineContext Figma Plugin - API Connector
// 让Figma能够调用MineContext Glass后端API

const MINECONTEXT_API_BASE = "http://localhost:8000"; // 可配置的API基础URL

// HTTP请求封装
async function apiRequest(endpoint, options = {}) {
  const url = `${MINECONTEXT_API_BASE}${endpoint}`;
  const defaultOptions = {
    headers: {
      'Accept': 'application/json',
    },
    credentials: 'include',
  };

  const finalOptions = { ...defaultOptions, ...options };

  try {
    const response = await fetch(url, finalOptions);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API请求失败: ${endpoint}`, error);
    throw error;
  }
}

// 获取上传配额
async function fetchUploadLimits() {
  const response = await apiRequest('/glass/uploads/limits');
  return response.data;
}

// 获取时间线列表
async function fetchTimelines() {
  const response = await apiRequest('/glass/timelines');
  return response.data;
}

// 上传视频文件
async function uploadVideo(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiRequest('/glass/upload', {
    method: 'POST',
    body: formData,
    headers: {} // 让浏览器自动设置Content-Type
  });

  return response.data;
}

// 获取日报
async function fetchDailyReport(timelineId) {
  const response = await apiRequest(`/glass/report/${timelineId}`);
  return response.data;
}

// 生成日报
async function generateDailyReport(timelineId) {
  const response = await apiRequest(`/glass/report/${timelineId}/generate`, {
    method: 'POST',
  });
  return response.data;
}

// Figma Plugin主逻辑
figma.showUI(__html__, { width: 400, height: 600 });

// 接收来自UI的消息
figma.ui.onmessage = async (msg) => {
  try {
    switch (msg.type) {
      case 'fetch-limits':
        const limits = await fetchUploadLimits();
        figma.ui.postMessage({ type: 'limits-result', data: limits });
        break;

      case 'fetch-timelines':
        const timelines = await fetchTimelines();
        figma.ui.postMessage({ type: 'timelines-result', data: timelines });
        break;

      case 'upload-video':
        // Figma Plugin中无法直接处理文件上传
        // 需要通过UI层处理
        figma.ui.postMessage({
          type: 'upload-error',
          error: '请使用UI界面的文件选择功能'
        });
        break;

      case 'fetch-report':
        const report = await fetchDailyReport(msg.timelineId);
        figma.ui.postMessage({ type: 'report-result', data: report });
        break;

      case 'generate-report':
        const genResult = await generateDailyReport(msg.timelineId);
        figma.ui.postMessage({ type: 'generate-result', data: genResult });
        break;

      case 'update-api-base':
        // 更新API基础URL
        globalThis.MINECONTEXT_API_BASE = msg.apiBase;
        figma.ui.postMessage({ type: 'api-base-updated' });
        break;

      default:
        figma.ui.postMessage({
          type: 'error',
          error: `未知消息类型: ${msg.type}`
        });
    }
  } catch (error) {
    figma.ui.postMessage({
      type: 'error',
      error: error.message
    });
  }
};
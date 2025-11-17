const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
    // 后端状态检查
    checkBackendStatus: () => ipcRenderer.invoke('check-backend-status'),
    getBackendPort: () => ipcRenderer.invoke('get-backend-port'),

    // 系统操作
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    showMessageBox: (options) => ipcRenderer.invoke('show-message-box', options),
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),

    // 应用控制
    quitApp: () => ipcRenderer.invoke('quit-app'),
    minimizeApp: () => ipcRenderer.invoke('minimize-app'),
    restartBackend: () => ipcRenderer.invoke('restart-backend'),

    // 平台信息
    platform: process.platform,
    versions: process.versions,

    // 事件监听
    onBackendReady: (callback) => {
        ipcRenderer.on('backend-ready', (event, port) => callback(port));
    },
    onBackendError: (callback) => {
        ipcRenderer.on('backend-error', (event, error) => callback(error));
    },

    // 移除监听器
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    }
});

// 开发环境下的调试信息
if (process.env.NODE_ENV === 'development') {
    console.log('Preload script loaded');
    console.log('Platform:', process.platform);
}
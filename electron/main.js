const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let mainWindow;
let backendProcess;
let backendPort;
let frontendPort = 5174; // 默认端口，Vite 会自动切换

function createWindow() {
    console.log('🚀 创建 Electron 主窗口...');
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 1000,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../assets/app.icns'),
        show: false  // 先不显示，等后端启动
    });

    console.log('📡 启动后端服务...');
    // 启动后端
    startBackend();

    // 监听后端启动完成
    const checkBackend = setInterval(() => {
        if (backendPort) {
            clearInterval(checkBackend);
            console.log(`✅ 后端已启动，端口: ${backendPort}`);
            console.log(`🌐 开始连接前端服务器...`);

            // 加载前端
            console.log(`🔍 检查环境变量: NODE_ENV = ${process.env.NODE_ENV}`);
            if (process.env.NODE_ENV === 'development' || true) {  // 临时强制开发模式
                console.log('🔧 开发模式：智能检测Vite开发服务器端口');
                // 开发模式：智能检测Vite开发服务器端口
                const tryLoadFrontend = async (startPort) => {
                    for (let port = startPort; port < 5185; port++) {
                        try {
                            console.log(`尝试连接前端端口 ${port}，后端端口: ${backendPort}...`);
                            await mainWindow.loadURL(`http://localhost:${port}?backend_port=${backendPort}`);
                            console.log(`✅ 成功连接到前端端口 ${port}`);
                            frontendPort = port;

                            // 发送后端就绪信号到前端
                            mainWindow.webContents.once('did-finish-load', () => {
                                console.log('📡 前端加载完成，发送后端端口信息');
                                mainWindow.webContents.send('backend-ready', backendPort);
                            });

                            return;
                        } catch (error) {
                            console.log(`❌ 端口 ${port} 连接失败，尝试下一个端口...`);
                            // 继续尝试下一个端口
                        }
                    }
                    throw new Error('无法连接到前端开发服务器，请确保 npm run dev 正在运行');
                };

                // 从5174开始尝试（默认Vite端口）
                tryLoadFrontend(5174);
            } else {
                // 生产模式：加载构建的静态文件
                mainWindow.loadFile(path.join(__dirname, '../frontend/dist/index.html'));
            }

            mainWindow.show();

            // 强制打开开发者工具进行调试
            mainWindow.webContents.openDevTools();
        }
    }, 100);

    // 应用退出时清理
    mainWindow.on('closed', () => {
        if (backendProcess) {
            backendProcess.kill('SIGTERM');
        }
    });
}

function startBackend() {
    const backendScript = path.join(__dirname, '../backend/main.py');

    // 使用uv运行Python后端，确保依赖正确加载
    backendProcess = spawn('uv', ['run', 'python', backendScript], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: path.join(__dirname, '..')
    });

    // 监听后端输出
    backendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`Backend: ${output}`);

        // 解析端口信息
        const portMatch = output.match(/BACKEND_PORT:(\d+)/);
        if (portMatch && !backendPort) {
            backendPort = parseInt(portMatch[1]);
            mainWindow.webContents.send('backend-ready', backendPort);
        }
    });

    backendProcess.stderr.on('data', (data) => {
        const output = data.toString();

        // 区分错误和普通日志
        if (output.includes('ERROR:') || output.includes('Error:') || output.includes('error:')) {
            console.error(`Backend Error: ${output}`);

            // 解析错误信息
            const errorMatch = output.match(/BACKEND_ERROR:(.+)/);
            if (errorMatch) {
                mainWindow.webContents.send('backend-error', errorMatch[1]);
            }
        } else {
            // 普通日志也显示为 stdout
            console.log(`Backend: ${output}`);
        }
    });

    backendProcess.on('close', (code) => {
        console.log(`Backend process exited with code ${code}`);
        if (code !== 0) {
            mainWindow.webContents.send('backend-error', `后端进程异常退出，代码: ${code}`);
        }
    });

    backendProcess.on('error', (error) => {
        console.error(`Failed to start backend: ${error}`);
        mainWindow.webContents.send('backend-error', `后端启动失败: ${error.message}`);
    });
}

// IPC处理程序
ipcMain.handle('get-backend-port', () => backendPort);

ipcMain.handle('check-backend-status', () => {
    return {
        running: !!backendProcess && !backendProcess.killed,
        port: backendPort,
        pid: backendProcess ? backendProcess.pid : null
    };
});

ipcMain.handle('restart-backend', async () => {
    if (backendProcess) {
        backendProcess.kill('SIGTERM');
        backendProcess = null;
        backendPort = null;
    }

    // 重新启动后端
    startBackend();

    // 等待后端启动
    return new Promise((resolve) => {
        const checkPort = () => {
            if (backendPort) {
                resolve(backendPort);
            } else {
                setTimeout(checkPort, 100);
            }
        };
        checkPort();
    });
});

// 应用程序事件
app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    if (backendProcess) {
        backendProcess.kill('SIGTERM');
    }
});

// 开发环境下的热重载
if (process.env.NODE_ENV === 'development') {
    try {
        require('electron-reload')(__dirname, {
            electron: require(`${__dirname}/../../node_modules/.bin/electron`),
            hardResetMethod: 'exit'
        });
    } catch (error) {
        console.log('electron-reload not available');
    }
}
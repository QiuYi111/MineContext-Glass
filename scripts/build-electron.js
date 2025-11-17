#!/usr/bin/env node

/**
 * MineContext Glass Electron应用构建脚本
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 开始构建 MineContext Glass Electron应用...');

// 检查必要文件
function checkRequiredFiles() {
    const requiredFiles = [
        'package.json',
        'electron/main.js',
        'electron/preload.js',
        'backend/main.py',
        'webui/package.json'
    ];

    for (const file of requiredFiles) {
        if (!fs.existsSync(file)) {
            console.error(`❌ 缺少必要文件: ${file}`);
            process.exit(1);
        }
    }
    console.log('✅ 必要文件检查通过');
}

// 清理旧的构建产物
function cleanBuild() {
    const dirsToClean = [
        'dist-electron',
        'backend/dist'
    ];

    for (const dir of dirsToClean) {
        if (fs.existsSync(dir)) {
            fs.rmSync(dir, { recursive: true, force: true });
            console.log(`🧹 清理目录: ${dir}`);
        }
    }
}

// 构建前端
function buildFrontend() {
    return new Promise((resolve, reject) => {
        console.log('🎨 构建前端...');
        const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
        const process = spawn(npm, ['run', 'build-frontend'], {
            stdio: 'inherit',
            cwd: process.cwd()
        });

        process.on('close', (code) => {
            if (code === 0) {
                console.log('✅ 前端构建完成');
                resolve();
            } else {
                console.error('❌ 前端构建失败');
                reject(new Error(`Frontend build failed with code ${code}`));
            }
        });
    });
}

// 构建后端
function buildBackend() {
    return new Promise((resolve, reject) => {
        console.log('🐍 构建Python后端...');
        const python = process.platform === 'win32' ? 'python.exe' : 'python3';
        const process = spawn(python, ['-m', 'PyInstaller', '--onefile', '--name', 'backend', 'backend/main.py'], {
            stdio: 'inherit',
            cwd: process.cwd()
        });

        process.on('close', (code) => {
            if (code === 0) {
                console.log('✅ 后端构建完成');
                resolve();
            } else {
                console.error('❌ 后端构建失败');
                reject(new Error(`Backend build failed with code ${code}`));
            }
        });
    });
}

// 构建Electron应用
function buildElectron() {
    return new Promise((resolve, reject) => {
        console.log('⚡ 构建Electron应用...');
        const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
        const process = spawn(npm, ['run', 'build-electron'], {
            stdio: 'inherit',
            cwd: process.cwd()
        });

        process.on('close', (code) => {
            if (code === 0) {
                console.log('✅ Electron应用构建完成');
                resolve();
            } else {
                console.error('❌ Electron应用构建失败');
                reject(new Error(`Electron build failed with code ${code}`));
            }
        });
    });
}

// 主构建流程
async function main() {
    try {
        checkRequiredFiles();
        cleanBuild();

        // 并行构建前端和后端
        await Promise.all([
            buildFrontend(),
            buildBackend()
        ]);

        // 构建Electron应用
        await buildElectron();

        console.log('\n🎉 构建完成！');
        console.log('📦 应用包位置: dist-electron/');
        console.log('🔧 运行应用: npm run electron');

    } catch (error) {
        console.error('\n💥 构建失败:', error.message);
        process.exit(1);
    }
}

// 运行构建
main();
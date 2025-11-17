#!/usr/bin/env python3
"""
MineContext Glass Python后端服务入口
用于Electron应用中的子进程启动
"""

import sys
import socket
import threading
import time
import json
from pathlib import Path

# 添加项目路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 注意：在实际使用中，Electron会通过uv运行这个脚本
from opencontext.cli import main as opencontext_main


class GlassBackend:
    def __init__(self):
        self.port = None
        self.server = None
        self.ready = False

    def get_available_port(self):
        """获取可用端口"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    def start(self):
        """启动后端服务"""
        try:
            # 获取可用端口
            self.port = self.get_available_port()

            # 输出端口信息给父进程
            print(f"BACKEND_PORT:{self.port}", flush=True)

            # 配置命令行参数
            sys.argv = [
                'opencontext',
                'start',
                f'--port={self.port}',
                '--no-capture'
            ]

            # 启动服务器
            opencontext_main()

        except Exception as e:
            print(f"BACKEND_ERROR:{str(e)}", flush=True)
            return False

        return True


if __name__ == "__main__":
    backend = GlassBackend()
    if backend.start():
        print(f"后端服务启动成功，端口: {backend.port}")
    else:
        print("后端服务启动失败")
        sys.exit(1)
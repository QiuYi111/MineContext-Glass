#!/usr/bin/env python3
"""
ChromaDB延迟加载管理器
解决首次启动ONNX模型下载阻塞问题
"""

import os
import time
import threading
from pathlib import Path
from typing import Optional, Callable
from loguru import logger
import requests

class ChromaDBManager:
    """ChromaDB延迟加载管理器"""

    _instance = None
    _client = None
    _preloading = False
    _preload_callback = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._model_cache_dir = Path.home() / ".cache" / "chroma" / "onnx_models"
        self._required_model = "all-MiniLM-L6-v2"
        self._model_url = "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz"

    def is_model_downloaded(self) -> bool:
        """检查ONNX模型是否已下载"""
        model_dir = self._model_cache_dir / self._required_model
        return model_dir.exists() and any(model_dir.iterdir())

    def preload_model(self, callback: Optional[Callable] = None):
        """后台预下载ONNX模型"""
        if self.is_model_downloaded() or self._preloading:
            return

        self._preloading = True
        self._preload_callback = callback

        def download_model():
            try:
                logger.info("开始预下载ChromaDB ONNX模型...")

                # 确保目录存在
                self._model_cache_dir.mkdir(parents=True, exist_ok=True)

                # 使用ChromaDB自己的下载机制
                import chromadb
                client = chromadb.Client()
                # 这会触发模型下载
                collection = client.get_or_create_collection("preload_test")
                collection.add(
                    documents=["预加载测试文档"],
                    ids=["preload_doc"]
                )

                # 清理测试数据
                client.delete_collection("preload_test")

                logger.info("ChromaDB ONNX模型预下载完成")

                if self._preload_callback:
                    self._preload_callback(True)

            except Exception as e:
                logger.error(f"ChromaDB模型预下载失败: {e}")
                if self._preload_callback:
                    self._preload_callback(False)
            finally:
                self._preloading = False

        # 后台线程下载
        thread = threading.Thread(target=download_model, daemon=True)
        thread.start()

    def get_client(self):
        """获取ChromaDB客户端，实现延迟加载"""
        if self._client is None:
            logger.info("初始化ChromaDB客户端...")
            start_time = time.time()

            import chromadb
            self._client = chromadb.Client()

            init_time = time.time() - start_time
            logger.info(f"ChromaDB客户端初始化完成，耗时: {init_time:.2f}秒")

        return self._client

    def get_collection(self, name: str):
        """获取集合，自动处理初始化"""
        if not self.is_model_downloaded():
            logger.warning("ChromaDB模型尚未下载完成，功能可能受限")

        client = self.get_client()
        return client.get_or_create_collection(name)

    def get_model_info(self) -> dict:
        """获取模型状态信息"""
        model_dir = self._model_cache_dir / self._required_model

        info = {
            "model_name": self._required_model,
            "model_dir": str(model_dir),
            "downloaded": self.is_model_downloaded(),
            "preloading": self._preloading,
        }

        if self.is_model_downloaded():
            try:
                # 检查模型文件大小
                total_size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                info["model_size_mb"] = round(total_size / 1024 / 1024, 1)
            except Exception as e:
                logger.warning(f"无法获取模型大小: {e}")

        return info


# 全局实例
_chromadb_manager = ChromaDBManager()

def get_chromadb_manager() -> ChromaDBManager:
    """获取ChromaDB管理器实例"""
    return _chromadb_manager

def lazy_get_collection(name: str):
    """便捷函数：延迟加载获取集合"""
    return get_chromadb_manager().get_collection(name)

def preload_chromadb_model(callback: Optional[Callable] = None):
    """便捷函数：预下载模型"""
    return get_chromadb_manager().preload_model(callback)
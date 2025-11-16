#!/usr/bin/env python3
"""测试ChromaDB启动时间"""

import time
import sys
from pathlib import Path

def test_chromadb_startup():
    """测试ChromaDB启动时间"""
    print("开始测试ChromaDB启动时间...")

    # 测试1：导入时间
    start_time = time.time()
    import chromadb
    import_time = time.time() - start_time
    print(f"ChromaDB导入时间: {import_time:.2f}秒")

    # 测试2：客户端初始化时间
    start_time = time.time()
    client = chromadb.Client()
    client_init_time = time.time() - start_time
    print(f"ChromaDB客户端初始化时间: {client_init_time:.2f}秒")

    # 测试3：创建集合时间
    start_time = time.time()
    collection = client.get_or_create_collection("test_collection")
    collection_init_time = time.time() - start_time
    print(f"创建/获取集合时间: {collection_init_time:.2f}秒")

    # 测试4：简单操作时间
    start_time = time.time()
    collection.add(
        documents=["测试文档1", "测试文档2"],
        ids=["doc1", "doc2"]
    )
    insert_time = time.time() - start_time
    print(f"插入2条文档时间: {insert_time:.2f}秒")

    total_time = import_time + client_init_time + collection_init_time + insert_time
    print(f"\n总计启动时间: {total_time:.2f}秒")

    # 性能评估
    if total_time < 3:
        print("✅ 启动性能优秀")
    elif total_time < 5:
        print("⚠️ 启动性能可接受")
    else:
        print("❌ 启动性能需要优化")

    return total_time

if __name__ == "__main__":
    test_chromadb_startup()
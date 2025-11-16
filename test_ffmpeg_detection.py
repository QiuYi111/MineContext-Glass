#!/usr/bin/env python3
"""测试FFmpeg自动检测功能"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from glass.ingestion.ffmpeg_runner import (
        get_ffmpeg_path,
        verify_ffmpeg_installation,
        FFmpegNotFoundError
    )

    print("=== FFmpeg自动检测测试 ===")

    # 测试1：路径检测
    try:
        ffmpeg_path = get_ffmpeg_path()
        print(f"✅ FFmpeg找到: {ffmpeg_path}")
    except FFmpegNotFoundError as e:
        print(f"❌ FFmpeg未找到: {e}")
        print(f"安装指导: {e.install_guide}")

    # 测试2：功能验证
    print("\n=== FFmpeg功能验证 ===")
    verification = verify_ffmpeg_installation()

    print(f"可用性: {'✅' if verification['available'] else '❌'}")
    if verification['version']:
        print(f"版本: {verification['version']}")
    if verification['codecs']:
        print(f"支持的编解码器: {', '.join(verification['codecs'])}")
    if verification['error']:
        print(f"错误: {verification['error']}")

except ImportError as e:
    print(f"❌ 导入失败: {e}")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
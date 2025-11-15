#!/usr/bin/env python3
"""
测试WebUI日报生成功能
"""
import requests
import json
import time

def test_webui_report_generation():
    """测试WebUI日报生成功能"""
    base_url = "http://127.0.0.1:8001"

    print("🔍 测试WebUI日报生成功能...")

    # 1. 获取所有timelines
    print("\n1. 获取timelines...")
    timelines_response = requests.get(f"{base_url}/glass/timelines")
    if timelines_response.status_code != 200:
        print(f"❌ 获取timelines失败: {timelines_response.status_code}")
        return False

    timelines_data = timelines_response.json()
    timelines = timelines_data.get("data", [])
    print(f"✅ 找到 {len(timelines)} 个timelines")

    if not timelines:
        print("❌ 没有找到任何timelines，请先上传视频")
        return False

    # 选择第一个timeline进行测试
    test_timeline = timelines[0]
    timeline_id = test_timeline["timeline_id"]
    print(f"📋 测试timeline: {timeline_id}")

    # 2. 测试获取日报（应该使用新的智能生成）
    print(f"\n2. 获取timeline {timeline_id} 的日报...")
    report_response = requests.get(f"{base_url}/glass/report/{timeline_id}")

    if report_response.status_code != 200:
        print(f"❌ 获取日报失败: {report_response.status_code}")
        print(f"响应内容: {report_response.text}")
        return False

    report_data = report_response.json()
    report = report_data.get("data", {})

    print("✅ 日报获取成功!")

    # 3. 分析日报质量
    auto_markdown = report.get("auto_markdown", "")
    manual_markdown = report.get("manual_markdown", "")

    print(f"\n3. 分析日报质量...")
    print(f"📄 自动生成日报长度: {len(auto_markdown)} 字符")
    print(f"✏️  手动编辑日报长度: {len(manual_markdown)} 字符")

    # 检查是否包含智能分析的特征
    intelligent_indicators = [
        "活动概述",
        "核心成就",
        "学习成长",
        "关键关联",
        "详细活动",
        "##",
        "###",
        "**"
    ]

    found_indicators = []
    for indicator in intelligent_indicators:
        if indicator in auto_markdown:
            found_indicators.append(indicator)

    print(f"\n🎯 智能分析指标发现: {len(found_indicators)}/{len(intelligent_indicators)}")
    for indicator in found_indicators:
        print(f"   ✅ {indicator}")

    # 4. 打印日报内容示例
    print(f"\n4. 日报内容示例（前500字符）:")
    print("```")
    print(auto_markdown[:500] + "..." if len(auto_markdown) > 500 else auto_markdown)
    print("```")

    # 5. 评估改进程度
    quality_score = len(found_indicators) / len(intelligent_indicators)
    print(f"\n📊 日报质量评分: {quality_score:.1%}")

    if quality_score >= 0.6:
        print("🎉 日报质量良好！智能分析功能正常工作")
        return True
    elif quality_score >= 0.3:
        print("⚠️  日报质量中等，部分智能分析功能工作")
        return True
    else:
        print("❌ 日报质量较低，智能分析功能可能未正常工作")
        return False

if __name__ == "__main__":
    print("开始测试WebUI日报生成功能...")
    print("确保服务器正在运行:")
    print("- OpenContext后端: http://127.0.0.1:8001")
    print("- WebUI前端: http://localhost:5175")
    print()

    success = test_webui_report_generation()

    if success:
        print("\n🎊 测试完成！WebUI日报生成功能验证成功")
    else:
        print("\n💥 测试失败！请检查配置和服务器状态")
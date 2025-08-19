#!/usr/bin/env python3
"""
TTS 服务对比测试脚本
对比 Edge TTS 和阿里百炼 TTS 的效果
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass

try:
    from oralcounsellor.core.tts.edge import EdgeTTS
    from oralcounsellor.core.tts.alibaba import AlibabaTTS
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已正确安装项目依赖")
    sys.exit(1)


def test_edge_tts():
    """测试 Edge TTS"""
    print("🎵 测试 Edge TTS...")
    
    try:
        # 创建 Edge TTS 实例
        edge_tts = EdgeTTS({
            "voice": "en-US-JennyNeural",
            "rate": "+0%",
            "volume": "+0%"
        })
        
        print("   ✅ Edge TTS 实例创建成功")
        
        # 测试语音合成
        test_text = "Hello! This is a test of Edge TTS. How does it sound?"
        print(f"   📤 合成文本: {test_text}")
        
        start_time = time.time()
        audio_data = edge_tts.synthesize(test_text)
        synthesis_time = time.time() - start_time
        
        if audio_data and len(audio_data) > 0:
            print(f"   📥 合成成功，音频大小: {len(audio_data)} bytes")
            print(f"   ⏱️  合成耗时: {synthesis_time:.2f}s")
            
            # 保存音频文件
            output_file = project_root / "test_edge_tts.wav"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            print(f"   💾 音频已保存到: {output_file}")
            
            return {
                "success": True,
                "audio_size": len(audio_data),
                "synthesis_time": synthesis_time,
                "provider": "Edge TTS",
                "voice": "en-US-JennyNeural",
                "file": "test_edge_tts.wav"
            }
        else:
            print("   ❌ Edge TTS 合成失败: 无音频数据")
            return {"success": False, "provider": "Edge TTS"}
            
    except Exception as e:
        print(f"   ❌ Edge TTS 测试失败: {e}")
        return {"success": False, "provider": "Edge TTS", "error": str(e)}


def test_alibaba_tts():
    """测试阿里百炼 TTS"""
    print("\n🎭 测试阿里百炼 TTS...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 API 密钥，跳过阿里百炼 TTS 测试")
        return {"success": False, "provider": "Alibaba TTS", "error": "No API key"}
    
    try:
        # 创建阿里百炼 TTS 实例
        alibaba_tts = AlibabaTTS({
            "api_key": api_key,
            "voice_name": "英文女",  # 英文女声
            "volume": 50,
            "speech_rate": 1.0
        })
        
        print("   ✅ 阿里百炼 TTS 实例创建成功")
        
        # 测试语音合成
        test_text = "Hello! This is a test of Alibaba TTS. How does it sound?"
        print(f"   📤 合成文本: {test_text}")
        
        start_time = time.time()
        audio_data = alibaba_tts.synthesize(test_text)
        synthesis_time = time.time() - start_time
        
        if audio_data and len(audio_data) > 0:
            print(f"   📥 合成成功，音频大小: {len(audio_data)} bytes")
            print(f"   ⏱️  合成耗时: {synthesis_time:.2f}s")
            
            # 保存音频文件
            output_file = project_root / "test_alibaba_tts.wav"
            with open(output_file, "wb") as f:
                f.write(audio_data)
            print(f"   💾 音频已保存到: {output_file}")
            
            return {
                "success": True,
                "audio_size": len(audio_data),
                "synthesis_time": synthesis_time,
                "provider": "Alibaba TTS",
                "voice": "英文女",
                "file": "test_alibaba_tts.wav"
            }
        else:
            print("   ❌ 阿里百炼 TTS 合成失败: 无音频数据")
            return {"success": False, "provider": "Alibaba TTS"}
            
    except Exception as e:
        print(f"   ❌ 阿里百炼 TTS 测试失败: {e}")
        return {"success": False, "provider": "Alibaba TTS", "error": str(e)}


def compare_results(edge_result, alibaba_result):
    """对比测试结果"""
    print("\n" + "=" * 60)
    print("📊 TTS 服务对比结果")
    print("=" * 60)
    
    # 基本信息对比
    print("\n🔍 基本信息对比:")
    print(f"{'服务':<15} {'状态':<10} {'语音':<20} {'文件':<25}")
    print("-" * 70)
    
    edge_status = "✅ 成功" if edge_result["success"] else "❌ 失败"
    edge_voice = edge_result.get("voice", "N/A")
    edge_file = edge_result.get("file", "N/A")
    print(f"{'Edge TTS':<15} {edge_status:<10} {edge_voice:<20} {edge_file:<25}")
    
    alibaba_status = "✅ 成功" if alibaba_result["success"] else "❌ 失败"
    alibaba_voice = alibaba_result.get("voice", "N/A")
    alibaba_file = alibaba_result.get("file", "N/A")
    print(f"{'Alibaba TTS':<15} {alibaba_status:<10} {alibaba_voice:<20} {alibaba_file:<25}")
    
    # 性能对比
    if edge_result["success"] and alibaba_result["success"]:
        print("\n⚡ 性能对比:")
        print(f"{'服务':<15} {'音频大小':<15} {'合成耗时':<15} {'速度评级':<15}")
        print("-" * 60)
        
        edge_size = edge_result["audio_size"]
        edge_time = edge_result["synthesis_time"]
        edge_speed = "快" if edge_time < 2 else "中" if edge_time < 5 else "慢"
        print(f"{'Edge TTS':<15} {f'{edge_size} bytes':<15} {f'{edge_time:.2f}s':<15} {edge_speed:<15}")
        
        alibaba_size = alibaba_result["audio_size"]
        alibaba_time = alibaba_result["synthesis_time"]
        alibaba_speed = "快" if alibaba_time < 2 else "中" if alibaba_time < 5 else "慢"
        print(f"{'Alibaba TTS':<15} {f'{alibaba_size} bytes':<15} {f'{alibaba_time:.2f}s':<15} {alibaba_speed:<15}")
        
        # 推荐建议
        print("\n💡 推荐建议:")
        if alibaba_time < edge_time:
            print("   🚀 阿里百炼 TTS 合成速度更快")
        elif edge_time < alibaba_time:
            print("   🚀 Edge TTS 合成速度更快")
        else:
            print("   ⚖️  两个服务合成速度相近")
            
        if alibaba_size > edge_size:
            print("   🎵 阿里百炼 TTS 音频文件更大（可能音质更好）")
        elif edge_size > alibaba_size:
            print("   🎵 Edge TTS 音频文件更大（可能音质更好）")
        else:
            print("   🎵 两个服务音频文件大小相近")
    
    # 错误信息
    if not edge_result["success"] or not alibaba_result["success"]:
        print("\n❌ 错误信息:")
        if not edge_result["success"] and "error" in edge_result:
            print(f"   Edge TTS: {edge_result['error']}")
        if not alibaba_result["success"] and "error" in alibaba_result:
            print(f"   Alibaba TTS: {alibaba_result['error']}")
    
    # 总体建议
    print("\n🎯 总体建议:")
    if edge_result["success"] and alibaba_result["success"]:
        print("   ✅ 两个 TTS 服务都可以正常工作")
        print("   🎭 阿里百炼 TTS 通常提供更好的音质和更自然的语音")
        print("   💰 Edge TTS 免费使用，阿里百炼 TTS 按量付费")
        print("   🌐 Edge TTS 无需 API 密钥，阿里百炼 TTS 需要配置密钥")
        print("   📚 对于英语学习场景，推荐使用阿里百炼 TTS 获得更好的发音质量")
    elif edge_result["success"]:
        print("   ✅ Edge TTS 可以正常工作")
        print("   ⚠️  阿里百炼 TTS 暂时无法使用，可能是网络或配置问题")
        print("   💡 建议先使用 Edge TTS，稍后再尝试配置阿里百炼 TTS")
    elif alibaba_result["success"]:
        print("   ✅ 阿里百炼 TTS 可以正常工作")
        print("   ⚠️  Edge TTS 暂时无法使用")
        print("   🎯 阿里百炼 TTS 是很好的选择，音质优秀")
    else:
        print("   ❌ 两个 TTS 服务都无法正常工作")
        print("   🔧 请检查网络连接和配置设置")


def show_configuration_guide():
    """显示配置指南"""
    print("\n" + "=" * 60)
    print("⚙️  TTS 服务配置指南")
    print("=" * 60)
    
    print("\n🔧 如何切换到阿里百炼 TTS:")
    print("1. 在 .env 文件中设置:")
    print("   TTS_PROVIDER=alibaba")
    print("   ALIBABA_TTS_VOICE=英文女")
    print("   ALIBABA_TTS_VOLUME=50")
    print("   ALIBABA_TTS_SPEECH_RATE=1.0")
    print("   ALIBABA_TTS_PITCH_RATE=1.0")
    print("")
    print("2. 设置阿里云 API 密钥:")
    print("   DASHSCOPE_API_KEY=your_api_key")
    print("")
    print("🔧 如何切换到 Edge TTS:")
    print("1. 在 .env 文件中设置:")
    print("   TTS_PROVIDER=edge")
    print("   EDGE_TTS_VOICE=en-US-JennyNeural")
    print("   EDGE_TTS_RATE=+0%")
    print("   EDGE_TTS_VOLUME=+0%")
    print("")
    print("📚 支持的阿里百炼语音:")
    print("   英文: 英文女, 英文男")
    print("   中文: 中文女, 中文男")
    print("   其他: 粤语女, 日语女, 日语男, 韩语女, 韩语男")
    print("")
    print("📚 常用的 Edge TTS 语音:")
    print("   英文: en-US-JennyNeural, en-US-GuyNeural")
    print("   中文: zh-CN-XiaoxiaoNeural, zh-CN-YunxiNeural")


def main():
    """主函数"""
    print("🔧 TTS 服务对比测试")
    print("=" * 60)
    
    # 运行测试
    edge_result = test_edge_tts()
    alibaba_result = test_alibaba_tts()
    
    # 对比结果
    compare_results(edge_result, alibaba_result)
    
    # 显示配置指南
    show_configuration_guide()
    
    # 生成的音频文件列表
    print("\n🎵 生成的音频文件:")
    audio_files = list(project_root.glob("test_*.wav"))
    if audio_files:
        for file in audio_files:
            print(f"   • {file.name}")
        print("\n💡 您可以播放这些文件来对比不同 TTS 服务的音质效果")
    else:
        print("   暂无生成的音频文件")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
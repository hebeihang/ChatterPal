#!/usr/bin/env python3
"""
阿里百炼 TTS 调试脚本
用于调试和测试阿里百炼 TTS API
"""

import os
import sys
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
    from dashscope.audio.tts import SpeechSynthesizer
    import dashscope
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已安装 dashscope: pip install dashscope")
    sys.exit(1)


def debug_api_call():
    """调试 API 调用"""
    print("🔧 阿里百炼 TTS API 调试")
    print("=" * 50)
    
    # 获取 API 密钥
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("❌ 未设置 API 密钥")
        print("请设置 DASHSCOPE_API_KEY 环境变量")
        return
    
    print(f"✅ API 密钥已设置: {api_key[:10]}...")
    
    # 设置 API 密钥
    dashscope.api_key = api_key
    
    # 测试参数
    test_params = [
        {
            "model": "cosyvoice-v1",
            "text": "Hello, this is a test.",
            "voice": "英文女",
            "format": "wav",
            "sample_rate": 22050
        },
        {
            "model": "cosyvoice-v1", 
            "text": "你好，这是一个测试。",
            "voice": "中文女",
            "format": "wav",
            "sample_rate": 22050
        }
    ]
    
    for i, params in enumerate(test_params, 1):
        print(f"\n🧪 测试 {i}: {params['voice']}")
        print(f"   文本: {params['text']}")
        
        try:
            # 调用 API
            result = SpeechSynthesizer.call(**params)
            
            # 打印结果信息
            print(f"   结果类型: {type(result)}")
            print(f"   结果属性: {dir(result)}")
            
            # 检查各种可能的属性
            if hasattr(result, 'status_code'):
                print(f"   状态码: {result.status_code}")
            if hasattr(result, 'message'):
                print(f"   消息: {result.message}")
            if hasattr(result, 'output'):
                print(f"   输出: {result.output}")
            if hasattr(result, 'usage'):
                print(f"   使用情况: {result.usage}")
            
            # 尝试获取音频数据
            audio_data = None
            if hasattr(result, 'get_audio_data'):
                try:
                    audio_data = result.get_audio_data()
                    print(f"   音频数据大小: {len(audio_data) if audio_data else 0} bytes")
                except Exception as e:
                    print(f"   获取音频数据失败: {e}")
            
            # 尝试其他可能的音频数据获取方式
            if not audio_data:
                if hasattr(result, 'audio'):
                    audio_data = result.audio
                    print(f"   音频数据 (audio): {len(audio_data) if audio_data else 0} bytes")
                elif hasattr(result, 'output') and hasattr(result.output, 'audio'):
                    audio_data = result.output.audio
                    print(f"   音频数据 (output.audio): {len(audio_data) if audio_data else 0} bytes")
            
            # 保存音频文件
            if audio_data:
                output_file = project_root / f"debug_test_{i}.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                print(f"   ✅ 音频已保存到: {output_file}")
            else:
                print("   ❌ 未获取到音频数据")
                
        except Exception as e:
            print(f"   ❌ 调用失败: {e}")
            print(f"   错误类型: {type(e)}")


def test_different_models():
    """测试不同的模型"""
    print("\n🎭 测试不同模型")
    print("=" * 50)
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("❌ 未设置 API 密钥")
        return
    
    dashscope.api_key = api_key
    
    # 可能的模型名称
    models = [
        "cosyvoice-v1",
        "sambert-zhichu-v1",
        "sambert-zhiba-v1",
        "sambert-zhitian-v1"
    ]
    
    for model in models:
        print(f"\n🧪 测试模型: {model}")
        try:
            result = SpeechSynthesizer.call(
                model=model,
                text="Hello, this is a test.",
                voice="英文女",
                format="wav"
            )
            print(f"   ✅ 模型 {model} 可用")
            
            if hasattr(result, 'get_audio_data'):
                audio_data = result.get_audio_data()
                if audio_data:
                    print(f"   音频大小: {len(audio_data)} bytes")
                    
        except Exception as e:
            print(f"   ❌ 模型 {model} 不可用: {e}")


def main():
    """主函数"""
    debug_api_call()
    test_different_models()
    
    print("\n" + "=" * 50)
    print("🎵 生成的调试音频文件:")
    for file in project_root.glob("debug_test_*.wav"):
        print(f"   • {file.name}")


if __name__ == "__main__":
    main()
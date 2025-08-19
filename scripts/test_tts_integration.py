#!/usr/bin/env python3
"""
TTS 集成测试脚本
测试 TTS 服务在整个系统中的集成情况
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
    from oralcounsellor.config.loader import create_tts
    from oralcounsellor.config.settings import get_settings
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保项目依赖已正确安装")
    sys.exit(1)


def test_tts_integration():
    """测试 TTS 集成"""
    print("🔧 TTS 集成测试")
    print("=" * 50)
    
    try:
        # 获取设置
        settings = get_settings()
        print(f"✅ 配置加载成功")
        print(f"   TTS 提供商: {settings.tts_provider}")
        
        # 创建 TTS 实例
        tts = create_tts(settings)
        print(f"✅ TTS 实例创建成功: {type(tts).__name__}")
        
        # 获取服务信息
        service_info = tts.get_service_info()
        print(f"✅ 服务信息获取成功")
        print(f"   提供商: {service_info['provider']}")
        
        if 'voice' in service_info:
            print(f"   语音: {service_info['voice']}")
        if 'model' in service_info:
            print(f"   模型: {service_info['model']}")
        
        # 测试语音合成
        test_text = "Hello! This is an integration test of the TTS system."
        print(f"\n🎵 测试语音合成")
        print(f"   文本: {test_text}")
        
        audio_data = tts.synthesize(test_text)
        
        if audio_data and len(audio_data) > 0:
            print(f"   ✅ 合成成功，音频大小: {len(audio_data)} bytes")
            
            # 保存测试音频
            output_file = project_root / "integration_test.wav"
            tts.synthesize_to_file(test_text, str(output_file))
            print(f"   💾 音频已保存到: {output_file}")
            
            return True
        else:
            print(f"   ❌ 合成失败，无音频数据")
            return False
            
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        return False


def test_tts_switching():
    """测试 TTS 服务切换"""
    print("\n🔄 TTS 服务切换测试")
    print("=" * 50)
    
    # 测试不同的 TTS 提供商
    providers = ["edge", "alibaba"]
    results = {}
    
    for provider in providers:
        print(f"\n🧪 测试 {provider.upper()} TTS")
        
        try:
            # 临时修改环境变量
            original_provider = os.getenv("TTS_PROVIDER")
            os.environ["TTS_PROVIDER"] = provider
            
            # 重新获取设置
            settings = get_settings()
            
            # 检查是否有必要的配置
            if provider == "alibaba":
                api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
                if not api_key:
                    print(f"   ⚠️  跳过 {provider} TTS: 未配置 API 密钥")
                    results[provider] = "skipped"
                    continue
            
            # 创建 TTS 实例
            tts = create_tts(settings)
            
            # 测试合成
            test_text = f"This is a test of {provider} TTS service."
            audio_data = tts.synthesize(test_text)
            
            if audio_data and len(audio_data) > 0:
                print(f"   ✅ {provider.upper()} TTS 工作正常")
                print(f"   音频大小: {len(audio_data)} bytes")
                results[provider] = "success"
                
                # 保存测试音频
                output_file = project_root / f"switch_test_{provider}.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_data)
                print(f"   💾 音频已保存到: {output_file}")
            else:
                print(f"   ❌ {provider.upper()} TTS 合成失败")
                results[provider] = "failed"
                
        except Exception as e:
            print(f"   ❌ {provider.upper()} TTS 测试失败: {e}")
            results[provider] = "error"
        
        finally:
            # 恢复原始设置
            if original_provider:
                os.environ["TTS_PROVIDER"] = original_provider
            elif "TTS_PROVIDER" in os.environ:
                del os.environ["TTS_PROVIDER"]
    
    return results


def main():
    """主函数"""
    print("🚀 OralCounsellor TTS 集成测试")
    print("=" * 60)
    
    # 基本集成测试
    integration_success = test_tts_integration()
    
    # 服务切换测试
    switching_results = test_tts_switching()
    
    # 总结结果
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    print(f"基本集成测试: {'✅ 通过' if integration_success else '❌ 失败'}")
    
    print("\nTTS 服务切换测试:")
    for provider, result in switching_results.items():
        status_map = {
            "success": "✅ 成功",
            "failed": "❌ 失败", 
            "error": "❌ 错误",
            "skipped": "⚠️  跳过"
        }
        status = status_map.get(result, "❓ 未知")
        print(f"  {provider.upper()} TTS: {status}")
    
    # 生成的测试文件
    print("\n🎵 生成的测试音频文件:")
    test_files = list(project_root.glob("*test*.wav"))
    if test_files:
        for file in test_files:
            print(f"   • {file.name}")
    else:
        print("   无测试音频文件生成")
    
    # 总体评估
    success_count = sum(1 for result in switching_results.values() if result == "success")
    total_tests = len(switching_results) + (1 if integration_success else 0)
    
    print(f"\n总体测试通过率: {success_count + (1 if integration_success else 0)}/{total_tests + 1}")
    
    if integration_success and success_count > 0:
        print("🎉 TTS 集成测试整体通过！系统可以正常使用。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和依赖。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
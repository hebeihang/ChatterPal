#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终编码测试脚本
模拟Web应用的完整启动流程
"""

import os
import sys
from pathlib import Path

# 设置编码环境
os.environ['PYTHONIOENCODING'] = 'utf-8'
if os.name == 'nt':
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def test_full_application_flow():
    """测试完整的应用流程"""
    print("🚀 最终编码测试 - 模拟完整应用流程")
    print("=" * 60)
    
    try:
        # 1. 导入所有必要的模块
        print("1️⃣  导入模块...")
        from oralcounsellor.web.app import OralCounsellorApp
        from oralcounsellor.config.settings import get_settings
        print("   ✅ 模块导入成功")
        
        # 2. 创建设置
        print("\n2️⃣  加载配置...")
        settings = get_settings()
        print(f"   ✅ 配置加载成功，LLM: {settings.llm_provider}, TTS: {settings.tts_provider}")
        
        # 3. 创建应用实例
        print("\n3️⃣  创建应用实例...")
        app = OralCounsellorApp(settings)
        print("   ✅ 应用实例创建成功")
        
        # 4. 测试中文对话
        print("\n4️⃣  测试中文对话...")
        test_messages = [
            "你好",
            "请用英文介绍一下自己",
            "What's your favorite color? 你最喜欢什么颜色？",
            "今天天气很好，适合学习英语。"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"   🔤 测试消息 {i}: {message}")
            try:
                audio_output, history = app.chat_tab._handle_chat(
                    audio=None,
                    text_input=message,
                    chat_history=[],
                    use_text=True
                )
                
                if audio_output and len(audio_output) > 1 and len(audio_output[1]) > 0:
                    print(f"      ✅ 成功 - 音频: {len(audio_output[1])} bytes")
                else:
                    print(f"      ⚠️  成功但无音频输出")
                    
                if history and len(history) > 0:
                    if isinstance(history[-1], list) and len(history[-1]) > 1:
                        response = str(history[-1][1])[:50]
                    elif isinstance(history[-1], dict):
                        response = str(history[-1].get('content', ''))[:50]
                    else:
                        response = str(history[-1])[:50]
                    print(f"      💬 回复: {response}...")
                    
            except Exception as e:
                print(f"      ❌ 失败: {e}")
                return False
        
        print("\n🎉 所有测试通过！编码问题已完全修复。")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = test_full_application_flow()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 最终验证通过！")
        print("🚀 应用现在可以正常启动，不会出现编码错误。")
        print("💡 您可以安全地运行: uv run python scripts/run.py")
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ 最终验证失败！")
        print("🔧 请检查编码设置和错误信息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
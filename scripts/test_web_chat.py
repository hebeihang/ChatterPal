#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web应用聊天功能的脚本
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

try:
    from oralcounsellor.web.app import OralCounsellorApp
    from oralcounsellor.config.settings import get_settings
except ImportError as e:
    print(f"导入错误: {e}")
    sys.exit(1)

def test_web_app_chat():
    """测试Web应用的聊天功能"""
    print("🌐 测试Web应用聊天功能...")
    
    try:
        # 获取设置
        settings = get_settings()
        print(f"✅ 配置加载成功")
        
        # 创建Web应用实例
        app = OralCounsellorApp(settings)
        print("✅ Web应用实例创建成功")
        
        # 测试聊天功能
        test_message = "你好，请介绍一下自己"
        print(f"🔤 测试消息: {test_message}")
        
        # 直接调用聊天处理函数
        try:
            # 模拟Web界面的聊天调用
            history = []
            audio_output, updated_history = app.chat_tab._handle_chat(
                audio=None, 
                text_input=test_message, 
                chat_history=history, 
                use_text=True
            )
            print(f"✅ 聊天成功")
            print(f"   音频输出: {len(audio_output[1]) if audio_output and len(audio_output) > 1 else 0} bytes")
            print(f"   对话历史: {len(updated_history)} 条消息")
            if updated_history:
                if isinstance(updated_history[-1], dict):
                    last_response = updated_history[-1].get('content', '')[:100]
                else:
                    last_response = str(updated_history[-1])[:100]
                print(f"   最后回复: {last_response}...")
            return True
        except Exception as e:
            print(f"❌ 聊天失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Web应用测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🌐 Web应用聊天功能测试")
    print("=" * 50)
    
    success = test_web_app_chat()
    
    if success:
        print("\n✅ Web应用聊天功能正常！")
        return 0
    else:
        print("\n❌ Web应用聊天功能存在问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
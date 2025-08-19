#!/usr/bin/env python3
"""
阿里百炼 API 测试脚本
测试更新后的阿里百炼 LLM 实现
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
    from oralcounsellor.core.llm.alibaba import AlibabaBailianLLM, create_alibaba_llm
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已正确安装项目依赖")
    sys.exit(1)


def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试基本功能...")
    
    # 检查是否有 API 密钥
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 或 ALIBABA_API_KEY 环境变量，跳过实际 API 测试")
        return False
    
    try:
        # 创建 LLM 实例
        llm = AlibabaBailianLLM({
            "api_key": api_key,
            "model": "qwen-plus",
            "temperature": 0.7,
            "max_tokens": 100
        })
        
        print(f"   ✅ LLM 实例创建成功")
        
        # 测试模型信息
        model_info = llm.get_model_info()
        print(f"   ✅ 模型信息: {model_info['provider']} - {model_info['model']}")
        
        # 测试支持的模型列表
        models = llm.get_supported_models()
        print(f"   ✅ 支持 {len(models)} 个模型")
        
        # 测试模型能力
        capabilities = llm.get_model_capabilities()
        print(f"   ✅ 模型能力: 最大上下文 {capabilities['max_context_length']} tokens")
        
        # 测试成本估算
        cost = llm.estimate_cost(100, 50)
        print(f"   ✅ 成本估算: {cost['total_cost_yuan']:.6f} 元")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 基本功能测试失败: {e}")
        return False


def test_chat_functionality():
    """测试对话功能"""
    print("\n💬 测试对话功能...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 或 ALIBABA_API_KEY 环境变量，跳过对话测试")
        return False
    
    try:
        # 创建 LLM 实例
        llm = create_alibaba_llm(
            api_key=api_key,
            model="qwen-plus",
            temperature=0.7,
            max_tokens=50
        )
        
        # 测试简单对话
        print("   📤 发送测试消息...")
        response = llm.chat("Hello! Please reply with 'Test successful' in English.")
        print(f"   📥 收到回复: {response[:100]}...")
        
        if response and len(response.strip()) > 0:
            print("   ✅ 对话测试成功")
            return True
        else:
            print("   ❌ 对话测试失败: 无回复内容")
            return False
            
    except Exception as e:
        print(f"   ❌ 对话测试失败: {e}")
        return False


def test_stream_functionality():
    """测试流式对话功能"""
    print("\n🌊 测试流式对话功能...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 或 ALIBABA_API_KEY 环境变量，跳过流式测试")
        return False
    
    try:
        # 创建 LLM 实例
        llm = create_alibaba_llm(
            api_key=api_key,
            model="qwen-plus",
            temperature=0.7,
            max_tokens=50
        )
        
        # 测试流式对话
        print("   📤 发送流式测试消息...")
        print("   📥 流式回复: ", end="")
        
        response_chunks = []
        for chunk in llm.chat_stream("Please count from 1 to 5 in English."):
            print(chunk, end="", flush=True)
            response_chunks.append(chunk)
        
        print()  # 换行
        
        if response_chunks:
            full_response = "".join(response_chunks)
            print(f"   ✅ 流式对话测试成功，共收到 {len(response_chunks)} 个片段")
            return True
        else:
            print("   ❌ 流式对话测试失败: 无回复片段")
            return False
            
    except Exception as e:
        print(f"   ❌ 流式对话测试失败: {e}")
        return False


def test_advanced_features():
    """测试高级功能"""
    print("\n🚀 测试高级功能...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 或 ALIBABA_API_KEY 环境变量，跳过高级功能测试")
        return False
    
    try:
        # 测试搜索增强功能
        llm = AlibabaBailianLLM({
            "api_key": api_key,
            "model": "qwen-plus",
            "enable_search": True,
            "max_tokens": 100
        })
        
        print("   🔍 测试搜索增强功能...")
        response = llm.chat("What's the latest news about AI?", enable_search=True)
        print(f"   ✅ 搜索增强测试完成，回复长度: {len(response)}")
        
        # 测试不同模型
        print("   🔄 测试模型切换...")
        response2 = llm.chat("Hello", model="qwen-turbo")
        print(f"   ✅ 模型切换测试完成")
        
        # 测试连接
        print("   🔗 测试连接...")
        connection_ok = llm.test_connection()
        if connection_ok:
            print("   ✅ 连接测试成功")
        else:
            print("   ❌ 连接测试失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 高级功能测试失败: {e}")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n🛡️  测试错误处理...")
    
    try:
        # 测试无效 API 密钥
        print("   🔑 测试无效 API 密钥...")
        try:
            llm = AlibabaBailianLLM({
                "api_key": "invalid_key",
                "model": "qwen-plus"
            })
            llm.chat("test")
            print("   ❌ 应该抛出错误但没有")
            return False
        except Exception as e:
            print(f"   ✅ 正确处理无效 API 密钥错误: {type(e).__name__}")
        
        # 测试无效模型
        api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("ALIBABA_API_KEY")
        if api_key:
            print("   🤖 测试无效模型...")
            try:
                llm = AlibabaBailianLLM({
                    "api_key": api_key,
                    "model": "invalid-model"
                })
                llm.chat("test")
                print("   ❌ 应该抛出错误但没有")
                return False
            except Exception as e:
                print(f"   ✅ 正确处理无效模型错误: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 错误处理测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 阿里百炼 API 测试")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        ("基本功能", test_basic_functionality),
        ("对话功能", test_chat_functionality),
        ("流式对话", test_stream_functionality),
        ("高级功能", test_advanced_features),
        ("错误处理", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！阿里百炼 API 更新成功。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
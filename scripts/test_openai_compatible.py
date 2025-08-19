#!/usr/bin/env python3
"""
阿里百炼 OpenAI 兼容接口测试脚本
验证使用 OpenAI SDK 调用阿里百炼 API 的功能
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
    from openai import OpenAI
except ImportError:
    print("❌ OpenAI 库未安装，请运行: pip install openai")
    sys.exit(1)


def test_direct_openai_client():
    """直接使用 OpenAI 客户端测试阿里百炼接口"""
    print("🧪 测试直接使用 OpenAI 客户端...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 环境变量，跳过测试")
        return False
    
    try:
        # 创建 OpenAI 客户端，指向阿里百炼兼容接口
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        print("   ✅ OpenAI 客户端创建成功")
        
        # 测试基本对话
        print("   📤 发送测试消息...")
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello! Please reply 'Test successful' in English."}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        if completion.choices and len(completion.choices) > 0:
            response = completion.choices[0].message.content
            print(f"   📥 收到回复: {response}")
            
            # 显示使用统计
            if completion.usage:
                print(f"   📊 Token使用: {completion.usage.prompt_tokens}(输入) + {completion.usage.completion_tokens}(输出) = {completion.usage.total_tokens}(总计)")
            
            print("   ✅ 基本对话测试成功")
            return True
        else:
            print("   ❌ 基本对话测试失败: 无回复")
            return False
            
    except Exception as e:
        print(f"   ❌ 基本对话测试失败: {e}")
        return False


def test_stream_response():
    """测试流式响应"""
    print("\n🌊 测试流式响应...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 环境变量，跳过测试")
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        print("   📤 发送流式测试消息...")
        print("   📥 流式回复: ", end="")
        
        stream = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "user", "content": "Please count from 1 to 5 in English."}
            ],
            stream=True,
            stream_options={"include_usage": True},
            max_tokens=100
        )
        
        chunks_received = 0
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta.content:
                    print(delta.content, end="", flush=True)
                    chunks_received += 1
        
        print()  # 换行
        
        if chunks_received > 0:
            print(f"   ✅ 流式响应测试成功，收到 {chunks_received} 个片段")
            return True
        else:
            print("   ❌ 流式响应测试失败: 无内容片段")
            return False
            
    except Exception as e:
        print(f"   ❌ 流式响应测试失败: {e}")
        return False


def test_search_enhancement():
    """测试搜索增强功能"""
    print("\n🔍 测试搜索增强功能...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 环境变量，跳过测试")
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        print("   📤 发送搜索增强测试消息...")
        completion = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "user", "content": "What are the latest developments in AI technology in 2024?"}
            ],
            extra_body={"enable_search": True},
            max_tokens=200
        )
        
        if completion.choices and len(completion.choices) > 0:
            response = completion.choices[0].message.content
            print(f"   📥 搜索增强回复长度: {len(response)} 字符")
            print(f"   📝 回复预览: {response[:100]}...")
            print("   ✅ 搜索增强测试成功")
            return True
        else:
            print("   ❌ 搜索增强测试失败: 无回复")
            return False
            
    except Exception as e:
        print(f"   ❌ 搜索增强测试失败: {e}")
        return False


def test_different_models():
    """测试不同模型"""
    print("\n🤖 测试不同模型...")
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("   ⚠️  未设置 DASHSCOPE_API_KEY 环境变量，跳过测试")
        return False
    
    models_to_test = ["qwen-turbo", "qwen-plus", "qwen-max"]
    successful_models = []
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    for model in models_to_test:
        try:
            print(f"   🧪 测试模型: {model}")
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=20
            )
            
            if completion.choices and len(completion.choices) > 0:
                response = completion.choices[0].message.content
                print(f"      ✅ {model}: {response[:30]}...")
                successful_models.append(model)
            else:
                print(f"      ❌ {model}: 无回复")
                
        except Exception as e:
            print(f"      ❌ {model}: {e}")
    
    if successful_models:
        print(f"   ✅ 成功测试 {len(successful_models)}/{len(models_to_test)} 个模型")
        return True
    else:
        print(f"   ❌ 所有模型测试失败")
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n🛡️  测试错误处理...")
    
    try:
        # 测试无效 API 密钥
        print("   🔑 测试无效 API 密钥...")
        client = OpenAI(
            api_key="invalid_key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        
        try:
            completion = client.chat.completions.create(
                model="qwen-plus",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            print("   ❌ 应该抛出错误但没有")
            return False
        except Exception as e:
            print(f"   ✅ 正确处理无效 API 密钥: {type(e).__name__}")
        
        # 测试无效模型
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if api_key:
            print("   🤖 测试无效模型...")
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            try:
                completion = client.chat.completions.create(
                    model="invalid-model-name",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                print("   ❌ 应该抛出错误但没有")
                return False
            except Exception as e:
                print(f"   ✅ 正确处理无效模型: {type(e).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 错误处理测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 阿里百炼 OpenAI 兼容接口测试")
    print("=" * 50)
    
    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("⚠️  未设置 DASHSCOPE_API_KEY 环境变量")
        print("请设置环境变量后重试：")
        print("export DASHSCOPE_API_KEY='your_api_key'")
        print("\n或者在 .env 文件中添加：")
        print("DASHSCOPE_API_KEY=your_api_key")
        return 1
    
    # 运行所有测试
    tests = [
        ("直接 OpenAI 客户端", test_direct_openai_client),
        ("流式响应", test_stream_response),
        ("搜索增强", test_search_enhancement),
        ("不同模型", test_different_models),
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
        print("🎉 所有测试通过！OpenAI 兼容接口工作正常。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置和网络连接。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
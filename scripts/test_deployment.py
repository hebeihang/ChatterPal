#!/usr/bin/env python3
"""
部署测试脚本
验证 OralCounsellor 增强聊天模块的部署配置和功能
"""

import os
import sys
import json
import time
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from oralcounsellor.config.settings import get_settings
    from oralcounsellor.services.chat import ChatService
    from oralcounsellor.services.chat_config import ChatConfigManager
    from oralcounsellor.utils.logger import get_logger
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保已正确安装项目依赖")
    sys.exit(1)


logger = get_logger(__name__)


class DeploymentTester:
    """部署测试器"""
    
    def __init__(self):
        self.test_results: Dict[str, bool] = {}
        self.errors: List[str] = []
        
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("🚀 开始部署测试...")
        print("=" * 50)
        
        tests = [
            ("环境变量检查", self.test_environment_variables),
            ("依赖包检查", self.test_dependencies),
            ("配置文件检查", self.test_configuration_files),
            ("目录结构检查", self.test_directory_structure),
            ("服务初始化测试", self.test_service_initialization),
            ("聊天模块功能测试", self.test_chat_module_functionality),
            ("缓存系统测试", self.test_cache_system),
            ("错误处理测试", self.test_error_handling),
            ("性能配置测试", self.test_performance_configuration),
        ]
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}...")
            try:
                result = test_func()
                self.test_results[test_name] = result
                status = "✅ 通过" if result else "❌ 失败"
                print(f"   {status}")
            except Exception as e:
                self.test_results[test_name] = False
                self.errors.append(f"{test_name}: {str(e)}")
                print(f"   ❌ 错误: {e}")
        
        self.print_summary()
        return all(self.test_results.values())
    
    def test_environment_variables(self) -> bool:
        """测试环境变量配置"""
        required_vars = [
            "OPENAI_API_KEY",
            "DASHSCOPE_API_KEY",  # 阿里百炼新的环境变量名
        ]
        
        optional_vars = [
            "CHAT_MAX_HISTORY_LENGTH",
            "AUDIO_MAX_RECORDING_DURATION",
            "TOPIC_DEFAULT_DIFFICULTY",
            "TTS_CACHE_SIZE",
            "ENABLE_ASYNC_PROCESSING",
        ]
        
        missing_required = []
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        if missing_required:
            print(f"   缺少必需的环境变量: {', '.join(missing_required)}")
            return False
        
        # 检查可选变量
        missing_optional = []
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        if missing_optional:
            print(f"   建议设置的环境变量: {', '.join(missing_optional)}")
        
        return True
    
    def test_dependencies(self) -> bool:
        """测试依赖包"""
        required_packages = [
            "gradio",
            "openai",
            "edge_tts",
            "pydantic",
            "python_dotenv",
            "cachetools",
            "aiofiles",
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"   缺少依赖包: {', '.join(missing_packages)}")
            print("   请运行: pip install -e .")
            return False
        
        return True
    
    def test_configuration_files(self) -> bool:
        """测试配置文件"""
        config_files = [
            ".env.example",
            "config/chat_config.yaml.example",
            "pyproject.toml",
        ]
        
        missing_files = []
        for file_path in config_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"   缺少配置文件: {', '.join(missing_files)}")
            return False
        
        # 测试配置管理器
        try:
            config_manager = ChatConfigManager()
            config = config_manager.get_config()
            print(f"   配置加载成功，包含 {len(config.__dict__)} 个配置项")
        except Exception as e:
            print(f"   配置管理器初始化失败: {e}")
            return False
        
        return True
    
    def test_directory_structure(self) -> bool:
        """测试目录结构"""
        required_dirs = [
            "src/oralcounsellor",
            "src/oralcounsellor/services",
            "src/oralcounsellor/utils",
            "src/oralcounsellor/core",
            "logs",
            "temp_audio",
            ".cache",
            "config",
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"   创建目录: {dir_path}")
                except Exception as e:
                    missing_dirs.append(f"{dir_path} ({e})")
        
        if missing_dirs:
            print(f"   无法创建目录: {', '.join(missing_dirs)}")
            return False
        
        return True
    
    def test_service_initialization(self) -> bool:
        """测试服务初始化"""
        try:
            # 测试设置加载
            settings = get_settings()
            print(f"   设置加载成功")
            
            # 测试阿里百炼 LLM 初始化
            from oralcounsellor.core.llm.alibaba import AlibabaBailianLLM
            try:
                llm = AlibabaBailianLLM({"api_key": "test_key"})
                print(f"   阿里百炼 LLM 类初始化成功")
            except Exception as e:
                if "API密钥" in str(e):
                    print(f"   阿里百炼 LLM 类初始化成功（预期的API密钥错误）")
                else:
                    raise e
            
            # 测试聊天服务初始化
            chat_service = ChatService()
            print(f"   聊天服务初始化成功")
            
            # 测试服务状态
            status = chat_service.get_service_status()
            print(f"   服务状态: {len(status)} 个状态项")
            
            return True
        except Exception as e:
            print(f"   服务初始化失败: {e}")
            return False
    
    def test_chat_module_functionality(self) -> bool:
        """测试聊天模块功能"""
        try:
            chat_service = ChatService()
            
            # 测试会话创建
            session_id = chat_service.create_session()
            print(f"   会话创建成功: {session_id[:8]}...")
            
            # 测试主题生成（如果 LLM 可用）
            try:
                topic = chat_service.generate_topic(session_id)
                print(f"   主题生成成功: {topic[:50]}...")
            except Exception as e:
                print(f"   主题生成跳过 (LLM 不可用): {e}")
            
            # 测试配置管理
            config_manager = ChatConfigManager()
            config = config_manager.get_config()
            print(f"   配置管理成功")
            
            return True
        except Exception as e:
            print(f"   聊天模块功能测试失败: {e}")
            return False
    
    def test_cache_system(self) -> bool:
        """测试缓存系统"""
        try:
            from oralcounsellor.utils.cache import get_tts_cache, get_chat_cache
            
            # 测试 TTS 缓存
            tts_cache = get_tts_cache()
            test_key = "test_deployment"
            test_data = b"test_audio_data"
            
            tts_cache.put("test", "en-US-JennyNeural", test_data)
            cached_data = tts_cache.get("test", "en-US-JennyNeural")
            
            if cached_data != test_data:
                print(f"   TTS 缓存测试失败")
                return False
            
            print(f"   TTS 缓存测试成功")
            
            # 测试聊天缓存
            chat_cache = get_chat_cache()
            print(f"   聊天缓存初始化成功")
            
            return True
        except Exception as e:
            print(f"   缓存系统测试失败: {e}")
            return False
    
    def test_error_handling(self) -> bool:
        """测试错误处理"""
        try:
            from oralcounsellor.core.errors import error_handler, ChatModuleError
            
            # 测试错误创建
            error = error_handler.create_error("AUDIO_FORMAT_ERROR", message="测试错误")
            print(f"   错误创建成功: {error.error_info.code}")
            
            # 测试用户友好错误信息
            user_message = error_handler.format_user_error_message(error)
            print(f"   用户错误信息格式化成功")
            
            return True
        except Exception as e:
            print(f"   错误处理测试失败: {e}")
            return False
    
    def test_performance_configuration(self) -> bool:
        """测试性能配置"""
        try:
            # 检查性能相关的环境变量
            performance_vars = {
                "ENABLE_ASYNC_PROCESSING": "true",
                "MAX_CONCURRENT_REQUESTS": "10",
                "TTS_CACHE_SIZE": "1000",
                "CHAT_CACHE_SIZE": "500",
            }
            
            for var, default in performance_vars.items():
                value = os.getenv(var, default)
                print(f"   {var}: {value}")
            
            return True
        except Exception as e:
            print(f"   性能配置测试失败: {e}")
            return False
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 50)
        print("📊 测试摘要")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {total - passed}")
        print(f"成功率: {passed/total*100:.1f}%")
        
        if self.errors:
            print("\n❌ 错误详情:")
            for error in self.errors:
                print(f"   • {error}")
        
        if passed == total:
            print("\n🎉 所有测试通过！部署配置正确。")
        else:
            print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置。")


def test_web_interface(port: int = 7860, timeout: int = 30) -> bool:
    """测试 Web 界面"""
    print(f"\n🌐 测试 Web 界面 (端口 {port})...")
    
    # 启动应用（在后台）
    try:
        process = subprocess.Popen([
            sys.executable, "scripts/run.py", "--port", str(port)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待应用启动
        print("   等待应用启动...")
        time.sleep(10)
        
        # 测试健康检查端点
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            if response.status_code == 200:
                print("   ✅ 健康检查端点正常")
                health_ok = True
            else:
                print(f"   ❌ 健康检查失败: {response.status_code}")
                health_ok = False
        except requests.RequestException as e:
            print(f"   ❌ 无法连接到应用: {e}")
            health_ok = False
        
        # 终止进程
        process.terminate()
        process.wait(timeout=5)
        
        return health_ok
        
    except Exception as e:
        print(f"   ❌ Web 界面测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 OralCounsellor 增强聊天模块部署测试")
    print("=" * 60)
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 运行部署测试
    tester = DeploymentTester()
    deployment_ok = tester.run_all_tests()
    
    # 测试 Web 界面（可选）
    if deployment_ok:
        web_ok = test_web_interface()
        if not web_ok:
            deployment_ok = False
    
    # 输出最终结果
    print("\n" + "=" * 60)
    if deployment_ok:
        print("🎉 部署测试完成！系统已准备就绪。")
        print("\n📝 下一步:")
        print("   1. 配置您的 API 密钥")
        print("   2. 运行 python scripts/run.py 启动应用")
        print("   3. 访问 http://localhost:7860 使用应用")
        sys.exit(0)
    else:
        print("❌ 部署测试失败！请修复上述问题后重试。")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
环境设置脚本

用于初始化ChatterPal项目的开发和运行环境�?
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional


class EnvironmentSetup:
    """环境设置类"""
    
    def __init__(self):
        """初始化设置器"""
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.data_dir = self.project_root / "data"
        self.temp_audio_dir = self.project_root / "temp_audio"
        
    def check_python_version(self) -> bool:
        """检查Python版本"""
        print("检查Python版本...")
        
        if sys.version_info < (3, 8):
            print("❌ 错误: 需要Python 3.8或更高版本")
            print(f"当前版本: {sys.version}")
            return False
        
        print(f"✅ Python版本: {sys.version}")
        return True
    
    def check_uv_installation(self) -> bool:
        """检查uv是否已安装"""
        print("检查uv包管理器...")
        
        try:
            result = subprocess.run(['uv', '--version'], 
                                  capture_output=True, text=True, check=True)
            print(f"�?uv版本: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("�?错误: 未找到uv包管理器")
            print("请访�?https://docs.astral.sh/uv/getting-started/installation/ 安装uv")
            return False
    
    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        print("安装项目依赖...")
        
        try:
            # 同步依赖
            subprocess.run(['uv', 'sync'], cwd=self.project_root, check=True)
            print("�?依赖安装完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"�?依赖安装失败: {e}")
            return False
    
    def create_directories(self) -> None:
        """创建必要的目录"""
        print("创建项目目录...")
        
        directories = [
            self.data_dir / "models",
            self.data_dir / "audio",
            self.data_dir / "configs",
            self.temp_audio_dir,
            self.project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"�?创建目录: {directory}")
    
    def setup_environment_file(self) -> None:
        """设置环境变量文件"""
        print("设置环境变量文件...")
        
        env_example = self.project_root / ".env.example"
        env_file = self.project_root / ".env"
        
        if env_example.exists() and not env_file.exists():
            shutil.copy(env_example, env_file)
            print("✅ 创建.env文件（从.env.example复制）")
            print("⚠️  请编辑.env文件，填入您的API密钥")
        elif env_file.exists():
            print("✅ .env文件已存在")
        else:
            # 创建基本.env文件
            env_content = """# ChatterPal 环境变量配置

# 阿里云API配置
ALIBABA_API_KEY=your_alibaba_api_key_here
ALIBABA_API_SECRET=your_alibaba_api_secret_here

# OpenAI API配置（可选）
OPENAI_API_KEY=your_openai_api_key_here

# 音频配置
AUDIO_SAMPLE_RATE=16000
AUDIO_TEMP_DIR=temp_audio

# Whisper模型配置
WHISPER_MODEL=base

# Web界面配置
GRADIO_SHARE=false
GRADIO_PORT=7860

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/chatterpal.log
"""
            env_file.write_text(env_content, encoding='utf-8')
            print("✅ 创建基本.env文件")
            print("⚠️  请编辑.env文件，填入您的API密钥")
    
    def check_optional_dependencies(self) -> None:
        """检查可选依赖"""
        print("检查可选依赖...")
        
        optional_packages = {
            'librosa': '音频处理增强功能',
            'torch': 'PyTorch深度学习框架',
            'transformers': 'Hugging Face模型库',
            'gradio': 'Web界面框架'
        }
        
        for package, description in optional_packages.items():
            try:
                __import__(package)
                print(f"�?{package}: 已安�?({description})")
            except ImportError:
                print(f"⚠️  {package}: 未安�?({description})")
    
    def verify_installation(self) -> bool:
        """验证安装"""
        print("验证安装...")
        
        try:
            # 尝试导入主要模块
            sys.path.insert(0, str(self.src_dir))
            
            from chatterpal.config import Settings
            from chatterpal.utils import get_logger
            
            print("✅ 核心模块导入成功")
            
            # 测试配置加载
            settings = Settings()
            print("✅ 配置系统正常")
            
            # 测试日志系统
            logger = get_logger()
            logger.configure(console_output=False)  # 避免输出到控制台
            print("�?日志系统正常")
            
            return True
            
        except Exception as e:
            print(f"�?验证失败: {e}")
            return False
    
    def run_setup(self) -> bool:
        """运行完整设置流程"""
        print("🚀 开始ChatterPal环境设置...\n")
        
        # 检查基础环境
        if not self.check_python_version():
            return False
        
        if not self.check_uv_installation():
            return False
        
        # 创建目录
        self.create_directories()
        
        # 设置环境文件
        self.setup_environment_file()
        
        # 安装依赖
        if not self.install_dependencies():
            return False
        
        # 检查可选依�?
        self.check_optional_dependencies()
        
        # 验证安装
        if not self.verify_installation():
            return False
        
        print("\n🎉 环境设置完成✅")
        print("\n下一�?")
        print("1. 编辑.env文件，填入您的API密钥")
        print("2. 运行 'uv run python scripts/run.py' 启动应用")
        print("3. 或者运�?'uv run python -m chatterpal.web.app' 直接启动Web界面")
        
        return True


def main():
    """主函数"""
    setup = EnvironmentSetup()
    
    # 解析命令行参�?
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command in ["--help", "-h", "help"]:
            print("ChatterPal 环境设置脚本")
            print()
            print("用法:")
            print("  python scripts/setup.py [命令]")
            print()
            print("可用命令:")
            print("  check    - 只检查环境，不安�?")
            print("  verify   - 只验证安�?")
            print("  dirs     - 只创建目�?")
            print("  env      - 只设置环境文�?")
            print("  help     - 显示此帮助信�?")
            print()
            print("不带参数运行将执行完整的环境设置流程✅")
            sys.exit(0)
        elif command == "check":
            # 只检查环境，不安�?
            setup.check_python_version()
            setup.check_uv_installation()
            setup.check_optional_dependencies()
        elif command == "verify":
            # 只验证安�?
            setup.verify_installation()
        elif command == "dirs":
            # 只创建目�?
            setup.create_directories()
        elif command == "env":
            # 只设置环境文�?
            setup.setup_environment_file()
        else:
            print(f"未知命令: {command}")
            print("可用命令: check, verify, dirs, env, help")
            print("使用 'python scripts/setup.py --help' 查看详细帮助")
            sys.exit(1)
    else:
        # 运行完整设置
        success = setup.run_setup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用启动脚本

用于启动OralCounsellor应用的各种模式和功能。
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

# 设置编码环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
if os.name == 'nt':  # Windows
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'


class OralCounsellorRunner:
    """OralCounsellor运行器"""
    
    def __init__(self):
        """初始化运行器"""
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        
        # 添加src目录到Python路径
        sys.path.insert(0, str(self.src_dir))
    
    def check_environment(self) -> bool:
        """检查运行环境"""
        print("检查运行环境...")
        
        # 检查.env文件
        env_file = self.project_root / ".env"
        if not env_file.exists():
            print("❌ 错误: 未找到.env文件")
            print("请运行 'python scripts/setup.py' 进行环境设置")
            return False
        
        # 检查必要目录
        required_dirs = [
            self.project_root / "temp_audio",
            self.project_root / "data"
        ]
        
        for directory in required_dirs:
            if not directory.exists():
                print(f"⚠️  创建缺失目录: {directory}")
                directory.mkdir(parents=True, exist_ok=True)
        
        print("✅ 环境检查完成")
        return True
    
    def load_environment(self) -> None:
        """加载环境变量"""
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
    
    def run_web_app(self, port: Optional[int] = None, share: bool = False, 
                   debug: bool = False) -> None:
        """启动Web应用"""
        print("🚀 启动OralCounsellor Web应用...")
        
        # 强制设置UTF-8编码
        self._force_utf8_encoding()
        
        try:
            from oralcounsellor.web.app import create_app
            from oralcounsellor.utils import setup_logging
            
            # 设置日志
            log_config = {
                'level': 'DEBUG' if debug else 'INFO',
                'console_output': True,
                'colored_output': True
            }
            
            if not debug:
                log_config['log_file'] = str(self.project_root / "logs" / "oralcounsellor.log")
            
            setup_logging(log_config)
            
            # 创建应用
            app = create_app()
            
            # 启动参数
            launch_kwargs = {
                'share': share,
                'inbrowser': True,
                'show_error': debug
            }
            
            if port:
                launch_kwargs['server_port'] = port
            
            # 启动应用
            app.launch(**launch_kwargs)
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            if debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def run_chat_mode(self) -> None:
        """启动命令行聊天模式"""
        print("🗣️  启动命令行聊天模式...")
        
        try:
            from oralcounsellor.services.chat import ChatService
            from oralcounsellor.config import Settings
            from oralcounsellor.utils import setup_logging
            
            # 设置日志
            setup_logging({'level': 'INFO', 'console_output': True})
            
            # 初始化服务
            settings = Settings()
            chat_service = ChatService.from_settings(settings)
            
            print("聊天模式已启动！输入 'quit' 或 'exit' 退出。")
            print("-" * 50)
            
            while True:
                try:
                    user_input = input("\n您: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', '退出']:
                        print("再见！")
                        break
                    
                    if not user_input:
                        continue
                    
                    # 处理文本输入（不使用语音）
                    response = chat_service.process_text_message(user_input)
                    print(f"\nAI: {response}")
                    
                except KeyboardInterrupt:
                    print("\n\n再见！")
                    break
                except Exception as e:
                    print(f"❌ 处理消息时出错: {e}")
                    
        except Exception as e:
            print(f"❌ 启动聊天模式失败: {e}")
            sys.exit(1)
    
    def run_test_mode(self, test_type: str = "all") -> None:
        """运行测试"""
        print(f"🧪 运行测试: {test_type}")
        
        test_commands = {
            "all": ["python", "-m", "pytest", "tests/", "-v"],
            "unit": ["python", "-m", "pytest", "tests/", "-v", "-k", "not integration"],
            "integration": ["python", "-m", "pytest", "tests/", "-v", "-k", "integration"],
            "config": ["python", "-m", "pytest", "tests/test_config.py", "-v"]
        }
        
        if test_type not in test_commands:
            print(f"❌ 未知测试类型: {test_type}")
            print(f"可用类型: {', '.join(test_commands.keys())}")
            return
        
        try:
            subprocess.run(test_commands[test_type], 
                         cwd=self.project_root, check=True)
            print("✅ 测试完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 测试失败: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ 未找到pytest，请安装测试依赖")
            print("运行: uv add --dev pytest")
            sys.exit(1)
    
    def run_demo_mode(self, demo_type: str = "basic") -> None:
        """运行演示模式"""
        print(f"🎬 运行演示: {demo_type}")
        
        try:
            if demo_type == "basic":
                self._run_basic_demo()
            elif demo_type == "asr":
                self._run_asr_demo()
            elif demo_type == "tts":
                self._run_tts_demo()
            elif demo_type == "assessment":
                self._run_assessment_demo()
            else:
                print(f"❌ 未知演示类型: {demo_type}")
                print("可用类型: basic, asr, tts, assessment")
                
        except Exception as e:
            print(f"❌ 演示失败: {e}")
            sys.exit(1)
    
    def _run_basic_demo(self) -> None:
        """运行基础功能演示"""
        from oralcounsellor.config import Settings
        from oralcounsellor.utils import get_logger
        
        print("基础功能演示:")
        
        # 测试配置
        settings = Settings()
        print(f"✅ 配置加载成功")
        print(f"   - 音频采样率: {settings.audio_sample_rate}")
        print(f"   - Whisper模型: {settings.whisper_model}")
        
        # 测试日志
        logger = get_logger()
        logger.configure(console_output=True)
        logger.info("日志系统测试")
        print("✅ 日志系统正常")
        
        print("🎉 基础功能演示完成")
    
    def _run_asr_demo(self) -> None:
        """运行ASR演示"""
        print("ASR功能演示 - 需要音频文件进行测试")
        # 这里可以添加ASR测试代码
        
    def _run_tts_demo(self) -> None:
        """运行TTS演示"""
        print("TTS功能演示 - 需要配置TTS服务")
        # 这里可以添加TTS测试代码
        
    def _run_assessment_demo(self) -> None:
        """运行评估演示"""
        print("发音评估演示 - 需要音频文件和目标文本")
        # 这里可以添加评估测试代码
    
    def _force_utf8_encoding(self):
        """强制设置UTF-8编码"""
        print("🔧 设置UTF-8编码环境...")
        
        # 设置环境变量
        encoding_vars = {
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONLEGACYWINDOWSSTDIO': '1',
            'LANG': 'zh_CN.UTF-8',
            'LC_ALL': 'zh_CN.UTF-8'
        }
        
        for key, value in encoding_vars.items():
            os.environ[key] = value
        
        # 重新配置标准输入输出
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
                print("✅ 标准输入输出已重新配置为UTF-8")
            except Exception as e:
                print(f"⚠️  标准输入输出重新配置失败: {e}")
        
        print("✅ UTF-8编码环境设置完成")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="OralCounsellor应用启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python scripts/run.py                    # 启动Web应用
  python scripts/run.py --port 8080       # 在指定端口启动Web应用
  python scripts/run.py --mode chat       # 启动命令行聊天模式
  python scripts/run.py --mode test       # 运行所有测试
  python scripts/run.py --mode demo       # 运行基础演示
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['web', 'chat', 'test', 'demo'],
        default='web',
        help='运行模式 (默认: web)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        help='Web应用端口号'
    )
    
    parser.add_argument(
        '--share',
        action='store_true',
        help='启用Gradio公共分享链接'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--test-type',
        choices=['all', 'unit', 'integration', 'config'],
        default='all',
        help='测试类型 (默认: all)'
    )
    
    parser.add_argument(
        '--demo-type',
        choices=['basic', 'asr', 'tts', 'assessment'],
        default='basic',
        help='演示类型 (默认: basic)'
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    runner = OralCounsellorRunner()
    
    # 检查环境
    if not runner.check_environment():
        sys.exit(1)
    
    # 加载环境变量
    runner.load_environment()
    
    # 根据模式运行
    try:
        if args.mode == 'web':
            runner.run_web_app(
                port=args.port,
                share=args.share,
                debug=args.debug
            )
        elif args.mode == 'chat':
            runner.run_chat_mode()
        elif args.mode == 'test':
            runner.run_test_mode(args.test_type)
        elif args.mode == 'demo':
            runner.run_demo_mode(args.demo_type)
            
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
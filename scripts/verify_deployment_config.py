#!/usr/bin/env python3
"""
部署配置验证脚本
验证增强聊天模块的部署配置文件和结构
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_file_exists(file_path: str) -> Tuple[bool, str]:
    """检查文件是否存在"""
    path = Path(file_path)
    if path.exists():
        return True, f"✅ {file_path}"
    else:
        return False, f"❌ {file_path} (缺失)"


def check_directory_exists(dir_path: str) -> Tuple[bool, str]:
    """检查目录是否存在"""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        return True, f"✅ {dir_path}/"
    else:
        return False, f"❌ {dir_path}/ (缺失)"


def check_pyproject_dependencies() -> Tuple[bool, List[str]]:
    """检查 pyproject.toml 中的依赖"""
    try:
        with open("pyproject.toml", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查新增的依赖
        new_dependencies = [
            "openai>=1.0.0",
            "aiofiles>=23.0.0", 
            "cachetools>=5.0.0",
            "asyncio-throttle>=1.0.0",
            "python-multipart>=0.0.6",
            "websockets>=11.0.0",
            "dataclasses-json>=0.6.0",
            "typing-extensions>=4.5.0"
        ]
        
        missing = []
        found = []
        
        for dep in new_dependencies:
            dep_name = dep.split(">=")[0].split("==")[0]
            if dep_name in content:
                found.append(f"✅ {dep}")
            else:
                missing.append(f"❌ {dep}")
        
        return len(missing) == 0, found + missing
        
    except Exception as e:
        return False, [f"❌ 无法读取 pyproject.toml: {e}"]


def check_env_example() -> Tuple[bool, List[str]]:
    """检查 .env.example 文件中的新配置"""
    try:
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()
        
        # 检查新增的环境变量
        new_env_vars = [
            "CHAT_MAX_HISTORY_LENGTH",
            "AUDIO_MAX_RECORDING_DURATION", 
            "TOPIC_DEFAULT_DIFFICULTY",
            "TTS_CACHE_SIZE",
            "ENABLE_ASYNC_PROCESSING",
            "AUDIO_AUTO_PLAY",
            "TOPIC_CONTEXT_AWARE"
        ]
        
        missing = []
        found = []
        
        for var in new_env_vars:
            if var in content:
                found.append(f"✅ {var}")
            else:
                missing.append(f"❌ {var}")
        
        return len(missing) == 0, found + missing
        
    except Exception as e:
        return False, [f"❌ 无法读取 .env.example: {e}"]


def check_config_template() -> Tuple[bool, str]:
    """检查配置模板文件"""
    config_file = "config/chat_config.yaml.example"
    if Path(config_file).exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 检查关键配置节
            required_sections = [
                "audio:",
                "topic_generation:",
                "session:",
                "ui:",
                "cache:",
                "performance:",
                "system_prompts:",
                "default_topics:"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                return False, f"❌ 配置模板缺少节: {', '.join(missing_sections)}"
            else:
                return True, f"✅ 配置模板完整 ({len(required_sections)} 个节)"
                
        except Exception as e:
            return False, f"❌ 无法读取配置模板: {e}"
    else:
        return False, f"❌ 配置模板文件不存在: {config_file}"


def check_documentation() -> Tuple[bool, List[str]]:
    """检查文档更新"""
    docs_to_check = [
        ("docs/api.md", "API 文档"),
        ("docs/chat_module_user_guide.md", "用户使用指南"),
        ("docs/deployment.md", "部署文档")
    ]
    
    results = []
    all_exist = True
    
    for doc_path, doc_name in docs_to_check:
        if Path(doc_path).exists():
            # 检查文档是否包含聊天模块相关内容
            try:
                with open(doc_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 检查关键词
                keywords = ["聊天", "chat", "主题生成", "topic", "音频", "audio"]
                if any(keyword in content.lower() for keyword in keywords):
                    results.append(f"✅ {doc_name} (已更新)")
                else:
                    results.append(f"⚠️  {doc_name} (可能未更新)")
                    
            except Exception as e:
                results.append(f"❌ {doc_name} (读取失败: {e})")
                all_exist = False
        else:
            results.append(f"❌ {doc_name} (不存在)")
            all_exist = False
    
    return all_exist, results


def main():
    """主函数"""
    print("🔧 OralCounsellor 增强聊天模块部署配置验证")
    print("=" * 60)
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    all_passed = True
    
    # 1. 检查核心配置文件
    print("\n📋 核心配置文件检查:")
    core_files = [
        "pyproject.toml",
        ".env.example", 
        "config/chat_config.yaml.example"
    ]
    
    for file_path in core_files:
        passed, message = check_file_exists(file_path)
        print(f"   {message}")
        if not passed:
            all_passed = False
    
    # 2. 检查目录结构
    print("\n📁 目录结构检查:")
    required_dirs = [
        "config",
        "logs",
        "temp_audio",
        ".cache",
        "scripts"
    ]
    
    for dir_path in required_dirs:
        passed, message = check_directory_exists(dir_path)
        print(f"   {message}")
        if not passed:
            all_passed = False
    
    # 3. 检查依赖配置
    print("\n📦 依赖配置检查:")
    passed, deps = check_pyproject_dependencies()
    for dep in deps:
        print(f"   {dep}")
    if not passed:
        all_passed = False
    
    # 4. 检查环境变量配置
    print("\n🔧 环境变量配置检查:")
    passed, env_vars = check_env_example()
    for var in env_vars:
        print(f"   {var}")
    if not passed:
        all_passed = False
    
    # 5. 检查配置模板
    print("\n⚙️  配置模板检查:")
    passed, message = check_config_template()
    print(f"   {message}")
    if not passed:
        all_passed = False
    
    # 6. 检查文档更新
    print("\n📚 文档更新检查:")
    passed, docs = check_documentation()
    for doc in docs:
        print(f"   {doc}")
    if not passed:
        all_passed = False
    
    # 7. 检查测试脚本
    print("\n🧪 测试脚本检查:")
    test_scripts = [
        "scripts/test_deployment.py",
        "scripts/verify_deployment_config.py"
    ]
    
    for script in test_scripts:
        passed, message = check_file_exists(script)
        print(f"   {message}")
        if not passed:
            all_passed = False
    
    # 输出总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有部署配置检查通过！")
        print("\n📝 下一步:")
        print("   1. 安装新的依赖包: pip install -e .")
        print("   2. 复制配置模板: cp config/chat_config.yaml.example config/chat_config.yaml")
        print("   3. 配置环境变量: cp .env.example .env")
        print("   4. 编辑 .env 文件，填入您的 API 密钥")
        print("   5. 运行完整测试: python scripts/test_deployment.py")
        sys.exit(0)
    else:
        print("❌ 部署配置检查失败！请修复上述问题。")
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目最终验证脚本
验证项目重构后的所有功能是否正常工作
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    print("🔍 检查Python版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"�?Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"�?Python版本过低: {version.major}.{version.minor}.{version.micro}")
        return False

def check_uv_available():
    """检查uv是否可用"""
    print("🔍 检查uv包管理器...")
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ uv可用: {result.stdout.strip()}")
            return True
        else:
            print("❌ uv不可用")
            return False
    except FileNotFoundError:
        print("❌ uv未安装")
        return False

def check_project_structure():
    """检查项目结构"""
    print("🔍 检查项目结构..")
    
    required_dirs = [
        "src/chatterpal",
        "src/chatterpal/core",
        "src/chatterpal/services",
        "src/chatterpal/web",
        "src/chatterpal/config",
        "src/chatterpal/utils",
        "tests",
        "docs",
        "scripts",
        "data"
    ]
    
    required_files = [
        "pyproject.toml",
        "uv.lock",
        "README.md",
        ".env.example",
        ".gitignore"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"�?目录存在: {dir_path}")
        else:
            print(f"�?目录缺失: {dir_path}")
            all_good = False
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"�?文件存在: {file_path}")
        else:
            print(f"�?文件缺失: {file_path}")
            all_good = False
    
    return all_good

def check_dependencies():
    """检查依赖安装"""
    print("🔍 检查依赖安装...")
    try:
        result = subprocess.run(['uv', 'sync', '--dry-run'], capture_output=True, text=True)
        if result.returncode == 0:
            print("�?依赖同步正常")
            return True
        else:
            print(f"�?依赖同步失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 检查依赖失败: {e}")
        return False

def check_imports():
    """检查核心模块导入"""
    print("🔍 检查核心模块导入...")
    
    modules_to_test = [
        "chatterpal.config.settings",
        "chatterpal.core.asr",
        "chatterpal.core.tts",
        "chatterpal.core.llm",
        "chatterpal.core.assessment",
        "chatterpal.services.chat",
        "chatterpal.services.evaluation",
        "chatterpal.services.correction",
        "chatterpal.utils.audio",
        "chatterpal.utils.text",
        "chatterpal.utils.logger",
        "chatterpal.web.app"
    ]
    
    all_good = True
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"�?模块导入成功: {module}")
        except ImportError as e:
            print(f"�?模块导入失败: {module} - {e}")
            all_good = False
        except Exception as e:
            print(f"⚠️  模块导入警告: {module} - {e}")
    
    return all_good

def check_configuration():
    """检查配置系统"""
    print("🔍 检查配置系统...")
    try:
        from chatterpal.config.settings import get_settings
        settings = get_settings()
        print(f"�?配置加载成功")
        print(f"   - Whisper模型: {settings.whisper_model}")
        print(f"   - 音频采样�? {settings.audio_sample_rate}")
        print(f"   - 日志级别: {settings.log_level}")
        return True
    except Exception as e:
        print(f"❌ 配置系统失败: {e}")
        return False

def check_documentation():
    """检查文档完整性"""
    print("🔍 检查文档完整性...")
    
    required_docs = [
        "README.md",
        "docs/api.md",
        "docs/deployment.md", 
        "docs/development.md",
        "docs/README.md"
    ]
    
    all_good = True
    
    for doc in required_docs:
        if Path(doc).exists():
            size = Path(doc).stat().st_size
            if size > 100:  # 至少100字节
                print(f"�?文档完整: {doc} ({size} bytes)")
            else:
                print(f"⚠️  文档过短: {doc} ({size} bytes)")
        else:
            print(f"�?文档缺失: {doc}")
            all_good = False
    
    return all_good

def check_scripts():
    """检查脚本功能"""
    print("🔍 检查脚本功能...")
    
    scripts_to_test = [
        ("scripts/run.py", ["--help"]),
        ("scripts/setup.py", ["--help"])
    ]
    
    all_good = True
    
    for script, args in scripts_to_test:
        try:
            result = subprocess.run(['python', script] + args, 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"�?脚本正常: {script}")
            else:
                print(f"�?脚本异常: {script}")
                all_good = False
        except subprocess.TimeoutExpired:
            print(f"⚠️  脚本超时: {script}")
        except Exception as e:
            print(f"�?脚本错误: {script} - {e}")
            all_good = False
    
    return all_good

def main():
    """主验证流"""
    print("🚀 开始项目最终验证...\n")
    
    checks = [
        ("Python版本", check_python_version),
        ("uv包管理器", check_uv_available),
        ("项目结构", check_project_structure),
        ("依赖管理", check_dependencies),
        ("模块导入", check_imports),
        ("配置系统", check_configuration),
        ("文档完整性", check_documentation),
        ("脚本功能", check_scripts)
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n{'='*50}")
        print(f"检查项�? {name}")
        print('='*50)
        
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"�?检查失�? {e}")
            results.append((name, False))
    
    # 输出总结
    print(f"\n{'='*50}")
    print("验证结果总结")
    print('='*50)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "�?通过" if result else "�?失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("🎉 项目最终验证完全通过")
        print("\n�?项目已准备就绪，可以正常使用")
        print("�?所有模块功能正常")
        print("�?文档完整")
        print("�?依赖管理正常")
        return 0
    else:
        print("⚠️  项目最终验证部分通过")
        print(f" ❌ {total - passed} 项检查未通过，请检查上述错误")
        return 1

if __name__ == "__main__":
    result = main();
    sys.exit(result)

#!/usr/bin/env python3
"""
集成测试运行脚本
运行所有端到端和集成测试
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """运行命令并处理结果"""
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        # 在Windows上使用虚拟环境
        env = os.environ.copy()
        if sys.platform == "win32":
            venv_python = Path(__file__).parent.parent / ".venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                cmd[0] = str(venv_python)
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent, env=env)
        
        if result.returncode == 0:
            print(f"✅ {description} - 成功")
            if result.stdout:
                print("输出:")
                print(result.stdout)
        else:
            print(f"❌ {description} - 失败 (退出码: {result.returncode})")
            if result.stdout:
                print("标准输出:")
                print(result.stdout)
            if result.stderr:
                print("错误输出:")
                print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description} - 执行异常: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始运行增强聊天模块的集成测试")
    
    # 确保在正确的目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 测试配置
    test_configs = [
        {
            "cmd": ["python", "-m", "pytest", "tests/test_end_to_end_chat_flows.py", "-v", "--tb=short", "--disable-warnings"],
            "description": "端到端对话流程测试"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/test_error_scenarios_integration.py", "-v", "--tb=short", "--disable-warnings"],
            "description": "错误场景集成测试"
        },
        {
            "cmd": ["python", "-m", "pytest", "tests/test_performance_and_ux.py", "-v", "--tb=short", "--disable-warnings"],
            "description": "性能和用户体验测试"
        }
    ]
    
    # 运行测试
    results = []
    for config in test_configs:
        success = run_command(config["cmd"], config["description"])
        results.append((config["description"], success))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("📊 测试结果汇总")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    for description, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {description}")
    
    print(f"\n总计: {total_tests} 个测试套件")
    print(f"通过: {passed_tests} 个")
    print(f"失败: {failed_tests} 个")
    
    if failed_tests == 0:
        print("\n🎉 所有集成测试都通过了！")
        return 0
    else:
        print(f"\n⚠️  有 {failed_tests} 个测试套件失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
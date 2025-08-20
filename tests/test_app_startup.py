"""
Test application startup functionality
"""

import pytest
import os
from unittest.mock import patch, Mock

def test_app_startup():
    """测试应用启动功能"""
    try:
        # 设置环境变量以避免真实API调用
        os.environ['ALIBABA_API_KEY'] = 'test_key'
        os.environ['ALIBABA_API_SECRET'] = 'test_secret'
        
        from chatterpal.web.app import create_app
        
        # 模拟Gradio接口以避免实际启
        with patch('gradio.TabbedInterface') as mock_interface:
            mock_interface.return_value = Mock()
            
            app = create_app()
            assert app is not None
            
            print("✅应用可以成功创建")
            
    except Exception as e:
        pytest.fail(f"应用启动测试失败: {e}")
    finally:
        # 清理环境变量
        if 'ALIBABA_API_KEY' in os.environ:
            del os.environ['ALIBABA_API_KEY']
        if 'ALIBABA_API_SECRET' in os.environ:
            del os.environ['ALIBABA_API_SECRET']

def test_run_script_exists():
    """测试运行脚本存在"""
    import os
    
    # 检查运行脚
    run_py_path = "scripts/run.py"
    assert os.path.exists(run_py_path), f"运行脚本 {run_py_path} 不存在"
    
    # 检查脚本可以导
    try:
        import sys
        sys.path.insert(0, 'scripts')
        import run
        assert hasattr(run, 'main') or hasattr(run, 'run_app'), "运行脚本缺少主函数"
        print("✅运行脚本存在且可导入")
    except Exception as e:
        pytest.fail(f"运行脚本测试失败: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])









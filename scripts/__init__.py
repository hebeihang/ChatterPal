"""
OralCounsellor脚本包

包含项目的设置和运行脚本。
"""

from .setup import main as setup_main
from .run import main as run_main

__all__ = ['setup_main', 'run_main']
# -*- coding: utf-8 -*-
"""
ChatterPal - AI-powered English pronunciation practice system.
"""

import os
import sys

# 设置编码环境变量（确保在所有导入之前）
os.environ['PYTHONIOENCODING'] = 'utf-8'
if os.name == 'nt':  # Windows
    os.environ['PYTHONLEGACYWINDOWSSTDIO'] = '1'

__version__ = "0.1.0"
__author__ = "ChatterPal Team"

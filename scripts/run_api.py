#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动API服务器脚�?
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.chatterpal.web.api_server import create_api_server
from src.chatterpal.config.settings import get_settings
from src.chatterpal.utils.logger import get_logger


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    logger = get_logger(__name__)
    
    try:
        # 获取配置
        settings = get_settings()
        logger.info("配置加载完成")
        
        # 创建API服务�?
        server = create_api_server(settings)
        logger.info("API服务器创建完成")
        
        # 启动服务�?
        logger.info("启动API服务�?..")
        logger.info("API服务器地址: http://localhost:8010")
        logger.info("API文档地址: http://localhost:8010/docs")
        logger.info("健康检�? http://localhost:8010/health")
        
        server.run(host="0.0.0.0", port=8010, debug=False)
        
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"启动API服务器失�? {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

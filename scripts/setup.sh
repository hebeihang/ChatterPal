#!/bin/bash
# Shell脚本用于设置OralCounsellor环境

echo "设置OralCounsellor环境..."

# 检查是否安装了uv
if ! command -v uv &> /dev/null; then
    echo "错误: 未找到uv包管理器"
    echo "请访问 https://docs.astral.sh/uv/getting-started/installation/ 安装uv"
    exit 1
fi

# 运行设置脚本
uv run python scripts/setup.py "$@"
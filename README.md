# OralCounsellor

一个基于AI的英语口语练习系统，提供智能对话、发音评估和纠错功能。

## 项目简介

OralCounsellor 是一个现代化的英语口语学习平台，结合了最新的AI技术来帮助用户提高英语口语能力。系统提供三大核心功能：

- **智能对话练习**：与AI导师进行自然对话，提升口语表达能力
- **发音评估打分**：专业级别的发音质量评估和流利度分析
- **发音纠错指导**：基于音素级别的详细发音纠错和改进建议

## 快速开始

### 环境要求

- Python 3.8+
- 4GB+ RAM
- 网络连接（用于API服务）

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/your-org/oralcounsellor.git
cd oralcounsellor
```

#### 2. 安装依赖（推荐使用 uv）
```bash
# 安装 uv（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

#### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
# 详细配置说明请参考 docs/deployment.md
```

#### 4. 启动应用
```bash
# 使用启动脚本
python scripts/run.py

# 或直接运行
uv run python -m oralcounsellor.web.app
```

访问 http://localhost:7860 开始使用！

## 核心功能

### 🎯 技术架构
- **多引擎语音识别**：Whisper（本地）+ 阿里云（云端）双重支持
- **高质量语音合成**：Edge TTS 多种音色选择
- **大模型集成**：OpenAI GPT + 阿里云通义千问
- **专业发音评估**：音素级别和韵律分析

### 🚀 三大主要功能
1. **对话模式**：与AI导师进行互动式口语练习
2. **评分模式**：发音质量评估和流利度打分
3. **纠错模式**：详细的发音纠错和IPA音标分析

### 🔬 技术特色
- 模块化架构，支持依赖注入
- 实时音频处理和分析
- 专业音素级发音纠错
- 多语言支持（专注英语，中文界面）
- 现代化 Gradio Web 界面

## 项目结构

```
oralcounsellor/
├── src/oralcounsellor/          # 主应用代码
│   ├── core/                    # 核心功能模块
│   │   ├── asr/                # 语音识别引擎
│   │   ├── tts/                # 语音合成引擎
│   │   ├── llm/                # 大语言模型接口
│   │   └── assessment/         # 发音评估模块
│   ├── services/               # 业务逻辑服务
│   ├── web/                    # Web界面组件
│   ├── config/                 # 配置管理
│   └── utils/                  # 工具函数
├── scripts/                    # 安装和运行脚本
├── docs/                       # 项目文档
├── tests/                      # 测试套件
└── data/                       # 数据和模型文件
```

## 文档导航

- [API 文档](docs/api.md) - 完整的API参考手册
- [部署指南](docs/deployment.md) - 安装和部署说明
- [开发文档](docs/development.md) - 开发环境搭建和贡献指南
- [纠错系统概述](docs/correction_system_overview.md) - 发音纠错技术详解
- [系统设计](docs/pronunciation_correction_design.md) - 架构和设计决策

## 功能特性

### ✅ 已完成功能
- [x] 多引擎语音识别（Whisper + 阿里云ASR）
- [x] 高质量语音合成（Edge TTS）
- [x] 大语言模型集成（OpenAI + 阿里云通义千问）
- [x] 专业发音评估系统
- [x] 音素级发音纠错
- [x] 韵律分析和评价
- [x] 现代化Web界面（三个功能模块）
- [x] 模块化项目架构
- [x] 统一配置管理
- [x] 完整测试套件

### 🚧 开发中功能
- [ ] 多语言支持扩展
- [ ] 用户学习进度跟踪
- [ ] 个性化学习建议
- [ ] 移动端适配

## 技术栈

- **后端框架**：Python 3.8+
- **Web界面**：Gradio
- **语音识别**：OpenAI Whisper, 阿里云ASR
- **语音合成**：Microsoft Edge TTS
- **大语言模型**：OpenAI GPT, 阿里云通义千问
- **音频处理**：librosa, soundfile
- **依赖管理**：uv
- **测试框架**：pytest

## 贡献指南

我们欢迎所有形式的贡献！请查看 [开发文档](docs/development.md) 了解如何参与项目开发。

### 贡献方式
- 🐛 报告Bug和问题
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- 🌟 分享使用体验

## 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](LICENSE) 文件。

## 联系我们

- 项目主页：[GitHub Repository](https://github.com/your-org/oralcounsellor)
- 问题反馈：[GitHub Issues](https://github.com/your-org/oralcounsellor/issues)
- 在线演示：[Demo](https://aistudio.baidu.com/aistudio/projectdetail/6566149)

## 致谢

感谢所有为项目做出贡献的开发者：
[@Liyulingyue](https://github.com/Liyulingyue/), [@mrcangye](https://github.com/mrcangye/), [@ccsuzzh](https://github.com/ccsuzzh/), [@gouzil](https://github.com/gouzil/), [@Tomoko-hjf](https://github.com/Tomoko-hjf/)


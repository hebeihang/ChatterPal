# ChatterPal 项目架构文档

## 概述

ChatterPal 是一个基于 AI 的英语口语练习系统，提供智能对话练习和发音纠错功能。项目采用前后端分离架构，后端使用 Python + Gradio，前端使用 React + TypeScript。

## 技术栈

### 后端技术栈
- **语言**: Python 3.12+
- **Web框架**: Gradio 4.0+
- **AI服务**: 
  - ASR: OpenAI Whisper / 阿里云语音识别
  - TTS: Edge TTS / 阿里百炼 TTS
  - LLM: 阿里百炼 / OpenAI GPT
- **音频处理**: librosa, soundfile, scipy
- **语音分析**: myprosody, praat-parselmouth
- **配置管理**: pydantic, pydantic-settings
- **依赖管理**: uv (pyproject.toml)

### 前端技术栈
- **语言**: TypeScript
- **框架**: React 18.2+
- **构建工具**: Vite 5.0+
- **HTTP客户端**: Axios
- **开发工具**: ESLint, TypeScript ESLint

## 项目结构

```
ChatterPal/
├── src/chatterpal/           # 后端核心代码
│   ├── config/                   # 配置管理
│   ├── core/                     # 核心模块
│   │   ├── asr/                  # 语音识别
│   │   ├── tts/                  # 语音合成
│   │   ├── llm/                  # 大语言模型
│   │   └── assessment/           # 发音评估
│   ├── services/                 # 业务服务层
│   ├── utils/                    # 工具模块
│   └── web/                      # Web界面
├── frontend/                     # 前端代码
│   └── src/
│       ├── components/           # React组件
│       ├── App.tsx              # 主应用
│       └── main.tsx             # 入口文件
├── tests/                        # 测试代码
├── scripts/                      # 脚本工具
├── docs/                         # 项目文档
├── config/                       # 配置文件
└── data/                         # 数据目录
```

## 核心架构

### 1. 配置管理层 (config/)

**核心文件**: `settings.py`, `loader.py`

- **Settings类**: 基于 Pydantic 的类型安全配置管理
- **环境变量支持**: 支持 .env 文件和环境变量
- **配置验证**: 自动验证配置参数的有效性
- **多服务配置**: 统一管理 ASR、TTS、LLM 等服务配置

**主要配置项**:
- API密钥 (阿里云、OpenAI)
- 模型参数 (Whisper模型、LLM参数)
- 音频配置 (采样率、最大时长)
- Web服务配置 (端口、主机)

### 2. 核心模块层 (core/)

#### 2.1 语音识别 (ASR)
```
asr/
├── base.py          # ASR基类和接口定义
├── whisper.py       # OpenAI Whisper实现
└── aliyun.py        # 阿里云语音识别实现
```

**设计模式**: 策略模式 + 工厂模式
- 统一的ASR接口 (`ASRBase`)
- 可插拔的ASR实现
- 错误处理和重试机制

#### 2.2 语音合成 (TTS)
```
tts/
├── base.py          # TTS基类和接口定义
├── edge.py          # Edge TTS实现
├── alibaba.py       # 阿里百炼TTS实现
└── alibaba_simple.py # 简化版阿里TTS
```

**特性**:
- 多语音引擎支持
- 音频格式统一处理
- 流式音频生成
- 缓存机制

#### 2.3 大语言模型 (LLM)
```
llm/
├── base.py          # LLM基类和对话管理
├── alibaba.py       # 阿里百炼LLM实现
└── openai.py        # OpenAI GPT实现
```

**核心功能**:
- 对话上下文管理 (`Conversation`类)
- 消息历史管理
- 流式响应支持
- 错误处理和重试

#### 2.4 发音评估 (Assessment)
```
assessment/
├── base.py          # 评估基类和数据结构
├── corrector.py     # 发音纠错器
├── phoneme.py       # 音素分析
└── prosody.py       # 韵律分析
```

**评估维度**:
- 发音准确性
- 流利度
- 韵律特征
- 音素级别分析

### 3. 业务服务层 (services/)

#### 3.1 对话服务 (ChatService)
**文件**: `chat.py`

**核心功能**:
- 多轮对话管理
- 会话状态维护
- 音频/文本输入处理
- 主题生成和管理
- 上下文增强

**关键类**:
- `ChatSession`: 单个用户会话管理
- `ChatService`: 核心对话服务
- `TopicGenerator`: 智能主题生成

#### 3.2 纠错服务 (CorrectionService)
**文件**: `correction.py`

**核心功能**:
- 综合发音评估
- 多维度错误检测
- 个性化改进建议
- 练习推荐

**评估流程**:
1. 音频识别
2. 发音评估
3. 音素分析
4. 韵律分析
5. 生成纠错报告

#### 3.3 其他服务
- `evaluation.py`: 评估服务
- `ai_correction.py`: AI驱动的纠错
- `topic_generator.py`: 主题生成器
- `chat_config.py`: 聊天配置管理

### 4. Web界面层 (web/)

#### 4.1 后端Web (Gradio)
**文件**: `app.py`

**架构特点**:
- 组件化设计
- 标签页界面
- 实时音频处理
- 状态管理

**主要组件**:
- `ChatTab`: 对话练习界面
- `ScoreTab`: 评分界面
- `CorrectTab`: 纠错界面

#### 4.2 前端Web (React)
**主要组件**:
- `App.tsx`: 主应用，标签页切换
- `ChatInterface.tsx`: 对话界面
- `PronunciationCorrection.tsx`: 发音纠错界面
- `AudioRecorder.tsx`: 音频录制组件
- `MessageBubble.tsx`: 消息气泡组件

### 5. 工具模块层 (utils/)

**核心工具**:
- `audio.py`: 音频处理工具
- `encoding_fix.py`: 编码修复
- `logger.py`: 日志管理
- `cache.py`: 缓存管理
- `preferences.py`: 用户偏好
- `text.py`: 文本处理

## 数据流架构

### 对话流程
```
用户输入(音频/文本) → ASR识别 → LLM处理 → TTS合成 → 返回响应
                    ↓
                会话管理 → 上下文维护 → 主题生成
```

### 纠错流程
```
用户音频 → ASR识别 → 发音评估 → 音素分析 → 韵律分析 → 生成报告
         ↓
      目标文本对比 → 错误检测 → 改进建议 → 练习推荐
```

## 部署架构

### 开发环境
- 后端: `python scripts/run.py` (Gradio开发服务器)
- 前端: `npm run dev` (Vite开发服务器)
- 端口: 后端7860, 前端5173

### 生产环境
- 容器化部署支持
- 环境变量配置
- 日志管理
- 性能监控

## 扩展性设计

### 1. 插件化架构
- ASR/TTS/LLM 提供商可插拔
- 统一接口设计
- 工厂模式创建实例

### 2. 配置驱动
- 运行时配置切换
- 环境特定配置
- 热重载支持

### 3. 模块化设计
- 松耦合组件
- 清晰的依赖关系
- 易于测试和维护

## 性能优化

### 1. 缓存策略
- 模型缓存
- 音频缓存
- 会话缓存

### 2. 异步处理
- 音频流式处理
- 并发请求处理
- 非阻塞I/O

### 3. 资源管理
- 内存优化
- 临时文件清理
- 连接池管理

## 安全考虑

### 1. 数据安全
- API密钥保护
- 音频数据加密
- 用户隐私保护

### 2. 访问控制
- 主机白名单
- 请求限流
- 输入验证

## 监控和日志

### 1. 日志系统
- 结构化日志
- 多级别日志
- 文件和控制台输出

### 2. 错误处理
- 统一错误处理
- 错误分类
- 用户友好提示

### 3. 性能监控
- 响应时间监控
- 资源使用监控
- 服务健康检查

## 测试架构

### 1. 测试分层
- 单元测试: 核心模块测试
- 集成测试: 服务间集成测试
- 端到端测试: 完整流程测试

### 2. 测试工具
- pytest: Python测试框架
- 模拟对象: 外部服务模拟
- 测试数据: 标准测试集

## 未来规划

### 1. 功能扩展
- 多语言支持
- 高级语音分析
- 个性化学习路径

### 2. 技术升级
- 微服务架构
- 云原生部署
- AI模型优化

### 3. 用户体验
- 移动端适配
- 离线模式
- 社交功能

---

本文档提供了 ChatterPal 项目的完整架构概览，涵盖了技术栈、模块设计、数据流、部署方案等各个方面，为开发者理解和维护项目提供了全面的参考。
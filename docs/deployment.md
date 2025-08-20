# ChatterPal Deployment Guide

## System Requirements

### Minimum Requirements
- Python 3.8+
- 4GB RAM
- 2GB free disk space
- Internet connection for API services

### Recommended Requirements
- Python 3.10+
- 8GB RAM
- 5GB free disk space
- GPU support for faster Whisper processing (optional)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/chatterpal.git
cd chatterpal
```

### 2. Set Up Python Environment

#### Using uv (Recommended)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

#### Using pip
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Configure Environment Variables
```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

### 4. 必需的环境变量配置

#### ASR 配置
```bash
# Whisper (本地处理)
WHISPER_MODEL=base  # 选项: tiny, base, small, medium, large

# 阿里云 ASR (云服务)
ALIYUN_ASR_APP_KEY=your_app_key
ALIYUN_ASR_ACCESS_KEY_ID=your_access_key_id
ALIYUN_ASR_ACCESS_KEY_SECRET=your_access_key_secret
```

#### TTS 配置
```bash
# Edge TTS (免费服务)
EDGE_TTS_VOICE=en-US-JennyNeural
```

#### LLM 配置
```bash
# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 阿里百炼 (Alibaba Bailian) - OpenAI 兼容接口
DASHSCOPE_API_KEY=your_dashscope_api_key
ALIBABA_MODEL=qwen-plus
ALIBABA_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ALIBABA_MAX_TOKENS=2000
ALIBABA_TEMPERATURE=0.7
ALIBABA_TOP_P=0.8
ALIBABA_ENABLE_SEARCH=false
```

#### 增强聊天模块配置
```bash
# 会话管理
CHAT_MAX_HISTORY_LENGTH=50
CHAT_SESSION_TIMEOUT=3600
CHAT_AUTO_SAVE=true
CHAT_MAX_SESSIONS=100

# 音频配置
AUDIO_MAX_RECORDING_DURATION=60
AUDIO_MIN_RECORDING_DURATION=1
AUDIO_SAMPLE_RATE=16000
AUDIO_AUTO_PLAY=true
AUDIO_PLAYBACK_SPEED=1.0
AUDIO_VOLUME=0.8

# 主题生成配置
TOPIC_DEFAULT_DIFFICULTY=intermediate
TOPIC_MAX_RETRIES=3
TOPIC_CONTEXT_AWARE=true
TOPIC_PREFERRED_CATEGORIES=daily,hobby,travel

# 缓存配置
TTS_CACHE_SIZE=1000
TTS_CACHE_TTL=3600
CHAT_CACHE_SIZE=500
ENABLE_AUDIO_CACHE=true

# 性能优化
ENABLE_ASYNC_PROCESSING=true
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
```

#### 基础应用配置
```bash
# 通用设置
ASSESSMENT_LANGUAGE=en-US
LOG_LEVEL=INFO
TEMP_AUDIO_DIR=temp_audio
```

## Running the Application

### Development Mode
```bash
# Using the run script
python scripts/run.py

# Or directly
python -m chatterpal.web.app
```

### Production Mode

#### Using Gunicorn (Linux/Mac)
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:7860 chatterpal.web.app:app
```

#### Using Waitress (Windows)
```bash
# Install waitress
pip install waitress

# Run with waitress
waitress-serve --host=0.0.0.0 --port=7860 chatterpal.web.app:app
```

## Docker Deployment

### 1. 构建 Docker 镜像
```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 依赖
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip install --system -e .

# 创建必要的目录
RUN mkdir -p logs temp_audio .cache/audio .cache/tts config

# 复制应用代码
COPY . .

# 复制配置模板
COPY config/chat_config.yaml.example config/chat_config.yaml

# 设置权限
RUN chmod +x scripts/run.py

# 暴露端口
EXPOSE 7860

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# 运行应用
CMD ["python", "scripts/run.py"]
```

### 2. Build and Run
```bash
# Build image
docker build -t chatterpal .

# Run container
docker run -p 7860:7860 --env-file .env chatterpal
```

### 3. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  chatterpal:
    build: .
    ports:
      - "7860:7860"
    env_file:
      - .env
    volumes:
      - ./temp_audio:/app/temp_audio
      - ./logs:/app/logs
      - ./.cache:/app/.cache
      - ./config:/app/config
      - ./data:/app/data
    environment:
      - PYTHONPATH=/app/src
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Redis 缓存服务（可选）
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

volumes:
  redis_data:
```

#### 生产环境 Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  chatterpal:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "7860:7860"
    env_file:
      - .env.prod
    volumes:
      - ./temp_audio:/app/temp_audio
      - ./logs:/app/logs
      - ./.cache:/app/.cache
      - ./config:/app/config
    environment:
      - PYTHONPATH=/app/src
      - ENVIRONMENT=production
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - chatterpal
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru

volumes:
  redis_data:
```

```bash
# Run with docker-compose
docker-compose up -d
```

## Cloud Deployment

### Hugging Face Spaces
1. Create a new Space on Hugging Face
2. Upload your code to the Space repository
3. Add environment variables in Space settings
4. The app will automatically deploy

### Railway
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -e .`
4. Set start command: `python scripts/run.py`
5. Add environment variables

### Google Cloud Run
```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/chatterpal

# Deploy to Cloud Run
gcloud run deploy --image gcr.io/PROJECT_ID/chatterpal --platform managed
```

## 配置选项

### 增强聊天模块配置

#### 聊天配置文件设置
```bash
# 复制配置模板
cp config/chat_config.yaml.example config/chat_config.yaml

# 编辑配置文件
nano config/chat_config.yaml
```

#### 音频处理配置
```bash
# 音频质量设置
AUDIO_SAMPLE_RATE=16000        # 16kHz 推荐用于语音识别
AUDIO_MAX_RECORDING_DURATION=60  # 最大录音时长
AUDIO_AUTO_PLAY=true           # 自动播放 AI 回复

# 音频缓存设置
ENABLE_AUDIO_CACHE=true        # 启用音频缓存
AUDIO_CACHE_DIR=.cache/audio   # 缓存目录
TTS_CACHE_SIZE=1000           # TTS 缓存大小
```

#### 主题生成配置
```bash
# 主题生成设置
TOPIC_DEFAULT_DIFFICULTY=intermediate  # 默认难度级别
TOPIC_CONTEXT_AWARE=true              # 启用上下文感知
TOPIC_MAX_RETRIES=3                   # 生成失败重试次数

# 用户偏好设置
TOPIC_PREFERRED_CATEGORIES=daily,hobby,travel  # 偏好主题分类
```

#### 会话管理配置
```bash
# 会话设置
CHAT_MAX_HISTORY_LENGTH=50     # 最大对话历史长度
CHAT_SESSION_TIMEOUT=3600      # 会话超时时间（秒）
CHAT_AUTO_SAVE=true           # 自动保存会话
CHAT_MAX_SESSIONS=100         # 最大并发会话数
```

#### 性能优化配置
```bash
# 异步处理
ENABLE_ASYNC_PROCESSING=true   # 启用异步处理
MAX_CONCURRENT_REQUESTS=10     # 最大并发请求数

# 缓存优化
TTS_CACHE_TTL=3600            # TTS 缓存过期时间
CHAT_CACHE_TTL=1800           # 聊天缓存过期时间

# 重试机制
RETRY_ATTEMPTS=3              # 重试次数
RETRY_DELAY=1.0               # 重试延迟（秒）
```

### ASR 引擎选择
```bash
# 在 .env 文件中设置
DEFAULT_ASR_ENGINE=whisper  # 或 'aliyun'
```

### TTS 语音选项
```bash
# 英语语音
EDGE_TTS_VOICE=en-US-JennyNeural
EDGE_TTS_VOICE=en-US-GuyNeural
EDGE_TTS_VOICE=en-GB-SoniaNeural

# 其他语言
EDGE_TTS_VOICE=zh-CN-XiaoxiaoNeural  # 中文
EDGE_TTS_VOICE=ja-JP-NanamiNeural    # 日语
```

### 模型性能调优
```bash
# Whisper 模型大小（影响速度与准确性）
WHISPER_MODEL=tiny    # 最快，准确性最低
WHISPER_MODEL=base    # 平衡
WHISPER_MODEL=small   # 良好准确性
WHISPER_MODEL=medium  # 更好准确性
WHISPER_MODEL=large   # 最佳准确性，最慢
```

## Monitoring and Logging

### Log Configuration
```bash
# Set log level
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR

# Log file location
LOG_FILE=logs/chatterpal.log
```

### Health Check Endpoint
The application provides a health check endpoint at `/health`:
```bash
curl http://localhost:7860/health
```

## Troubleshooting

### 常见问题

#### 1. 音频处理错误
```bash
# 安装 ffmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg portaudio19-dev

# macOS
brew install ffmpeg portaudio

# Windows
# 从 https://ffmpeg.org/download.html 下载
```

#### 2. 内存问题
```bash
# 减少 Whisper 模型大小
WHISPER_MODEL=tiny

# 或使用云端 ASR
DEFAULT_ASR_ENGINE=aliyun

# 调整缓存大小
TTS_CACHE_SIZE=500
CHAT_CACHE_SIZE=250
```

#### 3. API 速率限制
```bash
# 添加请求间延迟
API_RATE_LIMIT_DELAY=1.0

# 使用不同的 API 密钥进行负载均衡
OPENAI_API_KEY_BACKUP=your_backup_key

# 减少并发请求数
MAX_CONCURRENT_REQUESTS=5
```

#### 4. 端口已被占用
```bash
# 更改运行脚本中的端口
python scripts/run.py --port 7861

# 或在环境变量中设置
GRADIO_PORT=7861
```

#### 5. 聊天模块特定问题

##### 主题生成失败
```bash
# 检查 LLM 服务连接
curl -X POST "https://api.openai.com/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}]}'

# 使用备用主题配置
TOPIC_USE_FALLBACK=true
```

##### 语音识别准确性低
```bash
# 调整音频质量设置
AUDIO_NOISE_THRESHOLD=0.05
AUDIO_MIN_RECORDING_DURATION=2

# 使用更大的 Whisper 模型
WHISPER_MODEL=small
```

##### 会话管理问题
```bash
# 清理过期会话
CHAT_CLEANUP_INTERVAL=3600

# 减少历史记录长度
CHAT_MAX_HISTORY_LENGTH=20

# 启用自动保存
CHAT_AUTO_SAVE=true
```

##### 缓存问题
```bash
# 清理缓存目录
rm -rf .cache/audio/*
rm -rf .cache/tts/*

# 重新配置缓存
ENABLE_AUDIO_CACHE=false  # 临时禁用
```

### Performance Optimization

#### 1. Enable GPU for Whisper
```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Whisper will automatically use GPU if available
```

#### 2. Audio Caching
```bash
# Enable audio caching
ENABLE_AUDIO_CACHE=true
AUDIO_CACHE_DIR=cache/audio
```

#### 3. Model Caching
```bash
# Cache downloaded models
MODEL_CACHE_DIR=cache/models
```

## Security Considerations

### 1. API Key Management
- Never commit API keys to version control
- Use environment variables or secure key management services
- Rotate API keys regularly

### 2. Audio File Security
- Implement file size limits
- Validate audio file formats
- Clean up temporary files regularly

### 3. Network Security
- Use HTTPS in production
- Implement rate limiting
- Add authentication if needed

## Backup and Recovery

### 1. Configuration Backup
```bash
# Backup environment configuration
cp .env .env.backup
```

### 2. Model Cache Backup
```bash
# Backup downloaded models
tar -czf models_backup.tar.gz cache/models/
```

### 3. User Data Backup
```bash
# If storing user sessions or data
tar -czf user_data_backup.tar.gz data/users/
```

## Support

For deployment issues:
1. Check the logs for error messages
2. Verify all environment variables are set correctly
3. Ensure all dependencies are installed
4. Check system requirements are met
5. Consult the [development guide](development.md) for additional help

For production deployments, consider:
- Load balancing for high traffic
- Database integration for user management
- CDN for static assets
- Monitoring and alerting systems
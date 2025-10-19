# 配置文件
import os

# OpenAI API 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
OPENAI_MODEL = "gpt-4"

# 语音识别配置
VOICE_RECOGNITION_LANGUAGE = "zh-CN"
VOICE_TIMEOUT = 5  # 语音识别超时时间（秒）
VOICE_PHRASE_TIMEOUT = 0.3  # 语音间隔超时时间（秒）

# 语音合成配置
TTS_RATE = 200  # 语音速度
TTS_VOLUME = 0.9  # 语音音量

# 系统配置
DEFAULT_MUSIC_PATH = "~/Music"  # 默认音乐路径
DEFAULT_DOCUMENT_PATH = "~/Documents"  # 默认文档路径

# 应用配置
APP_NAME = "语音控制AI助手"
APP_VERSION = "1.0.0"

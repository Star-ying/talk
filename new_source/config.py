# 配置文件
import os

# OpenAI API 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "sk-6175f4c9a399401d914d11b1e1db1873")
DASHSCOPE_MODEL = "qwen-plus"

# 语音识别配置
VOICE_RECOGNITION_LANGUAGE = "zh-CN"
VOICE_TIMEOUT = 5  # 语音识别超时时间（秒）
VOICE_PHRASE_TIMEOUT = 0.3  # 语音间隔超时时间（秒）

# 语音合成配置
TTS_RATE = 200  # 语音速度
TTS_VOLUME = 0.9  # 语音音量

# 系统配置
DEFAULT_MUSIC_PATH = "F:\\程序员的日常\\python\\new_source\\Music"  # 默认音乐路径
DEFAULT_DOCUMENT_PATH = "F:\\程序员的日常\\python\\new_source\\Documents"  # 默认文档路径

# 应用配置
APP_NAME = "语音控制AI助手"
APP_VERSION = "1.0.0"

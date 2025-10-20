# 语音控制AI助手

一个基于大模型的语音控制应用，可以通过语音对话控制电脑执行各种任务。

## 功能特性

- 🎤 语音识别与理解
- 🤖 GPT-4 驱动的智能对话
- 🔊 语音合成反馈
- 💻 系统控制（播放音乐、文件操作等）
- 📝 文本生成与处理
- 🔄 多步骤任务编排
- 🧠 上下文记忆

## 技术栈

- Python 3.8+
- OpenAI GPT-4 API
- SpeechRecognition (语音识别)
- pyttsx3 (语音合成)
- tkinter (GUI界面)
- subprocess (系统控制)

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
python main.py
```

## 配置

在 `config.py` 中设置你的 OpenAI API Key：

```python
OPENAI_API_KEY = "your-api-key-here"
```

## 支持的命令示例

- "播放音乐"
- "写一篇关于人工智能的文章"
- "打开浏览器"
- "总结这个文档"
- "设置明天上午9点的提醒"

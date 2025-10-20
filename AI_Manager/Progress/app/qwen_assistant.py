"""
GPT-4 API集成模块 → 已改造为【通义千问 Qwen】API集成模块
用于意图理解和任务处理
"""
import json
import re
from config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL  # 确保 config.py 中有这两个配置
import dashscope
from dashscope import Generation


class QWENAssistant:
    def __init__(self):
        # 设置 DashScope API Key（✅ 替代 OpenAI 的 api_key）
        dashscope.api_key = DASHSCOPE_API_KEY

        # 模型名称（如 qwen-max, qwen-plus, qwen-turbo）
        self.model_name = DASHSCOPE_MODEL or 'qwen-max'

        # 对话历史记录
        self.conversation_history = []

        # 🔧 系统提示词：定义 AI 助手的角色和输出格式（保持不变）
        self.system_prompt = """
你是一个智能语音控制助手，能够理解用户的语音指令并执行相应的任务。

你的主要能力包括：
1. 播放音乐和控制媒体
2. 文件操作（创建、读取、编辑文件）
3. 文本生成（写文章、总结、翻译等）
4. 系统控制（打开应用、设置提醒等）
5. 多步骤任务编排

当用户发出指令时，你需要：
1. 理解用户的意图
2. 确定需要执行的具体操作
3. 返回结构化的响应，包含操作类型和参数

🎯 响应格式必须是严格合法的 JSON：
{
    "intent": "操作类型",
    "action": "具体动作",
    "parameters": {"参数名": "参数值"},
    "response": "给用户的回复",
    "needs_confirmation": true/false
}

📌 支持的操作类型：
- music: 音乐相关操作
- file: 文件操作
- text: 文本生成
- system: 系统控制
- task: 多步骤任务
- chat: 普通对话

❗请始终用中文回复用户。
"""

    def process_voice_command(self, voice_text):
        """处理语音指令，返回结构化 JSON 响应"""
        if not voice_text.strip():
            return self._create_response("chat", "empty", {}, "我没有听清楚，请重新说话。", False)

        # 添加用户输入到对话历史
        self.conversation_history.append({"role": "user", "content": voice_text})

        try:
            # 构建消息列表：系统提示 + 最近最多10轮对话（限制上下文长度）
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history[-10:])  # 保留最近对话

            # 🚀 调用通义千问模型（✅ 替代 openai.ChatCompletion.create）
            response = Generation.call(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                top_p=0.8,
                max_tokens=1024
            )

            # ✅ 修改点1：不再使用 .choices[0].message.content（OpenAI 特有）
            if response.status_code != 200:
                print(f"[错误] Qwen API 调用失败: {response.status_code}, {response.message}")
                return self._create_response("chat", "error", {}, f"服务暂时不可用: {response.message}", False)

            # ✅ 正确获取输出内容（通义千问专用）
            ai_response = response.output['text'].strip()
            print(f"[DEBUG] 模型原始输出: {ai_response}")  # 调试用

            # 将模型回复加入对话历史
            self.conversation_history.append({"role": "assistant", "content": ai_response})

            # 尝试解析 JSON 响应
            try:
                parsed_response = json.loads(ai_response)
                return parsed_response
            except json.JSONDecodeError:
                # 如果不是完整 JSON，尝试提取大括号内的部分
                json_match = re.search(r'\{[\s\S]*\}', ai_response)  # 匹配第一个完整的 { ... }
                if json_match:
                    try:
                        parsed_response = json.loads(json_match.group())
                        return parsed_response
                    except json.JSONDecodeError:
                        pass

                # 若仍无法解析，作为普通聊天返回
                return self._create_response("chat", "reply", {}, ai_response, False)

        except Exception as e:
            print(f"[异常] GPT API调用错误: {e}")
            return self._create_response("chat", "error", {}, "抱歉，我遇到了一些技术问题，请稍后再试。", False)

    def _create_response(self, intent, action, parameters, response, needs_confirmation):
        """创建标准响应格式"""
        return {
            "intent": intent,
            "action": action,
            "parameters": parameters,
            "response": response,
            "needs_confirmation": needs_confirmation
        }

    # -----------------------------
    # ✅ 所有生成类方法也改为使用 Qwen
    # -----------------------------

    def generate_text(self, prompt, task_type="general"):
        """生成指定类型的文本内容"""
        try:
            system_prompt = f"""
你是一个专业的文本生成助手。根据用户的要求生成高质量的文本内容。

任务类型：{task_type}
要求：{prompt}

请生成相应的文本内容，确保内容准确、有逻辑、语言流畅。
"""
            response = Generation.call(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )

            if response.status_code == 200:
                return response.output['text']
            else:
                print(f"文本生成失败: {response.message}")
                return f"生成失败: {response.message}"

        except Exception as e:
            print(f"文本生成错误: {e}")
            return f"抱歉，生成文本时遇到错误：{str(e)}"

    def summarize_text(self, text):
        """总结文本内容"""
        try:
            prompt = f"请总结以下文本的主要内容：\n\n{text}"
            response = Generation.call(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            if response.status_code == 200:
                return response.output['text']
            else:
                return f"总结失败: {response.message}"
        except Exception as e:
            print(f"文本总结错误: {e}")
            return f"抱歉，总结文本时遇到错误：{str(e)}"

    def translate_text(self, text, target_language="英文"):
        """翻译文本"""
        try:
            prompt = f"请将以下文本翻译成{target_language}：\n\n{text}"
            response = Generation.call(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            if response.status_code == 200:
                return response.output['text']
            else:
                return f"翻译失败: {response.message}"
        except Exception as e:
            print(f"文本翻译错误: {e}")
            return f"抱歉，翻译文本时遇到错误：{str(e)}"

    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()


# =============================
# 🧪 测试代码
# =============================
if __name__ == "__main__":
    assistant = QWENAssistant()

    test_commands = [
        "播放周杰伦的歌曲",
        "写一篇关于气候变化的文章",
        "把这段话翻译成英文：今天天气真好",
        "总结一下人工智能的发展历程",
        "你好啊",
        "打开浏览器"
    ]

    for cmd in test_commands:
        print(f"\n🔊 用户指令: {cmd}")
        result = assistant.process_voice_command(cmd)
        print("🤖 AI响应:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

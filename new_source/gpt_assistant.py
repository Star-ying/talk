"""
GPT-4 API集成模块
用于意图理解和任务处理
"""
import openai
import json
import re
from config import OPENAI_API_KEY, OPENAI_MODEL


class GPTAssistant:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.conversation_history = []
        
        # 系统提示词，定义AI助手的角色和能力
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

响应格式必须是JSON：
{
    "intent": "操作类型",
    "action": "具体动作",
    "parameters": {"参数名": "参数值"},
    "response": "给用户的回复",
    "needs_confirmation": true/false
}

支持的操作类型：
- music: 音乐相关操作
- file: 文件操作
- text: 文本生成
- system: 系统控制
- task: 多步骤任务
- chat: 普通对话

请始终用中文回复用户。
"""
    
    def process_voice_command(self, voice_text):
        """处理语音指令"""
        if not voice_text.strip():
            return self._create_response("chat", "请重新说话", {}, "我没有听清楚，请重新说话。", False)
        
        # 添加用户输入到对话历史
        self.conversation_history.append({"role": "user", "content": voice_text})
        
        try:
            # 构建消息
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history[-10:])  # 只保留最近10轮对话
            
            # 调用GPT-4 API
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # 尝试解析JSON响应
            try:
                parsed_response = json.loads(ai_response)
                return parsed_response
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试提取JSON部分
                json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if json_match:
                    try:
                        parsed_response = json.loads(json_match.group())
                        return parsed_response
                    except json.JSONDecodeError:
                        pass
                
                # 如果无法解析JSON，返回默认响应
                return self._create_response("chat", "reply", {}, ai_response, False)
                
        except Exception as e:
            print(f"GPT API调用错误: {e}")
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
    
    def generate_text(self, prompt, task_type="general"):
        """生成文本内容"""
        try:
            system_prompt = f"""
你是一个专业的文本生成助手。根据用户的要求生成高质量的文本内容。

任务类型：{task_type}
要求：{prompt}

请生成相应的文本内容，确保内容准确、有逻辑、语言流畅。
"""
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"文本生成错误: {e}")
            return f"抱歉，生成文本时遇到错误：{str(e)}"
    
    def summarize_text(self, text):
        """总结文本内容"""
        try:
            prompt = f"请总结以下文本的主要内容：\n\n{text}"
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"文本总结错误: {e}")
            return f"抱歉，总结文本时遇到错误：{str(e)}"
    
    def translate_text(self, text, target_language="英文"):
        """翻译文本"""
        try:
            prompt = f"请将以下文本翻译成{target_language}：\n\n{text}"
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"文本翻译错误: {e}")
            return f"抱歉，翻译文本时遇到错误：{str(e)}"
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []


if __name__ == "__main__":
    # 测试GPT助手
    assistant = GPTAssistant()
    
    test_commands = [
        "播放音乐",
        "写一篇关于人工智能的文章",
        "打开浏览器",
        "总结这个文档",
        "你好，今天天气怎么样？"
    ]
    
    for cmd in test_commands:
        print(f"\n用户指令: {cmd}")
        response = assistant.process_voice_command(cmd)
        print(f"AI响应: {json.dumps(response, ensure_ascii=False, indent=2)}")

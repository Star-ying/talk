"""
语音合成模块
将文本转换为语音输出
"""
import pyttsx3
import threading
import queue
import time
from config import TTS_RATE, TTS_VOLUME


class TextToSpeech:
    def __init__(self):
        self.engine = None
        self.is_speaking = False
        self.speech_queue = queue.Queue()
        self.speech_thread = None
        self.stop_speaking = False
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """初始化语音合成引擎"""
        try:
            self.engine = pyttsx3.init()
            
            # 设置语音参数
            self.engine.setProperty('rate', TTS_RATE)  # 语音速度
            self.engine.setProperty('volume', TTS_VOLUME)  # 音量
            
            # 获取可用的语音
            voices = self.engine.getProperty('voices')
            if voices:
                # 尝试找到中文语音
                for voice in voices:
                    if 'chinese' in voice.name.lower() or 'mandarin' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                else:
                    # 如果没有找到中文语音，使用第一个可用的
                    self.engine.setProperty('voice', voices[0].id)
            
            print("语音合成引擎初始化成功")
            
        except Exception as e:
            print(f"语音合成引擎初始化失败: {e}")
            self.engine = None
    
    def speak(self, text, interrupt=True):
        """语音输出文本"""
        if not self.engine:
            print("语音合成引擎未初始化")
            return False
        
        if not text.strip():
            return False
        
        try:
            if interrupt and self.is_speaking:
                self.stop_current_speech()
            
            # 将文本添加到队列
            self.speech_queue.put(text)
            
            # 启动语音线程
            if not self.speech_thread or not self.speech_thread.is_alive():
                self.speech_thread = threading.Thread(target=self._speech_worker)
                self.speech_thread.daemon = True
                self.speech_thread.start()
            
            return True
            
        except Exception as e:
            print(f"语音输出失败: {e}")
            return False
    
    def speak_async(self, text):
        """异步语音输出"""
        thread = threading.Thread(target=self._speak_sync, args=(text,))
        thread.daemon = True
        thread.start()
    
    def _speak_sync(self, text):
        """同步语音输出"""
        if not self.engine:
            return
        
        try:
            self.is_speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
            self.is_speaking = False
        except Exception as e:
            print(f"语音输出异常: {e}")
            self.is_speaking = False
    
    def _speech_worker(self):
        """语音工作线程"""
        while not self.stop_speaking:
            try:
                # 从队列获取文本
                text = self.speech_queue.get(timeout=1)
                
                if text is None:  # 停止信号
                    break
                
                # 执行语音输出
                self.is_speaking = True
                self.engine.say(text)
                self.engine.runAndWait()
                self.is_speaking = False
                
                self.speech_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"语音工作线程异常: {e}")
                self.is_speaking = False
    
    def stop_current_speech(self):
        """停止当前语音输出"""
        try:
            if self.is_speaking and self.engine:
                self.engine.stop()
                self.is_speaking = False
            
            # 清空队列
            while not self.speech_queue.empty():
                try:
                    self.speech_queue.get_nowait()
                except queue.Empty:
                    break
            
        except Exception as e:
            print(f"停止语音输出失败: {e}")
    
    def pause_speech(self):
        """暂停语音输出"""
        try:
            if self.is_speaking and self.engine:
                self.engine.stop()
                self.is_speaking = False
        except Exception as e:
            print(f"暂停语音输出失败: {e}")
    
    def set_rate(self, rate):
        """设置语音速度"""
        try:
            if self.engine:
                self.engine.setProperty('rate', rate)
        except Exception as e:
            print(f"设置语音速度失败: {e}")
    
    def set_volume(self, volume):
        """设置音量"""
        try:
            if self.engine:
                self.engine.setProperty('volume', volume)
        except Exception as e:
            print(f"设置音量失败: {e}")
    
    def get_available_voices(self):
        """获取可用的语音列表"""
        try:
            if self.engine:
                voices = self.engine.getProperty('voices')
                return [{"id": voice.id, "name": voice.name} for voice in voices]
            return []
        except Exception as e:
            print(f"获取语音列表失败: {e}")
            return []
    
    def set_voice(self, voice_id):
        """设置语音"""
        try:
            if self.engine:
                self.engine.setProperty('voice', voice_id)
                return True
        except Exception as e:
            print(f"设置语音失败: {e}")
        return False
    
    def is_available(self):
        """检查语音合成是否可用"""
        return self.engine is not None
    
    def cleanup(self):
        """清理资源"""
        try:
            self.stop_speaking = True
            self.stop_current_speech()
            
            if self.speech_thread and self.speech_thread.is_alive():
                self.speech_thread.join(timeout=2)
            
            if self.engine:
                self.engine.stop()
                
        except Exception as e:
            print(f"清理语音合成资源失败: {e}")


class VoiceFeedback:
    """语音反馈管理器"""
    
    def __init__(self):
        self.tts = TextToSpeech()
        self.feedback_enabled = True
    
    def enable_feedback(self):
        """启用语音反馈"""
        self.feedback_enabled = True
    
    def disable_feedback(self):
        """禁用语音反馈"""
        self.feedback_enabled = False
    
    def speak_response(self, response_text):
        """语音输出响应"""
        if self.feedback_enabled and response_text:
            self.tts.speak(response_text)
    
    def speak_confirmation(self, action):
        """语音确认操作"""
        if self.feedback_enabled:
            self.tts.speak(f"好的，正在{action}")
    
    def speak_error(self, error_message):
        """语音输出错误信息"""
        if self.feedback_enabled:
            self.tts.speak(f"抱歉，{error_message}")
    
    def speak_success(self, success_message):
        """语音输出成功信息"""
        if self.feedback_enabled:
            self.tts.speak(success_message)
    
    def speak_waiting(self):
        """语音提示等待"""
        if self.feedback_enabled:
            self.tts.speak("请稍等，我正在处理")


if __name__ == "__main__":
    # 测试语音合成
    tts = TextToSpeech()
    
    if tts.is_available():
        print("语音合成可用")
        
        # 测试基本语音输出
        print("测试语音输出...")
        tts.speak("你好，我是语音控制助手")
        
        # 等待语音完成
        time.sleep(3)
        
        # 测试异步语音输出
        print("测试异步语音输出...")
        tts.speak_async("这是一个异步语音测试")
        
        # 等待语音完成
        time.sleep(3)
        
        # 测试语音列表
        print("可用语音:")
        voices = tts.get_available_voices()
        for voice in voices:
            print(f"  {voice['name']} ({voice['id']})")
        
        # 清理资源
        tts.cleanup()
    else:
        print("语音合成不可用")

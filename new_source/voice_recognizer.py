"""
语音识别模块
使用麦克风进行实时语音识别
"""
import speech_recognition as sr
import threading
import time
from config import VOICE_RECOGNITION_LANGUAGE, VOICE_TIMEOUT, VOICE_PHRASE_TIMEOUT


class VoiceRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.callback = None
        
        # 调整麦克风环境噪音
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
    
    def set_callback(self, callback):
        """设置语音识别结果回调函数"""
        self.callback = callback
    
    def start_listening(self):
        """开始监听语音"""
        if self.is_listening:
            return
        
        self.is_listening = True
        thread = threading.Thread(target=self._listen_loop)
        thread.daemon = True
        thread.start()
    
    def stop_listening(self):
        """停止监听语音"""
        self.is_listening = False
    
    def _listen_loop(self):
        """语音监听循环"""
        while self.is_listening:
            try:
                with self.microphone as source:
                    # 监听语音输入
                    audio = self.recognizer.listen(
                        source, 
                        timeout=VOICE_TIMEOUT,
                        phrase_time_limit=VOICE_PHRASE_TIMEOUT
                    )
                
                # 识别语音
                text = self.recognizer.recognize_google(
                    audio, 
                    language=VOICE_RECOGNITION_LANGUAGE
                )
                
                if text and self.callback:
                    self.callback(text.strip())
                    
            except sr.WaitTimeoutError:
                # 超时，继续监听
                continue
            except sr.UnknownValueError:
                # 无法识别语音
                if self.callback:
                    self.callback("")
            except sr.RequestError as e:
                print(f"语音识别服务错误: {e}")
                time.sleep(1)
            except Exception as e:
                print(f"语音识别异常: {e}")
                time.sleep(1)
    
    def recognize_once(self):
        """单次语音识别"""
        try:
            with self.microphone as source:
                print("请说话...")
                audio = self.recognizer.listen(source, timeout=VOICE_TIMEOUT)
                
            text = self.recognizer.recognize_google(
                audio, 
                language=VOICE_RECOGNITION_LANGUAGE
            )
            return text.strip()
            
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"语音识别服务错误: {e}")
            return ""
        except Exception as e:
            print(f"语音识别异常: {e}")
            return ""


if __name__ == "__main__":
    # 测试语音识别
    recognizer = VoiceRecognizer()
    
    def on_recognized(text):
        if text:
            print(f"识别到: {text}")
        else:
            print("未识别到语音")
    
    recognizer.set_callback(on_recognized)
    recognizer.start_listening()
    
    print("开始语音识别，按 Ctrl+C 退出...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        recognizer.stop_listening()
        print("语音识别已停止")

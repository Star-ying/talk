"""
系统控制模块
实现各种系统操作功能
"""
import os
import subprocess
import platform
import psutil
import pygame
import schedule
import time
import threading
from datetime import datetime
from config import DEFAULT_MUSIC_PATH, DEFAULT_DOCUMENT_PATH


class SystemController:
    def __init__(self):
        self.system = platform.system()
        self.music_player = None
        self.scheduled_tasks = {}
        self.task_counter = 0
        
        # 初始化音乐播放器
        try:
            pygame.mixer.init()
            self.music_player = pygame.mixer.music
        except Exception as e:
            print(f"音乐播放器初始化失败: {e}")
    
    def play_music(self, music_path=None):
        """播放音乐"""
        try:
            if not music_path:
                music_path = DEFAULT_MUSIC_PATH
            
            # 查找音乐文件
            music_files = self._find_music_files(music_path)
            if not music_files:
                return False, "未找到音乐文件"
            
            # 播放第一个找到的音乐文件
            music_file = music_files[0]
            self.music_player.load(music_file)
            self.music_player.play()
            
            return True, f"正在播放: {os.path.basename(music_file)}"
            
        except Exception as e:
            return False, f"播放音乐失败: {str(e)}"
    
    def stop_music(self):
        """停止音乐"""
        try:
            self.music_player.stop()
            return True, "音乐已停止"
        except Exception as e:
            return False, f"停止音乐失败: {str(e)}"
    
    def pause_music(self):
        """暂停音乐"""
        try:
            self.music_player.pause()
            return True, "音乐已暂停"
        except Exception as e:
            return False, f"暂停音乐失败: {str(e)}"
    
    def resume_music(self):
        """恢复音乐"""
        try:
            self.music_player.unpause()
            return True, "音乐已恢复"
        except Exception as e:
            return False, f"恢复音乐失败: {str(e)}"
    
    def open_application(self, app_name):
        """打开应用程序"""
        try:
            app_commands = {
                "浏览器": self._get_browser_command(),
                "记事本": self._get_text_editor_command(),
                "文件管理器": self._get_file_manager_command(),
                "计算器": self._get_calculator_command(),
                "终端": self._get_terminal_command()
            }
            
            if app_name in app_commands:
                command = app_commands[app_name]
                subprocess.Popen(command, shell=True)
                return True, f"正在打开{app_name}"
            else:
                return False, f"不支持打开{app_name}"
                
        except Exception as e:
            return False, f"打开应用失败: {str(e)}"
    
    def create_file(self, file_path, content=""):
        """创建文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True, f"文件已创建: {file_path}"
        except Exception as e:
            return False, f"创建文件失败: {str(e)}"
    
    def read_file(self, file_path):
        """读取文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content
        except Exception as e:
            return False, f"读取文件失败: {str(e)}"
    
    def write_file(self, file_path, content):
        """写入文件"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, f"文件已保存: {file_path}"
        except Exception as e:
            return False, f"写入文件失败: {str(e)}"
    
    def get_system_info(self):
        """获取系统信息"""
        try:
            info = {
                "操作系统": platform.system(),
                "系统版本": platform.version(),
                "处理器": platform.processor(),
                "内存使用率": f"{psutil.virtual_memory().percent}%",
                "CPU使用率": f"{psutil.cpu_percent()}%",
                "磁盘使用率": f"{psutil.disk_usage('/').percent}%"
            }
            return True, info
        except Exception as e:
            return False, f"获取系统信息失败: {str(e)}"
    
    def set_reminder(self, message, delay_minutes):
        """设置提醒"""
        try:
            self.task_counter += 1
            task_id = f"reminder_{self.task_counter}"
            
            def reminder_job():
                print(f"提醒: {message}")
                # 这里可以添加通知功能
            
            schedule.every(delay_minutes).minutes.do(reminder_job)
            self.scheduled_tasks[task_id] = {
                "message": message,
                "delay": delay_minutes,
                "created": datetime.now()
            }
            
            return True, f"提醒已设置: {delay_minutes}分钟后提醒 - {message}"
        except Exception as e:
            return False, f"设置提醒失败: {str(e)}"
    
    def run_scheduled_tasks(self):
        """运行定时任务"""
        schedule.run_pending()
    
    def _find_music_files(self, directory):
        """查找音乐文件"""
        music_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
        music_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in music_extensions):
                        music_files.append(os.path.join(root, file))
        except Exception as e:
            print(f"搜索音乐文件失败: {e}")
        
        return music_files
    
    def _get_browser_command(self):
        """获取浏览器启动命令"""
        if self.system == "Windows":
            return "start chrome"
        elif self.system == "Darwin":  # macOS
            return "open -a Safari"
        else:  # Linux
            return "xdg-open"
    
    def _get_text_editor_command(self):
        """获取文本编辑器启动命令"""
        if self.system == "Windows":
            return "notepad"
        elif self.system == "Darwin":  # macOS
            return "open -a TextEdit"
        else:  # Linux
            return "gedit"
    
    def _get_file_manager_command(self):
        """获取文件管理器启动命令"""
        if self.system == "Windows":
            return "explorer"
        elif self.system == "Darwin":  # macOS
            return "open -a Finder"
        else:  # Linux
            return "nautilus"
    
    def _get_calculator_command(self):
        """获取计算器启动命令"""
        if self.system == "Windows":
            return "calc"
        elif self.system == "Darwin":  # macOS
            return "open -a Calculator"
        else:  # Linux
            return "gnome-calculator"
    
    def _get_terminal_command(self):
        """获取终端启动命令"""
        if self.system == "Windows":
            return "cmd"
        elif self.system == "Darwin":  # macOS
            return "open -a Terminal"
        else:  # Linux
            return "gnome-terminal"


class TaskOrchestrator:
    """任务编排器，用于处理多步骤任务"""
    
    def __init__(self, system_controller, gpt_assistant):
        self.system_controller = system_controller
        self.gpt_assistant = gpt_assistant
        self.task_queue = []
        self.current_task = None
    
    def execute_task_sequence(self, tasks):
        """执行任务序列"""
        results = []
        
        for task in tasks:
            try:
                result = self._execute_single_task(task)
                results.append(result)
                
                # 如果任务失败，可以选择继续或停止
                if not result["success"]:
                    print(f"任务失败: {result['message']}")
                    
            except Exception as e:
                results.append({
                    "success": False,
                    "message": f"任务执行异常: {str(e)}"
                })
        
        return results
    
    def _execute_single_task(self, task):
        """执行单个任务"""
        task_type = task.get("type")
        parameters = task.get("parameters", {})
        
        if task_type == "music":
            action = parameters.get("action", "play")
            if action == "play":
                success, message = self.system_controller.play_music()
            elif action == "stop":
                success, message = self.system_controller.stop_music()
            elif action == "pause":
                success, message = self.system_controller.pause_music()
            elif action == "resume":
                success, message = self.system_controller.resume_music()
            else:
                success, message = False, f"不支持的音乐操作: {action}"
        
        elif task_type == "file":
            action = parameters.get("action", "create")
            file_path = parameters.get("path", "")
            content = parameters.get("content", "")
            
            if action == "create":
                success, message = self.system_controller.create_file(file_path, content)
            elif action == "read":
                success, message = self.system_controller.read_file(file_path)
            elif action == "write":
                success, message = self.system_controller.write_file(file_path, content)
            else:
                success, message = False, f"不支持的文件操作: {action}"
        
        elif task_type == "text":
            action = parameters.get("action", "generate")
            prompt = parameters.get("prompt", "")
            
            if action == "generate":
                content = self.gpt_assistant.generate_text(prompt)
                success, message = True, content
            elif action == "summarize":
                content = self.gpt_assistant.summarize_text(prompt)
                success, message = True, content
            elif action == "translate":
                target_lang = parameters.get("target_language", "英文")
                content = self.gpt_assistant.translate_text(prompt, target_lang)
                success, message = True, content
            else:
                success, message = False, f"不支持的文本操作: {action}"
        
        elif task_type == "system":
            action = parameters.get("action", "info")
            
            if action == "info":
                success, message = self.system_controller.get_system_info()
            elif action == "open_app":
                app_name = parameters.get("app_name", "")
                success, message = self.system_controller.open_application(app_name)
            elif action == "reminder":
                message_text = parameters.get("message", "")
                delay = parameters.get("delay_minutes", 5)
                success, message = self.system_controller.set_reminder(message_text, delay)
            else:
                success, message = False, f"不支持的系统操作: {action}"
        
        else:
            success, message = False, f"不支持的任务类型: {task_type}"
        
        return {
            "success": success,
            "message": message,
            "task": task
        }


if __name__ == "__main__":
    # 测试系统控制器
    controller = SystemController()
    
    # 测试音乐播放
    print("测试音乐播放...")
    success, message = controller.play_music()
    print(f"结果: {success}, {message}")
    
    # 测试文件操作
    print("\n测试文件创建...")
    success, message = controller.create_file("test.txt", "这是一个测试文件")
    print(f"结果: {success}, {message}")
    
    # 测试应用打开
    print("\n测试打开应用...")
    success, message = controller.open_application("记事本")
    print(f"结果: {success}, {message}")
    
    # 测试系统信息
    print("\n测试系统信息...")
    success, info = controller.get_system_info()
    print(f"结果: {success}")
    if success:
        for key, value in info.items():
            print(f"{key}: {value}")

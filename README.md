# talk
基础版基于deepseek-coder-1.3b-instruct版本的模型展开对话，实现本地API对话，为用户提供最原始的AI"调教"服务

运行前需要配置mysql数据库，可以运行mysql文件夹下的database.sql文件

上传文件没有模型，若要测试，请在 https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct 网址下载

运行myapp.py文件，按照提示打开本地网址，即可开始“调教”

本版本将远程API版和基础版分开实现，未来再将两版合并，满足不同需求的用户

远程API版无需下载模型，“开盖即食”

myapp2.py启动远程API版，这一版采用API链接千帆模型，可以直接使用已经训练好的模型来完成角色扮演

现在已经完成myapp和myapp2的合并，并且实现了登录、注册、身份认证、主页等功能，但AI"调教"暂未开放，还没有建立多用户数据库，计划将每个用户的对话历史分开存储，并在登出或关闭网页时总结对话历史，减少存储和运行压力。

身份认证目前采用cookie（本地检测）+JWT（加密存储）的形式，未来还会增加redis（redis本身只能在Linux运行，但我找到办法使用redis，目前还在研究），方便管理session和token状态，加强安全性。
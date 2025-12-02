import torch
print(torch.cuda.is_available())        # 应输出 True
print(torch.version.cuda)               # 应显示 CUDA 版本（如 11.8）

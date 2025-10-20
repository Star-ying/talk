chcp 65001
echo 测试中文是否正常

@echo off
:: =====================================================
:: 项目依赖安装脚本
:: 功能：创建虚拟环境（如不存在），并安装 requirements.txt 中的依赖
:: 使用方法：双击运行 或 在命令行中执行 install_deps.bat
:: =====================================================

echo [1/4] 正在检查 Python 是否安装...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误：未找到 Python，请先安装 Python 并加入系统 PATH！
    echo    下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/4] 正在检查并创建虚拟环境 (venv)...
if not exist venv (
    echo 创建虚拟环境中...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境创建失败！
        pause
        exit /b 1
    )
) else (
    echo 虚拟环境已存在，跳过创建。
)

echo [3/4] 正在激活虚拟环境并升级 pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
if %errorlevel% neq 0 (
    echo ❌ pip 升级失败！
    pause
    exit /b 1
)

echo [4/4] 正在安装依赖包 (from requirements.txt)...
pip install -r %~dp0requirements.txt
if %errorlevel% equ 0 (
    echo ✅ 所有依赖安装成功！
) else (
    echo ❌ 安装失败，请检查网络或 requirements.txt 文件是否存在。
    echo 可能的原因：
    echo   - 缺少 Microsoft Visual C++ Build Tools
    echo   - 网络问题导致无法下载包
    echo   - requirements.txt 文件路径不正确
    pause
    exit /b 1
)

echo.
echo 🎉 安装完成！依赖已成功安装到虚拟环境中。
echo 提示：手动激活虚拟环境请运行：venv\Scripts\activate.bat

exit /b 0
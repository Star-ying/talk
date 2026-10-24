chcp 65001 >nul
@echo off

:: =====================================================

:: 项目依赖安装脚本

:: 功能：创建虚拟环境（如不存在），安装 requirements.txt，并自动激活

:: 使用方法：双击运行 或 命令行执行 install_deps.bat

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

:: 设置虚拟环境名称
set VENV_DIR=venv-py

echo [2/4] 正在检查并创建虚拟环境 (%VENV_DIR%)...
if not exist "%VENV_DIR%" (
    echo 创建虚拟环境中...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境创建失败！请确保 Python 可用且路径无中文或空格。
        pause
        exit /b 1
    )
) else (
    echo 虚拟环境已存在，跳过创建。
)

echo [3/4] 正在激活虚拟环境并升级 pip...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo ❌ 虚拟环境激活失败，请检查 "%VENV_DIR%" 是否存在。
    pause
    exit /b 1
)

echo 升级 pip 到最新版本...
python -m pip install --upgrade pip >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip 升级失败！
    pause
    exit /b 1
)

echo [4/4] 正在安装依赖包 (from requirements.txt)...
if not exist "%~dp0requirements.txt" (
    echo ❌ 错误：找不到 requirements.txt 文件！
    echo    当前路径：%~dp0
    pause
    exit /b 1
)
pip install -r "%~dp0requirements.txt"
if %errorlevel% equ 0 (
    echo ✅ 所有依赖安装成功！
) else (
    echo ❌ 安装失败，请检查网络或 requirements.txt 内容。
    echo 可能原因：
    echo   - 缺少 Microsoft Visual C++ Build Tools
    echo   - 网络问题导致无法下载包
    echo   - requirements.txt 中有错误格式
    pause
    exit /b 1
)

echo.
echo 🎉 安装完成！你现在处于虚拟环境中。
echo 🔁 输入 'deactivate' 可退出虚拟环境。
echo 💡 接下来你可以运行主程序，例如：
echo      python MaApp.py
echo.

:: 保持 CMD 打开并在激活状态下等待用户操作
cmd /k
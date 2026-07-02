@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+ 并加入 PATH。
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 正在检查依赖...
python -m pip show requests >nul 2>nul
if errorlevel 1 (
    echo 正在安装依赖 requests...
    python -m pip install -r requirements.txt
)

echo 正在启动 神州租车 全国搜车工具 ...
python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序异常退出，请查看上方日志。
    pause
)

endlocal

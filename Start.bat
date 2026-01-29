@echo off
title ABS 快速开发环境启动
echo 正在并行启动服务...

:: 1. Start Core Services (如果这个脚本很快，可以加 -Wait)
echo [1/3] 启动 Core Services...
powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\abs-ai-fabric\core; .\start-core.ps1'"
timeout /t 5

:: 2. Start AI Fabric
echo [2/3] 启动 AI Fabric...
powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\abs-ai-fabric\abs-ai-hub\hub-ui-v2; npm run dev'"
timeout /t 8

:: 3. Start Workstation Console
echo [3/3] 启动 Workstation Console...
powershell -Command "Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd D:\abs-ai-fabric\abs-ai-hub\apps\abs_workstation_console; npm run dev'"
timeout /t 5

:: 4. Open Edge
echo 正在连接至 http://localhost:5173 ...
start msedge http://localhost:5173

echo 所有窗口已弹出。